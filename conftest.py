from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest

from environment_config import Environment


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Restrict to one environment from config/environments.yaml (e.g. countries, weather)",
    )


@pytest.fixture
def http_client(environment: Environment) -> Iterator[httpx.Client]:
    with httpx.Client(
        base_url=environment.base_url,
        timeout=environment.max_response_time,
    ) as client:
        yield client
