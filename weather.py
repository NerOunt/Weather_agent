from datetime import datetime, timezone
from typing import Any

import aiohttp


CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherError(Exception):
    """Base OpenWeather client error."""


class CityNotFoundError(WeatherError):
    """Requested city was not found by OpenWeather."""


class OpenWeatherClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def get_current_weather(self, city: str) -> dict[str, Any]:
        data = await self._request(CURRENT_WEATHER_URL, city)
        weather = (data.get("weather") or [{}])[0]
        main = data.get("main") or {}
        wind = data.get("wind") or {}

        return {
            "city": city,
            "temp": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "description": weather.get("description"),
            "wind_speed": wind.get("speed"),
            "humidity": main.get("humidity"),
            "pressure_hpa": main.get("pressure"),
        }

    async def get_today_forecast(self, city: str) -> dict[str, Any]:
        data = await self._request(FORECAST_URL, city)
        city_data = data.get("city") or {}
        timezone_offset = int(city_data.get("timezone") or 0)
        forecasts = data.get("list") or []

        today = self._local_date(datetime.now(timezone.utc).timestamp(), timezone_offset)
        today_items = [
            item
            for item in forecasts
            if self._local_date(item.get("dt"), timezone_offset) == today
        ]

        if not today_items:
            today_items = forecasts[:4]

        temperatures = [
            float(item["main"]["temp"])
            for item in today_items
            if item.get("main", {}).get("temp") is not None
        ]
        wind_speeds = [
            float(item["wind"]["speed"])
            for item in today_items
            if item.get("wind", {}).get("speed") is not None
        ]
        descriptions = [
            (item.get("weather") or [{}])[0].get("description")
            for item in today_items
            if (item.get("weather") or [{}])[0].get("description")
        ]

        precipitation_possible = any(
            item.get("rain")
            or item.get("snow")
            or float(item.get("pop") or 0) >= 0.2
            for item in today_items
        )

        avg_temp = sum(temperatures) / len(temperatures) if temperatures else None

        return {
            "city": city,
            "min_temp": min(temperatures) if temperatures else None,
            "max_temp": max(temperatures) if temperatures else None,
            "avg_temp": avg_temp,
            "descriptions": descriptions,
            "max_wind_speed": max(wind_speeds) if wind_speeds else None,
            "precipitation_possible": precipitation_possible,
        }

    async def _request(self, url: str, city: str) -> dict[str, Any]:
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 404:
                        raise CityNotFoundError
                    if response.status >= 400:
                        raise WeatherError
                    return await response.json()
        except CityNotFoundError:
            raise
        except (aiohttp.ClientError, TimeoutError):
            raise WeatherError

    @staticmethod
    def _local_date(timestamp: float | int | None, timezone_offset: int) -> str | None:
        if timestamp is None:
            return None
        local_timestamp = int(timestamp) + timezone_offset
        return datetime.fromtimestamp(local_timestamp, tz=timezone.utc).date().isoformat()
