---
title: MedSignal
emoji: 🏥
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
---
# 🏥 MedSignal
### Multi-Agent Clinical Risk Detection System

> Detects critical clinical risks from unstructured patient input using parallel AI agents, deterministic rules, and live FDA grounding.

![Compute](https://img.shields.io/badge/Compute-AMD%20Developer%20Cloud-ED1C24?style=flat-square)
![Framework](https://img.shields.io/badge/Framework-CrewAI-4B32C3?style=flat-square)
![Model](https://img.shields.io/badge/Model-Llama%203-0064A5?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Hackathon](https://img.shields.io/badge/Hackathon-AMD%20Developer%202026-ED1C24?style=flat-square)

---

## 🚨 The Problem

Doctors don't miss critical signals because they lack knowledge — they miss them because they lack **time under pressure**.

- 80+ patients/day in high-volume clinics
- Fragmented, informal, or mixed-language patient descriptions
- No structured EMR data at point of care
- Critical patterns scattered across symptoms, habits, vitals, and medications
- Existing AI tools assume clean records and hallucinate when data is missing

> The failure is not intelligence. It's real-time reasoning under overload.

---

## 💡 The Solution

MedSignal is a **multi-agent clinical risk engine** built for reality:

- Accepts raw, unstructured, incomplete patient input
- Structures data deterministically without inventing history
- Runs **three clinical agents in parallel** on AMD Instinct MI300X GPUs
- Combines hard rules, live OpenFDA data, and bounded LLM reasoning
- Outputs a **severity-ranked, uncertainty-aware clinical report**
- Flags missing data explicitly instead of guessing

---

## 🏗️ System Architecture

Raw Patient Input (unstructured text)
            │
            ▼
    ┌───────────────┐
    │  Intake Agent │ → Structures raw input into JSON
    │               │   Flags missing fields explicitly
    └───────┬───────┘   Never invents history
            │
            ▼
┌───────────────────────────────────────────────────┐
│       ⚡ PARALLEL EXECUTION (AMD Instinct MI300X) │                      
│                                                   │
│                                                   │
│  ├── DDx Agent          → Differential diagnosis  │
│  ├── Red Flag Agent     → Rules + OpenFDA + LLM   │
│  └── Consistency Agent  → Contradiction detection │
└───────────────────┬───────────────────────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  Summary Agent   │ → Severity-ranked report
          │                  │   Recommended actions
          └──────────────────┘   Uncertainty notes
                    │
                    ▼
        Structured Clinical Report

Parallel execution is only viable at low latency because of AMD's compute stack. DDx, Red Flag, and Consistency run **concurrently**, not sequentially — cutting total wall time from ~4.5s to ~2.0s.

Agent status is streamed to the frontend via **Server-Sent Events (SSE)** as each agent completes — no polling, no fake animations.

### Latency Profile (AMD Instinct MI300X)

| Agent | Mode | Avg Latency |
|-------|------|-------------|
| Intake | Sequential | ~312ms |
| DDx | Parallel | ~890ms |
| Red Flag | Parallel | ~1240ms |
| Consistency | Parallel | ~670ms |
| Summary | Sequential | ~420ms |
| **Total (parallel)** | | **~1.97s** |
| Total (sequential) | | ~4.53s |

---

## 🧠 Cross-Agent Reasoning & Uncertainty Modeling

Agents don't operate in silos. They **modulate each other's confidence** based on data reliability.

### Flow
`Consistency Agent` → `Red Flag Agent` & `DDx Agent`

### Behavior
| Consistency Score | Downstream Effect |
|-------------------|-------------------|
| `HIGH`            | Normal reasoning, full confidence bounds |
| `MEDIUM`          | LLM confidence clamped to `0.60–0.70`, notes flag minor gaps |
| `LOW`             | Adds `⚠️ Unreliable clinical history`, penalizes LLM flags, escalates only when directly supported by rules/FDA |

### Example
**Input:** `"No diabetes" but taking insulin`  
**Consistency:** `LOW`  
**Red Flags:** - `Unreliable clinical history` (RULE)  
- `Hypoglycemia risk` (confidence reduced from 0.75 → 0.65)  
**DDx Notes:** `Contradictory history — probability scores conservative`

> MedSignal models **uncertainty**, not just severity.

---

## 🔍 Hybrid Reasoning Layer

No single AI layer achieves reliable clinical precision. MedSignal combines three:

### 1️⃣ Rule Engine (Deterministic)
- 28 weighted clinical patterns covering cardiac, neuro, sepsis, obstetric,
  toxicology, vector-borne, pediatric, and India-specific presentations
- ALWAYS_CRITICAL set prevents emergency downgrades from alarm-fatigue guards
- Numeric vitals parsing (e.g. BP 90/60 → Hypotension CRITICAL)
- Exposure field checks conditions + symptoms + habits to prevent missed presentations
- Triggers only when minimum clinical weight is met
- Outputs dynamic confidence `0.30–1.00` with missing-data penalties
- Zero hallucination, fully reproducible

### 2️⃣ OpenFDA API (Live Grounding)
- Real drug interaction labels pulled live from FDA database
- Word-boundary matching prevents substring false positives (`"in"` ≠ `"insulin"`)
- Adds `"FDA confirmed"` credibility to every drug-related flag
- Conservative severity tiering (`fatal/life-threatening` → CRITICAL, else HIGH)

### 3️⃣ LLM Reasoning (Context-Aware)
- Handles combinations not covered by rules
- Explains clinical context, symptom clusters, and drug-disease interactions
- Confidence strictly clamped to `0.60–0.80`
- Prompt guardrails forbid inventing history or repeating deterministic flags

## 🇮🇳 India-Specific Clinical Coverage

Rule engine tuned for high-volume Indian emergency presentations:
- Dengue warning signs (monsoon-aware, season-weighted)
- Snake envenomation with WBCT-first protocol
- Organophosphate poisoning (pesticide exposure pattern)
- Scorpion envenomation
- Rabies exposure risk
- Tetanus-prone wound detection
- TB red flag (cough >2 weeks required, no false positives)
- Paracetamol + alcohol hepatotoxicity (common OTC pattern)
> 2025 peer-reviewed research showed best DDI screening F1: 0.25 for single-model AI. MedSignal's hybrid architecture catches what any single layer misses.

---

## 🤖 The Five Agents

| Agent | Role | Key Capability | Safety Guardrail |
|-------|------|----------------|------------------|
| **Intake** | Clinical intake specialist | Parses messy text → structured JSON | Never assumes missing data; flags explicitly |
| **DDx** | Differential diagnosis expert | Ranks conditions by severity × probability | Truncates reasoning, blocks unsupported diagnoses |
| **Red Flag** | Emergency medicine specialist | Hybrid: Rules + OpenFDA + LLM | Deterministic severity, confidence clamping, deduplication |
| **Consistency** | Case coherence checker | Detects stated vs implied contradictions | 4 deterministic prechecks + LLM deep scan |
| **Summary** | Clinical report writer | Assembles severity-ranked output | Injects uncertainty notes, conservative recommendations |

All agents run on **Llama 3 via AMD Developer Cloud**. One engine, five specialists.

---

## 🛡️ Clinical Safety & Fault Tolerance

Built for production, not demos:

- ✅ **Deterministic-first**: Rules & FDA form the immutable base. LLM only augments.
- ✅ **No hallucination**: Missing data flagged explicitly. Never invents history.
- ✅ **Confidence integrity**: Rule penalties preserved. LLM bounds enforced (`0.60–0.80`).
- ✅ **Safe parsing**: Multiline regex cleaning, Pydantic `model_validate`, graceful fallbacks.
- ✅ **Word-boundary drug matching**: Prevents substring false positives.
- ✅ **Deterministic severity**: `overall_severity` computed from sorted flags, never trusted to LLM.
- ✅ **Timeout & fallback**: OpenFDA calls protected; pipeline degrades safely to rule-only output.

---

## ⚡ Live Example

**Input**

65 year old male, chest tightness since morning, breathlessness.
Smoker, diabetic, on BP meds (unknown name), recently prescribed antibiotic.
No prior medical records available.


**Output**

SEVERITY: ● CRITICAL
────────────────────────────────────────────
RED FLAGS
🔴 Probable ACS — chest symptoms + diabetes + smoker pattern
🟡 Missing medication data — conservative risk assessment applied
🟡 No prior records — actual risk may be understated

DIFFERENTIAL DIAGNOSIS
1. Acute coronary syndrome        [HIGH]
2. Pulmonary embolism             [MODERATE]
3. Hypertensive crisis            [MODERATE]
4. GERD / musculoskeletal         [LOW — symptoms atypical]

RECOMMENDED ACTIONS
→ Immediate ECG and troponin
→ Verify medication names before any new prescription
→ Cardiology referral — do not discharge without cardiac workup

⚠️ Decision support only. Not a diagnosis. All outputs require clinical validation.


---

## 🚀 Tech Stack & Structure

| Component | Technology |
|-----------|------------|
| Agent Framework | CrewAI |
| LLM | Llama 3 (AMD Developer Cloud) |
| Compute | AMD Instinct MI300X |
| Drug Data | OpenFDA API (free, no auth) |
| Backend | FastAPI |
| Frontend | React (Vite) |
| Analytics | Vercel Analytics |
| Streaming | SSE (Server-Sent Events) — real-time agent status |
| Deployment | Vercel (frontend) + HuggingFace Spaces Docker (backend) |

```text
medsignal/
├── data/
│   └── mappings.json            # Hindi-English clinical term normalization
├── agents/
│   ├── intake_agent.py          # Raw text → structured JSON
│   ├── ddx_agent.py             # Differential diagnosis
│   ├── red_flag_agent.py        # Hybrid rule + LLM + OpenFDA
│   ├── consistency_agent.py     # Contradiction detection
│   └── summary_agent.py         # Final report assembly
├── tools/
│   ├── openfda_tool.py          # OpenFDA API wrapper
│   └── rule_engine.py           # Weighted clinical risk engine
├── crew/
│   └── medsignal_crew.py        # CrewAI crew + parallel config
├── api/
│   └── main.py                  # FastAPI endpoints
├── frontend/                    # React UI
├── demo/
│   └── cases.py                 # 5 synthetic demo cases
├── tests/
│   └── test_agents.py
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md

## 🔮 Future Updates

### Near-term (v1.1)
- **Golden test suite** — 30 synthetic cases covering 10 high-risk patterns, with clinician-validated labels. Runs in CI before every deploy
- **Meningitis LP guardrail** — LP suggested only when ≥2 of fever, neck stiffness, altered mental status, or immunocompromise are present, and no contraindications
- **ACS hierarchy fix** — group STEMI, NSTEMI, and unstable angina under "ACS" to prevent duplicate differential entries
- **LOW severity actions** — replace generic "urgent evaluation" with context-aware home care and watchlist advice

### Clinical Coverage (v1.2)
- **Pre-hospital protocol cards** — VIEW PROTOCOL button with evidence-based steps per diagnosis, with disclaimer
- **WHY THIS DIAGNOSIS** — per-condition reasoning explainer using DDx agent output
- **Export Report** — one-click PDF of structured clinical summary
- **Telemetry dashboard** — live view of agent latency, flag rates, and severity distribution

### Intelligence (v2.0)
- **Hybrid rule engine** — augment hand-coded rules with a small classifier trained on golden suite corrections. Target precision 0.90, recall 0.85 on validation set
- **Atypical presentation detection** — flag ACS in women and diabetics, sepsis without fever in elderly
- **Polypharmacy engine** — expand beyond warfarin to 3+ drug interactions using OpenFDA and DrugBank
- **Temporal reasoning** — validate symptom onset against medication start dates and prior events

### Infrastructure (v2.0)
- **Hindi and Hinglish intake** — extend mappings.json to full intake parsing for regional languages
- **FHIR input support** — accept structured EMR records alongside free text
- **Clinician feedback loop** — correction UI writes back to golden suite and rule weights, with audit trail
- **Multi-model benchmarking on MI300X** — compare Llama 3, Mistral, and clinical fine-tunes using batched inference on AMD Instinct

## Clone
git clone [https://github.com/Alok8732/medsignal](https://github.com/Alok8732/medsignal)
cd medsignal

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add AMD Developer Cloud API key to .env

# Run backend
uvicorn api.main:app --reload

# Run frontend (new terminal)
cd frontend
npm install
npm run dev