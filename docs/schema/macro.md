# FRED Macro Indicators — Data Dictionary

## Source

[Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/) via the FRED API.
Requires `FRED_API_KEY` environment variable (free registration).

## File Layout

- **Registry:** `macro/registry.yaml` — series metadata, keyed by FRED series ID
- **Time series data:** `macro/fred/{series_id}.json` — one file per series
- **Refresh script:** `macro/scripts/refresh_fred.py`
- **Helper module:** `macro/scripts/macro_indicators.py` (also `helpers/macro_indicators.py`)

## JSON Schema

### File-level fields

| Field | Type | Description |
|---|---|---|
| `series_id` | `string` | FRED series identifier (e.g., `GDPC1`, `SP500`) |
| `title` | `string` | Human-readable series name from FRED |
| `frequency` | `string` | Observation frequency: `quarterly`, `monthly`, `weekly`, or `daily` |
| `units` | `string` | Unit of measurement (see [Unit reference](#unit-reference)) |
| `last_refreshed` | `string` | ISO date (`YYYY-MM-DD`) of last data refresh |
| `observations` | `array` | Time series entries, sorted descending by `date` (most recent first) |

### Observation fields

| Field | Type | Description |
|---|---|---|
| `date` | `string` | Observation date (`YYYY-MM-DD`). For quarterly series, this is the first day of the quarter. For monthly, the first day of the month. |
| `value` | `float` | Observed value. **Not normalized** — interpretation depends on `units` field at file level. |

### Null semantics

Missing observations (FRED returns `.` for unavailable data) are **excluded** from the array. There are no `null` values — if a date is missing, it simply isn't present.

## Unit Reference

Values are **not normalized to a common unit**. The `units` field tells you how to interpret `value`.

| Category | Series IDs | Units | Interpretation |
|---|---|---|---|
| **GDP** | `GDPC1` | Billions of Chained 2017 Dollars | `value` = billions (e.g., `22038.2` = $22.04 T) |
| **Price indices** | `CPIAUCSL` | Index 1982-1984=100 | Relative to base period |
| | `CUSR0000SEEE` | Index Dec 1988=100 | IT-specific CPI |
| | `PCU518210518210` | Index Jun 2009=100 | Data processing/hosting PPI |
| **Employment** | `CE16OV` | Thousands of Persons | `value` = thousands |
| | `CES5051200001` | Thousands of Persons | Tech sector employment |
| **Interest rates** | `FEDFUNDS`, `DGS2`, `DGS10` | Percent | `value` = percentage (e.g., `5.33` = 5.33%) |
| **Credit spreads** | `BAA10Y` | Percent | Baa yield minus 10-year Treasury yield |
| **Market indices** | `SP500`, `NASDAQCOM` | Index | Dimensionless index level |
| **Unemployment** | `UNRATE` | Percent | `value` = percentage |
| **Jobless claims** | `ICSA` | Number | Raw count of initial claims |
| **FX rates** | See below | Various | See [FX conventions](#fx-conventions) |

## FX Conventions

FRED FX series use **inconsistent quoting conventions** — some are USD-per-foreign, others are foreign-per-USD. The helper provides `fx_usd_per_local()` to normalize.

| Series ID | Quote convention | Example | To get USD per 1 local unit |
|---|---|---|---|
| `DEXUSEU` | USD per 1 EUR | `1.08` = $1.08/€ | Use value directly |
| `DEXUSUK` | USD per 1 GBP | `1.27` = $1.27/£ | Use value directly |
| `DEXUSAL` | USD per 1 AUD | `0.66` = $0.66/A$ | Use value directly |
| `DEXCAUS` | CAD per 1 USD | `1.36` = C$1.36/$1 | Invert: `1 / value` |
| `DEXJPUS` | JPY per 1 USD | `149.5` = ¥149.5/$1 | Invert: `1 / value` |
| `DEXSZUS` | CHF per 1 USD | `0.88` = CHF 0.88/$1 | Invert: `1 / value` |
| `DEXKOUS` | KRW per 1 USD | `1320` = ₩1320/$1 | Invert: `1 / value` |
| `DEXSIUS` | SEK per 1 USD | `10.5` = kr 10.5/$1 | Invert: `1 / value` |

## Registry Schema (`macro/registry.yaml`)

| Field | Type | Description |
|---|---|---|
| `title` | `string` | Human-readable series name |
| `frequency` | `string` | `quarterly`, `monthly`, `weekly`, or `daily` |
| `units` | `string` | Unit of measurement |
| `relevance` | `string` | Why this series matters for cloud economics analysis |

## Series Inventory

### Economic growth
| Series ID | Title | Frequency |
|---|---|---|
| `GDPC1` | Real Gross Domestic Product | Quarterly |

### Inflation & pricing
| Series ID | Title | Frequency |
|---|---|---|
| `CPIAUCSL` | CPI: All Items | Monthly |
| `CUSR0000SEEE` | CPI: IT Hardware & Services | Monthly |
| `PCU518210518210` | PPI: Data Processing, Hosting & Related Services | Monthly |

### Employment
| Series ID | Title | Frequency |
|---|---|---|
| `CE16OV` | Civilian Employment Level | Monthly |
| `CES5051200001` | Tech Sector Employment (Computer Systems Design) | Monthly |
| `UNRATE` | Unemployment Rate | Monthly |
| `ICSA` | Initial Jobless Claims | Weekly |

### Interest rates & credit
| Series ID | Title | Frequency |
|---|---|---|
| `FEDFUNDS` | Federal Funds Effective Rate | Monthly |
| `DGS2` | 2-Year Treasury Rate | Daily |
| `DGS10` | 10-Year Treasury Rate | Daily |
| `BAA10Y` | Baa Corporate Spread vs 10-Year Treasury | Daily |

### Market indices
| Series ID | Title | Frequency |
|---|---|---|
| `SP500` | S&P 500 | Daily |
| `NASDAQCOM` | NASDAQ Composite | Daily |

### Foreign exchange
| Series ID | Title | Frequency |
|---|---|---|
| `DEXUSEU` | USD/EUR | Daily |
| `DEXUSUK` | USD/GBP | Daily |
| `DEXUSAL` | USD/AUD | Daily |
| `DEXCAUS` | CAD/USD | Daily |
| `DEXJPUS` | JPY/USD | Daily |
| `DEXSZUS` | CHF/USD | Daily |
| `DEXKOUS` | KRW/USD | Daily |
| `DEXSIUS` | SEK/USD | Daily |
