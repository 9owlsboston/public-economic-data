# CapEx XBRL Tag Gap Report

**Date:** 2026-04-20
**Triggered by:** HP Inc AIRX report (March 2026) — FCF Stability and CapEx Efficiency showing N/A

---

## Executive Summary

50 companies in `public-companies.yaml` had `capex_M: null`, causing N/A values
for four AIRX metrics: FCF Stability (CoV), CapEx Efficiency, FCF Margin Trend,
and CapEx Trend Inflection. Root cause: the SEC EDGAR refresh pipeline only
looked for the primary XBRL tag `PaymentsToAcquirePropertyPlantAndEquipment`,
but many filers use alternative tags.

**Result:** 27 companies fixed, 22 stale AIRX reports flagged for regeneration,
24 companies classified as expected N/A (financials, international IFRS gaps).

---

## Root Cause

The `refresh.py` script in `public-economic-data` extracted CapEx from SEC EDGAR
using a fixed set of XBRL tags. Several common alternatives were missing:

| Tag | Standard | Companies Affected |
|-----|----------|--------------------|
| `PaymentsToAcquirePropertyPlantAndEquipment` | us-gaap | ✅ Already supported |
| `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` | ifrs-full | ✅ Already supported |
| **`PaymentsToAcquireProductiveAssets`** | us-gaap | **17 companies** |
| **`PaymentsForCapitalImprovements`** | us-gaap | **2 companies** |
| **`PurchaseOfPropertyPlantAndEquipmentIntangibleAssets...`** | ifrs-full | **5 companies** |

The three **bold** tags were added to the pipeline.

---

## AIRX Metrics Impacted

All four metrics depend on `capex_M` and cascade into pillar scores:

| Metric | Formula | Pillar |
|--------|---------|--------|
| FCF Stability (CoV) | StdDev / Mean of trailing-8Q FCF | Sustainability |
| CapEx Efficiency | Revenue ÷ CapEx | Capital Efficiency |
| FCF Margin Trend | Δ(FCF ÷ Revenue) YoY | Sustainability |
| CapEx Trend Inflection | CapEx growth ÷ Revenue growth | Capital Efficiency |

When `capex_M` is null, these show N/A and the Sustainability and Capital
Efficiency pillar scores are degraded.

---

## Companies Fixed (27)

All companies below now have `capex_M` populated in both the JSON source files
and `public-companies.yaml`.

| Company | Ticker | TPID | LQ CapEx ($M) | FY CapEx ($M) |
|---------|--------|------|---------------|---------------|
| AT&T Inc. | T | 641918 | 14,061 | 20,842 |
| Albertsons Companies | ACI | 636308 | 1,413 | 1,931 |
| American Airlines Group | AAL | 644222 | 2,149 | 3,779 |
| Barclays Bank | ATMP | 1835064 | — | 574 |
| British American Tobacco | BTI | 522792 | — | 551 |
| CRH plc | CRH | 1719110 | 1,892 | 2,713 |
| Chevron Corp. | CVX | 640683 | 12,083 | 17,347 |
| Concentra Group | CON | 12238980 | 62 | 82 |
| eToro Group | ETOR | 21197550 | — | 5 |
| FactSet Research Systems | FDS | 624466 | 57 | 109 |
| FedEx | FDX | 645655 | 2,335 | 4,055 |
| General Electric | GE | 641734 | 842 | 1,273 |
| HP Inc | HPQ | 31698539 | 233 | 897 |
| Intuitive Surgical | ISRG | 633787 | 377 | 540 |
| KT Corp | KT | 3841799 | — | 2,909,481¹ |
| Kroger Co. | KR | 1178588 | 2,909 | 3,855 |
| Kyndryl Holdings | KD | 91297611 | 492 | 605 |
| Melco Resorts | MLCO | 5670505 | — | 16 |
| Motorola Solutions | MSI | 640691 | 66 | 265 |
| NVIDIA Corp. | NVDA | 2494921 | 4,758 | 6,042 |
| Palo Alto Networks | PANW | 9477301 | 254 | 246 |
| PepsiCo Inc. | PEP | 636846 | 447 | 4,415 |
| Ryan Specialty Holdings | RYAN | 5516916 | 3 | 3 |
| SAP SE | SAP | 603819 | — | 739 |
| Sumitomo Mitsui Financial Group | SMFG | 4912864 | — | 98,498¹ |
| Willis Towers Watson | WTW | 642917 | 166 | 229 |
| bp plc | BP | 211996 | — | 13,221 |

¹ KT Corp reports in KRW (millions), Sumitomo Mitsui in JPY (millions).
"—" = company files only annual reports (20-F), no quarterly capex available.

### New SEC Registry Entries

9 companies were missing from `registry.yaml` and were added:

Barclays, British American Tobacco, Concentra Group, CRH, eToro, Intuitive
Surgical, Melco Resorts, Ryan Specialty, Sumitomo Mitsui.

---

## Reports Requiring Regeneration

22 AIRX reports (all March 2026) have stale N/A capex metrics:

