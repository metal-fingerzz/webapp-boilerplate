from typing import Literal

from api.routes import main_router


@main_router.get(path="/health-check")
async def health_check() -> Literal["OK"]:
    return "OK"
