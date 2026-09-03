import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV: str = os.getenv("ENV", "production")
BACKEND_PATH = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_PATH / f".env.{ENV}",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: PostgresDsn
    FRONTEND_URL: str
    LOG_LEVEL: Literal["debug", "info", "warn", "warning", "error", "critical", "fatal"]

    @property
    def logging_level(self) -> int:
        match self.LOG_LEVEL:
            case "debug":
                return logging.DEBUG
            case "info":
                return logging.INFO
            case "warn" | "warning":
                return logging.WARNING
            case "error":
                return logging.ERROR
            case "critical" | "fatal":
                return logging.CRITICAL


settings = Settings()  # type: ignore[call-arg]
