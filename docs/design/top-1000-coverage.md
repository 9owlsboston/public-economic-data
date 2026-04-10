# Design: Top 1000 Azure Customer Financial Coverage

**Status:** Draft
**Date:** 2026-04-09
**Modules:** `sec/`, `intl/`, `edinet/`

## Problem

The CFO one-pager recipe in `acr-analytics` needs public financial data for the top Azure customers by ACR spend. Today we cover **~134 SEC + 11 intl + 4 EDINET = ~149 companies**. The `tpid-cik-mapping.yaml` in acr-analytics maps **105 TPIDs** to public identifiers (97 CIK, 4 ISIN, 4 EDINET).

The target is coverage for the **top 1000 Azure customers**. A top-500 analysis (generated 2026-04-08) found:

| Category | Count | Status |
|---|---|---|
| Already mapped (in tpid-cik-mapping) | 97 | ✅ Serving financials |
| In SEC registry but no TPID mapping | 99 | 🔶 Data exists, mapping missing |
| In mapping but not in SEC registry | 61 | 🔶 Mapping exists, data missing |
| SEC auto-discovered (unverified) | 124 | ⚠️ Many wrong CIK matches |
| Government/military | 32 | ❌ Not public companies |
| Known private | 9+ | ❌ No structured financials |
| European (actionable) | 37 | 🟡 Expand `intl` module |
| Japanese (actionable) | 11 | 🟡 Expand `edinet` module |
| Other/unclassified | 185+ | 🟡 Needs triage |

Scaling from 500 to 1000 will surface roughly the same proportional mix — more SEC filers, more internationals, more government/private that can't be covered.

## Scope

| Phase | What | Count | Effort |
|---|---|---|---|
| P0 | Reconcile mapping ↔ registry sync gap | 160 | Low — data/scripts exist |
| P1 | Verify & fix auto-discovered CIK matches | 124 | Medium — manual review |
| P2 | Expand `intl` module (European companies) | ~40 | Medium — Yahoo Finance |
| P3 | Expand `edinet` module (Japanese companies) | ~15 | Medium — EDINET API V2 |
| P4 | Build bulk CIK lookup for unclassified | ~200+ | Medium — new script |
| P5 | Scale to top 1000 (incremental) | ~400 more | Ongoing |

**Not in scope:** Private companies (Deloitte, PwC, EY, KPMG, Mars, ByteDance, Databricks, etc.), government entities, sovereign wealth funds. These have no structured public financial data.

---

## P0: Reconcile Mapping ↔ Registry Sync Gap

### Problem

61 CIKs exist in `tpid-cik-mapping.yaml` (acr-analytics has the TPID mapping) but NOT in `sec/registry.yaml` (this repo has no entry, so refresh never runs). Conversely, 99 CIKs exist in the registry but have no TPID mapping.

### 61 CIKs → Add to Registry

Major companies missing from this repo's registry despite having TPID mappings:

| CIK | Company | Ticker | ACR Category |
|---|---|---|---|
| 0001326801 | Meta Platforms | META | Top 20 |
| 0001108524 | Salesforce | CRM | Top 50 |
| 0000858877 | Cisco Systems | CSCO | Top 50 |
| 0000909832 | Costco Wholesale | COST | Top 50 |
| 0000019617 | JPMorgan Chase | JPM | Top 50 |
| 0000002488 | Advanced Micro Devices | AMD | Top 50 |
| 0001089113 | HSBC Holdings | HSBC | Top 100 |
| 0001048911 | FedEx | FDX | Top 100 |
| 0000034088 | Exxon Mobil | XOM | Top 100 |
| 0000080424 | Procter & Gamble | PG | Top 100 |
| 0001321655 | Palantir Technologies | PLTR | Top 100 |
| 0001561550 | Datadog | DDOG | Top 100 |
| 0001943896 | Rubrik | RBRK | Top 100 |
| 0000798354 | Fiserv | FISV | Top 100 |
| 0001058290 | Cognizant | CTSH | Top 100 |
| 0001734722 | UiPath | PATH | Top 200 |
| 0001867072 | Kyndryl | KD | Top 200 |
| 0002012383 | BlackRock | BLK | Top 200 |
| 0001261333 | DocuSign | DOCU | Top 200 |
| 0001393818 | Blackstone | BX | Top 200 |
| ... | *(41 more — see full list below)* | | |

