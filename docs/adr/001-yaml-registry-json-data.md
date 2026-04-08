# ADR-001: YAML Registry + Per-Company JSON Storage

**Status:** Accepted
**Date:** 2026-03-29
**Deciders:** velen

## Context

We started with a single `public-companies.yaml` that stored both company metadata (name, ticker, CIK) and financial data (latest quarter, latest FY) in one file. With 27 companies and only the latest period each, the file was ~900 lines.

Adding full historical data (5+ annual periods, 20+ quarterly periods per company) would balloon to 10,000+ lines. This creates multiple problems:

- **Parse speed** — YAML is slow for large files; agent loads everything to look up one company
- **Git noise** — every refresh rewrites the entire file; diffs are unreadable
- **Blast radius** — a bad refresh corrupts all companies at once
- **Context waste** — agent loads 10K lines when it only needs ~50 lines for one company

## Decision

Split into two tiers:

1. **`sec/registry.yaml`** — Company registry only (~200 lines). Metadata: name, ticker, CIK, exchange, ai_keywords, tag_overrides. Stable, rarely changes.
2. **`sec/financials/{cik}.json`** — One JSON file per company. All historical annual and quarterly data. Machine-readable, fast to parse, ~5KB each.

JSON was chosen over YAML for financial data because:
- 10× faster to parse at scale
- Native support in Python, JavaScript, and HTTP APIs
- No ambiguity with types (YAML has implicit type coercion issues)

## Consequences

- Agent loads only the company it needs (1 JSON file, ~50 lines)
- Git diffs show exactly which company changed
- A bad refresh only corrupts one company's JSON
- Adding history is free — just more entries in the array
- Helper module (`sec_financials.py`) needed for consumer convenience
- Two files to maintain per company (registry entry + JSON) instead of one

## Alternatives Considered

- **Single YAML with history** — rejected: doesn't scale past ~30 companies
- **SQLite database** — rejected: not git-diffable, requires tooling
- **One big JSON** — rejected: same git-noise problem as single YAML
