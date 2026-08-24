from ...config.llm import classification_llm_settings
from ...schema.classification import ClassificationResponse
from ..core.guard import call_llm, guarded_llm_node
from ..core.log import _log
from ..core.logger import get_logger
from ..prompts.classify_prompt import build_classify_prompt
from ..state import TicketState

logger = get_logger("nodes.classify")


@guarded_llm_node("classify")  # failure here has no category to route on -> hard escalate
async def classify(state: TicketState) -> dict:
    logger.info("node_start", node="classify", ticket_id=state["ticket_id"])
    system_prompt, user_content = build_classify_prompt(state["subject"], state["body"])
    result = await call_llm(
        system_prompt,
        user_content,
        ClassificationResponse,
        model=classification_llm_settings.classification_llm_model,
        max_tokens=classification_llm_settings.classification_max_tokens,
        temperature=classification_llm_settings.classification_temperature,
        settings=classification_llm_settings,
    )

    logger.info(
        "node_complete",
        node="classify",
        ticket_id=state["ticket_id"],
        category=result.category,
        confidence=result.confidence,
    )
    return {
        "category": result.category,
        "classification_confidence": result.confidence,
        "trail": await _log(state, "classify", category=result.category, confidence=result.confidence),
    }
