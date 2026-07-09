# AGENTS.md — public-economic-data

Repo-specific operating contract for any AI coding agent (Copilot CLI, VS Code,
Claude, etc.) working here.

> **Not here:** the SDLC (explore → plan → implement → verify → ship → **close-out**,
> the `planner`/`implementer`/`verifier` personas + the `explorer`/`rubber-duck`
> review capabilities, conventional commits, branching) lives in the **global**
> `~/.copilot/copilot-instructions.md` (SoT: `ai-tooling-config`) — this file does
> **not** repeat it. The full model + diagram is in
> [`dev-env-setup` `docs/guides/sdlc.md`](https://github.com/9owlsboston/dev-env-setup/blob/main/docs/guides/sdlc.md).
> Keep this file to what is *unique to this repo*.

## 1. What this repo is

Aggregator of **public** financial + economic datasets — SEC EDGAR company
financials, FRED macro series, international financials (Yahoo Finance), and
Japanese filings (EDINET) — into per-entity JSON keyed by public identifiers. It is
a **data + helper-scripts repo**, not an app. Primary consumer: the CFO one-pager
recipe in the `acr-analytics` skill. Repo `9owlsboston/public-economic-data`
(private). Module/field detail lives in
[`.github/copilot-instructions.md`](.github/copilot-instructions.md) + `docs/schema/`.

## 2. Hard rules (repo-specific)

- **Public identifiers only.** CIK, ticker, FRED series ID, ISIN, EDINET code —
  **never** internal IDs (TPID, enrollment numbers). Those belong in consumer repos
  (e.g. the TPID→CIK map lives in `acr-analytics`).
- **Never hand-edit JSON data files.** Always regenerate via the module's
  `refresh` script. Registry YAML holds **metadata only** — never mix financial
  data into it.
- **Helper-sync (CI-enforced).** Read helpers exist in two identical places —
  `{module}/scripts/` (canonical) and `helpers/` (consumer copy). Keep **both** in
  sync after any change; `.github/workflows/check-helpers.yml` fails the PR otherwise.
- **Raw data only — no derived metrics in JSON.** YoY, R&D intensity, Azure % are
  computed at read time by consumers, never stored.
- **Monetary values in millions**, suffixed `_M` (e.g. `revenue_M: 23769`). Period
  arrays sorted **descending** by `period_end`.
- **Never assume USD.** Check each entry's `currency`; suppress Azure % ratios when
  currency ≠ USD.
- **`null` = not disclosed** (XBRL tag not found) — surface "Not disclosed", never
  omit silently. Keep **both** original and amended filings (distinct `filing_date`).
- **Design-doc first.** Start every new/changed data module with
  `docs/design/{module}.md` before code — see the Development Workflow in
  [`.github/copilot-instructions.md`](.github/copilot-instructions.md) and
  [`docs/guides/adding-a-data-module.md`](docs/guides/adding-a-data-module.md).

## 3. Run / test

Python via the repo `.venv` (no `requirements.txt` — deps are installed into the
venv). Per-module refresh scripts fetch → transform → store; **always `--dry-run`
first**. Tests are pytest.

```bash
# read data via a module helper (example: SEC by CIK)
python3 -c "import sys; sys.path.insert(0,'sec/scripts'); \
  from sec_financials import SECFinancials; \
  print(SECFinancials(local_dir='sec/financials').latest_annual('0000796343'))"

# refresh a module (dry-run first, then for real)
python3 sec/scripts/refresh.py --dry-run
python3 macro/scripts/refresh_fred.py --dry-run
# also: intl/scripts/refresh_intl.py, edinet/scripts/refresh_edinet.py,
#       sec/scripts/refresh_segments.py

# validate
python3 -m pytest tests/ -q
```

After touching any helper, mirror it between `{module}/scripts/` and `helpers/`
(CI check: `.github/workflows/check-helpers.yml`).

## 4. Where to write (docs map)

Pick the destination by the **kind** of content, not the topic:

| Kind of content | Goes in |
|---|---|
| How to run / use this repo | `README.md` |
| Rules for agents working here | `AGENTS.md` (this file) |
| Dated "where we are now" snapshot (current → future → gaps) | `docs/current-state.md` |
| **What commands actually ran / how verified** (action trail) | `docs/history/execution-log.md` |
| Architecture, proposals, per-module design — the *why* | `docs/design/` |
| Non-obvious decisions (numbered ADRs) | `docs/adr/` |
| Field-level data dictionary / schema | `docs/schema/` |
| How-to workflows and walkthroughs | `docs/guides/` |
| Consumer-facing change log (content) | `CHANGELOG.md` |

## 5. Drift-rules

Facts that **must stay true** in this repo. `docs-drift` flags any doc/code hit
against a bad-substring below. Use a **live/actionable pattern** (a command or
import used *as if current*), NOT a bare noun — nouns appear in explanatory prose
and history and would just create noise. Add a row whenever a live path moves/renames.

```drift-rules
# <live-pattern>       ->   <why it's wrong / what's correct now>
docs/execution-log.md  ->   moved to docs/history/execution-log.md (MVRS floor path, 2026-07-09); update any link
```

## 6. Doc-lifecycle (pre / post — agent-enforced)

- **Pre** (session start): read this file + the relevant plan/design doc; run
  `docs-drift` before changing code.
- **During**: update `docs/history/execution-log.md` *as part of* the change
  (what ran, how verified) — not after; keep any plan status honest. Docs change
  *with* code: if a change alters behavior, config, CLI, API, or deployment, the
  closest doc changes in the same change.
- **Post** (session/PR end): **close out the change** — squash-merge, then ff
  `main` (primary worktree) → remove the worktree → delete the local branch (`-D`,
  since a squash-merged branch isn't an ancestor of `main`) → run `docs-drift` →
  update refs on any move/rename (and the drift-rules above) → note residuals. If
  the change moved the current state, reconcile `docs/current-state.md` and bump
  its snapshot date as the **last step**.
- **Wrap review (current-state rubber-duck):** at the end of any change that
  touched product code or config, read `git diff` + `docs/current-state.md` +
  `README.md` + any touched topic docs, then explicitly report one of
  `current-state: updated / not-affected / needs-human-decision`. A read-only
  judgment pass — not a script.

Full lifecycle spec: global `~/.copilot/copilot-instructions.md`.

## 7. Documentation output style

When writing or editing any doc, follow this output contract so a human can trust
and skim it (full rationale: the ecosystem's *AI documentation output contract*
design doc).

**Structure**

- **Summary first.** Open with a plain-English summary a non-author grasps in one
  read: *what this is, who it's for, when to use it.* For non-trivial topics, lead
  the summary with a high-level **contextual diagram** (source in `docs/diagrams/`,
  Mermaid/drawio/excalidraw) — the diagram *is* the summary.
- **Why before how.** State purpose/value before implementation detail.
- **One doc, one intent.** Route by Diátaxis (tutorial / how-to / reference /
  explanation) and the where-to-write map (§4); don't mix intents. *(Exception:
  `docs/current-state.md` is a deliberate rollup/index.)*
- **Link, don't duplicate.** Point to the source-of-truth doc instead of copying
  it; on conflict, the linked topic doc wins.

**Prose discipline (the anti-machine rules)**

- **Don't restate code.** If the code/signature already says it, link to it —
  don't narrate it.
- **No filler, no narration of the obvious.** Cut "In this section we will…" and
  ceremony.
- **Cite or flag.** Every non-obvious behavioral claim must trace to code, a test,
  an ADR, or a linked source — otherwise mark it **`unverified`**.
- **Mark assumptions explicitly.** Never present an assumption as a fact.
- **Length discipline (soft).** Summaries stay short (a few sentences / ≤ ~8
  lines); depth goes in the detail sections below.