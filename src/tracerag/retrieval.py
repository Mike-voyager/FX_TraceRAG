"""Deterministic keyword retrieval over the local Markdown SOP corpus.

The public boundary is asynchronous; all synchronous I/O and CPU-bound parsing
runs through :func:`asyncio.to_thread` so the event loop is never blocked.
Documents are loaded once per resolved corpus path and cached.
"""

from __future__ import annotations

import asyncio
import math
import re
from functools import lru_cache
from pathlib import Path

from tracerag.models import DocumentMetadata, ProcedureDocument, RetrievedChunk
from tracerag.settings import get_settings

# --- Tokenization -------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokenizer; drops single-character tokens."""
    return [tok for tok in _TOKEN_RE.findall(text.lower()) if len(tok) >= 2]


# --- Front matter parsing -----------------------------------------------------

_FRONT_MATTER_RE = re.compile(
    r"\A---\s*\n(?P<body>.*?)\n---\s*\n(?P<rest>.*)\Z",
    re.DOTALL,
)
_KV_RE = re.compile(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$")


def _parse_tags(value: str) -> list[str]:
    """Parse a YAML-style inline list ``["a", "b"]`` into a list of strings."""
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    tags: list[str] = []
    for part in re.split(r"[,\s]+", inner.strip()):
        if not part:
            continue
        tags.append(_strip_quotes(part))
    return tags


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


class FrontMatter:
    """Parsed Markdown front matter: scalar fields plus tags and body content."""

    __slots__ = ("content", "scalars", "tags")

    def __init__(self, scalars: dict[str, str], tags: list[str], content: str) -> None:
        self.scalars = scalars
        self.tags = tags
        self.content = content


def _parse_front_matter(text: str) -> FrontMatter | None:
    """Split a Markdown document into front-matter fields and body content."""
    match = _FRONT_MATTER_RE.match(text)
    if match is None:
        return None
    body = match.group("body")
    content = match.group("rest")
    scalars: dict[str, str] = {}
    tags: list[str] = []
    for line in body.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        kv = _KV_RE.match(line)
        if kv is None:
            continue
        key = kv.group(1)
        raw = kv.group(2).strip()
        if key == "tags":
            tags = _parse_tags(raw)
        else:
            scalars[key] = _strip_quotes(raw)
    return FrontMatter(scalars, tags, content)


# --- Document loading ---------------------------------------------------------


def _document_from_text(path: Path, text: str) -> ProcedureDocument | None:
    parsed = _parse_front_matter(text)
    if parsed is None:
        return None
    scalars = parsed.scalars
    try:
        metadata = DocumentMetadata(
            document_id=scalars["id"],
            title=scalars["title"],
            version=scalars["version"],
            last_reviewed=scalars["last_reviewed"],
            tags=parsed.tags,
        )
    except KeyError:
        return None
    body = parsed.content.strip()
    if not body:
        return None
    return ProcedureDocument(metadata=metadata, content=body)


def _load_documents(docs_path: Path) -> list[ProcedureDocument]:
    """Read every ``*.md`` file under ``docs_path`` and parse it."""
    if not docs_path.is_dir():
        return []
    documents: list[ProcedureDocument] = []
    for path in sorted(docs_path.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        doc = _document_from_text(path, text)
        if doc is not None:
            documents.append(doc)
    return documents


# --- Chunking -----------------------------------------------------------------

_H2_RE = re.compile(r"^##[ \t]+(.+?)\s*$", re.MULTILINE)


def _split_sections(content: str) -> list[tuple[str, str]]:
    """Split Markdown body into ``(heading, body)`` pairs at H2 headings."""
    matches = list(_H2_RE.finditer(content))
    if not matches:
        return [("Overview", content.strip())]
    sections: list[tuple[str, str]] = []
    # Content before the first H2 becomes the Overview section.
    if matches[0].start() > 0:
        pre = content[: matches[0].start()].strip()
        if pre:
            sections.append(("Overview", pre))
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append((heading, body))
    return sections


def _chunk_document(doc: ProcedureDocument) -> list[RetrievedChunk]:
    """Produce unscored chunks (``score=0``) for a document."""
    chunks: list[RetrievedChunk] = []
    for section, body in _split_sections(doc.content):
        if not body:
            continue
        chunks.append(
            RetrievedChunk(
                document_id=doc.metadata.document_id,
                title=doc.metadata.title,
                section=section,
                content=body,
                score=0.0,
            )
        )
    return chunks


# --- Scoring ------------------------------------------------------------------


def _score_chunk(query_terms: set[str], chunk: RetrievedChunk) -> float:
    """Deterministic unique-term overlap score.

    Rewarded metric: the fraction of *unique* query terms that appear in the
    chunk, scaled by ``1/sqrt(|unique query terms|)`` so short, highly specific
    queries are not penalized relative to long ones.
    """
    if not query_terms:
        return 0.0
    chunk_terms = set(_tokenize(f"{chunk.section} {chunk.content}"))
    overlap = query_terms & chunk_terms
    return len(overlap) / math.sqrt(len(query_terms))


# --- Cache --------------------------------------------------------------------


@lru_cache(maxsize=8)
def _cached_documents(docs_path_str: str) -> tuple[ProcedureDocument, ...]:
    docs = _load_documents(Path(docs_path_str))
    return tuple(docs)


@lru_cache(maxsize=8)
def _cached_chunks(docs_path_str: str) -> tuple[RetrievedChunk, ...]:
    docs = _cached_documents(docs_path_str)
    chunks: list[RetrievedChunk] = []
    for doc in docs:
        chunks.extend(_chunk_document(doc))
    return tuple(chunks)


def _docs_path() -> Path:
    return get_settings().docs_path_resolved


# --- Public async API ---------------------------------------------------------


async def search_procedures(query: str, limit: int = 3) -> list[RetrievedChunk]:
    """Search the corpus for chunks matching ``query``.

    Returns at most ``limit`` chunks with a positive score, sorted by score
    descending with a deterministic tie-breaker.
    """
    docs_path = _docs_path()
    query_terms = set(_tokenize(query))

    def _search() -> list[RetrievedChunk]:
        chunks = _cached_chunks(str(docs_path))
        scored: list[RetrievedChunk] = []
        for chunk in chunks:
            score = _score_chunk(query_terms, chunk)
            if score > 0.0:
                scored.append(
                    chunk.model_copy(update={"score": round(score, 6)})
                )
        # Deterministic order: highest score first, then document_id, section.
        scored.sort(key=lambda c: (-c.score, c.document_id, c.section))
        return scored[:limit]

    return await asyncio.to_thread(_search)


async def get_procedure(document_id: str) -> ProcedureDocument | None:
    """Return the full procedure document for ``document_id`` or ``None``.

    Unknown identifiers return ``None``; retrieval never invents documents.
    """
    docs_path = _docs_path()

    def _get() -> ProcedureDocument | None:
        for doc in _cached_documents(str(docs_path)):
            if doc.metadata.document_id == document_id:
                return doc
        return None

    return await asyncio.to_thread(_get)


def clear_caches() -> None:
    """Clear the document/chunk caches. Intended for tests and reloads."""
    _cached_documents.cache_clear()
    _cached_chunks.cache_clear()