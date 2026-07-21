# TraceRAG

[![CI](https://github.com/Mike-voyager/FX_TraceRAG/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Mike-voyager/FX_TraceRAG/actions/workflows/ci.yml)

An async, typed RAG assistant that answers procedural questions **only from an approved local Markdown SOP corpus**, returns traceable sources and Pydantic-validated structured output, and streams typed SSE events.

## Why it exists

LLM outputs for operational documentation must be **traceable, validated, and source-grounded**. TraceRAG is a narrow engineering demonstrator that proves this: every actionable statement is backed by a retrieved document excerpt, the answer is a strict typed contract (not free-form text), and the assistant **fails closed** to an explicit `insufficient_evidence` status when evidence is absent.

## Architecture

```
Client
  |
  | POST /v1/assist/stream  (AssistRequest JSON)
  v
FastAPI + SSE  (event: retrieval_started | sources_found | answer_ready | done)
  |
  v
Service orchestration (async, asyncio.timeout)
  |
  v
PydanticAI agent  <->  MCP tools (search_procedures / get_procedure)  <->  local Markdown SOP corpus
  |
  v
Validated AssistantAnswer (Pydantic v2)
```

The agent calls the MCP retrieval tools itself — the application never pre-feeds retrieved text as fact. MCP isolates data access behind a typed tool boundary; structured output (`AssistantAnswer`) makes the model's answer safer than free-form text because the contract is validated before it reaches the client.

## Stack

Python 3.12+, `asyncio`, **FastAPI**, **Pydantic v2**, **PydanticAI**, **FastMCP**, and **Server-Sent Events** (via `sse-starlette`). Retrieval is deterministic keyword overlap over local Markdown — no vector database, embeddings, or rerankers.

## Quick start

```bash
python3.12 -m venv .venv          # requires Python >=3.12 (3.13/3.14 also fine)
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env             # edit model settings if necessary

ruff check . && pyright src/tracerag tests && pytest -q   # delivery checks
```

Run the API:

```bash
uvicorn tracerag.api:app --app-dir src --reload
# or: python -m tracerag.api
```

## Example invocation

```bash
curl -N -X POST http://127.0.0.1:8000/v1/assist/stream \
  -H 'Content-Type: application/json' \
  -d '{"question":"What should an operator do when a device loses network connectivity?","session_id":"demo-001"}'
```

## Example SSE output

```
event: retrieval_started
data: {"query":"What should an operator do when a device loses network connectivity?"}

event: sources_found
data: {"count":2,"sources":[{"document_id":"SOP-004","title":"Device Network Recovery"},{"document_id":"SOP-002","title":"Incident Response and Escalation"}]}

event: answer_ready
data: {"answer":{"status":"answered","answer":"Restart only the network service on the device, verify the physical link, and validate connectivity.","steps":["Record the error state","Verify the physical link","Restart only the network service","Validate connectivity"],"sources":[{"document_id":"SOP-004","title":"Device Network Recovery","section":"Recovery steps","quote":"Restart only the network service on the device.","relevance":"primary"}],"limitations":["A full device restart must not be performed."]}}

event: done
data: {"request_id":"94c186a3759849819a660b0103e9ac7d","duration_ms":123}
```

Negative path — a question with no matching approved procedure returns `insufficient_evidence` with no invented steps:

```
event: answer_ready
data: {"answer":{"status":"insufficient_evidence","answer":"No approved procedure covers firmware replacement order.","steps":[],"sources":[],"limitations":["An approved procedure for firmware replacement order is missing."]}}
```

## Guarantees

- **Typed API contract** — every request/response is a Pydantic model; no untyped dicts on the public boundary.
- **Structured, validated output** — `AssistantAnswer` is enforced by Pydantic before it is sent; invalid model output retries once, then fails closed.
- **Source-backed answers** — quotes are verbatim excerpts from retrieved tool results; sources not returned by a tool are never cited.
- **Explicit uncertainty** — `insufficient_evidence` and `clarification_required` statuses surface when evidence is absent or the question is ambiguous.
- **Async orchestration and timeouts** — a 30-second `asyncio.timeout` bounds every agent run; the SSE flow always completes with a `done` event.

## Limitations

- **Demonstrator, not a medical system** — the SOP corpus is fictional technical operations; it makes no medical claim and must not be used as one.
- **Local keyword retrieval, not semantic retrieval** — matching is deterministic term overlap; there are no embeddings or rerankers.
- **Model quality depends on the selected local model** — TraceRAG enforces structure and sourcing, but the quality of prose and step selection reflects the configured OpenAI-compatible model.

## Repository layout

```
src/tracerag/   settings, models, retrieval, mcp_server, agent, service, api
data/docs/      six Markdown SOPs (SOP-001 … SOP-006)
tests/          models, retrieval, mcp tools, api
docs/           architecture.md
```

## License

MIT.
