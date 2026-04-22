from crewai import Agent, Task
from textwrap import dedent


DDX_TASK_PROMPT = dedent("""
You are a differential diagnosis expert in emergency medicine.

Given structured patient data, generate a ranked differential diagnosis list.

Rules:
- Rank by probability (most likely first)
- ALWAYS prioritize life-threatening conditions first, even if probability is moderate
- Assign severity: CRITICAL / HIGH / MODERATE / LOW
- Probability: HIGH / MEDIUM / LOW based ONLY on available data
- Each reasoning MUST reference specific patient data (symptoms, vitals, conditions, meds)
- DO NOT introduce diagnoses not supported by the provided data
- Keep reasoning concise (1 line per condition)
- Maximum 5 diagnoses
- If data is incomplete, still provide ranking but highlight uncertainty

Return ONLY valid JSON:

{
  "differential": [
    {
      "rank": 1,
      "condition": "Acute Coronary Syndrome",
      "severity": "CRITICAL",
      "probability": "HIGH",
      "reasoning": "Chest pain + diabetes + smoker + age >50"
    }
  ],
  "ddx_confidence": "HIGH|MEDIUM|LOW",
  "ddx_notes": "mention missing data, uncertainty, or limitations"
}

Patient data:
{structured_input}
""")



def get_ddx_agent(llm) -> Agent:
    return Agent(
        role="Differential Diagnosis Expert",
        goal="Generate a ranked, severity-weighted differential diagnosis from structured patient data",
        backstory=dedent("""
            You are a senior emergency physician with 20 years of experience.
            You think systematically — you never anchor on one diagnosis too early,
            and you always consider life-threatening conditions first.
        """),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def get_ddx_task(agent: Agent, structured_input: dict) -> Task:
    import json
    return Task(
        description=DDX_TASK_PROMPT.format(
            structured_input=json.dumps(structured_input, indent=2)
        ),
        expected_output="Valid JSON with ranked differential diagnosis",
        agent=agent,
    )