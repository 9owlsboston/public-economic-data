# Public Economic Data

Private aggregator of public economic and financial datasets for cloud economics analysis.

> **Current state:** see [`docs/current-state.md`](docs/current-state.md) for the
> dated "where we are now" snapshot (current → future → open gaps). This README
> holds the durable orientation; the snapshot holds the moving picture.

## Data Sources

| Source | Directory | Status | Refresh |
|---|---|---|---|
| **SEC EDGAR XBRL** | `sec/` | ✅ Active — 366 companies, full history | Quarterly (GitHub Action) |
| **FRED Macro Indicators** | `macro/` | ✅ Active — 22 series, full history | Monthly (GitHub Action) |
| **International Financials** | `intl/` | ✅ Active — 190 companies (Yahoo Finance) | Quarterly (GitHub Action) |
| **EDINET Financials** | `edinet/` | ✅ Active — 14 Japanese companies (EDINET XBRL) | Quarterly (GitHub Action) |
| Cloud Pricing (Azure/AWS/GCP) | `cloud-pricing/` | Planned | Monthly |
| SDK Adoption (PyPI/npm) | `sdk-adoption/` | Planned | Weekly |

## Data Dictionary

Field-level schema documentation for each data source:

| Module | Schema doc |
|---|---|
| SEC EDGAR | [`docs/schema/sec.md`](docs/schema/sec.md) — 10 financial metrics, XBRL tag mappings, segment schema |
| FRED Macro | [`docs/schema/macro.md`](docs/schema/macro.md) — 22 series, unit reference, FX conventions |
| International | [`docs/schema/intl.md`](docs/schema/intl.md) — 4 metrics, multi-currency handling |
| EDINET (Japan) | [`docs/schema/edinet.md`](docs/schema/edinet.md) — IFRS/J-GAAP tag resolution, 3 accounting standards |

## SEC Financials

### Coverage

366 companies from top Azure customers by ACR (registry-keyed; 369 standard data files — 3 filers predate registry entries). Revenue, R&D, COGS, net income, capex, operating cash flow, SGA, cash, total debt, total assets.
Supports `us-gaap` (10-K/10-Q) and `ifrs-full` (20-F foreign private issuers).

### Structure

```
sec/
  registry.yaml              # Company registry (CIK-keyed)
  financials/
    0000796343.json           # Adobe — 9 annual + 25 quarterly periods
    0000104169.json           # Walmart
    0000789019_segments.json  # Microsoft — segment-level revenue
    ...                       # 369 standard files + 1 segment file
  scripts/
    refresh.py                # SEC EDGAR fetcher (Submissions → CompanyFacts)
    refresh_segments.py       # Segment-level XBRL extraction
    sec_financials.py         # Helper module for reading data
```

### Usage

```python
from sec_financials import SECFinancials

# Local mode
sec = SECFinancials(local_dir="sec/financials")

# GitHub raw URL mode (private repo)
sec = SECFinancials(
    github_url="https://raw.githubusercontent.com/9owlsboston/public-economic-data/main/sec/financials",
    github_token="ghp_..."
)

# Get data (by CIK)
data = sec.get("0000796343")                    # Full Adobe data
latest = sec.latest_annual("0000796343")        # Most recent 10-K
yoy = sec.yoy_revenue_growth("0000796343")      # YoY revenue growth (decimal)
intensity = sec.rnd_intensity("0000796343")     # R&D / Revenue (decimal)
trend = sec.revenue_trend("0000796343", 5)      # Last 5 annual revenues
```

### Refresh

```bash
# All companies
python sec/scripts/refresh.py

# Single company (by CIK)
python sec/scripts/refresh.py --cik 0000796343

# Dry run
python sec/scripts/refresh.py --dry-run
```

Automated via GitHub Actions: runs quarterly on Jan/Apr/Jul/Oct 15.
Manual trigger available via `workflow_dispatch`.

### Data Flow

