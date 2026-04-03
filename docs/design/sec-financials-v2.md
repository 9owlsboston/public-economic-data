# Design: SEC Financials V2

**Status:** Proposed
**Date:** 2026-04-03
**Module:** `sec/`
**Phase:** Next iteration

## Problem

The current SEC module captures revenue, R&D, cost of revenue, and net income. That is enough for growth and profitability context, but not enough for capital intensity or balance-sheet analysis.

Consumers still cannot answer questions like:
- Is a company funding growth with operating cash flow or balance-sheet capacity?
- Is AI investment showing up in capex or cash flow pressure?
- Which companies are liquid enough to absorb large infrastructure spend?
- Which companies are already more leveraged going into a slower macro environment?

## Goals

- Extend the existing SEC dataset with a small set of additional raw financial metrics.
- Reuse the current `Submissions` + `CompanyFacts` pipeline.
- Preserve the current storage model: one JSON per company, annual and quarterly arrays, raw data only.
- Compute derived metrics in the helper at read time, not in the JSON files.

## Non-goals

- Perfectly normalize every balance-sheet concept across all industries.
- Infer undisclosed values from footnotes or management commentary.
- Build company-specific segment logic into the base financials file.

## Proposed Metrics

### Phase 1: Core additions

| Field | Type | Why it matters | Notes |
|---|---|---|---|
| `capex_M` | Duration | Proxy for infrastructure and capacity investment | Annual + quarterly |
| `operating_cash_flow_M` | Duration | Cash generation quality | Annual + quarterly |
| `cash_M` | Instant | Liquidity / near-term flexibility | Point-in-time at period end |
| `total_debt_M` | Instant | Leverage / financing posture | Point-in-time at period end |

### Phase 2: Optional additions

| Field | Type | Why it matters | Notes |
|---|---|---|---|
| `sbc_M` | Duration | Important for AI/software companies | Coverage may be uneven |

## Data Sources

### SEC Company Facts API

**API:** `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
**Auth:** None
**Rate limit:** SEC guidance requires a descriptive `User-Agent`; stay under 10 requests/sec
**Format:** JSON

This remains the source of record for extracted facts.

### SEC Submissions API

**API:** `https://data.sec.gov/submissions/CIK{cik}.json`

This remains the source of record for filing lists, filing dates, and `reportDate` period ends.

## Candidate Tag Families

These are starting points, not an exhaustive mapping:

| Metric | us-gaap examples | ifrs-full examples | Notes |
|---|---|---|---|
| `capex_M` | `PaymentsToAcquirePropertyPlantAndEquipment` | `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` | Cash-flow statement metric |
| `operating_cash_flow_M` | `NetCashProvidedByUsedInOperatingActivities` | `NetCashFlowsFromUsedInOperatingActivities` | Cash-flow statement metric |
| `cash_M` | `CashAndCashEquivalentsAtCarryingValue` | `CashAndCashEquivalents` | Balance-sheet instant metric |
| `total_debt_M` | `LongTermDebtAndFinanceLeaseObligations`, `LongTermDebtCurrent`, `LongTermDebtNoncurrent` | `Borrowings`, `CurrentBorrowings`, `NoncurrentBorrowings` | Often needs best-available tag selection rather than exact summation |
| `sbc_M` | `ShareBasedCompensation` | `ShareBasedPaymentExpense` | Optional second phase |

## Design Decisions

### D1: Store new raw metrics in the existing annual and quarterly entries

Do not create a second SEC dataset for these metrics. The existing company JSON is already the right aggregation boundary.

### D2: Keep derived metrics out of JSON

Continue the existing repo convention:
- store raw `capex_M`, `operating_cash_flow_M`, `cash_M`, `total_debt_M`
- compute `free_cash_flow_M`, `net_cash_M`, `capex_intensity`, and similar metrics in the helper

### D3: Support both duration and instant facts

The current extractor assumes duration-based facts keyed by `end == period_end`.
V2 needs two extraction modes:
- **Duration mode** for capex and operating cash flow
- **Instant mode** for cash and debt, keyed to the period-end balance-sheet date

