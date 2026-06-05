from __future__ import annotations

from validators.base_validator import BaseValidator
from validators.country_validator import NameValidator

# Generated validator for REST Countries v3.1 /currency/{code} responses.
# Differs from CountryValidator: region and timezones are REQUIRED here
# because the /currency/ test suite asserts their presence and content.


class CurrencyCountryValidator(BaseValidator):
    REQUIRED_FIELDS: dict[str, type] = {
        "name": dict,
        "region": str,
        "timezones": list,
        "languages": dict,
        "currencies": dict,
        "population": int,
        "capital": list,
    }
    OPTIONAL_FIELDS: dict[str, type] = {
        "area": float,
        "subregion": object,  # null for some territories
    }

    @classmethod
    def _validate_nested(cls, data: dict) -> list[str]:
        if "name" in data and isinstance(data["name"], dict):
            return [f"name.{e}" for e in NameValidator.validate(data["name"])]
        return []
