# Current state — public-economic-data

> **Snapshot:** 2026-07-09. The single, always-current answer to *"where is this
> project right now?"* — a **supplement to the README**, not a design-doc rollup.
> Lead with a human summary, then keep the rest thin — one line per area + **links**
> to the authoritative topic docs. On any conflict, the linked topic doc wins. Update
> this doc and bump the snapshot date as the **last step** of any change that moves
> the current state.

## Summary

**public-economic-data aggregates *public* financial and economic datasets** — SEC
EDGAR company financials, FRED macro series, international financials (Yahoo Finance),
and Japanese filings (EDINET) — into per-entity JSON keyed by public identifiers
(CIK, FRED series ID, ISIN, EDINET code). It exists to feed cloud-economics analysis,
primarily the CFO one-pager in the `acr-analytics` skill. It stores **raw data only**:
derived metrics (YoY, ratios, Azure %) are computed by consumers at read time. Each
module is a `refresh` script + a `registry.yaml` (metadata) + per-entity JSON + a read
helper (mirrored into `helpers/`).

**Where it stands today.** The four data modules — SEC, FRED, international, EDINET —
are **active and populated**, each with a scheduled GitHub Actions refresh workflow.
Two modules (cloud-pricing, SDK-adoption) are **planned**. Field-level schema is
documented per module in [`docs/schema/`](schema/). The coverage numbers below track
what's ingested; the design docs track where coverage is heading.

## Diagram

_No diagram yet — add one under `docs/diagrams/` when the architecture warrants it._

## Current state

One line per area, each linking to the doc that owns the detail.

- **SEC EDGAR financials** — active: 366 companies (369 standard data files; 3 filers
  predate registry entries), full history (+ Microsoft segment revenue). See
  [`schema/sec.md`](schema/sec.md),
  [`design/sec-financials-v2.md`](design/sec-financials-v2.md).
- **FRED macro indicators** — active: 22 series, full history. See
  [`schema/macro.md`](schema/macro.md),
  [`design/macro-indicators.md`](design/macro-indicators.md).
- **International financials** — active: 190 companies via Yahoo Finance. See
  [`schema/intl.md`](schema/intl.md),
  [`adr/005-yahoo-finance-for-european-data.md`](adr/005-yahoo-finance-for-european-data.md).
- **EDINET (Japan)** — active: 14 companies via EDINET XBRL. See
  [`schema/edinet.md`](schema/edinet.md).
- **Automation** — per-module refresh workflows + a helper-sync check in
  `.github/workflows/`.

## Future state / vision

- **New modules:** cloud-pricing and SDK-adoption
  ([`design/new-datasets-assessment.md`](design/new-datasets-assessment.md)).
- **Broader coverage:** toward the top-1000
  ([`design/top-1000-coverage.md`](design/top-1000-coverage.md)) and non-SEC filers
  ([`design/non-sec-filers.md`](design/non-sec-filers.md)).

## Open gaps

- cloud-pricing and SDK-adoption modules are not yet implemented (planned — see the
  assessment doc above).
- Coverage expansion (top-1000 / non-SEC filers) is scoped in design docs but not yet
  ingested.