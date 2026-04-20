#!/usr/bin/env python3
"""Refresh SEC EDGAR financial data for all tracked companies.

Flow:
  1. Submissions API → find ALL 10-K/10-Q/20-F filings + period end dates
  2. CompanyFacts API → extract revenue, R&D, COGS, net income by period end
  3. Tag resolution (three-layer: preferred list → best match → YAML override)
  4. Write per-company JSON to sec/financials/{cik}.json

Supports us-gaap (10-K/10-Q) and ifrs-full (20-F foreign private issuers).

Usage:
    python sec/scripts/refresh.py [--dry-run] [--cik CIK]

Rate limit: SEC requires User-Agent header, max 10 req/sec.
"""

import argparse
import json
import time
import urllib.request
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = ROOT / "sec" / "registry.yaml"
FINANCIALS_DIR = ROOT / "sec" / "financials"

SEC_FACTS_BASE = "https://data.sec.gov/api/xbrl/companyfacts"
SEC_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
USER_AGENT = "PublicEconomicData public-economic-data@microsoft.com"

# XBRL tags per namespace, priority order
METRIC_TAGS = {
    "revenue": {
        "us-gaap": [
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet",
        ],
        "ifrs-full": [
            "Revenue",
            "RevenueFromContractsWithCustomers",
        ],
    },
    "rnd": {
        "us-gaap": [
            "ResearchAndDevelopmentExpense",
            "ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost",
        ],
        "ifrs-full": [
            "ResearchAndDevelopmentExpense",
        ],
    },
    "cost_of_revenue": {
        "us-gaap": [
            "CostOfRevenue",
            "CostOfGoodsAndServicesSold",
            "CostOfGoodsSold",
        ],
        "ifrs-full": [
            "CostOfSales",
        ],
    },
    "net_income": {
        "us-gaap": [
            "NetIncomeLoss",
            "ProfitLoss",
        ],
        "ifrs-full": [
            "ProfitLossAttributableToOwnersOfParent",
            "ProfitLoss",
        ],
    },
    # ── V2 duration metrics ──────────────────────────────────────────────
    "capex": {
        "us-gaap": [
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsToAcquireProductiveAssets",
            "PaymentsForCapitalImprovements",
            "PaymentsToAcquireOtherProductiveAssets",
            "PaymentsToAcquireOtherPropertyPlantAndEquipment",
        ],
        "ifrs-full": [
            "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
            "PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets",
            "PurchaseOfOtherLongtermAssetsClassifiedAsInvestingActivities",
        ],
    },
    "operating_cash_flow": {
        "us-gaap": [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ],
        "ifrs-full": [
            "CashFlowsFromUsedInOperatingActivities",
        ],
    },
    "operating_income": {
        "us-gaap": [
            "OperatingIncomeLoss",
        ],
        "ifrs-full": [
            "ProfitLossFromOperatingActivities",
        ],
    },
    "sga": {
        "us-gaap": [
            "SellingGeneralAndAdministrativeExpense",
            "GeneralAndAdministrativeExpense",
        ],
        "ifrs-full": [
            "SellingGeneralAndAdministrativeExpense",
        ],
    },
    # ── V2 instant (balance-sheet) metrics ───────────────────────────────
    "cash": {
        "us-gaap": [
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsAndShortTermInvestments",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ],
        "ifrs-full": [
            "CashAndCashEquivalents",
            "CashAndCashEquivalentsIfDifferentFromStatementOfFinancialPosition",
        ],
    },
    "total_debt": {
        "us-gaap": [
            "LongTermDebt",
            "LongTermDebtAndCapitalLeaseObligations",
            "LongTermDebtNoncurrent",
            "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
        ],
        "ifrs-full": [
            "Borrowings",
            "NoncurrentFinancialLiabilities",
        ],
    },
    "total_assets": {
        "us-gaap": [
            "Assets",
        ],
        "ifrs-full": [
            "Assets",
        ],
    },
}

# Instant metrics use balance-sheet point-in-time values (no start date)
INSTANT_METRICS = {"cash", "total_debt", "total_assets"}

NAMESPACES = ["us-gaap", "ifrs-full"]
ANNUAL_FORMS = ("10-K", "20-F", "40-F", "10-K/A", "20-F/A", "40-F/A")
QUARTERLY_FORMS = ("10-Q", "10-Q/A")


def _sec_get(url: str) -> dict:
    """Fetch JSON from SEC EDGAR."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ── Step 1: Submissions API ─────────────────────────────────────────────

def fetch_all_filings(cik: str) -> dict[str, list[dict]]:
    """Get ALL annual and quarterly filings from submissions API.

    Returns {"annual": [...], "quarterly": [...]}, each a list of
    {"form", "filing_date", "period_end"} sorted by period_end descending.
    """
    data = _sec_get(f"{SEC_SUBMISSIONS_BASE}/CIK{cik}.json")
    recent = data.get("filings", {}).get("recent", {})
    form_list = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])

    result = {"annual": [], "quarterly": []}
    seen = {"annual": set(), "quarterly": set()}

    for i, form in enumerate(form_list):
        if not filing_dates[i] or not report_dates[i]:
            continue

        if form in ANNUAL_FORMS:
            scope = "annual"
        elif form in QUARTERLY_FORMS:
            scope = "quarterly"
        else:
            continue

        period_end = report_dates[i]
        filing_date = filing_dates[i]
        form_normalized = form.replace("/A", "")

        # Keep both original and amended filings
        key = (period_end, filing_date)
        if key in seen[scope]:
            continue
        seen[scope].add(key)

        result[scope].append({
            "form": form_normalized,
            "filing_date": filing_date,
            "period_end": period_end,
            "is_amended": "/A" in form,
        })

    # Sort by period_end descending (most recent first)
    for scope in result:
        result[scope].sort(key=lambda x: x["period_end"], reverse=True)

    return result


# ── Step 2: CompanyFacts API ─────────────────────────────────────────────

def fetch_company_facts(cik: str) -> dict:
    return _sec_get(f"{SEC_FACTS_BASE}/CIK{cik}.json")


# ── Step 3: Tag resolution ──────────────────────────────────────────────

def extract_metric_by_period(
    facts: dict,
    metric_name: str,
    period_end: str,
    scope: str = "annual",
    tag_override: str | None = None,
) -> dict | None:
    """Extract a metric matching a specific period end date.

    For instant metrics (cash, debt, assets): picks entries with no start date.
    For duration metrics: quarterly = shortest, annual = longest.
    """
    is_instant = metric_name in INSTANT_METRICS

    candidates = []
    if tag_override and ":" in tag_override:
        ns, tag = tag_override.split(":", 1)
        candidates.append((ns, tag))
    for ns in NAMESPACES:
        for tag in METRIC_TAGS.get(metric_name, {}).get(ns, []):
            candidates.append((ns, tag))

    for ns, tag in candidates:
        ns_facts = facts.get(ns, {})
        tag_data = ns_facts.get(tag, {})
        units = tag_data.get("units", {})
        for currency, entries in units.items():
            matches = [e for e in entries if e.get("end") == period_end]
            if not matches:
                continue

            if is_instant:
                # Instant metrics: prefer entries without a start date
                instant_matches = [e for e in matches if "start" not in e]
                if not instant_matches:
                    continue
                best_entry = instant_matches[0]
            elif len(matches) > 1:
                # Duration disambiguation
                with_duration = []
                for m in matches:
                    start = m.get("start", "")
                    if start:
                        try:
                            from datetime import datetime
                            d_start = datetime.strptime(start, "%Y-%m-%d")
                            d_end = datetime.strptime(m["end"], "%Y-%m-%d")
                            duration = (d_end - d_start).days
                        except ValueError:
                            duration = 999
                        with_duration.append((duration, m))
                if with_duration:
                    with_duration.sort(key=lambda x: x[0])
                    if scope == "annual":
                        best_entry = with_duration[-1][1]
                    else:
                        best_entry = with_duration[0][1]
                else:
                    best_entry = matches[0]
            else:
                best_entry = matches[0]

            return {
                "namespace": ns,
                "tag_full": f"{ns}:{tag}",
                "val_M": round(best_entry["val"] / 1e6),
                "currency": currency,
            }
    return None


# ── Step 4: Orchestration ───────────────────────────────────────────────

def refresh_company(cik: str, name: str, tag_overrides: dict | None = None) -> dict:
    """Build full financial history for one company."""
    print(f"  {name} (CIK {cik})...")
    overrides = tag_overrides or {}

    # Step 1: All filings
    filings = fetch_all_filings(cik)
    time.sleep(0.1)

    # Step 2: All XBRL facts
    facts_data = fetch_company_facts(cik)
    facts = facts_data.get("facts", {})

    output = {
        "cik": cik,
        "name": name,
        "last_refreshed": date.today().isoformat(),
        "annual": [],
        "quarterly": [],
    }

    all_metrics = (
        "revenue", "rnd", "cost_of_revenue", "net_income",
        "capex", "operating_cash_flow", "operating_income", "sga",
        "cash", "total_debt", "total_assets",
    )

    for scope in ("annual", "quarterly"):
        first = True
        for filing in filings[scope]:
            period_end = filing["period_end"]

            metrics = {}
            tags_used = {}
            for metric_name in all_metrics:
                override = overrides.get(f"{metric_name}_tag")
                m = extract_metric_by_period(facts, metric_name, period_end, scope, override)
                if m:
                    metrics[metric_name] = m["val_M"]
                    tags_used[metric_name] = m["tag_full"]
                else:
                    metrics[metric_name] = None

            # Skip periods where we couldn't resolve any metric
            if not any(v is not None for v in metrics.values()):
                continue

            # Determine namespace/currency from revenue
            rev = extract_metric_by_period(facts, "revenue", period_end, scope, overrides.get("revenue_tag"))

            entry = {
                "period_end": period_end,
                "filing_date": filing["filing_date"],
                "form": filing["form"],
                "namespace": rev["namespace"] if rev else "",
                "currency": rev["currency"] if rev else "",
                "revenue_M": metrics["revenue"],
                "rnd_M": metrics["rnd"],
                "cost_of_revenue_M": metrics["cost_of_revenue"],
                "net_income_M": metrics["net_income"],
                "capex_M": metrics["capex"],
                "operating_cash_flow_M": metrics["operating_cash_flow"],
                "operating_income_M": metrics["operating_income"],
                "sga_M": metrics["sga"],
                "cash_M": metrics["cash"],
                "total_debt_M": metrics["total_debt"],
                "total_assets_M": metrics["total_assets"],
            }

            if filing.get("is_amended"):
                entry["amended"] = True

            # Include tags_used on first entry only
            if first and tags_used:
                entry["tags_used"] = tags_used
                first = False

            output[scope].append(entry)

    a_count = len(output["annual"])
    q_count = len(output["quarterly"])
    print(f"    → {a_count} annual, {q_count} quarterly periods")

    return output


def main():
    parser = argparse.ArgumentParser(description="Refresh SEC financials")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument("--cik", type=str, help="Refresh a single company by CIK")
    args = parser.parse_args()

    with open(REGISTRY_PATH) as f:
        registry = yaml.safe_load(f)

    FINANCIALS_DIR.mkdir(parents=True, exist_ok=True)

    companies = registry.get("companies", {})
    total = 0
    errors = 0

    for cik, info in companies.items():
        if args.cik and cik != args.cik:
            continue

        try:
            result = refresh_company(
                cik, info.get("name", cik),
                info.get("tag_overrides"),
            )
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            errors += 1
            continue

        time.sleep(0.2)  # rate limit

        if args.dry_run:
            total += 1
            continue

        # Merge with existing data
        json_path = FINANCIALS_DIR / f"{cik}.json"
        if json_path.exists():
            with open(json_path) as f:
                existing = json.load(f)
            for scope in ("annual", "quarterly"):
                existing_periods = {
                    (e["period_end"], e.get("filing_date", "")): e
                    for e in existing.get(scope, [])
                    if "period_end" in e
                }
                for entry in result[scope]:
                    key = (entry["period_end"], entry.get("filing_date", ""))
                    existing_periods[key] = entry  # newer data wins
                result[scope] = sorted(
                    existing_periods.values(),
                    key=lambda x: x["period_end"],
                    reverse=True,
                )

        with open(json_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        total += 1

    if args.dry_run:
        print(f"\n[dry-run] Would write {total} JSON files. {errors} errors.")
    else:
        print(f"\nRefreshed {total} companies → {FINANCIALS_DIR}/")
        if errors:
            print(f"  ⚠ {errors} errors")


if __name__ == "__main__":
    main()