### Action

```bash
# 1. Add all 61 CIKs to sec/registry.yaml (scripted)
# 2. Run refresh for new CIKs
python sec/scripts/refresh.py   # refreshes all registry entries
# 3. Run tests
python -m pytest tests/test_sec.py -v
```

**Time estimate:** ~2 min to refresh 61 new companies (2 API calls each, 0.3s delay = ~20s + network).

### 99 CIKs → Add to tpid-cik-mapping

These are in the registry but have no TPID mapping. Many were added from auto-discovered matches where the TPID association is unknown or wrong. Two options:

1. **Auto-map via batch_runner**: Run `--top 500` and cross-reference company names against the SEC registry to discover TPID→CIK pairs.
2. **Manual lookup**: Use the ACR dataset's company name field with fuzzy matching against `sec/registry.yaml` names.

This work happens in the **acr-analytics** repo, not here.

---

## P1: Verify & Fix Auto-Discovered CIK Matches

### Problem

The top500 coverage doc lists 124 "SEC auto-discovered" CIKs found by searching EDGAR with customer names. Many matches are **wrong** — the EDGAR full-text search returned incorrect companies:

| TPID | Customer Name | Matched CIK | Matched Ticker | Correct? |
|---|---|---|---|---|
| 647598 | UPS | 0001647639 | UPST | ❌ Should be 0001090727 (UPS) |
| 637627 | CITRIX SYSTEMS | 0000813672 | CDNS | ❌ Should be 0000877890 (Citrix) |
| 641629 | BNY MELLON | 0000818972 | LEO | ❌ Should be 0001390777 (BK) |
| 642087 | ALLSTATE INSURANCE | 0000776867 | WTM | ❌ Should be 0000899629 (ALL) |
| 668846 | MOODYS INVESTORS | 0001279715 | IWSH | ❌ Should be 0001090727 or MCO |
| 120819781 | Cognition AI | 0001455365 | CGTX | ❌ Different company entirely |
| 1528896 | Swiss Re | 0001958399 | HCAI | ❌ Should be Swiss Re CIK |
| 50658619 | ROADGET BUSINESS | 0002075589 | LSBA | ⚠️ Shein — likely correct but obscure |

### Root Cause

The SEC EDGAR company search (`/cgi-bin/browse-edgar`) returns fuzzy results. When the exact company name doesn't match, it returns the "closest" match, which may be completely unrelated. The auto-discovery script accepted the first result without verification.

### Solution: Bulk CIK Lookup Script

Build `sec/scripts/lookup_cik.py` that:

1. Downloads SEC's `company_tickers.json` (single 2MB file, all tickers + CIKs)
2. Downloads SEC's `company_tickers_exchange.json` (includes exchange info)
3. Does **exact ticker match** first (most reliable)
4. Falls back to **normalized name match** (strip Inc/Corp/Ltd, lowercase)
5. Flags ambiguous matches for human review
6. Outputs a CSV of TPID → CIK → confidence (exact_ticker | name_match | fuzzy | unresolved)

```
Input:  TPID, customer_name, optional_ticker
Output: TPID, CIK, name, ticker, match_type, confidence
```

### Data Source

SEC provides two bulk files (no rate limiting, single download):

| File | URL | Size | Contents |
|---|---|---|---|
| `company_tickers.json` | `https://www.sec.gov/files/company_tickers.json` | ~2MB | All SEC filers: CIK, ticker, company name |
| `company_tickers_exchange.json` | `https://www.sec.gov/files/company_tickers_exchange.json` | ~3MB | Same + exchange |

