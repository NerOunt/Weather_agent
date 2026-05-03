from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


WEATHER_NOW_BUTTON = "🌤 Погода сейчас"
TODAY_BUTTON = "📅 Прогноз на сегодня"
POPULAR_CITIES_BUTTON = "🏙 Популярные города"
HELP_BUTTON = "ℹ️ Помощь"

POPULAR_CITIES = (
    "Москва",
    "Санкт-Петербург",
    "Казань",
    "Екатеринбург",
    "Новосибирск",
    "Сочи",
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=WEATHER_NOW_BUTTON),
                KeyboardButton(text=TODAY_BUTTON),
            ],
            [
                KeyboardButton(text=POPULAR_CITIES_BUTTON),
                KeyboardButton(text=HELP_BUTTON),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напишите город",
    )


def popular_cities_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for index in range(0, len(POPULAR_CITIES), 2):
        rows.append(
            [
                InlineKeyboardButton(text=city, callback_data=f"popular_city:{city}")
                for city in POPULAR_CITIES[index : index + 2]
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)
