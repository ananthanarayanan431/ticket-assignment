from ...config.llm import draft_for_review_llm_settings
from ...schema.draft import DraftResponse
from ..core.guard import call_llm, guarded_llm_node
from ..core.log import _log
from ..core.logger import get_logger
from ..prompts.draft_for_review_prompt import build_draft_for_review_prompt
from ..state import TicketState

logger = get_logger("nodes.draft_for_review")


@guarded_llm_node("draft_for_review")
async def draft_for_review(state: TicketState) -> dict:
    logger.info("node_start", node="draft_for_review", ticket_id=state["ticket_id"], category=state.get("category"))
    system_prompt, user_content = build_draft_for_review_prompt(
        state["category"],
        state.get("extracted_fields", {}),
        state["body"],
        state["from_name"],
        state["from_email"],
    )
    result = await call_llm(
        system_prompt,
        user_content,
        DraftResponse,
        model=draft_for_review_llm_settings.draft_for_review_llm_model,
        max_tokens=draft_for_review_llm_settings.draft_for_review_max_tokens,
        temperature=draft_for_review_llm_settings.draft_for_review_temperature,
        settings=draft_for_review_llm_settings,
    )

    logger.info("node_complete", node="draft_for_review", ticket_id=state["ticket_id"], queued=True)
    return {
        "response_text": result.draft,
        "queued_for_human": True,
        "trail": await _log(state, "draft_for_review", queued=True, response_text=result.draft),
    }
