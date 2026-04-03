#!/usr/bin/env python3
"""Refresh SEC EDGAR segment-level financial data.

Extracts dimensional XBRL facts (e.g., Intelligent Cloud revenue) from
individual 10-K/10-Q filings. The standard companyfacts API only provides
consolidated totals — segment breakdowns require parsing inline XBRL from
each filing.

Usage:
    python sec/scripts/refresh_segments.py [--cik CIK] [--dry-run]
    python sec/scripts/refresh_segments.py --cik 0000789019  # Microsoft only

Architecture:
    1. Load registry.yaml for companies with segment_tags defined
    2. Get filing list from Submissions API
    3. For each filing, download the inline XBRL HTML
    4. Parse XBRL contexts to find segment-dimensioned contexts
    5. Extract revenue facts with those contexts
    6. Write to sec/financials/{cik}_segments.json
"""

import argparse
import json
import re
import time
import urllib.request
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = ROOT / "sec" / "registry.yaml"
FINANCIALS_DIR = ROOT / "sec" / "financials"

USER_AGENT = "PublicEconomicData public-economic-data@microsoft.com"


def _fetch(url: str) -> bytes:
    """Fetch URL with SEC-required User-Agent header."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _fetch_json(url: str) -> dict:
    return json.loads(_fetch(url))


def get_filings(cik: str) -> list[dict]:
    """Get all 10-K and 10-Q filings for a CIK."""
    subs = _fetch_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    recent = subs["filings"]["recent"]
    filings = []
    for i in range(len(recent["form"])):
        form = recent["form"][i]
        if form in ("10-K", "10-Q"):
            filings.append({
                "form": form,
                "accn": recent["accessionNumber"][i],
                "period": recent["reportDate"][i],
                "filed": recent["filingDate"][i],
            })
    # Also get older filings
    for older_file in subs["filings"].get("files", []):
        try:
            older = _fetch_json(f"https://data.sec.gov/submissions/{older_file['name']}")
            for i in range(len(older["form"])):
                form = older["form"][i]
                if form in ("10-K", "10-Q"):
                    filings.append({
                        "form": form,
                        "accn": older["accessionNumber"][i],
                        "period": older["reportDate"][i],
                        "filed": older["filingDate"][i],
                    })
            time.sleep(0.15)
        except Exception:
            pass
    filings.sort(key=lambda f: f["period"])
    return filings


def find_main_doc(cik: str, accn: str) -> str | None:
    """Find the main 10-K/10-Q HTML document in a filing."""
    accn_path = accn.replace("-", "")
    idx = _fetch_json(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn_path}/index.json")
    items = idx.get("directory", {}).get("item", [])
    for item in items:
        name = item.get("name", "")
        # Match patterns like msft-20250630.htm, msft-10q_20221231.htm
        if name.endswith(".htm") and not name.endswith("_htm.xml"):
            if re.match(r"msft-.*\d{8}.*\.htm$", name) or re.match(r"d\d+d10[qk]\.htm$", name):
                return name
    # Fallback: any .htm file with the company ticker
    for item in items:
        name = item.get("name", "")
        if name.endswith(".htm") and ("10q" in name.lower() or "10k" in name.lower()):
            if not name.endswith("_htm.xml"):
                return name
    return None


def extract_segment_revenue(cik: str, accn: str, doc_name: str,
                            segment_member: str) -> dict | None:
    """Extract segment revenue from inline XBRL in a filing HTML.

    Parses the HTML looking for XBRL context definitions that reference
    the segment member, then finds revenue facts using those contexts.
    """
    accn_path = accn.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn_path}/{doc_name}"
    html = _fetch(url).decode("utf-8", errors="ignore")

    # Strategy: inline XBRL embeds contexts and facts in the HTML
    # Contexts with segment dimensions look like:
    #   <xbrli:context id="...">
    #     <xbrli:entity>...</xbrli:entity>
    #     <xbrli:period>...</xbrli:period>
    #     <xbrli:segment>
    #       <xbrldi:explicitMember dimension="...">msft:IntelligentCloudMember</xbrldi:explicitMember>
    #     </xbrli:segment>
    #   </xbrli:context>

    # Extract the member name (without namespace prefix for matching)
    member_local = segment_member.split(":")[-1]

    # Find all context IDs that reference this segment member
    # Pattern: context id="XXXX" ... IntelligentCloudMember ... </context>
    context_pattern = re.compile(
        r'<xbrli:context\s+id="([^"]+)"[^>]*>.*?</xbrli:context>',
        re.DOTALL
    )
    segment_contexts = {}
    for m in context_pattern.finditer(html):
        ctx_id = m.group(1)
        ctx_body = m.group(0)
        if member_local in ctx_body:
            # Extract period info
            start_m = re.search(r'<xbrli:startDate>(\d{4}-\d{2}-\d{2})</xbrli:startDate>', ctx_body)
            end_m = re.search(r'<xbrli:endDate>(\d{4}-\d{2}-\d{2})</xbrli:endDate>', ctx_body)
            instant_m = re.search(r'<xbrli:instant>(\d{4}-\d{2}-\d{2})</xbrli:instant>', ctx_body)

            # Only want duration contexts (revenue is a duration concept)
            if start_m and end_m:
                # Check it's ONLY this segment (no additional dimensions we don't want)
                segment_contexts[ctx_id] = {
                    "start": start_m.group(1),
                    "end": end_m.group(1),
                }

    if not segment_contexts:
        return None

    # Find revenue facts with these context refs
    # Revenue tags we look for:
    revenue_tags = [
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:Revenues",
        "us-gaap:SalesRevenueNet",
    ]

    # Pattern for inline XBRL facts: <ix:nonFraction contextRef="XXX" name="us-gaap:Revenue..." ...>VALUE</ix:nonFraction>
    fact_pattern = re.compile(
        r'<ix:nonFraction[^>]+contextRef="([^"]+)"[^>]+name="([^"]+)"[^>]*>([^<]*)</ix:nonFraction>',
        re.DOTALL
    )

    revenue_facts = []
    for m in fact_pattern.finditer(html):
        ctx_ref = m.group(1)
        tag_name = m.group(2)
        raw_value = m.group(3).strip()

        if ctx_ref in segment_contexts and any(t.split(":")[-1] in tag_name for t in revenue_tags):
            # Parse the numeric value
            # Remove commas, handle negative (sign attribute)
            try:
                value = float(raw_value.replace(",", ""))
            except ValueError:
                continue

            # Check for scale/decimals attributes
            scale_m = re.search(
                rf'<ix:nonFraction[^>]+contextRef="{re.escape(ctx_ref)}"[^>]+scale="([^"]+)"',
                html
            )
            if scale_m:
                value *= 10 ** int(scale_m.group(1))

            ctx = segment_contexts[ctx_ref]
            revenue_facts.append({
                "tag": tag_name,
                "start": ctx["start"],
                "end": ctx["end"],
                "value": value,
                "context_id": ctx_ref,
            })

    if not revenue_facts:
        return None

    # Deduplicate and pick the best value per period
    # Quarterly = shortest duration, Annual = longest
    periods = {}
    for fact in revenue_facts:
        key = (fact["start"], fact["end"])
        if key not in periods or "RevenueFromContract" in fact["tag"]:
            periods[key] = fact

    return {"contexts_found": len(segment_contexts), "facts": list(periods.values())}


def refresh_segments(cik: str, company_name: str, segment_tags: dict,
                     dry_run: bool = False) -> dict:
    """Refresh segment data for one company."""
    print(f"  {company_name} (CIK {cik})...")

    filings = get_filings(cik)
    print(f"    Found {len(filings)} 10-K/10-Q filings")

    all_segments = {}
    for seg_name, seg_member in segment_tags.items():
        print(f"    Extracting segment: {seg_name} ({seg_member})")
        segment_data = []

        for f in filings:
            if f["period"] < "2015-07-01":
                continue

            try:
                doc = find_main_doc(cik, f["accn"])
                if not doc:
                    continue

                result = extract_segment_revenue(cik, f["accn"], doc, seg_member)
                if result and result["facts"]:
                    for fact in result["facts"]:
                        segment_data.append({
                            "period_end": f["period"],
                            "form": f["form"],
                            "start": fact["start"],
                            "end": fact["end"],
                            "revenue": fact["value"],
                            "tag": fact["tag"],
                        })
                    print(f"      {f['period']} ({f['form']}): {len(result['facts'])} facts")
                else:
                    print(f"      {f['period']} ({f['form']}): no segment facts found")

                time.sleep(0.3)  # Rate limit
            except Exception as e:
                print(f"      {f['period']} ({f['form']}): ERROR - {e}")
                time.sleep(1)

        all_segments[seg_name] = segment_data

    # Write output
    output = {
        "cik": cik,
        "company": company_name,
        "last_refreshed": date.today().isoformat(),
        "segments": all_segments,
    }

    if not dry_run:
        out_path = FINANCIALS_DIR / f"{cik}_segments.json"
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"    → Saved to {out_path}")

    return output


def main():
    parser = argparse.ArgumentParser(description="Refresh SEC EDGAR segment data")
    parser.add_argument("--cik", help="Single CIK to refresh")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files")
    args = parser.parse_args()

    with open(REGISTRY_PATH) as f:
        registry = yaml.safe_load(f)

    companies = registry.get("companies", {})
    if args.cik:
        companies = {k: v for k, v in companies.items() if k == args.cik}

    # Only process companies with segment_tags defined
    segment_companies = {k: v for k, v in companies.items() if v.get("segment_tags")}

    if not segment_companies:
        print("No companies with segment_tags in registry. Add segment_tags to registry.yaml.")
        return

    print(f"Refreshing segment data for {len(segment_companies)} companies...")
    for cik, info in segment_companies.items():
        refresh_segments(cik, info["name"], info["segment_tags"], args.dry_run)

    print("Done.")


if __name__ == "__main__":
    main()
