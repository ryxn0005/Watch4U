"""RAG service - Retrieval-Augmented Generation for medical Q&A using SurrealDB."""

import logging
import uuid
from typing import Any

from app.models.rag import (
    Citation,
    DocumentChunk,
    PatientContext,
    RAGQueryRequest,
    RAGQueryResponse,
)

log = logging.getLogger(__name__)

# Sample medical knowledge base for demonstration (used when SurrealDB is empty)
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


class RAGService:
    """RAG service using SurrealDB for document storage and vector search."""

    def __init__(self, db: Any):
        """Initialize RAG service with SurrealDB connection."""
        self.db = db

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text.
        
        TODO: Replace with PhoBERT for Vietnamese and multilingual model for English.
        Currently uses a simple hash-based mock embedding for demonstration.
        """
        import hashlib
        
        # Create deterministic mock embedding (768 dimensions for PhoBERT compatibility)
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Generate 768-dim vector from hash
        embedding = []
        for i in range(768):
            # Use hash bytes to create values between -1 and 1
            val = (hash_bytes[i % len(hash_bytes)] / 128.0) - 1.0
            embedding.append(val)
        
        return embedding

    async def _get_document_count(self) -> int:
        """Get total document count from SurrealDB."""
        if not self.db:
            return 0
        
        try:
            result = await self.db.query("SELECT count() FROM document GROUP BY count")
            if result and len(result) > 0:
                return result[0].get("count", 0)
            return 0
        except Exception as e:
            log.warning(f"Failed to get document count: {e}")
            return 0

    async def _retrieve_from_surrealdb(
        self, query: str, language: str, max_results: int = 3
    ) -> list[DocumentChunk]:
        """Retrieve relevant documents from SurrealDB using vector similarity."""
        if not self.db:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Use SurrealDB HNSW vector search
            # Note: <|K,EF|> is SurrealDB's K-NN operator with HNSW
            surreal_query = """
                SELECT id, content, source, language, 
                       vector::distance::knn() as distance
                FROM document
                WHERE language = $language 
                  AND embedding <|$k,40|> $query_embedding
                ORDER BY distance
                LIMIT $limit
            """
            
            result = await self.db.query(
                surreal_query,
                {
                    "language": language,
                    "k": max_results,
                    "query_embedding": query_embedding,
                    "limit": max_results,
                }
            )
            
            chunks = []
            for doc in result:
                chunks.append(
                    DocumentChunk(
                        id=str(doc.get("id")),
                        content=doc.get("content", ""),
                        source=doc.get("source", "unknown"),
                        language=doc.get("language", language),
                    )
                )
            
            return chunks
            
        except Exception as e:
            log.error(f"SurrealDB retrieval failed: {e}")
            return []

    def _retrieve_sample_knowledge(
        self, language: str, max_results: int = 3
    ) -> list[DocumentChunk]:
        """Return sample knowledge when SurrealDB is empty."""
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

    async def retrieve_relevant_chunks(
        self, query: str, language: str, max_results: int = 3
    ) -> list[DocumentChunk]:
        """Retrieve relevant document chunks based on query."""
        # Try SurrealDB first
        chunks = await self._retrieve_from_surrealdb(query, language, max_results)
        
        # Fall back to sample knowledge if SurrealDB is empty or failed
        if not chunks:
            chunks = self._retrieve_sample_knowledge(language, max_results)
            log.info(f"Using sample knowledge for query: {query[:50]}...")
        
        return chunks

    def _generate_answer(
        self, query: str, chunks: list[DocumentChunk], language: str
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

    def _get_suggested_followups(self, query: str, language: str) -> list[str]:
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

    async def run_rag_query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """Execute a RAG query and return response with citations."""
        log.info(f"RAG query: lang={request.language}, query={request.query[:50]}...")
        
        # Retrieve relevant chunks
        chunks = await self.retrieve_relevant_chunks(
            request.query, request.language, request.max_citations
        )
        
        # Generate answer
        answer, confidence = self._generate_answer(
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
        followups = self._get_suggested_followups(request.query, request.language)
        
        return RAGQueryResponse(
            answer=answer,
            language=request.language,
            citations=citations,
            confidence=confidence,
            suggested_followups=followups,
        )

    async def ingest_documents(
        self, documents: list[str], source: str, language: str
    ) -> dict[str, Any]:
        """Ingest documents into SurrealDB with embeddings."""
        if not self.db:
            log.warning("SurrealDB not available, documents not persisted")
            return {
                "chunks_created": 0,
                "source": source,
                "status": "error",
                "error": "SurrealDB not configured",
            }
        
        chunks_created = 0
        
        try:
            for doc in documents:
                # Generate embedding
                embedding = self._generate_embedding(doc)
                
                # Insert into SurrealDB
                doc_id = f"document:{uuid.uuid4()}"
                await self.db.create(
                    doc_id,
                    {
                        "content": doc,
                        "embedding": embedding,
                        "source": source,
                        "language": language,
                        "metadata": {},
                    }
                )
                chunks_created += 1
            
            log.info(f"Ingested {chunks_created} chunks from {source} ({language}) into SurrealDB")
            
            return {
                "chunks_created": chunks_created,
                "source": source,
                "status": "success",
            }
            
        except Exception as e:
            log.error(f"Failed to ingest documents: {e}")
            return {
                "chunks_created": chunks_created,
                "source": source,
                "status": "error",
                "error": str(e),
            }

    async def get_vector_store_stats(self) -> dict[str, Any]:
        """Get statistics about the vector store from SurrealDB."""
        if not self.db:
            return {
                "total_chunks": 0,
                "by_language": {},
                "by_source": {},
                "storage": "none",
            }
        
        try:
            # Get total count
            count_result = await self.db.query("SELECT count() FROM document GROUP BY count")
            total = count_result[0].get("count", 0) if count_result else 0
            
            # Get language breakdown
            lang_result = await self.db.query(
                "SELECT language, count() as count FROM document GROUP BY language"
            )
            by_language = {r["language"]: r["count"] for r in lang_result} if lang_result else {}
            
            # Get source breakdown
            source_result = await self.db.query(
                "SELECT source, count() as count FROM document GROUP BY source"
            )
            by_source = {r["source"]: r["count"] for r in source_result} if source_result else {}
            
            return {
                "total_chunks": total,
                "by_language": by_language,
                "by_source": by_source,
                "storage": "surrealdb",
            }
            
        except Exception as e:
            log.error(f"Failed to get stats: {e}")
            return {
                "total_chunks": 0,
                "by_language": {},
                "by_source": {},
                "storage": "error",
                "error": str(e),
            }


# Global service instance (initialized with DB connection)
_rag_service: RAGService | None = None


def init_rag_service(db: Any) -> RAGService:
    """Initialize the global RAG service with SurrealDB connection."""
    global _rag_service
    _rag_service = RAGService(db)
    log.info(f"RAG service initialized with {'SurrealDB' if db else 'no database'}")
    return _rag_service


def get_rag_service() -> RAGService:
    """Get the global RAG service instance."""
    if _rag_service is None:
        # Initialize with None (will use sample knowledge)
        return RAGService(None)
    return _rag_service


# Backward-compatible function exports
async def run_rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
    """Execute a RAG query (backward-compatible)."""
    service = get_rag_service()
    return await service.run_rag_query(request)


async def ingest_documents(
    documents: list[str], source: str, language: str
) -> dict[str, Any]:
    """Ingest documents (backward-compatible)."""
    service = get_rag_service()
    return await service.ingest_documents(documents, source, language)


async def get_vector_store_stats() -> dict[str, Any]:
    """Get vector store stats (backward-compatible)."""
    service = get_rag_service()
    return await service.get_vector_store_stats()
