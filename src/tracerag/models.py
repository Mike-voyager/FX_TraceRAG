"""Typed data contracts for TraceRAG.

All public and internal data contracts live here as Pydantic v2 models. No
untyped dictionaries are used for API responses or inter-module boundaries.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnswerStatus(StrEnum):
    """Outcome classification for an assistant answer."""

    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CLARIFICATION_REQUIRED = "clarification_required"


class DocumentMetadata(BaseModel):
    """Front-matter metadata for a procedure document."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=32)
    last_reviewed: str = Field(min_length=1, max_length=32)
    tags: list[str] = Field(default_factory=list[str], max_length=20)


class ProcedureDocument(BaseModel):
    """A full procedure document: metadata plus raw Markdown content."""

    model_config = ConfigDict(frozen=True)

    metadata: DocumentMetadata
    content: str = Field(min_length=1)


class RetrievedChunk(BaseModel):
    """A scored retrieval chunk drawn from a procedure document section."""

    document_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    section: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    score: float = Field(ge=0.0)


class SourceRef(BaseModel):
    """A traceable reference to a retrieved document excerpt."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    section: str = Field(min_length=1, max_length=200)
    quote: str = Field(min_length=1, max_length=500)
    relevance: Literal["primary", "supporting"]


class AssistantAnswer(BaseModel):
    """Structured, validated answer returned by the TraceRAG agent."""

    status: AnswerStatus
    answer: str = Field(min_length=1, max_length=1200)
    steps: list[str] = Field(default_factory=list[str], max_length=8)
    sources: list[SourceRef] = Field(default_factory=list[SourceRef], max_length=3)
    limitations: list[str] = Field(default_factory=list[str], max_length=3)


class AssistRequest(BaseModel):
    """Inbound request to the assistant streaming endpoint."""

    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=5, max_length=1000)
    session_id: str = Field(min_length=1, max_length=100)


# --- SSE event payload models -------------------------------------------------
# Typed payloads for the four event kinds emitted by the service layer. Phase 3
# (API/service) serializes these to the wire format; defining them here keeps
# the SSE contract typed end-to-end.


class RetrievalStartedEvent(BaseModel):
    """``retrieval_started`` event payload."""

    query: str = Field(min_length=1, max_length=1000)


class SourceSummary(BaseModel):
    """Compact source descriptor used in the ``sources_found`` event."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)


class SourcesFoundEvent(BaseModel):
    """``sources_found`` event payload."""

    count: int = Field(ge=0, le=50)
    sources: list[SourceSummary] = Field(default_factory=list[SourceSummary], max_length=50)


class AnswerReadyEvent(BaseModel):
    """``answer_ready`` event payload."""

    answer: AssistantAnswer


class DoneEvent(BaseModel):
    """``done`` event payload."""

    request_id: str = Field(min_length=1, max_length=100)
    duration_ms: int = Field(ge=0)