### Implementation Steps

- [ ] Download and cache SEC bulk ticker files
- [ ] Build exact-ticker lookup index
- [ ] Build normalized-name lookup index
- [ ] Accept input: list of (TPID, name, optional_ticker) from acr-analytics
- [ ] Output: verified CIK matches with confidence scores
- [ ] Human review for low-confidence matches
- [ ] Add verified CIKs to registry + mapping

---

## P2: Expand International (`intl`) Module

### Problem

37 European companies in the top 500 have no financial data coverage. The `intl` module currently has 11 companies (4 German automakers + 7 others). Yahoo Finance covers most European exchanges.

### Target Companies (top 37 by ACR)

| Company | TPID | ACR ($M) | Exchange | Country |
|---|---|---|---|---|
| LSEG | 53833429 | 15.2 | LSE | UK |
| AXA | 1742023 | 11.8 | Euronext | France |
| Allianz | 815363 | 10.8 | XETRA | Germany |
| Rabobank | 1877637 | 10.8 | — | Netherlands (coop) |
| Bayer | 520706 | 9.9 | XETRA | Germany |
| Robert Bosch | 605418 | 8.9 | — | Germany (private) |
| ASML | 3012127 | 8.3 | Euronext | Netherlands |
| Munich Re | 797605 | 6.8 | XETRA | Germany |
| ABN AMRO | 1877639 | 6.5 | Euronext | Netherlands |
| Telefonica | 5107666 | 6.3 | BME | Spain |
| Ahold Delhaize | 1877656 | 5.1 | Euronext | Netherlands |
| ABB | 2179491 | 4.5 | SIX | Switzerland |
| Bertelsmann | 522112 | 4.0 | — | Germany (private) |
| Sage Group | 668245 | 3.8 | LSE | UK |
| Capgemini | 1742031 | 3.6 | Euronext | France |
| Philips | 1859386 | 3.2 | Euronext | Netherlands |
| Commerzbank | 523173 | 2.8 | XETRA | Germany |
| Repsol | 815245 | 2.7 | BME | Spain |
| Inditex | 1983563 | 2.5 | BME | Spain |
| Iberdrola | 521043 | 2.2 | BME | Spain |
| Societe Generale | 1742079 | 4.3 | Euronext | France |
| LVMH | 1741830 | 4.1 | Euronext | France |
| Deutsche Post DHL | 523860 | 4.1 | XETRA | Germany |
| AB Volvo | 882153 | 4.0 | OMX | Sweden |
| BASF | 520423 | 3.9 | XETRA | Germany |
| L'Oréal | 1742069 | 5.0 | Euronext | France |
| Marks & Spencer | 594978 | 3.8 | LSE | UK |
| ... | | | | |

**~5 are private** (Bosch, Bertelsmann, Rabobank, Aldi, SHV) → not actionable.

### Action

1. Look up Yahoo Finance symbols for each company
2. Look up ISIN for each company
3. Add entries to `intl/registry.yaml`
4. Add TPID→ISIN entries to `tpid-cik-mapping.yaml` (in acr-analytics)
5. Run `python intl/scripts/refresh_intl.py`

**Time estimate:** ~2-3 min refresh for 30 new companies (1s delay each).

**Note:** Some European companies also file 20-F with SEC (e.g., ASML, AXA, Allianz). For those, we could use the SEC module instead. ADR/20-F filers report in USD which simplifies comparisons. Decision: prefer SEC module when a 20-F filing exists; use intl module for companies that don't file with SEC.

---

## P3: Expand EDINET Module

### Problem

11 Japanese companies identified in the top 500. Currently covering 4 (NTT, Hitachi, NEC, Fujitsu).

### Target Additions

