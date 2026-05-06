"""Pydantic models for RAG (Retrieval-Augmented Generation) chat."""

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class Citation(BaseModel):
    """Citation for a retrieved document chunk."""
    source: str = Field(..., description="Source document name")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Retrieved chunk content")
    score: float = Field(default=0.0, description="Retrieval relevance score")


class PatientContext(BaseModel):
    """Optional patient context for personalized responses."""
    patient_id: str | None = None
    age: int | None = Field(default=None, ge=0)
    medical_conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    mobility_status: str | None = None
    language_preference: str = "en"


class RAGQueryRequest(BaseModel):
    """Request model for RAG chat queries."""
    query: str = Field(..., description="User query in EN or VI")
    language: str = Field(default="en", description="Query language: 'en' or 'vi'")
    patient_context: PatientContext | None = Field(default=None, description="Optional patient context")
    chat_history: list[ChatMessage] = Field(default_factory=list, description="Previous conversation history")
    max_citations: int = Field(default=3, ge=1, le=10, description="Maximum citations to return")


class RAGQueryResponse(BaseModel):
    """Response model for RAG chat queries."""
    answer: str = Field(..., description="Generated answer in query language")
    language: str = Field(..., description="Response language")
    citations: list[Citation] = Field(default_factory=list, description="Source citations")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Answer confidence score")
    suggested_followups: list[str] = Field(default_factory=list, description="Suggested follow-up questions")


class DocumentChunk(BaseModel):
    """Internal model for document chunks in the vector store."""
    id: str
    content: str
    source: str
    language: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    """Request to ingest documents into the RAG system."""
    documents: list[str] = Field(..., description="List of document texts to ingest")
    source: str = Field(..., description="Source identifier (e.g., 'vimq', 'vietmed')")
    language: str = Field(default="en", description="Document language")


class IngestResponse(BaseModel):
    """Response after document ingestion."""
    chunks_created: int
    source: str
    status: str
