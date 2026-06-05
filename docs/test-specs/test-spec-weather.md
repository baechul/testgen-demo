# Test Specification: Weather API

**Environment Key**: `weather`
**Base URL**: `https://api.open-meteo.com/v1`
**Last Synced**: 2026-06-04
**Spec Version**: 1.0.0

---

## Summary

| Metric | Count |
|---|---|
| Total Scenarios | 8 |
| Implemented | 1 |
| Missing Implementation | 7 |
| Spec Coverage % | 12.5% |

---

## Endpoints Covered

- `GET /forecast` — Retrieve weather forecast for given coordinates with parametrizable fields

---

## Test Scenarios

### TC-WEATHER-001: Forecast Schema Validation — Seoul

**Endpoint**: `GET /forecast`
**Priority**: P0
**Rule Reference**: RULE-ALL-001, RULE-HTTP-001, RULE-SCHEMA-001, RULE-DATA-003
**Status**: ✅ Implemented
**Implemented As**: `test_forecast_schema[Seoul]` in `tests/test_weather.py`

**Objective**: Validate that the `/forecast` endpoint returns a structurally valid forecast response with required fields present when querying Seoul coordinates.

**Preconditions**:
- Open-Meteo API is accessible at configured base URL
- Seoul coordinates (37.5665, 126.978) are valid

**Test Steps**:
1. Issue `GET /forecast` with params: `latitude=37.5665`, `longitude=126.978`, `hourly=temperature_2m`
2. Measure response time
3. Check HTTP status code
4. Parse JSON response
5. Validate response structure and required fields
6. Validate hourly temperature field structure

**Expected Results**:
- Response time < `3.0s` (from environment config)
- HTTP status code = 200
- Response contains required fields: `latitude`, `longitude`, `timezone`, `hourly` with `temperature_2m` array
- `hourly.temperature_2m` is an array with at least one temperature value

**Notes**: Parametrized test case for Seoul. Uses `ForecastValidator.assert_valid()` to validate forecast schema. Part of multi-city parametrization (RULE-DATA-003).

---

### TC-WEATHER-002: Forecast Schema Validation — Tokyo

**Endpoint**: `GET /forecast`
**Priority**: P0
**Rule Reference**: RULE-HTTP-001, RULE-SCHEMA-001, RULE-DATA-003
**Status**: ✅ Implemented
**Implemented As**: `test_forecast_schema[Tokyo]` in `tests/test_weather.py`

**Objective**: Validate forecast response for Tokyo as a representative city case.

**Preconditions**:
- Open-Meteo API is accessible
- Tokyo coordinates (35.6762, 139.6503) are valid

**Test Steps**:
1. Issue `GET /forecast` with params: `latitude=35.6762`, `longitude=139.6503`, `hourly=temperature_2m`
2. Measure response time
3. Check HTTP status code = 200
4. Validate response structure using ForecastValidator

**Expected Results**:
- Response time < `3.0s`, status = 200
- Response schema is valid with required fields present

**Notes**: Parametrized test case for Tokyo.

---

### TC-WEATHER-003: Forecast Schema Validation — Berlin

**Endpoint**: `GET /forecast`
**Priority**: P0
**Rule Reference**: RULE-HTTP-001, RULE-SCHEMA-001, RULE-DATA-003
**Status**: ✅ Implemented
**Implemented As**: `test_forecast_schema[Berlin]` in `tests/test_weather.py`

**Objective**: Validate forecast response for Berlin.

**Preconditions**:
- Open-Meteo API is accessible
- Berlin coordinates (52.52, 13.405) are valid

**Test Steps**:
1. Issue `GET /forecast` with params: `latitude=52.52`, `longitude=13.405`, `hourly=temperature_2m`
2. Measure response time
3. Validate response structure

**Expected Results**:
- Response time < `3.0s`, status = 200
- Response schema is valid

**Notes**: Parametrized test case for Berlin.

---

### TC-WEATHER-004: Forecast Schema Validation — New York

**Endpoint**: `GET /forecast`
**Priority**: P0
**Rule Reference**: RULE-HTTP-001, RULE-SCHEMA-001, RULE-DATA-003
**Status**: ✅ Implemented
**Implemented As**: `test_forecast_schema[New York]` in `tests/test_weather.py`

**Objective**: Validate forecast response for New York.

**Preconditions**:
- Open-Meteo API is accessible
- New York coordinates (40.7128, -74.006) are valid

**Test Steps**:
1. Issue `GET /forecast` with params: `latitude=40.7128`, `longitude=-74.006`, `hourly=temperature_2m`
2. Measure response time
3. Validate response structure

**Expected Results**:
- Response time < `3.0s`, status = 200
- Response schema is valid

**Notes**: Parametrized test case for New York. Tests negative longitude (Western Hemisphere).

---

### TC-WEATHER-005: Forecast Schema Validation — São Paulo

**Endpoint**: `GET /forecast`
**Priority**: P0
**Rule Reference**: RULE-HTTP-001, RULE-SCHEMA-001, RULE-DATA-003
**Status**: ✅ Implemented
**Implemented As**: `test_forecast_schema[São Paulo]` in `tests/test_weather.py`

**Objective**: Validate forecast response for São Paulo.

**Preconditions**:
- Open-Meteo API is accessible
- São Paulo coordinates (-23.5505, -46.6333) are valid

**Test Steps**:
1. Issue `GET /forecast` with params: `latitude=-23.5505`, `longitude=-46.6333`, `hourly=temperature_2m`
2. Measure response time
3. Validate response structure

**Expected Results**:
- Response time < `3.0s`, status = 200
- Response schema is valid

