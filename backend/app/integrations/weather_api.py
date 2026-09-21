"""Real external integration: Open-Meteo (no API key required).

This is the "at least one integration must demonstrate actual tool calling" requirement -
an honest outbound HTTP call, not a simulated fixture. Used by the Monitoring Agent to flag
severe-weather risk near a supplier's location as an early disruption signal. Network failure
degrades gracefully to "unknown" risk rather than raising, since a monitoring pass must not
crash the whole pipeline over a flaky third-party call.
"""
import httpx

from app.config import settings

SEVERE_WEATHER_CODES = {
    65: "heavy rain",
    75: "heavy snow",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}


def get_weather_risk(latitude: float, longitude: float) -> dict:
    try:
        response = httpx.get(
            settings.weather_api_base,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "weather_code,wind_speed_10m",
                "forecast_days": 1,
            },
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
        code = data.get("current", {}).get("weather_code")
        wind = data.get("current", {}).get("wind_speed_10m")
        severe = code in SEVERE_WEATHER_CODES
        return {
            "source": "open-meteo",
            "queried": True,
            "weather_code": code,
            "wind_speed_10m": wind,
            "severe": severe,
            "description": SEVERE_WEATHER_CODES.get(code, "normal conditions") if code is not None else "unknown",
        }
    except (httpx.HTTPError, httpx.TimeoutException, Exception):
        return {
            "source": "open-meteo",
            "queried": False,
            "weather_code": None,
            "wind_speed_10m": None,
            "severe": False,
            "description": "weather service unavailable - risk unknown, not assumed clear",
        }
