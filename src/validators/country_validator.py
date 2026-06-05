from __future__ import annotations

from validators.base_validator import BaseValidator

# Generated validator for REST Countries v3.1 country records.
# Covers endpoints: /name/{name}, /region/{region}, /lang/{code}
# All return the same country object shape.


class NameValidator(BaseValidator):
    REQUIRED_FIELDS: dict[str, type] = {
        "common": str,
        "official": str,
    }


class CountryValidator(BaseValidator):
    REQUIRED_FIELDS: dict[str, type] = {
        "name": dict,
        "capital": list,
        "population": int,
        "currencies": dict,
        "languages": dict,
    }
    OPTIONAL_FIELDS: dict[str, type] = {
        "region": str,
        "subregion": object,  # type unknown — null for some territories
        "area": float,
        "landlocked": bool,
        "flag": str,
    }

    @classmethod
    def _validate_nested(cls, data: dict) -> list[str]:
        if "name" in data and isinstance(data["name"], dict):
            return [f"name.{e}" for e in NameValidator.validate(data["name"])]
        return []
