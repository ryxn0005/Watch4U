"""Data Pipeline - Preprocessing and feature extraction visualization."""
from __future__ import annotations

import streamlit as st

from lib import api_client

st.set_page_config(
    page_title="Data Pipeline",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Data Pipeline")
st.caption("PR #9: FallVision & OmniFall Preprocessing Pipeline")

st.divider()

st.subheader("📈 Dataset Statistics")

stats = api_client.get_preprocessing_stats()

datasets = ["fallvision", "omnifall", "synthetic_profiles"]
dataset_names = {"fallvision": "FallVision", "omnifall": "OmniFall", "synthetic_profiles": "Synthetic Profiles"}

tabs = st.tabs([dataset_names[d] for d in datasets])

for idx, dataset in enumerate(datasets):
    with tabs[idx]:
        data = stats.get(dataset, {})
        
        if dataset == "synthetic_profiles":
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Generated", data.get("generated", 0))
            with col2:
                st.metric("🔴 High Risk", data.get("high_risk", 0))
            with col3:
                st.metric("🟡 Moderate Risk", data.get("moderate_risk", 0))
            with col4:
                st.metric("🟢 Low Risk", data.get("low_risk", 0))
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Raw Videos", data.get("raw_videos", 0))
            with col2:
                st.metric("Processed Frames", data.get("processed_frames", 0))
            with col3:
                st.metric("Train Samples", data.get("train_samples", 0))
            with col4:
                st.metric("Val Samples", data.get("val_samples", 0))
            
            if "categories" in data:
                st.markdown("### Category Distribution")
                for cat, count in data["categories"].items():
                    st.markdown(f"- **{cat}:** {count} videos")

st.divider()

st.subheader("🔧 Preprocessing Pipeline")

pipeline_steps = [
    {
        "title": "1️⃣ Video Ingestion",
        "description": "Load raw video files from FallVision and OmniFall datasets",
        "details": "Supported formats: MP4, AVI, MOV. Videos are validated and checked for corruption.",
    },
    {
        "title": "2️⃣ Frame Extraction",
        "description": "Extract frames at 1 FPS to prevent dataset bloat",
        "details": "Each video is processed frame-by-frame using OpenCV. One frame per second is extracted to maintain temporal information while keeping dataset size manageable.",
    },
    {
        "title": "3️⃣ YOLO Preprocessing",
        "description": "Resize frames to 640x640 for YOLO compatibility",
        "details": "Frames are resized to YOLO's standard input size. Aspect ratio is preserved with padding if necessary.",
    },
    {
        "title": "4️⃣ Train/Val Split",
        "description": "80/20 split using stratified sampling",
        "details": "Videos are split into train (80%) and validation (20%) sets. Stratification ensures balanced class distribution.",
    },
    {
        "title": "5️⃣ Pose Detection",
        "description": "MediaPipe Pose Landmarker extracts 33 keypoints",
        "details": "MediaPipe Pose Landmarker Lite runs on each frame to detect body keypoints with x, y, z coordinates and visibility scores.",
    },
    {
        "title": "6️⃣ Feature Extraction",
        "description": "Calculate body geometry and motion features",
        "details": "Features include: head/hip/ankle Y positions, body height/width, height-width ratio, torso angle, and mean confidence.",
    },
]

for step in pipeline_steps:
    with st.expander(step["title"]):
        st.markdown(f"**{step['description']}**")
        st.markdown(step["details"])

st.divider()

st.subheader("🎯 Feature Engineering")

feature_info = api_client.get_feature_extraction_info()

feat_col1, feat_col2 = st.columns(2)

with feat_col1:
    st.markdown(f"**Model:** {feature_info.get('pose_model', 'N/A')}")
    st.markdown(f"**Keypoints:** {feature_info.get('keypoints', 'N/A')} body landmarks")
    st.markdown(f"**Sliding Window:** {feature_info.get('window_size', 'N/A')} frames")
    st.markdown(f"**Overlap:** {feature_info.get('overlap', 0) * 100:.0f}%")

with feat_col2:
    st.markdown("**Computed Features:**")
    for feature in feature_info.get("features", []):
        description = {
            "head_y": "Vertical position of head",
            "hip_y": "Vertical position of hip center",
            "ankle_y": "Vertical position of ankles",
            "body_height": "Distance from head to ankles",
            "body_width": "Distance between shoulders",
            "height_width_ratio": "Body height / body width",
            "torso_angle_degrees": "Angle of torso relative to vertical",
            "mean_confidence": "Average landmark detection confidence",
        }.get(feature, "")
        st.markdown(f"- **{feature}**: {description}")

st.divider()

st.subheader("🧬 MediaPipe Pose Keypoints")

keypoints = api_client.get_pose_keypoints()

st.markdown(f"Total keypoints detected: **{len(keypoints)}**")

kp_cols = st.columns(4)

for idx, kp in enumerate(keypoints):
    with kp_cols[idx % 4]:
        st.markdown(f"**{kp['index']}**: {kp['name']}")

st.divider()

st.subheader("📁 Directory Structure")

st.code("""
data/
├── raw/
│   ├── fallvision/          # Original FallVision videos
│   └── omnifall/            # Original OmniFall videos
├── processed/
│   └── fallvision/
│       ├── train/
│       │   ├── Fall/        # Training frames (fall)
│       │   └── No_Fall/     # Training frames (no fall)
│       └── val/
│           ├── Fall/        # Validation frames (fall)
│           └── No_Fall/     # Validation frames (no fall)
├── features/                 # Extracted features (JSON)
├── models/                   # Trained model checkpoints
└── synthetic/                # Generated patient profiles
    └── samples/
        └── profiles.json
""")

st.divider()

st.caption("💡 **Tip:** The preprocessing pipeline is optimized for YOLO input. See **Fall Detection** to test the trained model!")
