# Execution Log

Running record of implementation sessions — actions, outcomes, and decisions made.
Each session appends a dated entry. Agents and humans both contribute.

**Format:** Each session has scope, contributor, action/outcome table, key decisions, and coverage snapshot.

---

### 2026-03-29 — Initial Bootstrap

**Scope:** SEC EDGAR financials module + repo structure
**Contributor:** velen + AI agent

| Time | Action | Outcome |
|---|---|---|
| — | Design: CFO one-pager needs public financial context | `acr-analytics/docs/design/cfo-qa.md` — design section added |
| — | Implement v1: single YAML with latest-only data | `data/public-companies.yaml` — 27 companies, latest Q + FY |
| — | Implement v2: IFRS namespace, tag overrides, period-end anchoring | Unlocked SAP, Shell, Toyota. Fixed quarterly disambiguation |
| — | Decision: separate repo for public data | ADR-003: TPID is internal, CIK is public. Clean separation |
| — | Create repo `9owlsboston/public-economic-data` (private) | Scaffolded with SEC module, 27 companies |
| — | Refactor: full history extraction | Per-company JSON with all annual + quarterly periods |
| — | Refactor: CIK as primary key (not TPID) | JSON files renamed, registry rekeyed, TPID→CIK mapping in acr-analytics |
| — | Repo structure: ADRs, copilot-instructions, roadmap, tests | AI-agent-friendly development workflow established |
| — | FRED API key registered and stored as GitHub Secret | Ready for Phase 3 implementation |

**Key decisions:**
- ADR-001: YAML registry + per-company JSON (not single YAML)
- ADR-002: IFRS namespace support (us-gaap + ifrs-full)
- ADR-003: Separate repo, public identifiers only (CIK, not TPID)
- Keep all history, keep amended filings, access via helper module

**Coverage at end of session:**
- 27 companies tracked (top 50 Azure ACR customers)
- 25/27 with annual data, 23/27 with quarterly data
- 27 JSON files, ~236KB total
- Tests: 6 checks, 1 known issue (UBS: XBRL period-end mismatch)

### 2026-03-29 — FRED Macro Indicators Module

**Scope:** Implement Phase 3 from roadmap — FRED macro indicators
**Contributor:** velen + AI agent

| Time | Action | Outcome |
|---|---|---|
| — | Read design doc `docs/design/macro-indicators.md` | 6 target series, FRED API, JSON-per-series schema |
| — | Study SEC module patterns (registry, refresh, helper, tests, workflow) | Established consistency targets |
| — | Create `macro/registry.yaml` with 6 series | Series metadata (title, frequency, units, relevance) |
| — | Implement `macro/scripts/refresh_fred.py` | FRED API fetcher with `--dry-run`, `--series-id`, merge logic |
| — | Implement `macro/scripts/macro_indicators.py` helper | `latest()`, `yoy_growth()`, `trend()`, `series_list()` |
| — | Copy helper to `helpers/macro_indicators.py` | Consumer convenience copy |
| — | Create `.github/workflows/refresh-macro.yml` | Monthly on 5th, manual dispatch per series |
| — | Initial refresh: 4/6 series succeeded | GDPC1 (316), PCU518210518210 (303), CE16OV (937), CES5051200001 (434) |
| — | **Decision:** `CPURNSA` → `CPIAUCSL` | `CPURNSA` returns 400 from FRED API. `CPIAUCSL` is the seasonally adjusted equivalent |
| — | **Decision:** `CUSR0000SEEE02` → `CUSR0000SEEE` | Series not found in FRED. `CUSR0000SEEE` (IT Hardware & Services) is the closest valid CPI proxy |
| — | Re-refresh corrected series | CPIAUCSL (949 obs), CUSR0000SEEE (241 obs) — all 6 series populated |
| — | Run `tests/test_macro.py` | 6 files, 5 checks, 0 errors ✅ |
| — | Helper smoke test | GDP YoY: 2.03%, CPI YoY: 2.43%, tech employment: 344.1K |
| — | Update README, CHANGELOG, copilot-instructions, design doc | Status → Active, corrected series IDs, added FRED section |

**Key decisions:**
- Use FRED API for everything (no separate BLS integration — FRED re-hosts BLS data)
- `CPURNSA` invalid → replaced with `CPIAUCSL` (seasonally adjusted CPI, same concept)
- `CUSR0000SEEE02` invalid → replaced with `CUSR0000SEEE` (IT Hardware & Services, broader but valid)
- Design doc series IDs corrected to match actual FRED API availability

**Coverage at end of session:**
- 6 FRED series, full history, ~200KB total
- GDPC1 (316 obs), CPIAUCSL (949), CUSR0000SEEE (241), PCU518210518210 (303), CE16OV (937), CES5051200001 (434)
- Tests: 5 checks, 0 errors
- GitHub Action ready (requires `FRED_API_KEY` secret)
