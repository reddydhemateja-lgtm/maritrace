from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "MARITRACE API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LIVE_MODE: bool = False

    # Satellite (Copernicus)
    COPERNICUS_CLIENT_ID: str = ""
    COPERNICUS_CLIENT_SECRET: str = ""
    SATELLITE_PROVIDER: str = "copernicus"

    # AIS
    AIS_API_KEY: str = ""
    AIS_API_URL: str = ""

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"

    # Ocean / Weather – Open-Meteo
    OCEAN_API_URL: str = "https://marine-api.open-meteo.com/v1/marine"
    OCEAN_API_KEY: str = "free"
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_API_KEY: str = "free"

    # Model
    MODEL_PATH: str = "models/best_model.pth"

    # Database
    DATABASE_URL: str = "sqlite:///./maritrace.db"

    # Frontend URL (optional)
    vite_api_url: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


config = Settings()