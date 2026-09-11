from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Research Agent"
    app_version: str = "0.2.0"

    # Data provider
    financial_provider: str = "mock"
    brapi_base_url: str = "https://brapi.dev/api"
    brapi_token: str | None = None
    provider_timeout_seconds: float = 8.0

    # AI engineering / unit economics
    default_model: str = "deterministic-financial-analyzer-v1"
    input_cost_per_million_tokens_usd: float = 0.0
    output_cost_per_million_tokens_usd: float = 0.0

    # Retrieval
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.05

    model_config = SettingsConfigDict(env_prefix="FRA_", env_file=".env", extra="ignore")


settings = Settings()
