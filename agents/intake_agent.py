from crewai import Agent, Task, Crew
from textwrap import dedent
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
import json
import re
import os

# =============================
# Pydantic Schema
# =============================

class IntakeOutput(BaseModel):
    age: Optional[int] = None
    sex: str = "unknown"

    symptoms: List[str] = []
    vitals: List[str] = []
    conditions: List[str] = []
    medications: List[str] = []
    habits: List[str] = []
    history: List[str] = []

    timeline: Dict[str, Optional[str]] = {"onset": None, "duration": None}
    negations: List[str] = []
    uncertain: List[str] = []

    missing_fields: List[str] = []
    data_quality: str = "LOW"

    original_text: str = ""


# =============================
# Prompts
# =============================

INTAKE_SYSTEM_PROMPT = dedent("""
You are a clinical intake specialist.

Rules:
- NEVER invent or assume data
- Extract only explicitly mentioned information
- If unsure, put data in "uncertain"
- Capture negations explicitly
- Extract timeline: onset (sudden/gradual), duration
- Respond ONLY with valid JSON
""")

INTAKE_TASK_PROMPT = dedent("""
Extract structured clinical data from the input.

Return JSON with:
{
  "age": int or null,
  "sex": "male"|"female"|"unknown",
  "symptoms": [],
  "vitals": [],
  "conditions": [],
  "medications": [],
  "habits": [],
  "history": [],
  "timeline": {"onset": null, "duration": null},
  "negations": [],
  "uncertain": [],
  "missing_fields": [],
  "data_quality": "HIGH|MEDIUM|LOW"
}

Patient input:
{patient_input}
""")


# =============================
# Load Mappings (external JSON)
# =============================



def load_mappings():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "..", "data", "mappings.json")

    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load mappings: {e}")
        return {}

# =============================
# Negation Handling
# =============================

NEGATIONS = ["no", "denies", "without", "nahi", "nahin", "bina", "nai", "na"]

def is_negated(term: str, text: str) -> bool:
    text_l = text.lower()
    term_l = term.lower()
    for n in NEGATIONS:
        if f"{n} {term_l}" in text_l or f"{term_l} {n}" in text_l:
            return True
    return False


# =============================
# Normalization
# =============================

def normalize_term(item: str, mappings: Dict[str, str]) -> str:
    item_l = item.lower().strip()

    if item_l in mappings:
        return mappings[item_l]

    for key, val in mappings.items():
        if re.search(rf"\b{re.escape(key)}\b", item_l):
            return val

    return item_l


def normalize_list(items: List[str], mappings: Dict[str, str], minimal=False) -> List[str]:
    if minimal:
        return items
    return list(dict.fromkeys([normalize_term(i, mappings) for i in items if i]))


# =============================
# Cleaning Pipeline
# =============================

