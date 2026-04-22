<img width="1983" height="793" alt="ChatGPT Image Apr 22, 2026, 02_21_26 AM" src="https://github.com/user-attachments/assets/6772588e-b764-4cca-8637-172cad44af06" />


# 🏥 MedSignal
### High-Performance Multi-Agent Clinical Risk Detection System

> **"Detects critical clinical risks from unstructured patient input — using parallel AI agents optimized for AMD GPU infrastructure."**

![AMD Developer Cloud](https://img.shields.io/badge/Compute-AMD%20Developer%20Cloud-ED1C24?style=flat-square)
![Built with CrewAI](https://img.shields.io/badge/Framework-CrewAI-4B32C3?style=flat-square)
![Model](https://img.shields.io/badge/Model-Llama%203-0064A5?style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![AMD Developer Hackathon](https://img.shields.io/badge/Hackathon-AMD%20Developer%202026-ED1C24?style=flat-square)

---

## 🚨 The Problem

Doctors don't miss critical signals because they lack knowledge — they miss them because they lack **time under pressure**.

- 80+ patients per day in busy clinical settings
- No structured medical records in most cases
- Fragmented, informal patient descriptions
- Critical patterns spread across symptoms, habits, and medications

> The failure is not intelligence — it's **real-time reasoning under overload.**

Existing clinical decision support tools assume structured EMR data. Most patients arrive with none.

> MedSignal is designed for this reality. It flags missing data explicitly rather than inferring history that wasn't provided.

---

## 💡 The Solution

MedSignal is a **multi-agent AI system** that analyzes patient cases like a team of specialists — not a single chatbot.

It:
- Accepts **unstructured, real-world input** — informal descriptions, incomplete histories, mixed-language notes
- Processes multiple clinical dimensions **simultaneously** via parallel agents
- Outputs a **structured, severity-ranked red flag report**
- Works with **zero prior records** — flags missing data rather than hallucinating it

---

## ⚡ Example

### Input

```
65 year old male, chest tightness since morning, breathlessness.
Smoker, diabetic, on BP meds (unknown name), recently prescribed antibiotic.
No prior medical records available.
```

### Output

```
Severity levels: 🔴 CRITICAL / HIGH   🟡 MEDIUM   🟢 LOW

SEVERITY: ● CRITICAL
────────────────────────────────────────────

RED FLAGS
🔴 Probable ACS — chest pain + diabetes + 20yr smoker pattern
🔴 Possible drug interaction — warfarin + antibiotic (rule + OpenFDA)
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

────────────────────────────────────────────
⚠️  Decision support only. Not a diagnosis.
    All outputs require clinical validation.
```

---

## 🏗️ System Architecture

```
Raw Patient Input (unstructured text)
            │
            ▼
    ┌───────────────┐
    │  Intake Agent │  → Structures raw input into JSON
    │               │    Flags missing data explicitly
    └───────┬───────┘    Never invents history
            │
            ▼
┌───────────────────────────────────────────────┐
│       ⚡ PARALLEL EXECUTION                    │
│          (AMD Instinct MI300X)                 │
│                                               │
│  ├── DDx Agent          → differential diagnosis
│  ├── Red Flag Agent     → rules + OpenFDA + LLM
│  └── Consistency Agent  → contradiction detection
└───────────────────┬───────────────────────────┘
                    │         ↑ GPU advantage:
                    │         concurrent inference,
                    │         lower latency
                    ▼
          ┌──────────────────┐
          │  Summary Agent   │  → Structured report
          │                  │    Severity-ranked output
          └──────────────────┘    Recommended actions
                    │
                    ▼
        Structured Clinical Report
```

Parallel agent execution is only viable at low latency because of AMD's compute stack. The DDx, Red Flag, and Consistency agents run **concurrently** on AMD Instinct MI300X — not sequentially. This is the core GPU advantage: multiple reasoning tasks handled simultaneously, reducing response time from seconds to near real-time.

---

## 🤖 The Five Agents

| Agent | Role | Key capability |
|---|---|---|
| **Intake Agent** | Clinical intake specialist | Parses messy free text into structured JSON; flags missing fields; never invents data |
| **DDx Agent** | Differential diagnosis expert | Generates ranked conditions by probability and severity |
| **Red Flag Agent** | Emergency medicine specialist | Hybrid: 7 hard rules + LLM reasoning + OpenFDA API grounding |
| **Consistency Agent** | Case coherence checker | Detects contradictions — stated vs implied history, inconsistent symptom patterns |
| **Summary Agent** | Clinical report writer | Assembles structured output with severity ratings and action recommendations |

All five agents run on the **same model** — Llama 3 via AMD Developer Cloud. What makes each agent different is its role, goal, and task prompt. One engine, five specialists.

---

## 🔍 Hybrid Reasoning Layer

MedSignal does **not** rely purely on LLMs. It combines three layers for reliability:

### Layer 1 — Pattern-Based Risk Engine (fast, deterministic)

MedSignal uses a **weighted risk pattern system** instead of rigid rules.

Each pattern:
- Combines symptoms, conditions, habits, **vitals**, and context
- Uses clinical weights (not all signals are equal)
- Triggers only if a minimum threshold is met
- Outputs a confidence score (0.3–1.0)

Example:
chest pain + diabetes → CRITICAL  
fever + confusion + neck stiffness → CRITICAL  

Drug interaction patterns:
warfarin + interacting drugs (e.g., clarithromycin, fluconazole) → HIGH: bleeding risk  
opioid + benzodiazepine → HIGH: respiratory depression  
paracetamol + heavy alcohol use → HIGH: hepatotoxicity

### Layer 2 — OpenFDA API (real data grounding)
Drug interaction labels pulled live from the FDA database. Prevents hallucinated drug information. Adds "FDA confirmed" credibility to every drug-related flag.

### Layer 3 — LLM Reasoning (flexible, context-aware)
Handles combinations not covered by rules. Explains *why* the risk exists. Provides clinical context, severity rationale, and handles incomplete input gracefully.

> 2025 peer-reviewed research showed no single AI achieved reliable precision for clinical DDI screening (best F1: 0.25). MedSignal's multi-layer architecture directly addresses this — each layer catches what the others miss.

---

## 🌍 Multi-Dimensional Risk Detection

Beyond drug interactions, MedSignal analyzes the full clinical picture:

```
Symptoms        →  chest tightness, breathlessness, confusion
Habits          →  smoking (20yr), alcohol use, sedentary lifestyle
Medications     →  known + unknown + inferred drug classes
History         →  present or explicitly flagged as absent
Contradictions  →  "no allergies" but amoxicillin reaction mentioned
```

Example chain:
> *65yr male + smoker 20 years + diabetic + chest pain + unknown BP med + antibiotic → CRITICAL: probable ACS + high drug interaction risk*

This is the connection a tired doctor at patient #75 might miss. MedSignal catches it by design.

---

## 🚀 Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | CrewAI |
| LLM | Llama 3 (AMD Developer Cloud) |
| Compute | AMD Instinct MI300X |
| Drug Data | OpenFDA API (free, no auth) |
| Backend | FastAPI |
| Frontend | React (Vite) |
| Deployment | Vercel (frontend) + HuggingFace Spaces Docker (backend) || Deployment | HuggingFace Spaces (Docker) |

---

## 📁 Project Structure

```
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
│   └── rule_engine.py           #  pattern-based clinical risk engine
├── crew/
│   └── medsignal_crew.py        # CrewAI crew + parallel config
├── api/
│   └── main.py                  # FastAPI endpoints
├── frontend/
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── pages/               # Route pages
│   │   └── main.jsx             # Entry point
│   ├── public/
│   ├── index.html
│   └── package.json
├── demo/
│   └── cases.py                 # 5 synthetic demo cases
├── tests/
│   └── test_agents.py
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🧪 Demo Cases

Five synthetic cases, each designed to trigger a different agent capability:

| # | Case | Pattern | Caught by |
|---|---|---|---|
| 1 | 65M, chest pain, smoker, diabetic, warfarin + clarithromycin | ACS risk + drug interaction | Red Flag (rule + OpenFDA) |
| 2 | 28F, headache + neck stiffness + fever + light sensitivity | Meningitis | Red Flag (rule) |
| 3 | 45M, paracetamol daily, heavy drinker | Hepatotoxicity | Red Flag (rule) |
| 4 | 55F, "no allergies" — mentions amoxicillin reaction 2019 | History contradiction | Consistency Agent |
| 5 | 70M, long-term steroids, now fever + low BP + confusion | Adrenal crisis | Red Flag (rule + LLM) |

---

## 🏁 Quickstart

```bash
# Clone
git clone https://github.com/Alok8732/medsignal
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
```

---

## 🔌 API Usage

```python
import requests

response = requests.post("http://localhost:8000/analyze", json={
    "case": "65 year old male, chest pain since morning, diabetic, smoker, \
             on warfarin and recently prescribed clarithromycin"
})

print(response.json())
# {
#   "severity": "CRITICAL",
#   "red_flags": [...],
#   "differential": [...],
#   "recommendations": [...],
#   "data_quality": "MEDIUM",
#   "disclaimer": "Decision support only. Not a diagnosis."
# }
```

---

## 🧩 What Makes It Different

| Typical AI Tool | MedSignal |
|---|---|
| Single LLM | Multi-agent system |
| Sequential reasoning | Parallel execution on AMD GPU |
| Generic chatbot output | Structured, severity-ranked report |
| Assumes structured records | Works with zero prior history |
| LLM-only, hallucination-prone | Hybrid: rules + OpenFDA + LLM |
| English-only input | Hindi + English mixed input supported | Handles noisy, informal, real-world input |

---

## ⚠️ Important Disclaimer

MedSignal is a **clinical decision support tool**, not a diagnostic system.

- All outputs require validation by a qualified medical professional
- Not approved for autonomous clinical decision-making
- Missing or incomplete patient data produces conservative risk assessments
- Do not use as a substitute for clinical judgment

---

## 📢 Build in Public

Built for the **AMD Developer Hackathon 2026** — Track 1: AI Agents & Agentic Workflows.

Follow the build journey:
- Tag `@AIatAMD` and `@lablab` on X for updates
- Open source — MIT License — contributions welcome

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

*MedSignal — because the connection that saves a life shouldn't depend on whether the doctor had enough sleep.*