| Company | TPID | ACR ($M) | EDINET Code | Ticker |
|---|---|---|---|---|
| SMFG (三井住友FG) | 4912864 | 5.6 | E03674 | 8316 |
| Rakuten (楽天) | 7335556 | 4.6 | E05765 | 4755 |
| AEON Retail (イオンリテール) | 13451122 | 4.1 | — | — |
| SoftBank Group | 10048477 | 3.3 | E02778 | 9984 |
| Nissan Motor | 2447314 | 3.2 | E02142 | 7201 |
| Panasonic | 13183730 | 2.7 | E01772 | 6752 |
| Sony | 1096511 | 2.6 | E01777 | 6758 |
| Kubota | 3309229 | 2.4 | E01144 | 6326 |
| MUFG (三菱UFJFG) | 5025483 | 2.2 | E03606 | 8306 |
| FUJIFILM Holdings | 11795940 | 2.1 | E00334 | 4901 |

**Note:** 厚生労働省 (Ministry of Health, Labour and Welfare) is government — not actionable. AEON Retail is a subsidiary, not the listed parent; parent is AEON Co. (EDINET E03498).

### Action

1. Verify EDINET codes (some may need lookup via EDINET code list)
2. Add to `edinet/registry.yaml`
3. Add TPID→EDINET entries to `tpid-cik-mapping.yaml`
4. Run `python edinet/scripts/refresh_edinet.py`

**Time estimate:** ~10-20 min for 10 new companies (EDINET is slow — day-by-day filing discovery).

---

## P4: Bulk CIK Lookup for Unclassified

### Problem

~185 unclassified companies in the top 500 (and ~400 more in positions 501-1000). Many are:
- SEC filers under alternate names (IBM, Mastercard, J&J, Fidelity, etc.)
- Foreign ADR filers (Samsung, Tencent, etc.)
- Private companies (Databricks, Wiz, Perplexity, Cohesity, etc.)
- Subsidiaries that file under parent company CIK

### Approach

1. **Ticker-based lookup** (highest confidence):
   - Source ticker from TPID→ticker mapping in `public-companies.yaml` or manual enrichment
   - Match against SEC `company_tickers.json`
   - ~60-70% of public companies resolvable this way

2. **Name-based lookup** (medium confidence):
   - Normalize: strip legal suffixes (Inc, Corp, Ltd, SA, AG, GmbH, plc)
   - Match against SEC `company_tickers.json` names
   - Common mismatches: "IBM" vs "INTERNATIONAL BUSINESS MACHINES", "J&J" vs "JOHNSON & JOHNSON"
   - Build alias table for known divergences

3. **Exchange-based routing**:
   - Identify non-US companies by name heuristics (AG, GmbH, SA, NV, plc, AB, ASA)
   - Route to `intl` module (Yahoo Finance) or `edinet` module
   - These companies won't have CIKs (unless they also file 20-F)

4. **Manual triage** for remainder:
   - Flag as private, government, subsidiary, or genuinely unresolvable
   - Mark as "not_coverable" with reason code

### Implementation

```
sec/scripts/lookup_cik.py
├── Download SEC company_tickers.json (one-time, ~2MB)
├── Build indexes: ticker→CIK, normalized_name→CIK
├── Accept: CSV/YAML of (tpid, customer_name, optional_ticker)
├── Output: YAML with match_type + confidence
└── Generate: registry diff (new entries to add)
```

---

## P5: Scale to Top 1000

### Estimated Composition (extrapolated from top 500 analysis)

| Category | Top 500 | Est. 501-1000 | Est. Total 1000 |
|---|---|---|---|
| SEC filers (US + ADR) | ~220 | ~200 | ~420 |
| European public | ~40 | ~40 | ~80 |
| Japanese public | ~15 | ~10 | ~25 |
| Government/military | ~32 | ~30 | ~62 |
| Known private | ~9 | ~15 | ~24 |
| Other/unresolvable | ~184 | ~205 | ~389 |
| **Total public coverable** | **~275** | **~250** | **~525** |
| **Not coverable** | **~225** | **~250** | **~475** |

**Realistic ceiling: ~525 companies out of 1000** can have public financial data. The rest are government, private, subsidiaries, or entities without structured financial disclosures.

