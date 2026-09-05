from fastapi import APIRouter

main_router = APIRouter()

# Imported for its side effect: the module attaches its routes to main_router,
# which therefore has to exist first. noqa E402 (import below the top of the
# file) and F401 (imported but unused) both follow from that ordering.
import api.routes.health_check  # noqa: E402, F401
