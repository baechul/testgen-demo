# testgen-demo

Integration test suite for public REST APIs, with Allure reporting and Claude Code automation for test generation.

## APIs under test

| Environment | Base URL |
|---|---|
| `countries` | https://restcountries.com/v3.1 |
| `weather` | https://api.open-meteo.com/v1 |

## Setup

**Prerequisites**

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- [Allure CLI](https://allure.qatools.ru/) — for HTML reports only (`brew install allure`)

**Install dependencies**

```bash
uv sync --group dev
```

## Running tests

Run both environments:

```bash
uv run pytest tests
```

Run a single environment:

```bash
uv run pytest --env countries tests
uv run pytest --env weather tests
```

Run a single test by node ID:

```bash
uv run pytest tests/test_countries.py::test_germany_schema
```

## Allure report

Generate and open the report in a browser:

```bash
make report-open
```

Stop the report server:

```bash
make report-stop
```

`make report` generates the HTML without opening the browser.

## Test coverage

30 tests across 4 files (as of last update):

| File | Endpoints | Tests |
|---|---|---|
| `tests/test_countries.py` | `/name/{name}`, `/region/{region}` | schema, result count, cross-endpoint consistency, Americas area/population domain checks |
| `tests/test_currency.py` | `/currency/{code}` | schema, result count, timezone format, languages/region presence, cross-endpoint consistency, 404 negative path |
| `tests/test_lang.py` | `/lang/{code}` | parametrized schema + result count (Korean, Spanish, French, Japanese), cross-endpoint region consistency, 404 negative path |
| `tests/test_weather.py` | `/forecast` | parametrized schema across 5 cities (Seoul, Tokyo, Berlin, New York, São Paulo) |

## Project layout

```
config/
  environments.yaml       # base_url, max_response_time, min_results_count per env
src/
  utils/
    environment_config.py # resolve_environment(name) → Environment dataclass
  validators/
    base_validator.py     # BaseValidator with REQUIRED_FIELDS / OPTIONAL_FIELDS / assert_valid()
    country_validator.py  # CountryValidator + NameValidator (countries, lang, region endpoints)
    currency_validator.py # CurrencyCountryValidator (currency endpoint — region/timezones required)
    forecast_validator.py # ForecastValidator + HourlyValidator (weather forecast endpoint)
test_data/
  cities.json             # parametrize inputs for weather tests
  lang_inputs.json        # parametrize inputs for lang tests
tests/
  test_countries.py
  test_currency.py
  test_lang.py
  test_weather.py
docs/
  test-specs/
    test-spec-countries.md  # living spec: scenarios, implementation status, coverage gaps
    test-spec-weather.md
conftest.py               # --env CLI option + http_client fixture
```

## Validators

`src/validators/` contains typed validator classes that replace verbose `assert "field" in data` / `isinstance` chains in tests. Each class exposes:

- `REQUIRED_FIELDS` — field name → expected Python type; fails if missing or wrong type
- `OPTIONAL_FIELDS` — same but skipped if the field is absent or `null`
- `validate(data) -> list[str]` — returns all errors; empty list means valid
- `assert_valid(data) -> None` — raises `AssertionError` with all errors if any fail

All validators extend `BaseValidator`. Nested object fields get their own validator class (e.g., `NameValidator` for `country.name`).

Usage in a test:

```python
from validators.currency_validator import CurrencyCountryValidator

def test_currency_usd_schema(http_client, environment):
    response = http_client.get("/currency/USD")
    assert response.elapsed.total_seconds() < environment.max_response_time
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list) and len(results) > 0
    CurrencyCountryValidator.assert_valid(results[0])
```

## Claude Code automation

This project uses Claude Code agents and skills to generate, verify, and document tests.

### Agents (`.claude/agents/`)

| Agent | Trigger | What it does |
|---|---|---|
| `testgen` | `@testgen` | Generates a complete test file for a given endpoint, then delegates to `testrun` |
| `testrun` | `@testrun` | Executes pytest, analyzes failures, reports pass/fail |
| `testqa` | `@testqa` | Syncs `docs/test-specs/` with actual test implementations; reports drift and gaps |

### Skills (`.claude/skills/`)

| Skill | Trigger | What it does |
|---|---|---|
| `test-generator` | `/test-generator` | Generates a pytest test file from an endpoint spec (URL, method, response fields) |
| `validator-generator` | `/validator-generator` | Generates a typed validator class from a live API response or JSON sample |

### Rules (`.claude/rules/`)

Three rule files govern the codebase and are enforced during code generation:

- `framework-rules.md` — fixture scoping, config loading, CI wiring, `--env` selector
- `testing-standards.md` — assertion ordering, schema coverage, parametrization, cross-endpoint consistency
- `code-style.md` — type annotations, import ordering, naming conventions, assertion messages

## Interpreting results

### Terminal output

pytest prints one line per test. Each line ends with `PASSED`, `FAILED`, `ERROR`, or `SKIPPED`.

- `FAILED` — the assertion fired; the failure message is printed immediately below the test name. Validator failures list every broken field at once:
  ```
  AssertionError: Validation failed:
    - Missing required field: 'capital'
    - Field 'population': expected int, got str
  ```
- `SKIPPED` — the test's environment was excluded by `--env`. Skips do not count against the pass rate.
- `ERROR` — a fixture or setup step raised an exception before the test body ran (e.g. network unreachable, YAML misconfigured).

### Test name conventions

Test names follow `test_<subject>_<check>` or `test_<subject>_<condition>_<expected>` (RULE-STY-006), so the name alone identifies the failure layer:

| Suffix / pattern | What it checks |
|---|---|
| `_schema` | All required fields are present and correctly typed |
| `_result_count` | Collection endpoint returns at least the expected minimum |
| `_appears_in_region` | Cross-endpoint consistency — entity from narrow endpoint is in collection |
| `_returns_404` | Negative path — invalid input produces the correct error status |
| `_in_valid_range` | Domain constraint — numeric field is within its physical/business bounds |

### Allure report

After `make report-open`, the **Behaviors** tab groups tests by API (`Countries API`, `Weather API`). Expand a failing feature to see the individual test, its parameters (for parametrized cases), and the full assertion message.

The **Timeline** tab shows wall-clock execution order — useful for spotting intermittent latency failures where response time exceeded `max_response_time`.

### CI quality gate

The GitHub Actions workflow enforces `PASS_RATE_THRESHOLD=100`. The gate computes:

```
pass rate = passed / (total - skipped) * 100
```

If the rate falls below the threshold, the `Quality gate` step exits non-zero and the job fails. The full breakdown (`total`, `passed`, `failed`, `skipped`, `pass rate`) is printed to the step log and written to the GitHub job summary.

---

## Design decisions

**Per-environment fixtures in each test file** — each test file owns a module-scoped `environment` fixture that resolves its own environment name and skips if `--env` targets a different one. When `--env` is omitted, all files run.

**Thresholds in config, not in tests** — `config/environments.yaml` is the single source of truth for `max_response_time` and `min_results_count`. Changing a threshold never requires touching test code.

**Response-time assertion first** — every test asserts `elapsed < environment.max_response_time` immediately after the HTTP call, before status code or body checks. Performance regressions are surfaced at the same level as functional failures.

**Test data in `test_data/`** — parametrized tests load structured inputs (cities, languages) from JSON files at module scope. Adding a case requires no code change.

**Typed validators over inline assertions** — `src/validators/` classes consolidate field-presence and type checks. A single `Validator.assert_valid(record)` replaces a block of `assert "field" in data` lines and produces a unified failure message listing all errors at once.
