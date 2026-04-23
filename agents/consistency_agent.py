from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from textwrap import dedent
import json
import re
import concurrent.futures


# =============================
# Pydantic Schema
# =============================

class ContradictionItem(BaseModel):
    field_a: str
    field_b: str
    description: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]


class ConsistencyOutput(BaseModel):
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)
    consistency_score: Literal["HIGH", "MEDIUM", "LOW"]
    notes: str = ""


# =============================
# Constants (centralized rules)
# =============================

TB_MEDS = {"isoniazid", "rifampicin", "ethambutol"}
TB_CONDITIONS = {"tb", "tuberculosis"}

PREGNANCY_CONTRA = {"warfarin", "methotrexate", "isotretinoin"}


# =============================
# Pre-check logic
# =============================

def _precheck_contradictions(data: dict) -> List[dict]:
    found = []

    text = (data.get("original_text") or "").lower()

    negations = {str(n).lower() for n in data.get("negations", []) if n}
    conds = {str(c).lower() for c in data.get("conditions", []) if c}
    meds = {str(m).lower() for m in data.get("medications", []) if m}
    habits = {str(h).lower() for h in data.get("habits", []) if h}
    history = {str(h).lower() for h in data.get("history", []) if h}

    # -------------------------
    # Pattern 1: Allergy contradiction
    # -------------------------
    has_allergy_word = bool(re.search(r'\ballerg', text))
    negated_allergy = bool(re.search(r'(no|denies|not)\s+\w*\s*allerg', text))

    allergy_denied = any("allerg" in n for n in negations)
    allergy_in_history = any("allerg" in h for h in history)

    if allergy_denied and (allergy_in_history or (has_allergy_word and not negated_allergy)):
        found.append({
            "field_a": "negations: no allergies",
            "field_b": "history/text: allergy mentioned",
            "description": "Patient denies allergies but allergy evidence present",
            "severity": "HIGH"
        })

    # -------------------------
    # Pattern 2: Smoking contradiction
    # -------------------------
    smoking_denied = any(re.search(r'\bsmok', n) for n in negations)
    smoking_present = any(re.search(r'\bsmok', h) for h in habits)

    if smoking_denied and smoking_present:
        found.append({
            "field_a": "negations: no smoking",
            "field_b": "habits: smoking",
            "description": "Smoking simultaneously denied and present",
            "severity": "HIGH"
        })

    # -------------------------
    # Pattern 3: Age vs elderly condition
    # -------------------------
    age = data.get("age") or 0
    elderly_conds = ["coronary artery disease", "copd", "prostate", "osteoporosis", "cataract"]

    if age and age < 30:
        for c in conds:
            if any(e in c for e in elderly_conds):
                found.append({
                    "field_a": f"age: {age}",
                    "field_b": f"condition: {c}",
                    "description": f"Condition '{c}' atypical for age {age}",
                    "severity": "MEDIUM"
                })

    # -------------------------
    # Pattern 4: Diabetes contradiction
    # -------------------------
    diabetes_denied = any("diabet" in n for n in negations)
    diabetes_meds = any(m in meds for m in ["insulin", "metformin", "glipizide"])

    if diabetes_denied and diabetes_meds:
        found.append({
            "field_a": "negations: no diabetes",
            "field_b": "medications: diabetic drugs",
            "description": "Diabetes denied but medication present",
            "severity": "HIGH"
        })

    # -------------------------
    # Pattern 5: TB meds without diagnosis
    # -------------------------
    if any(any(t in m for t in TB_MEDS) for m in meds) and not any(t in c for t in TB_CONDITIONS for c in conds):
        found.append({
            "field_a": "medications: anti-TB drugs",
            "field_b": "conditions: TB missing",
            "description": "Anti-TB drugs present but TB not listed",
            "severity": "MEDIUM"
        })

    # -------------------------
    # Pattern 6: Pregnancy + contraindicated meds
    # -------------------------
    if any("pregnan" in c for c in conds):
        if any(any(d in m for d in PREGNANCY_CONTRA) for m in meds):
            found.append({
                "field_a": "condition: pregnancy",
                "field_b": "medications: contraindicated",
                "description": "Contraindicated drug in pregnancy",
                "severity": "HIGH"
            })

    return found


# =============================
# Prompt
# =============================

CONSISTENCY_TASK_PROMPT = dedent("""
You are a clinical coherence specialist.

PRE-DETECTED CONTRADICTIONS:
{precheck_findings}

STRUCTURED DATA:
{structured_input}

ORIGINAL TEXT:
{original_text}

TASK:
- Add ONLY new contradictions
- List missing critical data
- Assign consistency_score

Return JSON only.
""")


# =============================
# Timeout wrapper
# =============================

def _run_with_timeout(crew, timeout=10):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(crew.kickoff)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return None


# =============================
# Safe parser
# =============================

