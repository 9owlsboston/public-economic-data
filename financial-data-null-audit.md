# Financial Data Layer — Null Metric Audit

**Date:** 2026-04-20 (initial), 2026-07-13 (cross-source expansion), 2026-07-18 (re-audit + remediation)
**Scope:** All data sources — SEC (365 companies), INTL (190 companies), EDINET (14 companies), FRED (22 series)
**Context:** Following CapEx XBRL tag gap fix, SEC Phase 1-4 tag expansion, INTL metric expansion (4→11), EDINET metric expansion (5→9→11), SEC legacy migration (32 companies), EDINET sga_M + total_debt_M extraction

---

## Status: ✅ All Phases Complete (Phase 1–9)

### Phase 1-3: SEC XBRL Tag Expansion (original audit)
All recommended tag additions applied to `sec/scripts/refresh.py`.

| Metric | Tags Added | Companies Resolved | Notes |
|--------|-----------|-------------------|-------|
| `total_debt_M` | +3 tags | **55** | `LongTermDebtNoncurrent` primary fix |
| `cost_of_revenue_M` | +1 tag | **7** (historical) | Companies changed tags |
| `operating_income_M` | NEW metric, +2 tags | **245** | Brand new metric |
| `sga_M` | +1 tag | **91** | `GeneralAndAdministrativeExpense` fallback |
| `cash_M` | +2 tags | **43** | Restricted cash variant primary fix |
| `capex_M` | (prior fix) | ✅ Done | See `capex-xbrl-gap-report.md` |

### Phase 4: SEC Cross-Metric Tag Expansion
Additional tags to close gaps discovered in comprehensive re-audit.

| Metric | Tag Added | Companies Resolved | Notes |
|--------|----------|-------------------|-------|
| `revenue_M` | `RevenueFromContractWithCustomerIncludingAssessedTax` | **7** (TJX, KHC, AKAM, RH, VRNS +2) | Companies switched from `Excluding` to `Including` variant |
| `net_income_M` | `ProfitLoss` (us-gaap) | **11** (CAT, CMI, MA, BSX, F +6) | Major US companies that stopped using `NetIncomeLoss` |
| `operating_cash_flow_M` | `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` | **6** (BDX, JCI, DD, FIS, NWSA +1) | Companies reporting continuing-ops OCF only |

### Phase 5: INTL Extraction Fixes
Fixes to `intl/scripts/refresh_intl.py` for Yahoo Finance data extraction.

| Issue | Fix | Companies Resolved | Notes |
|-------|-----|-------------------|-------|
| All-null entries (CBK, TSCO, 1810) | Skip income statement columns where all metrics are null (placeholder periods) | **3** | yfinance creates future-date columns with NaN for unreported periods |
| OCF null for AU/EU companies | Added fallback label `Cash Flowsfromusedin Operating Activities Direct` | **~9** | Australian and some European exchanges use different yfinance labels |
| Stale all-null entries | Filter all-null entries during merge | **3** | Old entries from previous refreshes with placeholder periods |

### Phase 6: INTL Metric Expansion (4→11 metrics) — completed prior
| Metric Added | Source | Coverage |
|-------------|--------|----------|
| `operating_income_M` | `ticker.financials` | 77% |
| `sga_M` | `ticker.financials` | 78% |
| `capex_M` | `ticker.cashflow` | 97% |
| `operating_cash_flow_M` | `ticker.cashflow` | 98% |
| `cash_M` | `ticker.balance_sheet` | 99.5% |
| `total_debt_M` | `ticker.balance_sheet` | 98% |
| `total_assets_M` | `ticker.balance_sheet` | 100% |

### Phase 7: EDINET Metric Expansion (5→9 metrics) — completed prior
| Metric Added | XBRL Tags | Coverage |
|-------------|-----------|----------|
| `total_assets_M` | `Assets` | 100% |
| `operating_cash_flow_M` | `CashFlowsFromUsedInOperatingActivities` | 100% |
| `capex_M` | `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` | 93% |
| `cash_M` | `CashAndCashEquivalents` | 86% |

