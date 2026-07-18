# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
HOW TO USE THIS FILE
====================
Every PR (except `noncodefix/*`, `spike/*`, `release/*` branches) should add at
least one row under `## [Unreleased]`.

Pick the right section:
  Added      — new features
  Changed    — changes in existing functionality
  Deprecated — soon-to-be-removed features
  Removed    — now-removed features
  Fixed      — bug fixes
  Security   — vulnerabilities
-->

## [Unreleased]

### Added
- **SEC Phase 4 tag expansion** — 3 new XBRL tags: `RevenueFromContractWithCustomerIncludingAssessedTax` (revenue), `ProfitLoss` in us-gaap (net_income), `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` (OCF). Fixes revenue for TJX/KHC/AKAM/RH/VRNS, net income for CAT/CMI/MA/BSX/F, OCF for BDX/JCI/DD/FIS/NWSA.
- **EDINET balance sheet/cash flow expansion** — `refresh_edinet.py` now extracts 9 metrics (was 5): added `cash_M`, `total_assets_M`, `capex_M`, `operating_cash_flow_M` from XBRL. Added EBIT fallback for `operating_income_M` (Hitachi uses EBIT). Added `INSTANT_METRICS` set for balance sheet items (instant vs duration context). Coverage: total_assets 100%, operating_cash_flow 100%, capex 93%, cash 86%.
- **INTL metric expansion** — `refresh_intl.py` now extracts 11 metrics (was 4) from Yahoo Finance: added `operating_income_M`, `sga_M`, `capex_M`, `operating_cash_flow_M`, `cash_M`, `total_debt_M`, `total_assets_M` from balance sheet and cash flow statements. Coverage: capex 97%, cash 99.5%, total_debt 98%, total_assets 100%, operating_cash_flow 98%, sga 78%, operating_income 77%.
- **INTL quarterly merge** — merge logic now handles quarterly data (was annual-only).

### Changed
- **FRED macro refresh** — 21/22 series refreshed. `CUSR0000SEEE` (IT CPI) hit transient HTTP 500 from FRED server.

### Fixed
- **INTL all-null company fix** — skip income statement columns where all financial metrics are NaN (yfinance creates placeholder columns for unreported future periods). Also filter stale all-null entries during merge. Fixes Commerzbank, Tesco, Xiaomi.
- **INTL OCF fallback label** — added `Cash Flowsfromusedin Operating Activities Direct` as fallback for `Operating Cash Flow`. Fixes ~9 Australian and European companies (Woolworths, Telefónica, Sonae, etc.).
- **SEC test runner** — test functions now return error lists instead of using `assert` (same fix as INTL/EDINET tests).
- **EDINET test runner** — test functions now return error lists instead of using `assert` (same fix as INTL tests).
- **INTL test runner** — test functions now return error lists instead of using `assert` (broke `main()` harness which expects return values).

### Removed
- **19 orphan INTL files** — removed legacy files not in registry (`AE_FAB`, `CA_THOMSON`, `NL_WOLTERS`, and 16 ISIN-format files from pre-registry era or EDINET overlaps).

