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


def _run_with_timeout(crew, timeout=10):
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
- If consistency score is LOW, FIRST recommendation must be to verify contradictory history
- Lead with the most urgent action (e.g., "Immediate ECG and troponin")
- Reference specific flags/diagnoses (e.g., "Verify {{drug_name}} before administering")
- Include data collection if critical vitals/labs are missing
- End with specialist referral if warranted
- Never recommend "watchful waiting" when CRITICAL flags present
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

    return FinalReport(
        severity=red_flags.overall_severity,
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
    result = _run_with_timeout(crew)

    # Timeout fallback
    if result is None:
        report.recommendations = _fallback_recommendations(red_flags)
        return report

    # Parse recommendations
    try:
        raw_text = getattr(result, "raw", None) or getattr(result, "output", None) or str(result)
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw_text).strip()
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
    """Generate basic recommendations from flag types when LLM fails."""
    recs = []
    if any("unreliable" in f.flag.lower() for f in red_flags.red_flags):
        recs.append("Verify contradictory history before proceeding")
    for f in red_flags.red_flags:
        flag_lower = f.flag.lower()
        reasoning_lower = f.reasoning.lower()

        if "acs" in flag_lower or "chest" in reasoning_lower:
            recs.append("Immediate ECG and troponin")

        if "warfarin" in reasoning_lower or "bleeding" in flag_lower:
            recs.append("Review anticoagulant + interacting medication immediately")

        if "meningitis" in flag_lower:
            recs.append("Urgent LP and empirical antibiotics")

        if "adrenal" in flag_lower:
            recs.append("Immediate hydrocortisone — do not delay for investigations")

        if "serotonin" in flag_lower:
            recs.append("Discontinue serotonergic agent — monitor for hyperthermia")

        if "hepatotox" in flag_lower:
            recs.append("Stop paracetamol — check LFTs urgently")

        if "respiratory" in flag_lower:
            recs.append("Monitor respiratory rate and O2 saturation closely")

    recs = list(dict.fromkeys(recs))  # deduplicate
    if not recs:
        recs = ["Urgent clinical review required", "Do not discharge without specialist assessment"]
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