def clean_intake(data: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:

    text = data.get("original_text", "").lower()
    print("[CLEAN] starting")

    data.setdefault("negations", [])

    # ---- Negation ----
    for field in ["symptoms", "conditions"]:
        filtered = []
        for item in data.get(field, []):
            if not is_negated(item, text):
                filtered.append(item)
            else:
                data["negations"].append(item)

        data[field] = list(dict.fromkeys(filtered))
        print(f"[NEGATION] {field} → {data[field]}")

    # ---- Data Quality (early for normalization mode) ----
    quality = compute_data_quality(data)

    minimal_mode = quality == "LOW"

    # ---- Normalization ----
    data["symptoms"] = normalize_list(data.get("symptoms", []), mappings, minimal_mode)
    data["conditions"] = normalize_list(data.get("conditions", []), mappings, minimal_mode)
    data["habits"] = normalize_list(data.get("habits", []), mappings, minimal_mode)

    print(f"[NORMALIZED] symptoms → {data['symptoms']}")

    # ---- Vitals ----
    cleaned_vitals = []
    for v in data.get("vitals", []):
        v_l = v.lower()

        # reuse normalization
        norm = normalize_term(v_l, mappings)
        if norm != v_l:
            cleaned_vitals.append(norm)
            continue

        m = re.search(r'(\d{2,3})\s*(?:over|/)\s*(\d{2,3})', v_l)
        if m:
            cleaned_vitals.append(f"{m.group(1)}/{m.group(2)}")
            continue

        cleaned_vitals.append(v_l)

    data["vitals"] = cleaned_vitals
    print(f"[VITALS] → {data['vitals']}")

    # ---- Timeline ----
    tl = data.get("timeline", {}) or {}

    if not tl.get("duration"):
        for key in ["kal se", "aaj subah se", "2 din se"]:
            if key in text:
                tl["duration"] = mappings.get(key)
                break

    if not tl.get("onset"):
        if any(w in text for w in ["sudden", "suddenly", "achanak"]):
            tl["onset"] = "sudden"
        elif any(w in text for w in ["gradual", "dheere"]):
            tl["onset"] = "gradual"

    data["timeline"] = tl
    print(f"[TIMELINE] → {tl}")

    return data


# =============================
# Missing Fields
# =============================

def compute_missing_fields(data: Dict[str, Any]) -> List[str]:
    missing = []

    syms = data.get("symptoms", [])
    tl = data.get("timeline", {})

    if any("chest pain" in s for s in syms):
        if not tl.get("duration"):
            missing.append("duration")
        if not tl.get("onset"):
            missing.append("onset")

    if any("fever" in s for s in syms):
        if not tl.get("duration"):
            missing.append("fever_duration")

    if any("breathlessness" in s for s in syms) and not data.get("vitals"):
        missing.append("vitals")

    return list(set(missing))


# =============================
# Data Quality
# =============================

def compute_data_quality(data: Dict[str, Any]) -> str:
    score = 0

    if data.get("age"): score += 1
    if data.get("symptoms"): score += 1
    if data.get("medications"): score += 1
    if data.get("vitals"): score += 1
    if data.get("timeline", {}).get("duration"): score += 1

    if score >= 4: return "HIGH"
    if score >= 2: return "MEDIUM"
    return "LOW"


# =============================
# Agent Setup
# =============================

def get_intake_agent(llm) -> Agent:
    return Agent(
        role="Clinical Intake Specialist",
        goal="Extract structured clinical data reliably",
        backstory="Experienced intake specialist who never assumes missing data",
        llm=llm,
        verbose=False,
        allow_delegation=False,
        system_prompt=INTAKE_SYSTEM_PROMPT
    )


def get_intake_task(agent: Agent, patient_input: str) -> Task:
    return Task(
        description=INTAKE_TASK_PROMPT.format(patient_input=patient_input),
        expected_output="Valid JSON",
        agent=agent,
    )


# =============================
# Main Pipeline
# =============================

def run_intake(llm, patient_input: str) -> Dict[str, Any]:

    print(f"[RAW_INPUT] {patient_input}")

    agent = get_intake_agent(llm)
    task = get_intake_task(agent, patient_input)

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()

    try:
        raw = re.sub(r"```(?:json)?|```", "", str(result)).strip()
        data = json.loads(str(result))
    except Exception as e:
        print(f"[ERROR] Invalid JSON: {e}")
        return {"error": "Invalid LLM output", "original_text": patient_input}

    data["original_text"] = patient_input
    print(f"[LLM_OUTPUT] {data}")

    try:
        validated = IntakeOutput(**data).model_dump()
    except ValidationError as e:
        print(f"[ERROR] Validation failed: {e}")
        return {"error": "Validation failed", "original_text": patient_input}

    mappings = load_mappings()

    cleaned = clean_intake(validated, mappings)

    cleaned["missing_fields"] = compute_missing_fields(cleaned)
    cleaned["data_quality"] = compute_data_quality(cleaned)

    print(f"[FINAL_OUTPUT] {cleaned}")

    return cleaned


# ============================================================
# ARCHITECTURE
# ============================================================

"""
Raw Input
   ↓
LLM Extraction
   ↓
Pydantic Validation
   ↓
clean_intake()
   ├─ Negation
   ├─ Normalization (mappings.json)
   ├─ Vitals Cleaning
   ├─ Timeline Structuring
   ↓
Missing Fields Detection
   ↓
Data Quality Scoring
   ↓
Final JSON (+ original_text)
   ↓
Rule Engine + Agents
"""