# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.0.0] - 2026-03-29

### Added
- **SEC EDGAR integration** — Submissions API + CompanyFacts API pipeline
- **27 companies** from top 50 Azure ACR customers, seeded with full XBRL history
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
- 25/27 companies have annual data (TD Bank and Manulife: XBRL period-end mismatch)
- 23/27 companies have quarterly data
- Adobe: 9 annual periods (FY2017–FY2025) + 25 quarterly periods
- Total data: 27 JSON files, ~236KB
