"""Tests for the deterministic retrieval layer (tests 2-5)."""

from __future__ import annotations

from tracerag.models import RetrievedChunk
from tracerag.retrieval import get_procedure, search_procedures


async def test_network_query_returns_sop_004_chunk() -> None:
    """A network connectivity query must surface a chunk from SOP-004 (test 2)."""
    chunks = await search_procedures("network connectivity lost")
    assert chunks, "expected at least one matching chunk"
    assert any(c.document_id == "SOP-004" for c in chunks)
    top = chunks[0]
    assert isinstance(top, RetrievedChunk)
    assert top.score > 0.0


async def test_nonsense_query_returns_no_chunks() -> None:
    """An unrelated nonsense query must return no chunks (test 3)."""
    chunks = await search_procedures("zzqx wibble flonk")
    assert chunks == []


async def test_get_procedure_returns_sop_004() -> None:
    """get_procedure returns the expected procedure for a known id (test 4)."""
    doc = await get_procedure("SOP-004")
    assert doc is not None
    assert doc.metadata.document_id == "SOP-004"
    assert doc.metadata.title == "Device Network Recovery"
    assert "network service" in doc.content


async def test_get_procedure_unknown_returns_none() -> None:
    """get_procedure returns None for an unknown document id (test 5)."""
    doc = await get_procedure("SOP-999")
    assert doc is None


async def test_search_results_are_sorted_and_limited() -> None:
    """Results are sorted by score desc and capped at the requested limit."""
    chunks = await search_procedures("device network recovery", limit=2)
    assert len(chunks) <= 2
    if len(chunks) >= 2:
        assert chunks[0].score >= chunks[1].score
    for chunk in chunks:
        assert chunk.document_id.startswith("SOP-")