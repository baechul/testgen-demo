# Testing Standards

**Version**: 1.2
**Last Updated**: 2026-06-04
**Owner**: Baechul Kim

---

## Overview

These rules govern **how tests are written** in the `testgen-demo` integration test suite: parametrization patterns, data sourcing, assertion ordering, what to validate on each endpoint, naming conventions, and output discipline. They are not concerned with how the framework is wired together — those structural constraints live in `framework-rules.md`.

Rules marked **REQUIRED** are non-negotiable; violations must be corrected before a PR is merged. Rules marked **RECOMMENDED** represent strong defaults; deviations require a comment explaining the exception.

Rules about what to test and how to structure tests live in `testing-standards.md`. Rules about framework wiring (fixture scopes, CI configuration, import boundaries between modules) live in `framework-rules.md`.

---

## Rules

### RULE-ALL-001: `allure.feature` marker required on every test module

**Severity**: REQUIRED

**Rationale**: Allure reports are the primary artifact reviewed after CI runs. Without a `feature` label, tests appear in the report under an unnamed group, making triage and drill-down impossible when reports contain results from multiple services.

**Rule**: Every test file must declare a module-level `pytestmark` with `allure.feature("<Service Name>")` as its first non-import statement. The feature name must match the human-readable API name (e.g., `"Countries API"`, `"Weather API"`), not the internal environment key.

**Good Example**:
```python
import allure
import pytest
from environment_config import resolve_environment

pytestmark = allure.feature("Countries API")
```

**Bad Example**:
```python
# test file with no pytestmark
import pytest
from environment_config import resolve_environment

def test_something(http_client, environment):
    ...
```

**Exceptions**: `conftest.py` is not a test module and does not require `pytestmark`.

---

### RULE-HTTP-001: Every HTTP call must assert response time before asserting body content

**Severity**: REQUIRED

**Rationale**: `max_response_time` is the contractual SLA for each environment, stored in `config/environments.yaml`. Asserting it on every response ensures that performance regressions are caught at the same level as functional failures. Placing the response-time assertion first enforces a consistent reading order and prevents body assertions from masking a latency violation that happened to return a valid payload.

**Rule**: Immediately after every `http_client.get(...)` (or any HTTP verb call), the test must assert:

```python
assert response.elapsed.total_seconds() < environment.max_response_time
```

This assertion must appear before any assertions on the response status code or body. Omitting it on even one call creates a blind spot.

**Good Example**:
```python
def test_germany_schema(http_client, environment):
    response = http_client.get("/name/germany")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200
    country = response.json()[0]
    assert "name" in country
```

**Bad Example**:
```python
def test_germany_schema(http_client, environment):
    response = http_client.get("/name/germany")
    assert response.status_code == 200  # response time never checked
    country = response.json()[0]
    assert "name" in country
```

**Exceptions**: Tests that are explicitly testing timeout or error behavior and deliberately trigger slow or failing requests may omit this assertion, but must be marked `@pytest.mark.slow` and include a comment explaining the omission.

---

### RULE-ASS-001: Assertion ordering within a test follows the sequence: latency, status, shape, content

**Severity**: RECOMMENDED

**Rationale**: A consistent assertion sequence means any reader can scan a test top-to-bottom and immediately understand what layer of the contract is being checked. Failures are also more informative: a latency failure at line 3 is unambiguous; a content failure at line 10 presupposes the earlier layers passed. Mixing orders forces readers to reconstruct intent from context.

**Rule**: Within a single test function, assertions must follow this sequence:
1. Response time (`response.elapsed.total_seconds() < environment.max_response_time`)
2. Status code (`response.status_code == 200`)
3. Shape (`isinstance(result, list)`, `len(result) > 0`, top-level key presence)
4. Content (field values, domain constraints, cross-field relationships)

**Good Example**:
```python
def test_forecast(http_client, environment, city):
    response = http_client.get("/forecast", params={...})
    assert response.elapsed.total_seconds() < environment.max_response_time  # 1. latency
    assert response.status_code == 200                                        # 2. status
    data = response.json()
    assert "timezone" in data                                                 # 3. shape
    temperatures = data["hourly"]["temperature_2m"]
    assert len(temperatures) > 0                                              # 3. shape
    assert all(-80 <= t <= 60 for t in temperatures)                         # 4. content
```

**Bad Example**:
```python
def test_forecast(http_client, environment, city):
    response = http_client.get("/forecast", params={...})
    data = response.json()
    assert all(-80 <= t <= 60 for t in data["hourly"]["temperature_2m"])  # content before status
    assert response.status_code == 200
    assert response.elapsed.total_seconds() < environment.max_response_time
```

**Exceptions**: None.

---

### RULE-SCHEMA-001: Every endpoint must have at least one dedicated schema validation test

**Severity**: REQUIRED

**Rationale**: Schema validation tests are the first line of defense against breaking API changes. If the upstream API removes or renames a field, a schema test catches it immediately and with a clear failure message. Tests that only check status codes or aggregate counts will pass silently in the face of structural regressions.

