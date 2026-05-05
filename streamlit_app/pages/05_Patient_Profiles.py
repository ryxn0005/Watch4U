"""Patient Profiles demo (Affan)."""
import json

import streamlit as st

from lib.api_client import health

st.set_page_config(page_title="Patient Profiles - Watch4U", page_icon="👥")

st.title("Patient Profiles")
st.caption("Owner: Affan · data/synthetic/ + data/preprocessing/")

# Backend connectivity check
try:
    backend_health = health()
    st.success(f"✅ Backend connected: {backend_health.get('status', 'unknown')}")
except Exception as e:
    st.error(f"❌ Backend connection failed: {e}")
    st.stop()

st.markdown("---")

# Load sample profiles
try:
    with open("data/synthetic/samples/profiles.json", "r") as f:
        profiles_data = json.load(f)
        profiles = profiles_data.get("profiles", [])
except FileNotFoundError:
    st.error("Sample profiles not found. Run: python data/synthetic/generate_profiles.py")
    profiles = []
except Exception as e:
    st.error(f"Error loading profiles: {e}")
    profiles = []

if not profiles:
    st.warning("No patient profiles available")
    st.stop()

# Filters
st.sidebar.header("Filters")

age_range = st.sidebar.slider(
    "Age Range",
    min_value=60,
    max_value=100,
    value=(60, 100),
)

risk_levels = st.sidebar.multiselect(
    "Risk Level",
    ["low", "moderate", "high"],
    default=["low", "moderate", "high"],
)

conditions = st.sidebar.multiselect(
    "Medical Conditions",
    ["Diabetes", "Hypertension", "Osteoporosis", "Dementia", "Stroke History"],
)

# Filter profiles
filtered_profiles = []
for p in profiles:
    # Age filter
    if not (age_range[0] <= p.get("age", 0) <= age_range[1]):
        continue
    
    # Risk filter
    risk = p.get("risk_level", "unknown")
    if risk not in risk_levels:
        continue
    
    # Conditions filter
    if conditions:
        profile_conditions = [c.lower() for c in p.get("medical_conditions", [])]
        if not any(c.lower() in profile_conditions for c in conditions):
            continue
    
    filtered_profiles.append(p)

# Summary stats
st.markdown(f"### Showing {len(filtered_profiles)} of {len(profiles)} profiles")

col1, col2, col3, col4 = st.columns(4)
with col1:
    avg_age = sum(p.get("age", 0) for p in filtered_profiles) / len(filtered_profiles) if filtered_profiles else 0
    st.metric("Average Age", f"{avg_age:.1f}")
with col2:
    high_risk = sum(1 for p in filtered_profiles if p.get("risk_level") == "high")
    st.metric("High Risk", high_risk)
with col3:
    living_alone = sum(1 for p in filtered_profiles if p.get("lives_alone"))
    st.metric("Living Alone", living_alone)
with col4:
    fall_history = sum(1 for p in filtered_profiles if p.get("fall_history"))
    st.metric("Previous Falls", fall_history)

# Display profiles
st.markdown("---")

for i, profile in enumerate(filtered_profiles):
    risk_emoji = {"low": "🟢", "moderate": "🟡", "high": "🔴"}.get(
        profile.get("risk_level", "unknown"), "⚪"
    )
    
    with st.expander(f"{risk_emoji} {profile.get('name', 'Unknown')} (Age: {profile.get('age', 'N/A')})"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Demographics**")
            st.text(f"Age: {profile.get('age', 'N/A')}")
            st.text(f"Gender: {profile.get('gender', 'N/A')}")
            st.text(f"Language: {profile.get('language_preference', 'N/A')}")
            st.text(f"Lives Alone: {'Yes' if profile.get('lives_alone') else 'No'}")
            
            st.markdown("**Medical History**")
            conditions = profile.get("medical_conditions", [])
            if conditions:
                for condition in conditions:
                    st.text(f"• {condition}")
            else:
                st.text("No major conditions")
        
        with col2:
            st.markdown("**Functional Status**")
            st.text(f"Mobility: {profile.get('mobility_status', 'N/A')}")
            st.text(f"Vision: {profile.get('vision_impairment', 'N/A')}")
            st.text(f"Hearing: {profile.get('hearing_impairment', 'N/A')}")
            
            st.markdown("**Fall History**")
            if profile.get("fall_history"):
                st.text(f"Previous Falls: {profile.get('falls_last_12_months', 0)}")
                st.text(f"Last Fall: {profile.get('last_fall_date', 'N/A')}")
            else:
                st.text("No previous falls")
            
            st.markdown("**Risk Assessment**")
            st.text(f"Risk Level: {profile.get('risk_level', 'unknown').upper()}")
            st.text(f"Risk Score: {profile.get('risk_score', 0)}/100")
        
        # Emergency contacts
        st.markdown("**Emergency Contacts**")
        contacts = profile.get("emergency_contacts", [])
        if contacts:
            for contact in contacts:
                st.text(f"• {contact.get('name', 'Unknown')} ({contact.get('relationship', 'Unknown')}): {contact.get('phone', 'N/A')}")
        else:
            st.text("No emergency contacts on file")
        
        # Medications
        st.markdown("**Medications**")
        medications = profile.get("medications", [])
        if medications:
            for med in medications[:5]:  # Show first 5
                st.text(f"• {med}")
            if len(medications) > 5:
                st.text(f"... and {len(medications) - 5} more")
        else:
            st.text("No medications recorded")
        
        # Raw data
        with st.expander("📋 Raw Profile Data"):
            st.json(profile)

st.markdown("---")
st.caption("This demo displays synthetic patient profiles from data/synthetic/samples/")

# Generation info
with st.expander("ℹ️ About Synthetic Profiles"):
    st.markdown("""
    **Generation Method:**
    - Based on CALD (Culturally and Linguistically Diverse) senior population statistics
    - Realistic comorbidity patterns
    - Medication interactions considered
    - Fall risk calculated based on multiple factors
    
    **Risk Factors:**
    - Age (65+)
    - Previous fall history
    - Cognitive impairment
    - Mobility limitations
    - Medications (blood thinners, sedatives)
    - Living alone
    
    **To generate more profiles:**
    ```bash
    python data/synthetic/generate_profiles.py -n 100 --out data/synthetic/samples/profiles.json
    ```
    """)
