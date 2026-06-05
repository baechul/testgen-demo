from __future__ import annotations

import re

import allure
import pytest

from utils.environment_config import Environment, resolve_environment
from validators.currency_validator import CurrencyCountryValidator

pytestmark = allure.feature("Countries API")


@pytest.fixture(scope="module")
def environment(request: pytest.FixtureRequest) -> Environment:
    env_option = request.config.getoption("--env")
    if env_option and env_option != "countries":
        pytest.skip(f"--env {env_option} selected; skipping currency tests")
    return resolve_environment("countries")


def test_currency_usd_schema(http_client: "httpx.Client", environment: Environment) -> None:
    response = http_client.get("/currency/USD")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    CurrencyCountryValidator.assert_valid(results[0])


def test_currency_usd_result_count(http_client: "httpx.Client", environment: Environment) -> None:
    response = http_client.get("/currency/USD")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list)
    # USD is used by the US and many territories; conservatively >5 countries/territories
    assert len(results) > 5, (
        f"Expected >5 countries using USD, got {len(results)}"
    )


def test_currency_usd_timezones_valid_format(http_client: "httpx.Client", environment: Environment) -> None:
    response = http_client.get("/currency/USD")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    # UTC offset pattern: "UTC", "UTC+HH:MM", or "UTC-HH:MM"
    utc_pattern = re.compile(r"^UTC([+-]\d{2}:\d{2})?$")
    invalid: list[str] = []
    for country in results:
        for tz in country.get("timezones", []):
            if not utc_pattern.match(tz):
                invalid.append(f"{country['name']['common']}: {tz!r}")

    assert len(invalid) == 0, (
        f"Timezone values with unexpected format (expected UTC or UTC±HH:MM): {invalid}"
    )


def test_currency_usd_languages_non_empty(http_client: "httpx.Client", environment: Environment) -> None:
    response = http_client.get("/currency/USD")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    # Every country using USD should declare at least one language
    countries_without_language = [
        country["name"]["common"]
        for country in results
        if not country.get("languages")
    ]
    assert len(countries_without_language) == 0, (
        f"Countries with USD but no declared language: {countries_without_language}"
    )


def test_currency_usd_region_non_empty(http_client: "httpx.Client", environment: Environment) -> None:
    response = http_client.get("/currency/USD")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list) and len(results) > 0

    # Every country should belong to a recognized geographic region (non-empty string)
    countries_without_region = [
        country["name"]["common"]
        for country in results
        if not country.get("region")
    ]
    assert len(countries_without_region) == 0, (
        f"Countries with USD but empty/missing region: {countries_without_region}"
    )


def test_currency_usd_country_appears_in_region(http_client: "httpx.Client", environment: Environment) -> None:
    """Cross-endpoint consistency: a country from /currency/USD must appear
    in the /region/{region} collection for its declared region (RULE-CROSS-001).
    """
    currency_resp = http_client.get("/currency/USD")
    assert currency_resp.elapsed.total_seconds() < environment.max_response_time
    assert currency_resp.status_code == 200

    currency_results = currency_resp.json()
    assert isinstance(currency_results, list) and len(currency_results) > 0

    # Pick the first country with a non-empty region from the USD list
    reference_country = next(
        (c for c in currency_results if c.get("region")),
        None,
    )
    assert reference_country is not None, "No country with a region found in /currency/USD response"

    country_name = reference_country["name"]["common"]
    region = reference_country["region"].lower()

    region_resp = http_client.get(f"/region/{region}")
    assert region_resp.elapsed.total_seconds() < environment.max_response_time
    assert region_resp.status_code == 200

    region_results = region_resp.json()
    assert isinstance(region_results, list) and len(region_results) > 0

    region_names = {c["name"]["common"] for c in region_results}
    assert country_name in region_names, (
        f"{country_name!r} (from /currency/USD) not found in /region/{region} "
        f"({len(region_names)} countries returned)"
    )


def test_currency_usd_not_found_returns_404(http_client: "httpx.Client", environment: Environment) -> None:
    response = http_client.get("/currency/ZZZNOTREAL")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 404
