"""Async SSE orchestration for the /v1/assist/stream endpoint.

:func:`assist` is the single orchestration entry point. It emits exactly four
event kinds for a successful request, in order:

1. ``retrieval_started``   — echoes the query for client-side progress.
2. ``sources_found``        — preliminary retrieval results (user-visible).
3. ``answer_ready``         — the validated :class:`AssistantAnswer`.
4. ``done``                 — request id and elapsed time in ms.

The agent still calls the MCP retrieval tools itself; the preliminary retrieval
in ``sources_found`` is only progress feedback, never treated as the agent's
tool call. Internal failures never surface stack traces to the client: the
service always emits a valid ``insufficient_evidence`` ``answer_ready`` and a
``done`` event.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator

from sse_starlette.event import ServerSentEvent

from tracerag.agent import run_agent
from tracerag.models import (
    AnswerReadyEvent,
    AnswerStatus,
    AssistantAnswer,
    AssistRequest,
    DoneEvent,
    RetrievalStartedEvent,
    SourcesFoundEvent,
    SourceSummary,
)
from tracerag.retrieval import search_procedures

logger = logging.getLogger("tracerag.service")

# Monotonic-ish timing using a perf counter avoids wall-clock drift and keeps
# ``duration_ms`` deterministic within a single request.
_PRELIMINARY_LIMIT: int = 3


def _insufficient_answer(message: str) -> AssistantAnswer:
    return AssistantAnswer(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        answer=message,
        steps=[],
        sources=[],
        limitations=["A validated answer could not be produced from the available evidence."],
    )


async def assist(request: AssistRequest) -> AsyncIterator[ServerSentEvent]:
    """Yield the four SSE events for an assistance request.

    Yields:
        ServerSentEvent objects in the required order. On internal failure a
        valid ``insufficient_evidence`` ``answer_ready`` is still emitted
        before ``done``.
    """
    request_id = uuid.uuid4().hex
    start = time.perf_counter()
    query = request.question

    # 1. retrieval_started
    yield ServerSentEvent(
        event="retrieval_started",
        data=RetrievalStartedEvent(query=query).model_dump_json(),
    )

    # 2. sources_found (preliminary progress; the agent still calls tools itself)
    try:
        preliminary = await search_procedures(query, limit=_PRELIMINARY_LIMIT)
        summaries = [
            SourceSummary(document_id=c.document_id, title=c.title) for c in preliminary
        ]
        sources_event = SourcesFoundEvent(count=len(summaries), sources=summaries)
    except Exception:
        logger.exception("preliminary retrieval failed")
        sources_event = SourcesFoundEvent(count=0, sources=[])
    yield ServerSentEvent(
        event="sources_found",
        data=sources_event.model_dump_json(),
    )

    # 3. answer_ready (fail closed; never expose internals)
    try:
        answer = await run_agent(query)
    except Exception:
        logger.exception("agent invocation failed; failing closed")
        answer = _insufficient_answer("The assistant could not produce a validated answer.")
    answer_event = AnswerReadyEvent(answer=answer)
    yield ServerSentEvent(
        event="answer_ready",
        data=answer_event.model_dump_json(),
    )

    # 4. done
    duration_ms = int((time.perf_counter() - start) * 1000)
    done_event = DoneEvent(request_id=request_id, duration_ms=duration_ms)
    yield ServerSentEvent(
        event="done",
        data=done_event.model_dump_json(),
    )


def encode_event(event: ServerSentEvent) -> str:
    """Render a ServerSentEvent to the SSE wire format (debug/test helper)."""
    # Reuse sse-starlette's encoder for correctness, then decode to str.
    return event.encode().decode("utf-8")


__all__ = ["assist", "encode_event"]