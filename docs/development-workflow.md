# Development Workflow

Standard workflow for all changes in this repo — whether adding a data module, fixing a bug, or extending an existing module. Applies to both human and AI agent contributors.

## The 7-Step Process

```
1. DESIGN    → docs/design/{module}.md       What and why — always start here
2. ADR       → docs/adr/00N-*.md             Non-obvious decisions (if any)
3. IMPLEMENT → {module}/scripts/              Fetch + transform + store
4. VALIDATE  → tests/test_{module}.py         Data quality checks
5. AUTOMATE  → .github/workflows/             Scheduled refresh
6. DOCUMENT  → README + copilot-instructions  Consumer-facing docs
7. CHANGELOG → CHANGELOG.md                   What changed and when
```

### When to Use Each Step

| Change type | Steps needed |
|---|---|
| **New data module** (FRED, cloud pricing) | All 7 steps |
| **Add companies to SEC registry** | 3 (implement) → 4 (validate) → 7 (changelog) |
| **Fix a bug in refresh script** | 3 → 4 → 7 |
| **Structural change** (schema, storage) | 1 (design) → 2 (ADR) → 3 → 4 → 7 |
| **Documentation only** | 6 → 7 |

### Key Rule

> **Always start with the design doc for new modules.** Don't jump to implementation.
> The design doc forces you to answer: what problem does this solve, what does the output look like, how will consumers use it?

### Details

- **Step 1 (Design):** Template at `docs/design/macro-indicators.md`. Cover: problem, API, schema, data flow, implementation steps, consumer usage.
- **Step 2 (ADR):** Only for non-obvious decisions. Format: Status, Date, Context, Decision, Consequences. See `docs/adr/` for examples.
- **Step 3 (Implement):** See `docs/guides/adding-a-data-module.md` for the full checklist. Scripts must support `--dry-run`.
- **Step 4 (Validate):** Data validation, not unit tests. Check: JSON parseable, required fields, sorted correctly, key matches filename, non-empty, freshness.
- **Step 5 (Automate):** GitHub Action with schedule + manual dispatch. API keys as secrets.
- **Step 6 (Document):** Update README data sources table, copilot-instructions conventions, and create guides if operational.
- **Step 7 (Changelog):** Every change gets a CHANGELOG entry. Use [Keep a Changelog](https://keepachangelog.com/) format.

---

## Execution Log

Running record of what was built, when, and key decisions made during implementation.

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