**Rule**: For every endpoint exercised in the test suite, at least one test function must assert the presence and type of every top-level field in the response contract. For list responses, assertions must be made against `results[0]`, not the list as a whole. The test name must include `_schema` (e.g., `test_germany_schema`, `test_forecast_schema`).

**Good Example**:
```python
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
```

**Bad Example**:
```python
def test_germany(http_client, environment):
    response = http_client.get("/name/germany")
    assert response.status_code == 200
    # no field presence checks — structural regressions pass silently
```

**Exceptions**: Endpoints that return a single scalar value (e.g., a plain integer or boolean) need not follow the `results[0]` pattern but must still assert field presence where applicable.

---

### RULE-DATA-001: External test data files live under `test_data/` at the project root

**Severity**: REQUIRED

**Rationale**: `test_weather.py` loads `test_data/cities.json` using a path anchored to `Path(__file__).parent.parent`. Establishing `test_data/` as the canonical location for static test data files prevents scattering JSON/CSV/fixture files across the repository and makes it obvious where to look when adding new parametrize datasets.

**Rule**: All static data files consumed by tests (JSON, CSV, YAML payloads, etc.) must be placed under the `test_data/` directory at the project root. Test files reference them using `Path(__file__).parent.parent / "test_data" / "<filename>"`. These files must be committed to the repository.

**Good Example**:
```python
CITIES = json.loads(
    (Path(__file__).parent.parent / "test_data" / "cities.json").read_text()
)
```

**Bad Example**:
```python
# data file committed next to the test file
CITIES = json.loads(
    (Path(__file__).parent / "cities.json").read_text()
)
```

**Exceptions**: None.

---

### RULE-DATA-002: Parametrize data-driven tests from files only; no inline test data

**Severity**: RECOMMENDED

**Rationale**: Inline parametrize data (dicts or values declared directly in the `@pytest.mark.parametrize` decorator) mixes test inputs with test logic and makes it impossible to extend the dataset without touching test code. Loading from `test_data/` allows QA and non-engineers to add cases without modifying Python files and keeps test data reviewable as a separate diff artifact.

**Rule**: Any `@pytest.mark.parametrize` call that operates over a collection of structured records (dicts, objects) must load that collection from a file under `test_data/`. Inline list literals containing more than one structured record are forbidden. The file is loaded at module scope (not inside the test function).

**Good Example**:
```python
# test_data/cities.json contains the dataset
CITIES = json.loads(
    (Path(__file__).parent.parent / "test_data" / "cities.json").read_text()
)

@pytest.mark.parametrize("city", CITIES, ids=[c["name"] for c in CITIES])
def test_forecast(http_client, environment, city):
    ...
```

**Bad Example**:
```python
@pytest.mark.parametrize("city", [
    {"name": "Tokyo", "latitude": 35.68, "longitude": 139.69},
    {"name": "London", "latitude": 51.51, "longitude": -0.13},
])
def test_forecast(http_client, environment, city):
    ...
```

**Exceptions**: Single scalar values (strings, ints, booleans) used to test boundary conditions may be declared inline if they are self-explanatory and fewer than five cases.

---

### RULE-DATA-003: `@pytest.mark.parametrize` over structured data must supply explicit `ids`

**Severity**: REQUIRED

**Rationale**: Without explicit `ids`, pytest generates opaque identifiers like `city0`, `city1`. This makes Allure reports and failure output ambiguous when a single parametrized case fails — the reader cannot determine which city or record triggered the failure without cross-referencing the source data file.

**Rule**: Any `@pytest.mark.parametrize` call over a list of dicts or objects must supply an `ids=` argument that produces a human-readable, unique string for each case. The `ids` must be derived from a field in the data, not hardcoded.

**Good Example**:
```python
@pytest.mark.parametrize("city", CITIES, ids=[c["name"] for c in CITIES])
def test_forecast(http_client, environment, city):
    ...
```

**Bad Example**:
```python
@pytest.mark.parametrize("city", CITIES)  # generates city0, city1, ...
def test_forecast(http_client, environment, city):
    ...
```

**Exceptions**: Single scalar parametrize values (strings, ints) where pytest generates readable IDs automatically (e.g., `parametrize("status_code", [200, 404, 500])`).

---

### RULE-DOMAIN-001: Numeric response values must be asserted against domain-valid ranges

**Severity**: REQUIRED

**Rationale**: Asserting only that a numeric field is non-empty (`len(temperatures) > 0`) will pass even if the API returns physically impossible values (e.g., a temperature of 9999 due to a serialization bug). Domain range assertions are a lightweight sanity check that catches data corruption or unit-conversion errors that structural checks miss.

**Rule**: Any numeric field with a known physical or business domain (temperatures, coordinates, population counts, currency rates, etc.) must be asserted against its valid range. The range must be expressed as a closed interval with comment explaining the bound choice.

**Good Example**:
```python
temperatures = data["hourly"]["temperature_2m"]
assert len(temperatures) > 0
# -80°C (Antarctic record low) to 60°C (documented surface maximum)
assert all(-80 <= t <= 60 for t in temperatures)
```

