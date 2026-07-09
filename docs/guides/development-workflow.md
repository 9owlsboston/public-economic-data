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

See [`docs/history/execution-log.md`](../history/execution-log.md) — running record of implementation sessions with actions, outcomes, and decision points.