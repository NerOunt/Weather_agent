from collections import Counter
from typing import Any


CITY_PREPOSITIONAL_EXCEPTIONS = {
    "москва": "Москве",
    "санкт-петербург": "Санкт-Петербурге",
    "казань": "Казани",
    "екатеринбург": "Екатеринбурге",
    "новосибирск": "Новосибирске",
    "сочи": "Сочи",
    "краснодар": "Краснодаре",
    "ростов-на-дону": "Ростове-на-Дону",
    "нижний новгород": "Нижнем Новгороде",
    "воронеж": "Воронеже",
    "самара": "Самаре",
    "уфа": "Уфе",
    "пермь": "Перми",
    "омск": "Омске",
    "челябинск": "Челябинске",
    "красноярск": "Красноярске",
    "волгоград": "Волгограде",
}

RUSSIAN_CONSONANTS = set("бвгджзйклмнпрстфхцчшщ")


def decline_city_for_weather_text(city: str) -> str:
    city = (city or "").strip()
    if not city:
        return ""

    normalized = " ".join(city.split()).lower()
    if normalized in CITY_PREPOSITIONAL_EXCEPTIONS:
        return CITY_PREPOSITIONAL_EXCEPTIONS[normalized]

    last = city[-1].lower()
    if last == "а":
        return f"{city[:-1]}е"
    if last == "я":
        return f"{city[:-1]}е"
    if last == "ь":
        return f"{city[:-1]}и"
    if last in RUSSIAN_CONSONANTS:
        return f"{city}е"

    return ""


def city_weather_title(prefix: str, city: str) -> str:
    declined_city = decline_city_for_weather_text(city)
    if declined_city:
        return f"{prefix} в {declined_city}:"
    return f"{prefix}. Город: {city}"


def format_temperature(value: float | int | None) -> str:
    if value is None:
        return "нет данных"

    rounded = round(float(value))
    sign = "+" if rounded > 0 else ""
    return f"{sign}{rounded}°C"


def format_wind(value: float | int | None) -> str:
    if value is None:
        return "нет данных"

    wind = float(value)
    rounded = round(wind, 1)
    if rounded.is_integer():
        return f"{int(rounded)} м/с"
    return f"{rounded} м/с"


def pressure_hpa_to_mmhg(hpa: float | int | None) -> int | None:
    if hpa is None:
        return None
    return round(float(hpa) * 0.75006)


def get_clothing_advice(temp: float | int | None) -> str:
    if temp is None:
        return "ориентируйтесь по погоде за окном."

    value = float(temp)
    if value < -10:
        return "очень тепло оденьтесь."
    if value < 0:
        return "наденьте зимнюю куртку."
    if value < 10:
        return "наденьте куртку, на улице прохладно."
    if value < 18:
        return "легкая куртка или худи будут к месту."
    if value <= 25:
        return "подойдет комфортная одежда."
    return "выбирайте легкую одежду и возьмите воду с собой."


def extract_city_from_command(text: str | None, default_city: str) -> str:
    if not text:
        return default_city

    parts = text.strip().split(maxsplit=1)
    if len(parts) == 1:
        return default_city

    city = parts[1].strip()
    return city or default_city


def format_weather_message(data: dict[str, Any]) -> str:
    pressure = pressure_hpa_to_mmhg(data.get("pressure_hpa"))
    pressure_text = f"{pressure} мм рт. ст." if pressure is not None else "нет данных"
    humidity = data.get("humidity")
    humidity_text = f"{humidity}%" if humidity is not None else "нет данных"

    return (
        f"{city_weather_title('Погода', data.get('city', 'город'))}\n\n"
        f"🌡 Температура: {format_temperature(data.get('temp'))}\n"
        f"🤔 Ощущается как: {format_temperature(data.get('feels_like'))}\n"
        f"☁️ Состояние: {data.get('description') or 'нет данных'}\n"
        f"💨 Ветер: {format_wind(data.get('wind_speed'))}\n"
        f"💧 Влажность: {humidity_text}\n"
        f"🧭 Давление: {pressure_text}\n\n"
        f"Совет: {get_clothing_advice(data.get('temp'))}"
    )


def format_today_forecast(data: dict[str, Any]) -> str:
    descriptions = data.get("descriptions") or []
    description = "нет данных"
    if descriptions:
        description = Counter(descriptions).most_common(1)[0][0]

    precipitation = "возможны" if data.get("precipitation_possible") else "не ожидаются"
    advice_temp = data.get("avg_temp")

    return (
        f"{city_weather_title('Прогноз на сегодня', data.get('city', 'город'))}\n\n"
        f"🌡 Температура: от {format_temperature(data.get('min_temp'))} "
        f"до {format_temperature(data.get('max_temp'))}\n"
        f"☁️ Состояние: {description}\n"
        f"💨 Ветер: до {format_wind(data.get('max_wind_speed'))}\n"
        f"🌧 Осадки: {precipitation}\n\n"
        f"Совет: {get_clothing_advice(advice_temp)}"
    )
