# Code Style Rules

**Version**: 1.0
**Last Updated**: 2026-06-04
**Owner**: Baechul Kim

---

## Overview

These rules govern **how Python code is written** in the `testgen-demo` test suite and its supporting modules: naming conventions, type annotations, import ordering, comment policy, assertion messaging, and where shared helpers and validators live. They apply to all files under `tests/`, `conftest.py`, and project-level modules such as `environment_config.py`.

Rules marked **REQUIRED** are non-negotiable; violations must be corrected before a PR is merged. Rules marked **RECOMMENDED** represent strong defaults; deviations require a comment explaining the exception.

Rules about what to test and how to structure tests live in `testing-standards.md`. Rules about framework wiring (fixture scopes, CI configuration, import boundaries between modules) live in `framework-rules.md`.

---

## Rules

### RULE-STY-001: Test files import only from the standard library, third-party packages, and `environment_config`

**Severity**: REQUIRED

**Rationale**: The only project-internal module test files should need is `environment_config`. If a test file imports from `main.py` or other application modules, it is testing implementation details rather than the public HTTP API, which defeats the purpose of integration tests and couples the test suite to internal structure that may change independently.

**Rule**: In this integration test suite, test files may import from: the Python standard library, installed packages (`allure`, `pytest`, `httpx`, `json`, `pathlib`, etc.), and `environment_config`. Imports from other application modules (`main`, etc.) are forbidden in test files.

**Good Example**:
```python
import json
from pathlib import Path

import allure
import pytest

from environment_config import resolve_environment
```

**Bad Example**:
```python
from main import build_url  # importing application logic into a test file
from environment_config import resolve_environment
```

**Exceptions**: None for integration tests. If unit tests for application logic are added in the future, a separate `tests/unit/` directory should be created with its own import rules.

---

### RULE-STY-002: No `print()` statements in test files

**Severity**: REQUIRED

**Rationale**: `print()` output is swallowed by pytest's capture by default and produces noisy output when `-s` is passed. Structured diagnostic information belongs in assertion failure messages or Allure attachments, not in ad hoc print calls that are invisible during normal runs and disruptive during debugging sessions.

**Rule**: Test files must not contain `print()` calls. Use `allure.attach()` for diagnostic data that must appear in the Allure report, or embed context directly in assertion failure messages using the `assert <expr>, "<message>"` form.

**Good Example**:
```python
assert germany_name in region_names, (
    f"{germany_name!r} not found in /region/europe response "
    f"({len(region_names)} countries returned)"
)
```

**Bad Example**:
```python
print(f"Germany name: {germany_name}")  # invisible in normal runs, noisy with -s
assert germany_name in region_names
```

**Exceptions**: None.

---

### RULE-STY-003: All fixture signatures must carry complete type annotations

**Severity**: REQUIRED

**Rationale**: `conftest.py` demonstrates the expected standard: `http_client(environment: Environment) -> Iterator[httpx.Client]`. Type annotations on fixtures serve two purposes: they make the dependency graph self-documenting (a reader immediately knows what type each injected argument provides), and they allow static analysis tools to catch mismatches between fixture return types and the parameter types of consuming tests.

**Rule**: Every fixture function must annotate all parameters and its return type. For generator fixtures that `yield`, the return type must be `Iterator[T]` or `Generator[T, None, None]`, not bare `T`. The `Environment` type must be imported from `environment_config`, not re-declared inline.

**Good Example**:
```python
from collections.abc import Iterator

import httpx

from environment_config import Environment


@pytest.fixture
def http_client(environment: Environment) -> Iterator[httpx.Client]:
    with httpx.Client(
        base_url=environment.base_url,
        timeout=environment.max_response_time,
    ) as client:
        yield client
```

**Bad Example**:
```python
@pytest.fixture
def http_client(environment):  # missing type annotations
    with httpx.Client(base_url=environment.base_url) as client:
        yield client
```

**Exceptions**: Module-level `environment` fixtures in test files accept `request: pytest.FixtureRequest` as their sole typed parameter; the return type is `Environment`.

---

### RULE-STY-004: Imports must follow stdlib → third-party → local ordering with blank-line separation

**Severity**: REQUIRED

