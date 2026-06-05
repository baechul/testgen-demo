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

`config/environments.yaml` → `src/utils/environment_config.py` (`resolve_environment(name) -> Environment`) → per-test-file `environment` fixture → `http_client` fixture (in `conftest.py`).

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

`CLAUDE_LOG.md` in the project root is the single source of truth for what changed and why. It must be kept current — a future session should be able to read it and understand exactly where things stand.

### When to log

Append an entry **before** concluding any of the following — no exceptions:
- A completed feature, bug fix, or refactor touching repository files
- A skill created, modified, or deleted under `.claude/skills/`
- An agent task (e.g. `/testgen`, `/testgen`, `/test-generator`, `/validator-generator`) that produces or modifies files in the repository
- Any multi-step work block, even if interrupted mid-way

Ephemeral work that leaves no repository artifacts (pure Q&A, read-only research, failed runs that were rolled back) does not require an entry.

### Entry format

Entries are reverse-chronological (newest at top). Each entry covers one logical work block:

```markdown
## YYYY-MM-DD — <one-line description of what was done>

**Objective:** What was the goal.

**Duration:** How long the task took to complete (e.g. `~15 min`, `~2 h`).

**Actions Taken:**
- `path/to/file` — what changed and why (created / modified / deleted)

**Obstacles & Solutions:** What failed, why, and how it was resolved. Omit if nothing went wrong.

**Next Steps:** Concrete, prioritized follow-up tasks for the next session. Omit if none.
```

### Scope: repository-level changes only

Log changes to files that are checked into (or intended to be checked into) the repository:
- Source files: `src/`, `tests/`, `conftest.py`, `config/`, `test_data/`
- Project instructions and skills: `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `.claude/agents/`
- CI and tooling: `.github/`, `pyproject.toml`, `Makefile`

Do **not** log: eval workspaces, scratch files, generated Allure artifacts, or anything in `.gitignore`.

