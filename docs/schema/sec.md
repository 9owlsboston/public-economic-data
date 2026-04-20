# SEC EDGAR — Data Dictionary

## Source

[SEC EDGAR XBRL](https://www.sec.gov/edgar/searchedgar/companysearch) via CompanyFacts and Submissions APIs.
Supports `us-gaap` (10-K/10-Q domestic filers) and `ifrs-full` (20-F foreign private issuers).

## File Layout

- **Registry:** `sec/registry.yaml` — company metadata, keyed by CIK
- **Standard financials:** `sec/financials/{cik}.json` — one file per company
- **Segment financials:** `sec/financials/{cik}_segments.json` — segment-level revenue (separate schema)
- **Refresh script:** `sec/scripts/refresh.py`
- **Helper module:** `sec/scripts/sec_financials.py` (also `helpers/sec_financials.py`)

## Standard Financials Schema

### File-level fields

| Field | Type | Description |
|---|---|---|
| `cik` | `string` | SEC Central Index Key — 10-digit zero-padded identifier |
| `name` | `string` | Company legal name from SEC |
| `last_refreshed` | `string` | ISO date (`YYYY-MM-DD`) of last data refresh |
| `annual` | `array` | Annual filing entries (10-K, 20-F), sorted descending by `period_end` |
| `quarterly` | `array` | Quarterly filing entries (10-Q), sorted descending by `period_end` |

### Entry-level fields (each item in `annual[]` or `quarterly[]`)

| Field | Type | Unit | Description |
|---|---|---|---|
| `period_end` | `string` | — | Fiscal period end date (`YYYY-MM-DD`). Matches SEC `reportDate`. |
| `filing_date` | `string` | — | Date the filing was submitted to SEC (`YYYY-MM-DD`). |
| `form` | `string` | — | SEC form type: `10-K`, `10-Q`, `20-F`, or `40-F`. Amended forms (`/A`) are normalized (suffix stripped), with `amended: true` flag. |
| `namespace` | `string` | — | XBRL taxonomy namespace used: `us-gaap` or `ifrs-full`. Determined from the revenue tag's namespace. |
| `currency` | `string` | — | ISO 4217 currency code for all monetary values in this entry (usually `USD`). |
| `revenue_M` | `int \| null` | Millions | Total revenue. See [XBRL tag mapping](#xbrl-tag-mapping) for tag resolution. |
| `rnd_M` | `int \| null` | Millions | Research & development expense. `null` when the company does not disclose R&D as a separate line item. |
| `cost_of_revenue_M` | `int \| null` | Millions | Cost of revenue / cost of goods sold. |
| `net_income_M` | `int \| null` | Millions | Net income (loss) attributable to the entity. Negative values = net loss. |
| `capex_M` | `int \| null` | Millions | Capital expenditures (payments to acquire property, plant & equipment). Always positive in source data. |
| `operating_cash_flow_M` | `int \| null` | Millions | Net cash from operating activities. |
| `operating_income_M` | `int \| null` | Millions | Operating income (loss). `null` for financial sector companies and some energy/industrial filers. |
| `sga_M` | `int \| null` | Millions | Selling, general & administrative expense. Falls back to G&A-only when full SG&A is not reported. |
| `cash_M` | `int \| null` | Millions | Cash & cash equivalents (balance sheet, point-in-time as of `period_end`). |
| `total_debt_M` | `int \| null` | Millions | Long-term debt. Tags include `LongTermDebt`, `LongTermDebtNoncurrent`, and `LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities` — does **not** include short-term borrowings. |
| `total_assets_M` | `int \| null` | Millions | Total assets (balance sheet). |
| `amended` | `bool` | — | Present and `true` only for amended filings (10-K/A, 20-F/A). Omitted for original filings. |
| `tags_used` | `object \| absent` | — | Map of `{metric_name: "namespace:TagName"}` showing which XBRL tag resolved for each metric. **Included on the first entry per scope only** (to avoid bloat). |

### Null semantics

A value of `null` means the XBRL tag was not found in the company's filings. This typically means:
- The company does not disclose the metric as a separate line item (e.g., many non-tech companies omit `rnd_M`)
- The specific XBRL tag didn't match any entry in the CompanyFacts API for that period

`null` ≠ zero. Display as "Not disclosed" in reports.

### Duration vs instant metrics

| Category | Metrics | How matched |
|---|---|---|
| **Duration** (income statement, cash flow) | `revenue_M`, `rnd_M`, `cost_of_revenue_M`, `net_income_M`, `capex_M`, `operating_cash_flow_M`, `operating_income_M`, `sga_M` | Matched by `end` date = `period_end`. For quarterly: shortest duration; for annual: longest duration. |
| **Instant** (balance sheet) | `cash_M`, `total_debt_M`, `total_assets_M` | Matched by `end` date = `period_end`, no start date. Point-in-time snapshot. |

### Filing deduplication

Both original and amended filings are kept (different `filing_date` for the same `period_end`). The helper's `latest_annual()` method picks the entry with the latest `filing_date` when duplicates exist.

## XBRL Tag Mapping

Tags are resolved in priority order (first match wins). Companies can override via `tag_overrides` in `sec/registry.yaml`.

### us-gaap tags

| Metric | Priority 1 | Priority 2 | Priority 3 | Priority 4 | Priority 5 |
|---|---|---|---|---|---|
| `revenue_M` | `Revenues` | `RevenueFromContractWithCustomerExcludingAssessedTax` | `SalesRevenueNet` | — | — |
| `rnd_M` | `ResearchAndDevelopmentExpense` | `ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost` | — | — | — |
| `cost_of_revenue_M` | `CostOfRevenue` | `CostOfGoodsAndServicesSold` | `CostOfGoodsSold` | — | — |
| `net_income_M` | `NetIncomeLoss` | — | — | — | — |
| `capex_M` | `PaymentsToAcquirePropertyPlantAndEquipment` | `PaymentsToAcquireProductiveAssets` | `PaymentsForCapitalImprovements` | `PaymentsToAcquireOtherProductiveAssets` | `PaymentsToAcquireOtherPropertyPlantAndEquipment` |
| `operating_cash_flow_M` | `NetCashProvidedByUsedInOperatingActivities` | — | — | — | — |
| `operating_income_M` | `OperatingIncomeLoss` | — | — | — | — |
| `sga_M` | `SellingGeneralAndAdministrativeExpense` | `GeneralAndAdministrativeExpense` | — | — | — |
| `cash_M` | `CashAndCashEquivalentsAtCarryingValue` | `CashCashEquivalentsAndShortTermInvestments` | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | — | — |
| `total_debt_M` | `LongTermDebt` | `LongTermDebtAndCapitalLeaseObligations` | `LongTermDebtNoncurrent` | `LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities` | — |
| `total_assets_M` | `Assets` | — | — | — | — |

### ifrs-full tags

| Metric | Priority 1 | Priority 2 |
|---|---|---|
| `revenue_M` | `Revenue` | `RevenueFromContractsWithCustomers` |
| `rnd_M` | `ResearchAndDevelopmentExpense` | — |
| `cost_of_revenue_M` | `CostOfSales` | — |
| `net_income_M` | `ProfitLossAttributableToOwnersOfParent` | `ProfitLoss` |
| `capex_M` | `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` | `PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets` |
| `operating_cash_flow_M` | `CashFlowsFromUsedInOperatingActivities` | — |
| `operating_income_M` | `ProfitLossFromOperatingActivities` | — |
| `sga_M` | `SellingGeneralAndAdministrativeExpense` | — |
| `cash_M` | `CashAndCashEquivalents` | `CashAndCashEquivalentsIfDifferentFromStatementOfFinancialPosition` |
| `total_debt_M` | `Borrowings` | `NoncurrentFinancialLiabilities` |
| `total_assets_M` | `Assets` | — |

## Segment Financials Schema

Segment files use a different schema from standard financials. Currently Microsoft only.

### File-level fields

| Field | Type | Description |
|---|---|---|
| `cik` | `string` | SEC CIK |
| `company` | `string` | Company name |
| `last_refreshed` | `string` | ISO date of last refresh |
| `segments` | `object` | Map of `{segment_key: entries[]}` |

### Segment entry fields

| Field | Type | Unit | Description |
|---|---|---|---|
| `period_end` | `string` | — | Fiscal period end date (`YYYY-MM-DD`) |
| `form` | `string` | — | `10-K` or `10-Q` |
| `start` | `string` | — | Period start date |
| `end` | `string` | — | Period end date (same as `period_end`) |
| `revenue` | `float` | Full units | Segment revenue in full units (not millions). Extracted from inline XBRL dimensional contexts. |
| `tag` | `string` | — | XBRL tag used (e.g., `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`) |

**Note:** Segment revenue is in **full units** (not millions), unlike standard financials. Consumers must divide by 1,000,000 for consistency.

## Registry Schema (`sec/registry.yaml`)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Company legal name |
| `ticker` | `string` | Yes | Stock ticker symbol |
| `exchange` | `string` | No | Stock exchange (e.g., `NYSE`, `NASDAQ`) |
| `tag_overrides` | `object` | No | Map of `{metric_tag: "namespace:TagName"}` to override default tag resolution |
| `segment_tags` | `object` | No | Segment member names for segment extraction (e.g., `intelligent_cloud: "msft:IntelligentCloudMember"`) |
