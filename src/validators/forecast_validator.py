from __future__ import annotations

from validators.base_validator import BaseValidator

# Generated validator for Open-Meteo /forecast API responses.
# Fields reflect what test_weather.py currently validates; extend as more
# hourly variables are added to the parametrize params list.


class HourlyValidator(BaseValidator):
    REQUIRED_FIELDS: dict[str, type] = {
        "temperature_2m": list,
    }
    OPTIONAL_FIELDS: dict[str, type] = {
        "windspeed_10m": list,
        "time": list,
    }

    @classmethod
    def _validate_nested(cls, data: dict) -> list[str]:
        if "temperature_2m" not in data or not isinstance(data["temperature_2m"], list):
            return []
        out_of_range = [
            t for t in data["temperature_2m"]
            if not isinstance(t, (int, float)) or not (-80 <= t <= 60)
        ]
        if out_of_range:
            # -80°C (Antarctic record low) to 60°C (documented surface maximum)
            return [f"temperature_2m has out-of-range values: {out_of_range}"]
        return []


class ForecastValidator(BaseValidator):
    REQUIRED_FIELDS: dict[str, type] = {
        "timezone": str,
        "hourly": dict,
    }
    OPTIONAL_FIELDS: dict[str, type] = {
        "latitude": float,
        "longitude": float,
        "elevation": float,
        "utc_offset_seconds": int,
        "timezone_abbreviation": str,
        "generationtime_ms": float,
    }

    @classmethod
    def _validate_nested(cls, data: dict) -> list[str]:
        if "hourly" in data and isinstance(data["hourly"], dict):
            return [f"hourly.{e}" for e in HourlyValidator.validate(data["hourly"])]
        return []
