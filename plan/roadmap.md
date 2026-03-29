# Roadmap

## Current State (2026-03-29)

**SEC Financials** — Active, 27 companies, full XBRL history.
**FRED Macro Indicators** — Active, 6 series, full history.

| Metric | Value |
|---|---|
| Companies tracked | 27 (top 50 Azure ACR customers) |
| With annual data | 25 |
| With quarterly data | 23 |
| FRED series | 6 (GDP, CPI, PPI, employment) |
| Total JSON files | 33 (~436KB) |
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
