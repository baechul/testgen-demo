from __future__ import annotations


class BaseValidator:
    REQUIRED_FIELDS: dict[str, type] = {}
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
        errors.extend(cls._validate_nested(data))
        return errors

    @classmethod
    def _validate_nested(cls, data: dict) -> list[str]:
        return []

    @classmethod
    def assert_valid(cls, data: dict) -> None:
        errors = cls.validate(data)
        assert not errors, "Validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
