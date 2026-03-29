# Adding a New Data Module

This guide describes the workflow for implementing a new data source (e.g., FRED, cloud pricing, SDK adoption).

## Workflow

```
1. DESIGN    → docs/design/{module}.md       Why, what, how
2. ADR       → docs/adr/00N-{decision}.md    Key design decisions
3. IMPLEMENT → {module}/scripts/refresh.py    Fetch + transform + store
4. VALIDATE  → tests/test_{module}.py         Data quality checks
5. AUTOMATE  → .github/workflows/refresh-{module}.yml
6. DOCUMENT  → README.md + docs/guides/
7. CHANGELOG → CHANGELOG.md entry
```

## Step 1: Design Doc

Create `docs/design/{module}.md` covering:

- **Problem** — what question does this data answer?
- **Data sources** — API endpoint, auth, rate limits, format
- **Schema** — what the output JSON looks like
- **Data flow** — API → transform → merge → write
- **Implementation steps** — numbered, with effort estimates
- **Consumer usage** — how the helper is called

See [macro-indicators.md](../design/macro-indicators.md) as a template.

## Step 2: ADR (if making non-obvious decisions)

If the design involves trade-offs, write an ADR in `docs/adr/`:

```markdown
# ADR-00N: {Title}

**Status:** Accepted
**Date:** YYYY-MM-DD
**Context:** {Why this decision was needed}
**Decision:** {What we chose}
**Consequences:** {What follows from this choice}
```

## Step 3: Implement

Create the module directory:

```
{module}/
  registry.yaml          # If tracking specific entities (optional)
  {subdir}/              # Output data files
  scripts/
    refresh_{module}.py  # Fetcher script
    {module}_helper.py   # Helper module for reading
```

Refresh script requirements:
- `--dry-run` flag (print without writing)
- `--key` flag for single-entity refresh (e.g., `--cik`, `--series-id`)
- Rate limit compliance (sleep between requests)
- Merge with existing data (don't lose history)
- Error handling with `⚠` prefix for warnings

Helper module requirements:
- Works locally (file path) and via GitHub raw URL
- `get(key)` → full data for one entity
- `latest(key)` → most recent observation
- Derived metrics computed at read time, not stored

Copy helper to `helpers/` for consumer convenience.

## Step 4: Validate

Create `tests/test_{module}.py`:

- JSON parseable (all files)
- Required fields present
- Data sorted correctly (descending by date)
- Primary key matches filename
- Non-empty data
- Freshness check (warn if >N days stale)

Run: `python tests/test_{module}.py`

## Step 5: Automate

Create `.github/workflows/refresh-{module}.yml`:

```yaml
name: Refresh {Module}
on:
  schedule:
    - cron: '{schedule}'
  workflow_dispatch:
    inputs:
      key:
        description: 'Optional: refresh a single entity'
        required: false
jobs:
  refresh:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install pyyaml
      - run: python {module}/scripts/refresh_{module}.py
        env:
          API_KEY: ${{ secrets.{MODULE}_API_KEY }}
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: refresh {module} data [automated]"
          file_pattern: "{module}/**/*.json"
```

## Step 6: Document

- Update `README.md` — add row to data sources table, add usage example
- Update `.github/copilot-instructions.md` — add module conventions
- Create `docs/guides/` runbook if the module has operational procedures

## Step 7: Changelog

Add entry to `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- **{Module}** — {one-line description} ({N} series, {cadence} refresh)
```

## Checklist

```
[ ] docs/design/{module}.md
[ ] docs/adr/00N-*.md (if needed)
[ ] {module}/registry.yaml (if needed)
[ ] {module}/scripts/refresh_{module}.py
[ ] {module}/scripts/{module}_helper.py
[ ] helpers/{module}_helper.py (copy)
[ ] tests/test_{module}.py
[ ] .github/workflows/refresh-{module}.yml
[ ] README.md updated
[ ] .github/copilot-instructions.md updated
[ ] CHANGELOG.md entry
[ ] Initial data refresh run
[ ] All tests pass
```
