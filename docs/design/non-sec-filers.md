# Design: Non-SEC Filers — International & Private Company Coverage

**Status:** Implemented (P2 + P3); P4 deferred
**Date:** 2026-04-08
**Modules:** `edinet/` (implemented), `intl/` (implemented), n/a (private — deferred)

## Problem

The SEC module covers 29 companies, all of which are US-listed and file 10-K, 10-Q, or 20-F with the SEC. This leaves significant gaps:

1. **Japanese public companies** (NTT, Hitachi, NEC, Fujitsu) — large technology and infrastructure companies with meaningful cloud and AI spending. They file with Japan's FSA via EDINET, not the SEC.
2. **European public companies** (BMW, Siemens, Mercedes-Benz, Volkswagen) — large industrials with growing digital/cloud footprints. They file with national regulators under ESEF/IFRS, not the SEC.
3. **Private companies** (Deloitte, PwC, EY, KPMG, Mars, G42, ByteDance) — no structured public financial data at all.

Without these, the repo cannot benchmark non-US public companies or provide any coverage for major private enterprises.

## Scope

This design doc covers three workstreams at different maturity levels:

| # | Workstream | Target companies | Status |
|---|---|---|---|
| P2 | Japan EDINET module | NTT, Hitachi, NEC, Fujitsu | **Implemented** — EDINET API V2 + iXBRL parser |
| P3 | European company financials | BMW, Siemens, Mercedes-Benz, Volkswagen | **Implemented** — Yahoo Finance via `yfinance` |
| P4 | Private company coverage | Big 4, Mars, G42, ByteDance | Deferred — no viable source |

---

## P2: Japan EDINET Module

### Why

Japan's Financial Services Agency (FSA) operates EDINET — an electronic disclosure system analogous to SEC EDGAR. It has a public REST API (V2), supports XBRL, and provides structured financial data for all Japanese public companies. NTT, Hitachi, NEC, and Fujitsu are all EDINET filers.

### Target Companies

| Company | Ticker (TSE) | EDINET Code | Accounting Standard | Currency | Relevance |
|---|---|---|---|---|---|
| NTT (Nippon Telegraph & Telephone) | 9432 | E04430 | IFRS | JPY | Largest telco/IT services in Japan; major cloud infra customer |
| Hitachi Ltd | 6501 | E01737 | IFRS | JPY | Diversified industrial + IT services; Lumada platform |
| NEC Corporation | 6701 | E01765 | IFRS | JPY | IT services, 5G, public safety; Azure partner |
| Fujitsu Limited | 6702 | E01766 | IFRS | JPY | IT services, mainframes, cloud migration |

All four now report under IFRS. EDINET IFRS filers use the `jpigp_cor` (Japanese IFRS General Purpose) taxonomy, not `ifrs-full` directly. Tags follow a `{ConceptName}IFRS` naming convention (e.g., `ProfitLossAttributableToOwnersOfParentIFRS`). Some companies also use company-specific namespaces for revenue (e.g., `jpcrp030000-asr_E04430-000:OperatingRevenuesIFRS`).

### Data Source

**EDINET API V2**

