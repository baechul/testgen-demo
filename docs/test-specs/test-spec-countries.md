# Test Specification: Countries API

**Environment Key**: `countries`
**Base URL**: `https://restcountries.com/v3.1`
**Last Synced**: 2026-06-04
**Spec Version**: 1.0.0

---

## Summary

| Metric | Count |
|---|---|
| Total Scenarios | 6 |
| Implemented | 3 |
| Missing Implementation | 3 |
| Spec Coverage % | 50% |

---

## Endpoints Covered

- `GET /name/<query>` — Search countries by name (e.g., `/name/germany`)
- `GET /region/<region>` — List all countries in a region (e.g., `/region/europe`)

---

## Test Scenarios

### TC-COUNTRIES-001: Country Name Search Schema Validation

**Endpoint**: `GET /name/{query}`
**Priority**: P0
**Rule Reference**: RULE-ALL-001, RULE-HTTP-001, RULE-SCHEMA-001, RULE-ASS-001
**Status**: ✅ Implemented
**Implemented As**: `test_germany_schema` in `tests/test_countries.py`

**Objective**: Validate that the `/name/<query>` endpoint returns a structurally valid country response with all required fields present.

**Preconditions**:
- REST Countries API is accessible at configured base URL
- Germany exists in the API

**Test Steps**:
1. Issue `GET /name/germany` request
2. Measure response time
3. Check HTTP status code
4. Parse JSON response
5. Validate response is a non-empty list
6. Validate first result has all required country fields

**Expected Results**:
- Response time < `2.0s` (from environment config)
- HTTP status code = 200
- Response is a JSON array with at least one element
- First country object contains required fields: `name`, `capital`, `population`, `currencies`, `languages` (and others validated by CountryValidator)

**Notes**: Uses `CountryValidator.assert_valid()` to validate country schema. Tests a specific country (Germany) as a representative case of the `/name/<query>` endpoint contract.

---

### TC-COUNTRIES-002: Country Name Search with Invalid Query

**Endpoint**: `GET /name/{query}`
**Priority**: P1
**Rule Reference**: RULE-HTTP-001
**Status**: ❌ Missing
**Implemented As**: N/A

**Objective**: Verify that searching for a non-existent country returns a 404 or empty result set, not a 500 error.

**Preconditions**:
- REST Countries API is accessible

**Test Steps**:
1. Issue `GET /name/xyznonexistentcountry123` request
2. Measure response time
3. Check HTTP status code
4. If 200, verify response is empty list

**Expected Results**:
- Response time < `2.0s`
- HTTP status code = 404 OR (200 with empty list)
- No 5xx errors

**Notes**: Error-path validation for the name search endpoint. Currently missing from implementation.

---

### TC-COUNTRIES-003: Country Name Search Case Insensitivity

**Endpoint**: `GET /name/{query}`
**Priority**: P1
**Rule Reference**: RULE-HTTP-001
**Status**: ❌ Missing
**Implemented As**: N/A

**Objective**: Verify that country name search is case-insensitive or follows documented case-handling rules.

**Preconditions**:
- REST Countries API is accessible

**Test Steps**:
1. Issue requests with different casing: `/name/germany`, `/name/Germany`, `/name/GERMANY`
2. Measure response time for each
3. Compare results across all cases

**Expected Results**:
- All three requests return response time < `2.0s`
- All three requests return HTTP 200
- Results are identical or documented as case-sensitive

**Notes**: Critical for usability. Currently missing from implementation.

---

### TC-COUNTRIES-004: Region Listing Schema Validation

**Endpoint**: `GET /region/{region}`
**Priority**: P0
**Rule Reference**: RULE-HTTP-001, RULE-COUNT-001, RULE-ASS-001, RULE-SCHEMA-001
**Status**: ✅ Implemented
**Implemented As**: `test_region_europe_result_count` in `tests/test_countries.py`

**Objective**: Validate that the `/region/<region>` endpoint returns a structurally valid list of countries with a minimum expected count.

**Preconditions**:
- REST Countries API is accessible
- Europe region contains >40 countries

**Test Steps**:
1. Issue `GET /region/europe` request
2. Measure response time
3. Check HTTP status code
4. Parse JSON response
5. Validate response is a list
6. Count result elements
7. Verify count exceeds 40

**Expected Results**:
- Response time < `2.0s`
- HTTP status code = 200
- Response is a JSON array
- Array length > 40 (Europe has 44+ countries)

**Notes**: Tests the collection endpoint contract with both structural validation and minimum count assertion (RULE-COUNT-001). The threshold of 40 is conservative and stable across API updates.

