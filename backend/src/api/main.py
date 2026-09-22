import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from api.config import ENV, settings
from api.error import (
    http_exception_json,
    request_validation_error_json,
    unhandled_exception_json,
)
from api.routes import main_router
from api.routes.auth import auth_router

IS_DEV_ENV: bool = ENV == "development"

logging.basicConfig(
    level=settings.logging_level,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_engine: AsyncEngine = create_async_engine(
        url=str(settings.DATABASE_URL), pool_pre_ping=True
    )
    app.state.database_engine = database_engine
    app.state.database_session_factory = async_sessionmaker(
        database_engine, expire_on_commit=False
    )
    try:
        yield
    finally:
        await database_engine.dispose()


api = FastAPI(
    openapi_url="/openapi.json" if IS_DEV_ENV else None,
    docs_url="/docs" if IS_DEV_ENV else None,
    redoc_url="/redoc" if IS_DEV_ENV else None,
    lifespan=lifespan,
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
api.include_router(router=auth_router)
