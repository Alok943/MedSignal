from crewai import Agent, Task
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from textwrap import dedent
import json
import re

# =============================
# Pydantic Schema
# =============================

class DifferentialItem(BaseModel):
    rank: int
    condition: str
    severity: Literal["CRITICAL", "HIGH", "MODERATE", "LOW"]
    probability: Literal["HIGH", "MEDIUM", "LOW"]
    reasoning: str

    @field_validator("reasoning")
    def truncate_reasoning(cls, v):
        return v[:140] if len(v) > 140 else v


class DDxOutput(BaseModel):
    differential: List[DifferentialItem] = Field(min_length=1, max_length=5)
    ddx_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    ddx_notes: str
    missing_critical_data: List[str] = Field(default_factory=list)


# =============================
# Prompt (~300 tokens, optimized)
# =============================

DDX_TASK_PROMPT = dedent("""
Generate ranked differential diagnosis from structured patient data.

RULES:
- chest pain + any of (age>50, smoking, diabetes, hypertension) → ACS probability MUST be HIGH unless strong alternative diagnosis present
- Never assign MEDIUM to ACS when 2+ cardiac risk factors present
- Always return 3–5 diagnoses regardless of data quality
- Rank by RISK = severity × probability. Life-threats first.
- Severity: CRITICAL/HIGH/MODERATE/LOW (danger, not probability)
- Probability: HIGH/MEDIUM/LOW (based ONLY on input data)
- Reasoning format: 'field:value + field:value' (≥2 fields, exact input terms)
- reasoning must not be empty
- Only reference fields present in input; do not fabricate values
- Do NOT assume missing risk factors (e.g., smoking, diabetes unless in input)
- Do NOT introduce unsupported diagnoses
- Avoid overlapping diagnoses (e.g., ACS + MI together — pick most specific)
- Use normalized terms exactly as provided
- India context: consider TB, dengue, atypical CAD, tropical fevers
- ddx_confidence must reflect data_quality and missing_fields
- ddx_notes must explicitly state missing data — never assume it
- missing_critical_data: list clinically relevant gaps
- If priority_hint exists, include it in top 1–2 unless contradicted
- Always return 1–5 diagnoses, ranks sequential from 1

OUTPUT — valid JSON only, no markdown:
{{"differential":[{{"rank":1,"condition":"...","severity":"...","probability":"...","reasoning":"symptoms:chest pain + conditions:diabetes"}}],"ddx_confidence":"...","ddx_notes":"...","missing_critical_data":[...]}}

Input:
{structured_input}
""")


# =============================
# Fields used for DDx
# =============================

DDX_ALLOWED_KEYS = {
    "age", "sex", "symptoms", "vitals",
    "conditions", "medications", "habits",
    "history", "timeline", "data_quality",
    "missing_fields", "priority_hint"
}


# =============================
# Cache (RESULT CACHE — fixed)
# =============================

_ddx_cache = {}
CACHE_VERSION = "v1"


def _cache_key(data: dict) -> str:
    return CACHE_VERSION + json.dumps(data, sort_keys=True, separators=(',', ':'))


# =============================
# Agent Setup
# =============================

def get_ddx_agent(llm) -> Agent:
    return Agent(
        role="Differential Diagnosis Expert",
        goal="Generate ranked, severity-weighted differential diagnosis from structured patient data",
        backstory=dedent("""
            Senior emergency physician with 20 years in Indian hospitals.
            Never anchors early. Prioritizes life-threatening conditions.
            Familiar with TB, dengue, atypical cardiac presentations.
            Never invents history. Always flags missing data.
        """),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# =============================
# Task Builder
# =============================

def build_ddx_task(agent: Agent, structured_input: dict) -> Task:

    compact = {
        k: v for k, v in structured_input.items()
        if k in DDX_ALLOWED_KEYS and v not in [None, "", [], {}]
    }

    compact.setdefault("data_quality", "UNKNOWN")
    compact.setdefault("missing_fields", [])

    return Task(
        description=DDX_TASK_PROMPT.format(
            structured_input=json.dumps(compact, separators=(',', ':'))
        ),
        expected_output="Valid JSON with 1-5 ranked diagnoses matching DDxOutput schema",
        agent=agent,
        output_pydantic=DDxOutput,
    )


# =============================
# Safe Parser
# =============================

def parse_ddx_safe(raw) -> DDxOutput:
    raw_text = getattr(raw, "raw", None) or getattr(raw, "output", None) or str(raw)
    cleaned = re.sub(r"```(?:json)?|```", "", raw_text).strip()
    try:
        return DDxOutput(**json.loads(cleaned))
    except:
        data = json.loads(cleaned)
        for item in data.get("differential", []):
            if len(item.get("reasoning", "")) > 140:
                item["reasoning"] = item["reasoning"][:140]
        return DDxOutput(**data)


# =============================
# Main Runner (CACHED)
# =============================

def run_ddx(agent: Agent, structured_input: dict) -> DDxOutput:

    compact = {
        k: v for k, v in structured_input.items()
        if k in DDX_ALLOWED_KEYS and v not in [None, "", [], {}]
    }

    compact.setdefault("data_quality", "UNKNOWN")
    compact.setdefault("missing_fields", [])

    key = _cache_key(compact)

    if key in _ddx_cache:
        print("[DDX CACHE HIT]")
        return _ddx_cache[key]

    task = build_ddx_task(agent, compact)
    result = agent.execute_task(task)

    parsed = parse_ddx_safe(result)

    _ddx_cache[key] = parsed

    return parsed


# ============================================================
# ARCHITECTURE
# ============================================================

"""
Flow:
    intake_output
        ↓
    filter (DDX_ALLOWED_KEYS)
        ↓
    compact JSON (no whitespace)
        ↓
    LLM (CrewAI)
        ↓
    Pydantic validation (DDxOutput)
        ↓
    safe fallback parser (if needed)
        ↓
    cached result (hash key)
        ↓
    final DDxOutput

Key decisions:
    - reasoning truncated softly (no hard failure)
    - strict field usage → prevents hallucination
    - cache stores RESULT (not Task)
    - prompt compressed but guardrails preserved
    - priority_hint enables rule + LLM hybrid reasoning
"""