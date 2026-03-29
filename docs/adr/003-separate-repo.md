# ADR-003: Separate Repo for Public Economic Data

**Status:** Accepted
**Date:** 2026-03-29
**Deciders:** velen

## Context

SEC financial data was initially built inside `acr-analytics` (in `data/public-companies.yaml` and `scripts/refresh_public_companies.py`). As the scope expanded beyond SEC to include cloud pricing, macro indicators, and SDK adoption, it became clear this is a **reusable data layer**, not an acr-analytics feature.

The `acr-analytics` repo is in the work EMU GitHub environment (`~/cx/common/`) and contains internal Azure consumption data. SEC filing data is 100% public and has different concerns:

- Different refresh cadence (quarterly scheduled vs on-demand analysis)
- Different consumers (CFO reports, account planning, competitive analysis)
- Different sensitivity (public data vs internal ACR)
- Different access pattern (GitHub raw API vs local file reads)

## Decision

Create `9owlsboston/public-economic-data` as a private repo in `~/ws/` with:

1. SEC financials as the first data module (`sec/`)
2. Planned modules for cloud pricing, macro indicators, SDK adoption
3. GitHub Actions for automated scheduled refreshes
4. Consumer access via raw GitHub API (PAT auth for private repo)
5. Helper modules in both repos (canonical in `public-economic-data`, copy in `acr-analytics`)

Private (not public) because the TPID mapping reveals which companies we're tracking.

## Consequences

- Clean separation: `acr-analytics` has KQL/ACR logic, `public-economic-data` has public datasets
- GitHub Actions run independently — no coupling to acr-analytics workflows
- Any project can consume data via GitHub raw URL without cloning
- Helper module (`sec_financials.py`) lives in both repos — may diverge over time
- New dependency: acr-analytics CFO recipe now depends on this repo's data being available

## Alternatives Considered

- **Keep in acr-analytics** — rejected: mixes concerns, bloats a KQL-focused repo
- **Public repo** — rejected: TPID mapping is low-sensitivity but still reveals strategic focus
- **Shared org repo** — deferred: start personal, transfer if others need access
