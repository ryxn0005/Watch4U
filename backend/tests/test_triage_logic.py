from app.services.triage.triage_logic import (
    CARER_ALERT_SECONDS,
    EMERGENCY_ESCALATION_SECONDS,
    run_triage,
)


def test_low_risk_okay_response_cancels_alert():
    result = run_triage(
        patient_profile={"age": 70},
        fall_event={"fall_detected": True},
        elapsed_seconds=CARER_ALERT_SECONDS,
        patient_response="okay",
    )

    assert result["category"] == "CAT_1"
    assert result["stage"] == "false_alarm_cancelled"
    assert result["action"] == "cancel_alert"
    assert result["risk_level"] == "low"


def test_medium_risk_no_response_notifies_carer_in_vietnamese():
    result = run_triage(
        patient_profile={
            "age": 79,
            "previous_fall_history": True,
            "limited_mobility": True,
            "lives_alone": True,
        },
        fall_event={"fall_detected": True},
        elapsed_seconds=CARER_ALERT_SECONDS,
        language="vi",
    )

    assert result["category"] == "CAT_3"
    assert result["risk_score"] == 5
    assert result["risk_level"] == "medium"
    assert result["action"] == "notify_carer"
    assert result["language"] == "vi"
    assert "Watch4U" in result["message_text"]


def test_red_flag_overrides_to_cat_5():
    result = run_triage(
        patient_profile={"age": 70},
        fall_event={"fall_detected": True, "head_impact": True},
        elapsed_seconds=1,
    )

    assert result["category"] == "CAT_5"
    assert result["stage"] == "critical_escalation"
    assert result["recommended_channel"] == "emergency_services"


def test_prolonged_no_response_escalates_to_cat_4():
    result = run_triage(
        patient_profile={"age": 75},
        fall_event={"fall_detected": True},
        elapsed_seconds=EMERGENCY_ESCALATION_SECONDS,
    )

    assert result["category"] == "CAT_4"
    assert result["stage"] == "emergency_escalation"
    assert result["recommended_channel"] == "emergency_contact"
