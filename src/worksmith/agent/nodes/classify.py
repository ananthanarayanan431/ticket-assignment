from ...config.llm import classification_llm_settings
from ...schema.classification import ClassificationResponse
from ..core.guard import call_llm, guarded_llm_node
from ..core.log import _log
from ..prompts.classify_prompt import build_classify_prompt
from ..state import TicketState


@guarded_llm_node("classify")  # failure here has no category to route on -> hard escalate
async def classify(state: TicketState) -> dict:
    prompt = build_classify_prompt(state["subject"], state["body"])
    result = await call_llm(
        prompt,
        ClassificationResponse,
        model=classification_llm_settings.classification_llm_model,
        max_tokens=classification_llm_settings.classification_max_tokens,
        temperature=classification_llm_settings.classification_temperature,
        settings=classification_llm_settings,
    )

    return {
        "category": result.category,
        "classification_confidence": result.confidence,
        "trail": _log(state, "classify", category=result.category, confidence=result.confidence),
    }