```
CIK
 ↓
Submissions API  → ALL 10-K/10-Q/20-F filings + period end dates
 ↓
CompanyFacts API → extract revenue, R&D, COGS, NI, capex, OCF, SGA, cash, debt, assets for each period end
 ↓
Tag resolution   → 3-layer: preferred list → best match → YAML override
 ↓
Duration disambig → quarterly = shortest duration, annual = longest
 ↓
Merge with existing JSON (keep all history)
 ↓
Write sec/financials/{cik}.json
```

## Adding a New Company

1. Find the company's CIK on [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany)
2. Add to `sec/registry.yaml`:
   ```yaml
   "0001234567":  # CIK
     name: "Company Name"
     ticker: "TICK"
     exchange: "NYSE"
   ```
3. Run `python sec/scripts/refresh.py --cik 0001234567`
4. Commit the new JSON file

## SEC Segment Data

For companies that disclose segment-level revenue in XBRL (e.g., Microsoft's Intelligent Cloud), an additional extraction pipeline produces segment files.

### Coverage

Currently Microsoft only. Segments: Intelligent Cloud, Productivity & Business Processes, More Personal Computing.

### Structure

Segment files use a `{cik}_segments.json` naming convention and a different schema from standard financials:

```json
{
  "cik": "0000789019",
  "company": "Microsoft Corporation",
  "last_refreshed": "2026-04-02",
  "segments": {
    "intelligent_cloud": [
      {"period_end": "2023-06-30", "form": "10-K", "start": "2022-07-01", "end": "2023-06-30", "revenue": 87907000000.0, "tag": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"}
    ]
  }
}
```

### Refresh

```bash
# Microsoft segments
python sec/scripts/refresh_segments.py --cik 0000789019
```

Segment extraction uses inline XBRL parsing (not CompanyFacts), since the standard API only provides consolidated totals. Companies must have `segment_tags` defined in `sec/registry.yaml`.

## FRED Macro Indicators

### Coverage

22 FRED series providing macroeconomic, market, FX, labor, and credit context.

| Series ID | Name | Frequency |
|---|---|---|
| `GDPC1` | Real GDP | Quarterly |
| `CPIAUCSL` | CPI All Items | Monthly |
| `CUSR0000SEEE` | CPI: IT Hardware & Services | Monthly |
| `PCU518210518210` | PPI: Data Processing & Hosting | Monthly |
| `CE16OV` | Civilian Employment Level | Monthly |
| `CES5051200001` | Tech Sector Employment | Monthly |
| `FEDFUNDS` | Federal Funds Effective Rate | Monthly |
| `DGS2` | 2-Year Treasury Rate | Daily |
| `DGS10` | 10-Year Treasury Rate | Daily |
| `SP500` | S&P 500 Index | Daily |
| `NASDAQCOM` | NASDAQ Composite Index | Daily |
| `DEXUSEU` | U.S. Dollars to One Euro | Daily |
| `DEXCAUS` | Canadian Dollars to One U.S. Dollar | Daily |
| `DEXJPUS` | Japanese Yen to One U.S. Dollar | Daily |
| `DEXSZUS` | Swiss Francs to One U.S. Dollar | Daily |
| `DEXUSUK` | U.S. Dollars to One British Pound | Daily |
| `DEXUSAL` | U.S. Dollars to One Australian Dollar | Daily |
| `DEXKOUS` | South Korean Won to One U.S. Dollar | Daily |
| `DEXSIUS` | Swedish Kronor to One U.S. Dollar | Daily |
| `UNRATE` | Unemployment Rate | Monthly |
| `ICSA` | Initial Claims | Weekly |
| `BAA10Y` | Baa Corporate Spread vs 10-Year Treasury | Daily |

### Structure

```
macro/
  registry.yaml              # Series registry (ID → metadata)
  fred/
    GDPC1.json               # Real GDP — 316 observations
    PCU518210518210.json      # PPI Data Processing
    ...                       # 22 files
  scripts/
    refresh_fred.py           # FRED API fetcher
    macro_indicators.py       # Helper module for reading data
```

### Usage

```python
from macro_indicators import MacroIndicators

macro = MacroIndicators(local_dir="macro/fred")

gdp = macro.latest("GDPC1")                    # Most recent observation
growth = macro.yoy_growth("GDPC1")              # YoY % change (decimal)
ppi = macro.trend("PCU518210518210", 12)         # Last 12 observations
series = macro.series_list()                     # All available series IDs
curve = macro.spread("DGS10", "DGS2")           # Yield curve spread
eurusd = macro.fx_usd_per_local("DEXUSEU")      # USD per 1 EUR
```

### Refresh

```bash
# All series
python macro/scripts/refresh_fred.py

# Single series
python macro/scripts/refresh_fred.py --series-id GDPC1

# Dry run
python macro/scripts/refresh_fred.py --dry-run
```

Automated via GitHub Actions: runs monthly on the 5th.
Manual trigger available via `workflow_dispatch`.

## International Financials

### Coverage

190 European and international companies. Revenue, R&D (where disclosed), COGS, net income.
Data sourced via Yahoo Finance (`yfinance`).

### Structure

```
intl/
  registry.yaml              # Company registry (ISIN-keyed)
  financials/
    DE0005190003.json          # BMW
    DE0007236101.json          # Siemens
    DE0007100000.json          # Mercedes-Benz
    DE0007664039.json          # Volkswagen
  scripts/
    refresh_intl.py            # Yahoo Finance fetcher
    intl_financials.py         # Helper module for reading data
```

### Usage

```python
from intl_financials import IntlFinancials

intl = IntlFinancials(local_dir="intl/financials")

latest = intl.latest_annual("DE0007236101")       # Siemens by ISIN
yoy = intl.yoy_revenue_growth("DE0007236101")     # YoY revenue growth (decimal)
trend = intl.revenue_trend("DE0005190003", 5)     # BMW last 5 annual revenues
```

### Refresh

```bash
# All companies
python intl/scripts/refresh_intl.py

# Single company (by ISIN)
python intl/scripts/refresh_intl.py --isin DE0007236101

# Dry run
python intl/scripts/refresh_intl.py --dry-run
```

Automated via GitHub Actions: runs quarterly on Jan/Apr/Jul/Oct 20.
Manual trigger available via `workflow_dispatch`.

## EDINET Financials (Japan)

### Coverage

14 Japanese companies. Revenue, operating income, net income.
Data sourced directly from EDINET XBRL filings (Japan FSA). All values in millions JPY.

### Structure

```
edinet/
  registry.yaml              # Company registry (EDINET code-keyed)
  financials/
    E04430.json                # NTT
    E01737.json                # Hitachi
    E01765.json                # NEC
    E01766.json                # Fujitsu
  scripts/
    refresh_edinet.py          # EDINET API + iXBRL parser
    edinet_financials.py       # Helper module for reading data
```

### Usage

```python
from edinet_financials import EDINETFinancials

edinet = EDINETFinancials(local_dir="edinet/financials")

latest = edinet.latest_annual("E04430")           # NTT by EDINET code
yoy = edinet.yoy_revenue_growth("E04430")         # YoY revenue growth (decimal)
trend = edinet.revenue_trend("E01766", 5)         # Fujitsu last 5 annual revenues
```

### Refresh

```bash
# All companies
python edinet/scripts/refresh_edinet.py

# Single company (by EDINET code)
python edinet/scripts/refresh_edinet.py --edinet-code E04430

# Dry run
python edinet/scripts/refresh_edinet.py --dry-run
```

Automated via GitHub Actions: runs quarterly on Jan/Apr/Jul/Oct 25.
Manual trigger available via `workflow_dispatch`.

**Note:** The refresh is slow (~20 min for all 4 companies) because EDINET's document list API requires scanning individual dates to find filings, and each XBRL ZIP must be downloaded and parsed.

## Requirements

- Python 3.10+
- `pyyaml` (`pip install pyyaml`)
- **SEC module:** No API keys required (SEC EDGAR is public, rate limit: 10 req/sec with User-Agent)
- **FRED module:** `FRED_API_KEY` environment variable (free — [register here](https://fred.stlouisfed.org/docs/api/api_key.html))
- **International module:** `yfinance` (`pip install yfinance`) — no API key required
- **EDINET module:** `EDINET_API_KEY` environment variable (free — [register here](https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1))
