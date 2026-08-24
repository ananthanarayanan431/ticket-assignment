from typing import TypeVar

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, ValidationError

from ...config.llm import OpenRouterSettings
from .exceptions import LLMCallError
from .log import _log
from ..state import TicketState

client: AsyncOpenAI | None = None

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


def get_client(settings: OpenRouterSettings) -> AsyncOpenAI:
    global client
    if client is None:
        if not settings.openrouter_api_key:
            raise LLMCallError("OPENROUTER_API_KEY is not set in the environment.")
        client = AsyncOpenAI(base_url=settings.openrouter_api_url, api_key=settings.openrouter_api_key)
    return client


async def call_llm(
    prompt: str,
    response_model: type[ResponseModelT],
    *,
    model: str,
    max_tokens: int,
    temperature: float,
    settings: OpenRouterSettings,
) -> ResponseModelT:

    llm_client = get_client(settings)

    try:
        completion = await llm_client.chat.completions.parse(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_model,
        )
    except APITimeoutError as e:
        raise TimeoutError(str(e)) from e
    except (APIConnectionError, APIStatusError) as e:
        raise LLMCallError(str(e)) from e

    message = completion.choices[0].message
    if message.refusal:
        raise LLMCallError(f"LLM refused to respond: {message.refusal}")
    if message.parsed is None:
        raise LLMCallError("LLM response did not match the expected schema.")
    return message.parsed


def guarded_llm_node(node_name: str, *, on_error_updates=None):
    """
    Decorator for any async node function that calls an LLM. On timeout,
    exception, or unparseable output, degrades safely instead of crashing the
    graph or silently dropping the ticket.

    By default this means forcing hard_constraint_flag so the ticket is
    routed to escalate through route_decision. Pass `on_error_updates(state,
    error) -> dict` to override that default with node-specific degrade
    logic (e.g. keep the ticket moving with partial data instead of always
    forcing an escalate).
    """

    def decorator(fn):
        async def wrapped(state: TicketState) -> dict:
            try:
                return await fn(state)
            except (LLMCallError, TimeoutError, ValidationError, NotImplementedError) as e:
                updates = (
                    on_error_updates(state, e)
                    if on_error_updates is not None
                    else {"hard_constraint_flag": True, "failure_reason": f"{node_name} failed: {e}"}
                )
                return {**updates, "trail": _log(state, node_name, error=str(e))}

        wrapped.__name__ = fn.__name__
        return wrapped

    return decorator