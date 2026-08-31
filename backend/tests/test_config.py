import logging

import pytest
from api.config import Settings


@pytest.mark.parametrize(
    ("log_level", "expected"),
    [
        ("debug", logging.DEBUG),
        ("info", logging.INFO),
        ("warn", logging.WARNING),
        ("warning", logging.WARNING),
        ("error", logging.ERROR),
        ("critical", logging.CRITICAL),
        ("fatal", logging.CRITICAL),
    ],
)
def test_logging_level_maps_log_level_to_stdlib_constant(
    log_level: str, expected: int
) -> None:
    settings = Settings(LOG_LEVEL=log_level)  # type: ignore[call-arg]

    assert settings.logging_level == expected
