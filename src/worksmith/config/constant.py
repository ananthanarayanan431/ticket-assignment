"""Constants for the Agent."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConstants(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hard_constraint_categories: frozenset[str] = frozenset({"billing", "account_deletion", "legal", "security"})
    no_extraction_needed_categories: frozenset[str] = frozenset({"spam"})
    auto_resolve_confidence_threshold: float = 0.85
    draft_confidence_threshold: float = 0.55


agent_constants = AgentConstants()
