"""HTTP endpoints for RAG (Retrieval-Augmented Generation) chat."""

from fastapi import APIRouter, Request

from app.models.rag import (
    IngestRequest,
    IngestResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services.rag.service import (
    get_vector_store_stats,
    ingest_documents,
    init_rag_service,
    run_rag_query,
)

router = APIRouter(tags=["rag"])


def _get_db(request: Request):
    """Get SurrealDB connection from app state."""
    return getattr(request.app.state, "surreal", None)


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: Request, payload: RAGQueryRequest) -> RAGQueryResponse:
    """Query the RAG system for medical Q&A."""
    db = _get_db(request)
    init_rag_service(db)
    return await run_rag_query(payload)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_rag_documents(request: Request, payload: IngestRequest) -> IngestResponse:
    """Ingest documents into the RAG vector store."""
    db = _get_db(request)
    init_rag_service(db)
    result = await ingest_documents(
        documents=payload.documents,
        source=payload.source,
        language=payload.language,
    )
    return IngestResponse(**result)


@router.get("/stats")
async def get_rag_stats(request: Request) -> dict:
    """Get statistics about the RAG vector store."""
    db = _get_db(request)
    init_rag_service(db)
    return await get_vector_store_stats()
