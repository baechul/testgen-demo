---
name: project-test-suite-state
description: Current test files, test counts, and all-green baseline for the testgen-demo project as of 2026-06-04
metadata:
  type: project
---

As of 2026-06-04, the full suite has 30 tests across 4 files, all passing (30/30 in 16s).

**Why:** Verified by running `uv run pytest tests -v` — baseline to compare against after future generations.

**How to apply:** When asked to "continue" or verify state, run the full suite first to confirm the baseline is still green before generating new tests.

## Test files and counts

| File | Tests | Environment | Notes |
|------|-------|-------------|-------|
| tests/test_countries.py | 7 | countries | /name, /region (europe + americas) endpoints |
| tests/test_currency.py | 7 | countries | /currency/USD endpoint |
| tests/test_lang.py | 11 | countries | /lang/{code} parametrized over 4 languages |
| tests/test_weather.py | 5 | weather | /forecast parametrized over 5 cities |

## Test breakdown by type

- Schema tests: test_germany_schema, test_region_americas_schema, test_currency_usd_schema, test_lang_schema[x4], test_forecast_schema[x5]
- Count tests: test_region_europe_result_count, test_region_americas_result_count, test_currency_usd_result_count, test_lang_result_count[x4]
- Domain range tests: test_region_americas_area_in_valid_range, test_region_americas_population_in_valid_range, test_currency_usd_timezones_valid_format (format), test_currency_usd_languages_non_empty, test_currency_usd_region_non_empty
- Cross-endpoint consistency: test_name_search_appears_in_region, test_lang_korean_appears_in_region, test_lang_japanese_appears_in_region, test_currency_usd_country_appears_in_region
- Negative/error: test_lang_not_found_returns_404, test_currency_usd_not_found_returns_404
