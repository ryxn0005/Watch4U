"""Watch4U — Enhanced landing page with PR feature overview.

Phase 1 prototype demonstrating PRs #9, #10, #11.
Each demo lives under `pages/` and is auto-listed in the sidebar.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Watch4U",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🩺 Watch4U")
st.subheader("Context-Aware AI Fall Detection with Multilingual Staged Escalation")
st.caption("41004 — Group 43A · Empowering CALD Seniors Through Intelligent Monitoring")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🏥 Resident Management
    **PR #11: SurrealDB Backend**
    
    - Browse resident profiles with risk indicators
    - View fall event history
    - Manage caretaker assignments
    - Database schema explorer
    
    *[Navigate: Resident Management]*
    """)

with col2:
    st.markdown("""
    ### 🚨 Triage Response
    **PR #10: Multilingual Triage Engine**
    
    - CAT 1-5 severity classification
    - Staged escalation timeline (3s → 10s → 20s)
    - English & Vietnamese voice prompts
    - Red flag detection (immediate CAT-5)
    
    *[Navigate: Triage Simulator]*
    """)

with col3:
    st.markdown("""
    ### 🎥 Fall Detection
    **PR #9: Data Prep & CV Pipeline**
    
    - Video upload & analysis
    - Pose detection visualization
    - MediaPipe keypoint tracking
    - Preprocessing pipeline demo
    
    *[Navigate: Fall Detection, Data Pipeline]*
    """)

st.divider()

st.markdown("""
### 📱 Quick Navigation

Use the **sidebar** on the left to explore each component:

| Page | Feature | Owner |
|------|---------|-------|
| 🏥 **Resident Management** | Patient profiles, risk levels, database | PR #11 |
| 🚨 **Triage Simulator** | CAT classification, escalation timeline | PR #10 |
| 🎥 **Fall Detection** | Video analysis, pose detection | PR #9 |
| 📊 **Data Pipeline** | Preprocessing, feature extraction | PR #9 |
| 🗄️ **Database Explorer** | SurrealDB schema, fall events | PR #11 |
| 💬 **RAG Chat** | Multilingual medical Q&A | Existing |
| 📡 **Wi-Fi Detection** | CSI-based motion sensing | Existing |
""")

with st.expander("🔧 Technical Details"):
    st.markdown("""
    **Architecture:**
    - **Frontend:** Streamlit (Phase 1) → Next.js (Phase 2)
    - **Backend:** FastAPI with modular services
    - **Database:** SurrealDB (graph + document)
    - **ML Pipeline:** FallVision (YOLO) + MediaPipe Pose
    - **Triage:** Rule-based staged escalation with i18n
    
    **Key Technologies:**
    - Python 3.11, FastAPI, SurrealDB
    - MediaPipe Pose Landmarker (33 keypoints)
    - OpenCV, scikit-learn
    - Streamlit (prototype UI)
    """)

with st.expander("📋 Pull Request Summary"):
    st.markdown("""
    **PR #9 — Data Preparation:**
    - Synthetic patient profile generation (500 profiles)
    - FallVision preprocessing pipeline (YOLO-optimized)
    - MediaPipe pose keypoint extraction
    - Webcam demo with real-time detection
    
    **PR #10 — Multilingual Triage:**
    - CAT 1-5 classification engine
    - Staged escalation: 3s patient check → 10s carer alert → 20s emergency
    - English & Vietnamese voice prompt support
    - Red flag detection for immediate escalation
    
    **PR #11 — SurrealDB Backend:**
    - Resident, caretaker, device schemas
    - Fall event tracking with relationships
    - FastAPI integration with SurrealDB
    - CORS and environment configuration
    """)

st.divider()
st.caption("💡 **Tip:** Start with **Resident Management** to browse profiles, then try the **Triage Simulator** with different risk levels!")
