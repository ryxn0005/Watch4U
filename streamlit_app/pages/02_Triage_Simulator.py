"""Triage Simulator - Interactive CAT 1-5 classification with staged escalation."""
from __future__ import annotations

import time

import streamlit as st

from lib import api_client

st.set_page_config(
    page_title="Triage Simulator",
    page_icon="🚨",
    layout="wide",
)

st.title("🚨 Triage Simulator")
st.caption("PR #10: Multilingual Triage Engine with Staged Escalation")

if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False
if "current_time" not in st.session_state:
    st.session_state.current_time = 0.0
if "triage_result" not in st.session_state:
    st.session_state.triage_result = None
if "patient_response" not in st.session_state:
    st.session_state.patient_response = ""

profiles = api_client.get_patient_profiles()

st.divider()

config_col, patient_col = st.columns([1, 1])

with config_col:
    st.subheader("⚙️ Simulation Configuration")
    
    languages = api_client.get_triage_languages()
    language_options = {f"{lang['flag']} {lang['name']}": lang["code"] for lang in languages}
    selected_language = st.selectbox(
        "Response Language",
        options=list(language_options.keys()),
        index=0,
    )
    lang_code = language_options[selected_language]
    
    st.divider()
    
    st.subheader("👤 Select Patient Profile")
    
    profile_options = {f"{p['name']} ({p['risk_level'].upper()} risk)": p for p in profiles}
    selected_profile_label = st.selectbox(
        "Patient",
        options=list(profile_options.keys()),
        index=0,
    )
    selected_profile = profile_options[selected_profile_label]
    
    with st.expander("View Patient Details"):
        st.json(selected_profile)

with patient_col:
    st.subheader("💥 Fall Event Details")
    
    st.markdown("### Red Flags (Immediate CAT-5)")
    
    red_flag_cols = st.columns(2)
    
    with red_flag_cols[0]:
        unconscious = st.checkbox("😵 Unconscious / Unresponsive")
        head_impact = st.checkbox("🤕 Head Impact")
        severe_pain = st.checkbox("😰 Severe Pain")
    
    with red_flag_cols[1]:
        bleeding = st.checkbox("🩸 Bleeding")
        chest_pain = st.checkbox("💔 Chest Pain")
        breathing_difficulty = st.checkbox("😮‍💨 Breathing Difficulty")
    
    fall_event = {
        "unconscious": unconscious,
        "head_impact": head_impact,
        "severe_pain": severe_pain,
        "bleeding": bleeding,
        "chest_pain": chest_pain,
        "breathing_difficulty": breathing_difficulty,
        "detected_at": "2024-01-01T00:00:00Z",
        "source": "camera",
    }
    
    st.divider()
    
    st.markdown("### 🎙️ Patient Response Simulation")
    
    response_options = {
        "No Response": "",
        "✅ I'm okay (English)": "i am okay",
        "✅ Tôi ổn (Vietnamese)": "tôi ổn",
        "🆘 Cannot move (English)": "cannot_move",
        "🆘 Cứu tôi (Vietnamese)": "cứu tôi",
    }
    
    patient_response = st.selectbox(
        "Simulated Patient Response",
        options=list(response_options.keys()),
        index=0,
    )
    st.session_state.patient_response = response_options[patient_response]

st.divider()

st.subheader("▶️ Run Simulation")

sim_col1, sim_col2 = st.columns([1, 3])

with sim_col1:
    if st.button("🚀 Start Simulation", type="primary", use_container_width=True):
        st.session_state.simulation_running = True
        st.session_state.current_time = 0.0
        st.rerun()
    
    if st.button("🛑 Stop / Reset", use_container_width=True):
        st.session_state.simulation_running = False
        st.session_state.current_time = 0.0
        st.session_state.triage_result = None
        st.rerun()

