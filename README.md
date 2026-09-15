# MARITRACE — Marine Oil Spill Intelligence

SIH 2026 · Problem 26143 · Team AstraX-22

## Quick Start

### Backend
    cd backend
    python -m venv .venv
    .venv\Scripts\activate           # Windows
    pip install -r requirements.txt
    python scripts/load_historical_spills.py   # one-time
    python run.py

### Frontend (new terminal)
    cd frontend
    npm install
    npm run dev

Open http://127.0.0.1:5173

## Architecture
- **Backend:** FastAPI + WebSocket, live AISStream consumer, cached Cerulean spills
- **Drift:** Lagrangian hindcast using Open-Meteo currents + winds
- **Attribution:** 5-factor scoring (spatial 30%, temporal 25%, trajectory 25%, drift 10%, anomaly 10%)
- **Frontend:** React + Leaflet + Recharts tactical dashboard