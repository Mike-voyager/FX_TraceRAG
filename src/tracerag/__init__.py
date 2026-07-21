"""TraceRAG — async, typed RAG assistant for operational documentation."""

from tracerag.models import (
    AnswerStatus,
    AssistantAnswer,
    AssistRequest,
    DocumentMetadata,
    ProcedureDocument,
    RetrievedChunk,
    SourceRef,
)

__version__ = "0.1.0"

__all__ = [
    "AnswerStatus",
    "AssistRequest",
    "AssistantAnswer",
    "DocumentMetadata",
    "ProcedureDocument",
    "RetrievedChunk",
    "SourceRef",
    "__version__",
]