| # | Customer Slug | Company | TPID |
|---|---------------|---------|------|
| 1 | `albertsons-companies` | Albertsons Companies | 636308 |
| 2 | `american-airlines-group` | American Airlines Group | 644222 |
| 3 | `att` | AT&T Inc. | 641918 |
| 4 | `barracuda-networks-inc` | Palo Alto Networks | 9477301 |
| 5 | `bp` | bp plc | 211996 |
| 6 | `chevron-corporation` | Chevron Corp. | 640683 |
| 7 | `environmental-systems-research-institute-inc` | FactSet Research Systems | 624466 |
| 8 | `etoro-ltd` | eToro Group | 21197550 |
| 9 | `federal-express-corporation` | FedEx | 645655 |
| 10 | `general-electric-co` | General Electric | 641734 |
| 11 | `hp-inc` | HP Inc | 31698539 |
| 12 | `intuit` | Intuitive Surgical | 633787 |
| 13 | `kroger-co` | Kroger Co. | 1178588 |
| 14 | `kt-corp` | KT Corp | 3841799 |
| 15 | `kyndryl` | Kyndryl Holdings | 91297611 |
| 16 | `motorola-inc` | Motorola Solutions | 640691 |
| 17 | `nvidia` | NVIDIA Corp. | 2494921 |
| 18 | `pepsico` | PepsiCo Inc. | 636846 |
| 19 | `sap` | SAP SE | 603819 |
| 20 | `tpid-4912864` | Sumitomo Mitsui Financial Group | 4912864 |
| 21 | `wemade-entertainment-co-ltd` | Melco Resorts | 5670505 |
| 22 | `willis-towers-watson` | Willis Towers Watson | 642917 |

**Action:** Regenerate these reports with the AIRX recipe to populate the
previously-N/A capex metrics.

---

## Remaining N/A — Expected (No Fix Available)

### Financial Sector (13 entries, 11 unique companies)

Banks, insurers, and REITs do not report material PP&E capital expenditures.
CapEx metrics are structurally N/A for these companies.

| Company | Ticker |
|---------|--------|
| Chubb Ltd | CB |
| China Life Insurance | CILJF |
| Fidelity National Financial | FNF |
| Global Indemnity Group | GBLI |
| JPMorgan Chase & Co | JPM |
| Manulife Financial Corp. | MFC |
| MetLife Inc | MET |
| Morgan Stanley | MS |
| National Bank Holdings Corp | NBHC |
| Sabra Health Care REIT | SBRA |
| Toronto-Dominion Bank | TD |
| Western Alliance Bancorporation | WAL |

### International IFRS Filers — Tag Gap (2 companies)

These companies file with SEC but use IFRS tags not yet in the pipeline, or
report capex in non-standard line items.

| Company | Ticker | Notes |
|---------|--------|-------|
| UBS Group AG | UBS | Financial — minimal PP&E |
| Woodside Energy Group | WDS | Australian IFRS filer |

### No SEC Filing (0 companies)

Previously listed: Thomson Reuters — fixed by adding `40-F` form support.

### No Capex XBRL Tag Found (2 unique companies)

| Company | Ticker | Notes |
|---------|--------|-------|
| Brookfield Asset Management | BAM | Asset-light model, minimal PP&E |

### Capex Tag Discontinued in Recent Filings (3 companies)

These companies used standard capex tags in earlier filings but stopped
reporting them. No current XBRL capex tag is available.

| Company | Ticker | Notes |
|---------|--------|-------|
| Alibaba Group | BABA | `PaymentsToAcquireOtherPropertyPlantAndEquipment` stopped after FY2020 |
| PDD Holdings | PDD | `PaymentsToAcquirePropertyPlantAndEquipment` stopped after FY2020; negligible PP&E |
| Toyota Motor Corp. | TM | Switched from US-GAAP to IFRS; no standard capex cash-flow tag in recent filings |

---

## Commits

| Repo | Commit | Description |
|------|--------|-------------|
| `public-economic-data` | `779feb0` | Add `PaymentsToAcquireProductiveAssets` as capex fallback (HP Inc fix) |
| `acr-analytics` | `d582fd2` | Populate HP Inc `capex_M` in YAML |
| `public-economic-data` | `3cb5338` | Expand capex XBRL tags + add 9 companies to registry |
| `acr-analytics` | `803325d` | Bulk YAML capex sync for 24 companies |

---

## Prevention

The XBRL tag list in `refresh.py` now covers eight capex tags
across US-GAAP and IFRS. The priority order is:

1. `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` (primary)
2. `us-gaap:PaymentsToAcquireProductiveAssets` (broader, includes intangibles)
3. `us-gaap:PaymentsForCapitalImprovements` (alternative)
4. `us-gaap:PaymentsToAcquireOtherProductiveAssets` (variant — Roper)
5. `us-gaap:PaymentsToAcquireOtherPropertyPlantAndEquipment` (variant — Alibaba historical)
6. `ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` (IFRS primary)
7. `ifrs-full:PurchaseOfPropertyPlantAndEquipmentIntangibleAssets...` (IFRS composite)
8. `ifrs-full:PurchaseOfOtherLongtermAssetsClassifiedAsInvestingActivities` (IFRS broader — Shell)

Additionally, `40-F` (Canadian annual report) is now recognized alongside
`10-K` and `20-F`, fixing Thomson Reuters.

When adding new companies to the registry, verify their XBRL capex tag is
covered by checking SEC EDGAR:
```
https://data.sec.gov/api/xbrl/companyfacts/CID{cik}.json
```
