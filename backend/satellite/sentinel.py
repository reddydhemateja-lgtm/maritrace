"""Sentinel-1 SAR search via Copernicus Data Space Ecosystem."""
import os
import logging
from datetime import datetime, timedelta

import httpx

log = logging.getLogger("sentinel")

TOKEN_URL = ("https://identity.dataspace.copernicus.eu/auth/realms/CDSE"
             "/protocol/openid-connect/token")
SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"


async def get_token() -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(TOKEN_URL, data={
            "grant_type": "password",
            "client_id": "cdse-public",
            "username": os.getenv("CDSE_USER", ""),
            "password": os.getenv("CDSE_PASSWORD", ""),
        })
        r.raise_for_status()
        return r.json()["access_token"]


async def search_sar(bbox_wkt: str, hours_back: int = 48) -> list[dict]:
    if not os.getenv("CDSE_USER"):
        return []
    start = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + "Z"
    filt = (
        "Collection/Name eq 'SENTINEL-1' "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{bbox_wkt}') "
        f"and ContentDate/Start gt {start} "
        "and Attributes/OData.CSC.StringAttribute/any("
        "att:att/Name eq 'productType' "
        "and att/OData.CSC.StringAttribute/Value eq 'GRD')"
    )
    params = {"$filter": filt, "$top": 20, "$orderby": "ContentDate/Start desc"}
    try:
        token = await get_token()
    except Exception as e:
        log.warning("CDSE auth failed: %s", e)
        return []
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.get(SEARCH_URL, params=params,
                        headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json().get("value", [])