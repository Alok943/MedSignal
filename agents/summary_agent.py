from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field
from typing import List, Literal
from textwrap import dedent
from datetime import datetime, timezone
import json
import re
import logging
import concurrent.futures
from agents.ddx_agent import DDxOutput
from agents.red_flag_agent import RedFlagOutput
from agents.consistency_agent import ConsistencyOutput

logger = logging.getLogger(__name__)


def _run_with_timeout(crew, timeout=20):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(crew.kickoff)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return None
        
# =============================
# Final Report Schema
# (matches AnalysisResponse in main.py)
# =============================

class RedFlagReport(BaseModel):
    severity: str
    flag: str
    reasoning: str
    confidence: float


class DiffDiagReport(BaseModel):
    condition: str
    probability: str
    reasoning: str


class FinalReport(BaseModel):
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    red_flags: List[RedFlagReport]
    differential: List[DiffDiagReport]
    recommendations: List[str]
    data_quality: str
    consistency_notes: List[str]
    disclaimer: str = "Decision support only. Not a diagnosis."
    timestamp: str


# =============================
# Prompt
# =============================

SUMMARY_TASK_PROMPT = dedent("""
You are a senior clinical report writer. Synthesize multi-agent findings into a concise, structured report.

RED FLAGS (from Red Flag Agent):
{red_flags}

DIFFERENTIAL DIAGNOSIS (from DDx Agent):
{differential}

CONSISTENCY FINDINGS (from Consistency Agent):
{consistency}

PATIENT DATA SUMMARY:
{patient_summary}

TASK:
Generate 3–6 specific, actionable clinical recommendations based on the above.

Rules for recommendations:

- If consistency score is LOW, FIRST recommendation must be "Verify contradictory history"

- Order strictly:
  (1) immediate life-saving actions
  (2) investigations
  (3) data collection
  (4) referrals

- For CRITICAL flags, start with:
  "Initiate [condition] protocol immediately"
  (e.g., "Initiate ACS protocol immediately")

- Never use vague phrasing like "verify symptoms" for critical conditions

- Only recommend CT for PE if breathlessness, hypoxia, or DVT signs are present

- Only recommend LP if meningitis signs (fever + neck stiffness + altered mental status) are present
- For Snake Envenomation: first action must be "Immobilize limb, no tourniquet, no incision, transport rapidly", second must be "Perform 20-min WBCT, CBC, PT/INR", third "Administer antivenom if WBCT positive or systemic signs"

- Reference specific diagnoses or flags explicitly

- End with specialist referral if warranted

- Never recommend "watchful waiting" when CRITICAL flags are present

- Avoid unrelated diagnoses (e.g., TB without cough >2 weeks)

- Keep each recommendation ≤ 15 words
Return valid JSON only:
{{
  "recommendations": ["Immediate ECG and troponin", "Hold clarithromycin pending cardiology review"]
}}
""")


# =============================
# Pre-assembly (no LLM needed)
# =============================

