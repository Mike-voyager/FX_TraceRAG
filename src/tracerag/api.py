"""FastAPI application exposing the TraceRAG streaming assist endpoint.

Endpoints:

- ``GET /health`` returns a typed ``{"status": "ok"}`` JSON object.
- ``POST /v1/assist/stream`` accepts an :class:`AssistRequest` and returns a
  ``text/event-stream`` of the four SSE events produced by :func:`tracerag.service.assist`.

SSE responses carry no-cache / no-buffering headers so intermediaries forward
events immediately. No HTML frontend is provided.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI
from sse_starlette.event import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

from tracerag.models import AssistRequest
from tracerag.service import assist
from tracerag.settings import get_settings

logger = logging.getLogger("tracerag.api")

SSE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def create_app() -> FastAPI:
    """Build the FastAPI application instance."""
    app = FastAPI(
        title="TraceRAG",
        description=(
            "Async, typed RAG assistant for operational documentation. "
            "Answers procedural questions from an approved local Markdown SOP "
            "corpus via MCP tools and streams typed SSE events."
        ),
        version="0.1.0",
    )

    @app.get("/health", tags=["health"], summary="Service health check")
    async def health() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        """Return a typed service-health object."""
        return {"status": "ok"}

    @app.post(
        "/v1/assist/stream",
        tags=["assist"],
        summary="Stream a procedural answer as SSE events",
        response_class=EventSourceResponse,
        responses={200: {"content": {"text/event-stream": {}}}},
    )
    async def assist_stream(  # pyright: ignore[reportUnusedFunction]
        request: AssistRequest,
    ) -> EventSourceResponse:
        """Stream the four SSE events (retrieval_started, sources_found,
        answer_ready, done) for a procedural question.
        """
        events: AsyncIterator[ServerSentEvent] = assist(request)
        return EventSourceResponse(events, headers=SSE_HEADERS)

    return app


app = create_app()


def main() -> None:
    """Run the API with uvicorn for `tracerag` console script and `python -m`."""
    import uvicorn

    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    uvicorn.run(
        "tracerag.api:app",
        host="127.0.0.1",
        port=8000,
        app_dir="src",
        reload=False,
    )


if __name__ == "__main__":
    main()