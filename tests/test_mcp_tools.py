"""Tests for the FastMCP tools exposed by tracerag.mcp_server (test 6).

Tools are exercised over an in-memory FastMCP client (``Client(server)``) so
no network or subprocess transport is needed and no LLM is involved.
"""

from __future__ import annotations

import json
from typing import Any, cast

from fastmcp import Client

from tracerag.mcp_server import create_mcp_server


async def test_server_exposes_exactly_two_tools() -> None:
    """The server must expose search_procedures and get_procedure only."""
    server = create_mcp_server()
    async with Client(server) as client:
        names = {tool.name for tool in await client.list_tools()}
    assert names == {"search_procedures", "get_procedure"}


async def test_search_tool_returns_typed_serializable_results() -> None:
    """MCP search results are typed, structured, and JSON-serializable (test 6)."""
    server = create_mcp_server()
    async with Client(server) as client:
        result = await client.call_tool(
            "search_procedures",
            {"query": "network connectivity lost", "limit": 3},
        )

    # Structured content is a JSON-compatible mapping the agent can consume.
    structured = cast(dict[str, Any], result.structured_content)
    assert "result" in structured
    chunks = cast(list[dict[str, Any]], structured["result"])
    assert chunks, "expected at least one chunk for a network query"

    # Each chunk carries the typed fields a SourceRef can be built from.
    first = chunks[0]
    assert first["document_id"] == "SOP-004"
    assert "title" in first and "section" in first and "content" in first
    assert isinstance(first["score"], (int, float))
    assert first["score"] > 0.0

    # The whole payload round-trips through JSON (serializable, no pydantic objs).
    encoded = json.dumps(structured)
    decoded = json.loads(encoded)
    assert cast(list[dict[str, Any]], decoded["result"])[0]["document_id"] == "SOP-004"


async def test_search_tool_limit_is_respected() -> None:
    """The limit argument caps the number of returned chunks."""
    server = create_mcp_server()
    async with Client(server) as client:
        result = await client.call_tool(
            "search_procedures", {"query": "device network", "limit": 1}
        )
    structured = cast(dict[str, Any], result.structured_content)
    chunks = cast(list[dict[str, Any]], structured["result"])
    assert len(chunks) <= 1


async def test_get_tool_returns_full_document_and_none_for_unknown() -> None:
    """get_procedure returns the full document for a known id and None unknown."""
    server = create_mcp_server()
    async with Client(server) as client:
        known = await client.call_tool("get_procedure", {"document_id": "SOP-004"})
        unknown = await client.call_tool("get_procedure", {"document_id": "SOP-999"})

    known_envelope = cast(dict[str, Any], known.structured_content)
    known_data = cast(dict[str, Any], known_envelope["result"])
    assert known_data is not None
    assert known_data["metadata"]["document_id"] == "SOP-004"
    assert "content" in known_data
    assert "network service" in known_data["content"]
    unknown_envelope = cast(dict[str, Any], unknown.structured_content)
    assert unknown_envelope["result"] is None


async def test_tool_descriptions_guide_the_llm() -> None:
    """Tool descriptions explain search-first semantics for the agent."""
    server = create_mcp_server()
    async with Client(server) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    search_desc = tools["search_procedures"].description or ""
    get_desc = tools["get_procedure"].description or ""
    assert "mandatory" in search_desc.lower()
    assert "only" in get_desc.lower() or "when" in get_desc.lower()