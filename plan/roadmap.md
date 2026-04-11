# Roadmap

## Current State (2026-04-10)

**SEC Financials** — Active, 196 companies, full XBRL history.
**Intl Financials** — Active, 39 companies (Yahoo Finance sourced).
**EDINET Financials** — Active, 14 companies (Japan FSA sourced).
**FRED Macro Indicators** — Active, 22 series, full history.

| Metric | Value |
|---|---|
| SEC companies tracked | 196 |
| Intl companies tracked | 39 |
| EDINET companies tracked | 14 |
| **Total companies** | **249** |
| With annual data | ~230 |
| With quarterly data | ~180 |
| FRED series | 22 (GDP, inflation, employment, rates, market indices, FX, credit) |
| Total JSON files | ~270 |
| Namespaces | us-gaap + ifrs-full |
| Currencies | USD, EUR, CAD, JPY, CHF, GBP, KRW, AUD, SEK, NOK |

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

## Phase 2a: SEC Financials V2 (✅ Complete)

**Goal:** Add capital intensity, cash generation, liquidity, and leverage context to the existing SEC dataset.

**Source:** SEC EDGAR Submissions + CompanyFacts APIs

- [x] Add `capex_M` and `operating_cash_flow_M`
- [x] Add `cash_M` and `total_debt_M`
- [x] Add `sga_M` and `total_assets_M`
- [x] Add helper methods for free cash flow, net cash, capex intensity, and OCF margin
- [x] Pilot coverage on `MSFT`, `NVDA`, `ADBE`
- [x] Re-refresh all 196 SEC companies with V2 fields (191/196 populated; 5 Canadian filers have 0 annual entries)

**Enables:** "NVIDIA capex intensity rose to 11% of revenue while operating cash flow margin expanded to 49%."

## Phase 2b: ACR-Analytics Integration (NEW)

**Goal:** Close the data gaps identified by `acr-analytics` top-500 coverage analysis.
The consumer repo (`acr-analytics`) now reads financial data directly from this repo
via `get_public_financials()`. Coverage gaps here directly limit CFO report quality.

**Dependency:** `acr-analytics` WS4 (public data integration) is complete; WS5 (AI
monetization analytics) needs expanded coverage for cross-customer benchmarks.

**Reference:** `acr-analytics/docs/reference/top500-financial-coverage.md` (2026-04-08)

### 2b.1 — Verify expanded XBRL fields in SEC JSONs (✅ Complete)

`acr-analytics/_base.py` reads `capex_M`, `operating_cashflow_M`, `total_assets_M`,
`sga_M` from provider JSONs. Verify SEC refresh script extracts these XBRL tags
and that existing JSON files contain them. Overlaps with Phase 2a.

- [x] Audit `sec/scripts/refresh.py` tag list for `CapitalExpenditures*`, `OperatingCashFlow*`, `Assets`, `SellingGeneralAndAdministrativeExpense`
- [x] Run refresh on pilot companies (ADBE, MSFT, NVDA) and verify fields populated
- [x] Bulk re-refresh all 196 SEC companies if tag extraction was missing

**Validates:** WS4.4 expanded financials + WS5.1 AI financial linkage

### 2b.2 — Verify prior-year annual data in JSON arrays (✅ Verified)

`acr-analytics/_base.py` reads `annual[1]` for YoY revenue growth comparison.
All three modules (SEC, intl, EDINET) must produce `annual` arrays sorted
newest-first with ≥2 entries.

- [x] Verify `annual` array has ≥2 entries for companies with 2+ fiscal years of history
- [x] Verify sort order is newest-first (descending by `period_end`)
- [x] Fix any refresh scripts that truncate to single-year output

Note: 6 SEC files have exactly 1 annual entry — these are recent IPOs/newly-registered
filers (e.g., BlackRock 0002012383, Huachen AI 0001958399), not a truncation bug.
Intl and EDINET all have ≥2.

**Validates:** `revenue_yoy_growth_pct` and `ai_vs_revenue_growth_ratio` in WS5.1

### 2b.3 — Register remaining European companies (mostly done)

Original gap was 37 companies. 28 have been registered (intl count: 11 → 39).
Of the 10 priority targets, 8 are registered. Remaining 2 are non-public:

| Company | ACR ($M) | Status |
|---|---|—|
| Rabobank | 10.8 | Cooperative — no public equity, tombstone candidate |
| Robert Bosch GmbH | 8.9 | Private — tombstone |

- [x] Batch ISIN lookup for priority companies
- [x] Filter out private companies (Bosch, Aldi, Bertelsmann) → tombstone in acr-analytics mapping
- [x] Add public companies to `intl/registry.yaml` (28 added)
- [x] Run `intl/scripts/refresh.py` to fetch Yahoo Finance data
- [ ] Sync new entries to `acr-analytics/data/tpid-cik-mapping.yaml`
- [ ] Tombstone Rabobank + Bosch in acr-analytics mapping

