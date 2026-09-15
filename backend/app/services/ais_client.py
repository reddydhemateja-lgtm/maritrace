"""Persistent AISStream WebSocket consumer. Cache capped at 1000 vessels."""
import asyncio
import json
import logging

import websockets

from app.core.config import settings
from app.services.cache import ais_vessels

log = logging.getLogger("aisstream")

MAX_VESSELS = 1000
LOG_EVERY_N_REPORTS = 500

_consumer_task: asyncio.Task | None = None
_stop = asyncio.Event()


async def _consume_once():
    if not settings.AISSTREAM_API_KEY or settings.AISSTREAM_API_KEY.startswith("PASTE_"):
        log.error("AISSTREAM_API_KEY not set — AIS disabled")
        await asyncio.sleep(60)
        return

    bbox = settings.ais_bbox
    log.info("AISStream connecting: bbox=%s key_prefix=%s",
             bbox, settings.AISSTREAM_API_KEY[:8] + "...")

    async with websockets.connect(
        settings.AISSTREAM_WS,
        ping_interval=20,
        ping_timeout=20,
        max_size=2**22,
        compression="deflate",
    ) as ws:
        sub = {
            "APIKey": settings.AISSTREAM_API_KEY,
            "BoundingBoxes": [bbox],
            "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
        }
        await ws.send(json.dumps(sub))

        count = 0
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue

            mtype = msg.get("MessageType")

            if mtype == "SubscriptionConfirmation":
                log.info("AISStream subscription confirmed")
                continue

            meta = msg.get("MetaData", {})
            mmsi = meta.get("MMSI")
            ts = meta.get("time_utc")
            if not mmsi:
                continue

            mmsi_int = int(mmsi)

            if mmsi_int not in ais_vessels and len(ais_vessels) >= MAX_VESSELS:
                continue

            entry = ais_vessels.setdefault(mmsi_int, {
                "mmsi": mmsi_int,
                "name": "",
                "ship_type": None,
                "lon": None,
                "lat": None,
                "sog": None,
                "cog": None,
                "heading": None,
                "last_ts": None,
            })

            if mtype == "PositionReport":
                p = msg["Message"]["PositionReport"]
                entry.update({
                    "lon": p.get("Longitude"),
                    "lat": p.get("Latitude"),
                    "sog": p.get("Sog"),
                    "cog": p.get("Cog"),
                    "heading": p.get("TrueHeading"),
                    "last_ts": ts,
                })
                count += 1
                if count % LOG_EVERY_N_REPORTS == 0:
                    log.info("AISStream: %d PositionReports processed · cache %d/%d vessels",
                             count, len(ais_vessels), MAX_VESSELS)

            elif mtype == "ShipStaticData":
                s = msg["Message"]["ShipStaticData"]
                entry.update({
                    "name": (s.get("Name") or "").strip(),
                    "ship_type": s.get("Type"),
                })


async def _run():
    while not _stop.is_set():
        try:
            await _consume_once()
        except Exception as e:
            log.warning("AISStream disconnected: %s — retry in 5s", e)
            await asyncio.sleep(5)


def start():
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        return
    _consumer_task = asyncio.create_task(_run())
    log.info("AISStream background listener task started (cap=%d vessels)", MAX_VESSELS)


async def stop():
    _stop.set()
    if _consumer_task:
        try:
            await asyncio.wait_for(_consumer_task, timeout=5)
        except Exception:
            pass