### Added
- **Top 1000 coverage design** — `docs/design/top-1000-coverage.md` with 5-phase plan covering SEC, intl, and EDINET scaling. Estimated realistic ceiling: ~525 coverable out of top 1000.
- **SEC bulk CIK lookup** — `sec/scripts/lookup_cik.py` for verifying CIK↔ticker associations using SEC's `company_tickers.json`. Supports `--verify-mapping`, `--verify-registry`, and `--search` modes. Includes alias table for common name divergences (UPS, IBM, BNY Mellon, etc.).
- **62 new SEC companies** — Meta, Salesforce, Cisco, Costco, JPMorgan, AMD, Palantir, Datadog, Rubrik, UiPath, DocuSign, Kyndryl, Blackstone, BlackRock, FedEx, UPS, Moody's, Allstate, NICE, CGI, Lumen, and 41 more from tpid-cik-mapping. SEC company count: 134 → 196.
- **28 new international companies** — LSEG, AXA, Allianz, Bayer, ASML, Munich Re, ABN AMRO, Telefónica, Ahold Delhaize, ABB, Sage, Capgemini, Philips, Commerzbank, Repsol, Inditex, Iberdrola, Société Générale, LVMH, Deutsche Post, Volvo, BASF, L'Oréal, Marks & Spencer, Poste Italiane, Heineken, and more via Yahoo Finance. Intl company count: 11 → 39.
- **10 new EDINET companies** — SMFG, Rakuten, AEON, SoftBank, Nissan, Panasonic, Sony, Kubota, MUFG, FUJIFILM. EDINET company count: 4 → 14.
- **J-GAAP tag support in EDINET** — added `jppfs_cor:NetSales`, `jppfs_cor:OperatingRevenue1`, `jppfs_cor:OrdinaryIncome`, `jppfs_cor:OrdinaryIncomeBNK` (bank-specific), `jpigp_cor:NetSalesIFRS`, plus J-GAAP net income and cost of sales tags. Now supports companies reporting under both IFRS and Japanese GAAP.
- **EDINET Financials module** — 4 Japanese companies (NTT, Hitachi, NEC, Fujitsu) via EDINET API V2 + iXBRL parsing. Keyed by EDINET Code. Revenue, operating income, net income in JPY (millions). 6–7 annual periods per company (FY2019–FY2025). Helper: `edinet_financials.py`. Tests: `test_edinet.py` (7 checks). GitHub Action: quarterly refresh on 25th. First repo module with custom XBRL parser.
- **International Financials module** — 4 European companies (BMW, Siemens, Mercedes-Benz, Volkswagen) via Yahoo Finance. Keyed by ISIN. Revenue, R&D (where disclosed), COGS, net income in EUR. Helper: `intl_financials.py`. Tests: `test_intl.py` (7 checks). GitHub Action: quarterly refresh on 20th.
- **Alibaba (BABA)** — added to SEC module (CIK `0001577552`). Active 20-F filer on NYSE. 12 annual periods (FY2015–FY2025), currency CNY. SEC company count: 28 → 29.
- **ADR-004** — source-native keys per module (CIK for SEC, ISIN for intl, EDINET Code for edinet, FRED series ID for macro)
- **ADR-005** — Yahoo Finance for European data (Bundesanzeiger has no API, filings.xbrl.org excludes Germany, FMP free tier paywalls non-US exchanges)
- **Non-SEC filers design doc** — covers EDINET (Japan, implemented), Yahoo Finance (Europe, implemented), private companies (deferred). `docs/design/non-sec-filers.md`
- **FRED Macro Indicators** — 18 series total: GDP, CPI (all items + IT), PPI Data Processing, employment (civilian + tech sector), Federal Funds Rate, 2Y/10Y Treasury rates, S&P 500, NASDAQ, EUR/CAD/JPY/CHF FX rates, Unemployment Rate, Initial Claims, Baa credit spread. Full history, monthly refresh.
- **Macro helper enhancements** — added `observation()`, `spread()`, and `fx_usd_per_local()` for date-aligned comparisons and normalized FX reads
- **SEC segment extraction** — `refresh_segments.py` extracts dimensional XBRL segment revenue (Microsoft: Intelligent Cloud, Productivity & Business Processes, More Personal Computing). Stored in `{cik}_segments.json` with separate schema.
- **SEC Financials V2 design** — proposed next iteration covering capex, operating cash flow, cash, and debt in `docs/design/sec-financials-v2.md`
- **New datasets assessment** — evaluated 11 candidate public datasets, prioritized by value and effort in `docs/design/new-datasets-assessment.md`

