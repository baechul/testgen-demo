# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common commands

```bash
# Run all tests (both environments)
uv run pytest tests

# Run one environment only
uv run pytest tests --env countries
uv run pytest tests --env weather

# Run a single test by node ID
uv run pytest tests/test_countries.py::test_germany_schema

# Generate Allure report and open in browser
make report-open

# Stop the Allure report server
make report-stop

# Generate report without opening
make report
```

## Architecture

This is an **integration test suite** for two public REST APIs:

| Environment key | API | Base URL |
|---|---|---|
| `countries` | REST Countries v3.1 | https://restcountries.com/v3.1 |
| `weather` | Open-Meteo | https://api.open-meteo.com/v1 |

### Configuration flow

`config/environments.yaml` → `environment_config.py` (`resolve_environment(name) -> Environment`) → per-test-file `environment` fixture → `http_client` fixture (in `conftest.py`).

All environment-specific values (`base_url`, `max_response_time`, `min_results_count`) live exclusively in `config/environments.yaml`. Test code reads them only through the `Environment` dataclass — never hardcoded.

### Fixture ownership

- `conftest.py` owns two things only: the `--env` CLI option and the `http_client` fixture. It has no `environment` fixture.
- Each test file (`test_countries.py`, `test_weather.py`) owns its own module-scoped `environment` fixture. This fixture always resolves its own environment name and skips if `--env` targets a different environment.
- When `--env` is omitted, all test files run against their respective APIs.

### Test data

Parametrized inputs live in `test_data/` (e.g., `test_data/cities.json`). Test files load them at module scope via `Path(__file__).parent.parent / "test_data" / "<file>"`. Never inline structured test data in parametrize decorators.

### Reporting

`allure-pytest` collects raw results during `pytest` runs. The Allure CLI (`allure generate`) produces the HTML report. Each test module declares `pytestmark = allure.feature("<Name> API")` to create a separate section per environment in the Behaviors tab. Generated artifacts (`allure-results/`, `allure-report/`, `test-results.xml`) are gitignored.

### CI

`.github/workflows/ci.yml` runs on every push. It runs the full suite with `--alluredir` and `--junit-xml`, then a Python inline script parses the JUnit XML to enforce `PASS_RATE_THRESHOLD` (default 100%). The Allure HTML report is uploaded as a 30-day artifact.

## Architecture rules

Three rule files in `.claude/rules/` govern this codebase. Read them before making changes:

- `framework-rules.md` — structural constraints: fixture scoping, import boundaries, config loading, CI wiring
- `testing-standards.md` — what and how to test: assertion ordering, schema coverage, parametrization, cross-endpoint consistency
- `code-style.md` — Python style: type hints on fixtures, import ordering, naming conventions, assertion failure messages, domain-bound constant comments

## Session Logging Protocol
- Maintain a file named `CLAUDE_LOG.md` in the project root to preserve progress state across sessions.
- If `CLAUDE_LOG.md` does not exist, create it immediately upon your first task.
- **Mandatory Action:** Before marking any major task as complete, concluding a feature, or ending a continuous work block, append a new timestamped entry to `CLAUDE_LOG.md`.
- Each entry must explicitly detail:
  1. **Date & Objective:** The target goal of the current session.
  2. **Actions Taken:** Specific files created, modified, or deleted.
  3. **Obstacles & Solutions:** What failed, why it failed, and how you fixed it.
  4. **Next Steps:** The exact, prioritized tasks that need to be tackled in the next session.
- Keep the log concise, reverse-chronological (newest entries at the top), and focused purely on technical execution.

