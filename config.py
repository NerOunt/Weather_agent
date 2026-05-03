import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    weather_api_key: str
    default_city: str
    default_timezone: str
    webhook_url: str


def load_settings() -> Settings:
    load_dotenv()

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    weather_api_key = os.getenv("WEATHER_API_KEY")
    webhook_url = os.getenv("WEBHOOK_URL")

    missing = []
    if not telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not weather_api_key:
        missing.append("WEATHER_API_KEY")
    if not webhook_url:
        missing.append("WEBHOOK_URL")

    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Не заданы обязательные переменные окружения: {names}. "
            "Заполните Environment Variables на Render или локальный .env."
        )

    return Settings(
        telegram_bot_token=telegram_bot_token,
        weather_api_key=weather_api_key,
        default_city=os.getenv("DEFAULT_CITY", "Москва"),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow"),
        webhook_url=webhook_url.rstrip("/"),
    )