### D4: Prefer coverage and consistency over aggressive compositing

For V1:
- `cash_M` should mean cash and cash equivalents, not a custom rollup of every liquid asset
- `total_debt_M` should be best-effort and nullable

This keeps extraction rules understandable and avoids overfitting company-specific balance sheets.

### D5: Accept weaker debt coverage for financial institutions

Debt concepts are less comparable for banks and insurers. `total_debt_M` may be `null` for some filers, and that is acceptable.

## Schema

Top-level structure stays the same. New fields are added to each entry when available.

```json
{
  "cik": "0000789019",
  "name": "Microsoft Corporation",
  "last_refreshed": "2026-04-03",
  "annual": [
    {
      "period_end": "2025-06-30",
      "filing_date": "2025-07-30",
      "form": "10-K",
      "namespace": "us-gaap",
      "currency": "USD",
      "revenue_M": 281724,
      "rnd_M": 32488,
      "cost_of_revenue_M": 87831,
      "net_income_M": 101832,
      "capex_M": 24000,
      "operating_cash_flow_M": 130000,
      "cash_M": 79000,
      "total_debt_M": 42000,
      "tags_used": {
        "revenue": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "capex": "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        "operating_cash_flow": "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "cash": "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "total_debt": "us-gaap:LongTermDebtAndFinanceLeaseObligations"
      }
    }
  ],
  "quarterly": []
}
```

## Data Flow

```
CIK
 ↓
Submissions API → all 10-K / 10-Q / 20-F filings + filing dates + period ends
 ↓
CompanyFacts API → metric extraction by period end
 ↓
Metric mode routing:
  - duration metrics: revenue, R&D, COGS, NI, capex, OCF
  - instant metrics: cash, debt
 ↓
Tag resolution:
  preferred list → best match → YAML override
 ↓
Write sec/financials/{cik}.json
```

## Helper Additions

Add derived methods to `sec_financials.py`:
- `free_cash_flow(cik)` → latest annual `operating_cash_flow_M - capex_M`
- `net_cash(cik)` → latest annual or quarterly `cash_M - total_debt_M`
- `capex_intensity(cik)` → `capex_M / revenue_M`
- `operating_cash_flow_margin(cik)` → `operating_cash_flow_M / revenue_M`

These should return `None` when required raw fields are missing.

## Validation

Extend `tests/test_sec.py` to check:
- new fields are numeric or `null`
- annual and quarterly arrays remain sorted descending
- point-in-time metrics are not accidentally written into duration fields
- files remain parseable and fresh

## Implementation Steps

| # | Step | Effort |
|---|---|---|
| 1 | Add V2 design doc | Low |
| 2 | Expand metric tag registry in `sec/scripts/refresh.py` | Medium |
| 3 | Add instant-metric extraction path for cash and debt | Medium |
| 4 | Add helper methods for FCF, net cash, and intensity metrics | Low |
| 5 | Extend validation tests for the new fields | Low |
| 6 | Refresh a small pilot set of companies first (`MSFT`, `NVDA`, `ADBE`, `SAP`) | Low |
| 7 | Review coverage and tune tag priorities / overrides | Medium |
| 8 | Refresh all companies | Low |
| 9 | Update README and changelog | Low |

## Rollout Notes

Recommended pilot companies:
- `MSFT` for broad coverage and segment context
- `NVDA` for AI-capex and cash-generation relevance
- `ADBE` for software-style reporting
- `SAP` for IFRS coverage

Start with Phase 1 only. Add `sbc_M` only after the core metrics have acceptable coverage and clean tag behavior.

## Consumer Usage

```python
from sec_financials import SECFinancials

sec = SECFinancials(local_dir="sec/financials")

latest = sec.latest_annual("0001045810")
fcf = sec.free_cash_flow("0001045810")
capex_intensity = sec.capex_intensity("0001045810")
net_cash = sec.net_cash("0000789019")
```
