#!/usr/bin/env python3
"""Bulk CIK lookup using SEC's company_tickers.json.

Downloads SEC's bulk ticker files (one-time, ~2-3MB) and builds indexes
for exact-ticker and normalized-name matching.

Usage:
    # Lookup by ticker
    python sec/scripts/lookup_cik.py --ticker CSCO

    # Lookup by name
    python sec/scripts/lookup_cik.py --name "Cisco Systems"

    # Batch verify from a YAML/CSV file
    python sec/scripts/lookup_cik.py --verify-file candidates.yaml

    # Verify auto-discovered matches from top500 coverage doc
    python sec/scripts/lookup_cik.py --verify-mapping /path/to/tpid-cik-mapping.yaml

    # Search interactively
    python sec/scripts/lookup_cik.py --search "JPMorgan"
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
USER_AGENT = "PublicEconomicData public-economic-data@microsoft.com"
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"

# Legal suffixes to strip for normalized name matching
LEGAL_SUFFIXES = re.compile(
    r"\s*[,.]?\s*\b("
    r"inc\.?|corp\.?|co\.?|ltd\.?|plc|llc|lp|sa|ag|se|nv|n\.v\.|"
    r"ab|asa|gmbh|s\.a\.|a/s|oyj|tbk|bhd|pte|pty|srl|spa|s\.p\.a\.|"
    r"limited|incorporated|corporation|company|holdings?|group|"
    r"international|enterprises?|technologies|systems|solutions|"
    r"/de|/md|/mn|/new|/fi|/can/?"
    r")\b\.?\s*$",
    re.IGNORECASE,
)

# Common name aliases that differ between TPID names and SEC filings
NAME_ALIASES = {
    "IBM": "INTERNATIONAL BUSINESS MACHINES",
    "GOOGLE": "ALPHABET",
    "FACEBOOK": "META PLATFORMS",
    "META": "META PLATFORMS",
    "J&J": "JOHNSON & JOHNSON",
    "J AND J": "JOHNSON & JOHNSON",
    "P&G": "PROCTER & GAMBLE",
    "PEPSI": "PEPSICO",
    "COKE": "COCA-COLA",
    "BNY MELLON": "BANK OF NEW YORK MELLON",
    "UPS": "UNITED PARCEL SERVICE",
    "CITRIX": "CITRIX SYSTEMS",
    "MASTERCARD": "MASTERCARD INTERNATIONAL",
    "MOTOROLA": "MOTOROLA SOLUTIONS",
    "JPMORGAN": "JPMORGAN CHASE",
    "JP MORGAN": "JPMORGAN CHASE",
    "GE": "GENERAL ELECTRIC",
    "GM": "GENERAL MOTORS",
    "AT&T": "AT&T",
    "INTEL": "INTEL CORP",
    "WALMART": "WALMART",
    "NIKE": "NIKE",
    "ORACLE": "ORACLE",
    "CISCO": "CISCO SYSTEMS",
    "SALESFORCE": "SALESFORCE",
    "3M": "3M",
    "WELLS FARGO": "WELLS FARGO",
    "DISNEY": "WALT DISNEY",
    "WALT DISNEY": "WALT DISNEY",
    "BOEING": "BOEING",
    "CATERPILLAR": "CATERPILLAR",
    "CHEVRON": "CHEVRON",
    "EXXON": "EXXON MOBIL",
    "EXXONMOBIL": "EXXON MOBIL",
    "ALLSTATE": "ALLSTATE CORP",
    "MOODY'S": "MOODYS CORP",
    "MOODYS": "MOODYS CORP",
    "FIDELITY": "FMR",
    "DICK'S SPORTING GOODS": "DICKS SPORTING GOODS",
    "DICKS CLOTHING AND SPORTING GOODS": "DICKS SPORTING GOODS",
    "STARBUCKS": "STARBUCKS CORP",
    "JOHNSON CONTROLS": "JOHNSON CONTROLS INTERNATIONAL",
    "MORGAN STANLEY": "MORGAN STANLEY",
    "ESTEE LAUDER": "ESTEE LAUDER COMPANIES",
    "LOCKHEED MARTIN": "LOCKHEED MARTIN CORP",
    "RAYTHEON": "RTX CORP",
    "LUMEN": "LUMEN TECHNOLOGIES",
    "HEWLETT PACKARD": "HEWLETT PACKARD ENTERPRISE",
    "HP": "HP INC",
}


def _download(url: str) -> bytes:
    """Download with SEC-required User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _load_sec_tickers(use_cache: bool = True) -> list[dict]:
    """Download and cache SEC company_tickers.json.

    Returns list of {cik, ticker, name, exchange?}.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "company_tickers.json"

    if use_cache and cache_file.exists():
        with open(cache_file) as f:
            data = json.load(f)
    else:
        print("Downloading SEC company_tickers.json...", file=sys.stderr)
        raw = _download(SEC_TICKERS_URL)
        data = json.loads(raw)
        with open(cache_file, "w") as f:
            f.write(raw.decode())

    # Normalize: SEC returns {0: {cik_str, ticker, title}, 1: ...}
    entries = []
    for item in data.values():
        entries.append({
            "cik": str(item["cik_str"]).zfill(10),
            "ticker": item["ticker"].upper(),
            "name": item["title"].upper(),
        })
    return entries


def _normalize_name(name: str) -> str:
    """Normalize company name for fuzzy matching."""
    n = name.upper().strip()
    # Apply aliases
    for alias, canonical in NAME_ALIASES.items():
        if n == alias or n.startswith(alias + " "):
            n = canonical
            break
    # Strip legal suffixes (multiple passes for nested suffixes)
    for _ in range(3):
        prev = n
        n = LEGAL_SUFFIXES.sub("", n).strip()
        if n == prev:
            break
    # Remove punctuation and normalize whitespace
    n = re.sub(r"[^A-Z0-9\s&]", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def build_indexes(entries: list[dict]) -> tuple[dict, dict]:
    """Build ticker→entry and normalized_name→[entries] indexes."""
    ticker_idx = {}
    name_idx = {}

    for e in entries:
        ticker = e["ticker"]
        if ticker not in ticker_idx:
            ticker_idx[ticker] = e

        norm = _normalize_name(e["name"])
        if norm not in name_idx:
            name_idx[norm] = []
        name_idx[norm].append(e)

    return ticker_idx, name_idx


def lookup(
    query: str,
    ticker_idx: dict,
    name_idx: dict,
    query_type: str = "auto",
) -> list[dict]:
    """Look up a company by ticker or name.

    Returns list of {cik, ticker, name, match_type, confidence}.
    """
    results = []

    # Try exact ticker match first
    if query_type in ("auto", "ticker"):
        ticker = query.upper().strip()
        if ticker in ticker_idx:
            e = ticker_idx[ticker]
            results.append({
                **e,
                "match_type": "exact_ticker",
                "confidence": "high",
            })
            return results

    # Try normalized name match
    if query_type in ("auto", "name"):
        norm = _normalize_name(query)
        if norm in name_idx:
            for e in name_idx[norm]:
                results.append({
                    **e,
                    "match_type": "exact_name",
                    "confidence": "high",
                })
            if results:
                return results

        # Fuzzy: check if normalized query is a substring of any entry
        for idx_name, entries in name_idx.items():
            if norm in idx_name or idx_name in norm:
                for e in entries:
                    results.append({
                        **e,
                        "match_type": "partial_name",
                        "confidence": "medium",
                    })

    return results


def verify_mapping(mapping_path: str, ticker_idx: dict, name_idx: dict) -> None:
    """Verify CIK associations in tpid-cik-mapping.yaml.

    Checks each entry's ticker against SEC's official ticker→CIK mapping.
    Reports mismatches where the mapping has the wrong CIK for a ticker.
    """
    try:
        import yaml
    except ImportError:
        print("ERROR: pyyaml required for --verify-mapping", file=sys.stderr)
        sys.exit(1)

    with open(mapping_path) as f:
        mapping = yaml.safe_load(f)

    correct = 0
    wrong = 0
    not_found = 0
    results = []

    for tpid, info in mapping.get("tpid_to_cik", {}).items():
        cik = str(info["cik"]).zfill(10)
        ticker = info["ticker"].upper()
        name = info["name"]

        sec_entry = ticker_idx.get(ticker)
        if sec_entry:
            sec_cik = sec_entry["cik"]
            if sec_cik == cik:
                correct += 1
            else:
                wrong += 1
                results.append({
                    "tpid": tpid,
                    "name": name,
                    "ticker": ticker,
                    "mapping_cik": cik,
                    "correct_cik": sec_cik,
                    "sec_name": sec_entry["name"],
                    "status": "WRONG_CIK",
                })
        else:
            not_found += 1
            # Try name-based lookup
            name_results = lookup(name, ticker_idx, name_idx, "name")
            if name_results:
                best = name_results[0]
                results.append({
                    "tpid": tpid,
                    "name": name,
                    "ticker": ticker,
                    "mapping_cik": cik,
                    "suggested_cik": best["cik"],
                    "suggested_ticker": best["ticker"],
                    "sec_name": best["name"],
                    "match_type": best["match_type"],
                    "status": "TICKER_NOT_FOUND",
                })
            else:
                results.append({
                    "tpid": tpid,
                    "name": name,
                    "ticker": ticker,
                    "mapping_cik": cik,
                    "status": "UNRESOLVED",
                })

    # Print summary
    total = correct + wrong + not_found
    print(f"\n{'='*80}")
    print(f"Mapping Verification: {mapping_path}")
    print(f"{'='*80}")
    print(f"  Total entries:   {total}")
    print(f"  ✅ Correct:      {correct}")
    print(f"  ❌ Wrong CIK:    {wrong}")
    print(f"  ⚠️  Ticker N/F:   {not_found}")
    print()

    if results:
        # Group by status
        for status in ("WRONG_CIK", "TICKER_NOT_FOUND", "UNRESOLVED"):
            items = [r for r in results if r["status"] == status]
            if not items:
                continue
            print(f"\n--- {status} ({len(items)}) ---")
            for r in items:
                print(f"  TPID {r['tpid']:>12}  {r['name'][:40]:<40} "
                      f"ticker={r['ticker']:<8} mapping_cik={r['mapping_cik']}", end="")
                if "correct_cik" in r:
                    print(f"  → correct={r['correct_cik']} ({r['sec_name'][:30]})")
                elif "suggested_cik" in r:
                    print(f"  → suggested={r['suggested_cik']} "
                          f"({r['suggested_ticker']}, {r['sec_name'][:30]}, "
                          f"{r['match_type']})")
                else:
                    print()


def verify_registry(registry_path: str, ticker_idx: dict) -> None:
    """Verify CIK↔ticker consistency in sec/registry.yaml."""
    try:
        import yaml
    except ImportError:
        print("ERROR: pyyaml required for --verify-registry", file=sys.stderr)
        sys.exit(1)

    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    correct = 0
    wrong = 0
    not_found = 0
    results = []

    for cik_raw, info in registry["companies"].items():
        cik = str(cik_raw).zfill(10)
        ticker = info["ticker"].upper()
        name = info["name"]

        sec_entry = ticker_idx.get(ticker)
        if sec_entry:
            sec_cik = sec_entry["cik"]
            if sec_cik == cik:
                correct += 1
            else:
                wrong += 1
                results.append({
                    "cik": cik,
                    "name": name,
                    "ticker": ticker,
                    "correct_cik": sec_cik,
                    "sec_name": sec_entry["name"],
                })
        else:
            not_found += 1

    print(f"\n{'='*80}")
    print(f"Registry Verification: {registry_path}")
    print(f"{'='*80}")
    print(f"  Total entries:   {correct + wrong + not_found}")
    print(f"  ✅ Correct:      {correct}")
    print(f"  ❌ Wrong CIK:    {wrong}")
    print(f"  ⚠️  Ticker N/F:   {not_found}")
    print()

    if results:
        print("--- Wrong CIK ↔ ticker associations ---")
        for r in results:
            print(f"  registry: {r['cik']} {r['name'][:40]:<40} ticker={r['ticker']}")
            print(f"       SEC: {r['correct_cik']} {r['sec_name'][:40]}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Bulk CIK lookup using SEC data")
    parser.add_argument("--ticker", help="Look up by ticker symbol")
    parser.add_argument("--name", help="Look up by company name")
    parser.add_argument("--search", help="Fuzzy search by name or ticker")
    parser.add_argument("--verify-mapping", metavar="PATH",
                        help="Verify tpid-cik-mapping.yaml against SEC data")
    parser.add_argument("--verify-registry", metavar="PATH",
                        help="Verify sec/registry.yaml against SEC data")
    parser.add_argument("--no-cache", action="store_true",
                        help="Force re-download of SEC data")
    args = parser.parse_args()

    entries = _load_sec_tickers(use_cache=not args.no_cache)
    ticker_idx, name_idx = build_indexes(entries)
    print(f"Loaded {len(entries)} SEC filers", file=sys.stderr)

    if args.ticker:
        results = lookup(args.ticker, ticker_idx, name_idx, "ticker")
        _print_results(results, args.ticker)

    elif args.name:
        results = lookup(args.name, ticker_idx, name_idx, "name")
        _print_results(results, args.name)

    elif args.search:
        results = lookup(args.search, ticker_idx, name_idx, "auto")
        _print_results(results, args.search)

    elif args.verify_mapping:
        verify_mapping(args.verify_mapping, ticker_idx, name_idx)

    elif args.verify_registry:
        verify_registry(args.verify_registry, ticker_idx)

    else:
        parser.print_help()


def _print_results(results: list[dict], query: str) -> None:
    if not results:
        print(f"No matches for: {query}")
        return
    print(f"\nResults for '{query}':")
    for r in results[:10]:  # limit output
        print(f"  CIK {r['cik']}  {r['ticker']:<8}  {r['name'][:50]:<50}  "
              f"[{r['match_type']}, {r['confidence']}]")


if __name__ == "__main__":
    main()
