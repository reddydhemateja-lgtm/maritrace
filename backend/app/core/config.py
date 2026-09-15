from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    AISSTREAM_API_KEY: str = ""
    AISSTREAM_WS: str = "wss://stream.aisstream.io/v0/stream"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    AIS_BBOX_SW: str = "18.5,70.5"
    AIS_BBOX_NE: str = "21.5,73.5"
    CDSE_USER: str = ""
    CDSE_PASSWORD: str = ""
    GFW_API_TOKEN: str = ""

    @property
    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def ais_bbox(self) -> list:
        s, w = map(float, self.AIS_BBOX_SW.split(","))
        n, e = map(float, self.AIS_BBOX_NE.split(","))
        return [[s, w], [n, e]]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()