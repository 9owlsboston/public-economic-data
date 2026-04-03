# Assessment: Additional Public Datasets

**Date:** 2026-04-03
**Status:** Draft - revised after repo review and initial macro expansion
**Purpose:** Identify the next public economic and financial datasets that add the most value to this repo's existing SEC and macro foundation.

## Scope

This repo should continue to collect **publicly available economic and financial data only**:
- Government and central-bank statistics (FRED, BLS, BEA, EIA, World Bank)
- Public company disclosures (SEC EDGAR, earnings materials)
- Public cloud pricing APIs (Azure, AWS, GCP published list prices)
- Public market data and rates
- Curated public announcements when there is no stable API

Out of scope:
- Internal customer or contract data (ACR, TPID, subscriptions, discounts, effective rates)
- Scraped or legally ambiguous sources
- Highly manual datasets that do not create reusable leverage

## Review Summary

The repo is already strong where it matters most:
- The current modules are high-signal and low-friction.
- The storage pattern is consumer-friendly: one entity/series per file, simple helpers, straightforward tests.
- The best next additions are not broad new modules first. They are targeted extensions that deepen the existing SEC and FRED foundation.

The biggest gaps today:
1. **SEC data is still income-statement-heavy**. It is missing capex, cash flow, liquidity, and debt metrics that are very useful for cloud and AI investment analysis.
2. **Macro coverage is materially better now**, but it still lacks a few demand-side indicators and broader financial-conditions coverage.
3. **There is still no public cloud pricing module**, even though that is the clearest new non-SEC dataset for downstream cost analysis.
4. **Some proposed AI datasets remain interesting but less aligned** with the repo's core economics and financial use cases than pricing, SEC enrichment, or cloud-market benchmarks.

## Current State

| Module | Status | Data |
|---|---|---|
| SEC EDGAR financials | Active | 28 companies, revenue/R&D/COGS/net income, annual + quarterly history |
| FRED macro indicators | Active | 18 series covering GDP, inflation, employment, rates, market indices, FX, labor stress, and credit |

Notes from the current data:
- SEC already spans multiple currencies: USD, EUR, CAD, JPY, CHF.
- The macro module now includes an initial FX normalization path via `DEXUSEU`, `DEXCAUS`, `DEXJPUS`, `DEXSZUS` plus helper support for normalized USD-per-local-currency reads.
- The macro module now also includes `UNRATE`, `ICSA`, and `BAA10Y`, so the next macro additions should focus on demand and broader financial-conditions coverage.

## Assessment Criteria

Each candidate should be judged on:
- **Data value**: broadly useful signal for multiple consumers
- **Leverage**: whether normalization here saves repeated work elsewhere
- **Refreshability**: can it be fetched and refreshed with stable logic
- **Maintenance burden**: low ongoing curation cost
- **Fit**: directly relevant to cloud economics, company benchmarking, or market context

## Tier 1: Highest-value extensions to existing modules

These fit the repo's current architecture best and give the fastest payoff.

### 1. FX rates for currencies already present in SEC

Status: Implemented in the current pass.

**Source:** FRED FX series

**Recommended series to start with:**
- `DEXUSEU` - U.S. / Euro
- `DEXCAUS` - Canadian dollar / U.S. dollar
- `DEXJPUS` - Japanese yen / U.S. dollar
- `DEXSZUS` - Swiss franc / U.S. dollar

**Why this matters:** Several tracked companies file in non-USD currencies (`SAP`, `Toyota`, `UBS`, `TD`, `Manulife`). These series now give consumers a clean path to separate underlying business growth from currency translation effects.

**Value:** Very high.
**Effort:** Trivial to low. Same `macro/registry.yaml`, same FRED pipeline.

**Implementation note:** FRED FX series use different quote directions. The helper now normalizes them to `usd_per_local_currency` via `fx_usd_per_local()`.

---

### 2. Labor and demand indicators

Status: Initial labor coverage implemented; demand-side follow-ons still open.

**Source:** FRED API

**Current series:** `UNRATE`, `ICSA`

**Recommended follow-ons:**
- `PAYEMS` - All Employees, Total Nonfarm
- `INDPRO` - Industrial Production Index
- `RSAFS` - Retail Sales

**Why this matters:** GDP and CPI are useful, but they do not tell the full cycle story. Labor-market slack, claims, and real-economy demand make macro context much more interpretable when comparing company growth or customer spending.

**Value:** High.
**Effort:** Trivial.

**Recommendation:** The smallest high-signal labor set is now in place. The next best additions here are `INDPRO` and `RSAFS`.

---

### 3. Credit and financial conditions

Status: Initial credit coverage implemented; broader conditions still open.

**Source:** FRED API

**Current series:** `BAA10Y`

**Recommended follow-ons:**
- `NFCI` - National Financial Conditions Index
- `T10YIE` - 10-Year Breakeven Inflation Rate

**Why this matters:** You already have the raw Treasury points (`DGS2`, `DGS10`), but business conditions are often better captured by spreads and credit stress than by rates alone.

**Value:** High.
**Effort:** Trivial.

**Implementation note:** The helper now exposes `spread()` so consumers do not have to compute `DGS10 - DGS2` or similar gaps themselves.

---

### 4. Extend SEC financials beyond the income statement

**Source:** SEC Company Facts API, same pipeline you already use

**Recommended metrics:**
- Capex
- Operating cash flow
- Free cash flow (derived)
- Cash and short-term investments
- Total debt
- SBC, if reliably available across filers

**Why this matters:** This is likely the single most valuable dataset expansion in the repo. These metrics are directly useful for analyzing capital intensity, AI investment posture, cloud spend capacity, and balance-sheet resilience.

