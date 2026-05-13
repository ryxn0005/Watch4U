"""Pydantic models for fall-event triage."""

from typing import Any

from pydantic import BaseModel, Field


class PatientProfile(BaseModel):
    age: int = Field(default=0, ge=0)
    previous_fall_history: bool = False
    stroke_history: bool = False
    cognitive_impairment: bool = False
    dementia: bool = False
    limited_mobility: bool = False
    uses_walker: bool = False
    uses_wheelchair: bool = False
    blood_thinner_medication: bool = False
    osteoporosis: bool = False
    lives_alone: bool = False
    mobility: str | None = None
    medications: list[str] = Field(default_factory=list)


class FallEvent(BaseModel):
    fall_detected: bool = True
    unconscious: bool = False
    head_impact: bool = False
    severe_pain: bool = False
    bleeding: bool = False
    chest_pain: bool = False
    breathing_difficulty: bool = False
    red_flags: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class TriageEvaluateRequest(BaseModel):
    patient_profile: PatientProfile
    fall_event: FallEvent
    elapsed_seconds: float = Field(default=0, ge=0)
    language: str = "en"
    patient_response: str | None = None


class TriageResult(BaseModel):
    stage: str
    category: str
    risk_score: int
    risk_level: str
    action: str
    reason: str
    message_text: str
    language: str
    requires_voice_output: bool
    recommended_channel: str
