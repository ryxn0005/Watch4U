# Triage Logic

Jayce - Clinical severity / Cat 1-5 logic.

This component provides a rule-based, risk-adjusted staged escalation engine for fall events. It is intentionally pure Python and does not call STT, TTS, SMS, or emergency APIs. The API returns `message_text` plus `requires_voice_output` so another module can pass the text into a future TTS provider.

## Demo Timing Constants

The timing thresholds in `triage_logic.py` are compressed for prototype demonstration only. They are not clinical standards.

- `PATIENT_CHECK_SECONDS = 3`
- `CARER_ALERT_SECONDS = 10`
- `EMERGENCY_ESCALATION_SECONDS = 20`

## Main Function

```python
from app.services.triage import run_triage

result = run_triage(
    patient_profile={"age": 87, "previous_fall_history": True},
    fall_event={"fall_detected": True, "head_impact": False},
    elapsed_seconds=10,
    language="vi",
    patient_response=None,
)
```

## API

When `backend/main.py` includes the router, frontend/backend clients can call:

`POST /api/triage/evaluate`

Example request:

```json
{
  "patient_profile": {
    "age": 87,
    "previous_fall_history": true,
    "stroke_history": true,
    "cognitive_impairment": false,
    "limited_mobility": true,
    "blood_thinner_medication": true,
    "osteoporosis": false,
    "lives_alone": true
  },
  "fall_event": {
    "fall_detected": true,
    "head_impact": false,
    "severe_pain": false,
    "bleeding": false,
    "chest_pain": false,
    "breathing_difficulty": false
  },
  "elapsed_seconds": 10,
  "language": "vi",
  "patient_response": null
}
```

The response contains:

- `stage`
- `category`
- `risk_score`
- `risk_level`
- `action`
- `reason`
- `message_text`
- `language`
- `requires_voice_output`
- `recommended_channel`
