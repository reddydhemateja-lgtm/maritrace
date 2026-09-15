"""Spill endpoints — multi-region, live + historical."""
import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.cerulean import fetch_slicks, feature_to_dict
from app.services.cache import spill_cache
from app.services.regions import REGIONS, list_regions

log = logging.getLogger("slicks")

router = APIRouter(tags=["slicks"])

REFRESH_INTERVAL_SEC = 180

HISTORICAL_FILE = (Path(__file__).resolve().parent.parent.parent
                   / "data" / "historical_indian_spills.json")


def _load_historical() -> list:
    if not HISTORICAL_FILE.exists():
        return []
    try:
        data = json.loads(HISTORICAL_FILE.read_text())
        return data.get("spills", [])
    except Exception as e:
        log.warning("Failed to load historical spills: %s", e)
        return []


async def refresh_loop():
    historical = _load_historical()
    log.info("Loaded %d historical Indian spills from disk", len(historical))

    while True:
        try:
            spill_cache["refreshing"] = True
            live_spills = []
            region_summary = {}

            for slug, cfg in REGIONS.items():
                try:
                    features = await fetch_slicks(
                        bbox=cfg["slick_bbox"],
                        hours_back=72,
                        limit=300,
                    )
                    spills = [feature_to_dict(f) for f in features]
                    for s in spills:
                        s["region"] = slug
                        s["region_label"] = cfg["label"]
                        s["source"] = "live"
                    live_spills.extend(spills)
                    region_summary[slug] = {
                        "label": cfg["label"],
                        "live": len(spills),
                        "historical": 0,
                    }
                    log.info("Region %s: %d live slicks", slug, len(spills))
                except Exception as e:
                    log.warning("Region %s failed: %s", slug, e)
                    region_summary[slug] = {
                        "label": cfg["label"], "live": 0, "historical": 0,
                        "error": str(e),
                    }

            # Count historical per region
            for s in historical:
                s.setdefault("source", "historical")
                slug = s.get("region")
                if slug in region_summary:
                    region_summary[slug]["historical"] += 1
                else:
                    region_summary.setdefault(slug, {
                        "label": s.get("region_label", slug),
                        "live": 0, "historical": 0,
                    })
                    region_summary[slug]["historical"] += 1

            # Merge + dedupe by id
            combined = live_spills + historical
            seen = set()
            deduped = []
            for s in combined:
                sid = s.get("id")
                if sid and sid not in seen:
                    seen.add(sid)
                    deduped.append(s)
                elif not sid:
                    deduped.append(s)

            # Total per region
            for slug in region_summary:
                region_summary[slug]["count"] = (
                    region_summary[slug].get("live", 0)
                    + region_summary[slug].get("historical", 0)
                )

            deduped.sort(key=lambda s: s.get("timestamp") or "", reverse=True)

            spill_cache["data"] = deduped
            spill_cache["regions"] = region_summary
            spill_cache["last_refresh"] = asyncio.get_event_loop().time()
            log.info("Cache refreshed: %d slicks (%d historical + %d live)",
                     len(deduped), len(historical), len(live_spills))

        except Exception as e:
            log.warning("Spill cache refresh failed: %s", e)
        finally:
            spill_cache["refreshing"] = False
        await asyncio.sleep(REFRESH_INTERVAL_SEC)


@router.get("/recent-spills")
async def recent_spills(region: str | None = None):
    data = spill_cache["data"]
    if region:
        data = [s for s in data if s.get("region") == region]

    return {
        "count": len(data),
        "refreshing": spill_cache["refreshing"],
        "last_refresh": spill_cache["last_refresh"],
        "regions": spill_cache.get("regions", {}),
        "spills": data,
    }


@router.get("/regions")
async def get_regions():
    return {"regions": list_regions()}


@router.get("/spills/{slick_id}")
async def get_spill(slick_id: int):
    for s in spill_cache["data"]:
        if s.get("id") == slick_id:
            return s
    raise HTTPException(404, "Slick not found in cache")