### Phase 8: EDINET Metric Expansion (9→11 metrics) — ✅ Complete
| Metric Added | XBRL Tags | Actual Coverage |
|-------------|-----------|-----------------|
| `sga_M` | `SellingGeneralAndAdministrativeExpensesIFRS` (IFRS), `SellingGeneralAndAdministrativeExpenses` (J-GAAP) | 71.4% (10/14) |
| `total_debt_M` | `BondsAndBorrowingsNonCurrentIFRS` (IFRS), `LongTermLoansPayable` / `BondsPayable` (J-GAAP) | 21.4% (3/14) |

### Phase 9: SEC Legacy Schema Migration — ✅ Complete (32/32)
32 companies had pre-pipeline JSON files using old schema (`year` key instead of `period_end`, no `_M` suffixed metrics). All 32 were added to `sec/registry.yaml` and refreshed via `refresh.py --cik <CIK>`.

<details><summary>Legacy-schema CIKs (32 companies)</summary>

| CIK | Company |
|-----|---------|
| 0000004962 | American Express |
| 0000008670 | ADP |
| 0000014272 | Bristol-Myers Squibb |
| 0000039899 | Tegna |
| 0000078003 | Pfizer |
| 0000082473 | RELX PLC |
| 0000749251 | Gartner |
| 0000804328 | Qualcomm |
| 0000875320 | Vertex Pharmaceuticals |
| 0001009829 | LivePerson |
| 0001091667 | Charter Communications |
| 0001137774 | Prudential Financial |
| 0001289419 | Morningstar |
| 0001315098 | Roblox |
| 0001324424 | Expedia Group |
| 0001372612 | Box Inc. |
| 0001428439 | Roku |
| 0001467623 | Dropbox |
| 0001495153 | MakeMyTrip |
| 0001544522 | Freshworks |
| 0001551152 | AbbVie |
| 0001562088 | Duolingo |
| 0001576789 | Wix Ltd |
| 0001594805 | Shopify Inc. |
| 0001639920 | Spotify |
| 0001643269 | Sprinklr |
| 0001650372 | Atlassian |
| 0001679788 | Coinbase |
| 0001764046 | Clarivate Analytics |
| 0001786842 | Tempus AI |
| 0001818502 | Trip.com Group |
| 0001845338 | monday.com |

</details>

---

## Current Coverage Summary (post all phases)

### SEC (365 companies, latest annual entry)
**All 365 companies on new schema (0 legacy remaining).**

| Metric | Non-null | Coverage | Residual Category |
|--------|----------|----------|-------------------|
| `revenue_M` | 348 | 95.3% | Banks (interest income) + IFRS filers |
| `net_income_M` | 364 | 99.7% | DB (IFRS) |
| `rnd_M` | 181 | 49.6% | Structural — many sectors don't report R&D |
| `cost_of_revenue_M` | 215 | 58.9% | Structural — financials, energy |
| `sga_M` | 264 | 72.3% | Financials, non-standard structures |
| `operating_income_M` | 271 | 74.2% | Financials, energy majors |
| `capex_M` | 320 | 87.7% | Financials, some IFRS filers |
| `operating_cash_flow_M` | 362 | 99.2% | 3 IFRS 20-F filers |
| `cash_M` | 361 | 98.9% | SLB, DB + 2 others |
| `total_debt_M` | 274 | 75.1% | Financials, tech with no debt |
| `total_assets_M` | 364 | 99.7% | WPP (IFRS) |

### INTL (190 companies, latest annual entry)

| Metric | Null | Coverage | Notes |
|--------|------|----------|-------|
| `revenue_M` | 0 (0.0%) | 100% | ✅ |
| `net_income_M` | 0 (0.0%) | 100% | ✅ |
| `rnd_M` | 133 (70.0%) | 30.0% | Structural — industrials, financials, retail |
| `cost_of_revenue_M` | 47 (24.7%) | 75.3% | Banks, some exchanges don't report |
| `sga_M` | 42 (22.1%) | 77.9% | Structural |
| `operating_income_M` | 43 (22.6%) | 77.4% | Banks, some exchanges |
| `capex_M` | 6 (3.2%) | 96.8% | ✅ |
| `operating_cash_flow_M` | 4 (2.1%) | 97.9% | ✅ |
| `cash_M` | 1 (0.5%) | 99.5% | ✅ |
| `total_debt_M` | 3 (1.6%) | 98.4% | ✅ |
| `total_assets_M` | 0 (0.0%) | 100% | ✅ |

