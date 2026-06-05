import json
import allure
import pytest
from pathlib import Path
from utils.environment_config import Environment, resolve_environment
from validators.forecast_validator import ForecastValidator

pytestmark = allure.feature("Weather API")

CITIES = json.loads(
    (Path(__file__).parent.parent / "test_data" / "cities.json").read_text()
)

@pytest.fixture(scope="module")
def environment(request: pytest.FixtureRequest) -> Environment:
    env_option = request.config.getoption("--env")
    if env_option and env_option != "weather":
        pytest.skip(f"--env {env_option} selected; skipping weather tests")
    return resolve_environment("weather")

@pytest.mark.parametrize("city", CITIES, ids=[c["name"] for c in CITIES])
def test_forecast_schema(http_client, environment, city):
    response = http_client.get(
        "/forecast",
        params={
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "hourly": "temperature_2m",
        },
    )
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    ForecastValidator.assert_valid(response.json())