with sim_col2:
    if st.session_state.simulation_running:
        elapsed = st.session_state.current_time
        
        result = api_client.triage_classify(
            patient_profile=selected_profile,
            fall_event=fall_event,
            elapsed_seconds=elapsed,
            language=lang_code,
            patient_response=st.session_state.patient_response if elapsed > 3 else "",
        )
        st.session_state.triage_result = result
        
        progress_pct = min(elapsed / 25, 1.0)
        st.progress(progress_pct, text=f"⏱️ Elapsed: {elapsed:.1f}s")
        
        st.session_state.current_time += 0.5
        
        if elapsed < 25:
            time.sleep(0.5)
            st.rerun()
        else:
            st.session_state.simulation_running = False
    else:
        st.progress(0, text="⏱️ Ready to start")

st.divider()

st.subheader("📊 Triage Results")

if st.session_state.triage_result:
    result = st.session_state.triage_result
    
    result_cols = st.columns([1, 2])
    
    with result_cols[0]:
        category = result.get("category", "UNKNOWN")
        stage = result.get("stage", "unknown")
        
        cat_colors = {
            "CAT_1": "#44aa44",
            "CAT_2": "#88cc44",
            "CAT_3": "#ffaa00",
            "CAT_4": "#ff6600",
            "CAT_5": "#ff0000",
        }
        cat_color = cat_colors.get(category, "#888888")
        
        st.markdown(f"""
        <div style="background-color: {cat_color}20; border: 2px solid {cat_color}; 
                    border-radius: 10px; padding: 20px; text-align: center;">
            <h2 style="color: {cat_color}; margin: 0;">{category}</h2>
            <p style="font-size: 1.2em; margin: 10px 0;"><strong>{stage.replace('_', ' ').title()}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Action:** {result.get('action', 'N/A').replace('_', ' ').title()}")
        st.markdown(f"**Channel:** {result.get('recommended_channel', 'N/A').replace('_', ' ').title()}")
        st.markdown(f"**Risk Level:** {result.get('risk_level', 'N/A').upper()}")
        st.markdown(f"**Risk Score:** {result.get('risk_score', 'N/A')}")
    
    with result_cols[1]:
        st.markdown("### 📝 Decision Rationale")
        st.info(result.get("reason", "No rationale available"))
        
        if result.get("risk_reasons"):
            st.markdown("### 📋 Risk Factors")
            for reason in result.get("risk_reasons"):
                st.markdown(f"- {reason}")
        
        if result.get("messages"):
            st.markdown("### 🔊 Voice Prompt")
            messages = result.get("messages", {})
            if isinstance(messages, dict):
                for lang, msg in messages.items():
                    st.markdown(f"**{lang.upper()}:** {msg}")

st.divider()

st.subheader("⏱️ Staged Escalation Timeline")

timeline_data = [
    ("0s", "🎥", "Fall Detected", "System begins monitoring"),
    ("3s", "🗣️", "Patient Check", "Voice prompt: 'Are you okay?'") ,
    ("10s", "📱", "Carer Alert", "Notification sent to carer"),
    ("20s", "🚑", "Emergency Escalation", "Emergency services contacted"),
]

timeline_cols = st.columns(4)

for idx, (time_mark, emoji, label, desc) in enumerate(timeline_data):
    with timeline_cols[idx]:
        active = False
        if st.session_state.triage_result:
            elapsed = st.session_state.triage_result.get("elapsed_seconds", 0)
            time_val = int(time_mark.replace("s", ""))
            active = elapsed >= time_val
        
        bg_color = "#44aa4420" if active else "#33333320"
        border_color = "#44aa44" if active else "#888888"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <h3 style="margin: 0;">{emoji}</h3>
            <h4 style="margin: 5px 0;">{time_mark}</h4>
            <p style="font-weight: bold; margin: 5px 0;">{label}</p>
            <p style="font-size: 0.8em; color: #666;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

st.caption("📚 **CAT Classification:** CAT 1 (False Alarm) → CAT 2 (Low Risk) → CAT 3 (Moderate) → CAT 4 (High Risk) → CAT 5 (Emergency)")
