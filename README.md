# Public Economic Data

Private aggregator of public economic and financial datasets for cloud economics analysis.

## Data Sources

| Source | Directory | Status | Refresh |
|---|---|---|---|
| **SEC EDGAR XBRL** | `sec/` | ✅ Active — 27 companies, full history | Quarterly (GitHub Action) |
| Cloud Pricing (Azure/AWS/GCP) | `cloud-pricing/` | Planned | Monthly |
| FRED / BLS Macro Indicators | `macro/` | Planned | Monthly |
| SDK Adoption (PyPI/npm) | `sdk-adoption/` | Planned | Weekly |

## SEC Financials

### Coverage

27 companies from top 50 Azure customers by ACR. Revenue, R&D, COGS, net income.
Supports `us-gaap` (10-K/10-Q) and `ifrs-full` (20-F foreign private issuers).

### Structure

```
sec/
  registry.yaml              # Company registry (CIK-keyed)
  financials/
    0000796343.json           # Adobe — 9 annual + 25 quarterly periods
    0000104169.json           # Walmart
    ...                       # 27 files, ~236KB total
  scripts/
    refresh.py                # SEC EDGAR fetcher (Submissions → CompanyFacts)
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
Write sec/financials/{tpid}.json
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

## Requirements

- Python 3.10+
- `pyyaml` (`pip install pyyaml`)
- No API keys required (SEC EDGAR is public, rate limit: 10 req/sec with User-Agent)
