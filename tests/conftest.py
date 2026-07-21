"""Shared pytest fixtures for TraceRAG tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from tracerag import retrieval
from tracerag.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = REPO_ROOT / "data" / "docs"


@pytest.fixture(autouse=True)
def _isolate_corpus(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:  # pyright: ignore[reportUnusedFunction]
    """Pin the corpus path to the repo's data/docs and clear retrieval caches."""
    settings = get_settings()
    monkeypatch.setattr(settings, "docs_path", CORPUS_PATH)
    retrieval.clear_caches()
    yield
    retrieval.clear_caches()