from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest

from utils.environment_config import Environment


def pytest_addoption(parser: pytest.Parser) -> None:
    """ CLI custom options
    """
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Restrict to one environment from config/environments.yaml (e.g. countries, weather)",
    )


@pytest.fixture
def http_client(environment: Environment) -> Iterator[httpx.Client]:
    """ A fixture for HTTP client to be used by API tests
        timeout is set from environment.max_response_time so the client enforces the
        SLA at the transport level — a second line of defence on top of the
        response-time assertions in each test (RULE-HTTP-002)
    """
    with httpx.Client(
        base_url=environment.base_url,
        timeout=environment.max_response_time,
        headers=environment.headers,
    ) as client:
        yield client
