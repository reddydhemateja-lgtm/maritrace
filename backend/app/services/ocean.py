"""Open-Meteo Marine + Forecast APIs."""
import math
import httpx


async def get_currents(lat: float, lon: float) -> tuple[float, float]:
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "ocean_current_velocity,ocean_current_direction",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            cur = r.json().get("current", {}) or {}
    except Exception:
        return 0.0, 0.0

    speed = cur.get("ocean_current_velocity") or 0.0
    direction = cur.get("ocean_current_direction") or 0.0
    rad = math.radians(direction)
    return -speed * math.sin(rad), -speed * math.cos(rad)


async def get_wind(lat: float, lon: float) -> tuple[float, float]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "wind_speed_10m,wind_direction_10m",
        "wind_speed_unit": "ms",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            cur = r.json().get("current", {}) or {}
    except Exception:
        return 0.0, 0.0

    speed = cur.get("wind_speed_10m") or 0.0
    direction = cur.get("wind_direction_10m") or 0.0
    rad = math.radians(direction)
    return -speed * math.sin(rad), -speed * math.cos(rad)