**Value:** Very high.
**Effort:** Low to medium, because the extraction machinery already exists.

**Recommendation:** Prioritize `capex`, `operating_cash_flow`, `cash`, and `total_debt` first. Those four materially expand usefulness without exploding schema complexity.

---

### 5. Broader segment revenue extraction

**Source:** SEC filings with company-specific member tags

**Why this matters:** Segment data is often the closest public proxy to cloud business performance. Microsoft is the clearest example, but this pattern could also help with companies where a "cloud", "platform", or "software" segment is explicitly disclosed.

**Value:** Medium to high.
**Effort:** Medium. More company-specific mapping and QA than the base SEC module.

**Recommendation:** Treat this as a focused extension of the SEC module, not a standalone module.

## Tier 2: New modules that fit the repo well

### 6. Azure Retail Prices

**Source:** `https://prices.azure.com/api/retail/prices`
**Auth:** None
**Format:** JSON with pagination

**Why this matters:** This is the strongest new module idea in the current roadmap. It directly complements ACR-style analysis and gives a public benchmark for list prices by SKU, region, and purchase model.

**What to store first:**
- VM compute prices for a curated SKU list
- Storage prices by tier/redundancy
- AI service prices
- Database prices for a small number of widely used services

**Value:** Very high.
**Effort:** Medium.

**Recommendation:** Keep scope intentionally narrow for V1. Start with the services most likely to matter to downstream analysis, not the full catalog.

---

### 7. Cloud provider revenue from public earnings

**Source:** Microsoft, Amazon, and Alphabet public earnings materials

**Why this matters:** This is a compact, quarterly dataset with a lot of downstream value. It creates a simple market baseline for cloud growth without every consumer having to parse three separate earnings packets.

**Value:** High.
**Effort:** Low.

**Recommendation:** Move this ahead of broader AI ecosystem work. It is more aligned and much easier to maintain.

---

### 8. Power and infrastructure input costs

**Source:** U.S. EIA public API

**What to track:**
- U.S. industrial electricity prices
- Commercial electricity prices
- Henry Hub natural gas benchmark
- Optional: regional power price proxies if there is a clear consumer use case

**Why this matters:** For cloud and AI economics, power is a real cost driver. This dataset is more directly tied to infrastructure economics than many developer-ecosystem proxies.

**Value:** Medium to high.
**Effort:** Low to medium.

**Recommendation:** Strong candidate if the repo's focus expands toward AI infrastructure economics.

---

### 9. IT spending forecasts

**Source:** Gartner, IDC, and similar public press releases

**Why this matters:** Good benchmark context, especially for one-pagers and executive summaries.

**Value:** Medium.
**Effort:** Low, but manual.

**Recommendation:** Useful curated dataset, but still below pricing, SEC enrichment, and cloud revenue in priority.

## Tier 3: Interesting, but lower-priority modules

### 10. AI ecosystem metrics

Examples:
- Hugging Face model downloads
- Epoch AI training compute database
- PyPI and npm package downloads
- Cloudflare Radar AI traffic snapshots
- Curated AI model timeline

**Assessment:** Interesting and potentially valuable, but more indirect.

Why lower priority:
- The signal-to-noise ratio is lower.
- Definitions may drift over time.
- Some metrics are more "industry narrative" than reusable economic baseline.
- Several parts are better suited to an exploratory or analyst-facing repo than to the core public-financial substrate.

**Recommendation:** Keep this as an optional later module or split it into the smallest pieces with the clearest signal, such as SDK downloads.

---

### 11. Cross-cloud pricing

**Assessment:** Still valuable, but defer until Azure pricing is working well.

Why defer:
- Equivalent SKU mapping is the real problem, not just fetching prices.
- AWS pricing payloads are large and awkward.
- It adds schema and QA complexity quickly.

## Recommended Implementation Order

| Priority | Dataset / Module | Why first |
|---|---|---|
| **1** | SEC enrichment: capex, OCF, cash, debt | Highest value using existing pipeline |
| **2** | Azure Retail Prices | Strong new module with direct cloud-economics fit |
| **3** | Cloud provider revenue | Low-effort curated benchmark with high downstream value |
| **4** | Power/input-cost data | Good fit if AI infra economics becomes a focus |
| **5** | FRED demand indicators (`INDPRO`, `RSAFS`, optional `PAYEMS`) | Best remaining low-effort macro additions |
| **6** | Broader financial-conditions indicators (`NFCI`, `T10YIE`) | Extends macro stress and inflation-expectations context |
| **7** | IT spending forecasts | Useful narrative context, but manual |
| **8** | AI ecosystem metrics | Interesting, but less core than the items above |
| **9** | Cross-cloud pricing | High complexity; wait until Azure pricing is proven |

## Quick Wins

These can be done immediately without new infrastructure:

1. Write a design doc for SEC enrichment before creating a brand-new module.
2. Add `INDPRO` and `RSAFS` as the next macro demand indicators.
3. Add one broader financial-conditions series such as `NFCI` or `T10YIE`.
4. Keep Azure Retail Prices as the first new non-FRED module.

## Recommended design-doc follow-ups

If you want to continue with this direction, the next design docs worth writing are:

1. `docs/design/sec-financials-v2.md` - capex, cash flow, liquidity, debt
2. `docs/design/azure-retail-prices.md` - scoped Azure pricing V1
3. `docs/design/cloud-provider-revenue.md` - curated quarterly cloud metrics
4. `docs/design/power-input-costs.md` - optional EIA module for infra economics
