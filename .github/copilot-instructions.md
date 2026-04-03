# Public Economic Data — Agent Instructions

## Purpose

Aggregator of public financial and economic datasets for cloud economics analysis.
Primary consumer: CFO one-pager recipe in `acr-analytics` skill.
Repo: `9owlsboston/public-economic-data` (private).

## Data Modules

| Module | Directory | Status |
|---|---|---|
| SEC EDGAR financials | `sec/` | Active — 28 companies, full history |
| SEC segment revenue | `sec/` | Active — Microsoft only (Intelligent Cloud, P&BP, MPC) |
| FRED macro indicators | `macro/` | Active — 18 series, full history |
| Cloud pricing | `cloud-pricing/` | Planned |
| SDK adoption | `sdk-adoption/` | Planned |

## Key Conventions

- **Registry vs data separation** — `sec/registry.yaml` has metadata only (name, ticker, exchange). Keyed by **CIK** (SEC's primary identifier). Financial data lives in `sec/financials/{cik}.json` (one file per company). Segment data lives in `sec/financials/{cik}_segments.json` (separate file, different schema — requires `segment_tags` in registry). `macro/registry.yaml` has series metadata (title, frequency, units). Keyed by **FRED series ID**. Time series data lives in `macro/fred/{series_id}.json` (one file per series).
- **No internal identifiers** — This repo uses public identifiers only (CIK, ticker, FRED series ID). Internal IDs like TPID belong in consumer repos (e.g., acr-analytics has a TPID→CIK mapping).
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
  → Write sec/financials/{cik}.json
```

```
SEC Segment Extraction (companies with segment_tags in registry):
  → Submissions API → filing list
  → Download inline XBRL HTML for each filing
  → Parse dimensional contexts to find segment members
  → Extract revenue by segment
  → Write sec/financials/{cik}_segments.json
```

```
FRED API (series/observations) → all observations for each series
  → Parse (date, value) pairs, skip missing values
  → Merge with existing JSON (deduplicate by date, newer wins)
  → Sort descending by date
  → Write macro/fred/{series_id}.json
```

## Helper Modules

Helpers exist in two identical locations: `{module}/scripts/` (canonical) and `helpers/` (consumer convenience copy). Always keep both in sync after changes.

Use `sec/scripts/sec_financials.py` (or `helpers/sec_financials.py`) to read SEC data:

```python
from sec_financials import SECFinancials
sec = SECFinancials(local_dir="sec/financials")
latest = sec.latest_annual("0000796343")
yoy = sec.yoy_revenue_growth("0000796343")
```

Use `macro/scripts/macro_indicators.py` (or `helpers/macro_indicators.py`) to read FRED data:

```python
from macro_indicators import MacroIndicators
macro = MacroIndicators(local_dir="macro/fred")
gdp = macro.latest("GDPC1")
growth = macro.yoy_growth("GDPC1")
ppi = macro.trend("PCU518210518210", 12)
curve = macro.spread("DGS10", "DGS2")
eurusd = macro.fx_usd_per_local("DEXUSEU")
```

## Do NOT

- Store derived ratios (YoY, R&D intensity, Azure %) in JSON — compute at read time
- Mix financial data into registry YAML files
- Hardcode currency assumptions — always check the `currency` field
- Overwrite amended filings — keep both original and amended (different `filing_date`)
- Manually edit JSON data files — always use the module's `refresh` script
- Use internal identifiers (TPID, enrollment numbers) — this repo uses public IDs only (CIK, ticker, FRED series ID)

## Development Workflow

When adding or modifying a data module, follow this sequence:

```
1. DESIGN    → docs/design/{module}.md       What and why (problem, API, schema)
2. ADR       → docs/adr/00N-*.md             Non-obvious decisions (if any)
3. IMPLEMENT → {module}/scripts/refresh.py    Fetch + transform + store
4. VALIDATE  → tests/test_{module}.py         Data quality checks
5. AUTOMATE  → .github/workflows/refresh-{module}.yml
6. DOCUMENT  → README.md + copilot-instructions.md
7. CHANGELOG → CHANGELOG.md entry
```

Full checklist: `docs/guides/adding-a-data-module.md`

**Always start with the design doc.** The design doc is what the agent (or human) reads to understand what we're building before writing code. Don't jump to implementation.

## Architecture Decision Records

See `docs/adr/` for numbered decisions explaining _why_ things are the way they are.
Read these before making structural changes — the decision may already be documented.

## Adding a New Data Source

Follow `docs/guides/adding-a-data-module.md` for the full checklist. Summary:

1. Write design doc (`docs/design/{module}.md`)
2. Create module directory with `scripts/`, `registry.yaml`
3. Implement refresh script with `--dry-run` and single-entity flags
4. Create validation tests (`tests/test_{module}.py`)
5. Add GitHub Action workflow
6. Copy helper to `helpers/`
7. Update README and this file
