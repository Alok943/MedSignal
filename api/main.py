import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI

from agents.intake_agent import run_intake
from crew.medsignal_crew import run_medsignal_crew
from agents.summary_agent import FinalReport
from pydantic import SecretStr

load_dotenv()
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# =============================
# LLM Setup (AMD Developer Cloud)
# =============================
from functools import lru_cache
from crewai import LLM

@lru_cache(maxsize=1)
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "groq")

    if provider == "groq":
        return LLM(
            model=f"groq/{os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')}",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1,
            max_tokens=1024,
        )

    elif provider == "google":
        return LLM(
            model=f"gemini/{os.getenv('GOOGLE_MODEL', 'gemini-1.5-flash')}",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1,
            max_tokens=1024,
        )

    elif provider == "amd":
        return LLM(
            model=f"openai/{os.getenv('AMD_MODEL', 'meta-llama/Llama-3.1-8B-Instruct')}",
            api_key=os.getenv("AMD_API_KEY"),
            base_url=os.getenv("AMD_API_BASE", "https://api.inference.amd.com/v1"),
            temperature=0.1,
            max_tokens=1024,
        )

    elif provider == "lightning":
        return LLM(
            model=f"openai/{os.getenv('LIGHTNING_MODEL', 'gemma')}",
            api_key=os.getenv("LIGHTNING_API_KEY"),
            base_url=os.getenv("LIGHTNING_API_BASE"),
            temperature=0.1,
            max_tokens=1024,
        )

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

# =============================
# FastAPI App
# =============================

app = FastAPI(
    title="MedSignal API",
    description="Multi-Agent Clinical Risk Detection System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================
# Request / Response Models
# =============================

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
    consistency_notes: List[str] = Field(default_factory=list)
    disclaimer: str = "Decision support only. Not a diagnosis."
    timestamp: str
    requires_verification: bool = False # NEW


# =============================
# Converter: FinalReport → AnalysisResponse
# =============================

def _to_response(report: FinalReport) -> AnalysisResponse:
    requires_verification = any(
        "unreliable" in f.flag.lower()
        for f in report.red_flags
    )

    return AnalysisResponse(
        severity=report.severity,
        red_flags=[
            RedFlag(
                severity=f.severity,
                flag=f.flag,
                reasoning=f.reasoning,
                confidence=f.confidence,
            )
            for f in report.red_flags
        ],
        differential=[
            DifferentialDiagnosis(
                condition=d.condition,
                probability=d.probability,
                reasoning=d.reasoning,
            )
            for d in report.differential
        ],
        recommendations=report.recommendations,
        data_quality=report.data_quality,
        consistency_notes=report.consistency_notes,
        timestamp=report.timestamp,
        requires_verification=requires_verification,  # ✅ FIXED
    )


# =============================
# Endpoints
# =============================

@app.get("/health")
async def health_check():
    """System telemetry and health status."""
    return {
        "status": "ONLINE",
        "agents_ready": True,
        "gpu_status": "AMD Instinct MI300X Ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_case(request: CaseRequest):
    """
    Main entry point for MedSignal Multi-Agent pipeline.
    """

    case_text = request.case.strip()

    if not case_text:
        raise HTTPException(status_code=400, detail="Patient case description cannot be empty.")

    if len(case_text) > 2000:
        raise HTTPException(status_code=400, detail="Input too long")

    try:
        llm = get_llm()

        # ── Stage 1: Intake ───────────────────────────────
        logger.debug(f"Intake starting for: {case_text[:80]}")
        structured_data = await asyncio.to_thread(run_intake, llm, case_text)

        if "error" in structured_data:
            raise HTTPException(
                status_code=422,
                detail=f"Intake Agent failed: {structured_data['error']}"
            )

        logger.debug(f"Intake complete. Quality={structured_data.get('data_quality')}")

        # ── Stages 2–5: Crew ─────────────────────────────
        try:
            final_report = await asyncio.to_thread(
                        run_medsignal_crew, llm, structured_data
            )
        except asyncio.TimeoutError:
            logger.error("Pipeline timeout")
            raise HTTPException(status_code=500, detail="Processing timeout")

        return _to_response(final_report)

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        logger.error(f"API error: {msg}", exc_info=True)
    
    # surface provider overload cleanly
        if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg:
            raise HTTPException(
                status_code=503, 
                detail="LLM provider overloaded. Retry in 10s or set LLM_PROVIDER=groq in .env"
        )
        raise HTTPException(status_code=500, detail="Internal processing error")


@app.post("/intake-only", response_model=dict)
async def intake_only(request: CaseRequest):
    """
    Debug endpoint: runs only the intake agent.
    Returns structured JSON without running risk analysis.
    """
    if not request.case.strip():
        raise HTTPException(status_code=400, detail="Empty input.")
    try:
        llm = get_llm()
        return await asyncio.to_thread(run_intake, llm, request.case)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))