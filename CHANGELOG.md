# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **FRED Macro Indicators** — 18 series total: GDP, CPI (all items + IT), PPI Data Processing, employment (civilian + tech sector), Federal Funds Rate, 2Y/10Y Treasury rates, S&P 500, NASDAQ, EUR/CAD/JPY/CHF FX rates, Unemployment Rate, Initial Claims, Baa credit spread. Full history, monthly refresh.
- **Macro helper enhancements** — added `observation()`, `spread()`, and `fx_usd_per_local()` for date-aligned comparisons and normalized FX reads
- **SEC segment extraction** — `refresh_segments.py` extracts dimensional XBRL segment revenue (Microsoft: Intelligent Cloud, Productivity & Business Processes, More Personal Computing). Stored in `{cik}_segments.json` with separate schema.
- **SEC Financials V2 design** — proposed next iteration covering capex, operating cash flow, cash, and debt in `docs/design/sec-financials-v2.md`
- **New datasets assessment** — evaluated 11 candidate public datasets, prioritized by value and effort in `docs/design/new-datasets-assessment.md`

### Fixed
- **SEC test harness** — excluded `_segments.json` from standard validators (different schema); null-revenue check is now a warning for known IFRS bank filers (UBS)
- **Documentation audit (2026-04-03)** — found and resolved 10 gaps between code and docs:
  - SEC segments were completely undocumented (script, data file, registry config existed since 2026-03-29 with zero mentions in README, copilot-instructions, CHANGELOG, or execution log)
  - CHANGELOG said "27 companies" (actually 28)
  - CHANGELOG [Unreleased] listed FRED additions as three fragmented lines (consolidated to single "18 series" entry)
  - copilot-instructions missing `segment_tags` convention, segment data flow, and helper sync guidance
  - README data flow still referenced `{tpid}` (should be `{cik}`)
  - Design doc `macro-indicators.md` showed 6 series with no note about expansion to 18
  - Execution log missing sessions for segment implementation and macro expansion
  - All gaps now resolved — see `docs/execution-log.md` for details

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
- **Per-company JSON storage** — `sec/financials/{tpid}.json` with full annual + quarterly history
- **YAML registry** — `sec/registry.yaml` with company metadata only (no financial data)
- **Python helper** — `sec/scripts/sec_financials.py` with `get()`, `latest_annual()`, `yoy_revenue_growth()`, `rnd_intensity()`, `revenue_trend()`
- **GitHub Action** — quarterly auto-refresh (Jan/Apr/Jul/Oct 15) + manual dispatch per TPID
- **Agent instructions** — `.github/copilot-instructions.md` with conventions and boundaries
- **ADRs** — 3 initial architectural decision records (storage split, IFRS, separate repo)

### Coverage
- 26/28 companies have annual data (TD Bank and Manulife: XBRL period-end mismatch; UBS: revenue tags not mapped)
- 23/28 companies have quarterly data
- Adobe: 9 annual periods (FY2017–FY2025) + 25 quarterly periods
- Total data: 28 standard JSON files + 1 segment file, ~236KB
