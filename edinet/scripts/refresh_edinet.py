#!/usr/bin/env python3
"""Refresh Japanese company financial data via EDINET API.

Fetches 有価証券報告書 (Annual Securities Reports) for companies listed
in edinet/registry.yaml and extracts IFRS financial facts from iXBRL.

Usage:
    python edinet/scripts/refresh_edinet.py [--dry-run] [--edinet-code CODE]

Requires EDINET_API_KEY environment variable.
Register (free) at https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1
"""

import argparse
import io
import json
import os
import re
import time
import urllib.request
import zipfile
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = ROOT / "edinet" / "registry.yaml"
FINANCIALS_DIR = ROOT / "edinet" / "financials"

EDINET_BASE = "https://api.edinet-fsa.go.jp/api/v2"
USER_AGENT = "PublicEconomicData public-economic-data@microsoft.com"

# Annual Securities Report
DOC_TYPE_ANNUAL = "120"

# IFRS financial tags to extract from iXBRL.
# Format: {metric_name: [(namespace_suffix, tag_name), ...]}
# Priority order: first match wins.
# Tags may appear in jpigp_cor (standard) or company-specific namespace.
METRIC_TAGS = {
    "revenue_M": [
        ("jpigp_cor", "RevenueIFRS"),
        ("jpigp_cor", "OperatingRevenueIFRS"),
        # Company-specific revenue tags (e.g., NTT uses OperatingRevenuesIFRS)
        (None, "OperatingRevenuesIFRS"),
        (None, "RevenueIFRS"),
        (None, "RevenueFromContractsWithCustomersIFRS"),
    ],
    "operating_income_M": [
        ("jpigp_cor", "OperatingProfitLossIFRS"),
        (None, "OperatingProfitLossIFRS"),
    ],
    "net_income_M": [
        ("jpigp_cor", "ProfitLossAttributableToOwnersOfParentIFRS"),
        ("jpigp_cor", "ProfitLossIFRS"),
        (None, "ProfitLossAttributableToOwnersOfParentIFRS"),
    ],
    "cost_of_revenue_M": [
        ("jpigp_cor", "CostOfSalesIFRS"),
        (None, "CostOfSalesIFRS"),
    ],
    "rnd_M": [
        ("jpigp_cor", "ResearchAndDevelopmentExpenseIFRS"),
        (None, "ResearchAndDevelopmentExpenseIFRS"),
    ],
}


def _edinet_get(endpoint: str, params: dict, api_key: str) -> dict | None:
    """GET from EDINET API, return parsed JSON."""
    params["Subscription-Key"] = api_key
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{EDINET_BASE}/{endpoint}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"    ⚠ API error: {e}")
        return None


def _edinet_download_zip(doc_id: str, api_key: str) -> zipfile.ZipFile | None:
    """Download XBRL ZIP for a document, return ZipFile object."""
    url = f"{EDINET_BASE}/documents/{doc_id}?type=1&Subscription-Key={api_key}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        return zipfile.ZipFile(io.BytesIO(data))
    except Exception as e:
        print(f"    ⚠ Download error for {doc_id}: {e}")
        return None


def _parse_ixbrl_facts(zip_file: zipfile.ZipFile) -> dict[str, list[dict]]:
    """Extract IFRS financial facts from iXBRL HTML files in a ZIP.

    Returns {tag_suffix: [{context, value}, ...]} for all matching tags.
    """
    facts = {}

    # Find iXBRL files in PublicDoc
    ixbrl_files = [
        n for n in zip_file.namelist()
        if "PublicDoc" in n and n.endswith("_ixbrl.htm")
    ]

    for fname in ixbrl_files:
        with zip_file.open(fname) as f:
            content = f.read().decode("utf-8", errors="replace")

        # Extract ix:nonFraction elements: name, contextRef, and text value
        # Handle both self-closing and normal elements, and ix:nonFraction with sign attribute
        pattern = (
            r'<ix:nonFraction[^>]*'
            r'name="([^"]+)"[^>]*'
            r'contextRef="([^"]+)"[^>]*'
            r'(?:sign="([^"]*)")?[^>]*>'
            r'([^<]*)'
            r'</ix:nonFraction>'
        )
        for match in re.finditer(pattern, content):
            name, ctx, sign, val_str = match.groups()
            val_str = val_str.strip().replace(",", "")
            if not val_str:
                continue
            try:
                val = int(val_str)
                if sign == "-":
                    val = -val
            except ValueError:
                try:
                    val = float(val_str)
                    if sign == "-":
                        val = -val
                except ValueError:
                    continue

            # Split name into prefix:tag
            parts = name.split(":")
            if len(parts) == 2:
                tag_suffix = parts[1]
            else:
                tag_suffix = name

            if tag_suffix not in facts:
                facts[tag_suffix] = []
            facts[tag_suffix].append({"context": ctx, "value": val, "full_name": name})

    return facts


def _extract_metric(facts: dict, metric: str, context_prefix: str) -> tuple[int | None, str | None]:
    """Extract a metric value from parsed facts for a given context prefix.

    Returns (value_in_millions, tag_used) or (None, None).
    """
    candidates = METRIC_TAGS.get(metric, [])
    for ns_prefix, tag_suffix in candidates:
        entries = facts.get(tag_suffix, [])
        for entry in entries:
            ctx = entry["context"]
            full_name = entry["full_name"]

            # Match context (e.g., "CurrentYearDuration" or "Prior1YearDuration")
            if not ctx.startswith(context_prefix):
                continue

            # Skip member-specific contexts (equity breakdown rows)
            if "Member" in ctx:
                continue

            # If namespace prefix specified, check it matches
            if ns_prefix and not full_name.startswith(f"{ns_prefix}:"):
                continue

            # Value is already in millions (EDINET IFRS uses decimals=-6 convention)
            return entry["value"], full_name

    return None, None


