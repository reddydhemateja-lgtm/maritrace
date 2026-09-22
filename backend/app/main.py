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
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# ===== Lifespan =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Main] Starting up...")
    
    # Create database tables if they don't exist
    try:
        from .database.database import Base, engine
        from .database import seed  # triggers model registration
        Base.metadata.create_all(bind=engine)
        print("[Main] Database tables created/verified")
        
        # Optionally seed demo data (only inserts if tables are empty)
        from .database.seed import seed_all
        from .database.database import SessionLocal
        with SessionLocal() as db:
            seed_all(db)
        print("[Main] Seed data loaded")
    except Exception as e:
        print(f"[Main] DB setup warning: {e}")
    
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

# CORS — read allowed origins from environment variable (comma-separated).
# Falls back to localhost origins for development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in config.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ All routers must be mounted – including vessels
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "init", "status": "connected"})
        while True:
            await asyncio.sleep(5)
            await manager.broadcast({"type": "ping", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)