**Validates:** WS5.2 cross-customer AI leaderboard (broader coverage)

### 2b.4 — Add FX rate series to FRED (✅ Complete)

SEC/intl/EDINET JSONs report in local currency. `acr-analytics` uses static
`FX_RATES_USD` for conversion. Add FRED exchange rate series so the consumer
can read live rates.

- [x] Add series: DEXUSEU (USD/EUR), DEXJPUS (USD/JPY), DEXUSUK (USD/GBP), DEXSZUS (USD/CHF), DEXCAUS (USD/CAD), DEXUSAL (USD/AUD), DEXKOUS (USD/KRW), DEXSIUS (USD/SEK)
- [x] Run `macro/scripts/refresh_fred.py` to fetch history
- [x] Add `get_fx_rate(currency, date)` helper to `macro_indicators.py`

**Enables:** Dynamic FX conversion in CFO reports (replace static rates)

### 2b.5 — Register 11 Japanese companies (✅ Complete)

All 10 target companies registered and data fetched. Government ministry tombstoned.

| Company | EDINET Code | Status |
|---|---|---|
| 三井住友FG (SMFG) | E03674 | ✅ Registered, 7 annual entries |
| 楽天 (Rakuten) | E05080 | ✅ Registered, 8 annual entries |
| イオン (AEON) | E03498 | ✅ Registered, 7 annual entries |
| ソフトバンクG | E02778 | ✅ Registered, 7 annual entries |
| 日産自動車 | E02142 | ✅ Registered, 7 annual entries |
| パナソニック | E01772 | ✅ Registered, 7 annual entries |
| ソニー | E01777 | ✅ Registered, 7 annual entries |
| クボタ | E01267 | ✅ Registered, 8 annual entries |
| 三菱UFJFG | E03606 | ✅ Registered, 7 annual entries |
| 富士フイルムHD | E00334 | ✅ Registered, 7 annual entries |
| 厚生労働省 | — | Tombstoned (government ministry) |

- [x] Look up EDINET codes for all 11 companies
- [x] Filter government entities → tombstone
- [x] Add to `edinet/registry.yaml`
- [x] Run `edinet/scripts/refresh_edinet.py`
- [ ] Sync to acr-analytics mapping

### 2b.6 — Triage 124 SEC auto-discovered matches (P4)

`acr-analytics` auto-discovery found 124 CIK matches via `search_sec_cik()` but
many are wrong (e.g., PwC → RH, Barracuda → Palo Alto, G42 → Huachen AI).
Human verification required before registration.

- [ ] Export candidate list with company name, matched ticker, matched CIK
- [ ] Manual triage: confirm, reject, or correct each match
- [ ] Add confirmed matches to `sec/registry.yaml`
- [ ] Run SEC refresh for new entries
- [ ] Tombstone rejected matches in acr-analytics mapping

**Effort:** Largest item — ~124 entries to review. Expected yield: ~60-80 valid matches.

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

### SEC Segments (mostly resolved)

`sec/scripts/refresh_segments.py` and `sec/financials/0000789019_segments.json` exist and work.

- [x] Add helper methods to `sec_financials.py`: `get_segments(cik)`, `latest_segment_annual(cik, segment)`, `segment_names(cik)`
- [x] Add segment schema tests to `tests/test_sec.py` (validate `segments` key, revenue fields, sort order)
- [x] Add segment refresh to GitHub Action
- [ ] Evaluate extending segments beyond Microsoft (requires `segment_tags` in registry per company)

### UBS Revenue Gap

UBS (CIK 0001610520) files as an IFRS bank. Revenue tags (`ifrs-full:Revenue`) don't map to their reporting structure (interest income, fee income, trading income are separate). All annual entries have `revenue_M: null`.

Options:
- [ ] Add bank-specific tag overrides in registry (e.g., `tag_overrides: { revenue: "ifrs-full:InterestIncomeExpenseNet" }`)
- [ ] Or accept as known limitation and keep the warning

### Helper Module Duplication (mitigated)

Helpers exist in two locations (`{module}/scripts/` and `helpers/`). Both must be manually kept in sync.

- [ ] Symlink `helpers/` files to canonical location (simplest)
- [x] Add a CI check that diffs the two copies and fails on mismatch (`.github/workflows/check-helpers.yml`)
- [ ] Or restructure as a proper Python package with a single source

### Test Return Values (✅ Resolved)

Fixed: tests now use `assert not errors` for hard checks and `warnings.warn()` for known-issue soft checks. Zero `PytestReturnNotNoneWarning`.
