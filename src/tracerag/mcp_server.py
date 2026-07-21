"""FastMCP server exposing the retrieval tools to the PydanticAI agent.

The server wraps :mod:`tracerag.retrieval` and exposes exactly two tools:

- ``search_procedures`` — the mandatory first step for answering a procedure
  question.
- ``get_procedure`` — fetch a full document only when a search result needs
  more context.

For local development the server can be run standalone over stdio. For tests and
the agent integration an in-memory connection is used (``Client(server)``),
which avoids any network or subprocess transport.
"""

from __future__ import annotations

from fastmcp import FastMCP

from tracerag.models import ProcedureDocument, RetrievedChunk
from tracerag.retrieval import get_procedure as _get_procedure
from tracerag.retrieval import search_procedures as _search_procedures

SERVER_NAME = "tracerag-tools"
SERVER_INSTRUCTIONS = (
    "TraceRAG operational-documentation tools. Use search_procedures as the "
    "mandatory first step for any procedural question; only call get_procedure "
    "to fetch a full document when a search result needs more context."
)

SEARCH_TOOL_DESCRIPTION = (
    "Search the approved Markdown SOP corpus for chunks relevant to a "
    "procedural question. This is the mandatory first step before answering: "
    "retrieve candidate chunks, then base every factual statement on the "
    "returned content. Returns at most `limit` scored chunks with their "
    "source document id, title, section, content, and overlap score. Chunks "
    "with no match are not returned."
)

GET_TOOL_DESCRIPTION = (
    "Fetch a full procedure document by its document id (for example "
    "'SOP-004'). Use this only when a search result needs more surrounding "
    "context than the chunk provided. Returns the document metadata and full "
    "Markdown content, or None when the document id is unknown — never invent "
    "documents."
)


def create_mcp_server() -> FastMCP:
    """Build a FastMCP server exposing the two retrieval tools."""
    server = FastMCP(name=SERVER_NAME, instructions=SERVER_INSTRUCTIONS)

    @server.tool(description=SEARCH_TOOL_DESCRIPTION)
    async def search_procedures(query: str, limit: int = 3) -> list[RetrievedChunk]:
        """Search approved SOPs for chunks relevant to a procedural question.

        Args:
            query: The operator's procedural question or key terms.
            limit: Maximum number of chunks to return (default 3).

        Returns:
            Scored chunks, highest overlap first. Empty list when nothing matches.
        """
        return await _search_procedures(query, limit=limit)

    @server.tool(description=GET_TOOL_DESCRIPTION)
    async def get_procedure(document_id: str) -> ProcedureDocument | None:
        """Fetch a full procedure document by id, or None if unknown.

        Args:
            document_id: The SOP document identifier (e.g. 'SOP-004').

        Returns:
            The full procedure document, or None for an unknown id.
        """
        return await _get_procedure(document_id)

    # Reference the registered tools so static analysis does not flag them as
    # unused; the decorator has already registered them on ``server``.
    _registered = (search_procedures, get_procedure)
    assert all(_registered)
    return server


# Module-level server for standalone execution (`python -m tracerag.mcp_server`).
mcp = create_mcp_server()


def main() -> None:
    """Run the MCP server over stdio for manual inspection."""
    mcp.run()


if __name__ == "__main__":
    main()