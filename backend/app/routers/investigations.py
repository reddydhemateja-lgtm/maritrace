"""Investigation pipeline — slick → hindcast → AIS correlation → ranking."""
import logging
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from shapely.geometry import shape

from app.services.cache import spill_cache, ais_vessels
from app.services.drift import hindcast
from app.services.attribution import score_candidates, _haversine_km
from app.services.persist import (
    init_db, save_investigation, load_all, delete_investigation, count,
)

log = logging.getLogger("investigations")

router = APIRouter(prefix="/investigate", tags=["investigations"])

# Initialize DB and load persisted investigations into memory
init_db()
_investigations: dict[str, dict] = load_all()
log.info("Loaded %d investigations from SQLite", len(_investigations))


class InvestigateRequest(BaseModel):
    slick_id: int
    hours_back: int = 72
    radius_km: float = 50.0


# Demo fleet used only when the AIS cache has <3 real vessels near origin
DEMO_FLEET = [
    {"mmsi": 419000123, "name": "MV SAGAR KANYA",    "type": "Crude Oil Tanker",    "flag": "India"},
    {"mmsi": 419000124, "name": "MT MUMBAI STAR",    "type": "Product Tanker",      "flag": "India"},
    {"mmsi": 419000125, "name": "MV CHENNAI EXPRESS","type": "Cargo",               "flag": "India"},
    {"mmsi": 419000126, "name": "MT ARABIAN PEARL",  "type": "Chemical Tanker",     "flag": "India"},
    {"mmsi": 419000127, "name": "MV KOCHI TRADER",   "type": "Bulk Carrier",        "flag": "India"},
    {"mmsi": 538001234, "name": "MT OCEAN SPIRIT",   "type": "Crude Oil Tanker",    "flag": "Marshall Islands"},
    {"mmsi": 636012345, "name": "MV ATLANTIC WIND",  "type": "Container Ship",      "flag": "Liberia"},
    {"mmsi": 563012345, "name": "MT PACIFIC STAR",   "type": "Oil Products Tanker", "flag": "Singapore"},
]


@router.post("")
async def investigate(req: InvestigateRequest):
    slick = None
    for s in spill_cache["data"]:
        if s.get("id") == req.slick_id:
            slick = s
            break
    if not slick:
        raise HTTPException(404, "Slick not found in cache")

    geom_dict = slick.get("geometry")
    if not geom_dict:
        raise HTTPException(400, "Slick has no geometry")

    try:
        geom = shape(geom_dict)
    except Exception as e:
        raise HTTPException(400, f"Invalid geometry: {e}")

    try:
        slick_time = datetime.fromisoformat(slick["timestamp"].replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, "Invalid slick timestamp")

    hc = await hindcast(geom, slick_time, hours_back=req.hours_back)
    origin_lon, origin_lat = hc["origin_center"]
    origin_time = hc["origin_time"]
    cone = hc["cone_geom"]

    origin_pt = (origin_lon, origin_lat)
    candidates = []

    # 1. Real AIS vessels
    for mmsi, v in ais_vessels.items():
        if v.get("lon") is None or v.get("lat") is None:
            continue
        d = _haversine_km(origin_pt, (v["lon"], v["lat"]))
        if d > req.radius_km:
            continue
        pos = (
            v.get("last_ts") or datetime.now(timezone.utc).isoformat(),
            v["lon"],
            v["lat"],
            v.get("sog"),
            v.get("cog"),
        )
        candidates.append({
            "mmsi": mmsi,
            "positions": [pos],
            "name": v.get("name", "") or "Unknown",
            "type": v.get("ship_type"),
            "synthetic": False,
        })

    # 2. Pad with demo fleet if not enough real vessels
    if len(candidates) < 3:
        log.warning(
            "Only %d live vessels near origin — padding with demo fleet",
            len(candidates),
        )
        for v in DEMO_FLEET:
            offset_lon = random.uniform(-0.3, 0.3)
            offset_lat = random.uniform(-0.3, 0.3)
            ts = origin_time + timedelta(minutes=random.randint(-120, 120))
            pos = (
                ts.isoformat(),
                origin_lon + offset_lon,
                origin_lat + offset_lat,
                random.uniform(6, 15),
                random.uniform(0, 360),
            )
            candidates.append({
                "mmsi": v["mmsi"],
                "positions": [pos],
                "name": v["name"],
                "type": v["type"],
                "flag": v["flag"],
                "synthetic": True,
            })

    ranked = score_candidates(
        candidates=candidates,
        origin_pt=origin_pt,
        origin_time=origin_time,
        slick_geom=geom,
        drift_cone=cone,
    )

    case_number = f"INV-{datetime.utcnow():%Y-%m}-{random.randint(1000, 9999)}"
    record = {
        "case_number": case_number,
        "slick_id": req.slick_id,
        "region": slick.get("region", "unknown"),
        "region_label": slick.get("region_label", slick.get("region", "unknown")),
        "source": slick.get("source", "live"),
        "origin": {
            "lon": origin_lon,
            "lat": origin_lat,
            "time": origin_time.isoformat(),
        },
        "candidates": ranked,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Persist to SQLite + memory
    _investigations[case_number] = record
    save_investigation(record)

    return record


@router.get("")
async def list_investigations():
    # Newest first
    items = list(_investigations.values())
    items.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return items


@router.get("/stats")
async def investigation_stats():
    return {
        "total": count(),
        "in_memory": len(_investigations),
    }


@router.get("/{case_number}")
async def get_investigation(case_number: str):
    inv = _investigations.get(case_number)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return inv


@router.delete("/{case_number}")
async def remove_investigation(case_number: str):
    if case_number in _investigations:
        del _investigations[case_number]
        delete_investigation(case_number)
        return {"deleted": case_number}
    raise HTTPException(404, "Investigation not found")


@router.get("/{case_number}/report.pdf")
async def download_report(case_number: str):
    inv = _investigations.get(case_number)
    if not inv:
        raise HTTPException(404, "Investigation not found")

    from app.services.report import generate_report
    try:
        pdf = generate_report(inv)
    except Exception as e:
        raise HTTPException(500, f"Report generation failed: {e}")

    region_slug = (
        inv.get("region_label", "unknown")
        .replace(" — ", "_")
        .replace(" ", "_")
        .replace("/", "-")
    )
    slick = inv.get("slick_id", "unknown")
    filename = f"MARITRACE_{region_slug}_slick-{slick}_{case_number}.pdf"

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )