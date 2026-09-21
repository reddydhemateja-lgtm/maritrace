# MARITRACE — AI-Powered Marine Oil Spill Detection & Vessel Attribution

**Team:** SVCET AstraX-22  
**Problem Statement ID:** 26143  
**Theme:** Disaster Management | **Category:** Software

---

## 🎯 Overview

MARITRACE detects oil spills from satellite imagery, traces their origin using oceanographic drift modelling, and attributes them to vessels using historical AIS data — with fully explainable AI.

## 🚀 Features

- **SAR Satellite Analysis** — U-Net segmentation of oil slicks from Sentinel-1 imagery
- **Drift Hindcast & Forecast** — Backward/forward Lagrangian modelling with live ocean & wind data
- **AIS Vessel Intelligence** — Historical vessel reconstruction and multi-criteria scoring
- **Investigation Workspace** — Evidence fusion, timeline, and ranked attribution
- **Automated Reports** — PDF/CSV dossiers for coast guard use

## 🧠 Tech Stack

- **Frontend:** React + TypeScript + Vite + Tailwind + Leaflet + Recharts
- **Backend:** FastAPI + SQLAlchemy + Uvicorn
- **ML:** PyTorch (U-Net), OpenCV
- **Data:** Sentinel-1 SAR, AISStream.io, Open-Meteo (weather + ocean)
- **Deployment:** Vercel (frontend) + Render (backend)

## 🔧 Local Setup

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000