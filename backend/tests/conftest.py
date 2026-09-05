import os

# api.config resolves its .env file from ENV at import time, so this has to run
# before anything imports the application. pytest loads conftest.py before it
# imports any test module.
os.environ["ENV"] = "test"

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import api


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An HTTP client bound to the application, without a network layer."""
    async with AsyncClient(
        transport=ASGITransport(app=api), base_url="http://test"
    ) as client:
        yield client
