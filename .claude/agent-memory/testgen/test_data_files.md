---
name: test-data-files
description: Contents of test_data/ directory and which test files consume each file
metadata:
  type: project
---

All test data files live at project root `/test_data/`. Loaded at module scope via:
`Path(__file__).parent.parent / "test_data" / "<filename>"`

## test_data/cities.json
Consumed by: tests/test_weather.py
5 cities with latitude/longitude for /forecast parametrization:
- Seoul (37.5665, 126.978)
- Tokyo (35.6762, 139.6503)
- Berlin (52.52, 13.405)
- New York (40.7128, -74.006)
- São Paulo (-23.5505, -46.6333)

ids= derived from: c["name"]

## test_data/lang_inputs.json
Consumed by: tests/test_lang.py
4 languages for /lang/{code} parametrization:
- Korean (code: "korean")
- Spanish (code: "spanish")
- French (code: "french")
- Japanese (code: "japanese")

ids= derived from: l["name"]

**To add a new language:** Append `{"name": "<DisplayName>", "code": "<api-code>"}` to this file. The parametrized tests (test_lang_schema, test_lang_result_count) automatically pick it up. Add a separate `test_lang_<language>_appears_in_region` function if cross-endpoint consistency is wanted.
