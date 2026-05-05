"""RAG service - Retrieval-Augmented Generation for medical Q&A."""

import logging
from typing import Any

from app.models.rag import (
    Citation,
    DocumentChunk,
    PatientContext,
    RAGQueryRequest,
    RAGQueryResponse,
)

log = logging.getLogger(__name__)

# In-memory vector store (replace with Chroma/Qdrant in production)
_vector_store: list[DocumentChunk] = []

# Sample medical knowledge base for demonstration
_SAMPLE_KNOWLEDGE = {
    "en": [
        {
            "content": "Fall prevention in elderly: Remove tripping hazards like loose rugs, ensure adequate lighting, install grab bars in bathrooms, and encourage regular exercise to maintain strength and balance.",
            "source": "CDC_Fall_Prevention",
        },
        {
            "content": "Signs of serious fall injury: Loss of consciousness, severe headache, vomiting, confusion, inability to move limbs, severe pain, or visible deformity. Call emergency services immediately.",
            "source": "Mayo_Clinic",
        },
        {
            "content": "Blood thinners and fall risk: Patients on anticoagulants (warfarin, apixaban) have higher risk of internal bleeding after falls. Even minor head bumps require medical evaluation.",
            "source": "AHA_Guidelines",
        },
        {
            "content": "Osteoporosis management: Weight-bearing exercises, calcium (1200mg/day) and vitamin D (800-1000 IU/day) supplementation, and fall prevention strategies are essential.",
            "source": "NIH_Osteoporosis",
        },
    ],
    "vi": [
        {
            "content": "Phòng ngừa té ngã ở ngưởi cao tuổi: Loại bỏ các vật cản như thảm trơn, đảm bảo ánh sáng đầy đủ, lắp thanh vịn trong phòng tắm, và khuyến khích tập thể dục thường xuyên.",
            "source": "CDC_Fall_Prevention",
        },
        {
            "content": "Dấu hiệu chấn thương nghiêm trọng sau khi té: Mất ý thức, đau đầu dữ dội, nôn mửa, lú lẫn, không cử động được chi, đau dữ dội. Gọi cấp cứu ngay lập tức.",
            "source": "Mayo_Clinic",
        },
        {
            "content": "Thuốc làm loãng máu và nguy cơ té ngã: Bệnh nhân dùng thuốc chống đông (warfarin, apixaban) có nguy cơ chảy máu nội cao hơn sau khi té. Ngay cả va đầu nhẹ cũng cần được đánh giá y tế.",
            "source": "AHA_Guidelines",
        },
        {
            "content": "Quản lý loãng xương: Tập thể dục chịu lực, bổ sung canxi (1200mg/ngày) và vitamin D (800-1000 IU/ngày), và các biện pháp phòng ngừa té ngã là cần thiết.",
            "source": "NIH_Osteoporosis",
        },
    ],
}


def _simple_similarity(query: str, content: str) -> float:
    """Simple word overlap similarity (replace with embeddings in production)."""
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    if not query_words:
        return 0.0
    return len(query_words & content_words) / len(query_words)


def _retrieve_relevant_chunks(
    query: str, language: str, max_results: int = 3
) -> list[DocumentChunk]:
    """Retrieve relevant document chunks based on query."""
    if not _vector_store:
        # Return sample knowledge if store is empty
        samples = _SAMPLE_KNOWLEDGE.get(language, _SAMPLE_KNOWLEDGE["en"])
        return [
            DocumentChunk(
                id=f"sample_{i}",
                content=s["content"],
                source=s["source"],
                language=language,
            )
            for i, s in enumerate(samples[:max_results])
        ]
    
    # Score and rank chunks
    scored = []
    for chunk in _vector_store:
        if chunk.language == language or language == "auto":
            score = _simple_similarity(query, chunk.content)
            scored.append((score, chunk))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:max_results]]


def _generate_answer(
    query: str, chunks: list[DocumentChunk], language: str
) -> tuple[str, float]:
    """Generate answer from retrieved chunks (simplified - no LLM for now)."""
    if not chunks:
        if language == "vi":
            return "Xin lỗi, tôi không tìm thấy thông tin liên quan để trả lởi câu hỏi của bạn.", 0.0
        return "I apologize, but I couldn't find relevant information to answer your question.", 0.0
    
    # Simple extraction-based answer
    answer_parts = []
    for chunk in chunks:
        answer_parts.append(chunk.content)
    
    answer = " ".join(answer_parts)
    confidence = min(0.7 + (len(chunks) * 0.1), 0.95)
    
    return answer, confidence


def _get_suggested_followups(query: str, language: str) -> list[str]:
    """Generate suggested follow-up questions."""
    if language == "vi":
        return [
            "Tôi nên làm gì nếu ngưởi thân té ngã?",
            "Dấu hiệu nào cho thấy cần gọi cấp cứu?",
            "Làm thế nào để phòng ngừa té ngã ở nhà?",
        ]
    return [
        "What should I do if my elderly parent falls?",
        "What are warning signs that require emergency care?",
        "How can I make my home safer to prevent falls?",
    ]


def run_rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
    """Execute a RAG query and return response with citations."""
    log.info(f"RAG query: lang={request.language}, query={request.query[:50]}...")
    
    # Retrieve relevant chunks
    chunks = _retrieve_relevant_chunks(
        request.query, request.language, request.max_citations
    )
    
    # Generate answer
    answer, confidence = _generate_answer(
        request.query, chunks, request.language
    )
    
    # Build citations
    citations = [
        Citation(
            source=chunk.source,
            chunk_id=chunk.id,
            content=chunk.content,
            score=0.8,  # Placeholder score
        )
        for chunk in chunks
    ]
    
    # Get suggested followups
    followups = _get_suggested_followups(request.query, request.language)
    
    return RAGQueryResponse(
        answer=answer,
        language=request.language,
        citations=citations,
        confidence=confidence,
        suggested_followups=followups,
    )


def ingest_documents(
    documents: list[str], source: str, language: str
) -> dict[str, Any]:
    """Ingest documents into the vector store."""
    chunks_created = 0
    
    for i, doc in enumerate(documents):
        chunk = DocumentChunk(
            id=f"{source}_{language}_{i}",
            content=doc,
            source=source,
            language=language,
        )
        _vector_store.append(chunk)
        chunks_created += 1
    
    log.info(f"Ingested {chunks_created} chunks from {source} ({language})")
    
    return {
        "chunks_created": chunks_created,
        "source": source,
        "status": "success",
    }


def get_vector_store_stats() -> dict[str, Any]:
    """Get statistics about the vector store."""
    by_language: dict[str, int] = {}
    by_source: dict[str, int] = {}
    
    for chunk in _vector_store:
        by_language[chunk.language] = by_language.get(chunk.language, 0) + 1
        by_source[chunk.source] = by_source.get(chunk.source, 0) + 1
    
    return {
        "total_chunks": len(_vector_store),
        "by_language": by_language,
        "by_source": by_source,
    }
