# Financial Data Layer — Null Metric Audit

**Date:** 2026-04-20
**Scope:** All financial metrics in `public-companies.yaml` and SEC JSON source files
**Context:** Following the CapEx XBRL tag gap fix (see `capex-xbrl-gap-report.md`)

---

## Status: ✅ Implemented

All recommended tag additions have been applied to `sec/scripts/refresh.py`.
Run `refresh.py` to populate the new fields for all companies.

### Actual Impact (validated against 330 companies in registry)

| Metric | Tags Added | Companies Newly Resolved | Notes |
|--------|-----------|-------------------------|-------|
| `total_debt_M` | +3 tags | **55** | `LongTermDebtNoncurrent` is primary fix |
| `cost_of_revenue_M` | +1 tag | **7** (historical only) | Most are old periods — companies changed tags |
| `operating_income_M` | NEW metric, +2 tags | **245** | Brand new metric, massive coverage |
| `sga_M` | +1 tag | **91** | `GeneralAndAdministrativeExpense` fallback |
| `cash_M` | +2 tags | **43** | Restricted cash variant is primary fix |
| `capex_M` | (prior fix) | ✅ Done | See `capex-xbrl-gap-report.md` |

### What Remains Unfixable

- **Financial sector** (~18–25 per metric): Different income statement structure
- **Fiserv, Chevron, GE, T-Mobile** for `cost_of_revenue`: These companies don't
  report COGS separately in recent filings (restructured income statements)
- **Chevron, Exxon, SLB** for `operating_income`: Don't use `OperatingIncomeLoss`
  (oil majors report income differently)
- **International IFRS filers** with non-standard tags: Per-company mapping needed

| Metric | Total Null | Financial Sector | International | Fixable | Fix Priority |
|--------|-----------|------------------|---------------|---------|--------------|
| `total_debt_M` | 62 (46%) | 18 | 12 | **32 (24%)** | 🔴 High |
| `cost_of_revenue_M` | 59 (43%) | 25 | 6 | **28 (21%)** | 🔴 High |
| `sga_M` | 44 (32%) | 20 | 9 | **15 (11%)** | 🟡 Medium |
| `operating_income_M` | 39 (29%) | 23 | 4 | **12 (9%)** | 🟡 Medium |
| `cash_and_investments_M` | 29 (21%) | 16 | 4 | **9 (7%)** | 🟢 Low |
| `capex_M` | 9 (7%) | — | — | ✅ Fixed | ✅ Done |
| `rnd_M` | ~57% | — | — | Structural | ⚪ N/A |

**R&D (`rnd_M`)** is intentionally omitted from fix priority — most nulls are
structural (industrials, energy, financials that don't report R&D separately).

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

## Fix Plan — ✅ All Phases Complete

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
