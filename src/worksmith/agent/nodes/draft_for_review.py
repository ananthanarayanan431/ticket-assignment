from ...config.llm import draft_for_review_llm_settings
from ...schema.draft import DraftResponse
from ..guard import call_llm, guarded_llm_node
from ..log import _log
from ..prompts.draft_for_review_prompt import build_draft_for_review_prompt
from ..state import TicketState


@guarded_llm_node("draft_for_review")
async def draft_for_review(state: TicketState) -> dict:
    prompt = build_draft_for_review_prompt(state["category"], state.get("extracted_fields", {}), state["body"])
    result = await call_llm(
        prompt,
        DraftResponse,
        model=draft_for_review_llm_settings.draft_for_review_llm_model,
        max_tokens=draft_for_review_llm_settings.draft_for_review_max_tokens,
        temperature=draft_for_review_llm_settings.draft_for_review_temperature,
        settings=draft_for_review_llm_settings,
    )

    return {
        "response_text": result.draft,
        "queued_for_human": True,
        "trail": _log(state, "draft_for_review", queued=True),
    }
