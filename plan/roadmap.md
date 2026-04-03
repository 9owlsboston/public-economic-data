# Roadmap

## Current State (2026-04-03)

**SEC Financials** — Active, 28 companies, full XBRL history.
**FRED Macro Indicators** — Active, 18 series, full history.

| Metric | Value |
|---|---|
| Companies tracked | 28 (top 50 Azure ACR customers) |
| With annual data | 26 |
| With quarterly data | 21 |
| FRED series | 18 (GDP, inflation, employment, rates, market indices, FX, credit) |
| Total JSON files | 46 (~6.8MB) |
| Namespaces | us-gaap + ifrs-full |
| Currencies | USD, EUR, CAD, JPY, CHF |

## Phase 1: SEC Financials (✅ Complete)

- [x] SEC EDGAR integration (Submissions + CompanyFacts APIs)
- [x] us-gaap and ifrs-full namespace support
- [x] Period-end anchored extraction (not CY frames)
- [x] Duration disambiguation (quarterly vs annual)
- [x] 3-layer tag resolution (preferred → best match → YAML override)
- [x] Per-company JSON with full history
- [x] Python helper module (local + GitHub raw URL modes)
- [x] GitHub Action for quarterly auto-refresh
- [x] AI-agent-friendly repo structure (ADRs, copilot-instructions)

## Phase 2: Azure Retail Prices

**Goal:** Capture Azure list prices for ACD (Azure Commitment Discount) proxy analysis. Compare effective rate from ACR data against published list prices.

**Source:** Azure Retail Prices API — `https://prices.azure.com/api/retail/prices`

- [ ] Fetch VM compute prices by SKU × region
- [ ] Fetch storage prices by tier × redundancy × region
- [ ] Fetch AI/ML service prices (OpenAI, Cognitive Services)
- [ ] Store as `cloud-pricing/azure/{category}.json`
- [ ] Monthly refresh via GitHub Action
- [ ] Helper: `cloud_pricing.py` with `get_vm_price(sku, region)`

**Enables:** "D4s v5 effective rate ($0.154/hr) is 23% below list ($0.200/hr) → estimated ACD."

## Phase 2a: SEC Financials V2

**Goal:** Add capital intensity, cash generation, liquidity, and leverage context to the existing SEC dataset.

**Source:** SEC EDGAR Submissions + CompanyFacts APIs

- [ ] Add `capex_M` and `operating_cash_flow_M`
- [ ] Add `cash_M` and `total_debt_M`
- [ ] Add helper methods for free cash flow, net cash, and capex intensity
- [ ] Pilot coverage on `MSFT`, `NVDA`, `ADBE`, and `SAP`
- [ ] Extend `tests/test_sec.py` for the new fields

**Enables:** "NVIDIA capex intensity rose to 11% of revenue while operating cash flow margin expanded to 49%."

## Phase 3: Macro Indicators (FRED/BLS) (✅ Complete)

**Goal:** Context for IT spending trends. "Is Azure growth outpacing market?"

**Sources:**
- FRED API (free key) — GDP, CPI, PPI data processing, tech sector employment

- [x] Fetch key series: GDP (GDPC1), CPI (CPIAUCSL), CPI-IT (CUSR0000SEEE), PPI-DataProcessing (PCU518210518210), Employment (CE16OV), Tech Employment (CES5051200001)
- [x] Store as `macro/fred/{series_id}.json`
- [x] Monthly refresh via GitHub Action (5th of month)
- [x] Helper: `macro_indicators.py` with `latest()`, `yoy_growth()`, `trend()`, `series_list()`
- [x] Tests: `tests/test_macro.py` — 5 checks, 0 errors

**Enables:** "IT budgets grew 4% while Adobe's Azure grew 18% — 4.5× market rate."

## Phase 4: Cross-Cloud Pricing

**Goal:** "How does Azure pricing compare to AWS/GCP for equivalent workloads?"

**Sources:**
- AWS Pricing JSON (bulk download, no auth)
- GCP Cloud Billing Catalog API (API key, free)

- [ ] Map equivalent SKUs across clouds (D4s v5 ↔ m5.xlarge ↔ n2-standard-4)
- [ ] Fetch and normalize prices
- [ ] Store as `cloud-pricing/{provider}/{category}.json`

**Enables:** "Azure Compute is 8% cheaper than AWS for D-series equivalent in US East."

## Phase 5: SDK Adoption

**Goal:** Cloud platform momentum signals from developer ecosystem.

**Sources:**
- PyPI download stats API (`pypistats.org/api`)
- npm download stats API (`api.npmjs.org/downloads`)

- [ ] Track key packages: azure-identity, boto3, google-cloud-storage, openai
- [ ] Weekly refresh
- [ ] Store as `sdk-adoption/pypi/{package}.json`

**Enables:** "Azure Python SDK downloads grew 42% YoY vs AWS boto3 at 12%."

## Backlog (not prioritized)

- SEC full-text AI keyword mining (count "generative AI" mentions in 10-Q MD&A)
- USPTO patent data (AI/ML patent filings per company)
- Nightly bulk ZIP ingest (companyfacts.zip for scale)
- GitHub Archive (repo/contributor activity as tech adoption signal)
- World Bank data (regional cloud adoption context)
- Power / infrastructure input costs (EIA electricity + natural gas prices)
- IT spending forecasts (Gartner/IDC curated press-release data)
- AI ecosystem metrics (Hugging Face model downloads, Epoch AI training compute, Cloudflare Radar AI traffic, PyPI/npm SDK downloads)

## Known Issues & Technical Debt

Tracked here so agents and humans know what’s incomplete.

### SEC Segments (partially implemented)

`sec/scripts/refresh_segments.py` and `sec/financials/0000789019_segments.json` exist and work.

Open items:
- [ ] Add helper methods to `sec_financials.py`: `get_segments(cik)`, `latest_segment_annual(cik, segment)`
- [ ] Add segment schema tests to `tests/test_sec.py` (validate `segments` key, revenue fields, sort order)
- [ ] Add segment refresh to GitHub Action (or document as manual-only)
- [ ] Evaluate extending segments beyond Microsoft (requires `segment_tags` in registry per company)

### UBS Revenue Gap

UBS (CIK 0001610520) files as an IFRS bank. Revenue tags (`ifrs-full:Revenue`) don't map to their reporting structure (interest income, fee income, trading income are separate). All annual entries have `revenue_M: null`.

Options:
- [ ] Add bank-specific tag overrides in registry (e.g., `tag_overrides: { revenue: "ifrs-full:InterestIncomeExpenseNet" }`)
- [ ] Or accept as known limitation and keep the warning

### Helper Module Duplication

Helpers exist in two locations (`{module}/scripts/` and `helpers/`). Both must be manually kept in sync.

Options:
- [ ] Symlink `helpers/` files to canonical location (simplest)
- [ ] Or add a CI check that diffs the two copies and fails on mismatch
- [ ] Or restructure as a proper Python package with a single source

### Test Return Values

All test functions return error lists instead of asserting. pytest raises `PytestReturnNotNoneWarning` on every test. Functionally harmless but noisy.

- [ ] Refactor tests to use `assert not errors, errors` instead of `return errors`
