"""Database Explorer - SurrealDB schema and data viewer."""
from __future__ import annotations

import streamlit as st

from lib import api_client

st.set_page_config(
    page_title="Database Explorer",
    page_icon="🗄️",
    layout="wide",
)

st.title("🗄️ Database Explorer")
st.caption("PR #11: SurrealDB Backend Integration")

st.divider()

tab_schema, tab_residents, tab_falls, tab_caretakers = st.tabs([
    "📐 Schema", "👥 Residents", "🚨 Fall Events", "👨‍⚕️ Caretakers"
])

with tab_schema:
    st.subheader("📐 SurrealDB Schema Definition")
    
    schema = api_client.get_database_schema()
    
    for table in schema.get("tables", []):
        with st.expander(f"Table: **{table['name']}** ({table['type']})"):
            st.markdown(f"**Type:** {table['type']}")
            
            if table.get("from") and table.get("to"):
                st.markdown(f"**Relationship:** `{table['from']}` → `{table['to']}`")
            
            if table.get("fields"):
                st.markdown("**Fields:**")
                for field in table["fields"]:
                    req = "required" if field.get("required") else "optional"
                    default = f" (default: {field.get('default')})" if field.get("default") else ""
                    st.markdown(f"- `{field['name']}`: `{field['type']}` — {req}{default}")
            
            if table.get("indexes"):
                st.markdown("**Indexes:**")
                for idx in table["indexes"]:
                    fields = ", ".join(idx.get("fields", []))
                    st.markdown(f"- `{idx['name']}`: ({fields})")

with tab_residents:
    st.subheader("👥 Resident Records")
    
    residents = api_client.get_residents()
    
    st.markdown(f"Total residents: **{len(residents)}**")
    
    for resident in residents:
        with st.container(border=True):
            cols = st.columns([2, 2, 2, 1])
            with cols[0]:
                st.markdown(f"**{resident.get('name', 'Unknown')}**")
                st.markdown(f"`{resident.get('id', 'N/A')}`")
            with cols[1]:
                st.markdown(f"Room: {resident.get('room', 'N/A')}")
            with cols[2]:
                created = resident.get('created_at', 'N/A')
                if created != 'N/A':
                    created = created[:10] if isinstance(created, str) else created
                st.markdown(f"Added: {created}")
            with cols[3]:
                if st.button("View", key=f"view_{resident.get('id', '0')}"):
                    st.json(resident)
            
            notes = resident.get('notes', '')
            if notes:
                st.markdown(f"*Notes: {notes}*")

with tab_falls:
    st.subheader("🚨 Fall Event History")
    
    fall_events = api_client.get_fall_events(limit=20)
    
    st.markdown(f"Showing **{len(fall_events)}** recent events")
    
    severity_colors = {
        "CAT_1": "🟢",
        "CAT_2": "🟡",
        "CAT_3": "🟠",
        "CAT_4": "🔴",
        "CAT_5": "🚨",
    }
    
    for event in fall_events:
        severity = event.get("severity_label", "UNKNOWN")
        color = severity_colors.get(severity, "⚪")
        
        with st.container(border=True):
            cols = st.columns([1, 2, 2, 2, 1, 1])
            
            with cols[0]:
                st.markdown(f"{color} **{severity}**")
            
            with cols[1]:
                st.markdown(f"**{event.get('resident_name', 'Unknown')}**")
            
            with cols[2]:
                detected = event.get('detected_at', 'N/A')
                if detected != 'N/A' and isinstance(detected, str):
                    detected = detected[:16].replace('T', ' ')
                st.markdown(f"📅 {detected}")
            
            with cols[3]:
                source = event.get('source', 'unknown')
                source_emoji = {"camera": "📹", "wifi_csi": "📡", "wearable": "⌚"}.get(source, "❓")
                st.markdown(f"{source_emoji} {source}")
            
            with cols[4]:
                confidence = event.get('confidence', 0)
                st.markdown(f"🎯 {confidence:.0%}")
            
            with cols[5]:
                if event.get('false_alarm'):
                    st.markdown("❌ False Alarm")
                elif event.get('acknowledged_at'):
                    st.markdown("✅ Acknowledged")
                else:
                    st.markdown("⏳ Pending")
            
            if event.get('clip_uri'):
                st.markdown(f"📼 Clip: `{event['clip_uri']}`")

with tab_caretakers:
    st.subheader("👨‍⚕️ Caretaker Registry")
    
    caretakers = api_client.get_caretakers()
    
    st.markdown(f"Total caretakers: **{len(caretakers)}**")
    
    for caretaker in caretakers:
        with st.container(border=True):
            cols = st.columns([2, 2, 2, 1])
            
            with cols[0]:
                st.markdown(f"**{caretaker.get('name', 'Unknown')}**")
                st.markdown(f"`{caretaker.get('id', 'N/A')}`")
            
            with cols[1]:
                email = caretaker.get('email', 'N/A')
                st.markdown(f"📧 {email}")
            
            with cols[2]:
                phone = caretaker.get('phone', 'N/A')
                st.markdown(f"📱 {phone}")
            
            with cols[3]:
                if st.button("Details", key=f"ct_{caretaker.get('id', '0')}"):
                    st.json(caretaker)

st.divider()

st.subheader("🔗 Entity Relationship Diagram")

st.markdown("""
```
┌─────────────┐       cares_for        ┌─────────────┐
│  caretaker  │◄──────────────────────►│   resident  │
├─────────────┤                        ├─────────────┤
│ id          │                        │ id          │
│ name        │                        │ name        │
│ email       │                        │ room        │
│ phone       │                        │ notes       │
│ created_at  │                        │ created_at  │
└─────────────┘                        └──────┬──────┘
                                              │
                                              │ has
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │    device   │
                                       ├─────────────┤
                                       │ id          │
                                       │ resident    │◄──┐
                                       │ label       │   │
                                       │ external_id │   │
                                       │ created_at  │   │
                                       └─────────────┘   │
                                                         │
                                                         │ records
                                                         │
                                                         ▼
                                       ┌─────────────┐
                                       │  fall_event │
                                       ├─────────────┤
                                       │ id          │
                                       │ resident    │◄──┘
                                       │ detected_at │
                                       │ confidence  │
                                       │ severity    │
                                       │ source      │
                                       │ false_alarm │
                                       │ clip_uri    │
                                       │ payload     │
                                       └─────────────┘
```
""")

st.divider()

st.subheader("🔍 Sample Queries")

st.markdown("""
**SurrealQL Examples:**

```sql
-- Get all residents with high fall risk
SELECT * FROM resident WHERE 
    id IN (SELECT resident FROM fall_event WHERE severity_label = "CAT_5");

-- Get fall events for a specific resident
SELECT * FROM fall_event WHERE resident = resident:P0001
ORDER BY detected_at DESC;

-- Get caretaker assignments
SELECT * FROM cares_for;

-- Get unacknowledged fall events
SELECT * FROM fall_event WHERE acknowledged_at IS NULL;
```
""")

st.divider()

st.caption("💡 **Tip:** The database uses SurrealDB's graph capabilities to track relationships between caretakers, residents, devices, and fall events. See **Resident Management** to browse patient profiles!")
