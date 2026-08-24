from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenRouterSettings(BaseSettings):
    """Shared OpenRouter connection settings, reused by every task-specific LLM config."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str | None = None
    openrouter_api_url: str = "https://openrouter.ai/api/v1"


class ClassificationLLMSettings(OpenRouterSettings):
    classification_llm_model: str = "openai/gpt-4o-mini"
    classification_temperature: float = 0
    classification_max_tokens: int = 1024


class ExtractionLLMSettings(OpenRouterSettings):
    extraction_llm_model: str = "openai/gpt-4o-mini"
    extraction_temperature: float = 0
    extraction_max_tokens: int = 1024


class DraftForReviewLLMSettings(OpenRouterSettings):
    draft_for_review_llm_model: str = "openai/gpt-4o-mini"
    draft_for_review_temperature: float = 0
    draft_for_review_max_tokens: int = 1024


class EvalJudgeLLMSettings(OpenRouterSettings):
    eval_judge_llm_model: str = "openai/gpt-4.1-mini"
    eval_judge_temperature: float = 0
    eval_judge_max_tokens: int = 1024


classification_llm_settings = ClassificationLLMSettings()
extraction_llm_settings = ExtractionLLMSettings()
draft_for_review_llm_settings = DraftForReviewLLMSettings()
eval_judge_llm_settings = EvalJudgeLLMSettings()
