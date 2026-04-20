# EDINET Financials (Japan) — Data Dictionary

## Source

[EDINET API V2](https://disclosure2.edinet-fsa.go.jp/) — Japan Financial Services Agency.
Parses iXBRL from 有価証券報告書 (Annual Securities Reports).
Requires `EDINET_API_KEY` environment variable (free registration).

## File Layout

- **Registry:** `edinet/registry.yaml` — company metadata, keyed by EDINET code
- **Financial data:** `edinet/financials/{edinet_code}.json` — one file per company
- **Refresh script:** `edinet/scripts/refresh_edinet.py`
- **Helper module:** `edinet/scripts/edinet_financials.py` (also `helpers/edinet_financials.py`)

## JSON Schema

### File-level fields

| Field | Type | Description |
|---|---|---|
| `edinet_code` | `string` | EDINET entity code (e.g., `E04430`) — Japan FSA's primary identifier |
| `name` | `string` | Company name |
| `ticker` | `string` | Tokyo Stock Exchange ticker number (e.g., `9432` for NTT) |
| `exchange` | `string` | Stock exchange (always `TSE` for current coverage) |
| `last_refreshed` | `string` | ISO date (`YYYY-MM-DD`) of last data refresh |
| `annual` | `array` | Annual entries only (no quarterly), sorted descending by `period_end` |

### Entry-level fields (each item in `annual[]`)

| Field | Type | Unit | Description |
|---|---|---|---|
| `period_end` | `string` | — | Fiscal year end date (`YYYY-MM-DD`) |
| `filing_date` | `string` | — | Date the filing was submitted to EDINET (`YYYY-MM-DD`) |
| `form` | `string` | — | Always `有価証券報告書` (Annual Securities Report) |
| `namespace` | `string` | — | XBRL namespace: `jpigp_cor` (IFRS), `jppfs_cor` (J-GAAP), or company-specific |
| `currency` | `string` | — | Always `JPY` for current coverage |
| `revenue_M` | `int \| null` | Millions JPY | Total revenue / net sales / operating revenue. See [XBRL tag mapping](#xbrl-tag-mapping) for tag resolution by accounting standard. |
| `operating_income_M` | `int \| null` | Millions JPY | Operating income (profit/loss). |
| `net_income_M` | `int \| null` | Millions JPY | Net income attributable to owners of parent. Negative values = net loss. |
| `cost_of_revenue_M` | `int \| null` | Millions JPY | Cost of sales. Extracted but often `null` — many Japanese companies don't report this in iXBRL. |
| `rnd_M` | `int \| null` | Millions JPY | R&D expense. Extracted but rarely disclosed in iXBRL — `null` for most companies. |
| `cash_M` | `int \| null` | Millions JPY | Cash and cash equivalents (balance sheet, instant context). |
| `total_assets_M` | `int \| null` | Millions JPY | Total assets (balance sheet, instant context). Usually from summary section. |
| `capex_M` | `int \| null` | Millions JPY | Capital expenditures (cash flow / overview section). |
| `operating_cash_flow_M` | `int \| null` | Millions JPY | Net cash from operating activities (cash flow statement). |
| `tags_used` | `object \| absent` | — | Map of `{metric_name: "namespace:TagName"}` showing which XBRL tag resolved. **Included on the first entry only.** |

### Null semantics

A value of `null` means the XBRL tag was not found in the company's iXBRL filing. Common cases:
- `cost_of_revenue_M` — many IFRS reporters don't tag cost of sales separately
- `rnd_M` — only a handful of companies tag R&D expense in XBRL (most disclose it in notes only)
- `operating_income_M` — some companies (e.g., financial sector) don't report operating income; Hitachi reports EBIT instead

`null` ≠ zero. Display as "Not disclosed" in reports.

### Quarterly data

EDINET extraction currently covers **annual filings only** (有価証券報告書, doc type 120). Quarterly reports (四半期報告書, doc type 140) are not extracted.

## XBRL Tag Mapping

Japanese filings use multiple accounting standards. Tags are resolved in priority order (first match wins).

### revenue_M

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `RevenueIFRS` | IFRS |
| 2 | `jpigp_cor` | `OperatingRevenueIFRS` | IFRS |
| 3 | `jpigp_cor` | `NetSalesIFRS` | IFRS |
| 4 | company-specific | `OperatingRevenuesIFRS` | IFRS (e.g., NTT) |
| 5 | company-specific | `RevenueIFRS` | IFRS |
| 6 | company-specific | `RevenueFromContractsWithCustomersIFRS` | IFRS |
| 7 | company-specific | `NetSalesIFRS` | IFRS |
| 8 | `jppfs_cor` | `NetSales` | J-GAAP |
| 9 | `jppfs_cor` | `OperatingRevenue1` | J-GAAP |
| 10 | `jppfs_cor` | `OrdinaryIncomeBNK` | J-GAAP (banks) |
| 11 | `jppfs_cor` | `OrdinaryIncome` | J-GAAP |
| 12 | `jpcrp_cor` | `NetSalesSummaryOfBusinessResults` | Summary |
| 13 | `jpcrp_cor` | `OperatingRevenue1SummaryOfBusinessResults` | Summary |
| 14 | `jpcrp_cor` | `RevenueIFRSSummaryOfBusinessResults` | Summary |
| 15 | `jpcrp_cor` | `OrdinaryIncomeSummaryOfBusinessResults` | Summary |

### operating_income_M

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `OperatingProfitLossIFRS` | IFRS |
| 2 | company-specific | `OperatingProfitLossIFRS` | IFRS |
| 3 | company-specific | `EBITEarningsBeforeInterestAndTaxesIFRS` | IFRS (e.g., Hitachi) |
| 4 | `jppfs_cor` | `OperatingIncome` | J-GAAP |
| 5 | `jpcrp_cor` | `OperatingIncomeSummaryOfBusinessResults` | Summary |

### net_income_M

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `ProfitLossAttributableToOwnersOfParentIFRS` | IFRS |
| 2 | `jpigp_cor` | `ProfitLossIFRS` | IFRS |
| 3 | company-specific | `ProfitLossAttributableToOwnersOfParentIFRS` | IFRS |
| 4 | `jppfs_cor` | `ProfitLossAttributableToOwnersOfParent` | J-GAAP |
| 5 | `jppfs_cor` | `NetIncome` | J-GAAP |
| 6 | `jpcrp_cor` | `ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults` | Summary |

### cost_of_revenue_M

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `CostOfSalesIFRS` | IFRS |
| 2 | company-specific | `CostOfSalesIFRS` | IFRS |
| 3 | `jppfs_cor` | `CostOfSales` | J-GAAP |

### rnd_M

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `ResearchAndDevelopmentExpenseIFRS` | IFRS |
| 2 | company-specific | `ResearchAndDevelopmentExpenseIFRS` | IFRS |
| 3 | `jpcrp_cor` | `ResearchAndDevelopmentActivitiesTextBlock` | Summary |

### cash_M (instant context — balance sheet)

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `CashAndCashEquivalentsIFRS` | IFRS |
| 2 | company-specific | `CashAndCashEquivalentsIFRS` | IFRS |
| 3 | `jppfs_cor` | `CashAndDeposits` | J-GAAP |
| 4 | `jpcrp_cor` | `CashAndCashEquivalentsIFRSSummaryOfBusinessResults` | Summary |

### total_assets_M (instant context — balance sheet)

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpcrp_cor` | `TotalAssetsIFRSSummaryOfBusinessResults` | Summary (IFRS) |
| 2 | `jpcrp_cor` | `TotalAssetsSummaryOfBusinessResults` | Summary (J-GAAP) |
| 3 | `jpigp_cor` | `TotalAssetsIFRS` | IFRS |
| 4 | company-specific | `TotalAssetsIFRS` | IFRS |
| 5 | `jppfs_cor` | `TotalAssets` | J-GAAP |

### capex_M (duration context — cash flow / overview)

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `CapitalExpendituresIFRS` | IFRS |
| 2 | company-specific | `CapitalExpendituresIFRS` | IFRS |
| 3 | `jpcrp_cor` | `CapitalExpendituresOverviewOfCapitalExpendituresEtc` | Summary |
| 4 | `jppfs_cor` | `PurchaseOfPropertyPlantAndEquipmentAndIntangibleAssets` | J-GAAP |

### operating_cash_flow_M (duration context — cash flow)

| Priority | Namespace | Tag | Standard |
|---|---|---|---|
| 1 | `jpigp_cor` | `NetCashProvidedByUsedInOperatingActivitiesIFRS` | IFRS |
| 2 | company-specific | `NetCashProvidedByUsedInOperatingActivitiesIFRS` | IFRS |
| 3 | `jpcrp_cor` | `CashFlowsFromUsedInOperatingActivitiesIFRSSummaryOfBusinessResults` | Summary (IFRS) |
| 4 | `jpcrp_cor` | `CashFlowsFromOperatingActivitiesSummaryOfBusinessResults` | Summary (J-GAAP) |
| 5 | `jppfs_cor` | `NetCashProvidedByUsedInOperatingActivities` | J-GAAP |

## Japanese accounting standard context

Japanese public companies may report under:
- **IFRS** — namespace `jpigp_cor` (most large internationals: NTT, Hitachi, Sony, SoftBank)
- **J-GAAP** — namespace `jppfs_cor` (some domestically focused companies)
- **Company-specific** — custom namespaces for non-standard IFRS tags (e.g., NTT uses its own namespace for `OperatingRevenuesIFRS`)

The tag resolution cascade handles all three, falling back to summary tags (`jpcrp_cor`) as a last resort.

### Context types

Balance sheet metrics (`cash_M`, `total_assets_M`) use **instant** context (`CurrentYearInstant`).
All other metrics use **duration** context (`CurrentYearDuration`).

## Registry Schema (`edinet/registry.yaml`)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Company name |
| `ticker` | `string` | Yes | Tokyo Stock Exchange ticker number |
| `exchange` | `string` | Yes | Stock exchange (currently `TSE` for all) |
| `currency` | `string` | Yes | Reporting currency (currently `JPY` for all) |

## Coverage

14 Japanese companies across technology, financials, automotive, and consumer sectors:

| EDINET Code | Company | Sector |
|---|---|---|
| `E04430` | NTT | Telecommunications |
| `E01737` | Hitachi | Conglomerate / IT |
| `E01765` | NEC | IT / Telecommunications |
| `E01766` | Fujitsu | IT Services |
| `E01777` | Sony | Electronics / Entertainment |
| `E01772` | Panasonic | Electronics |
| `E02778` | SoftBank Group | Telecommunications / Investment |
| `E05080` | Rakuten | E-commerce / Fintech |
| `E02142` | Nissan | Automotive |
| `E01267` | Kubota | Machinery |
| `E03606` | Mitsubishi UFJ FG | Banking |
| `E03674` | Sumitomo Mitsui FG | Banking |
| `E00334` | FUJIFILM | Imaging / Healthcare |
| `E03498` | AEON | Retail |
