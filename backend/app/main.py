"""FastAPI app — wires routers and starts background tasks."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import health, slicks, ais, drift, investigations, satellite
from app.services import ais_client
from app.routers.slicks import refresh_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")

_bg_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting background tasks…")
    ais_client.start()
    _bg_tasks.append(asyncio.create_task(refresh_loop()))
    log.info("Background tasks started")
    yield
    log.info("Shutting down…")
    await ais_client.stop()
    for t in _bg_tasks:
        t.cancel()
    log.info("Shutdown complete")


app = FastAPI(title="MARITRACE API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(slicks.router)
app.include_router(ais.router)
app.include_router(drift.router)
app.include_router(investigations.router)
app.include_router(satellite.router)