"""Fall Detection - Video analysis with pose detection visualization."""
from __future__ import annotations

import random

import streamlit as st

from lib import api_client

st.set_page_config(
    page_title="Fall Detection",
    page_icon="🎥",
    layout="wide",
)

st.title("🎥 Fall Detection")
st.caption("PR #9: FallVision Pipeline with MediaPipe Pose Detection")

st.divider()

upload_col, samples_col = st.columns([2, 1])

with upload_col:
    st.subheader("📤 Upload Video")
    
    uploaded_file = st.file_uploader(
        "Upload video for fall detection analysis",
        type=["mp4", "avi", "mov"],
        help="Supported formats: MP4, AVI, MOV",
    )
    
    if uploaded_file:
        st.video(uploaded_file)
        
        if st.button("🔍 Analyze Video", type="primary", use_container_width=True):
            with st.spinner("Processing video..."):
                import time
                time.sleep(2)
                result = api_client.detect_fall("uploaded_video")
                st.session_state.detection_result = result
                st.success("Analysis complete!")

with samples_col:
    st.subheader("🎬 Sample Videos")
    
    samples = api_client.get_sample_videos()
    
    for sample in samples:
        with st.container(border=True):
            st.markdown(f"**{sample['name']}**")
            st.markdown(f"Duration: {sample['duration']} | Label: {sample['label']}")
            if st.button(f"Load {sample['id']}", key=f"sample_{sample['id']}"):
                st.session_state.detection_result = api_client.detect_fall(sample["id"])
                st.rerun()

st.divider()

st.subheader("📊 Detection Results")

if "detection_result" in st.session_state and st.session_state.detection_result:
    result = st.session_state.detection_result
    
    result_cols = st.columns([1, 2])
    
    with result_cols[0]:
        detected = result.get("detected", False)
        confidence = result.get("confidence", 0)
        label = result.get("label", "Unknown")
        
        if detected:
            st.error(f"### ⚠️ {label} DETECTED")
            st.markdown(f"**Confidence:** {confidence:.1%}")
            st.markdown(f"**Long-lie Probability:** {result.get('long_lie_probability', 0):.1%}")
        else:
            st.success(f"### ✅ {label}")
            st.markdown(f"**Confidence:** {(1 - confidence):.1%}")
        
        st.markdown(f"**Processing Time:** {result.get('processing_time_ms', 0)}ms")
        st.markdown(f"**Model:** {result.get('model_version', 'Unknown')}")
    
    with result_cols[1]:
        st.markdown("### 🎯 Pose Keypoints")
        
        keypoints = result.get("keypoints", [])
        
        if keypoints:
            st.markdown(f"Detected **{len(keypoints)}** keypoints")
            
            keypoint_defs = api_client.get_pose_keypoints()
            
            viz_cols = st.columns(2)
            
            with viz_cols[0]:
                st.markdown("**Upper Body**")
                upper_points = ["Nose", "Left Eye", "Right Eye", "Left Shoulder", "Right Shoulder", 
                               "Left Elbow", "Right Elbow", "Left Wrist", "Right Wrist"]
                for kp in keypoint_defs:
                    if kp["name"] in upper_points and kp["index"] < len(keypoints):
                        point = keypoints[kp["index"]]
                        vis = point.get("visibility", 0)
                        color = "🟢" if vis > 0.8 else "🟡" if vis > 0.5 else "🔴"
                        st.markdown(f"{color} **{kp['name']}**: ({point['x']:.0f}, {point['y']:.0f}) vis={vis:.2f}")
            
            with viz_cols[1]:
                st.markdown("**Lower Body**")
                lower_points = ["Left Hip", "Right Hip", "Left Knee", "Right Knee", "Left Ankle", "Right Ankle"]
                for kp in keypoint_defs:
                    if kp["name"] in lower_points and kp["index"] < len(keypoints):
                        point = keypoints[kp["index"]]
                        vis = point.get("visibility", 0)
                        color = "🟢" if vis > 0.8 else "🟡" if vis > 0.5 else "🔴"
                        st.markdown(f"{color} **{kp['name']}**: ({point['x']:.0f}, {point['y']:.0f}) vis={vis:.2f}")
            
            st.markdown("### 📐 Skeleton Visualization")
            
            skeleton_edges = [
                ("Left Shoulder", "Right Shoulder"),
                ("Left Shoulder", "Left Elbow"),
                ("Left Elbow", "Left Wrist"),
                ("Right Shoulder", "Right Elbow"),
                ("Right Elbow", "Right Wrist"),
                ("Left Shoulder", "Left Hip"),
                ("Right Shoulder", "Right Hip"),
                ("Left Hip", "Right Hip"),
                ("Left Hip", "Left Knee"),
                ("Left Knee", "Left Ankle"),
                ("Right Hip", "Right Knee"),
                ("Right Knee", "Right Ankle"),
            ]
            
            name_to_idx = {kp["name"]: kp["index"] for kp in keypoint_defs}
            
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            for edge in skeleton_edges:
                if edge[0] in name_to_idx and edge[1] in name_to_idx:
                    idx1 = name_to_idx[edge[0]]
                    idx2 = name_to_idx[edge[1]]
                    if idx1 < len(keypoints) and idx2 < len(keypoints):
                        x_vals = [keypoints[idx1]["x"], keypoints[idx2]["x"]]
                        y_vals = [keypoints[idx1]["y"], keypoints[idx2]["y"]]
                        fig.add_trace(go.Scatter(
                            x=x_vals, y=y_vals,
                            mode='lines',
                            line=dict(color='blue', width=2),
                            showlegend=False,
                        ))
            
            for kp in keypoint_defs:
                if kp["index"] < len(keypoints):
                    point = keypoints[kp["index"]]
                    fig.add_trace(go.Scatter(
                        x=[point["x"]], y=[point["y"]],
                        mode='markers+text',
                        marker=dict(size=8, color='red'),
                        text=[kp["name"]],
                        textposition="top center",
                        showlegend=False,
                    ))
            
            fig.update_layout(
                title="Pose Skeleton",
                xaxis=dict(range=[0, 640], showgrid=False, showticklabels=False),
                yaxis=dict(range=[480, 0], showgrid=False, showticklabels=False),
                width=600,
                height=400,
                plot_bgcolor='black',
            )
            
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Upload a video or select a sample to see detection results.")

st.divider()

st.subheader("🧠 Feature Extraction")

feature_info = api_client.get_feature_extraction_info()

feat_cols = st.columns([1, 2])

with feat_cols[0]:
    st.markdown(f"**Model:** {feature_info.get('pose_model', 'N/A')}")
    st.markdown(f"**Keypoints:** {feature_info.get('keypoints', 'N/A')}")
    st.markdown(f"**Window Size:** {feature_info.get('window_size', 'N/A')} frames")
    st.markdown(f"**Overlap:** {feature_info.get('overlap', 'N/A')}")

with feat_cols[1]:
    st.markdown("**Extracted Features:**")
    for feature in feature_info.get("features", []):
        st.markdown(f"- {feature}")

st.divider()

st.subheader("📹 Webcam Demo")

st.markdown("""
The webcam demo provides real-time fall detection using your camera:

1. **Pose Detection**: MediaPipe detects 33 body keypoints
2. **Feature Extraction**: Calculates body angles, ratios, and velocities
3. **Classification**: YOLO-based model classifies Fall vs No Fall
4. **Alert**: Triggers triage workflow on detection

*Note: Webcam access requires local Python environment. For this demo, use video upload instead.*
""")

st.info("💡 **Tip:** Try the **Data Pipeline** page to see how videos are preprocessed for training!")