### Fixed
- **EDINET XBRL parser** — `ix:nonFraction` regex now handles attributes in any order (was assuming `name` before `contextRef`, broke on Rakuten/Panasonic/Sony filings where `contextRef` appears first).
- **EDINET code corrections** — Rakuten was E05765 (subsidiary), corrected to E05080 (parent group). Kubota was E01144 (wrong entity), corrected to E01267.
- **EDINET filing scan window** — extended from Jun/Jul only to Mar–Jul, catching Dec 31 and Feb 28 fiscal year-end companies.
- **SEC registry YAML octal corruption** — 14 CIK keys with only digits 0–7 were silently interpreted as octal numbers by YAML parser (e.g., `0000006201` → decimal 3201). All CIK keys now quoted where needed.
- **6 wrong auto-discovered CIK matches** — UPS→UPST, Allstate→WTM, Moody's→IWSH, Lumen→ROP, NICE→ESLT, CGI→GS. Corrected to UPS→0001090727, ALL→0000899051, MCO→0001059556, LUMN→0000018926, NICE→0001003935, GIB→0001061574.
- **Removed 5 CIKs with no XBRL on EDGAR** — Wolters Kluwer, Deutsche Lufthansa, E.ON, H&M, Feitu Shanglian (foreign filers that no longer have XBRL data).
- **SEC test harness** — excluded `_segments.json` from standard validators (different schema); null-revenue check is now a warning for known IFRS bank filers (UBS)
- **Documentation audit (2026-04-03)** — found and resolved 10 gaps between code and docs:
  - SEC segments were completely undocumented (script, data file, registry config existed since 2026-03-29 with zero mentions in README, copilot-instructions, CHANGELOG, or execution log)
  - CHANGELOG said "27 companies" (actually 28)
  - CHANGELOG [Unreleased] listed FRED additions as three fragmented lines (consolidated to single "18 series" entry)
  - copilot-instructions missing `segment_tags` convention, segment data flow, and helper sync guidance
  - README data flow still referenced `{tpid}` (should be `{cik}`)
  - Design doc `macro-indicators.md` showed 6 series with no note about expansion to 18
  - Execution log missing sessions for segment implementation and macro expansion
  - All gaps now resolved — see `docs/history/execution-log.md` for details

### Known Issues
- **UBS (0001610520)** — all annual entries have `revenue_M: null`. UBS is an IFRS bank that reports interest/fee/trading income separately; none map to standard XBRL revenue tags. Flagged as warning, not error.
- **SEC segments** — feature works but has gaps: no helper methods for reading segment data, no dedicated tests for segment file schema, no GitHub Action for segment refresh. See roadmap.
- **Helper module duplication** — `{module}/scripts/*.py` and `helpers/*.py` are manual copies. No automated sync. Convention documented in copilot-instructions but still fragile.

## [1.0.0] - 2026-03-29

### Added
- **SEC EDGAR integration** — Submissions API + CompanyFacts API pipeline
- **28 companies** from top 50 Azure ACR customers, seeded with full XBRL history
- **us-gaap support** — 10-K (annual) and 10-Q (quarterly) domestic filers
- **ifrs-full support** — 20-F foreign private issuers (SAP, UBS, TD Bank, Shell, Manulife, Toyota)
- **Multi-currency extraction** — USD, EUR, CAD, JPY, CHF (picks most recent data regardless of currency)
- **Period-end anchored extraction** — uses filing `reportDate` from Submissions API, not CY calendar frames
- **Duration disambiguation** — correctly separates single-quarter from YTD entries on 10-Q filings
- **3-layer tag resolution** — preferred tag list → auto-select best match → YAML `tag_overrides`
- **Per-company JSON storage** — `sec/financials/{cik}.json` with full annual + quarterly history
- **YAML registry** — `sec/registry.yaml` with company metadata only (no financial data)
- **Python helper** — `sec/scripts/sec_financials.py` with `get()`, `latest_annual()`, `yoy_revenue_growth()`, `rnd_intensity()`, `revenue_trend()`
- **GitHub Action** — quarterly auto-refresh (Jan/Apr/Jul/Oct 15) + manual dispatch per CIK
- **Agent instructions** — `.github/copilot-instructions.md` with conventions and boundaries
- **ADRs** — 3 initial architectural decision records (storage split, IFRS, separate repo)

### Coverage
- 26/28 companies have annual data (TD Bank and Manulife: XBRL period-end mismatch; UBS: revenue tags not mapped)
- 23/28 companies have quarterly data
- Adobe: 9 annual periods (FY2017–FY2025) + 25 quarterly periods
- Total data: 28 standard JSON files + 1 segment file, ~236KB