def _assemble_without_llm(
    intake_data: dict,
    ddx: DDxOutput,
    red_flags: RedFlagOutput,
    consistency: ConsistencyOutput,
) -> FinalReport:
    """
    Assembles the report from agent outputs directly.
    Calls LLM only for recommendations.
    """

    # Convert red flags
    rf_items = [
        RedFlagReport(
            severity=f.severity,
            flag=f.flag,
            reasoning=f.reasoning,
            confidence=f.confidence,
        )
        for f in red_flags.red_flags
    ]

    # Convert differential
    diff_items = [
        DiffDiagReport(
            condition=d.condition,
            probability=d.probability,
            reasoning=d.reasoning,
        )
        for d in ddx.differential
    ]

    # Consistency notes
    consistency_notes = [
    f"Contradiction: {c.description}" for c in consistency.contradictions[:3]
    ]
    consistency_notes += [
    f"Missing: {g}" for g in consistency.data_gaps[:3]
    ]
    
    # 🔧 SAFETY: no red flags → LOW severity
    if not rf_items:
        severity = "LOW"
    else:
        severity = red_flags.overall_severity
    return FinalReport(
        severity=severity,
        red_flags=rf_items,
        differential=diff_items,
        recommendations=[],    # filled by LLM call
        data_quality=intake_data.get("data_quality", "UNKNOWN"),
        consistency_notes=consistency_notes,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# =============================
# Agent Setup
# =============================

def get_summary_agent(llm) -> Agent:
    return Agent(
        role="Senior Clinical Report Writer",
        goal="Synthesize multi-agent clinical findings into actionable, structured recommendations",
        backstory=dedent("""
            Experienced clinical coordinator trained in evidence-based medicine and patient safety.
            Expert at converting complex risk data into clear, prioritized clinical actions.
            Never recommends watchful waiting when life-threatening risks exist.
        """),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# =============================
# Format context for LLM
# =============================

def _fmt_red_flags(rf: RedFlagOutput) -> str:
    lines = [f"Overall: {rf.overall_severity}"]
    for f in rf.red_flags[:5]:  # top 5 only
        lines.append(f"• [{f.severity}] {f.flag} — {f.reasoning} (source: {f.source})")
    return "\n".join(lines)


def _fmt_ddx(ddx: DDxOutput) -> str:
    lines = [f"Confidence: {ddx.ddx_confidence}"]
    for d in ddx.differential[:3]:
        lines.append(f"• #{d.rank} {d.condition} [{d.severity}/{d.probability}] — {d.reasoning}")
    return "\n".join(lines)


def _fmt_consistency(c: ConsistencyOutput) -> str:
    if not c.contradictions and not c.data_gaps:
        return f"Score: {c.consistency_score}. No contradictions found."
    lines = [f"Score: {c.consistency_score}"]
    if c.consistency_score == "LOW":
        lines.append("⚠️ Unreliable history — verify critical details")
    for ct in c.contradictions[:3]:
        lines.append(f"• [{ct.severity}] {ct.description}")
    for g in c.data_gaps[:3]:
        lines.append(f"• Gap: {g}")
    return "\n".join(lines)


def _fmt_patient_summary(intake: dict) -> str:
    parts = []
    if intake.get("age"): parts.append(f"Age {intake['age']}")
    if intake.get("sex"): parts.append(intake["sex"])
    if intake.get("symptoms"): parts.append(f"Symptoms: {', '.join(map(str, intake['symptoms'][:4]))}")
    if intake.get("conditions"): parts.append(f"Conditions: {', '.join(map(str, intake['conditions'][:3]))}")
    if intake.get("medications"): parts.append(f"Meds: {', '.join(map(str, intake['medications'][:3]))}")
    if intake.get("data_quality"): parts.append(f"Data quality: {intake['data_quality']}")
    return " | ".join(parts) or "Minimal patient data available"


# =============================
# Main Runner
# =============================

def run_summary(
    llm,
    intake_data: dict,
    ddx: DDxOutput,
    red_flags: RedFlagOutput,
    consistency: ConsistencyOutput,
) -> FinalReport:

    logger.debug("Assembling summary report")

    # Deterministic assembly
    report = _assemble_without_llm(intake_data, ddx, red_flags, consistency)

    # LLM: generate recommendations only
    agent = get_summary_agent(llm)

    task = Task(
        description=SUMMARY_TASK_PROMPT.format(
            red_flags=_fmt_red_flags(red_flags),
            differential=_fmt_ddx(ddx),
            consistency=_fmt_consistency(consistency),
            patient_summary=_fmt_patient_summary(intake_data),
        ),
        expected_output='Valid JSON: {"recommendations": ["...", "..."]}',
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = None
    for attempt in range(3):
        result = _run_with_timeout(crew, timeout=20)
        logger.warning(f"Attempt {attempt+1} raw result: {repr(getattr(result, 'raw', None))}")
        if result is not None:
            raw_text = getattr(result, "raw", None) or ""
            if raw_text.strip() and raw_text.strip().lower() != "none":
                break
        logger.warning(f"Summary agent attempt {attempt+1} failed, retrying...")

    # Timeout fallback
    if result is None:
        report.recommendations = _fallback_recommendations(red_flags)
        return report
   # — catches bad result after retries
    raw_check = getattr(result, "raw", None) or ""
    if not raw_check.strip() or raw_check.strip().lower() == "none":
        report.recommendations = _fallback_recommendations(red_flags)
        return report
    
    # Parse recommendations
    try:
        raw_text = getattr(result, "raw", None) or getattr(result, "output", None) or str(result)
        
        if not raw_text or raw_text.strip().lower() == "none":
            raise ValueError("Empty LLM response")
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw_text).strip()
        
        if not cleaned:  # ← this catches the empty case you hit
            raise ValueError("Empty LLM response")
        
        # Try to extract JSON object if LLM wrapped it in prose
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{[^{}]*\}', cleaned)  # fallback: first simple object
        
        
    
        recs_data = json.loads(cleaned)
        recs = recs_data.get("recommendations", [])[:6]
        report.recommendations = recs if recs else _fallback_recommendations(red_flags)
    except Exception as e:
        logger.warning(f"Rec parse failed: {e}. Using fallback.")
        report.recommendations = _fallback_recommendations(red_flags)

    logger.debug(f"Summary complete. Severity={report.severity}, Flags={len(report.red_flags)}")
    return report


# =============================
# Fallback Recommendations
# =============================

def _fallback_recommendations(red_flags: RedFlagOutput) -> List[str]:
    recs = []

    # 1. Data quality first
    if any("unreliable" in f.flag.lower() for f in red_flags.red_flags):
        recs.append("Verify contradictory history")

    # 2. Immediate life-saving actions (priority)
    for f in red_flags.red_flags:
        flag_lower = f.flag.lower()
        reasoning_lower = f.reasoning.lower()

        if "acs" in flag_lower:
            recs.append("Initiate ACS protocol immediately")

        elif "stroke" in flag_lower:
            recs.append("Initiate stroke protocol immediately")

        elif "sepsis" in flag_lower:
            recs.append("Initiate sepsis protocol immediately")

        elif "anaphylaxis" in flag_lower:
            recs.append("Administer IM epinephrine immediately")

        elif "adrenal" in flag_lower:
            recs.append("Administer IV hydrocortisone immediately")

        elif "snake" in flag_lower or "envenomation" in flag_lower:
            recs.append("Immobilize limb, no tourniquet, no incision, transport rapidly")
            recs.append("Perform 20-min WBCT, CBC, PT/INR")
            recs.append("Administer antivenom if WBCT positive or systemic signs")
            
    # 3. Investigations
    for f in red_flags.red_flags:
        flag_lower = f.flag.lower()

        if "acs" in flag_lower:
            recs.append("Order ECG and troponin")

        if "bleeding" in flag_lower:
            recs.append("Check coagulation profile and INR")

        if "hepatotox" in flag_lower:
            recs.append("Check liver function tests urgently")

    # 4. Data collection
    for f in red_flags.red_flags:
        if "missing" in f.flag.lower():
            recs.append("Collect missing clinical data")

    # 5. Referral
    if any("acs" in f.flag.lower() for f in red_flags.red_flags):
        recs.append("Urgent cardiology referral")

    # Deduplicate while preserving order
    recs = list(dict.fromkeys(recs))

    if not recs:
        recs = ["Urgent clinical evaluation required"]

    return recs[:6]


# ============================================================
# ARCHITECTURE
# ============================================================

"""
Flow:
    (ddx, red_flags, consistency, intake_data)
        ↓
    _assemble_without_llm()     ← deterministic, no LLM
        ↓
    LLM agent → recommendations only (minimal token use)
        ↓
    _fallback_recommendations() if LLM fails
        ↓
    FinalReport

LLM scope is intentionally minimal — only recommendations need
clinical reasoning. All other fields come from upstream agents.
"""