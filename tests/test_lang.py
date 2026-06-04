import json
from pathlib import Path

import allure
import pytest

from environment_config import Environment, resolve_environment

pytestmark = allure.feature("Countries API")

LANGUAGES = json.loads(
    (Path(__file__).parent.parent / "test_data" / "lang_inputs.json").read_text()
)


@pytest.fixture(scope="module")
def environment(request: pytest.FixtureRequest) -> Environment:
    env_option = request.config.getoption("--env")
    if env_option and env_option != "countries":
        pytest.skip(f"--env {env_option} selected; skipping lang tests")
    return resolve_environment("countries")


@pytest.mark.parametrize("lang", LANGUAGES, ids=[l["name"] for l in LANGUAGES])
def test_lang_schema(http_client, environment, lang):
    response = http_client.get(f"/lang/{lang['code']}")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list) and len(results) > 0
    country = results[0]
    assert "status" in country


@pytest.mark.parametrize("lang", LANGUAGES, ids=[l["name"] for l in LANGUAGES])
def test_lang_result_count(http_client, environment, lang):
    response = http_client.get(f"/lang/{lang['code']}")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) >= environment.min_results_count, (
        f"/lang/{lang['code']} returned {len(results)} countries; "
        f"expected >= {environment.min_results_count}"
    )


def test_lang_korean_appears_in_region(http_client, environment):
    lang_resp = http_client.get("/lang/korean")
    assert lang_resp.elapsed.total_seconds() < environment.max_response_time
    assert lang_resp.status_code == 200
    lang_results = lang_resp.json()
    assert isinstance(lang_results, list) and len(lang_results) > 0
    korean_country_name = lang_results[0]["name"]["common"]

    region_resp = http_client.get("/region/asia")
    assert region_resp.elapsed.total_seconds() < environment.max_response_time
    assert region_resp.status_code == 200
    region_results = region_resp.json()
    assert isinstance(region_results, list) and len(region_results) > 0

    region_names = {c["name"]["common"] for c in region_results}
    assert korean_country_name in region_names, (
        f"{korean_country_name!r} from /lang/korean not found in /region/asia response "
        f"({len(region_names)} countries returned)"
    )


def test_lang_japanese_appears_in_region(http_client, environment):
    lang_resp = http_client.get("/lang/japanese")
    assert lang_resp.elapsed.total_seconds() < environment.max_response_time
    assert lang_resp.status_code == 200
    lang_results = lang_resp.json()
    assert isinstance(lang_results, list) and len(lang_results) > 0
    japanese_country_name = lang_results[0]["name"]["common"]

    region_resp = http_client.get("/region/asia")
    assert region_resp.elapsed.total_seconds() < environment.max_response_time
    assert region_resp.status_code == 200
    region_results = region_resp.json()
    assert isinstance(region_results, list) and len(region_results) > 0

    region_names = {c["name"]["common"] for c in region_results}
    assert japanese_country_name in region_names, (
        f"{japanese_country_name!r} from /lang/japanese not found in /region/asia response "
        f"({len(region_names)} countries returned)"
    )


def test_lang_not_found_returns_404(http_client, environment):
    response = http_client.get("/lang/notareallanguagexyz")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 404
