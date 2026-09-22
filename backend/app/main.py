from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime

from .api import incidents, satellite, ais, drift, vessels, reports, investigation
from .config import config
from .services.ais_service import AISService
from .scheduler import start_scheduler

# ===== WebSocket Manager =====
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)

manager = ConnectionManager()

# ===== WebSocket Origin Whitelist =====
# Starlette blocks cross-origin WebSockets by default (403).
# These are the origins we allow to connect via WebSocket.
ALLOWED_WS_ORIGINS = [
    "https://martirace2.netlify.app",
    "https://martirace.netlify.app",
    "https://maritrace.netlify.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]

# Also allow anything in CORS_ORIGINS env var
try:
    for origin in config.CORS_ORIGINS.split(","):
        o = origin.strip()
        if o and o not in ALLOWED_WS_ORIGINS:
            ALLOWED_WS_ORIGINS.append(o)
except Exception:
    pass

print(f"[Main] Allowed WebSocket origins: {ALLOWED_WS_ORIGINS}")

def _ws_origin_ok(websocket: WebSocket) -> bool:
    """Check if the WebSocket origin is allowed. Empty origin (native clients) is OK."""
    origin = websocket.headers.get("origin", "")
    if not origin:
        return True  # native clients (curl, wscat) don't send origin
    return origin in ALLOWED_WS_ORIGINS

# ===== Lifespan =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Main] Starting up...")

    # Ensure DB tables exist and seed demo data
    try:
        from .database import seed
        seed.main()
        print("[Main] Database ready and seeded")
    except Exception as e:
        print(f"[Main] DB setup warning: {e}")
        import traceback
        traceback.print_exc()

    if config.LIVE_MODE:
        ais_service = AISService()
        asyncio.create_task(ais_service.listen_for_vessels())
        start_scheduler()
        print("[Main] Scheduler started (live mode)")
    yield
    print("[Main] Shutting down...")

# ===== FastAPI App =====
app = FastAPI(
    title="MARITRACE API",
    version="1.0",
    lifespan=lifespan,
)

# CORS for HTTP
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in config.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(satellite.router, prefix="/api/satellite", tags=["Satellite"])
app.include_router(ais.router, prefix="/api/ais", tags=["AIS"])
app.include_router(drift.router, prefix="/api/drift", tags=["Drift"])
app.include_router(vessels.router, prefix="/api/vessels", tags=["Vessels"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(investigation.router, prefix="/api/investigation", tags=["Investigation"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "mode": "live" if config.LIVE_MODE else "demo"}


# ===== WebSocket: /ws =====
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get("origin", "")
    if not _ws_origin_ok(websocket):
        print(f"[WS /ws] Rejected origin: {origin}")
        await websocket.close(code=1008)  # policy violation
        return

    print(f"[WS /ws] Accepted connection from origin: {origin or '(none)'}")
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "init", "status": "connected"})
        while True:
            await asyncio.sleep(5)
            await manager.broadcast({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"[WS /ws] Client disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        print(f"[WS /ws] Error: {e}")


# ===== WebSocket: /api/realtime/ws =====
@app.websocket("/api/realtime/ws")
async def realtime_websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get("origin", "")
    if not _ws_origin_ok(websocket):
        print(f"[WS /api/realtime/ws] Rejected origin: {origin}")
        await websocket.close(code=1008)
        return

    print(f"[WS /api/realtime/ws] Accepted connection from origin: {origin or '(none)'}")
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "init", "status": "connected"})
        while True:
            await asyncio.sleep(5)
            await manager.broadcast({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"[WS /api/realtime/ws] Client disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        print(f"[WS /api/realtime/ws] Error: {e}")