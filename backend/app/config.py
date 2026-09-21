from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def strip_string_whitespace(cls, value):
        # Deployment dashboards (Render, Vercel, ...) are a common source of
        # env vars with an accidental trailing newline/space from copy-paste,
        # which corrupts connection strings and API keys silently.
        if isinstance(value, str):
            return value.strip()
        return value

    database_url: str = "sqlite:///./supply_chain.db"

    llm_provider: str = "mock"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    low_inventory_threshold_days: float = 10
    lead_time_increase_threshold: float = 0.3  # flag a supplier whose lead time has grown 30%+ past its on-file baseline

    email_mode: str = "log"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_recipient: str = "supply.manager@example.com"

    weather_api_base: str = "https://api.open-meteo.com/v1/forecast"

    monitor_interval_seconds: int = 60


settings = Settings()
