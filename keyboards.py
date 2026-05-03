from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


WEATHER_NOW_BUTTON = "🌤 Погода сейчас"
TODAY_BUTTON = "📅 Прогноз на сегодня"
HELP_BUTTON = "ℹ️ Помощь"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=WEATHER_NOW_BUTTON),
                KeyboardButton(text=TODAY_BUTTON),
            ],
            [
                KeyboardButton(text=HELP_BUTTON),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напишите город",
    )