- **Document list endpoint:** `https://api.edinet-fsa.go.jp/api/v2/documents.json?date={YYYY-MM-DD}&type=2&Subscription-Key={key}`
- **Document download:** `https://api.edinet-fsa.go.jp/api/v2/documents/{docID}?type=1&Subscription-Key={key}` (returns ZIP with XBRL)
- **Auth:** Free subscription key (register at https://disclosure.edinet-fsa.go.jp/)
- **Rate limit:** Undocumented; conservative pacing recommended (1 req/sec)
- **Format:** JSON metadata; XBRL instance documents inside ZIP archives
- **Coverage:** All filings since 2008 (XBRL mandatory since then)

### Key Differences from SEC

| Aspect | SEC EDGAR | EDINET |
|---|---|---|
| Company identifier | CIK (10-digit) | EDINET Code (6-char, e.g., E01737) |
| Fact extraction | CompanyFacts API (pre-parsed JSON) | Raw XBRL in ZIP — must parse ourselves |
| Filing discovery | Submissions API (all filings per CIK) | Documents API (date-range search, filter by EDINET code + form type) |
| Taxonomy | us-gaap / ifrs-full | jppfs-cor (JP-GAAP) / jpigp_cor (IFRS via Japanese taxonomy) |
| Period convention | `reportDate` in submissions | `periodOfReport` in document metadata |

The biggest difference: **SEC provides pre-parsed XBRL facts** via the CompanyFacts API. EDINET does not — we must download XBRL instance documents and parse them ourselves.

### Proposed Schema

Same structure as SEC, keyed by EDINET code instead of CIK:

```json
{
  "edinet_code": "E04430",
  "name": "Nippon Telegraph and Telephone Corporation",
  "ticker": "9432",
  "exchange": "TSE",
  "last_refreshed": "2026-04-08",
  "annual": [
    {
      "period_end": "2025-03-31",
      "filing_date": "2025-06-20",
      "form": "有価証券報告書",
      "namespace": "jpigp_cor",
      "currency": "JPY",
      "revenue_M": 13704727,
      "operating_income_M": 1649571,
      "net_income_M": 1000016,
      "cost_of_revenue_M": null,
      "rnd_M": null,
      "tags_used": {
        "revenue_M": "jpcrp030000-asr_E04430-000:OperatingRevenuesIFRS",
        "operating_income_M": "jpigp_cor:OperatingProfitLossIFRS",
        "net_income_M": "jpigp_cor:ProfitLossAttributableToOwnersOfParentIFRS"
      }
    }
  ]
}
```

Notes:
- Japanese fiscal years typically end March 31.
- `有価証券報告書` = Annual Securities Report (equivalent to 10-K).
- `四半期報告書` = Quarterly Securities Report (equivalent to 10-Q). Note: Japan abolished mandatory quarterly reports in April 2024 for most companies — quarterly data may not be available for recent periods.
- R&D and COGS may not be directly available as standalone XBRL tags in IFRS filings — these are often embedded in "expenses by nature" breakdowns. Accept `null` where not extractable.

### Data Flow

```
Registry (edinet_code → company metadata)
  ↓
EDINET Documents API → list filings by date range + type filter
  → Filter: edinetCode matches, docTypeCode = "120" (有価証券報告書)
  ↓
EDINET Document Download → ZIP containing XBRL instance + taxonomy
  ↓
Parse iXBRL HTML files in ZIP
  → Extract facts by jpigp_cor / company-specific IFRS taxonomy tags
  → Map to period_end using context period references
  ↓
Merge with existing JSON (deduplicate, keep history)
  ↓
Write edinet/financials/{edinet_code}.json
```

### Module Structure

```
edinet/
  registry.yaml              # EDINET code → name, ticker, exchange
  financials/
    E04430.json               # NTT
    E01737.json               # Hitachi
    E01765.json               # NEC
    E01766.json               # Fujitsu
  scripts/
    refresh_edinet.py          # Fetch + parse + store
    edinet_financials.py       # Helper for reading
```

### Registry Format

```yaml
version: 1
companies:
  E04430:
    name: Nippon Telegraph and Telephone Corporation
    ticker: '9432'
    exchange: TSE
    currency: JPY
  E01737:
    name: Hitachi, Ltd.
    ticker: '6501'
    exchange: TSE
    currency: JPY
  E01765:
    name: NEC Corporation
    ticker: '6701'
    exchange: TSE
    currency: JPY
  E01766:
    name: Fujitsu Limited
    ticker: '6702'
    exchange: TSE
    currency: JPY
```

### XBRL Tag Candidates (jpigp_cor / company-specific)

| Metric | Actual tags used | Notes |
|---|---|---|
| `revenue_M` | `jpigp_cor:RevenueIFRS`, company-specific `OperatingRevenuesIFRS` | NTT uses company-specific namespace; others may use `jpigp_cor` |
| `operating_income_M` | `jpigp_cor:OperatingProfitLossIFRS` | Available for NEC, Fujitsu, NTT; null for Hitachi |
| `net_income_M` | `jpigp_cor:ProfitLossAttributableToOwnersOfParentIFRS` | Available for all companies |
| `rnd_M` | `jpigp_cor:ResearchAndDevelopmentExpenseIFRS` | Tag exists but returns null for current companies |
| `cost_of_revenue_M` | `jpigp_cor:CostOfSalesIFRS` | Returns null for current companies |

### Macro Dependencies

JPY/USD conversion is already supported via the existing `DEXJPUS` series in the macro module.

### Implementation Steps

1. ✅ Register for EDINET API subscription key
2. ✅ Verify EDINET codes for all four companies
3. ✅ Download one sample ZIP and explore XBRL structure
4. ✅ Build iXBRL HTML parser using regex extraction from `_ixbrl.htm` files
5. ✅ Implement `refresh_edinet.py` with `--dry-run` and `--edinet-code` flags
6. ✅ Write `edinet_financials.py` helper (same interface as `sec_financials.py`)
7. ✅ Copy helper to `helpers/`
8. ✅ Write `tests/test_edinet.py`
9. ✅ Create GitHub Action workflow

### Results (2026-04-08)

| Company | EDINET Code | Periods | Latest Revenue (M JPY) | Latest Net Income (M JPY) |
|---|---|---|---|---|
| NTT | E04430 | 7 | 13,704,727 | 1,000,016 |
| Hitachi | E01737 | 6 | 9,783,370 | 615,724 |
| NEC | E01765 | 7 | 3,423,431 | 175,183 |
| Fujitsu | E01766 | 7 | 3,550,116 | 219,807 |

### Risks & Open Questions

- **XBRL parsing complexity.** ~~SEC's CompanyFacts API does the heavy lifting. For EDINET, we parse raw XBRL.~~ Resolved: built a regex-based iXBRL HTML parser that extracts `ix:nonFraction` elements from `_ixbrl.htm` files. Works reliably for all four companies.
- **R&D disclosure.** IFRS does not mandate a standalone R&D line item. Confirmed: `rnd_M` is `null` for all four current companies. The `jpigp_cor:ResearchAndDevelopmentExpenseIFRS` tag exists in the taxonomy but is not populated by these filers.
- **Quarterly data.** Japan eliminated mandatory quarterly securities reports (四半期報告書) starting FY2024. Confirmed: no quarterly data extracted.
- **EDINET code verification.** ~~The codes listed above need manual verification.~~ Resolved: all four codes verified against live API — filings found and parsed successfully.

### Effort Estimate

Medium. The API integration is straightforward, but XBRL parsing is new infrastructure for this repo. Expect 2–3 iteration cycles to get tag extraction right.

---

## P3: European Public Companies (BMW, Siemens, Mercedes-Benz, Volkswagen)

### Why

These are among Europe's largest industrial companies, all with growing digital transformation and cloud spending. Siemens in particular is a significant Azure customer. All four are publicly traded on European exchanges (primarily XETRA/Frankfurt) and publish IFRS-compliant financial statements.

### Target Companies

| Company | Ticker | Exchange | ISIN | Currency | Relevance |
|---|---|---|---|---|---|
| BMW AG | BMW | XETRA | DE0005190003 | EUR | Mobility + autonomous driving investment |
| Siemens AG | SIE | XETRA | DE0007236101 | EUR | Industrial IoT, digital twin, major Azure customer |
| Mercedes-Benz Group AG | MBG | XETRA | DE0007100000 | EUR | Connected vehicles, ADAS investment |
| Volkswagen AG | VOW3 | XETRA | DE0007664039 | EUR | Software-defined vehicle, CARIAD unit |

### The Challenge: No Single EU Filing API

Unlike SEC EDGAR (US) or EDINET (Japan), there is **no single pan-European API** for structured financial disclosure.

Under ESEF (European Single Electronic Format), EU-listed companies must publish annual reports in iXBRL since 2020. However:
- Each country has its own Officially Appointed Mechanism (OAM) for filing storage.
- Germany's OAM is the **Bundesanzeiger** (Federal Gazette), which has no public programmatic API for structured XBRL data.
- The European Securities and Markets Authority (ESMA) operates the **ESEF Filing Rules Database**, but it is not a data API — it stores filing metadata, not parsed financial facts.

### Candidate Approaches

Four candidate data sources were evaluated. See **ADR-005** for detailed test results.

| Source | API? | German coverage? | Cost | Verdict |
|---|---|---|---|---|
| Bundesanzeiger (German OAM) | No — web only | Yes (official) | Free to browse | No programmatic access |
| filings.xbrl.org | Yes (JSON-API) | **No** — Germany explicitly missing | Free | Confirmed: 0 results for `country=DE` |
| Financial Modeling Prep | Yes (REST) | Yes — but paywalled | Free tier: HTTP 402 for `.DE` symbols | Would need $14/mo paid tier |
| **Yahoo Finance (yfinance)** | Python package | **Yes** — all 4 companies | Free | **Selected** — works, no key needed |

### Implementation (Actual)

**Data source:** Yahoo Finance via `yfinance` Python package (see ADR-005 for rationale).

### Proposed Schema

```json
{
  "isin": "DE0007236101",
  "name": "Siemens AG",
  "ticker": "SIE",
  "exchange": "XETRA",
  "source": "yahoo_finance",
  "last_refreshed": "2026-04-08",
  "annual": [
    {
      "period_end": "2025-09-30",
      "currency": "EUR",
      "revenue_M": 78914,
      "rnd_M": 6559,
      "cost_of_revenue_M": 48515,
      "net_income_M": 9620,
      "tags_used": {
        "source": "yahoo_finance",
        "notes": "Values converted from full units to millions via yfinance"
      }
    }
  ]
}
```

Notes:
- yfinance returns values in full units (not millions). Refresh script converts to `_M` convention.
- yfinance does not provide `filing_date`, `form`, or `namespace` — these fields are omitted.
- A `source: "yahoo_finance"` field distinguishes this from direct regulatory data.
- R&D may be `null` for some companies (BMW, VW) — IFRS does not mandate a standalone R&D line item.

### Module Structure

```
intl/
  registry.yaml              # ISIN → name, ticker, exchange, yf_symbol
  financials/
    DE0005190003.json          # BMW
    DE0007236101.json          # Siemens
    DE0007100000.json          # Mercedes-Benz
    DE0007664039.json          # Volkswagen
  scripts/
    refresh_intl.py            # Fetch from Yahoo Finance → transform → store
    intl_financials.py         # Helper for reading
```

Key by ISIN (International Securities Identification Number) — the most stable global identifier for listed companies. Unlike ticker symbols, ISINs don't change with exchange or corporate rebranding.

### Macro Dependencies

EUR/USD conversion is already supported via the existing `DEXUSEU` series in the macro module.

### Implementation Steps

1. ~~Register for FMP API key~~ → Pivoted to Yahoo Finance (no key needed). See ADR-005.
2. ✅ Create `intl/registry.yaml` with ISIN keys and `yf_symbol` for Yahoo Finance
3. ✅ Implement `refresh_intl.py` with `--dry-run` and `--isin` flags
4. ✅ Write `intl_financials.py` helper + copy to `helpers/`
5. ✅ Write `tests/test_intl.py` — 7 validation checks
6. ✅ Run refresh — 4 companies, 4–5 annual periods each
7. ✅ Update `copilot-instructions.md`
8. ✅ Create GitHub Action workflow
9. ✅ Update README and CHANGELOG

### Results (2026-04-08)

| Company | Latest Period | Revenue (M EUR) | R&D (M EUR) | Net Income (M EUR) | Periods |
|---|---|---|---|---|---|
| BMW | 2025-12-31 | 133,453 | N/A | 7,294 | 4 |
| Siemens | 2025-09-30 | 78,914 | 6,559 | 9,620 | 4 |
| Mercedes-Benz | 2025-12-31 | 132,214 | 6,055 | 5,141 | 5 |
| Volkswagen | 2025-12-31 | 321,913 | N/A | 7,323 | 5 |

### Risks & Open Questions

- **yfinance is unofficial.** Yahoo could change their data format or block access. Mitigation: pin version, module is small (4 companies), manual fallback is feasible.
- **R&D coverage is incomplete.** BMW and VW return `null` for R&D. Acceptable per repo convention (`null` = not disclosed).
- **Limited history.** Only 4–5 annual periods. Sufficient for trend analysis; more history is not available via any free source.
- **Module naming.** `intl/` is generic. If EDINET is built separately, this module becomes specifically "companies sourced via Yahoo Finance" rather than "all international companies."

### Effort Estimate

Low to medium. yfinance does the heavy lifting on data parsing. Main work is the refresh script, normalization, and testing.

---

## P4: Private Companies (Deferred)

### Companies Assessed

| Company | Type | Public financial data? |
|---|---|---|
| Deloitte | Private partnership | Limited — publishes voluntary Global Report (PDF, aggregated) |
| PwC | Private partnership | Limited — publishes voluntary Global Annual Review (PDF, aggregated) |
| EY | Private partnership | Limited — publishes voluntary Global Review (PDF, aggregated) |
| KPMG | Private partnership | Limited — publishes voluntary International Annual Review (PDF, aggregated) |
| Mars Inc | Private corporation | Very limited — summary in annual Sustainability Report |
| G42 | Private / sovereign-backed | Minimal public financial information |
| ByteDance | Private corporation | No public financial disclosure; occasional media leaks |

### Assessment

**None of these companies provide structured, machine-readable financial data.**

The Big 4 publish annual transparency/revenue reports, but:
- These are PDFs, not structured data
- Revenue breakdowns vary year to year
- They report by member firm or by service line, not in a standardized financial statement format
- There are no XBRL filings, no API, no machine-readable equivalent

### Why Defer

This repo's core strength is **automated, scriptable data refresh from structured public sources**. Private company coverage would require:

1. **Manual data entry** from PDFs — violates the "refreshable via script" design principle
2. **Subjective interpretation** of what constitutes revenue, operating income, etc. across inconsistent disclosure formats
3. **High maintenance burden** for low data quality — each year's report may restructure categories

### Recommendation

**Do not build a private company module.** The maintenance cost is disproportionate to the value, and the data would lack the consistency and reliability of the SEC, EDINET, and aggregator-sourced modules.

If private company coverage becomes important for downstream consumers:
- The consumer repo (e.g., acr-analytics) should maintain its own curated dataset with manual entries
- This keeps the public-economic-data repo clean and fully automatable

### Exception: If a company IPOs or begins filing

- Alibaba was originally in this category but turned out to be an active SEC filer → added to SEC module (CIK `0001577552`)
- If ByteDance IPOs or G42 lists publicly, reassess at that time

---

## Implementation Priority

| Priority | Workstream | Effort | Dependency | Status |
|---|---|---|---|---|
| **P2** | EDINET (Japan) | Medium | EDINET API key, XBRL parser | **Done** |
| **P3** | Yahoo Finance (Europe) | Low–Medium | `yfinance` package | **Done** |
| **P4** | Private companies | — | Deferred indefinitely | Deferred |

## ADRs

- **ADR-004:** Source-native keys per module — CIK for SEC, ISIN for intl, EDINET Code for edinet, FRED series ID for macro (`docs/adr/004-source-native-keys.md`)
- **ADR-005:** Yahoo Finance for European data — Bundesanzeiger has no API, filings.xbrl.org excludes Germany, FMP paywalls non-US on free tier (`docs/adr/005-yahoo-finance-for-european-data.md`)
