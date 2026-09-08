from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Research Agent"
    app_version: str = "0.1.0"
    model_config = SettingsConfigDict(env_prefix="FRA_", env_file=".env")


settings = Settings()

