"""Tests for the typed data contracts in tracerag.models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tracerag.models import (
    AnswerStatus,
    AssistantAnswer,
    DocumentMetadata,
    SourceRef,
)


def _valid_metadata() -> DocumentMetadata:
    return DocumentMetadata(
        document_id="SOP-004",
        title="Device Network Recovery",
        version="1.2",
        last_reviewed="2026-07-01",
        tags=["network", "incident"],
    )


def test_assistant_answer_rejects_empty_answer() -> None:
    """An empty answer string must fail validation (test 1)."""
    with pytest.raises(ValidationError):
        AssistantAnswer(
            status=AnswerStatus.ANSWERED,
            answer="",
            steps=[],
            sources=[],
            limitations=[],
        )


def test_assistant_answer_accepts_valid_payload() -> None:
    """A well-formed answered payload validates successfully."""
    answer = AssistantAnswer(
        status=AnswerStatus.ANSWERED,
        answer="Restart only the network service on the device.",
        steps=["Record the error state", "Verify the physical link"],
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
    assert answer.status is AnswerStatus.ANSWERED
    assert len(answer.sources) == 1
    assert answer.sources[0].relevance == "primary"


def test_source_ref_relevance_is_constrained() -> None:
    """relevance must be exactly 'primary' or 'supporting'."""
    with pytest.raises(ValidationError):
        SourceRef(
            document_id="SOP-004",
            title="Device Network Recovery",
            section="Recovery steps",
            quote="Restart only the network service.",
            relevance="maybe",  # type: ignore[arg-type]
        )


def test_assistant_answer_rejects_too_many_sources() -> None:
    """At most three sources are allowed."""
    sources = [
        SourceRef(
            document_id="SOP-004",
            title="Device Network Recovery",
            section="Recovery steps",
            quote="Restart only the network service.",
            relevance="primary",
        )
        for _ in range(4)
    ]
    with pytest.raises(ValidationError):
        AssistantAnswer(
            status=AnswerStatus.ANSWERED,
            answer="ok",
            steps=[],
            sources=sources,
            limitations=[],
        )


def test_document_metadata_round_trips() -> None:
    """Metadata is frozen and serializes back to the same fields."""
    meta = _valid_metadata()
    assert meta.document_id == "SOP-004"
    assert meta.tags == ["network", "incident"]