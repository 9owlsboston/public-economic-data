# ADR-005: Yahoo Finance for European Company Financials

**Status:** Accepted
**Date:** 2026-04-08
**Deciders:** velen

## Context

The `intl/` module needs to fetch annual financial data for BMW, Siemens, Mercedes-Benz, and Volkswagen — all German-listed companies reporting under IFRS on XETRA/Frankfurt.

Unlike SEC EDGAR (US) or EDINET (Japan), there is no single European API for structured financial disclosure. The EU's ESEF mandate requires iXBRL reports, but data access is fragmented across national Officially Appointed Mechanisms (OAMs), most of which lack programmatic APIs.

We evaluated five candidate data sources.

## Sources Evaluated

| Source | Type | API? | Auth | German coverage? | Cost | Status |
|---|---|---|---|---|---|---|
| **Bundesanzeiger** | German OAM (official filing authority) | No — web search only | n/a | Yes — official source for German annual reports | Free to browse | No programmatic access; HTML scraping required. Fragile and legally ambiguous |
| **Unternehmensregister** | German company register (aggregates Bundesanzeiger) | No — web search only | n/a | Yes | Free to browse | Same problem as Bundesanzeiger; no API |
| **filings.xbrl.org** | XBRL International filing repository | Yes — JSON-API, free | None needed | **No** — Germany explicitly listed as missing country | Free | Confirmed: `filter[country]=DE` returns 0 results. Their docs state: "countries where ESEF filings are not made available... include Germany" |
| **Financial Modeling Prep (FMP)** | Commercial data aggregator | Yes — REST API | API key | Yes — symbols `BMW.DE`, `SIE.DE`, etc. | Free tier: US exchanges only (HTTP 402 for `.DE`). Paid: $14/month | Tested 2026-04-08: free-tier key returns 402 for all four German symbols. Would require paid subscription |
| **Yahoo Finance (yfinance)** | Market data aggregator | Python package (unofficial, no REST API) | None | Yes — all four companies, 4–5 annual periods | Free | Tested 2026-04-08: returns revenue, COGS, R&D (partial), net income for all four companies in EUR |

### Detailed Test Results (2026-04-08)

**FMP free tier:**
```
BMW.DE  → HTTP 402 (payment required)
SIE.DE  → HTTP 402
MBG.DE  → HTTP 402
VOW3.DE → HTTP 402
AAPL    → 200 OK (US stocks work fine)
BMWYY   → 402 (OTC ADR also paywalled)
```

**filings.xbrl.org API:**
```
GET /api/filings?filter[country]=DE&page[size]=3
→ {"data": [], "meta": {"count": 0}}
```

**yfinance:**
```
BMW.DE  → 4 periods (2022–2025), rev/cogs/ni ✓, rnd null
SIE.DE  → 4 periods (2022–2025), rev/cogs/ni/rnd ✓
MBG.DE  → 5 periods (2021–2025), rev/cogs/ni/rnd ✓
VOW3.DE → 5 periods (2021–2025), rev/cogs/ni ✓, rnd null
```

## Decision

**Use Yahoo Finance (via `yfinance` Python package) as the data source for European company financials.**

The refresh script (`intl/scripts/refresh_intl.py`) fetches annual income statements via `yfinance`, converts from full units to millions, and writes one JSON file per company keyed by ISIN.

## Rationale

1. **Germany has no programmatic filing API.** The Bundesanzeiger is the official OAM but offers only a web interface. The pan-European filings.xbrl.org repository explicitly excludes Germany.

2. **FMP requires a paid subscription for non-US stocks.** The free tier covers NYSE/NASDAQ only. The `.DE` (XETRA) symbols return HTTP 402. Even OTC ADR tickers (e.g., `BMWYY`) are paywalled.

3. **Yahoo Finance is free and works today.** No API key required. Returns the metrics we need (revenue, COGS, R&D where disclosed, net income) in the original reporting currency (EUR). Coverage spans 4–5 annual periods.

4. **The data ultimately comes from the same IFRS filings.** Yahoo Finance parses the same annual reports that Bundesanzeiger stores. We're choosing a data access path, not a different data source.

## Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **yfinance is unofficial** — Yahoo could change their data format or block access | Medium | Pin `yfinance` version. The `intl/` module is small (4 companies, annual only). Manual fallback is feasible. Monitor for breakage in CI. |
| **Data accuracy** — aggregator may have parsing errors vs. official filings | Low | Cross-reference latest period against published annual reports during initial load. Revenue and net income are high-confidence fields. |
| **R&D coverage is incomplete** — BMW and VW return `null` for R&D | Low | Acceptable per repo convention: `null` = not disclosed. These companies may not break out R&D as a separate line in their income statement presentation. |
| **Limited history** — only 4–5 annual periods vs. SEC's full XBRL history | Low | Sufficient for trend analysis and YoY growth. More history is not available via any free source. |

## Future Reconsideration

This decision should be revisited if:
- **Germany starts publishing ESEF data via a programmatic API** (Bundesanzeiger or European Single Access Point / ESAP)
- **filings.xbrl.org gains German coverage** — they have explicitly flagged this as a gap they want to fill
- **The repo builds an XBRL parser for EDINET (P2)** — the same parser could potentially process European iXBRL, enabling direct Bundesanzeiger scraping as a more defensible path
- **FMP becomes justified** — if the module scales beyond a handful of European companies, the $14/month paid tier may be worth the reliability vs. managing yfinance breakage

## Alternatives Rejected

1. **FMP paid tier ($14/month)** — Not justified for 4 companies with annual-only refresh. Would become viable if scope expands significantly.
2. **Bundesanzeiger scraping** — No API; requires HTML navigation, session handling, and potentially CAPTCHA. Fragile and maintenance-heavy. Legal gray area for automated access.
3. **Alpha Vantage** — Limited international coverage; free tier has severe rate limits (25 req/day).
4. **Polygon.io** — Minimal non-US financial statement coverage.
