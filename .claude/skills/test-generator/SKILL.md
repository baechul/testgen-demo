---
name: test-generator
description: Given an endpoint URL, method, response fields, generates a complete pytest test file with fixtures, parametrize, markers, positive and negative tests.
---

Generate a complete pytest test file for this endpoint specification:

$ARGUMENTS

Parse `$ARGUMENTS` as: `<METHOD> <endpoint-path> <field1,field2,...> [env=<name>]`

Examples of valid input:
- `GET /name/{country} name,capital,population,currencies,languages env=countries`
- `GET /forecast latitude,longitude,timezone,hourly env=weather`
- `GET /alpha/{code} name,cca2,cca3,region env=countries`

---

Before generating, read:
- `.claude/rules/framework-rules.md`
- `.claude/rules/testing-standards.md`
- `.claude/rules/code-style.md`
- `tests/test_countries.py` (reference implementation)
- `config/environments.yaml` (confirm the env key exists and read its `max_response_time` and `min_results_count`)

Derive `<resource>` from the primary noun in the endpoint path (e.g. `/name/{country}` → `name`, `/forecast` → `forecast`). Write the output to `tests/test_<resource>.py`. If the file already exists, extend it without removing existing tests.

---

## File structure to generate

### Imports (RULE-STY-004)
stdlib → third-party → local, blank-line separated. Always include `allure`, `pytest`, `Environment` and `resolve_environment` from `environment_config`. Add `json` and `pathlib.Path` if the test is parametrized.

### Module marker (RULE-ALL-001)
```python
pytestmark = allure.feature("<Human Name> API")
```

### Test data (if endpoint has path/query parameters that vary)
Create `test_data/<resource>_inputs.json` with at least 3 representative entries. Load at module scope:
```python
INPUTS = json.loads(
    (Path(__file__).parent.parent / "test_data" / "<resource>_inputs.json").read_text()
)
```

### Environment fixture (RULE-FIX-001, RULE-STY-003)
```python
@pytest.fixture(scope="module")
def environment(request: pytest.FixtureRequest) -> Environment:
    env_option = request.config.getoption("--env")
    if env_option and env_option != "<env-key>":
        pytest.skip(f"--env {env_option} selected; skipping <resource> tests")
    return resolve_environment("<env-key>")
```

### Positive tests

**Schema test** — `test_<resource>_schema` (RULE-SCHEMA-001)
Assert every field from the provided field list is present in `results[0]` (or the top-level response object for non-list responses). Use `@pytest.mark.parametrize` with `ids=` if the endpoint varies by input parameter.

**Result count test** — `test_<resource>_result_count` (RULE-COUNT-001)
Only for list-returning endpoints. Assert `len(results) > N` using `environment.min_results_count` or a conservative domain-known lower bound. Add an explanatory comment for any non-zero, non-one constant (RULE-STY-008).

**Domain range test** — `test_<resource>_<field>_in_valid_range` (RULE-DOMAIN-001)
Only if any field is a numeric domain value (temperature, coordinate, population, rate). Assert a closed interval with a comment explaining the bounds. Include a failure message listing out-of-range values (RULE-STY-007).

**Cross-endpoint consistency test** — `test_<resource>_appears_in_<collection>` (RULE-CROSS-001)
Only if both a narrow (single-entity) and a collection endpoint exist in the same environment. Fetch the entity and the collection; assert the entity is present by canonical identifier.

### Negative tests

**Not-found test** — `test_<resource>_not_found_returns_404`
Call the endpoint with an obviously invalid identifier. Assert latency → status 404. Do not assert body fields.

**Missing required param test** — `test_<resource>_missing_required_param_returns_4xx`
Only if the endpoint has required query parameters. Omit one. Assert `400 <= response.status_code < 500`.

---

## Assertion rules to apply throughout (RULE-ASS-001, RULE-STY-007, RULE-STY-008)
1. Latency: `assert response.elapsed.total_seconds() < environment.max_response_time`
2. Status: `assert response.status_code == <expected>`
3. Shape: `isinstance`, `len`, top-level key presence
4. Content: field values, domain ranges, cross-field relationships

Every `assert X in Y` and `assert all(...)` must include a failure message. Every domain-bound numeric literal must have an inline or preceding comment explaining its source.

---

After writing the file(s), run:
```
uv run pytest tests/test_<resource>.py -v
```
Report the results. Fix any failures before reporting complete.
