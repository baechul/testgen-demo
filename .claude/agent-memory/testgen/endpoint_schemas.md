---
name: endpoint-schemas
description: Validated response shapes for all exercised REST Countries v3.1 and Open-Meteo endpoints
metadata:
  type: project
---

All schemas validated against live API responses as of 2026-06-04.

## REST Countries v3.1 (env: countries, base: https://restcountries.com/v3.1)

### Country object shape (shared across /name, /region, /lang, /currency)
- `name` (dict) — required; nested: `common` (str), `official` (str)
- `capital` (list) — required
- `population` (int) — required; >= 0 (some territories have 0 permanent residents)
- `currencies` (dict) — required
- `languages` (dict) — required
- `region` (str) — optional
- `subregion` (str or null) — optional; null for some territories
- `area` (float) — optional; > 0 when present (even smallest territory > 0 km²)
- `landlocked` (bool) — optional
- `flag` (str) — optional
- `timezones` (list of str) — optional; format "UTC" or "UTC±HH:MM"

### /name/{country}
- Returns: list of country objects
- /name/germany → list with Germany object; name.common = "Germany"
- Not found: 404

### /region/{region}
- Returns: list of country objects
- /region/europe → >40 countries (stable lower bound; Europe has >40 sovereign states)
- /region/americas → >30 countries
- /region/asia → contains South Korea (Korean-speaking) and Japan (Japanese-speaking)

### /lang/{code}
- Returns: list of country objects
- Tested codes: korean, spanish, french, japanese
- All return >= 1 country (environment.min_results_count = 1)
- Not found: 404 (e.g. /lang/notareallanguagexyz)

### /currency/{code}
- Returns: list of country objects
- /currency/USD → >5 countries/territories (USD used widely)
- Not found: 404 (e.g. /currency/ZZZNOTREAL)

## Open-Meteo (env: weather, base: https://api.open-meteo.com/v1)

### /forecast
- Required params: latitude, longitude, hourly (e.g. "temperature_2m")
- Returns: single object (not a list)
  - `timezone` (str) — required
  - `hourly` (dict) — required; nested: `temperature_2m` (list of float)
  - `latitude` (float) — optional
  - `longitude` (float) — optional
  - `elevation` (float) — optional
  - `utc_offset_seconds` (int) — optional
  - `timezone_abbreviation` (str) — optional
  - `generationtime_ms` (float) — optional
- temperature_2m range: -80°C to 60°C (Antarctic record low to documented surface maximum)
- Missing required params: returns 4xx