**Notes**: Parametrized test case for São Paulo. Tests Southern Hemisphere coordinates (negative latitude/longitude). Non-ASCII city name in test ID.

---

### TC-WEATHER-006: Missing Latitude Parameter

**Endpoint**: `GET /forecast`
**Priority**: P1
**Rule Reference**: RULE-HTTP-001
**Status**: ❌ Missing
**Implemented As**: N/A

**Objective**: Verify that the API returns a 400 error when the required `latitude` parameter is omitted.

**Preconditions**:
- Open-Meteo API is accessible

**Test Steps**:
1. Issue `GET /forecast` with params: `longitude=139.6503`, `hourly=temperature_2m` (no latitude)
2. Measure response time
3. Check HTTP status code

**Expected Results**:
- Response time < `3.0s`
- HTTP status code = 400 (Bad Request)
- Error response includes descriptive message about missing parameter

**Notes**: Error-path validation. Missing required parameters should be caught and reported clearly.

---

### TC-WEATHER-007: Missing Longitude Parameter

**Endpoint**: `GET /forecast`
**Priority**: P1
**Rule Reference**: RULE-HTTP-001
**Status**: ❌ Missing
**Implemented As**: N/A

**Objective**: Verify that the API returns a 400 error when the required `longitude` parameter is omitted.

**Preconditions**:
- Open-Meteo API is accessible

**Test Steps**:
1. Issue `GET /forecast` with params: `latitude=35.6762`, `hourly=temperature_2m` (no longitude)
2. Measure response time
3. Check HTTP status code

**Expected Results**:
- Response time < `3.0s`
- HTTP status code = 400
- Error response includes message about missing longitude

**Notes**: Error-path validation for missing required parameter.

---

### TC-WEATHER-008: Temperature Range Validation

**Endpoint**: `GET /forecast`
**Priority**: P1
**Rule Reference**: RULE-HTTP-001, RULE-DOMAIN-001
**Status**: ❌ Missing
**Implemented As**: N/A

**Objective**: Verify that all temperature values returned are within physically plausible range.

**Preconditions**:
- Open-Meteo API is accessible
- Test data has at least one city configured

**Test Steps**:
1. Issue `GET /forecast` for a known city with `hourly=temperature_2m`
2. Measure response time
3. Check HTTP status code = 200
4. Extract all temperature values from `hourly.temperature_2m`
5. Verify all temperatures fall within valid range

**Expected Results**:
- Response time < `3.0s`
- HTTP status code = 200
- All temperature values are in range [-80°C, 60°C]
  - -80°C is the Antarctic record low
  - 60°C is the documented surface maximum
- If any value is outside this range, test fails with explicit message listing the invalid values

**Notes**: Domain range validation (RULE-DOMAIN-001). Catches data corruption or unit-conversion errors that structural tests miss. Currently missing implementation.

---

## Rule Compliance Summary

| Rule | Status | Notes |
|---|---|---|
| RULE-ALL-001 | ✅ Pass | Test file declares `pytestmark = allure.feature("Weather API")` |
| RULE-HTTP-001 | ✅ Pass | `test_forecast_schema` asserts response time before status/body on all parametrized cases |
| RULE-SCHEMA-001 | ✅ Pass | Dedicated schema validation test using `ForecastValidator.assert_valid()` |
| RULE-DATA-001 | ✅ Pass | Test data loaded from `test_data/cities.json` |
| RULE-DATA-002 | ✅ Pass | Parametrization data sourced from JSON file, not inline |
| RULE-DATA-003 | ✅ Pass | Parametrization includes explicit `ids=[c["name"] for c in CITIES]` |
| RULE-DOMAIN-001 | ❌ Fail | Temperature domain range validation missing (see TC-WEATHER-008) |
| RULE-COUNT-001 | N/A | Endpoint returns single forecast, not a collection; count rule not applicable |

---

## Coverage Gaps

### Critical Gaps (P0)
- None identified in P0 scenarios; all core schema tests are covered for 5 representative cities.

### High-Priority Gaps (P1)
1. **Missing required parameters**: Tests TC-WEATHER-006 and TC-WEATHER-007 for `latitude` and `longitude` validation are missing.
2. **Domain range validation**: Test TC-WEATHER-008 for temperature bounds is missing. This validates that values are physically plausible.

### Medium-Priority Gaps (P2)
1. **Extreme coordinate boundaries**: No tests for poles (latitude ±90°) or date line (longitude ±180°).
2. **Forecast horizon**: No tests for `forecast_days` parameter or default forecast coverage.
3. **Timezone handling**: No validation of timezone field or UTC offset accuracy.
4. **Hourly vs Daily parameters**: No tests exploring the difference between `hourly` and `daily` parameters.
5. **Invalid coordinate values**: No tests for out-of-range coordinates (latitude > 90°, etc.).
6. **Cross-city consistency**: No tests verifying that forecast data structure is consistent across different geographic locations.
7. **Model parameter validation**: No tests for alternative weather models (if supported by API).

---

## Recommended Next Actions

1. **Add required-parameter validation tests** (P1): Implement TC-WEATHER-006 and TC-WEATHER-007 to catch missing parameter errors.
2. **Add domain range validation** (P1): Implement TC-WEATHER-008 to validate temperature values are physically plausible.
3. **Expand city coverage** (P2): Add more cities to `test_data/cities.json` (polar regions, equator, international date line).
4. **Test extreme coordinates** (P2): Add test cases for boundary values (±90° latitude, ±180° longitude).
5. **Validate timezone handling** (P2): Add assertion that returned timezone matches or is compatible with the requested coordinates.
6. **Test optional parameters** (P2): Explore `forecast_days`, `daily`, and other optional parameters for consistency and correctness.
