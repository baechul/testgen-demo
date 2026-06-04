# testgen-demo

Integration test suite for public REST APIs, with Allure reporting.

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

## Interpreting results

The report's **Behaviors** tab has two sections — **Countries API** and **Weather API** — one per environment.

Each test enforces:

- **Status 200** — the endpoint responded successfully.
- **Response time** — must be under the `max_response_time` threshold defined in `config/environments.yaml`. No value is hardcoded in test code.
- **Schema** — required fields are present in the response body.
- **Data integrity** — e.g. temperature values fall within the physically plausible range of −80 °C to 60 °C.

## Design decisions

**Per-environment fixtures in each test file** — each test file owns a module-scoped `environment` fixture that always resolves its own environment. When `--env` is passed it skips mismatched suites; when omitted both suites run. This avoids a global session fixture that requires `--env` to be present.

**Thresholds in config, not in tests** — `config/environments.yaml` is the single source of truth for `max_response_time` and `min_results_count`. Tests read these values from the `environment` fixture so changing a threshold never requires touching test code.

**Cities loaded from `test_data/cities.json`** — parametrized weather tests read city coordinates from a JSON fixture file rather than embedding them in the test. Adding or removing a city requires no code change.

**`allure.feature` as `pytestmark`** — applying the Allure feature marker at module level keeps individual tests free of decorator boilerplate while still producing separate sections in the report.
