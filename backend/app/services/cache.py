"""Shared in-memory caches."""
import time
from typing import Any

ais_vessels: dict[int, dict[str, Any]] = {}

spill_cache: dict[str, Any] = {
    "data": [],
    "regions": {},
    "last_refresh": 0.0,
    "refreshing": False,
}


def ais_cache_stats() -> dict:
    return {"vessel_count": len(ais_vessels), "ts": time.time()}