**Bad Example**:
```python
temperatures = data["hourly"]["temperature_2m"]
assert len(temperatures) > 0  # does not catch values like 9999 or -9999
```

**Exceptions**: Fields with no well-defined domain bound (e.g., free-text strings, opaque IDs) are exempt.

---

### RULE-CROSS-001: Cross-endpoint consistency tests must be written when one endpoint's output is a subset of another's

**Severity**: RECOMMENDED

**Rationale**: APIs often expose both narrow (single-entity) and broad (collection) endpoints for the same data. A record returned by the narrow endpoint must appear in the collection endpoint's response. If it does not, one of the two endpoints has a bug. These tests catch divergence that pure schema tests miss because both endpoints can pass individually while being mutually inconsistent.

**Rule**: When the test suite exercises both a single-entity endpoint (e.g., `/name/germany`) and a collection endpoint that should contain that entity (e.g., `/region/europe`), at least one test must assert that the entity from the narrow endpoint is present in the collection. Use the canonical identifier field (e.g., `name.common`) as the membership key.

**Good Example**:
```python
def test_name_search_appears_in_region(http_client, environment):
    name_resp = http_client.get("/name/germany")
    assert name_resp.elapsed.total_seconds() < environment.max_response_time
    name_results = name_resp.json()
    assert isinstance(name_results, list) and len(name_results) > 0
    germany_name = name_results[0]["name"]["common"]

    region_resp = http_client.get("/region/europe")
    assert region_resp.elapsed.total_seconds() < environment.max_response_time
    region_results = region_resp.json()
    assert isinstance(region_results, list) and len(region_results) > 0

    region_names = {c["name"]["common"] for c in region_results}
    assert germany_name in region_names
```

**Bad Example**:
```python
# tests only the narrow endpoint and the collection independently,
# never checks that their results are consistent with each other
def test_germany(http_client, environment):
    ...

def test_europe(http_client, environment):
    ...
```

**Exceptions**: Collection endpoints that are not semantically supersets of the narrow endpoint (e.g., a search endpoint with different filtering semantics) do not require a cross-consistency test.

---

### RULE-COUNT-001: Collection endpoint tests must assert a minimum result count

**Severity**: RECOMMENDED

**Rationale**: An empty list (`[]`) is a structurally valid JSON response but represents a data availability failure. Asserting a minimum count guards against silent regressions where a filter bug or data migration causes a collection to return fewer results than expected. The threshold should be set conservatively to be stable across API updates.

**Rule**: Any test that calls a collection endpoint (one that returns a list of records) must assert `len(results) > N` where `N` is a conservative lower bound derived from domain knowledge or `environment.min_results_count`. The bound must not be so tight that legitimate API changes cause spurious failures.

**Good Example**:
```python
def test_region_europe_result_count(http_client, environment):
    response = http_client.get("/region/europe")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 40  # Europe has >40 countries; stable lower bound
```

**Bad Example**:
```python
def test_region_europe(http_client, environment):
    response = http_client.get("/region/europe")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)  # passes even if results is []
```

**Exceptions**: Endpoints whose result count is legitimately variable or unbounded (e.g., search endpoints with user-supplied queries) should use `environment.min_results_count` rather than a hardcoded constant.

---

### RULE-VAL-001: Response payload validation must use a typed validator class from `src/validators/`

**Severity**: REQUIRED

**Rationale**: Scattered `assert "field" in response` checks across test functions are fragile and inconsistent — each test rediscovers and re-asserts the same contract independently, so a field rename breaks tests in many places and a new required field is silently skipped unless every test is updated. A dedicated validator class centralizes the contract, makes it reviewable as a first-class artifact, and gives a single place to update when the API schema evolves.

**Rule**: All response payload validation (field presence, type checks, nested structure) must be delegated to a typed validator class located under `src/validators/`. Test functions call the validator and assert its return value; they do not perform inline `assert "field" in data` checks for fields covered by the validator.

If a validator for an endpoint does not yet exist, use the `/validator-generator` skill to generate it before writing or reviewing tests for that endpoint.

**Good Example**:
```python
# src/validators/country_validator.py (generated via /validator-generator)
class CountryValidator:
    def validate(self, data: dict) -> bool:
        required = {"name", "capital", "population", "currencies", "languages"}
        return all(field in data for field in required)

# tests/test_countries.py
from src.validators.country_validator import CountryValidator

def test_germany_schema(http_client, environment):
    response = http_client.get("/name/germany")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200
    country = response.json()[0]
    assert CountryValidator().validate(country), f"Schema validation failed: {country}"
```

**Bad Example**:
```python
def test_germany_schema(http_client, environment):
    response = http_client.get("/name/germany")
    assert response.status_code == 200
    country = response.json()[0]
    assert "name" in country        # inline field checks scattered across tests
    assert "capital" in country
    assert "population" in country
    assert "currencies" in country
    assert "languages" in country
```

**Exceptions**: Single-field spot checks added for a specific edge case (e.g., asserting a newly-discovered optional field) may be inline until a validator update is made. The validator must be updated in the same PR.
