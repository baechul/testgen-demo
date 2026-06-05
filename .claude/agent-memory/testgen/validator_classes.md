---
name: validator-classes
description: Validator classes in src/validators/ — what they cover and how to use them in tests
metadata:
  type: project
---

All validators extend `BaseValidator` from `src/validators/base_validator.py`.

## BaseValidator (src/validators/base_validator.py)
- `REQUIRED_FIELDS: dict[str, type]` — fields that must be present and type-match
- `OPTIONAL_FIELDS: dict[str, type]` — fields checked only when present and non-null
- `validate(data) -> list[str]` — returns list of error strings (empty = valid)
- `assert_valid(data) -> None` — asserts validate() returns empty list; raises AssertionError with all errors listed
- `_validate_nested(data) -> list[str]` — hook for subclasses; default returns []

## CountryValidator (src/validators/country_validator.py)
Covers: /name/{name}, /region/{region}, /lang/{code}, /currency/{code}
- REQUIRED: name (dict), capital (list), population (int), currencies (dict), languages (dict)
- OPTIONAL: region (str), subregion (object), area (float), landlocked (bool), flag (str)
- _validate_nested: delegates name dict to NameValidator

## NameValidator (src/validators/country_validator.py)
Sub-validator for the `name` dict inside a country object.
- REQUIRED: common (str), official (str)

## ForecastValidator (src/validators/forecast_validator.py)
Covers: /forecast
- REQUIRED: timezone (str), hourly (dict)
- OPTIONAL: latitude (float), longitude (float), elevation (float), utc_offset_seconds (int), timezone_abbreviation (str), generationtime_ms (float)
- _validate_nested: delegates hourly dict to HourlyValidator

## HourlyValidator (src/validators/forecast_validator.py)
Sub-validator for the `hourly` dict inside a forecast response.
- REQUIRED: temperature_2m (list)
- OPTIONAL: windspeed_10m (list), time (list)
- _validate_nested: checks all temperature_2m values are in [-80, 60] range

## Usage in tests
```python
from validators.country_validator import CountryValidator
CountryValidator.assert_valid(results[0])

from validators.forecast_validator import ForecastValidator
ForecastValidator.assert_valid(response.json())
```

**Why:** Replaces manual `assert "field" in data` chains. Single place to update when API contract changes. test_currency.py still uses manual assertions — a future refactor could migrate it to CountryValidator.