### EDINET (14 Japanese companies, latest annual entry)

| Metric | Non-null | Coverage | Notes |
|--------|----------|----------|-------|
| `revenue_M` | 14 | 100% | ✅ |
| `net_income_M` | 14 | 100% | ✅ |
| `operating_income_M` | 10 | 71.4% | Banks + SoftBank + FUJIFILM |
| `capex_M` | 13 | 92.9% | AEON |
| `operating_cash_flow_M` | 14 | 100% | ✅ |
| `total_assets_M` | 14 | 100% | ✅ |
| `cash_M` | 12 | 85.7% | Banks (SMFG, MUFG) |
| `rnd_M` | 0 | 0% | Structural — Japanese companies don't tag R&D in XBRL |
| `cost_of_revenue_M` | 10 | 71.4% | Banks + some industrials |
| `sga_M` | 10 | 71.4% | Banks + some industrials (Phase 8) |
| `total_debt_M` | 3 | 21.4% | Low tag match rate; only 3 of 14 match current XBRL tags |

### FRED (22 macro series)

| Status | Count | Notes |
|--------|-------|-------|
| ✅ Healthy | 22/22 | All series current, no null values |

---

## Downstream Impact by Recipe

### AIRX Index (`airx_index.py`)

| Input Metric | AIRX Calculations Affected | Pillar |
|-------------|---------------------------|--------|
| `cost_of_revenue_M` | gross_margin_vs_revenue, margin_expansion_delta, operating_margin_volatility_8q | Monetization (P1) |
| `capex_M` | fcf_margin_trend, capex_efficiency, capex_trend_inflection, fcf_stability_8q, capex_volatility_8q | Sustainability (P2), Capital Efficiency (P3) |
| `operating_cash_flow_M` | ocf_rnd_coverage, fcf_margin_trend, ai_burn_ratio, fcf_volatility_8q | Sustainability (P2) |
| `rnd_M` | monetization_efficiency, margin_expansion_delta, ocf_rnd_coverage, rnd_volatility_8q, rnd_as_pct_revenue | Monetization (P1), Sustainability (P2) |
| `sga_M` | operating_margin_volatility_8q (opex = rev − cogs − rnd − sga) | Risk/Volatility (P4) |
| `total_assets_M` | asset_turnover | Capital Efficiency (P3) |
| `net_income_M` | ai_burn_ratio | Sustainability (P2) |

### CFO One-Pager (`cfo_one_pager.py`)

| Input Metric | KPI | Null Impact |
|-------------|-----|-------------|
| `cost_of_revenue_M` | `gross_margin_pct` | Shows N/A |
| `sga_M` | `sga_pct_revenue` | Shows N/A |
| `operating_income_M` | `operating_margin_pct` | Shows N/A |
| `capex_M` | `free_cashflow_M`, `capex_intensity_pct` | Shows N/A |
| `operating_cashflow_M` | `free_cashflow_M` | Shows N/A |

---

## Metric-by-Metric Analysis

### 1. `total_debt_M` — 🔴 High Priority

**Current tags in `refresh.py`:**
- `us-gaap:LongTermDebt`
- `us-gaap:LongTermDebtAndCapitalLeaseObligations`
- `ifrs-full:Borrowings`

**Alternative tags found via EDGAR (add as fallbacks):**

| Tag | Standard | Companies Found | Notes |
|-----|----------|-----------------|-------|
| `LongTermDebtNoncurrent` | us-gaap | T-Mobile, multiple | Non-current portion only — common tag |
| `LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities` | us-gaap | GM | Includes current maturities |
| `ConvertibleLongTermNotesPayable` | us-gaap | ServiceNow | Convertible debt specific |
| `NoncurrentFinancialLiabilities` | ifrs-full | — | IFRS fallback for total borrowings |