### Refresh Performance at Scale

| Module | Companies | API calls/company | Total calls | Est. time |
|---|---|---|---|---|
| SEC | 420 | 2 | 840 | ~5 min |
| intl | 80 | 1 | 80 | ~3 min |
| EDINET | 25 | ~60 per co. | 1500 | ~30 min |
| **Total** | **525** | | **2420** | **~40 min** |

SEC and intl are fast; EDINET is the bottleneck (day-by-day scanning).

---

## Data Flow (end-to-end)

```
ACR Analytics (KQL)
  │
  ├─ --top 1000 → TPID list
  │
  ▼
tpid-cik-mapping.yaml
  │
  ├─ tpid_to_cik → sec/registry.yaml → refresh.py → sec/financials/{cik}.json
  ├─ tpid_to_isin → intl/registry.yaml → refresh_intl.py → intl/financials/{isin}.json
  └─ tpid_to_edinet → edinet/registry.yaml → refresh_edinet.py → edinet/financials/{code}.json
                                                  │
                                                  ▼
                                       Helper modules read JSON
                                       → CFO one-pager recipe
```

## Implementation Priority

| Step | Phase | Delta | Running Total | Blocking? |
|---|---|---|---|---|
| 1 | P0 — Add 61 mapped CIKs to registry + refresh | +61 | ~210 | **Yes** — immediate value |
| 2 | P0 — Sync 99 registry CIKs to mapping | +99 TPID mappings | ~210 (data), ~204 mappings | No — acr-analytics work |
| 3 | P1 — Build lookup_cik.py + fix bad matches | fix ~50 wrong CIKs | ~210 (corrected) | No |
| 4 | P2 — Expand intl to ~40 European cos | +30 | ~240 | No |
| 5 | P3 — Expand edinet to ~15 Japanese cos | +10 | ~250 | No |
| 6 | P4 — Bulk CIK lookup for unclassified | +100-150 | ~350-400 | No |
| 7 | P5 — Top 1000 incremental: same pipeline | +100-150 | ~500-525 | No |

## Risks & Open Questions

1. **SEC rate limits at scale** — 10 req/s limit. At 420 companies × 2 calls = 840 calls, we stay well under even with 0.3s delay (~4 min). Monthly cron refresh is fine.

2. **EDINET scaling** — Day-by-day scanning is very slow. For 25 companies × 8 years × 60 days = 12,000 API calls. Consider caching filing lists locally after first discovery.

3. **Yahoo Finance reliability** — yfinance scrapes Yahoo's web API; it can break without warning. No SLA. Consider SEC 20-F as primary for companies with dual listings.

4. **Coverage ceiling** — ~47% of top 1000 may be uncoverable (private, government, subsidiaries). Need to set expectations with acr-analytics consumers.

5. **Data staleness** — Annual filings lag 60-90 days. Q4 earnings (filed in Feb-Mar) won't appear until the filing is on EDGAR. Need to document "as-of" dates.

6. **Wrong CIK associations from auto-discovery** — 50+ wrong matches exist in the current top-500 coverage doc. If these propagate to the mapping file, CFO reports will show wrong financial data for those customers.

7. **Chinese companies** — Alibaba and TSMC have SEC 20-F filings; Tencent, Xiaomi do not. HK-listed companies could potentially use Yahoo Finance (`intl` module) with HK tickers.

## Effort Estimate

| Phase | Work | Estimate |
|---|---|---|
| P0 | Add 61 CIKs to registry yaml + refresh | 1-2 hours |
| P1 | Build lookup_cik.py + verify 124 matches | 1 day |
| P2 | Add ~30 European companies to intl | half day |
| P3 | Add ~10 Japanese companies to edinet | half day |
| P4 | Bulk lookup + triage ~200 unclassified | 1-2 days |
| P5 | Top 1000 pipeline (reuse P1-P4 tools) | 1 day |
| **Total** | | **~5 days** |
