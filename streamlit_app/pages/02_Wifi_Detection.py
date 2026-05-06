"""Wi-Fi Detection demo (Ryan)."""
import random

import streamlit as st

from lib.api_client import health

st.set_page_config(page_title="Wi-Fi Detection - Watch4U", page_icon="📶")

st.title("Wi-Fi Detection")
st.caption("Owner: Ryan · backend/app/services/wifi_detection/")

# Backend connectivity check
try:
    backend_health = health()
    st.success(f"✅ Backend connected: {backend_health.get('status', 'unknown')}")
    st.warning("⚠️ Wi-Fi Detection service not yet implemented - showing mock data")
except Exception as e:
    st.error(f"❌ Backend connection failed: {e}")
    st.stop()

st.markdown("---")

# Mock Wi-Fi CSI visualization
st.markdown("### 📊 Channel State Information (CSI) Analysis")

# Mock data controls
col1, col2, col3 = st.columns(3)
with col1:
    room = st.selectbox("Room", ["Living Room", "Bedroom", "Bathroom", "Kitchen"])
with col2:
    activity = st.selectbox("Activity", ["No Motion", "Walking", "Fall", "Sitting"])
with col3:
    duration = st.slider("Duration (s)", 1, 60, 10)

# Generate mock CSI data
import numpy as np
import pandas as pd

t = np.linspace(0, duration, duration * 50)

# Simulate different activities
if activity == "No Motion":
    amplitude = np.random.normal(0, 0.1, len(t))
    phase = np.random.normal(0, 0.05, len(t))
elif activity == "Walking":
    amplitude = np.sin(2 * np.pi * 1 * t) + np.random.normal(0, 0.2, len(t))
    phase = np.cos(2 * np.pi * 1 * t) + np.random.normal(0, 0.1, len(t))
elif activity == "Fall":
    # Sudden spike then drop
    amplitude = np.random.normal(0, 0.1, len(t))
    mid = len(t) // 2
    amplitude[mid:mid+10] = 3.0 + np.random.normal(0, 0.5, 10)
    phase = np.random.normal(0, 0.1, len(t))
else:  # Sitting
    amplitude = np.random.normal(0, 0.15, len(t))
    amplitude[t > duration/2] += 0.5  # Step change
    phase = np.random.normal(0, 0.08, len(t))

# Plot amplitude and phase
df = pd.DataFrame({
    "Time (s)": t,
    "Amplitude": amplitude,
    "Phase": phase,
})

st.subheader("Amplitude Over Time")
st.line_chart(df.set_index("Time (s)")["Amplitude"])

st.subheader("Phase Over Time")
st.line_chart(df.set_index("Time (s)")["Phase"])

# Mock detection result
st.markdown("---")
st.markdown("### 🎯 Detection Result")

# Simulate detection logic
detection_confidence = random.uniform(0.6, 0.95)

if activity == "Fall":
    st.error(f"🚨 **FALL DETECTED** (Confidence: {detection_confidence:.1%})")
    st.warning("⚠️ Alert: Sudden motion change detected in privacy zone")
elif activity == "Walking":
    st.info(f"🚶 **Motion Detected** (Confidence: {detection_confidence:.1%})")
else:
    st.success(f"✅ **No Anomaly** (Confidence: {detection_confidence:.1%})")

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("SNR (dB)", f"{random.uniform(15, 35):.1f}")
with col2:
    st.metric("Subcarriers", random.randint(52, 114))
with col3:
    st.metric("Update Rate", "100 Hz")

st.markdown("---")

# Hardware status
st.markdown("### 🔌 Hardware Status")

hw_col1, hw_col2 = st.columns(2)
with hw_col1:
    st.markdown("**ESP32 Sensor #1**")
    st.text("Status: Connected")
    st.text("RSSI: -45 dBm")
    st.text("Last ping: 0.2s ago")
    
with hw_col2:
    st.markdown("**ESP32 Sensor #2**")
    st.text("Status: Connected")
    st.text("RSSI: -52 dBm")
    st.text("Last ping: 0.3s ago")

# Info box
st.info("""
**Note:** Wi-Fi CSI (Channel State Information) sensing detects motion through 
disturbances in wireless signals. This is ideal for privacy-sensitive areas 
like bathrooms where cameras are inappropriate.

**Hardware Required:**
- ESP32 with CSI firmware
- Wi-Fi router with monitor mode support

**Current Status:** Hardware ordered (A2 milestone)
""")

st.caption("This demo shows mock CSI data - actual implementation requires ESP32 hardware")