**Rationale**: Consistent import ordering is a prerequisite for readable diffs and automated linting. The project's existing files (`test_weather.py`, `conftest.py`, `environment_config.py`) already follow the isort/ruff standard. Deviations introduce unnecessary noise in code review.

**Rule**: Imports must be grouped and ordered as follows, with exactly one blank line between groups:
1. `from __future__ import annotations` (if present, always first, alone in its group)
2. Standard library imports (`collections`, `dataclasses`, `json`, `pathlib`, `typing`, etc.)
3. Third-party package imports (`allure`, `httpx`, `pytest`, `yaml`, etc.)
4. Local project imports (`environment_config`, `tests/helpers/`, etc.)

Within each group, imports are sorted alphabetically. `from X import Y` and `import X` forms may coexist within a group; sort them together alphabetically by module name.

**Good Example**:
```python
from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest

from environment_config import resolve_environment
```

**Bad Example**:
```python
import pytest
import json
from environment_config import resolve_environment
import allure
from pathlib import Path
```

**Exceptions**: None. Configure `ruff` with `[tool.ruff.lint.isort]` to enforce this automatically.

---

### RULE-STY-005: `from __future__ import annotations` is required in files that annotate with `collections.abc` generics or forward references

**Severity**: REQUIRED

**Rationale**: Without `from __future__ import annotations`, using `collections.abc.Iterator` as a return-type annotation requires the type to be evaluated at runtime, which raises `TypeError` on Python 3.9 and below. The `from __future__ import annotations` import defers annotation evaluation, making the annotation a string and eliminating the runtime dependency. `conftest.py` and `environment_config.py` both already include this import.

**Rule**: Any file that uses `collections.abc.Iterator`, `collections.abc.Generator`, or any other generic from `collections.abc` as a type annotation must begin with `from __future__ import annotations`. Files that use only built-in generics (`list[T]`, `dict[K, V]`) or `typing` generics under a `TYPE_CHECKING` guard are exempt if the project's minimum Python version is 3.10 or higher.

**Good Example**:
```python
from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest


@pytest.fixture
def http_client(environment: Environment) -> Iterator[httpx.Client]:
    ...
```

**Bad Example**:
```python
from collections.abc import Iterator  # no __future__ import

@pytest.fixture
def http_client(environment: Environment) -> Iterator[httpx.Client]:
    ...
```

**Exceptions**: Files with no type annotations at all do not require this import.

---

### RULE-STY-006: Test function names follow `test_<subject>_<check>` or `test_<subject>_<condition>_<expected>` convention

**Severity**: REQUIRED

**Rationale**: A test function name is the first diagnostic signal when a test fails. `test_forecast` tells you nothing about what was verified; `test_forecast_schema` tells you a structural contract was checked; `test_forecast_temperature_in_valid_range` is unambiguous. The existing suite uses `_schema` and `_result_count` suffixes consistently. This rule codifies that pattern and extends it.

**Rule**: Test function names must follow one of these two patterns:
- `test_<subject>_<check>` — for tests that verify a single property. Examples: `test_germany_schema`, `test_region_europe_result_count`, `test_forecast_schema`.
- `test_<subject>_<condition>_<expected>` — for tests that verify behavior under a specific condition. Examples: `test_name_search_appears_in_region`, `test_forecast_missing_params_returns_400`.

The `<subject>` should name the endpoint, entity, or operation being tested. The `<check>` or `<expected>` must be specific enough that the test name alone communicates the failure when it appears in a report. Single-word suffixes like `test_germany` or `test_forecast` are forbidden.

**Good Example**:
```python
def test_germany_schema(http_client, environment): ...
def test_region_europe_result_count(http_client, environment): ...
def test_name_search_appears_in_region(http_client, environment): ...
```

**Bad Example**:
```python
def test_germany(http_client, environment): ...       # too vague
def test_weather(http_client, environment, city): ... # too vague
def test_it(http_client, environment): ...            # meaningless
```

**Exceptions**: None.

---

### RULE-STY-007: Non-obvious assertion failures must include an explanatory message

**Severity**: RECOMMENDED

