"""Triage demo (Jayce)."""
import json

import streamlit as st

from lib.api_client import post

st.set_page_config(page_title="Triage - Watch4U", page_icon="🩺")

st.title("Triage")
st.caption("Owner: Jayce · backend/app/services/triage/")

# Backend connectivity check
try:
    from lib.api_client import health
    health_status = health()
    st.success(f"✅ Backend connected: {health_status.get('status', 'unknown')}")
except Exception as e:
    st.error(f"❌ Backend connection failed: {e}")
    st.stop()

st.markdown("---")

# Load sample profiles
sample_profiles = [
    {
        "name": "Elderly Patient - Low Risk",
        "profile": {
            "age": 75,
            "previous_fall_history": False,
            "stroke_history": False,
            "cognitive_impairment": False,
            "dementia": False,
            "limited_mobility": False,
            "uses_walker": False,
            "uses_wheelchair": False,
            "blood_thinner_medication": False,
            "osteoporosis": False,
            "lives_alone": False,
        },
    },
    {
        "name": "High-Risk Patient - On Blood Thinners",
        "profile": {
            "age": 82,
            "previous_fall_history": True,
            "stroke_history": True,
            "cognitive_impairment": False,
            "dementia": False,
            "limited_mobility": True,
            "uses_walker": True,
            "uses_wheelchair": False,
            "blood_thinner_medication": True,
            "osteoporosis": True,
            "lives_alone": True,
        },
    },
    {
        "name": "Dementia Patient - Severe Risk",
        "profile": {
            "age": 78,
            "previous_fall_history": True,
            "stroke_history": False,
            "cognitive_impairment": True,
            "dementia": True,
            "limited_mobility": True,
            "uses_walker": False,
            "uses_wheelchair": True,
            "blood_thinner_medication": False,
            "osteoporosis": False,
            "lives_alone": True,
        },
    },
]

# Sidebar for patient selection
st.sidebar.header("Select Patient Profile")
selected_profile_name = st.sidebar.selectbox(
    "Patient Type", [p["name"] for p in sample_profiles]
)
selected_profile = next(
    p for p in sample_profiles if p["name"] == selected_profile_name
)["profile"]

# Display patient profile
st.sidebar.subheader("Patient Details")
for key, value in selected_profile.items():
    st.sidebar.text(f"{key}: {value}")

st.markdown("### Simulate Fall Event")

# Fall event configuration
col1, col2 = st.columns(2)

with col1:
    st.subheader("Injury Indicators")
    unconscious = st.checkbox("Unconscious", value=False)
    head_impact = st.checkbox("Head Impact", value=False)
    severe_pain = st.checkbox("Severe Pain", value=False)
    bleeding = st.checkbox("Bleeding", value=False)

with col2:
    st.subheader("Medical Emergency Signs")
    chest_pain = st.checkbox("Chest Pain", value=False)
    breathing_difficulty = st.checkbox("Breathing Difficulty", value=False)
    
st.subheader("Additional Context")
elapsed_seconds = st.slider("Time since fall (seconds)", 0, 300, 30)
patient_response = st.text_area(
    "Patient Response (if conscious)",
    value="I'm okay, just a bit shaken.",
    placeholder="Enter patient's response...",
)

language = st.selectbox("Response Language", ["en", "vi"], format_func=lambda x: "English" if x == "en" else "Vietnamese")

if st.button("🚨 Evaluate Triage", type="primary", use_container_width=True):
    with st.spinner("Analyzing triage category..."):
        # Build request
        fall_event = {
            "fall_detected": True,
            "unconscious": unconscious,
            "head_impact": head_impact,
            "severe_pain": severe_pain,
            "bleeding": bleeding,
            "chest_pain": chest_pain,
            "breathing_difficulty": breathing_difficulty,
            "red_flags": [],
            "context": {},
        }
        
        payload = {
            "patient_profile": selected_profile,
            "fall_event": fall_event,
            "elapsed_seconds": elapsed_seconds,
            "language": language,
            "patient_response": patient_response if patient_response else None,
        }
        
        try:
            result = post("/api/triage/evaluate", json=payload)
            
            # Display results
            st.markdown("---")
            st.markdown("### 🏥 Triage Result")
            
            # Category badge
            category_colors = {
                "C1": "🔴",
                "C2": "🟠", 
                "C3": "🟡",
                "C4": "🟢",
                "C5": "🔵",
            }
            cat = result.get("category", "UNKNOWN")
            emoji = category_colors.get(cat, "⚪")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Category", f"{emoji} {cat}")
            with col2:
                st.metric("Risk Score", result.get("risk_score", 0))
            with col3:
                st.metric("Risk Level", result.get("risk_level", "unknown"))
            
            # Action and message
            st.info(f"**Recommended Action:** {result.get('action', 'N/A')}")
            st.success(f"**Patient Message ({language}):** {result.get('message_text', 'N/A')}")
            
            # Escalation info
            with st.expander("📋 Full Response"):
                st.json(result)
                
        except Exception as e:
            st.error(f"API call failed: {e}")
            st.info("Make sure the backend is running at http://localhost:8000")

st.markdown("---")
st.caption("This demo connects to `/api/triage/evaluate` endpoint")
