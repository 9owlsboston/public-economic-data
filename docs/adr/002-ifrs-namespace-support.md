# ADR-002: IFRS Namespace Support for Foreign Private Issuers

**Status:** Accepted
**Date:** 2026-03-29
**Deciders:** velen

## Context

Five of our top 50 Azure customers (SAP, UBS, TD Bank, Shell, Manulife) file with SEC as foreign private issuers using Form 20-F instead of 10-K/10-Q. Their XBRL data uses the `ifrs-full` namespace instead of `us-gaap`, with different tag names:

| Metric | us-gaap | ifrs-full |
|---|---|---|
| Revenue | `Revenues` | `Revenue` |
| Cost of Revenue | `CostOfRevenue` | `CostOfSales` |
| Net Income | `NetIncomeLoss` | `ProfitLossAttributableToOwnersOfParent` |
| R&D | `ResearchAndDevelopmentExpense` | `ResearchAndDevelopmentExpense` (same) |

Additionally, these companies often report in non-USD currencies (EUR, CAD, CHF, JPY).

## Decision

1. Search both `us-gaap` and `ifrs-full` namespaces in CompanyFacts, trying `us-gaap` first
2. Search ALL currencies in the XBRL data, picking the entry with the most recent period end date (regardless of currency)
3. Store the `currency` field in each JSON entry so consumers know the denomination
4. Suppress Azure % ratios when `currency ≠ USD` (mixing currencies is misleading)

## Consequences

- Coverage expanded from 22 to 25 companies with data (SAP got EUR data, Shell got USD data, TD Bank got CAD data)
- UBS and Manulife have period-end mismatches in their XBRL — no data extracted despite having CIK and IFRS facts
- Non-USD companies show "Innovation Intensity" (R&D/Revenue) but not "Azure % of Revenue"
- Tag candidate lists doubled (must maintain per-namespace)

## Alternatives Considered

- **USD only** — rejected: would miss SAP (EUR), TD Bank (CAD) entirely
- **Currency conversion** — rejected: adds complexity, exchange rate timing issues, not worth it for a context section