**Recommended additions:**
```python
"total_debt": {
    "us-gaap": [
        "LongTermDebt",                                        # existing
        "LongTermDebtAndCapitalLeaseObligations",              # existing
        "LongTermDebtNoncurrent",                              # ← ADD
        "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",  # ← ADD
    ],
    "ifrs-full": [
        "Borrowings",                                           # existing
        "NoncurrentFinancialLiabilities",                       # ← ADD
    ],
}
```

**Fixable companies (sample):** ServiceNow, T-Mobile, GM, Chevron, Snowflake,
Cadence, OneStream, Rubrik, DocuSign, Caterpillar, Check Point, Datadog,
NIKE, Palantir.

---

### 2. `cost_of_revenue_M` — 🔴 High Priority

**Current tags in `refresh.py`:**
- `us-gaap:CostOfRevenue`
- `us-gaap:CostOfGoodsAndServicesSold`
- `ifrs-full:CostOfSales`

**Alternative tags found via EDGAR:**

| Tag | Standard | Companies | Notes |
|-----|----------|-----------|-------|
| `CostOfGoodsSold` | us-gaap | T-Mobile, Fiserv, SLB | Goods only (no services) |
| `CostOfServices` | us-gaap | T-Mobile, Fiserv, SLB | Services only — sum with CostOfGoodsSold |

**Recommended additions:**
```python
"cost_of_revenue": {
    "us-gaap": [
        "CostOfRevenue",                    # existing
        "CostOfGoodsAndServicesSold",       # existing
        "CostOfGoodsSold",                  # ← ADD (narrower, goods-only)
    ],
    "ifrs-full": [
        "CostOfSales",                      # existing
    ],
}
```

> **Note:** `CostOfGoodsSold` is narrower than `CostOfRevenue` and excludes
> service costs. For companies that report both `CostOfGoodsSold` and
> `CostOfServices`, the pipeline would need to sum them. As a pragmatic first
> step, using `CostOfGoodsSold` alone is a reasonable approximation for
> companies that don't report the composite tag.

**Fixable companies (sample):** AT&T, FedEx, GM, Fiserv, Exelon, Cognizant,
GE, Exxon, SLB, Kroger, Kimberly-Clark, American Airlines.

---

### 3. `sga_M` — 🟡 Medium Priority

**Current tags in `refresh.py`:**
- `us-gaap:SellingGeneralAndAdministrativeExpense`
- `ifrs-full:SellingGeneralAndAdministrativeExpense`

**Alternative tags found via EDGAR:**

| Tag | Standard | Companies | Notes |
|-----|----------|-----------|-------|
| `OperatingExpenses` | us-gaap | CVS, Willis, Exelon, GM | Broader — includes SG&A + other |
| `GeneralAndAdministrativeExpense` | us-gaap | — | G&A only (no selling) |

**Recommended addition:**
```python
"sga": {
    "us-gaap": [
        "SellingGeneralAndAdministrativeExpense",   # existing
        "GeneralAndAdministrativeExpense",          # ← ADD (narrower fallback)
    ],
    "ifrs-full": [
        "SellingGeneralAndAdministrativeExpense",   # existing
    ],
}
```

> **Note:** `OperatingExpenses` is too broad (includes depreciation, R&D, COGS)
> and should NOT be used as a fallback — it would overstate SG&A.
> `GeneralAndAdministrativeExpense` is a reasonable narrow fallback.

**Fixable companies (sample):** CVS, FedEx, GM, Gap Inc, Kimberly-Clark,
Kroger, Willis Towers Watson.

---

### 4. `operating_income_M` — 🟡 Medium Priority

**Not currently in `refresh.py` at all** — only available in YAML.

**Tags found via EDGAR:**

| Tag | Standard | Companies | Notes |
|-----|----------|-----------|-------|
| `OperatingIncomeLoss` | us-gaap | Toyota, GE, SLB | Standard US-GAAP tag |
| `ProfitLossFromOperatingActivities` | ifrs-full | — | IFRS equivalent |

