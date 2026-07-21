# TraceRAG Architecture

## Components

```
            +---------------------+
request --->| FastAPI (api.py)    |--- GET  /health           -> {"status":"ok"}
            |                     |--- POST /v1/assist/stream -> text/event-stream
            +----------+----------+
                       |
                       v
            +---------------------+
            | service.py           |  async assist() -> SSE
            |  retrieval_started   |  preliminary search (progress only)
            |  sources_found       |
            |  answer_ready        |
            |  done                |
            +----------+----------+
                       |
                       v
            +----------------------+         +------------------------+
            | agent.py (PydanticAI)|--MCP--> | mcp_server.py (FastMCP)|
            |  OpenAI-compatible   |<--tools-|  search_procedures     |
            |  output: AssistantAns|         |  get_procedure         |
            +----------+-----------+         +-----------+------------+
                       |                                 |
                       v                                 v
            +---------------------+          +-----------------------+
            | models.py (Pydantic)|          | retrieval.py          |
            |  AssistantAnswer    |          |  local Markdown SOPs  |
            |  validated contract |          |  deterministic overlap|
            +---------------------+          +-----------------------+
```

## Data flow (request → SSE response)

1. `POST /v1/assist/stream` accepts a validated `AssistRequest` (`question`, `session_id`).
2. `service.assist` emits `retrieval_started` with the query.
3. It runs a **preliminary** keyword search for user-visible progress (`sources_found`); this is not the agent's tool call.
4. `run_agent` runs the PydanticAI agent under a 30-second `asyncio.timeout`. The agent calls the MCP tools (`search_procedures`, then optionally `get_procedure`) and returns a validated `AssistantAnswer`.
5. `answer_ready` serializes that `AssistantAnswer`; `done` carries the request id and elapsed ms.

## Why MCP tools isolate data access

Retrieval lives behind a FastMCP tool boundary. The agent never reads files directly — it discovers documents through `search_procedures` and `get_procedure`. This means the corpus, scoring, and the "unknown id → None" rule are enforced in one place (`retrieval.py`) and reused identically by the agent and the in-memory client used in tests. The agent cannot invent document ids: a tool that returns `None` for an unknown id is the only source of documents. Swapping the retrieval implementation (e.g. for a real index later) changes one module, not the agent contract.

## Why structured output is safer than free-form text

`AssistantAnswer` is a Pydantic model with constrained fields: `status` is an enum, `answer` is length-bounded, `sources` is capped at three, and each `SourceRef.quote` is a length-bounded string. The model is forced to emit JSON that validates against this schema before it is returned, so the client always receives a well-formed object — never a half-broken paragraph. Sources that were not returned by a tool cannot be cited because the agent builds them from tool results. When the model cannot satisfy the schema after one retry, the agent returns an explicit `insufficient_evidence` answer instead of an unstructured apology.

## Failure behavior

- **Timeout**: `asyncio.timeout(30)` cancels a slow run; `run_agent` returns `insufficient_evidence` ("did not respond within the time limit").
- **Validation retry**: on a validation or model-behavior error, the run is retried once with a concise correction instruction; a second failure returns `insufficient_evidence` ("a validated answer could not be produced"). There is no indefinite loop.
- **Internal failure**: `service.assist` still emits `answer_ready` with a valid `insufficient_evidence` answer and a `done` event; stack traces are logged, never sent to the client.
- **Unknown document**: `get_procedure("SOP-999")` returns `None`; retrieval never fabricates documents.
