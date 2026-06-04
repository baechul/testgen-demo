# Test Framework Architecture Rules

**Version**: 2.0
**Last Updated**: 2026-06-04
**Owner**: Baechul Kim

---

## Overview

These rules govern the **structural architecture** of the `testgen-demo` integration test suite: how the framework is wired together, how environment configuration is loaded, how fixtures are scoped and composed, how the `--env` selector works, and how CI is structured. They are not concerned with how individual tests are written (those conventions live in `testing-standards.md`) or with how Python code is styled (those conventions live in `code-style.md`).

Rules marked **REQUIRED** are non-negotiable; violations must be corrected before a PR is merged.

---

## Rules

### RULE-CFG-001: All environment configuration lives in `config/environments.yaml`

**Severity**: REQUIRED

**Rationale**: Centralizing environment parameters (base URLs, timeouts, result thresholds) in a single YAML file means that changing a target endpoint or SLA threshold requires touching exactly one file, not hunting through test modules. It also makes CI-environment promotion safe because no test code changes are needed.

**Rule**: Every value that is specific to a deployment environment — `base_url`, `max_response_time`, `min_results_count`, or any future per-environment setting — must be stored as a named entry in `config/environments.yaml`. Test files must never declare these values as literals or module-level constants.

**Good Example**:
```yaml
# config/environments.yaml
countries:
  base_url: https://restcountries.com/v3.1
  max_response_time: 2.0
  min_results_count: 1
```
```python
# test file — reads config, never redeclares it
def test_something(http_client, environment):
    assert len(results) >= environment.min_results_count
```

**Bad Example**:
```python
# test file — hardcoded values
BASE_URL = "https://restcountries.com/v3.1"
MAX_RESPONSE_TIME = 2.0

def test_something(http_client):
    assert response.elapsed.total_seconds() < 2.0
```

**Exceptions**: None.

---

### RULE-CFG-002: `environment_config.py` is the sole loader of `config/environments.yaml`

**Severity**: REQUIRED

**Rationale**: `environment_config.py` owns the schema contract for the YAML file: it validates required keys, coerces types, and raises clear errors on misconfiguration. Bypassing it by calling `yaml.safe_load` directly in test code circumvents that validation and duplicates parsing logic.

**Rule**: Test files and fixtures must use `resolve_environment(name)` from `environment_config` to obtain an `Environment` dataclass. Direct `yaml` parsing in test modules is forbidden.

**Good Example**:
```python
from utils.environment_config import resolve_environment

@pytest.fixture(scope="module")
def environment(request):
    return resolve_environment("countries")
```

**Bad Example**:
```python
import yaml

@pytest.fixture(scope="module")
def environment():
    with open("config/environments.yaml") as f:
        return yaml.safe_load(f)["countries"]
```

**Exceptions**: None. The only legitimate direct consumer of `config/environments.yaml` is `environment_config.py` itself.

---

### RULE-ISO-001: Test files must not import from other test files

**Severity**: REQUIRED

**Rationale**: Cross-test-file imports create hidden coupling. A change to `test_countries.py` can silently break `test_weather.py` if there is a shared import between them. Isolation ensures that each test module can be run, refactored, or deleted independently.

**Rule**: No file under `tests/` may import from another file under `tests/`. Shared fixtures belong in `conftest.py`. Shared test-data helpers belong in a dedicated `tests/helpers/` module that contains no test functions.

**Good Example**:
```python
# conftest.py — shared fixture available to all test files
@pytest.fixture
def http_client(environment):
    ...
```

**Bad Example**:
```python
# tests/test_weather.py
from tests.test_countries import environment  # forbidden cross-test import
```

**Exceptions**: None.

---

### RULE-FIX-001: Each test file owns its own `environment` fixture

**Severity**: REQUIRED

**Rationale**: Different test modules target different APIs (`countries`, `weather`, etc.). The `environment` fixture is module-specific because it calls `resolve_environment` with a hardcoded environment name and handles `--env` skip logic for that specific service. A shared `environment` fixture would collapse the distinction between services and make `--env` filtering impossible to implement correctly.

**Rule**: Every test file that issues HTTP requests must define its own `environment` fixture at `scope="module"`. This fixture must call `resolve_environment("<service-name>")` and implement `--env` filtering via `pytest.skip` when the active `--env` option does not match this service. The fixture must not be defined in `conftest.py`.

**Good Example**:
```python
# tests/test_countries.py
@pytest.fixture(scope="module")
def environment(request):
    env_option = request.config.getoption("--env")
    if env_option and env_option != "countries":
        pytest.skip(f"--env {env_option} selected; skipping countries tests")
    return resolve_environment("countries")
```

**Bad Example**:
```python
# conftest.py — wrong: merges all environments into a single fixture
@pytest.fixture(scope="module", params=["countries", "weather"])
def environment(request):
    return resolve_environment(request.param)
```

**Exceptions**: None. The `http_client` fixture lives in `conftest.py` because it is environment-agnostic; `environment` does not.

---

### RULE-FIX-002: Module-scoped fixtures for expensive per-file setup; function scope for state

**Severity**: RECOMMENDED