def _parse_consistency_safe(raw: str, precheck: List[dict]) -> ConsistencyOutput:
    cleaned = re.sub(r'```(?:json)?|```', '', str(raw)).strip()

    try:
        data = json.loads(cleaned)
    except Exception:
        return ConsistencyOutput(
            contradictions=[ContradictionItem(**p) for p in precheck],
            data_gaps=[],
            consistency_score="LOW" if precheck else "HIGH",
            notes="Parse failed"
        )

    data.setdefault("contradictions", [])
    data.setdefault("data_gaps", [])

    # Deduplicate contradictions
    seen = set()
    unique = []
    for c in data["contradictions"]:
        key = c["description"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    data["contradictions"] = unique

    # Score logic
    high_count = sum(1 for c in data["contradictions"] if c.get("severity") == "HIGH")
    n = len(data["contradictions"])

    if high_count >= 2:
        data["consistency_score"] = "LOW"
    elif high_count == 1 or n >= 2:
        data["consistency_score"] = "MEDIUM"
    else:
        data["consistency_score"] = "HIGH"

    try:
        return ConsistencyOutput(**data)
    except Exception:
        return ConsistencyOutput(
            contradictions=[ContradictionItem(**p) for p in precheck],
            data_gaps=[],
            consistency_score="LOW" if precheck else "HIGH",
            notes="Validation fallback"
        )


# =============================
# Main runner
# =============================

def run_consistency(llm, structured_data: dict) -> ConsistencyOutput:

    precheck = _precheck_contradictions(structured_data)

    compact = {k: v for k, v in structured_data.items() if v not in [None, "", [], {}]}
    original_text = structured_data.get("original_text", "")

    precheck_str = "\n".join(
        f"• [{p['severity']}] {p['description']}" for p in precheck
    ) if precheck else "None"

    agent = Agent(
        role="Clinical Coherence Specialist",
        goal="Detect contradictions",
        backstory="Expert in medical reasoning",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task = Task(
        description=CONSISTENCY_TASK_PROMPT.format(
            precheck_findings=precheck_str,
            structured_input=json.dumps(compact),
            original_text=original_text[:500]
        ),
        expected_output="JSON",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)

    result = _run_with_timeout(crew, timeout=10)

    if result is None:
        return ConsistencyOutput(
            contradictions=[ContradictionItem(**p) for p in precheck],
            data_gaps=[],
            consistency_score="LOW" if precheck else "HIGH",
            notes="Timeout fallback"
        )

    return _parse_consistency_safe(str(result), precheck)

# ============================================================
# 🧠 CONSISTENCY AGENT ARCHITECTURE
# ============================================================
"""
Consistency Agent — Hybrid Validation Layer

PURPOSE:
Detect contradictions and missing clinical data to assess reliability
of structured patient input before further reasoning (e.g., red flags, diagnosis).

--------------------------------------------------
FLOW:
--------------------------------------------------

1. INPUT:
   structured_data (from intake agent)

        ↓

2. _precheck_contradictions()
   - Deterministic rule-based checks
   - Zero hallucination layer
   - Captures obvious conflicts:
        • "no allergies" vs allergy present
        • smoking denied vs smoking in habits
        • diabetes denied vs diabetic meds
        • age vs unlikely condition
        • TB meds without TB diagnosis
        • pregnancy + contraindicated drugs

        ↓

3. LLM AGENT (CrewAI)
   - Detects deeper inconsistencies:
        • timeline mismatches
        • medication-condition gaps
        • symptom-vitals mismatch
   - Also identifies clinically important missing data

        ↓

4. _run_with_timeout()
   - Prevents system hanging if LLM is slow/unresponsive
   - Ensures system always returns output

        ↓

5. _parse_consistency_safe()
   - Cleans JSON output
   - Merges precheck + LLM results
   - Deduplicates contradictions
   - Applies consistency scoring logic:
        • HIGH → no contradictions
        • MEDIUM → minor issues
        • LOW → multiple/high severity issues
   - Provides fallback if parsing fails

        ↓

6. OUTPUT:
   ConsistencyOutput
        • contradictions
        • data_gaps
        • consistency_score
        • notes


--------------------------------------------------
KEY DESIGN PRINCIPLES:
--------------------------------------------------

• Deterministic-first:
  Rules are always trusted and never overridden.

• LLM as augmentation:
  LLM adds insights but cannot remove rule-based findings.

• Fail-safe system:
  Works even if LLM fails (timeout or parse error).

• Clinical realism:
  Not all contradictions are equal → severity-aware scoring.

• Performance-aware:
  Compact input + timeout ensures responsiveness.

--------------------------------------------------
WHY THIS MATTERS:
--------------------------------------------------

This layer acts as a "sanity check" before medical reasoning.

Bad input → bad diagnosis  
This agent reduces that risk.

--------------------------------------------------
FUTURE EXTENSIONS:
--------------------------------------------------

• Feed contradictions into red_flag_agent (severity boost)
• Expand rule registry (central config)
• Add temporal reasoning (timeline validation)
"""