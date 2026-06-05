import allure
import pytest
from utils.environment_config import Environment, resolve_environment

pytestmark = allure.feature("Countries API")

@pytest.fixture(scope="module")
def environment(request: pytest.FixtureRequest) -> Environment:
    env_option = request.config.getoption("--env")
    if env_option and env_option != "countries":
        pytest.skip(f"--env {env_option} selected; skipping countries tests")
    return resolve_environment("countries")

def test_germany_schema(http_client, environment):
    response = http_client.get("/name/germany")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    country = results[0]
    assert "name" in country
    assert "capital" in country
    assert "population" in country
    assert "currencies" in country
    assert "languages" in country

def test_name_search_appears_in_region(http_client, environment):
    name_resp = http_client.get("/name/germany")
    assert name_resp.elapsed.total_seconds() < environment.max_response_time
    assert name_resp.status_code == 200
    name_results = name_resp.json()
    assert isinstance(name_results, list) and len(name_results) > 0
    germany_name = name_results[0]["name"]["common"]

    region_resp = http_client.get("/region/europe")
    assert region_resp.elapsed.total_seconds() < environment.max_response_time
    assert region_resp.status_code == 200
    region_results = region_resp.json()
    assert isinstance(region_results, list) and len(region_results) > 0

    region_names = {c["name"]["common"] for c in region_results}
    assert germany_name in region_names, (
        f"{germany_name!r} not found in /region/europe response "
        f"({len(region_names)} countries returned)"
    )

def test_region_europe_result_count(http_client, environment):
    response = http_client.get("/region/europe")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 40  # Europe has >40 regions; conservative lower bound
