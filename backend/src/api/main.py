import logging

from fastapi import FastAPI

from api.config import ENV, settings
from api.routes import main_router

IS_DEV_ENV: bool = ENV == "development"

logging.basicConfig(
    level=settings.logging_level(),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

api = FastAPI(
    openapi_url="/openapi.json" if IS_DEV_ENV else None,
    docs_url="/docs" if IS_DEV_ENV else None,
    redoc_url="/redoc" if IS_DEV_ENV else None,
)

api.include_router(router=main_router)
