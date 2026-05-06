"""Resident Management - Patient profile browser with risk indicators."""
from __future__ import annotations

import streamlit as st

from lib import api_client

st.set_page_config(
    page_title="Resident Management",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Resident Management")
st.caption("PR #11: SurrealDB Backend + PR #9: Synthetic Patient Profiles")

profiles = api_client.get_patient_profiles()
residents = api_client.get_residents()

st.divider()

filters_col, stats_col = st.columns([2, 1])

with filters_col:
    st.subheader("🔍 Filter Residents")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        risk_filter = st.multiselect(
            "Risk Level",
            options=["high", "moderate", "low"],
            default=[],
        )
    
    with filter_col2:
        age_range = st.slider(
            "Age Range",
            min_value=50,
            max_value=100,
            value=(60, 95),
        )
    
    with filter_col3:
        language_filter = st.multiselect(
            "Language",
            options=["English", "Vietnamese", "Bilingual (VI/EN)"],
            default=[],
        )

with stats_col:
    st.subheader("📊 Cohort Overview")
    
    high_risk = sum(1 for p in profiles if p.get("risk_level") == "high")
    moderate_risk = sum(1 for p in profiles if p.get("risk_level") == "moderate")
    low_risk = sum(1 for p in profiles if p.get("risk_level") == "low")
    
    risk_cols = st.columns(3)
    with risk_cols[0]:
        st.metric("🔴 High Risk", high_risk)
    with risk_cols[1]:
        st.metric("🟡 Moderate", moderate_risk)
    with risk_cols[2]:
        st.metric("🟢 Low Risk", low_risk)

filtered_profiles = [
    p for p in profiles
    if (not risk_filter or p.get("risk_level") in risk_filter)
    and (age_range[0] <= p.get("age", 0) <= age_range[1])
    and (not language_filter or p.get("language") in language_filter)
]

st.divider()

st.subheader(f"👥 Resident Profiles ({len(filtered_profiles)} shown)")

if not filtered_profiles:
    st.info("No residents match the selected filters.")
else:
    cols = st.columns(3)
    
    for idx, profile in enumerate(filtered_profiles):
        with cols[idx % 3]:
            risk = profile.get("risk_level", "unknown")
            risk_emoji = {"high": "🔴", "moderate": "🟡", "low": "🟢"}.get(risk, "⚪")
            risk_color = {"high": "#ff4444", "moderate": "#ffaa00", "low": "#44aa44"}.get(risk, "#888888")
            
            with st.container(border=True):
                st.markdown(f"""
                <div style="border-left: 4px solid {risk_color}; padding-left: 10px;">
                    <h4>{risk_emoji} {profile.get('name', 'Unknown')}</h4>
                    <p><strong>ID:</strong> {profile.get('id', 'N/A')} | <strong>Room:</strong> {profile.get('room', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Age:** {profile.get('age', 'N/A')}")
                    st.markdown(f"**Sex:** {profile.get('sex', 'N/A').title()}")
                    st.markdown(f"**Language:** {profile.get('language', 'N/A')}")
                
                with info_col2:
                    st.markdown(f"**Risk Score:** {profile.get('risk_score', 'N/A')}")
                    st.markdown(f"**Prev Falls:** {profile.get('previous_falls', 0)}")
                    mobility = profile.get("functional_status", {}).get("mobility", "unknown")
                    st.markdown(f"**Mobility:** {mobility}")
                
                conditions = profile.get("conditions", [])
                if conditions:
                    st.markdown(f"**Conditions:** {', '.join(conditions[:3])}")
                
                medications = profile.get("medications", [])
                if medications:
                    st.markdown(f"**Medications:** {', '.join(medications[:2])}...")
                
                with st.expander("View Details"):
                    st.json(profile)

st.divider()

st.subheader("📈 Risk Distribution")

risk_chart_data = {
    "Risk Level": ["High", "Moderate", "Low"],
    "Count": [high_risk, moderate_risk, low_risk],
}

chart_col, table_col = st.columns([1, 2])

with chart_col:
    import pandas as pd
    df = pd.DataFrame(risk_chart_data)
    st.bar_chart(df.set_index("Risk Level"))

with table_col:
    st.markdown("### Risk Factor Breakdown")
    
    risk_factors = {}
    for p in profiles:
        if p.get("risk_level") == "high":
            for reason in p.get("risk_reasons", []):
                risk_factors[reason] = risk_factors.get(reason, 0) + 1
    
    if risk_factors:
        factor_data = sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)[:5]
        for factor, count in factor_data:
            st.markdown(f"- {factor}: **{count}** residents")
    else:
        st.info("No high-risk residents in current view.")

st.divider()

st.caption("💡 **Tip:** Use the filters to identify high-risk residents who may need closer monitoring. Try the **Triage Simulator** to see how risk level affects emergency response.")
