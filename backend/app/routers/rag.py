"""HTTP endpoints for RAG (Retrieval-Augmented Generation) chat."""

from fastapi import APIRouter

from app.models.rag import (
    IngestRequest,
    IngestResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services.rag import (
    get_vector_store_stats,
    ingest_documents,
    run_rag_query,
)

router = APIRouter(tags=["rag"])


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(payload: RAGQueryRequest) -> RAGQueryResponse:
    """Query the RAG system for medical Q&A."""
    return run_rag_query(payload)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_rag_documents(payload: IngestRequest) -> IngestResponse:
    """Ingest documents into the RAG vector store."""
    result = ingest_documents(
        documents=payload.documents,
        source=payload.source,
        language=payload.language,
    )
    return IngestResponse(**result)


@router.get("/stats")
async def get_rag_stats() -> dict:
    """Get statistics about the RAG vector store."""
    return get_vector_store_stats()
