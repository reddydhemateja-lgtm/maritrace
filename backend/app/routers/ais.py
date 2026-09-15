"""AIS endpoints — serve from in-memory cache."""
from fastapi import APIRouter, Query
from app.services.cache import ais_vessels

router = APIRouter(prefix="/ais", tags=["ais"])


@router.get("/vessels")
async def list_vessels(
    bbox: str | None = Query(None, description="minx,miny,maxx,maxy"),
    limit: int = 500,
):
    items = list(ais_vessels.values())

    if bbox:
        try:
            minx, miny, maxx, maxy = map(float, bbox.split(","))
            items = [
                v for v in items
                if v.get("lon") is not None and v.get("lat") is not None
                and minx <= v["lon"] <= maxx and miny <= v["lat"] <= maxy
            ]
        except Exception:
            pass

    items = [v for v in items if v.get("lon") is not None]
    items.sort(key=lambda v: v.get("last_ts") or "", reverse=True)

    return {"count": len(items), "vessels": items[:limit]}


@router.get("/vessels/{mmsi}")
async def get_vessel(mmsi: int):
    v = ais_vessels.get(mmsi)
    if not v:
        return {"error": "not found"}
    return v