**Recommended: Add to `refresh.py` as a new metric:**
```python
"operating_income": {
    "us-gaap": [
        "OperatingIncomeLoss",
    ],
    "ifrs-full": [
        "ProfitLossFromOperatingActivities",
    ],
},
```

**Impact:** Would populate `operating_income_M` in JSON files, removing
dependence on YAML-only data. Currently 12 non-financial companies lack this
metric: Chevron, Exxon, GE, Kyndryl, Nike, SLB, CRH, Brookfield, Concentra,
Ryan Specialty.

---

### 5. `cash_and_investments_M` — 🟢 Low Priority

**Current tags in `refresh.py` (as `cash`):**
- `us-gaap:CashAndCashEquivalentsAtCarryingValue`
- `us-gaap:CashCashEquivalentsAndShortTermInvestments`
- `ifrs-full:CashAndCashEquivalents`

**Alternative tags found via EDGAR:**

| Tag | Standard | Companies | Notes |
|-----|----------|-----------|-------|
| `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | us-gaap | American Airlines | Includes restricted cash |
| `CashAndCashEquivalentsAtCarryingValueIncludingDiscontinuedOperations` | us-gaap | GE | Includes discontinued ops |
| `CashAndCashEquivalentsIfDifferentFromStatementOfFinancialPosition` | ifrs-full | BAT | IFRS variant |
| `ShortTermInvestments` | us-gaap | SLB | Separate from cash — would need summing |

**Recommended additions:**
```python
"cash": {
    "us-gaap": [
        "CashAndCashEquivalentsAtCarryingValue",                                          # existing
        "CashCashEquivalentsAndShortTermInvestments",                                     # existing
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",                   # ← ADD
    ],
    "ifrs-full": [
        "CashAndCashEquivalents",                                                          # existing
        "CashAndCashEquivalentsIfDifferentFromStatementOfFinancialPosition",               # ← ADD
    ],
}
```

**Fixable companies (sample):** American Airlines, GE, P&G, SLB, Chevron, BAT.

---

### 6. `rnd_M` — ⚪ No Action Needed

**Null rate:** ~57% in YAML, 61% in JSON

**Classification:** Structural — most nulls are in sectors that don't report R&D:
- **Energy:** Chevron, Exxon, Shell, bp, SLB, Equinor, Woodside
- **Financials:** All banks, insurers, REITs
- **Industrials:** Caterpillar, FedEx, American Airlines, GM
- **Consumer/Retail:** Kroger, Albertsons, Gap, CVS, Kimberly-Clark

These companies either don't perform R&D or report it within other line items
(operating expenses). This is not a data pipeline gap.

---

## Structural Null Categories

Three categories of nulls that require no pipeline fix:

### Financial Sector (~18–25 companies per metric)
Banks, insurers, and REITs have fundamentally different income statements:
- No COGS (revenue is interest income)
- No SG&A (reported as noninterest expense)
- No operating income (use pre-provision income)
- Debt is a liability product, not leverage

Companies: JPMorgan, Morgan Stanley, MetLife, Chubb, Manulife, UBS, State
Street, Northern Trust, TD Bank, Lloyds, Westpac, Blackstone, Berkshire
Hathaway, Allstate, Sabra REIT, Fidelity National, National Bank Holdings,
China Life, HDFC Bank, Western Alliance, Mitsubishi UFJ, Sumitomo Mitsui.

### International IFRS Filers (4–12 per metric)
Companies filing with non-standard IFRS tags not yet in the pipeline:
Toyota, Shell, PDD, Alibaba, Woodside, Schneider Electric, GSK, WPP,
Equinor, ENI, bp, KT Corp.

### No SEC Filing (0 companies — fixed)
Thomson Reuters — Canadian filer, uses `40-F` form. ✅ Now supported (added in capex fix).

---

## Fix Plan — Phases 1–7 Complete, 8–9 Added

### Phase 1 — High Impact (total_debt, cost_of_revenue) ✅
1. ✅ Added `LongTermDebtNoncurrent` + `LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities` to `total_debt` → **55 companies** resolved
2. ✅ Added `NoncurrentFinancialLiabilities` (IFRS) to `total_debt`
3. ✅ Added `CostOfGoodsSold` to `cost_of_revenue` → **7 companies** (mostly historical periods)

### Phase 2 — Medium Impact (sga, operating_income) ✅
4. ✅ Added `GeneralAndAdministrativeExpense` to `sga` → **91 companies** resolved
5. ✅ Added `operating_income` as **new metric** with `OperatingIncomeLoss` + `ProfitLossFromOperatingActivities` → **245 companies** populated

### Phase 3 — Low Impact (cash) ✅
6. ✅ Added `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` to cash → **43 companies** resolved
7. ✅ Added IFRS `CashAndCashEquivalentsIfDifferentFromStatementOfFinancialPosition`

### Not Fixable (accept as N/A)
- Financial sector companies — structural nulls, different income statement format
- International IFRS filers with non-standard tags — requires per-company tag mapping
- Thomson Reuters — no SEC filing

### Phase 8 — EDINET Metric Expansion (9→11) 🟡 Pending Refresh
8. ✅ Added `sga_M` with `SellingGeneralAndAdministrativeExpensesIFRS` (IFRS) + `SellingGeneralAndAdministrativeExpenses` (J-GAAP)
9. ✅ Added `total_debt_M` with `BondsAndBorrowingsNonCurrentIFRS` (IFRS) + `LongTermLoansPayable` / `BondsPayable` (J-GAAP)
10. Added `total_debt_M` to `INSTANT_METRICS`

### Phase 9 — SEC Legacy Schema Migration 🟡 Pending Refresh
32 companies have pre-pipeline JSON files (old `year` key, no `_M` suffix, no `period_end`).
Run `python sec/scripts/refresh.py --cik <CIK>` for each to migrate.

---

## Appendix: Complete Metric Dependency Tree

```
REVENUE_M (0% null — fully populated)
├─ AIRX: 10+ calculations (foundation metric)
├─ CFO: azure_pct_revenue, innovation_intensity, margins
└─ Industry: peer comparison baseline