**Rationale**: Both `environment` fixtures use `scope="module"`. This is appropriate because resolving an environment reads and parses YAML once per test file rather than once per test function. Fixtures that hold mutable state or produce side effects must use `scope="function"` to prevent cross-test contamination.

**Rule**: The `environment` fixture must remain `scope="module"`. Any fixture that accumulates or mutates state (e.g., a database connection, a counter, a list that gets appended to) must use `scope="function"`. Justify any fixture with `scope="session"` with a comment explaining why session scope is safe.

**Exceptions**: Read-only, immutable fixtures (like `Environment` dataclasses) are safe at `module` or `session` scope.

---

### RULE-HTTP-002: `http_client` is constructed in `conftest.py` with timeout from `environment`

**Severity**: REQUIRED

**Rationale**: The `http_client` fixture in `conftest.py` already sets `timeout=environment.max_response_time` on the underlying `httpx.Client`. This means the client will raise a timeout exception if the server exceeds the SLA — a second line of defense on top of the response-time assertion convention in `testing-standards.md`. This configuration must not be altered or bypassed by constructing a new client inline.

**Rule**: Tests must use the injected `http_client` fixture. Creating an `httpx.Client` directly inside a test function or test-scoped fixture is forbidden.

**Good Example**:
```python
def test_forecast(http_client, environment, city):
    response = http_client.get("/forecast", params={...})
```

**Bad Example**:
```python
def test_forecast(environment, city):
    with httpx.Client(base_url=environment.base_url) as client:  # bypasses conftest
        response = client.get("/forecast", params={...})
```

**Exceptions**: None.

---

### RULE-ALL-002: Allure report artifacts must remain gitignored

**Severity**: REQUIRED

**Rationale**: `allure-results/` and `allure-report/` are generated at runtime during CI. They can be hundreds of megabytes per run. Committing them pollutes the repository, inflates clone times, and creates meaningless diffs. The canonical location for these artifacts is the GitHub Actions artifact store (retention: 30 days per the workflow definition).

**Rule**: The entries `allure-results/` and `allure-report/` must always be present in `.gitignore`. They must never be committed to the repository. `test-results.xml` (JUnit output) is similarly generated and must also remain gitignored or excluded from commits.

**Exceptions**: None. If an Allure report needs to be shared, reference the GitHub Actions artifact URL, not a committed file.

---

### RULE-CI-001: The pass-rate quality gate threshold lives in the CI workflow, not in test code

**Severity**: REQUIRED

**Rationale**: The pass-rate threshold (`PASS_RATE_THRESHOLD`) is an operational policy — it belongs to the CI pipeline, not to the test suite. Hardcoding it in test files would mean a policy change requires modifying test code, which conflates test logic with deployment decisions and bypasses normal review channels for pipeline configuration.

**Rule**: The numeric pass-rate threshold must be defined exclusively as the `PASS_RATE_THRESHOLD` environment variable in `.github/workflows/ci.yml`. The quality gate script reads this variable from the environment. Test files must contain no reference to a pass-rate threshold value.

**Good Example** (in `ci.yml`):
```yaml
env:
  PASS_RATE_THRESHOLD: "100"
```

**Bad Example** (in test code):
```python
PASS_RATE_THRESHOLD = 100  # threshold must not live here
```

**Exceptions**: None.

---

### RULE-CI-002: pytest is invoked only from the CI workflow; test code must not shell out to pytest

**Severity**: REQUIRED

**Rationale**: The workflow step `uv run pytest tests --alluredir=allure-results --junit-xml=test-results.xml -v` is the single source of truth for how the test suite is executed. Arguments like `--alluredir` and `--junit-xml` must remain workflow-controlled so artifact paths stay consistent with the upload step that follows.

**Rule**: pytest invocation options (`--alluredir`, `--junit-xml`, `-v`, `--env`) are specified in the CI workflow step, not hardcoded in `pyproject.toml` `addopts` or in test code. `pyproject.toml` `[tool.pytest.ini_options]` is limited to structural settings: `testpaths`, `pythonpath`.

**Exceptions**: Developers may pass arbitrary options locally on the command line. Only persistent `addopts` entries are restricted.

---

### RULE-SCOPE-001: `--env` CLI option is the only mechanism for restricting test scope at runtime

**Severity**: REQUIRED

**Rationale**: The `--env` option is registered in `conftest.py` and consumed by each module's `environment` fixture. It is the single, documented mechanism for running tests against one service in isolation. Ad hoc scope restriction mechanisms (`-k` expressions baked into shell scripts, environment variables read directly in test bodies, etc.) fragment that interface.

**Rule**: To restrict test execution to a single service, pass `--env <name>` on the pytest command line. Do not introduce alternative scope-restriction mechanisms that bypass the `environment` fixture's skip logic.

**Good Example**:
```bash
uv run pytest tests --env countries
```

**Bad Example**:
```bash
uv run pytest tests/test_countries.py  # works but bypasses the --env contract
```
```python
# test body reads an env var directly instead of using the fixture
import os
if os.getenv("RUN_COUNTRIES") != "1":
    pytest.skip("set RUN_COUNTRIES=1 to run")
```

**Exceptions**: Running a single test by node ID (`pytest tests/test_countries.py::test_germany_schema`) is permitted during local debugging.
