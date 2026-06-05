---
name: validator-generator
description: >
  Generates a typed Python validator class from a JSON response sample. Use this skill
  whenever the user provides a JSON blob or API response and wants to validate its shape
  in tests — even if they say "schema check", "type check", "validate this response",
  "generate a validator", or "make sure this API response has the right fields". Also
  trigger when a test file has many manual `assert "field" in data` checks that could
  be replaced with a reusable validator. The skill produces a zero-dependency Python
  class saved to src/validators/ that can be dropped directly into pytest assertions.
---

## What this skill produces

A Python file in `src/validators/` containing one or more validator classes — one per
JSON object level. Each class has:
- `REQUIRED_FIELDS` — maps field name → expected Python type
- `OPTIONAL_FIELDS` — maps field name → expected Python type (may be missing or null)
- `validate(data: dict) -> list[str]` — returns a list of human-readable error strings; empty list means valid
- `assert_valid(data: dict) -> None` — calls validate() and raises AssertionError with all errors joined if any fail

Nested JSON objects get their own validator class (e.g., a `name` field that is a dict
generates a `NameValidator`), and the parent's `validate()` delegates to it automatically.

## Usage in tests

```python
from validators.country_validator import CountryValidator

def test_germany_schema(http_client, environment):
    response = http_client.get("/name/germany")
    assert response.status_code == 200
    country = response.json()[0]
    CountryValidator.assert_valid(country)
```

## Step-by-step process

### 1. Gather the JSON and context

The user will provide one of:
- A JSON blob pasted inline
- A file path to a `.json` file — read it with the Read tool
- An API endpoint — fetch a live sample with httpx or curl if needed

Also ask (or infer from context):
- **Validator name**: what should the class be called? Default: derive from the endpoint
  or outermost key (e.g., `/name/germany` → `CountryValidator`, `forecast` → `ForecastValidator`)
- **Output filename**: snake_case version of the class name (e.g., `country_validator.py`)
- **Nested depth**: do you want nested objects validated recursively, or just top-level?
  Default: yes, recurse one level for dicts that contain more than 2 keys; skip trivial
  leaf dicts

If the JSON is a list, validate `data[0]` as the canonical record shape and note this
in a comment.

### 2. Analyze the JSON structure

Walk every key in the JSON object and infer:

| JSON value type | Python type annotation | Notes |
|---|---|---|
| `"string"` | `str` | |
| `42` or `42.0` | `int` or `float` | prefer `int` if no decimal |
| `true` / `false` | `bool` | |
| `[...]` | `list` | |
| `{...}` | `dict` | → also recurse if substantial |
| `null` | mark as **optional** | can't infer type; note in comment |

Fields whose value is `null` cannot have their type inferred from a single example —
mark them as optional with a `# type unknown, inferred as optional from null value`
comment and use `object` as a placeholder type (meaning "present but type unverified").

### 3. Generate the validator file

Produce a single `.py` file. Structure it like this:

```python
from __future__ import annotations

# Generated validator for <source description>
# Fields marked optional were null in the sample response — verify if they can truly be absent.


class NameValidator:
    REQUIRED_FIELDS: dict[str, type] = {
        "common": str,
        "official": str,
    }
    OPTIONAL_FIELDS: dict[str, type] = {}

    @classmethod
    def validate(cls, data: dict) -> list[str]:
        errors: list[str] = []
        for field, expected_type in cls.REQUIRED_FIELDS.items():
            if field not in data:
                errors.append(f"Missing required field: {field!r}")
            elif not isinstance(data[field], expected_type):
                actual = type(data[field]).__name__
                errors.append(f"Field {field!r}: expected {expected_type.__name__}, got {actual}")
        for field, expected_type in cls.OPTIONAL_FIELDS.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    actual = type(data[field]).__name__
                    errors.append(f"Field {field!r}: expected {expected_type.__name__}, got {actual}")
        return errors

    @classmethod
    def assert_valid(cls, data: dict) -> None:
        errors = cls.validate(data)
        assert not errors, "Validation failed:\n" + "\n".join(f"  - {e}" for e in errors)


class CountryValidator:
    REQUIRED_FIELDS: dict[str, type] = {
        "name": dict,
        "capital": list,
        "population": int,
        "currencies": dict,
        "languages": dict,
    }
    OPTIONAL_FIELDS: dict[str, type] = {
        "area": float,  # type unknown, inferred as optional from null value
    }

    @classmethod
    def validate(cls, data: dict) -> list[str]:
        errors: list[str] = []
        for field, expected_type in cls.REQUIRED_FIELDS.items():
            if field not in data:
                errors.append(f"Missing required field: {field!r}")
            elif not isinstance(data[field], expected_type):
                actual = type(data[field]).__name__
                errors.append(f"Field {field!r}: expected {expected_type.__name__}, got {actual}")
        for field, expected_type in cls.OPTIONAL_FIELDS.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    actual = type(data[field]).__name__
                    errors.append(f"Field {field!r}: expected {expected_type.__name__}, got {actual}")
        # Nested validation
        if "name" in data and isinstance(data["name"], dict):
            errors.extend(f"name.{e}" for e in NameValidator.validate(data["name"]))
        return errors

    @classmethod
    def assert_valid(cls, data: dict) -> None:
        errors = cls.validate(data)
        assert not errors, "Validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
```

**Ordering**: define nested validator classes before the parent that references them.

**Nesting heuristic**: recurse into a dict field if it has ≥ 2 keys in the sample.
Single-key dicts or trivially small ones can be left as `dict` with no dedicated
validator class — use your judgment based on whether the sub-structure matters for
test assertions.

### 4. Handle edge cases

- **List of objects** (`"tags": [{"id": 1, "name": "foo"}]`): generate a `TagValidator`
  for the element shape and add a note in the parent's validate() that per-element
  validation is available but not called by default (to keep validate() fast).
- **Mixed-type lists** (`[1, "two", null]`): type the field as `list` with no element
  validation; add a comment describing the observed types.
- **Very deep nesting** (3+ levels): validate up to 2 levels deep by default; add a
  comment suggesting the user can extend further if needed.
- **Already has a validator**: check if `src/validators/<filename>.py` exists before
  writing. If it does, ask the user whether to overwrite or create a new version
  (e.g., `country_v2_validator.py`).

### 5. Save the file

Write to `src/validators/<filename>.py`. If the `src/validators/` directory doesn't
exist, create it first.

Also check if `src/validators/__init__.py` exists; if not, create an empty one so
the package is importable.

### 6. Confirm and show usage

After saving, tell the user:
1. The full path to the generated file
2. A one-liner showing how to import and use it in a test
3. Which fields were marked optional (and why) so the user can review them

If any fields had `null` values (type unknown), prompt the user: "These fields were
null in your sample — do you know their expected types? I can update the validator."
