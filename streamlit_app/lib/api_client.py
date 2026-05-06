"""Thin HTTP client for the FastAPI backend.

All Streamlit pages MUST go through this module — never hard-code the backend URL
or build requests inline. That way Phase 2 (Next.js) only has to mirror this contract.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT = httpx.Timeout(30.0, connect=5.0)


def health() -> dict:
    """Backend liveness probe."""
    with httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
        r = client.get("/health")
        r.raise_for_status()
        return r.json()


def get(path: str, **params) -> dict:
    with httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
        r = client.get(path, params=params)
        r.raise_for_status()
        return r.json()


def post(path: str, json: dict | None = None) -> dict:
    with httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
        r = client.post(path, json=json or {})
        r.raise_for_status()
        return r.json()


# ============================================================================
# TRIAGE API (PR #10)
# ============================================================================

def triage_classify(
    patient_profile: dict,
    fall_event: dict,
    elapsed_seconds: float,
    language: str = "en",
    patient_response: str | None = None,
) -> dict:
    """Classify a fall event using the triage engine.
    
    Returns:
        dict with keys: category, stage, action, reason, requires_voice_output,
        recommended_channel, messages
    """
    payload = {
        "patient_profile": patient_profile,
        "fall_event": fall_event,
        "elapsed_seconds": elapsed_seconds,
        "language": language,
        "patient_response": patient_response,
    }
    try:
        return post("/api/triage/classify", json=payload)
    except Exception:
        # Fallback to mock implementation for prototype
        return _mock_triage_classify(payload)


def _mock_triage_classify(payload: dict) -> dict:
    """Mock triage classification for prototype demonstration."""
    profile = payload.get("patient_profile", {})
    event = payload.get("fall_event", {})
    elapsed = payload.get("elapsed_seconds", 0)
    language = payload.get("language", "en")
    response = payload.get("patient_response", "")
    
    # Calculate risk level from profile
    risk_score = 0
    risk_reasons = []
    
    age = profile.get("age", 70)
    if age > 80:
        risk_score += 3
        risk_reasons.append("Advanced age (>80)")
    elif age > 65:
        risk_score += 1
        risk_reasons.append("Senior (65-80)")
    
    conditions = profile.get("conditions", [])
    if conditions:
        risk_score += len(conditions)
        risk_reasons.append(f"Medical conditions: {', '.join(conditions[:3])}")
    
    prev_falls = profile.get("previous_falls", 0)
    if prev_falls > 2:
        risk_score += 2
        risk_reasons.append(f"Fall history ({prev_falls})")
    
    mobility = profile.get("functional_status", {}).get("mobility", "")
    if mobility in ["bedridden", "wheelchair", "immobile"]:
        risk_score += 2
        risk_reasons.append("Limited mobility")
    
    cognition = profile.get("functional_status", {}).get("cognition", "")
    if cognition in ["mild impairment", "severe impairment"]:
        risk_score += 1
        risk_reasons.append("Cognitive impairment")
    
    # Determine risk level
    if risk_score >= 5:
        risk_level = "high"
    elif risk_score >= 3:
        risk_level = "moderate"
    else:
        risk_level = "low"
    
    # Check for red flags
    red_flags = []
    red_flag_fields = {
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
    
    for key, description in red_flag_fields.items():
        if event.get(key) or key in str(event).lower():
            red_flags.append(description)
    
    # Response normalization
    ok_responses = {"ok", "okay", "i_am_okay", "i_am_ok", "fine", "false_alarm", "i am okay", "i'm okay", "toi on", "tôi ổn"}
    help_responses = {"cannot_move", "need_help", "help", "cứu tôi", "can't move", "need help"}
    
    normalized_response = response.lower().strip() if response else ""
    
    # Decision logic
    PATIENT_CHECK_SECONDS = 3
    CARER_ALERT_SECONDS = 10
    EMERGENCY_ESCALATION_SECONDS = 20
    
    messages = {
        "en": {
            "emergency": "Emergency services have been contacted immediately due to critical symptoms.",
            "false_alarm": "Alert cancelled. Patient confirmed they are okay.",
            "monitoring": "Fall detected. Monitoring before patient check.",
            "patient_check": "Are you okay? Please respond if you can hear me.",
            "carer_alert": "Carer has been notified. Please check on the patient.",
            "emergency_escalation": "Escalating to emergency services due to no response.",
        },
        "vi": {
            "emergency": "Dịch vụ khẩn cấp đã được liên hệ ngay lập tức do các triệu chứng nghiêm trọng.",
            "false_alarm": "Đã hủy cảnh báo. Bệnh nhân xác nhận họ ổn.",
            "monitoring": "Đã phát hiện té ngã. Đang theo dõi trước khi kiểm tra bệnh nhân.",
            "patient_check": "Bạn có ổn không? Vui lòng phản hồi nếu bạn có thể nghe thấy tôi.",
            "carer_alert": "Ngưới chăm sóc đã được thông báo. Vui lòng kiểm tra bệnh nhân.",
            "emergency_escalation": "Đang chuyển lên dịch vụ khẩn cấp do không có phản hồi.",
        }
    }
    
    msg = messages.get(language, messages["en"])
    
    if red_flags:
        return {
            "category": "CAT_5",
            "stage": "critical_escalation",
            "action": "call_emergency_services",
            "reason": f"Red flag emergency: {', '.join(red_flags)}",
            "requires_voice_output": True,
            "recommended_channel": "emergency_services",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "messages": msg,
            "elapsed_seconds": elapsed,
            "next_check_seconds": None,
        }
    
    if normalized_response in ok_responses:
        return {
            "category": "CAT_1",
            "stage": "false_alarm_cancelled",
            "action": "cancel_alert",
            "reason": "Patient confirmed they are okay.",
            "requires_voice_output": True,
            "recommended_channel": "none",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "messages": msg,
            "elapsed_seconds": elapsed,
            "next_check_seconds": None,
        }
    
    if elapsed < PATIENT_CHECK_SECONDS:
        category = "CAT_2" if risk_level == "low" else "CAT_3"
        return {
            "category": category,
            "stage": "monitoring",
            "action": "monitor",
            "reason": f"Fall detected; monitoring before patient check. Risk: {risk_level}",
            "requires_voice_output": True,
            "recommended_channel": "voice_prompt",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "messages": msg,
            "elapsed_seconds": elapsed,
            "next_check_seconds": PATIENT_CHECK_SECONDS,
        }
    
    if elapsed < CARER_ALERT_SECONDS:
        category = "CAT_2" if risk_level == "low" else "CAT_3"
        return {
            "category": category,
            "stage": "patient_check",
            "action": "ask_patient_status",
            "reason": f"Patient check threshold reached. Risk: {risk_level}",
            "requires_voice_output": True,
            "recommended_channel": "voice_prompt",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "messages": msg,
            "elapsed_seconds": elapsed,
            "next_check_seconds": CARER_ALERT_SECONDS,
        }
    
    if elapsed < EMERGENCY_ESCALATION_SECONDS:
        if risk_level == "high":
            return {
                "category": "CAT_4",
                "stage": "carer_alert_escalated",
                "action": "alert_carer_escalate",
                "reason": f"High-risk patient with no response. Escalating to emergency. Risk: {risk_level}",
                "requires_voice_output": True,
                "recommended_channel": "carer_and_emergency",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_reasons": risk_reasons,
                "messages": msg,
                "elapsed_seconds": elapsed,
                "next_check_seconds": EMERGENCY_ESCALATION_SECONDS,
            }
        else:
            return {
                "category": "CAT_3",
                "stage": "carer_alert",
                "action": "alert_carer",
                "reason": f"Carer alert threshold reached. Risk: {risk_level}",
                "requires_voice_output": True,
                "recommended_channel": "carer",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_reasons": risk_reasons,
                "messages": msg,
                "elapsed_seconds": elapsed,
                "next_check_seconds": EMERGENCY_ESCALATION_SECONDS,
            }
    
    # Default: emergency escalation after timeout
    return {
        "category": "CAT_4",
        "stage": "emergency_escalation",
        "action": "escalate_emergency",
        "reason": f"No response after {EMERGENCY_ESCALATION_SECONDS}s. Risk: {risk_level}",
        "requires_voice_output": True,
        "recommended_channel": "emergency_services",
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_reasons": risk_reasons,
        "messages": msg,
        "elapsed_seconds": elapsed,
        "next_check_seconds": None,
    }


def get_triage_languages() -> list[dict]:
    """Get supported languages for triage."""
    return [
        {"code": "en", "name": "English", "flag": "🇬🇧"},
        {"code": "vi", "name": "Vietnamese", "flag": "🇻🇳"},
    ]


# ============================================================================
# PATIENT PROFILE API (PR #9)
# ============================================================================

def get_patient_profiles(
    risk_level: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    language: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Get patient profiles with optional filtering.
    
    Returns list of patient profiles with demographics, conditions, etc.
    """
    try:
        params = {
            "risk_level": risk_level,
            "age_min": age_min,
            "age_max": age_max,
            "language": language,
            "limit": limit,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        return get("/api/patients", **params)
    except Exception:
        # Return mock data for prototype
        return _get_mock_patient_profiles()


def get_patient_profile(patient_id: str) -> dict | None:
    """Get a single patient profile by ID."""
    try:
        return get(f"/api/patients/{patient_id}")
    except Exception:
        profiles = _get_mock_patient_profiles()
        for p in profiles:
            if p.get("id") == patient_id:
                return p
        return None


def _get_mock_patient_profiles() -> list[dict]:
    """Generate mock patient profiles for prototype."""
    import random
    
    # Use fixed seed for consistent data across reruns
    random.seed(42)
    
    conditions_pool = [
        ["osteoporosis", "arthritis"],
        ["cardiovascular disease", "stroke"],
        ["diabetes", "hypertension"],
        ["dementia", "osteoporosis"],
        ["parkinsons"],
        ["copd", "heart_failure"],
        [],
        ["arthritis"],
        ["diabetes"],
    ]
    
    medications_pool = [
        ["metformin", "aspirin"],
        ["lisinopril", "atorvastatin"],
        ["insulin", "metoprolol"],
        ["donepezil", "calcium"],
        ["levodopa"],
        ["albuterol", "furosemide"],
        [],
        ["ibuprofen"],
        ["metformin"],
    ]
    
    mobility_options = ["independent", "assisted", "wheelchair", "bedridden"]
    cognition_options = ["normal", "normal", "normal", "mild impairment", "severe impairment"]
    language_options = ["English", "Vietnamese", "Bilingual (VI/EN)"]
    
    profiles = []
    for i in range(12):
        age = random.randint(60, 95)
        conditions = random.choice(conditions_pool)
        medications = random.choice(medications_pool)
        mobility = random.choice(mobility_options)
        cognition = random.choice(cognition_options)
        language = random.choice(language_options)
        prev_falls = random.randint(0, 5)
        
        # Calculate risk
        risk_score = 0
        if age > 80:
            risk_score += 3
        elif age > 70:
            risk_score += 1
        risk_score += len(conditions) + prev_falls
        if mobility in ["bedridden", "wheelchair"]:
            risk_score += 2
        if cognition != "normal":
            risk_score += 1
        
        if risk_score >= 6:
            risk_level = "high"
        elif risk_score >= 3:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        profiles.append({
            "id": f"P{i+1:04X}",
            "name": f"Resident {i+1:03d}",
            "age": age,
            "sex": random.choice(["male", "female"]),
            "language": language,
            "conditions": conditions,
            "medications": medications,
            "functional_status": {
                "mobility": mobility,
                "cognition": cognition,
            },
            "previous_falls": prev_falls,
            "emergency_contacts": [
                {
                    "name": "Primary Contact",
                    "relationship": random.choice(["family", "friend", "carer"]),
                    "phone": f"04{random.randint(10000000, 99999999)}",
                }
            ],
            "risk_level": risk_level,
            "risk_score": risk_score,
            "room": f"{random.randint(1, 5)}{random.choice(['A', 'B', 'C'])}",
        })
    
    return profiles


# ============================================================================
# FALL DETECTION API (PR #9)
# ============================================================================

def detect_fall(video_data: bytes | str, source: str = "upload") -> dict:
    """Submit video for fall detection analysis.
    
    Args:
        video_data: Either bytes for upload or path to file
        source: 'upload', 'webcam', or 'sample'
    
    Returns:
        dict with detection results, confidence, keypoints, etc.
    """
    try:
        if isinstance(video_data, bytes):
            # Upload video file
            return post("/api/fall-detection/analyze", json={
                "video_bytes": video_data.decode('latin-1'),  # Simplified for demo
                "source": source,
            })
        else:
            # Analyze existing file
            return post("/api/fall-detection/analyze", json={
                "video_path": video_data,
                "source": source,
            })
    except Exception:
        # Mock response for prototype
        return _mock_fall_detection()


def get_fall_detection_status(job_id: str) -> dict:
    """Get status of a fall detection job."""
    try:
        return get(f"/api/fall-detection/status/{job_id}")
    except Exception:
        return {"status": "completed", "progress": 100}


def get_pose_keypoints() -> list[dict]:
    """Get MediaPipe pose keypoint definitions."""
    return [
        {"name": "Nose", "index": 0, "connection": ["Left Eye", "Right Eye"]},
        {"name": "Left Eye", "index": 2, "connection": ["Left Ear"]},
        {"name": "Right Eye", "index": 5, "connection": ["Right Ear"]},
        {"name": "Left Ear", "index": 7, "connection": []},
        {"name": "Right Ear", "index": 8, "connection": []},
        {"name": "Left Shoulder", "index": 11, "connection": ["Right Shoulder", "Left Elbow", "Left Hip"]},
        {"name": "Right Shoulder", "index": 12, "connection": ["Right Elbow", "Right Hip"]},
        {"name": "Left Elbow", "index": 13, "connection": ["Left Wrist"]},
        {"name": "Right Elbow", "index": 14, "connection": ["Right Wrist"]},
        {"name": "Left Wrist", "index": 15, "connection": []},
        {"name": "Right Wrist", "index": 16, "connection": []},
        {"name": "Left Hip", "index": 23, "connection": ["Right Hip", "Left Knee"]},
        {"name": "Right Hip", "index": 24, "connection": ["Right Knee"]},
        {"name": "Left Knee", "index": 25, "connection": ["Left Ankle"]},
        {"name": "Right Knee", "index": 26, "connection": ["Right Ankle"]},
        {"name": "Left Ankle", "index": 27, "connection": []},
        {"name": "Right Ankle", "index": 28, "connection": []},
    ]


def _mock_fall_detection() -> dict:
    """Generate mock fall detection results."""
    import random
    
    random.seed(42)
    
    is_fall = random.random() > 0.5
    confidence = random.uniform(0.7, 0.98) if is_fall else random.uniform(0.1, 0.4)
    
    # Generate mock keypoints
    keypoints = []
    for i in range(33):  # MediaPipe has 33 keypoints
        keypoints.append({
            "x": random.uniform(0, 640),
            "y": random.uniform(0, 480),
            "z": random.uniform(-1, 1),
            "visibility": random.uniform(0.5, 1.0),
            "presence": random.uniform(0.5, 1.0),
        })
    
    return {
        "detected": is_fall,
        "confidence": round(confidence, 3),
        "label": "Fall" if is_fall else "No Fall",
        "long_lie_probability": round(random.uniform(0, 0.8), 3) if is_fall else 0.0,
        "keypoints": keypoints,
        "processing_time_ms": random.randint(50, 200),
        "model_version": "fallvision_baseline_v1",
    }


def get_sample_videos() -> list[dict]:
    """Get list of sample videos for demo."""
    return [
        {"id": "sample_001", "name": "Fall Example 1", "duration": "0:05", "label": "Fall"},
        {"id": "sample_002", "name": "Fall Example 2", "duration": "0:04", "label": "Fall"},
        {"id": "sample_003", "name": "No Fall - Walking", "duration": "0:06", "label": "No Fall"},
        {"id": "sample_004", "name": "No Fall - Sitting", "duration": "0:05", "label": "No Fall"},
    ]


# ============================================================================
# DATABASE API (PR #11)
# ============================================================================

def get_database_schema() -> dict:
    """Get SurrealDB schema definition."""
    try:
        return get("/api/db/schema")
    except Exception:
        return _get_mock_schema()


def get_residents() -> list[dict]:
    """Get all residents from database."""
    try:
        return get("/api/db/residents")
    except Exception:
        # Return mock residents based on patient profiles
        profiles = _get_mock_patient_profiles()
        return [
            {
                "id": f"resident:{p['id']}",
                "name": p["name"],
                "room": p["room"],
                "notes": f"Risk level: {p['risk_level']}. Conditions: {', '.join(p['conditions']) if p['conditions'] else 'None'}",
                "created_at": "2024-01-15T08:00:00Z",
                "updated_at": "2024-01-15T08:00:00Z",
            }
            for p in profiles[:8]
        ]


def get_fall_events(limit: int = 20) -> list[dict]:
    """Get recent fall events."""
    try:
        return get("/api/db/fall-events", limit=limit)
    except Exception:
        return _get_mock_fall_events()


def get_caretakers() -> list[dict]:
    """Get all caretakers."""
    try:
        return get("/api/db/caretakers")
    except Exception:
        return [
            {"id": "caretaker:001", "name": "Sarah Johnson", "email": "sarah.j@watch4u.com", "phone": "0412345678"},
            {"id": "caretaker:002", "name": "Michael Chen", "email": "michael.c@watch4u.com", "phone": "0423456789"},
            {"id": "caretaker:003", "name": "Lisa Nguyen", "email": "lisa.n@watch4u.com", "phone": "0434567890"},
        ]


def _get_mock_schema() -> dict:
    """Return SurrealDB schema documentation."""
    return {
        "tables": [
            {
                "name": "resident",
                "type": "SCHEMAFULL",
                "fields": [
                    {"name": "name", "type": "string", "required": True},
                    {"name": "room", "type": "option<string>", "required": False},
                    {"name": "notes", "type": "option<string>", "required": False},
                    {"name": "created_at", "type": "datetime", "default": "time::now()"},
                    {"name": "updated_at", "type": "datetime", "default": "time::now()"},
                ],
                "indexes": [],
            },
            {
                "name": "caretaker",
                "type": "SCHEMAFULL",
                "fields": [
                    {"name": "name", "type": "string", "required": True},
                    {"name": "email", "type": "option<string>", "required": False},
                    {"name": "phone", "type": "option<string>", "required": False},
                    {"name": "created_at", "type": "datetime", "default": "time::now()"},
                ],
                "indexes": [],
            },
            {
                "name": "cares_for",
                "type": "RELATION",
                "from": "caretaker",
                "to": "resident",
                "fields": [
                    {"name": "created_at", "type": "datetime", "default": "time::now()"},
                ],
            },
            {
                "name": "device",
                "type": "SCHEMAFULL",
                "fields": [
                    {"name": "resident", "type": "record<resident>", "required": True},
                    {"name": "label", "type": "string", "required": True},
                    {"name": "external_id", "type": "option<string>", "required": False},
                    {"name": "created_at", "type": "datetime", "default": "time::now()"},
                ],
                "indexes": [],
            },
            {
                "name": "fall_event",
                "type": "SCHEMAFULL",
                "fields": [
                    {"name": "resident", "type": "record<resident>", "required": True},
                    {"name": "detected_at", "type": "datetime", "default": "time::now()"},
                    {"name": "confidence", "type": "option<float>", "required": False},
                    {"name": "severity_label", "type": "option<string>", "required": False},
                    {"name": "source", "type": "string", "default": "'camera'"},
                    {"name": "false_alarm", "type": "bool", "default": "false"},
                    {"name": "acknowledged_at", "type": "option<datetime>", "required": False},
                    {"name": "acknowledged_by", "type": "option<record<caretaker>>", "required": False},
                    {"name": "clip_uri", "type": "option<string>", "required": False},
                    {"name": "payload", "type": "option<object>", "required": False},
                ],
                "indexes": [
                    {"name": "idx_fall_resident_time", "fields": ["resident", "detected_at"]},
                ],
            },
        ],
    }


def _get_mock_fall_events() -> list[dict]:
    """Generate mock fall events."""
    import random
    from datetime import datetime, timedelta
    
    random.seed(42)
    
    events = []
    residents = get_residents()
    
    for i in range(15):
        resident = random.choice(residents)
        detected_at = datetime.now() - timedelta(hours=random.randint(1, 168))
        confidence = round(random.uniform(0.75, 0.99), 3)
        severity = random.choice(["CAT_1", "CAT_2", "CAT_3", "CAT_4", "CAT_5"])
        source = random.choice(["camera", "wifi_csi", "wearable"])
        is_false_alarm = random.random() < 0.1
        
        events.append({
            "id": f"fall_event:{i+1:04d}",
            "resident": resident["id"],
            "resident_name": resident["name"],
            "detected_at": detected_at.isoformat(),
            "confidence": confidence,
            "severity_label": severity,
            "source": source,
            "false_alarm": is_false_alarm,
            "acknowledged_at": (detected_at + timedelta(minutes=random.randint(1, 10))).isoformat() if not is_false_alarm else None,
            "acknowledged_by": f"caretaker:{random.randint(1, 3):03d}" if not is_false_alarm else None,
            "clip_uri": f"/clips/fall_{i+1:04d}.mp4" if source == "camera" else None,
        })
    
    return sorted(events, key=lambda x: x["detected_at"], reverse=True)


# ============================================================================
# DATA PIPELINE API (PR #9)
# ============================================================================

def get_preprocessing_stats() -> dict:
    """Get data preprocessing pipeline statistics."""
    try:
        return get("/api/data/preprocessing-stats")
    except Exception:
        return {
            "fallvision": {
                "raw_videos": 240,
                "processed_frames": 15234,
                "train_samples": 12187,
                "val_samples": 3047,
                "categories": {"Fall": 120, "No_Fall": 120},
            },
            "omnifall": {
                "raw_videos": 150,
                "processed_frames": 8900,
                "train_samples": 7120,
                "val_samples": 1780,
                "categories": {"Fall": 75, "No_Fall": 75},
            },
            "synthetic_profiles": {
                "generated": 500,
                "high_risk": 180,
                "moderate_risk": 220,
                "low_risk": 100,
            },
        }


def get_feature_extraction_info() -> dict:
    """Get information about feature extraction pipeline."""
    return {
        "pose_model": "MediaPipe Pose Landmarker Lite",
        "keypoints": 33,
        "features": [
            "head_y", "hip_y", "ankle_y",
            "body_height", "body_width", "height_width_ratio",
            "torso_angle_degrees", "mean_confidence",
        ],
        "window_size": 30,  # frames
        "overlap": 0.5,
    }
