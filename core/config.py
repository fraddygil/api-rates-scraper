import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def load_env_file(path: str = ".env") -> None:
    """Carga variables desde .env sin sobrescribir variables ya exportadas."""
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file()


@dataclass
class Settings:
    # API donde se guardan las tasas
    api_base_url: str = field(default_factory=lambda: os.environ["API_BASE_URL"])
    api_email: str = field(default_factory=lambda: os.environ["API_EMAIL"])
    api_password: str = field(default_factory=lambda: os.environ["API_PASSWORD"])

    # Telegram
    telegram_bot_token: Optional[str] = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN"))
    telegram_chat_id: Optional[str] = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID"))

    # Comportamiento
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))


settings = Settings()