---

### TC-COUNTRIES-005: Cross-Endpoint Consistency — Name in Region

**Endpoint**: `GET /name/{query}` and `GET /region/{region}`
**Priority**: P0
**Rule Reference**: RULE-HTTP-001, RULE-CROSS-001, RULE-STY-007
**Status**: ✅ Implemented
**Implemented As**: `test_name_search_appears_in_region` in `tests/test_countries.py`

**Objective**: Verify that a country returned by the name search endpoint appears in the corresponding region's country list (cross-endpoint consistency).

**Preconditions**:
- REST Countries API is accessible
- Germany is searchable by name
- Germany is included in the Europe region list

**Test Steps**:
1. Issue `GET /name/germany` request
2. Measure response time
3. Check HTTP status code = 200
4. Extract `name.common` field from first result
5. Issue `GET /region/europe` request
6. Measure response time
7. Check HTTP status code = 200
8. Extract `name.common` field from all results
9. Verify Germany's name appears in the region's country list

**Expected Results**:
- Name search response time < `2.0s`, status = 200
- Region search response time < `2.0s`, status = 200
- Both responses are non-empty lists
- Germany's `name.common` value exists in the set of names from Europe region
- Failure message includes the searched name and region size for diagnostics

**Notes**: Catches data consistency bugs that purely structural tests miss. Uses explicit assertion message (RULE-STY-007) to aid debugging when the test fails.

---

### TC-COUNTRIES-006: Region Listing with Invalid Region

**Endpoint**: `GET /region/{region}`
**Priority**: P1
**Rule Reference**: RULE-HTTP-001
**Status**: ❌ Missing
**Implemented As**: N/A

**Objective**: Verify that requesting a non-existent region returns an appropriate error code, not a 5xx error.

**Preconditions**:
- REST Countries API is accessible

**Test Steps**:
1. Issue `GET /region/nonexistentregion123` request
2. Measure response time
3. Check HTTP status code
4. If 200, verify response is empty list

**Expected Results**:
- Response time < `2.0s`
- HTTP status code = 404 OR (200 with empty list)
- No 5xx errors

**Notes**: Error-path validation for the region endpoint. Currently missing from implementation.

---

## Rule Compliance Summary

| Rule | Status | Notes |
|---|---|---|
| RULE-ALL-001 | ✅ Pass | Both test files declare `pytestmark = allure.feature("Countries API")` |
| RULE-HTTP-001 | ✅ Pass | All 3 implemented tests assert response time before status/body |
| RULE-ASS-001 | ✅ Pass | Assertion order: latency → status → shape → content |
| RULE-SCHEMA-001 | ✅ Pass | `test_germany_schema` uses dedicated schema validator |
| RULE-CROSS-001 | ✅ Pass | `test_name_search_appears_in_region` validates endpoint consistency |
| RULE-COUNT-001 | ✅ Pass | `test_region_europe_result_count` asserts minimum result count |
| RULE-STY-007 | ✅ Pass | `test_name_search_appears_in_region` includes diagnostic message in assertion |
| RULE-STY-008 | ✅ Pass | Magic number 40 in result count has explanatory comment |

---

## Coverage Gaps

### Critical Gaps (P0)
- None identified in implemented tests; all P0 scenarios are covered.

### High-Priority Gaps (P1)
1. **Error-path validation**: Tests for invalid query parameters (e.g., `/name/xyznonexistent`) are missing. Currently no 4xx handling tests.
2. **Case sensitivity**: No tests for case-insensitive name search, which is likely important for UX.

### Medium-Priority Gaps (P2)
1. **Multi-word country names**: Countries like "United Kingdom" or "United Arab Emirates" not tested.
2. **Non-ASCII names**: Countries with non-ASCII characters in official names not exercised.
3. **Fields with optional presence**: `currencies` and `languages` for countries without them not tested.
4. **Parametrized region testing**: Only Europe is tested; other regions not covered.
5. **Name field variants**: `name.official` vs `name.common` distinction not validated.

---

## Recommended Next Actions

1. **Add error-path tests** (P1): Implement TC-COUNTRIES-002 and TC-COUNTRIES-006 to validate 4xx handling.
2. **Add case-sensitivity test** (P1): Implement TC-COUNTRIES-003 to verify search behavior.
3. **Parametrize region tests** (P2): Extend region testing to cover multiple regions (Africa, Asia, etc.) using parametrization.
4. **Parametrize name search** (P2): Test a variety of countries with different naming patterns (multi-word, non-ASCII, etc.).
