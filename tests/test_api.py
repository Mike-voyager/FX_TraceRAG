"""Tests for the FastAPI application (tests 7 and 8).

No real LLM is called: the agent boundary is stubbed by monkeypatching
``tracerag.service.run_agent`` so the SSE flow is exercised end to end without
Ollama.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from tracerag import service
from tracerag.api import app
from tracerag.models import AnswerStatus, AssistantAnswer, SourceRef


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


async def _answered_stub(question: str) -> AssistantAnswer:
    return AssistantAnswer(
        status=AnswerStatus.ANSWERED,
        answer="Restart only the network service on the device.",
        steps=["Record the error state", "Verify the physical link", "Restart the network service"],
        sources=[
            SourceRef(
                document_id="SOP-004",
                title="Device Network Recovery",
                section="Recovery steps",
                quote="Restart only the network service on the device.",
                relevance="primary",
            )
        ],
        limitations=["A full device restart must not be performed."],
    )


async def _insufficient_stub(question: str) -> AssistantAnswer:
    return AssistantAnswer(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        answer="No approved procedure covers firmware replacement order.",
        steps=[],
        sources=[],
        limitations=["An approved procedure for firmware replacement order is missing."],
    )


def _parse_events(body: str) -> list[tuple[str, str]]:
    """Parse an SSE body into ordered (event, data) pairs."""
    events: list[tuple[str, str]] = []
    current_event = ""
    current_data: list[str] = []
    for line in body.splitlines():
        if line.startswith("event:"):
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            current_data.append(line[len("data:"):].strip())
        elif line == "":
            if current_event:
                events.append((current_event, "\n".join(current_data)))
            current_event = ""
            current_data = []
    return events


def test_health_returns_ok(client: TestClient) -> None:
    """GET /health returns HTTP 200 and typed {"status":"ok"} (test 7)."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_assist_stream_event_order_with_stubbed_agent(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The SSE stream emits the four event kinds in order (test 8)."""
    monkeypatch.setattr(service, "run_agent", _answered_stub)
    response = client.post(
        "/v1/assist/stream",
        json={"question": "What should an operator do when a device loses network connectivity?", "session_id": "demo-001"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "no-cache" in response.headers.get("cache-control", "")

    events = _parse_events(response.text)
    names = [name for name, _ in events]
    assert names == ["retrieval_started", "sources_found", "answer_ready", "done"]

    # sources_found exposes SOP-004 among the preliminary sources.
    sources_payload = json.loads(events[1][1])
    doc_ids = {s["document_id"] for s in sources_payload["sources"]}
    assert "SOP-004" in doc_ids

    # answer_ready serializes a valid answered AssistantAnswer referencing SOP-004.
    answer_payload = json.loads(events[2][1])["answer"]
    assert answer_payload["status"] == "answered"
    assert answer_payload["answer"]
    assert any(src["document_id"] == "SOP-004" for src in answer_payload["sources"])

    # done carries a request id and a non-negative duration.
    done_payload = json.loads(events[3][1])
    assert done_payload["request_id"]
    assert done_payload["duration_ms"] >= 0


def test_assist_stream_fail_closed_on_insufficient_evidence(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Negative path: insufficient_evidence still completes the four-event flow."""
    monkeypatch.setattr(service, "run_agent", _insufficient_stub)
    response = client.post(
        "/v1/assist/stream",
        json={"question": "In which order should I replace the device firmware?", "session_id": "demo-002"},
    )
    assert response.status_code == 200
    events = _parse_events(response.text)
    names = [name for name, _ in events]
    assert names == ["retrieval_started", "sources_found", "answer_ready", "done"]
    answer = json.loads(events[2][1])["answer"]
    assert answer["status"] == "insufficient_evidence"
    assert answer["steps"] == []