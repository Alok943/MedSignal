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
