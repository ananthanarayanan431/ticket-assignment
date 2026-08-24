from ...config.llm import auto_resolve_llm_settings
from ...schema.auto_resolve import AutoResolveResponse
from ..core.guard import call_llm, guarded_llm_node
from ..core.log import _log
from ..core.logger import get_logger
from ..core.utils import auto_resolve_on_error
from ..prompts.auto_resolve_prompt import build_auto_resolve_prompt
from ..state import TicketState

logger = get_logger("nodes.auto_resolve")


@guarded_llm_node("auto_resolve", on_error_updates=auto_resolve_on_error)
async def auto_resolve(state: TicketState) -> dict:
    logger.info("node_start", node="auto_resolve", ticket_id=state["ticket_id"], category=state.get("category"))
    system_prompt, user_content = build_auto_resolve_prompt(
        state["category"],
        state.get("extracted_fields", {}),
        state["body"],
        state["from_name"],
        state["from_email"],
    )
    result = await call_llm(
        system_prompt,
        user_content,
        AutoResolveResponse,
        model=auto_resolve_llm_settings.auto_resolve_llm_model,
        max_tokens=auto_resolve_llm_settings.auto_resolve_max_tokens,
        temperature=auto_resolve_llm_settings.auto_resolve_temperature,
        settings=auto_resolve_llm_settings,
    )

    logger.info("node_complete", node="auto_resolve", ticket_id=state["ticket_id"], sent=True)
    return {
        "response_text": result.response,
        "queued_for_human": False,
        "trail": await _log(state, "auto_resolve", sent=True, response_text=result.response),
    }
