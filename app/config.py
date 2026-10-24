
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("CELESTO_PROVIDER", "cloud").strip().lower()
    celesto_api_key: str = os.getenv("CELESTO_API_KEY", "replace-me")
    llm_api_key: str = os.getenv("LLM_API_KEY", "replace-me")
    llm_model: str = os.getenv("LLM_MODEL", "replace-with-a-model-name")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://example-llm-host/v1")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://ledger:ledger@localhost:5432/ledger")
    api_port: int = int(os.getenv("API_PORT", "8080"))

settings = Settings()
