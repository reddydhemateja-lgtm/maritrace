"""Drift hindcast endpoint."""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from shapely.geometry import shape

from app.services.cache import spill_cache
from app.services.drift import hindcast

log = logging.getLogger("drift")

router = APIRouter(prefix="/drift", tags=["drift"])


class DriftRequest(BaseModel):
    slick_id: int
    hours_back: int = 72


@router.post("/hindcast")
async def run_hindcast(req: DriftRequest):
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

    ts = slick.get("timestamp")
    try:
        slick_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, "Invalid slick timestamp")

    hc = await hindcast(geom, slick_time, hours_back=req.hours_back)

    return {
        "slick_id": req.slick_id,
        "origin_lon": hc["origin_center"][0],
        "origin_lat": hc["origin_center"][1],
        "origin_time": hc["origin_time"].isoformat(),
        "cone_wkt": hc["cone_geom"].wkt if not hc["cone_geom"].is_empty else None,
        "ensemble_count": len(hc["ensembles"]),
    }