**Rationale**: pytest rewrites bare `assert` statements and provides diff output for equality checks, but for membership tests (`in`), range checks, and `all(...)` expressions the default failure output is just the boolean result. An assertion message with relevant runtime values dramatically reduces the time needed to diagnose a failure from a CI log.

**Rule**: Any `assert` expression that does not produce a self-explanatory diff on failure must include a second argument: a descriptive string that names what was expected and includes the key runtime values. Required for: membership tests (`in`, `not in`), `all(...)` / `any(...)` expressions, and multi-condition boolean expressions. Equality and `isinstance` assertions where pytest's diff is sufficient are exempt.

**Good Example**:
```python
assert germany_name in region_names, (
    f"{germany_name!r} not found in /region/europe response "
    f"({len(region_names)} countries returned)"
)

assert all(-80 <= t <= 60 for t in temperatures), (
    f"Temperature out of range [-80, 60]: {[t for t in temperatures if not (-80 <= t <= 60)]}"
)
```

**Bad Example**:
```python
assert germany_name in region_names          # failure only shows: AssertionError
assert all(-80 <= t <= 60 for t in temps)   # no indication of which value failed
```

**Exceptions**: Assertions in schema tests that check key presence (`assert "name" in country`) are self-explanatory due to the key name and are exempt from the message requirement.

---

### RULE-STY-008: Domain-bound constants in test assertions must carry an explanatory comment

**Severity**: REQUIRED

**Rationale**: A raw number in an assertion like `assert all(-80 <= t <= 60 ...)` or `assert len(results) > 40` is opaque without context. A reader maintaining the test cannot tell whether the bound is a regulatory limit, a physical constant, a business SLA, or an arbitrary choice. A one-line comment on the same line or the line immediately above eliminates this ambiguity and makes the bound defensible in code review.

**Rule**: Any numeric literal used as a domain bound in an assertion — range limits, minimum counts, thresholds — must be accompanied by an inline or preceding comment that states the source or rationale for the value. Constants that are universally understood (`0`, `1`, `100`, `200`, `404`) are exempt.

**Good Example**:
```python
# -80°C (Antarctic record low) to 60°C (documented surface maximum)
assert all(-80 <= t <= 60 for t in temperatures)

assert len(results) > 40  # Europe has >40 sovereign states; conservative lower bound
```

**Bad Example**:
```python
assert all(-80 <= t <= 60 for t in temperatures)  # where do -80 and 60 come from?
assert len(results) > 40                           # why 40?
```

**Exceptions**: HTTP status codes (`200`, `404`, `500`) and zero/one sentinel values do not require comments.

---

### RULE-STY-009: Shared validator functions live in `conftest.py` or `tests/helpers/`; never duplicated across test files

**Severity**: REQUIRED

**Rationale**: If both `test_countries.py` and `test_weather.py` need to assert response-time compliance using the same expression, that expression should live in one place. Duplication means that when the assertion pattern changes (e.g., a new format for the failure message), all copies must be updated in lockstep. Missed updates produce inconsistent failure output across the test suite.

**Rule**: Any assertion helper, validator function, or data-transformation utility used by more than one test file must be placed in `conftest.py` (if it is a fixture or pytest hook) or in a dedicated `tests/helpers/` module (if it is a plain function). Test files must not copy-paste the same multi-line logic block.

**Good Example**:
```python
# conftest.py — shared fixture available to all test files
@pytest.fixture
def http_client(environment: Environment) -> Iterator[httpx.Client]:
    with httpx.Client(
        base_url=environment.base_url,
        timeout=environment.max_response_time,
    ) as client:
        yield client
```

```python
# tests/helpers/assertions.py — shared validator
def assert_response_time(response: httpx.Response, max_seconds: float) -> None:
    elapsed = response.elapsed.total_seconds()
    assert elapsed < max_seconds, (
        f"Response time {elapsed:.3f}s exceeded limit {max_seconds}s"
    )
```

**Bad Example**:
```python
# test_countries.py
def _check_response_time(response, max_time):
    assert response.elapsed.total_seconds() < max_time

# test_weather.py — identical copy
def _check_response_time(response, max_time):
    assert response.elapsed.total_seconds() < max_time
```

**Exceptions**: Single-use helpers that are specific to one test file may remain in that file. Move them only when a second file needs the same logic.
