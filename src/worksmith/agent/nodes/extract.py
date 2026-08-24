from ...config.llm import extraction_llm_settings
from ...schema.extraction import ExtractionResponse
from ..guard import call_llm, guarded_llm_node
from ..log import _log
from ..prompts.extract_prompt import build_extract_prompt
from ..state import TicketState
from ..utils import extract_on_error


@guarded_llm_node("extract", on_error_updates=extract_on_error)
async def extract(state: TicketState) -> dict:
    prompt = build_extract_prompt(state["category"], state["subject"], state["body"])
    result = await call_llm(
        prompt,
        ExtractionResponse,
        model=extraction_llm_settings.extraction_llm_model,
        max_tokens=extraction_llm_settings.extraction_max_tokens,
        temperature=extraction_llm_settings.extraction_temperature,
        settings=extraction_llm_settings,
    )

    return {
        "extracted_fields": result.extracted_fields.model_dump(),
        "extraction_confidence": result.confidence,
        "extraction_failed": False,
        "trail": _log(state, "extract", confidence=result.confidence),
    }
