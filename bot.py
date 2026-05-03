import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonCommands, Message, Update
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from config import load_settings
from keyboards import (
    HELP_BUTTON,
    TODAY_BUTTON,
    WEATHER_NOW_BUTTON,
    main_menu_keyboard,
)
from utils import (
    extract_city_from_command,
    format_today_forecast,
    format_weather_message,
)
from weather import CityNotFoundError, OpenWeatherClient, WeatherError


START_TEXT = """Привет! Я Погодный бот ☀️

Я показываю погоду по запросу для любого города.

Команды:
/weather <город> — погода сейчас
/today <город> — прогноз на сегодня
/help — помощь

Примеры:
/weather Москва
/weather Санкт-Петербург
/today Казань"""

HELP_TEXT = """Команды:
/weather <город> — погода сейчас в указанном городе
/today <город> — прогноз на сегодня в указанном городе

Кнопки:
🌤 Погода сейчас — запросить город и показать погоду
📅 Прогноз на сегодня — запросить город и показать прогноз
ℹ️ Помощь — показать справку

Если город не указан, используется город по умолчанию."""

CITY_NOT_FOUND_TEXT = (
    "Не удалось найти город. Попробуйте написать иначе, например: /weather Москва"
)
WEATHER_UNAVAILABLE_TEXT = "Не удалось получить погоду. Попробуйте позже."
WEATHER_CITY_PROMPT = "Введите город, для которого нужно показать погоду сейчас."
TODAY_CITY_PROMPT = "Введите город, для которого нужно показать прогноз на сегодня."
BOT_COMMANDS = [
    BotCommand(command="start", description="Запуск бота"),
    BotCommand(command="help", description="Список команд"),
    BotCommand(command="weather", description="Погода сейчас"),
    BotCommand(command="today", description="Прогноз на сегодня"),
]


class CityInput(StatesGroup):
    waiting_for_weather_city = State()
    waiting_for_today_city = State()


logging.basicConfig(level=logging.INFO)

settings = load_settings()
weather_client = OpenWeatherClient(settings.weather_api_key)
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()


async def send_current_weather(message: Message, city: str) -> None:
    try:
        weather = await weather_client.get_current_weather(city)
    except CityNotFoundError:
        await message.answer(CITY_NOT_FOUND_TEXT, reply_markup=main_menu_keyboard())
        return
    except WeatherError:
        await message.answer(WEATHER_UNAVAILABLE_TEXT, reply_markup=main_menu_keyboard())
        return

    await message.answer(format_weather_message(weather), reply_markup=main_menu_keyboard())


async def send_today_forecast(message: Message, city: str) -> None:
    try:
        forecast = await weather_client.get_today_forecast(city)
    except CityNotFoundError:
        await message.answer(CITY_NOT_FOUND_TEXT, reply_markup=main_menu_keyboard())
        return
    except WeatherError:
        await message.answer(WEATHER_UNAVAILABLE_TEXT, reply_markup=main_menu_keyboard())
        return

    await message.answer(format_today_forecast(forecast), reply_markup=main_menu_keyboard())


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(START_TEXT, reply_markup=main_menu_keyboard())


@dp.message(Command("help"))
async def help_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@dp.message(Command("weather"))
async def weather_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    city = extract_city_from_command(message.text, settings.default_city)
    await send_current_weather(message, city)


@dp.message(Command("today"))
async def today_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    city = extract_city_from_command(message.text, settings.default_city)
    await send_today_forecast(message, city)


@dp.message(F.text == WEATHER_NOW_BUTTON)
async def weather_button_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(CityInput.waiting_for_weather_city)
    await message.answer(WEATHER_CITY_PROMPT, reply_markup=main_menu_keyboard())


@dp.message(F.text == TODAY_BUTTON)
async def today_button_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(CityInput.waiting_for_today_city)
    await message.answer(TODAY_CITY_PROMPT, reply_markup=main_menu_keyboard())


@dp.message(F.text == HELP_BUTTON)
async def help_button_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@dp.message(CityInput.waiting_for_weather_city)
async def weather_city_input_handler(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if not city:
        await message.answer(WEATHER_CITY_PROMPT, reply_markup=main_menu_keyboard())
        return

    await state.clear()
    await send_current_weather(message, city)


@dp.message(CityInput.waiting_for_today_city)
async def today_city_input_handler(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if not city:
        await message.answer(TODAY_CITY_PROMPT, reply_markup=main_menu_keyboard())
        return

    await state.clear()
    await send_today_forecast(message, city)


@dp.message(F.text)
async def plain_city_text_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return

    await state.clear()
    await send_current_weather(message, text)


@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "OK"


@app.get("/health/", response_class=PlainTextResponse)
async def health_with_slash() -> str:
    return "OK"


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "OK"


@app.head("/")
async def root_head() -> PlainTextResponse:
    return PlainTextResponse("")


@app.get("/webhook", response_class=PlainTextResponse)
async def webhook_check() -> str:
    return "OK"


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


def build_webhook_url(base_url: str) -> str:
    base_url = base_url.strip().rstrip("/")
    if base_url.endswith("/webhook"):
        return base_url
    return f"{base_url}/webhook"


@app.on_event("startup")
async def on_startup() -> None:
    webhook_url = build_webhook_url(settings.webhook_url)
    await bot.set_webhook(webhook_url, drop_pending_updates=False)
    await bot.set_my_commands(BOT_COMMANDS)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    logging.info("Telegram webhook is set: %s", webhook_url)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await bot.session.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "bot:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
