from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import DEFAULT_MAX_AGE
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Assuming these are your local imports based on project structure
# from agents.intake_agent import run_intake
# from tools.rule_engine import run_hard_rules
# from crew.medsignal_crew import run_medsignal_crew

app = FastAPI(
    title="MedSignal API",
    description="Multi-Agent Clinical Risk Detection System",
    version="1.0.0"
)

# Enable CORS for the React frontend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------
class CaseRequest(BaseModel):
    case: str = Field(..., description="Unstructured patient clinical text")

class RedFlag(BaseModel):
    severity: str
    flag: str
    reasoning: str
    confidence: float

class DifferentialDiagnosis(BaseModel):
    condition: str
    probability: str
    reasoning: str

class AnalysisResponse(BaseModel):
    severity: str
    red_flags: List[RedFlag]
    differential: List[DifferentialDiagnosis]
    recommendations: List[str]
    data_quality: str
    disclaimer: str = "Decision support only. Not a diagnosis."
    timestamp: str

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    """System telemetry and health status."""
    return {"status": "ONLINE", "agents_ready": True, "gpu_status": "AMD Instinct MI300X Ready"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_case(request: CaseRequest):
    """
    Main entry point for MedSignal Multi-Agent execution.
    Accepts raw text, triggers parallel agents, and returns a structured risk report.
    """
    if not request.case.strip():
        raise HTTPException(status_code=400, detail="Patient case description cannot be empty.")

    try:
        # ==========================================
        # STEP 1: INTAKE AGENT (Raw Text -> JSON)
        # ==========================================
        # structured_data = await run_intake(request.case)
        
        # [MOCK DATA for structure representation]
        structured_data = {
            "symptoms": ["chest pain", "breathlessness"],
            "medications": ["clarithromycin", "warfarin"],
            "habits": ["smoker"],
            "conditions": ["diabetes"],
            "age": 65
        }

        # ==========================================
        # STEP 2: PARALLEL EXECUTION 
        # (Rule Engine + CrewAI DDx + Consistency)
        # ==========================================
        
        # 1. Run deterministic rule engine (from your rule_engine.py)
        # hard_rule_matches = run_hard_rules(structured_data)
        
        # 2. Trigger asynchronous CrewAI agents
        # crew_results = await run_medsignal_crew(structured_data)

        # ==========================================
        # STEP 3: SUMMARY AGENT (Formatting output)
        # ==========================================
        
        # Mocking the final response based on your README spec
        return AnalysisResponse(
            severity="CRITICAL",
            red_flags=[
                RedFlag(
                    severity="CRITICAL",
                    flag="Probable ACS",
                    reasoning="chest pain + diabetes + 20yr smoker pattern",
                    confidence=0.85
                ),
                RedFlag(
                    severity="HIGH",
                    flag="Possible drug interaction",
                    reasoning="warfarin + clarithromycin (Bleeding risk - OpenFDA confirmed)",
                    confidence=0.92
                )
            ],
            differential=[
                DifferentialDiagnosis(condition="Acute coronary syndrome", probability="HIGH", reasoning="Classic presentation with risk factors"),
                DifferentialDiagnosis(condition="Pulmonary embolism", probability="MODERATE", reasoning="Breathlessness present, awaiting D-dimer")
            ],
            recommendations=[
                "Immediate ECG and troponin",
                "Hold clarithromycin pending cardiology review",
                "Do not discharge without cardiac workup"
            ],
            data_quality="MEDIUM",
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        # Catch agent failures or parsing errors
        raise HTTPException(status_code=500, detail=f"AI Processing Error: {str(e)}")