"""HTTP endpoints for fall-event triage."""

from fastapi import APIRouter

from app.models.triage import TriageEvaluateRequest, TriageResult
from app.services.triage import run_triage

router = APIRouter(tags=["triage"])


@router.post("/evaluate", response_model=TriageResult)
async def evaluate_triage(payload: TriageEvaluateRequest) -> TriageResult:
    result = run_triage(
        patient_profile=payload.patient_profile,
        fall_event=payload.fall_event,
        elapsed_seconds=payload.elapsed_seconds,
        language=payload.language,
        patient_response=payload.patient_response,
    )
    return TriageResult(**result)