RND_M (57% null — structural, no fix needed)
├─ AIRX: monetization_efficiency, margin_expansion_delta,
│        ocf_rnd_coverage, rnd_volatility_8q
├─ CFO: innovation_intensity_pct, azure_pct_rnd
└─ Industry: peer comparison

COST_OF_REVENUE_M (43% null — 7 fixed via CostOfGoodsSold, most gaps structural)
├─ AIRX: gross_margin_vs_revenue, margin_expansion_delta,
│        operating_margin_volatility_8q
└─ CFO: gross_margin_pct, opex breakdown

TOTAL_DEBT_M (46% null — 55 fixed via LongTermDebtNoncurrent et al.)
└─ Currently informational (not in AIRX pillar scores)
   Potential: leverage ratio, interest coverage

OPERATING_INCOME_M (was 29% null — ✅ NEW metric, 245 companies populated)
├─ AIRX: margin_expansion_delta (fallback computed)
└─ CFO: operating_margin_pct

SGA_M (32% null — 91 fixed via GeneralAndAdministrativeExpense fallback)
├─ AIRX: operating_margin_volatility_8q (uses `or 0` fallback)
└─ CFO: sga_pct_revenue

CAPEX_M (7% null — ✅ fixed)
├─ AIRX: 6 calculations across P2 and P3 pillars
└─ CFO: free_cashflow_M, capex_intensity_pct

OPERATING_CASH_FLOW_M (0–1% null — fully populated)
├─ AIRX: ocf_rnd_coverage, fcf_margin_trend, ai_burn_ratio
└─ CFO: free_cashflow_M

NET_INCOME_M (4% null — minimal gap)
├─ AIRX: ai_burn_ratio
└─ CFO: sidecar (copy)

TOTAL_ASSETS_M (0% null — fully populated)
├─ AIRX: asset_turnover
└─ CFO: sidecar (copy)

CASH_AND_INVESTMENTS_M (21% null — 43 fixed via restricted-cash variant)
└─ Currently informational (not in AIRX pillar scores)

STOCKHOLDERS_EQUITY_M (0% null — fully populated, YAML only)
└─ Available for future: ROE, leverage ratios
```
