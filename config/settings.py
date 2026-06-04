from pydantic_settings import BaseSettings
from typing import Literal, Optional


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_CREDENTIALS_FILE: str = "google-credentials.json"
    TIMEZONE: str = "America/Argentina/Buenos_Aires"
    BOT_NAME: str = "Carlos"
    BOT_STYLE: Literal["professional", "friendly", "emoji", "formal"] = "friendly"
    APPOINTMENT_DURATION_HOURS: int = 1
    ADMIN_TELEGRAM_ID: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

_runtime_style: Optional[str] = None


def get_current_style() -> str:
    return _runtime_style or settings.BOT_STYLE


def set_current_style(style: str) -> bool:
    from config.styles import STYLES
    global _runtime_style
    if style in STYLES:
        _runtime_style = style
        return True
    return False
