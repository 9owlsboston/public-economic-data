# ADR-004: Source-Native Keys for Each Data Module

**Status:** Accepted
**Date:** 2026-04-08
**Deciders:** velen

## Context

The repo now spans multiple financial data sources, each with its own identifier system. As we expand beyond SEC EDGAR to international filing systems and financial aggregators, we need a consistent key strategy.

An attractive option is to use **ISIN** (International Securities Identification Number) as a universal key across all modules. ISIN is globally unique and standardized via ISO 6166. However, closer analysis reveals fundamental mismatches.

## Data Source Reference

| Source | Module | Natural Key | Key Type | API Endpoint | Auth | Rate Limit | Coverage |
|---|---|---|---|---|---|---|---|
| SEC EDGAR | `sec/` | **CIK** (10-digit, zero-padded) | Entity | `data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` | User-Agent header | 10 req/sec | US-listed filers (10-K, 10-Q, 20-F) |
| FRED | `macro/` | **Series ID** (e.g., `GDPC1`) | Series | `api.stlouisfed.org/fred/series/observations` | API key (free) | 120 req/min | US macro/economic time series |
| Yahoo Finance | `intl/` | **ISIN** (12-char, e.g., `DE0007236101`) | Security | `yfinance` Python package (no REST API) | None | Undocumented | Global listed companies |
| EDINET (planned) | `edinet/` | **EDINET Code** (6-char, e.g., `E01737`) | Entity | `api.edinet-fsa.go.jp/api/v2/documents.json` | Subscription key (free) | ~1 req/sec | Japanese public filers |

### Key type implications

| Key Type | What it identifies | Example problem |
|---|---|---|
| **Entity** (CIK, EDINET Code) | The legal filer / company | One key per company, always |
| **Security** (ISIN) | A specific share class | Volkswagen has 2 ISINs (ordinary `DE0007664005`, preferred `DE0007664039`); Berkshire has 2 (BRK-A, BRK-B); Alphabet has 3 (GOOGL, GOOG, GOOG on non-US exchanges) |
| **Series** (FRED ID) | A data time series | Not applicable to company identity |

### Why ISIN cannot be the universal key

1. **One company → multiple ISINs.** Dual-class shares force an arbitrary choice of "which ISIN represents the company." Financial statements are filed once for the entity, not per share class.
2. **Filing APIs don't accept ISINs.** SEC EDGAR requires CIK. EDINET requires EDINET Code. Using ISIN as the key would add an indirection layer with no benefit to the data pipeline.
3. **Not all entities have ISINs.** FRED series, private companies, and macro data have no ISIN.
4. **ISIN is the right key when there is no filing API.** For `intl/` (Yahoo Finance sourced), we have no entity-level key from a filing system. ISIN is the most stable identifier available — tickers change with rebranding, exchange codes are exchange-specific.

## Decision

**Use the source-native key for each module.** Do not force a universal key.

| Module | Primary Key | Why |
|---|---|---|
| `sec/` | CIK | Required by SEC EDGAR APIs; one per entity |
| `macro/` | FRED Series ID | Required by FRED API; identifies the time series |
| `intl/` | ISIN | Best stable ID when no filing API exists; ticker is unstable |
| `edinet/` (planned) | EDINET Code | Required by EDINET API; one per filer |

### Cross-module lookup

Cross-referencing the same company across modules (e.g., "find Toyota in SEC and EDINET") is the consumer's responsibility, not this repo's.

Consumer repos (e.g., `acr-analytics`) should maintain their own mapping tables:

```yaml
# Example consumer mapping (NOT in this repo)
- company: Toyota Motor Corp.
  sec_cik: "0001094517"
  isin: JP3633400001
  edinet_code: E02144
```

This keeps the data repo simple and avoids maintaining cross-source identity resolution logic.

## Consequences

- Each module uses the key its source API requires — no translation layer
- Adding a new data source doesn't require retrofitting keys on existing modules
- Cross-module lookups require a mapping table in the consumer, not here
- The `intl/` module uses ISIN because it's the best available option, not because ISIN is a universal standard for this repo
- If a company appears in multiple modules (e.g., Toyota in both `sec/` and a future `edinet/`), each module stores it independently under its source-native key

## Alternatives Considered

1. **ISIN as universal key everywhere.** Rejected — CIK and EDINET Code are entity-level; ISIN is security-level. Would create ambiguity for multi-class companies and add unnecessary indirection for API calls.
2. **Ticker as universal key.** Rejected — tickers are unstable (companies rebrand, exchanges differ) and non-unique across exchanges.
3. **Internal synthetic ID.** Rejected — the repo's principle is "no internal identifiers." Public IDs only.
