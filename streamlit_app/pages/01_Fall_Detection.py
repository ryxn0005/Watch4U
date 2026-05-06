"""Fall Detection demo (Darrel)."""
import time

import streamlit as st

from lib.api_client import get, health, post

st.set_page_config(page_title="Fall Detection - Watch4U", page_icon="🎥")

st.title("Fall Detection")
st.caption("Owner: Darrel · backend/app/services/fall_detection/")

# Backend connectivity check
try:
    backend_health = health()
    fall_health = get("/api/fall-detection/health")
    st.success(f"✅ Backend: {backend_health.get('status')} | Fall Detection: {fall_health.get('status')}")
except Exception as e:
    st.error(f"❌ Backend connection failed: {e}")
    st.stop()

st.markdown("---")

# Tabs for different input methods
tab1, tab2, tab3 = st.tabs(["📹 Video URL", "📁 Upload Video", "🔍 Check Status"])

with tab1:
    st.subheader("Analyze Video by URL")
    video_url = st.text_input(
        "Video URL",
        placeholder="https://example.com/fall-video.mp4",
        help="Enter URL to a video file for fall detection analysis",
    )
    
    col1, col2 = st.columns(2)
    with col1:
        sample_rate = st.slider("Sample Rate (fps)", 1, 30, 5)
    
    if st.button("🔍 Analyze Video URL", type="primary", use_container_width=True):
        if not video_url:
            st.warning("Please enter a video URL")
        else:
            with st.spinner("Analyzing video for falls..."):
                try:
                    result = post("/api/fall-detection/analyze", json={
                        "video_url": video_url,
                        "sample_rate": sample_rate,
                    })
                    
                    # Display results
                    _display_fall_result(result)
                    
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

with tab2:
    st.subheader("Upload Video File")
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=["mp4", "avi", "mov", "mkv"],
        help="Upload a video file for fall detection analysis",
    )
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        
        if st.button("📤 Upload & Analyze", type="primary", use_container_width=True):
            with st.spinner("Uploading video..."):
                try:
                    result = post("/api/fall-detection/analyze", json={
                        "video_url": f"file://{uploaded_file.name}",
                    })
                    
                    st.success(f"Video uploaded: {uploaded_file.name}")
                    _display_fall_result(result)
                    
                except Exception as e:
                    st.error(f"Upload failed: {e}")

with tab3:
    st.subheader("Check Analysis Status")
    video_id = st.text_input(
        "Video ID",
        placeholder="Enter video ID from upload",
    )
    
    if st.button("🔍 Check Status", use_container_width=True):
        if not video_id:
            st.warning("Please enter a video ID")
        else:
            try:
                status = get(f"/api/fall-detection/status/{video_id}")
                
                if status.get("status") == "not_found":
                    st.error(f"Video ID not found: {video_id}")
                else:
                    st.json(status)
                    
                    # Show progress
                    progress = status.get("progress", 0)
                    st.progress(progress, text=f"Progress: {progress*100:.0f}%")
                    
                    # Show result if completed
                    if status.get("status") == "completed" and status.get("result"):
                        st.markdown("---")
                        _display_fall_result(status["result"])
                        
            except Exception as e:
                st.error(f"Status check failed: {e}")


def _display_fall_result(result):
    """Display fall detection result in a formatted way."""
    fall_detected = result.get("fall_detected", False)
    confidence = result.get("confidence", 0)
    
    if fall_detected:
        st.error(f"🚨 **FALL DETECTED** (Confidence: {confidence:.1%})")
    else:
        st.success(f"✅ **No Fall Detected** (Confidence: {confidence:.1%})")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confidence", f"{confidence:.1%}")
    with col2:
        scene = result.get("scene", "unknown")
        st.metric("Scene", scene.title() if scene else "N/A")
    with col3:
        processing_time = result.get("processing_time_ms", 0)
        st.metric("Processing Time", f"{processing_time}ms")
    
    # Long lie detection
    if result.get("long_lie_detected"):
        st.warning("⚠️ Long-lie detected (>60s on ground)")
    
    # Fall events
    fall_events = result.get("fall_events", [])
    if fall_events:
        st.markdown("### Detected Fall Events")
        for i, event in enumerate(fall_events):
            with st.expander(f"Fall Event {i+1}"):
                st.write(f"**Time:** {event.get('start_time', 0):.1f}s - {event.get('end_time', 0):.1f}s")
                st.write(f"**Severity:** {event.get('severity', 'unknown')}")
                st.write(f"**Confidence:** {event.get('confidence', 0):.1%}")
    
    # Raw result
    with st.expander("📋 Raw Response"):
        st.json(result)


st.markdown("---")
st.caption("This demo connects to `/api/fall-detection/` endpoints")

# Demo notes
with st.expander("ℹ️ About Fall Detection"):
    st.markdown("""
    **How it works:**
    1. Upload a video or provide a URL
    2. The backend analyzes frames for pose keypoints
    3. ML model classifies movement as fall/no-fall
    4. Results include confidence, severity, and scene classification
    
    **Supported scenes:**
    - Bed (hardest to detect - lying vs fallen)
    - Chair (seated falls)
    - Stand (standing falls)
    
    **Model:** Baseline logistic regression on FallVision dataset
    """)
