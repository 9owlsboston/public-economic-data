# Public Economic Data

Private aggregator of public economic and financial datasets for cloud economics analysis.

## Data Sources

| Source | Directory | Status | Refresh |
|---|---|---|---|
| **SEC EDGAR XBRL** | `sec/` | ✅ Active — 28 companies, full history | Quarterly (GitHub Action) |
| **FRED Macro Indicators** | `macro/` | ✅ Active — 18 series, full history | Monthly (GitHub Action) |
| Cloud Pricing (Azure/AWS/GCP) | `cloud-pricing/` | Planned | Monthly |
| SDK Adoption (PyPI/npm) | `sdk-adoption/` | Planned | Weekly |

## SEC Financials

### Coverage

28 companies from top 50 Azure customers by ACR. Revenue, R&D, COGS, net income.
Supports `us-gaap` (10-K/10-Q) and `ifrs-full` (20-F foreign private issuers).

### Structure

```
sec/
  registry.yaml              # Company registry (CIK-keyed)
  financials/
    0000796343.json           # Adobe — 9 annual + 25 quarterly periods
    0000104169.json           # Walmart
    0000789019_segments.json  # Microsoft — segment-level revenue
    ...                       # 28 standard files + 1 segment file
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
CompanyFacts API → extract revenue, R&D, COGS, NI for each period end
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

18 FRED series providing macroeconomic, market, FX, labor, and credit context.

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
    ...                       # 18 files
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

## Requirements

- Python 3.10+
- `pyyaml` (`pip install pyyaml`)
- **SEC module:** No API keys required (SEC EDGAR is public, rate limit: 10 req/sec with User-Agent)
- **FRED module:** `FRED_API_KEY` environment variable (free — [register here](https://fred.stlouisfed.org/docs/api/api_key.html))
