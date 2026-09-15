"""Cerulean (SkyTruth) oil spill detection client."""
import logging
from datetime import datetime, timedelta, timezone

import httpx

log = logging.getLogger("cerulean")

BASE = "https://api.cerulean.skytruth.org/collections/public.slick_plus/items"


async def fetch_slicks(
    bbox: str = "70.5,18.5,73.5,21.5",
    hours_back: int = 72,
    min_score: float = 0.0,
    limit: int = 300,
) -> list[dict]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours_back)
    params = {
        "limit": limit,
        "bbox": bbox,
        "datetime": f"{start:%Y-%m-%dT%H:%M:%SZ}/{end:%Y-%m-%dT%H:%M:%SZ}",
        "filter": f"max_source_collated_score GTE {min_score}",
        "sortby": "-slick_timestamp",
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.get(BASE, params=params)
            r.raise_for_status()
            return r.json().get("features", [])
    except Exception as e:
        log.warning("Cerulean fetch failed: %s", e)
        return []


def feature_to_dict(f: dict) -> dict:
    p = f.get("properties", {}) or {}
    return {
        "id": p.get("id"),
        "timestamp": p.get("slick_timestamp"),
        "geometry": f.get("geometry"),
        "area_m2": p.get("area"),
        "length_m": p.get("length"),
        "perimeter_m": p.get("perimeter"),
        "linearity": p.get("linearity"),
        "fill_factor": p.get("fill_factor"),
        "polsby_popper": p.get("polsby_popper"),
        "slick_confidence": p.get("slick_confidence"),
        "max_source_collated_score": p.get("max_source_collated_score"),
        "hitl_cls_name": p.get("hitl_cls_name"),
        "s1_scene_id": p.get("s1_scene_id"),
        "slick_url": p.get("slick_url"),
    }