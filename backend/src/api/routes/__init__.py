# ruff: noqa: F401
from fastapi import APIRouter

main_router = APIRouter()

import api.routes.health_check
