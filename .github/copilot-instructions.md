# Public Economic Data — Agent Instructions

## Purpose

Aggregator of public financial and economic datasets for cloud economics analysis.
Primary consumer: CFO one-pager recipe in `acr-analytics` skill.
Repo: `9owlsboston/public-economic-data` (private).

## Data Modules

| Module | Directory | Status |
|---|---|---|
| SEC EDGAR financials | `sec/` | Active — 27 companies, full history |
| Cloud pricing | `cloud-pricing/` | Planned |
| Macro indicators | `macro/` | Planned |
| SDK adoption | `sdk-adoption/` | Planned |

## Key Conventions

- **Registry vs data separation** — `sec/registry.yaml` has metadata only (name, ticker, exchange). Keyed by **CIK** (SEC's primary identifier). Financial data lives in `sec/financials/{cik}.json` (one file per company).
- **No internal identifiers** — This repo uses public identifiers only (CIK, ticker). Internal IDs like TPID belong in consumer repos (e.g., acr-analytics has a TPID→CIK mapping).
- **Monetary values** — Always in millions, suffixed `_M` (e.g., `revenue_M: 23769`).
- **Period ordering** — Arrays sorted descending by `period_end` (most recent first).
- **Currency** — Each entry has a `currency` field. Do NOT assume USD. Suppress Azure % ratios when currency ≠ USD.
- **Null = not disclosed** — A metric value of `null` means the XBRL tag was not found. Show "Not disclosed" in reports, never omit silently.
- **No derived metrics in data files** — YoY growth, R&D intensity, Azure % are computed at report time, not stored. Raw data only.
- **tags_used** — Included on the first entry per scope only (to avoid bloat). Tags rarely change between periods.

## Data Flow

```
SEC EDGAR Submissions API → ALL filings + period end dates
  → CompanyFacts API → extract metrics by period end
  → Tag resolution (3-layer: preferred → best match → YAML override)
  → Duration disambiguation (quarterly = shortest, annual = longest)
  → Merge with existing JSON (keep all history, both original + amended)
  → Write sec/financials/{tpid}.json
```

## Helper Module

Use `sec/scripts/sec_financials.py` (or `helpers/sec_financials.py`) to read data:

```python
from sec_financials import SECFinancials
sec = SECFinancials(local_dir="sec/financials")
latest = sec.latest_annual(604913)
yoy = sec.yoy_revenue_growth(604913)
```

## Do NOT

- Store derived ratios (YoY, R&D intensity, Azure %) in JSON
- Mix financial data into `sec/registry.yaml`
- Hardcode currency assumptions — always check the `currency` field
- Overwrite amended filings — keep both original and amended (different `filing_date`)
- Manually edit JSON files — always use `sec/scripts/refresh.py`

## Architecture Decision Records

See `docs/adr/` for numbered decisions explaining _why_ things are the way they are.

## Adding a New Data Source

1. Create a new top-level directory (e.g., `cloud-pricing/`)
2. Add a `scripts/refresh_*.py` fetcher
3. Add a `.github/workflows/refresh-*.yml` Action
4. Add a helper to `helpers/`
5. Update README.md
