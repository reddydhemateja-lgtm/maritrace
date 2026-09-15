"""Sentinel-1 search."""
from fastapi import APIRouter, Query
from satellite.sentinel import search_sar

router = APIRouter(prefix="/satellite", tags=["satellite"])


@router.get("/search")
async def satellite_search(
    bbox: str = Query("70.5,18.5,73.5,21.5"),
    hours: int = 48,
):
    try:
        minx, miny, maxx, maxy = map(float, bbox.split(","))
    except Exception:
        return {"error": "invalid bbox"}

    wkt = f"POLYGON(({minx} {miny},{maxx} {miny},{maxx} {maxy},{minx} {maxy},{minx} {miny}))"
    try:
        results = await search_sar(wkt, hours_back=hours)
        return {"count": len(results), "products": results}
    except Exception as e:
        return {"error": str(e)}