def _find_annual_filings(edinet_code: str, api_key: str, years_back: int = 8) -> list[dict]:
    """Find annual securities reports for a company by scanning filing dates.

    Returns list of {docID, periodStart, periodEnd, submitDateTime}.
    Japanese FY typically ends March 31, filed in June.
    """
    filings = []
    today = date.today()

    # Scan June of each year (when March-end FY companies file)
    for years_ago in range(0, years_back):
        year = today.year - years_ago
        for month in [6, 7]:  # Most file in June, some in July
            for day in range(1, 31):
                try:
                    d = date(year, month, day)
                except ValueError:
                    continue
                if d > today:
                    continue

                data = _edinet_get("documents.json", {"date": d.isoformat(), "type": "2"}, api_key)
                if not data:
                    continue

                for r in data.get("results", []):
                    if r.get("edinetCode") == edinet_code and r.get("docTypeCode") == DOC_TYPE_ANNUAL:
                        # Avoid duplicates
                        if not any(f["docID"] == r["docID"] for f in filings):
                            filings.append({
                                "docID": r["docID"],
                                "periodStart": r.get("periodStart"),
                                "periodEnd": r.get("periodEnd"),
                                "submitDateTime": r.get("submitDateTime"),
                                "description": r.get("docDescription"),
                            })
                            print(f"    Found: {r.get('docDescription')} (period ending {r.get('periodEnd')})")

                time.sleep(0.5)  # rate limit

            # If we found a filing for this year, skip remaining months
            if any(f["periodEnd"] and f["periodEnd"].startswith(str(year)) for f in filings):
                break

    return sorted(filings, key=lambda x: x.get("periodEnd", ""), reverse=True)


def refresh_company(edinet_code: str, info: dict, api_key: str) -> dict | None:
    """Fetch and parse annual financial data for one EDINET company."""
    print(f"    Searching for annual filings...")
    filings = _find_annual_filings(edinet_code, api_key)

    if not filings:
        return None

    annual = []
    for i, filing in enumerate(filings):
        doc_id = filing["docID"]
        period_end = filing.get("periodEnd", "")

        print(f"    Downloading {doc_id} (period ending {period_end})...")
        zip_file = _edinet_download_zip(doc_id, api_key)
        if not zip_file:
            continue

        time.sleep(1.0)  # rate limit after download

        facts = _parse_ixbrl_facts(zip_file)

        # Extract metrics for CurrentYearDuration
        entry = {
            "period_end": period_end,
            "filing_date": (filing.get("submitDateTime") or "")[:10],
            "form": "有価証券報告書",
            "namespace": "jpigp_cor",
            "currency": info.get("currency", "JPY"),
        }

        tags_used = {}
        for metric in METRIC_TAGS:
            val, tag = _extract_metric(facts, metric, "CurrentYearDuration")
            entry[metric] = val
            if tag and i == 0:
                tags_used[metric] = tag

        if i == 0 and tags_used:
            entry["tags_used"] = tags_used

        annual.append(entry)

    if not annual:
        return None

    # Sort descending by period_end
    annual.sort(key=lambda x: x["period_end"], reverse=True)

    return {
        "edinet_code": edinet_code,
        "name": info.get("name", edinet_code),
        "ticker": info.get("ticker", ""),
        "exchange": info.get("exchange", ""),
        "last_refreshed": date.today().isoformat(),
        "annual": annual,
    }


def main():
    parser = argparse.ArgumentParser(description="Refresh EDINET financials")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument("--edinet-code", type=str, help="Refresh a single company by EDINET code")
    args = parser.parse_args()

    api_key = os.environ.get("EDINET_API_KEY")
    if not api_key:
        print("Error: EDINET_API_KEY environment variable is required.")
        print("Register at https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1")
        raise SystemExit(1)

    with open(REGISTRY_PATH) as f:
        registry = yaml.safe_load(f)

    FINANCIALS_DIR.mkdir(parents=True, exist_ok=True)

    companies = registry.get("companies", {})
    total = 0
    errors = 0

    for edinet_code, info in companies.items():
        if args.edinet_code and edinet_code != args.edinet_code:
            continue

        print(f"  {info.get('name', edinet_code)} ({edinet_code})...")

        try:
            result = refresh_company(edinet_code, info, api_key)
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            errors += 1
            continue

        if not result:
            print("    ⚠ No data returned")
            errors += 1
            continue

        a_count = len(result["annual"])
        print(f"    → {a_count} annual periods")

        if args.dry_run:
            total += 1
            continue

        # Merge with existing data
        json_path = FINANCIALS_DIR / f"{edinet_code}.json"
        if json_path.exists():
            with open(json_path) as f:
                existing = json.load(f)
            existing_periods = {
                e["period_end"]: e for e in existing.get("annual", [])
            }
            for entry in result["annual"]:
                existing_periods[entry["period_end"]] = entry  # newer wins
            result["annual"] = sorted(
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
