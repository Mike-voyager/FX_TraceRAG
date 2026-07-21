"""PydanticAI agent that answers procedural questions through MCP tools.

The agent uses the OpenAI-compatible model configured via environment
variables, exposes the retrieval tools through a PydanticAI MCP toolset, and
returns a validated :class:`AssistantAnswer`. Output is strictly typed — the
agent never produces free-form text to the caller.

Failure handling follows the spec:

- a 30-second ``asyncio.timeout`` wraps every agent run;
- if the model output fails validation or the model misbehaves, the run is
  retried once with a concise correction instruction (no indefinite loop);
- on the second failure, or on timeout, the agent fails closed to a valid
  ``insufficient_evidence`` :class:`AssistantAnswer`.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from fastmcp import Client
from pydantic import ValidationError
from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from tracerag.mcp_server import create_mcp_server
from tracerag.models import AnswerStatus, AssistantAnswer
from tracerag.settings import Settings, get_settings

logger = logging.getLogger("tracerag.agent")

AGENT_TIMEOUT_SECONDS: int = 30

SYSTEM_PROMPT = """You are TraceRAG, an assistant for operational documentation.

You must use document tools before answering a procedural question.
Use only facts present in retrieved documents. Never invent procedures,
document identifiers, quotes, or sources.

Every actionable factual statement must be traceable to one or more source
references returned by a tool. Keep answers concise.

If the tools do not provide enough evidence, return:
- status = insufficient_evidence
- a brief explanation in answer
- no invented steps
- a limitation explaining which approved procedure is missing

If the question is too ambiguous to search safely, return:
- status = clarification_required
- one concise question in answer
- no procedural steps

For answered responses, include 1-3 real sources. Quotes must be short,
verbatim excerpts from tool results. Do not cite a source that was not
returned by a tool.
"""

CORRECTION_PROMPT = (
    "Your previous response could not be validated as a structured answer. "
    "Return a single valid result: choose status from answered, "
    "insufficient_evidence, or clarification_required. If you cannot ground an "
    "answer in retrieved documents, return status = insufficient_evidence with "
    "a brief explanation and no invented steps or sources."
)

# Errors that justify one retry with a correction instruction.
_RETRYABLE_ERRORS: tuple[type[BaseException], ...] = (
    ValidationError,
    AgentRunError,
    ModelHTTPError,
)


def _build_model(settings: Settings) -> OpenAIChatModel:
    provider = OpenAIProvider(base_url=settings.base_url, api_key=settings.api_key)
    return OpenAIChatModel(settings.model_name, provider=provider)


def _build_agent(settings: Settings) -> Agent[object, AssistantAnswer]:
    """Construct the PydanticAI agent wired to the in-memory MCP toolset."""
    client = Client(create_mcp_server())
    toolset = MCPToolset(client)
    return Agent[object, AssistantAnswer](
        _build_model(settings),
        output_type=AssistantAnswer,
        instructions=SYSTEM_PROMPT,
        toolsets=[toolset],
    )


@lru_cache(maxsize=1)
def get_agent() -> Agent[object, AssistantAnswer]:
    """Return a process-wide cached agent instance."""
    return _build_agent(get_settings())


def _insufficient_evidence(message: str) -> AssistantAnswer:
    """Build a fail-closed answer that never exposes internals to clients."""
    return AssistantAnswer(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        answer=message,
        steps=[],
        sources=[],
        limitations=["A validated answer could not be produced from the available evidence."],
    )


async def _run_once(
    agent: Agent[object, AssistantAnswer],
    question: str,
    instructions: str | None,
) -> AssistantAnswer:
    """Run the agent once under a 30-second timeout and return validated output."""
    async with asyncio.timeout(AGENT_TIMEOUT_SECONDS):
        result = await agent.run(question, instructions=instructions)
    return result.output


async def run_agent(question: str) -> AssistantAnswer:
    """Answer a procedural question, failing closed to insufficient evidence.

    The agent calls the MCP retrieval tools itself; callers must not pre-feed
    retrieved content as fact. Returns a always-valid :class:`AssistantAnswer`.
    """
    agent = get_agent()
    try:
        return await _run_once(agent, question, instructions=None)
    except TimeoutError:
        logger.warning("agent timed out after %ss", AGENT_TIMEOUT_SECONDS)
        return _insufficient_evidence("The assistant did not respond within the time limit.")
    except _RETRYABLE_ERRORS:
        logger.warning("agent output validation failed; retrying with correction")
        try:
            return await _run_once(agent, question, instructions=CORRECTION_PROMPT)
        except Exception:
            logger.exception("agent retry failed")
            return _insufficient_evidence("A validated answer could not be produced.")
    except Exception:
        logger.exception("agent run failed unexpectedly")
        return _insufficient_evidence("The assistant could not produce a validated answer.")