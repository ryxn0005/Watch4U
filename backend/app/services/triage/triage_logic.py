"""Rule-based staged escalation engine for fall triage.

The timing constants below are compressed for prototype demonstrations.
They are not clinical standards.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.triage.multilingual_response import get_message

PATIENT_CHECK_SECONDS = 3
CARER_ALERT_SECONDS = 10
EMERGENCY_ESCALATION_SECONDS = 20

OK_RESPONSES = {"ok", "okay", "i_am_okay", "i_am_ok", "fine", "false_alarm"}
HELP_RESPONSES = {"cannot_move", "need_help"}
RESPONSE_ALIASES = {
    "i am okay": "i_am_okay",
    "i'm okay": "i_am_okay",
    "toi on": "i_am_okay",
    "tôi ổn": "i_am_okay",
    "can not move": "cannot_move",
    "can't move": "cannot_move",
    "need help": "need_help",
    "help": "need_help",
    "cứu tôi": "need_help",
}

RED_FLAG_FIELDS = {
    "unconscious": "patient unconscious",
    "head_impact": "head impact",
    "headImpact": "head impact",
    "severe_pain": "severe pain",
    "severePain": "severe pain",
    "bleeding": "bleeding",
    "chest_pain": "chest pain",
    "chestPain": "chest pain",
    "breathing_difficulty": "breathing difficulty",
    "breathingDifficulty": "breathing difficulty",
}


def run_triage(
    patient_profile: Mapping[str, Any] | Any,
    fall_event: Mapping[str, Any] | Any,
    elapsed_seconds: int | float,
    language: str = "en",
    patient_response: str | None = None,
) -> dict[str, Any]:
    """Evaluate a fall event and return a JSON-compatible triage decision."""
    profile = _as_mapping(patient_profile)
    event = _as_mapping(fall_event)
    elapsed = max(float(elapsed_seconds), 0.0)
    normalized_response = _normalize_response(patient_response)

    risk_score, risk_reasons = calculate_risk_score(profile)
    risk_level = risk_level_from_score(risk_score)
    red_flags = detect_red_flags(event, normalized_response)

    if red_flags:
        decision = _decision(
            stage="critical_escalation",
            category="CAT_5",
            action="call_emergency_services",
            reason="Red flag emergency: " + ", ".join(red_flags),
            requires_voice_output=True,
            recommended_channel="emergency_services",
        )
    elif normalized_response in OK_RESPONSES:
        decision = _decision(
            stage="false_alarm_cancelled",
            category="CAT_1",
            action="cancel_alert",
            reason="Patient confirmed they are okay.",
            requires_voice_output=True,
            recommended_channel="none",
        )
    elif elapsed < PATIENT_CHECK_SECONDS:
        decision = _decision(
            stage="monitoring",
            category="CAT_2" if risk_level == "low" else "CAT_3",
            action="monitor",
            reason=_risk_reason("Fall detected; monitoring before patient check.", risk_reasons),
            requires_voice_output=True,
            recommended_channel="voice_prompt",
        )
    elif elapsed < CARER_ALERT_SECONDS:
        decision = _decision(
            stage="patient_check",
            category="CAT_2" if risk_level == "low" else "CAT_3",
            action="ask_patient_status",
            reason=_risk_reason("Patient check threshold reached.", risk_reasons),
            requires_voice_output=True,
            recommended_channel="voice_prompt",
        )
    elif elapsed < EMERGENCY_ESCALATION_SECONDS:
        if risk_level == "high":
            decision = _decision(
                stage="carer_alert",
                category="CAT_4",
                action="urgent_carer_or_emergency_contact",
                reason=_risk_reason("High-risk profile after fall.", risk_reasons),
                requires_voice_output=False,
                recommended_channel="emergency_contact",
            )
        else:
            decision = _decision(
                stage="carer_alert" if normalized_response is None or risk_level == "medium" else "patient_recheck",
                category="CAT_3" if normalized_response is None or risk_level == "medium" else "CAT_2",
                action="notify_carer" if normalized_response is None or risk_level == "medium" else "monitor_and_recheck",
                reason=_risk_reason("Carer alert threshold reached.", risk_reasons),
                requires_voice_output=False if normalized_response is None or risk_level == "medium" else True,
                recommended_channel="carer_app" if normalized_response is None or risk_level == "medium" else "voice_prompt",
            )
    elif normalized_response is None:
        decision = _decision(
            stage="emergency_escalation",
            category="CAT_4",
            action="urgent_carer_or_emergency_contact",
            reason=_risk_reason("Prolonged no response after fall.", risk_reasons),
            requires_voice_output=True,
            recommended_channel="emergency_contact",
        )
    elif risk_level == "high":
        decision = _decision(
            stage="carer_alert",
            category="CAT_4",
            action="urgent_carer_or_emergency_contact",
            reason=_risk_reason("High-risk profile remains escalated after patient response.", risk_reasons),
            requires_voice_output=False,
            recommended_channel="emergency_contact",
        )
    else:
        decision = _decision(
            stage="patient_recheck",
            category="CAT_2" if risk_level == "low" else "CAT_3",
            action="monitor_and_recheck" if risk_level == "low" else "notify_carer",
            reason=_risk_reason("Patient responded without red flags.", risk_reasons),
            requires_voice_output=True,
            recommended_channel="voice_prompt" if risk_level == "low" else "carer_app",
        )

    message_text, normalized_language = get_message(decision["stage"], language)
    return {
        "stage": decision["stage"],
        "category": decision["category"],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "action": decision["action"],
        "reason": decision["reason"],
        "message_text": message_text,
        "language": normalized_language,
        "requires_voice_output": decision["requires_voice_output"],
        "recommended_channel": decision["recommended_channel"],
    }


def calculate_risk_score(patient_profile: Mapping[str, Any]) -> tuple[int, list[str]]:
    """Calculate the configured patient risk score."""
    score = 0
    reasons: list[str] = []
    age = _get_int(patient_profile, "age")

    if age >= 85:
        score += 2
        reasons.append("age >= 85")
    elif 75 <= age <= 84:
        score += 1
        reasons.append("age 75-84")

    risk_checks = [
        (2, "previous fall history", _has_any(patient_profile, "previous_fall_history", "fall_history", "previous_falls")),
        (2, "stroke history", _has_any(patient_profile, "stroke_history", "history_of_stroke")),
        (2, "cognitive impairment or dementia", _has_any(patient_profile, "cognitive_impairment", "dementia")),
        (1, "limited mobility/walker/wheelchair", _has_limited_mobility(patient_profile)),
        (3, "blood thinner medication", _has_blood_thinner(patient_profile)),
        (2, "osteoporosis", _has_any(patient_profile, "osteoporosis")),
        (1, "lives alone", _has_any(patient_profile, "lives_alone")),
    ]

    for points, reason, present in risk_checks:
        if present:
            score += points
            reasons.append(reason)

    return score, reasons


def risk_level_from_score(risk_score: int) -> str:
    if risk_score <= 3:
        return "low"
    if risk_score <= 6:
        return "medium"
    return "high"


def detect_red_flags(fall_event: Mapping[str, Any], patient_response: str | None) -> list[str]:
    red_flags: list[str] = []

    for field, reason in RED_FLAG_FIELDS.items():
        if _is_truthy(fall_event.get(field)):
            red_flags.append(reason)

    for value in _list_values(fall_event.get("red_flags")):
        normalized_value = _normalize_key(value)
        if normalized_value in RED_FLAG_FIELDS:
            red_flags.append(RED_FLAG_FIELDS[normalized_value])
        elif normalized_value in {"head impact", "severe pain", "chest pain", "breathing difficulty"}:
            red_flags.append(normalized_value)

    if patient_response in HELP_RESPONSES:
        red_flags.append(f"patient response: {patient_response}")

    return sorted(set(red_flags))


def _decision(
    stage: str,
    category: str,
    action: str,
    reason: str,
    requires_voice_output: bool,
    recommended_channel: str,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "category": category,
        "action": action,
        "reason": reason,
        "requires_voice_output": requires_voice_output,
        "recommended_channel": recommended_channel,
    }


def _as_mapping(value: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return {}


def _get_int(data: Mapping[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(data.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _has_any(data: Mapping[str, Any], *keys: str) -> bool:
    return any(_is_truthy(data.get(key)) for key in keys)


def _has_limited_mobility(data: Mapping[str, Any]) -> bool:
    if _has_any(data, "limited_mobility", "uses_walker", "uses_wheelchair", "wheelchair"):
        return True

    mobility = _normalize_key(data.get("mobility"))
    mobility_status = _normalize_key(data.get("mobility_status"))
    return any(term in mobility or term in mobility_status for term in ("limited", "walker", "wheelchair"))


def _has_blood_thinner(data: Mapping[str, Any]) -> bool:
    if _has_any(data, "blood_thinner_medication", "blood_thinners", "anticoagulant"):
        return True

    medications = " ".join(_normalize_key(value) for value in _list_values(data.get("medications")))
    return any(term in medications for term in ("blood thinner", "warfarin", "apixaban", "rivaroxaban", "anticoagulant"))


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "no", "none", "0", "unknown"}
    if isinstance(value, (list, tuple, set)):
        return len(value) > 0
    return bool(value)


def _list_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _normalize_response(patient_response: str | None) -> str | None:
    if patient_response is None:
        return None

    normalized = _normalize_key(patient_response).replace(" ", "_")
    alias_key = str(patient_response).strip().lower()
    return RESPONSE_ALIASES.get(alias_key, normalized)


def _risk_reason(base_reason: str, risk_reasons: list[str]) -> str:
    if not risk_reasons:
        return f"{base_reason} Risk profile: no configured risk factors."
    return f"{base_reason} Risk profile: {', '.join(risk_reasons)}."
