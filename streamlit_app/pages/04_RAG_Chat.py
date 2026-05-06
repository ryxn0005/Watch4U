"""RAG Chat demo (Ryan)."""
import streamlit as st

from lib.api_client import get, health, post

st.set_page_config(page_title="RAG Chat - Watch4U", page_icon="💬")

st.title("RAG Chat")
st.caption("Owner: Ryan · backend/app/services/rag/")

# Backend connectivity check
try:
    backend_health = health()
    rag_health = get("/api/rag/stats")
    st.success(f"✅ Backend: {backend_health.get('status')} | RAG vector store: {rag_health.get('total_chunks', 0)} chunks")
except Exception as e:
    st.error(f"❌ Backend connection failed: {e}")
    st.stop()

st.markdown("---")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "language" not in st.session_state:
    st.session_state.language = "en"

# Language selection
st.session_state.language = st.selectbox(
    "Language / Ngôn ngữ",
    ["en", "vi"],
    format_func=lambda x: "English" if x == "en" else "Tiếng Việt",
)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            with st.expander("📚 Citations"):
                for citation in message["citations"]:
                    st.markdown(f"**{citation.get('source', 'Unknown')}**")
                    st.text(citation.get('content', '')[:200] + "...")

# Chat input
lang_label = "Ask a medical question..." if st.session_state.language == "en" else "Hỏi về y tế..."

if prompt := st.chat_input(lang_label):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..." if st.session_state.language == "en" else "Đang suy nghĩ..."):
            try:
                result = post("/api/rag/query", json={
                    "query": prompt,
                    "language": st.session_state.language,
                    "max_citations": 3,
                })
                
                answer = result.get("answer", "No response")
                citations = result.get("citations", [])
                confidence = result.get("confidence", 0)
                suggested = result.get("suggested_followups", [])
                
                # Display answer
                st.markdown(answer)
                
                # Show confidence
                st.caption(f"Confidence: {confidence:.1%}")
                
                # Citations
                if citations:
                    with st.expander("📚 Sources"):
                        for citation in citations:
                            st.markdown(f"**{citation.get('source', 'Unknown')}** (score: {citation.get('score', 0):.2f})")
                            st.text(citation.get('content', '')[:300] + "...")
                            st.markdown("---")
                
                # Suggested followups
                if suggested:
                    st.markdown("**Suggested follow-up questions:**")
                    for q in suggested[:3]:
                        st.markdown(f"- {q}")
                
                # Store assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "citations": citations,
                })
                
            except Exception as e:
                error_msg = "Sorry, I couldn't process your question." if st.session_state.language == "en" else "Xin lỗi, tôi không thể xử lý câu hỏi của bạn."
                st.error(f"{error_msg} ({e})")

# Sidebar with info
with st.sidebar:
    st.header("About RAG")
    st.markdown("""
    **Retrieval-Augmented Generation** combines:
    1. **Retrieval**: Finding relevant medical documents
    2. **Generation**: Creating contextual answers
    
    **Supported Corpora:**
    - ViMQ (Vietnamese Medical QA)
    - VietMed-NER
    - ViMedical Disease
    - English clinical references
    
    **Features:**
    - Multilingual (EN/VI)
    - Citations for every answer
    - Confidence scoring
    """)
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Vector store stats
    st.markdown("---")
    st.subheader("Vector Store Stats")
    try:
        stats = get("/api/rag/stats")
        st.metric("Total Chunks", stats.get("total_chunks", 0))
        by_lang = stats.get("by_language", {})
        for lang, count in by_lang.items():
            st.text(f"{lang}: {count} chunks")
    except:
        st.text("Stats unavailable")

st.markdown("---")
st.caption("This demo connects to `/api/rag/query` endpoint")
