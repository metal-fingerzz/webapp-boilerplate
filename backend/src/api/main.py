import logging

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request

from api.config import ENV, settings
from api.error import (
    http_exception_json,
    request_validation_error_json,
    unhandled_exception_json,
)
from api.routes import main_router

IS_DEV_ENV: bool = ENV == "development"

logging.basicConfig(
    level=settings.logging_level,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

api = FastAPI(
    openapi_url="/openapi.json" if IS_DEV_ENV else None,
    docs_url="/docs" if IS_DEV_ENV else None,
    redoc_url="/redoc" if IS_DEV_ENV else None,
)


@api.exception_handler(RequestValidationError)
async def on_request_validation_error(
    request: Request, exception: RequestValidationError
):
    return request_validation_error_json(exception=exception)


@api.exception_handler(HTTPException)
async def on_http_exception(request: Request, exception: HTTPException):
    return http_exception_json(exception=exception)


@api.exception_handler(Exception)
async def on_unhandled_exception(request: Request, exception: Exception):
    logging.getLogger().exception(msg="Unhandled exception", exc_info=exception)
    return unhandled_exception_json()


api.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(router=main_router)
