"""Full System Flow - End-to-end fall detection and response workflow."""
from __future__ import annotations

import time

import streamlit as st

from lib import api_client

st.set_page_config(
    page_title="Full System Flow",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🔄 Full System Flow")
st.subheader("Complete Fall Detection & Response Workflow")
st.caption("PR #9 + #10: From Detection to Escalation")

if "flow_step" not in st.session_state:
    st.session_state.flow_step = 0
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "fall_detected" not in st.session_state:
    st.session_state.fall_detected = False
if "patient_response" not in st.session_state:
    st.session_state.patient_response = None
if "triage_result" not in st.session_state:
    st.session_state.triage_result = None
if "simulation_timer" not in st.session_state:
    st.session_state.simulation_timer = 0
if "patient_selector_key" not in st.session_state:
    st.session_state.patient_selector_key = 0

st.divider()

progress_cols = st.columns(5)
steps = [
    ("1", "👁️ Detection", st.session_state.flow_step >= 0),
    ("2", "🚨 Alert", st.session_state.flow_step >= 1),
    ("3", "🗣️ Check", st.session_state.flow_step >= 2),
    ("4", "📊 Triage", st.session_state.flow_step >= 3),
    ("5", "⏱️ Escalate", st.session_state.flow_step >= 4),
]

for idx, (num, label, active) in enumerate(steps):
    with progress_cols[idx]:
        color = "#44aa44" if active else "#cccccc"
        bg_color = "#44aa4420" if active else "#cccccc20"
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px; 
                        background-color: {bg_color}; border-radius: 8px;
                        border: 2px solid {color};">
                <h3 style="margin: 0; color: {color};">{num}</h3>
                <p style="margin: 5px 0; font-weight: bold;">{label}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

if st.session_state.flow_step == 0:
    st.header("Step 1: Fall Detection")
    st.markdown("""
    The system continuously monitors residents through cameras using **MediaPipe Pose Detection**.
    When a potential fall is detected, the computer vision pipeline analyzes:
    - Body posture and orientation
    - Sudden vertical displacement
    - Loss of balance indicators
    """)
    
    st.subheader("🎥 Live Monitor (Simulated)")
    
    profiles = api_client.get_patient_profiles()
    
    monitor_col, control_col = st.columns([2, 1])
    
    with monitor_col:
        st.markdown("""
        <div style="background-color: #1a1a1a; border-radius: 10px; padding: 20px; 
                    min-height: 300px; display: flex; align-items: center; justify-content: center;">
            <div style="text-align: center; color: #44aa44;">
                <h1 style="margin: 0;">📹</h1>
                <p style="margin: 10px 0;">Camera Feed Active</p>
                <p style="color: #666; font-size: 0.8em;">Monitoring 8 residents...</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with control_col:
        st.markdown("### 🎮 Simulation Controls")
        
        st.markdown("**Select Patient:**")
        
        patient_options = {}
        for p in profiles:
            label = f"{p['name']} (Room {p['room']}, {p['risk_level'].upper()} risk)"
            patient_options[label] = p
        
        selected_label = st.selectbox(
            "Select Resident",
            options=list(patient_options.keys()),
            label_visibility="collapsed",
            key=f"patient_selector_{st.session_state.patient_selector_key}",
        )
        
        selected_patient = patient_options[selected_label]
        st.session_state.selected_patient = selected_patient
        
        st.markdown("---")
        st.markdown(f"**✓ Selected:** {selected_patient['name']}")
        st.markdown(f"Room: {selected_patient['room']} | Risk: {selected_patient['risk_level'].upper()}")
        
        st.markdown("**Simulate Event:**")
        
        scenario = st.selectbox(
            "Fall Scenario",
            options=[
                "Normal Fall - Slow Response",
                "Normal Fall - Patient OK",
                "Hard Fall - Possible Injury",
                "Red Flag - Head Impact",
                "Red Flag - Unconscious",
            ],
        )
        
        if st.button("🚨 TRIGGER FALL DETECTION", type="primary", use_container_width=True):
            st.session_state.fall_detected = True
            st.session_state.flow_step = 1
            st.session_state.fall_scenario = scenario
            st.rerun()

elif st.session_state.flow_step == 1:
    st.header("Step 2: Alert Generated")
    
    patient = st.session_state.selected_patient
    
    st.success(f"""
    ### ✅ Fall Detected!
    
    **Patient:** {patient.get('name', 'Unknown')} (Room {patient.get('room', 'N/A')})
    **Time:** {time.strftime('%H:%M:%S')}
    **Confidence:** 94.3%
    **Detection Source:** Camera - Living Room
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div style="background-color: #ff444420; border: 2px solid #ff4444; 
                    border-radius: 10px; padding: 20px; text-align: center;">
            <h2 style="color: #ff4444; margin: 0;">🚨</h2>
            <h3 style="color: #ff4444; margin: 10px 0;">FALL DETECTED</h3>
            <p>Initiating triage protocol...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Initial Assessment")
        st.markdown(f"**Risk Level:** {patient.get('risk_level', 'Unknown').upper()}")
        st.markdown(f"**Risk Score:** {patient.get('risk_score', 'N/A')}")
        st.markdown(f"**Age:** {patient.get('age', 'N/A')}")
        
        if patient.get('conditions'):
            st.markdown(f"**Conditions:** {', '.join(patient['conditions'][:2])}")
    
    st.info("⏱️ The system waits **3 seconds** before checking with the patient to avoid false alarms from quick recovery.")
    
    if st.button("➡️ Proceed to Patient Check", type="primary", use_container_width=True):
        st.session_state.flow_step = 2
        st.session_state.simulation_timer = 0
        st.rerun()
    
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.flow_step = 0
        st.rerun()

elif st.session_state.flow_step == 2:
    st.header("Step 3: Patient Check")
    
    patient = st.session_state.selected_patient
    scenario = st.session_state.get('fall_scenario', 'Normal Fall')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🔊 Voice Prompt")
        
        lang = patient.get('language', 'English')
        if 'Vietnamese' in lang or 'VI' in lang:
            st.markdown("""
            <div style="background-color: #4444ff20; border: 2px solid #4444ff; 
                        border-radius: 10px; padding: 20px;">
                <h4 style="margin: 0;">🇻🇳 Vietnamese</h4>
                <p style="font-size: 1.2em; margin: 10px 0;">
                    <strong>"Bạn có ổn không? Vui lòng phản hồi nếu bạn nghe thấy tôi."</strong>
                </p>
                <p style="color: #666; font-size: 0.9em;">
                    (Are you okay? Please respond if you can hear me.)
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #4444ff20; border: 2px solid #4444ff; 
                        border-radius: 10px; padding: 20px;">
                <h4 style="margin: 0;">🇬🇧 English</h4>
                <p style="font-size: 1.2em; margin: 10px 0;">
                    <strong>"Are you okay? Please respond if you can hear me."</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### ⏱️ Waiting for Response...")
        
        st.progress(st.session_state.simulation_timer / 100)
        
        if st.session_state.simulation_timer < 100:
            st.session_state.simulation_timer += 10
            time.sleep(0.2)
            st.rerun()
    
    with col2:
        st.markdown("### 👤 Simulate Patient Response")
        
        st.markdown(f"**Current Scenario:** {scenario}")
        
        response_options = {
            "✅ I'm okay / Tôi ổn": "i_am_okay",
            "🆘 I need help / Cứu tôi": "need_help",
            "😵 Cannot move / Không thể di chuyển": "cannot_move",
            "🔇 No Response (timeout)": "no_response",
        }
        
        if "Head Impact" in scenario:
            st.error("⚠️ RED FLAG DETECTED: Head Impact")
            st.session_state.patient_response = ""
            st.session_state.red_flags = {"head_impact": True}
        elif "Unconscious" in scenario:
            st.error("⚠️ RED FLAG DETECTED: Unconscious")
            st.session_state.patient_response = ""
            st.session_state.red_flags = {"unconscious": True}
        else:
            st.session_state.red_flags = {}
            selected_response = st.radio(
                "Select Response:",
                options=list(response_options.keys()),
                index=3,
            )
            st.session_state.patient_response = response_options[selected_response]
    
    if st.button("➡️ Process Response", type="primary", use_container_width=True):
        st.session_state.flow_step = 3
        st.rerun()

elif st.session_state.flow_step == 3:
    st.header("Step 4: Triage Classification")
    
    patient = st.session_state.selected_patient
    response = st.session_state.patient_response
    red_flags = st.session_state.get('red_flags', {})
    
    fall_event = {
        "source": "camera",
        **red_flags,
    }
    
    result = api_client.triage_classify(
        patient_profile=patient,
        fall_event=fall_event,
        elapsed_seconds=5,
        language="vi" if "Vietnamese" in patient.get("language", "") else "en",
        patient_response=response if response != "no_response" else "",
    )
    
    st.session_state.triage_result = result
    
    category = result.get("category", "UNKNOWN")
    stage = result.get("stage", "unknown")
    
    cat_colors = {
        "CAT_1": ("#44aa44", "✅ False Alarm"),
        "CAT_2": ("#88cc44", "🟡 Low Risk"),
        "CAT_3": ("#ffaa00", "🟠 Moderate Risk"),
        "CAT_4": ("#ff6600", "🔴 High Risk"),
        "CAT_5": ("#ff0000", "🚨 EMERGENCY"),
    }
    
    color, description = cat_colors.get(category, ("#888888", "Unknown"))
    
    st.markdown(f"""
    <div style="background-color: {color}20; border: 3px solid {color}; 
                border-radius: 15px; padding: 30px; text-align: center; margin: 20px 0;">
        <h1 style="color: {color}; margin: 0; font-size: 3em;">{category}</h1>
        <h2 style="margin: 10px 0;">{description}</h2>
        <p style="font-size: 1.2em;">{stage.replace('_', ' ').title()}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Decision Details")
        st.info(result.get("reason", "No rationale available"))
        
        st.markdown(f"**Recommended Action:** {result.get('action', 'N/A').replace('_', ' ').title()}")
        st.markdown(f"**Communication Channel:** {result.get('recommended_channel', 'N/A').replace('_', ' ').title()}")
        
        if result.get("risk_reasons"):
            st.markdown("### 📋 Risk Factors Considered:")
            for reason in result.get("risk_reasons"):
                st.markdown(f"- {reason}")
    
    with col2:
        st.markdown("### 👤 Patient Profile Used")
        st.markdown(f"**Name:** {patient.get('name', 'N/A')}")
        st.markdown(f"**Age:** {patient.get('age', 'N/A')}")
        st.markdown(f"**Risk Level:** {patient.get('risk_level', 'N/A').upper()}")
        st.markdown(f"**Risk Score:** {patient.get('risk_score', 'N/A')}")
        
        if patient.get("conditions"):
            st.markdown(f"**Conditions:** {', '.join(patient['conditions'])}")
        
        st.markdown(f"**Previous Falls:** {patient.get('previous_falls', 0)}")
    
    if st.button("➡️ View Escalation Timeline", type="primary", use_container_width=True):
        st.session_state.flow_step = 4
        st.rerun()

elif st.session_state.flow_step == 4:
    st.header("Step 5: Escalation Timeline")
    
    result = st.session_state.triage_result
    category = result.get("category", "CAT_3")
    
    st.markdown("""
    ### ⏱️ Staged Escalation Protocol
    
    The system uses a time-based escalation strategy to balance response speed with false alarm prevention.
    """)
    
    timeline_steps = [
        ("0s", "🎥", "Fall Detected", "Camera detects unusual movement pattern", True),
        ("3s", "🗣️", "Voice Prompt", "System asks 'Are you okay?' in patient language", category != "CAT_5"),
        ("10s", "📱", "Carer Alert", "Notification sent to assigned carer", category not in ["CAT_1", "CAT_5"]),
        ("20s", "🚑", "Emergency", "Emergency services contacted", category in ["CAT_4", "CAT_5"]),
    ]
    
    st.divider()
    
    for idx, (time_mark, emoji, label, desc, active) in enumerate(timeline_steps):
        cols = st.columns([1, 4])
        with cols[0]:
            color = "#44aa44" if active else "#cccccc"
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background-color: {color}30; 
                        border-radius: 8px; border: 2px solid {color};">
                <h3 style="margin: 0;">{emoji}</h3>
                <p style="margin: 5px 0; font-weight: bold; color: {color};">{time_mark}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            status_color = "#44aa44" if active else "#666666"
            st.markdown(f"""
            <div style="padding: 10px; background-color: {'#44aa4420' if active else '#33333310'}; 
                        border-radius: 8px; border-left: 4px solid {status_color};">
                <h4 style="margin: 0; color: {status_color};">{label}</h4>
                <p style="margin: 5px 0; color: {'#333' if active else '#666'};">{desc}</p>
                {'✅ Completed' if active else '⏭️ Skipped/Not Reached'}
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
    
    st.subheader("📋 Summary")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.markdown("### What Happened")
        st.markdown(f"- **Final Category:** {category}")
        st.markdown(f"- **Patient Response:** {st.session_state.patient_response or 'No response / Red flag'}")
        st.markdown(f"- **Escalation Time:** {'< 3s' if category == 'CAT_5' else '3-20s based on response'}")
    
    with summary_col2:
        st.markdown("### Next Steps")
        if category == "CAT_1":
            st.success("✅ False alarm - monitoring continues")
        elif category == "CAT_5":
            st.error("🚑 Emergency services dispatched immediately")
        elif category in ["CAT_4"]:
            st.warning("📱 Carer alerted + Emergency standby")
        else:
            st.info("📱 Carer has been notified")
    
    st.divider()
    
    if st.button("🔄 Run Another Scenario", type="primary", use_container_width=True):
        st.session_state.flow_step = 0
        st.session_state.fall_detected = False
        st.session_state.patient_response = None
        st.session_state.triage_result = None
        st.session_state.simulation_timer = 0
        st.session_state.patient_selector_key += 1
        st.rerun()

with st.sidebar:
    st.header("👤 Current Patient")
    if st.session_state.selected_patient:
        patient = st.session_state.selected_patient
        st.markdown(f"**{patient.get('name', 'Unknown')}**")
        st.markdown(f"Room: {patient.get('room', 'N/A')}")
        st.markdown(f"Age: {patient.get('age', 'N/A')}")
        st.markdown(f"Risk: {patient.get('risk_level', 'N/A').upper()}")
        
        if st.session_state.flow_step > 0:
            st.divider()
            if st.button("🔄 Change Patient / Restart", use_container_width=True):
                st.session_state.flow_step = 0
                st.session_state.fall_detected = False
                st.session_state.patient_response = None
                st.session_state.triage_result = None
                st.session_state.simulation_timer = 0
                st.session_state.patient_selector_key += 1
                st.rerun()
    else:
        st.info("No patient selected")
