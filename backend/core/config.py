from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    _BACKEND_DB_PATH = _PROJECT_ROOT / "backend" / "cooperative.db"

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = f"sqlite:///{_BACKEND_DB_PATH.as_posix()}"
    anthropic_api_key: str = ""
    telegram_bot_token: str = ""


settings = Settings()
