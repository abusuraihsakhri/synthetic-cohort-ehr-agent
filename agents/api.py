"""
FastAPI REST API Server for Synthetic Cohort Ehr Agent.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .base import SecurityException
from synthetic_cohort_ehr_agent.generator import generate_cohort
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Synthetic Cohort Ehr Agent API",
    description="Demonstration metric audit and illustrative synthetic cohort generator",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class CohortRequest(BaseModel):
    count: int = Field(default=100, ge=1, le=2000)
    seed: int = Field(default=42, ge=0, le=4294967295)
    age_min: int = Field(default=18, ge=0, le=110)
    age_max: int = Field(default=85, ge=0, le=110)
    female_fraction: float = Field(default=0.5, ge=0, le=1, allow_inf_nan=False)
    max_encounters: int = Field(default=2, ge=1, le=5)


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "synthetic-cohort-ehr-agent", "domain": "Clinical & Biomedical AI", "standard": "Demonstration rules (not clinical standards)", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Potential personal identifiers are not accepted")
    return dossier.to_dict()


@app.post("/api/cohort")
def api_generate_cohort(req: CohortRequest):
    try:
        records = generate_cohort(**req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "disclaimer": "Illustrative synthetic records only; not clinically validated or certified anonymous.",
        "patients": req.count,
        "encounters": len(records),
        "records": records,
    }


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
