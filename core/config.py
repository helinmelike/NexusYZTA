from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        extra="ignore",
        case_sensitive=False,
    )
    
    database_url: str
    anthropic_api_key: str = ""
    telegram_bot_token: str = ""

settings = Settings()