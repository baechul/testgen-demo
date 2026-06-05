import allure
import pytest
from utils.environment_config import Environment, resolve_environment
from validators.country_validator import CountryValidator

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

    CountryValidator.assert_valid(results[0])

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


def test_region_americas_schema(http_client, environment):
    response = http_client.get("/region/americas")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    country = results[0]
    assert "area" in country
    assert "population" in country


def test_region_americas_result_count(http_client, environment):
    response = http_client.get("/region/americas")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 30  # Americas has >30 sovereign states; conservative lower bound


def test_region_americas_area_in_valid_range(http_client, environment):
    response = http_client.get("/region/americas")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    # Filter to entries that report an area value (some territories omit the field or return None)
    areas = [c["area"] for c in results if c.get("area") is not None]
    assert len(areas) > 0, "No countries in /region/americas returned an area value"

    # Area must be strictly positive — even the smallest territory (e.g. Saint Kitts ~261 km²) has area > 0
    out_of_range = [a for a in areas if not (a > 0)]
    assert len(out_of_range) == 0, (
        f"area values <= 0 found in /region/americas response: {out_of_range}"
    )


def test_region_americas_population_in_valid_range(http_client, environment):
    response = http_client.get("/region/americas")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    populations = [c["population"] for c in results if c.get("population") is not None]
    assert len(populations) > 0, "No countries in /region/americas returned a population value"

    # Population must be >= 0; some territories have 0 permanent residents but none can be negative
    out_of_range = [p for p in populations if not (p >= 0)]
    assert len(out_of_range) == 0, (
        f"population values < 0 found in /region/americas response: {out_of_range}"
    )
