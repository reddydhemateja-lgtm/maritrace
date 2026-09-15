"""Fast Lagrangian drift hindcast using Open-Meteo currents + winds.

Optimized: caches lookups by rounding lat/lon to 0.5° grid so we make
~10-20 HTTP calls per run instead of thousands.
"""
import math
from datetime import timedelta

import numpy as np
from shapely.geometry import Polygon
from scipy.spatial import ConvexHull

from app.services.ocean import get_currents, get_wind


def _rotate(u: float, v: float, deg: float) -> tuple[float, float]:
    t = math.radians(deg)
    return u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)


def _grid_key(lat: float, lon: float) -> tuple[float, float]:
    """Round lat/lon to 0.5° grid to enable caching."""
    return (round(lat * 2) / 2, round(lon * 2) / 2)


async def _cached_currents(lat: float, lon: float, cache: dict):
    key = _grid_key(lat, lon)
    if key in cache:
        return cache[key]
    u, v = await get_currents(lat, lon)
    cache[key] = (u, v)
    return u, v


async def _cached_wind(lat: float, lon: float, cache: dict):
    key = _grid_key(lat, lon)
    if key in cache:
        return cache[key]
    u, v = await get_wind(lat, lon)
    cache[key] = (u, v)
    return u, v


async def hindcast(
    slick_geom,
    slick_time,
    hours_back: int = 72,
    ensemble: int = 8,
    dt_hours: float = 2.0,
) -> dict:
    """
    Fast backward-time Lagrangian ensemble.

    Tuned for real-time use:
      - 8 ensembles instead of 15
      - 2-hour step instead of 0.5-hour (fewer lookups)
      - Grid caching reduces Open-Meteo calls from ~4000 to ~20
    """
    cx, cy = slick_geom.centroid.x, slick_geom.centroid.y
    n_steps = max(1, int(hours_back / dt_hours))

    # Shared caches across all ensembles and steps
    currents_cache: dict = {}
    winds_cache: dict = {}

    paths = []
    for e in range(ensemble):
        # Wider ensemble spread so the cone has meaningful area
        alpha = 0.03 + (e / max(1, ensemble - 1)) * 0.02   # 0.03..0.05
        ek = -25 + (e / max(1, ensemble - 1)) * 50          # -25..25

        lon, lat = cx, cy
        t = slick_time
        path = [(lon, lat)]

        for _ in range(n_steps):
            t = t - timedelta(hours=dt_hours)

            uc, vc = await _cached_currents(lat, lon, currents_cache)
            uw, vw = await _cached_wind(lat, lon, winds_cache)
            uw_r, vw_r = _rotate(uw, vw, ek)

            u = uc + alpha * uw_r
            v = vc + alpha * vw_r

            # Backward integration: move in the negative direction
            lat -= v * dt_hours * 3600.0 / 111_320.0
            cos_lat = math.cos(math.radians(lat)) or 1e-6
            lon -= u * dt_hours * 3600.0 / (111_320.0 * cos_lat)

            # Clamp to sane bounds
            lat = max(-89.0, min(89.0, lat))
            lon = ((lon + 180) % 360) - 180

            path.append((lon, lat))

        paths.append(path)

    endpoints = np.array([p[-1] for p in paths])
    origin = endpoints.mean(axis=0)
    origin_time = slick_time - timedelta(hours=hours_back)

    cone = Polygon()
    if len(endpoints) >= 3:
        try:
            hull = ConvexHull(endpoints)
            coords = [tuple(endpoints[i]) for i in hull.vertices]
            coords.append(coords[0])
            cone = Polygon(coords)
        except Exception:
            pass

    return {
        "origin_center": (float(origin[0]), float(origin[1])),
        "origin_time": origin_time,
        "cone_geom": cone,
        "ensembles": paths,
    }