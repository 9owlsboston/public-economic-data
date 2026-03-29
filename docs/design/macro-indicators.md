# Design: FRED & BLS Macro Indicators Module

**Status:** Implemented
**Date:** 2026-03-29
**Module:** `macro/`
**Phase:** 3 (per roadmap)

## Problem

CFO one-pager reports Azure spend in isolation. Adding macroeconomic context answers: _"Is Azure growth outpacing the market, or just riding the wave?"_

Example output: _"Enterprise IT spending grew 4.2% YoY (FRED) while Adobe's Azure spend grew 18% — 4.3× market rate."_

## Data Sources

### FRED (Federal Reserve Economic Data)

**API:** `https://api.stlouisfed.org/fred/series/observations`
**Auth:** Free API key (register at https://fred.stlouisfed.org/docs/api/api_key.html)
**Rate limit:** 120 requests/minute
**Format:** JSON

| Series ID | Name | Frequency | Relevance |
|---|---|---|---|
| `GDPC1` | Real GDP (chained 2017 dollars) | Quarterly | Overall economic growth context |
| `CPIAUCSL` | CPI-U All Items (seasonally adjusted) | Monthly | Inflation context for IT budgets |
| `CUSR0000SEEE` | CPI: IT Hardware & Services | Monthly | IT-specific inflation — closest CPI proxy for cloud pricing |
| `PCU518210518210` | PPI: Data Processing, Hosting | Monthly | Producer price index for data centers — closest proxy to cloud pricing pressure |
| `CE16OV` | Civilian Employment Level | Monthly | Overall employment (macro context) |
| `CES5051200001` | Employment: Computer Systems Design | Monthly | Tech sector hiring — demand signal |

### BLS (Bureau of Labor Statistics)

**API:** `https://api.bls.gov/publicAPI/v2/timeseries/data/`
**Auth:** Free registration key (higher rate limits with key)
**Rate limit:** 50 requests/day (unregistered), 500/day (registered)
**Format:** JSON

BLS series IDs overlap with FRED (FRED re-hosts many BLS series). **Use FRED as the single API** for both FRED and BLS data to avoid maintaining two API integrations.

## Design Decisions

### D1: Use FRED API for Everything

Both FRED and BLS data is available through FRED's API. No need for a separate BLS integration.
The FRED API key is free, has higher rate limits, and returns cleaner JSON.

### D2: Store as Time Series JSON (one file per series)

```
macro/fred/
  GDPC1.json              # Real GDP
  PCU518210518210.json     # PPI Data Processing
  CUSR0000SEEE.json        # CPI IT Hardware & Services
  CES5051200001.json       # Tech Employment
```

Each file:
```json
{
  "series_id": "GDPC1",
  "title": "Real Gross Domestic Product",
  "frequency": "quarterly",
  "units": "Billions of Chained 2017 Dollars",
  "last_refreshed": "2026-03-29",
  "observations": [
    {"date": "2025-10-01", "value": 23456.7},
    {"date": "2025-07-01", "value": 23234.5},
    {"date": "2025-04-01", "value": 23012.3}
  ]
}
```

### D3: Helper Provides Derived Metrics

The helper computes at read time:
- `yoy_growth(series_id, date)` — YoY % change
- `latest(series_id)` — most recent observation
- `trend(series_id, n)` — last N observations

### D4: Refresh Monthly

Most series update monthly. GDP is quarterly but still benefits from monthly refresh (revisions).
GitHub Action runs on the 5th of each month.

## Data Flow

```
FRED API Key (stored as GitHub Secret)
 ↓
GET /fred/series/observations?series_id=GDPC1&api_key=...&file_type=json
 ↓
Parse observations → extract (date, value) pairs
 ↓
Read existing macro/fred/GDPC1.json (if exists)
 ↓
Merge: add new observations, keep existing, deduplicate by date
 ↓
Write macro/fred/GDPC1.json
```

## File Structure

```
macro/
  fred/
    GDPC1.json
    PCU518210518210.json
    CUSR0000SEEE.json
    CES5051200001.json
  registry.yaml               # Series registry (ID → metadata)
  scripts/
    refresh_fred.py            # Fetcher
    macro_indicators.py        # Helper module

helpers/
  macro_indicators.py          # Consumer copy

tests/
  test_macro.py                # Validate JSON structure, freshness, data types

.github/workflows/
  refresh-macro.yml            # Monthly (5th of month)
```

## Implementation Steps

| # | Step | Effort |
|---|---|---|
| 1 | Register FRED API key, add as GitHub Secret `FRED_API_KEY` | Trivial |
| 2 | Create `macro/registry.yaml` with target series | Low |
| 3 | Create `macro/scripts/refresh_fred.py` | Medium |
| 4 | Create `macro/scripts/macro_indicators.py` helper | Low |
| 5 | Create `tests/test_macro.py` — validate JSON structure | Low |
| 6 | Run initial refresh to populate JSONs | Trivial |
| 7 | Create `.github/workflows/refresh-macro.yml` | Low |
| 8 | Write ADR-004 for design decisions | Low |
| 9 | Update README.md | Low |

## Consumer Usage

```python
from macro_indicators import MacroIndicators

macro = MacroIndicators(local_dir="macro/fred")

# Latest GDP
gdp = macro.latest("GDPC1")  # {"date": "2025-10-01", "value": 23456.7}

# YoY growth
gdp_growth = macro.yoy_growth("GDPC1")  # 0.024 = 2.4%

# PPI for data processing (cloud cost pressure proxy)
ppi = macro.trend("PCU518210518210", 12)  # last 12 months

# In CFO report:
# "PPI for Data Processing grew 3.1% YoY, while Azure ACR grew 18% —
#  Azure spend growth reflects demand expansion, not just price inflation."
```
