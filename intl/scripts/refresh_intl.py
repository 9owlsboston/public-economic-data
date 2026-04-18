#!/usr/bin/env python3
"""Refresh international company financial data via Yahoo Finance (yfinance).

Fetches income statements for companies listed in intl/registry.yaml
and writes per-company JSON to intl/financials/{isin}.json.

Usage:
    python intl/scripts/refresh_intl.py [--dry-run] [--isin ISIN]

Requires: pip install yfinance pyyaml
No API key needed — Yahoo Finance is free.
"""

import argparse
import json
import math
import time
from datetime import date
from pathlib import Path

import yaml
import yfinance as yf

ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = ROOT / "intl" / "registry.yaml"
FINANCIALS_DIR = ROOT / "intl" / "financials"


def _to_millions(value) -> int | None:
    """Convert full-unit value to millions (integer)."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return round(value / 1_000_000)


def refresh_company(yf_symbol: str, info: dict) -> dict | None:
    """Fetch annual and quarterly income statements for a company via yfinance.

    Returns a dict matching the repo's standard schema, or None on error.
    """
    ticker = yf.Ticker(yf_symbol)
    inc = ticker.financials  # columns = dates, rows = line items

    if inc is None or inc.empty:
        return None

    currency = info.get("currency", "EUR")

    def _extract_entries(df):
        """Extract financial entries from a yfinance DataFrame."""
        entries = []
        if df is None or df.empty:
            return entries
        for i, col in enumerate(df.columns):
            def _get(label, _df=df, _col=col):
                return _df.loc[label, _col] if label in _df.index else None

            entry = {
                "period_end": col.date().isoformat(),
                "currency": currency,
                "revenue_M": _to_millions(_get("Total Revenue")),
                "rnd_M": _to_millions(_get("Research And Development")),
                "cost_of_revenue_M": _to_millions(_get("Cost Of Revenue")),
                "net_income_M": _to_millions(_get("Net Income")),
            }
            if i == 0:
                entry["tags_used"] = {
                    "source": "yahoo_finance",
                    "notes": "Values converted from full units to millions via yfinance",
                }
            entries.append(entry)
        entries.sort(key=lambda x: x["period_end"], reverse=True)
        return entries

    annual = _extract_entries(inc)

    # Quarterly financials
    q_inc = ticker.quarterly_financials
    quarterly = _extract_entries(q_inc)

    return {
        "isin": None,  # filled in by caller
        "name": info.get("name", yf_symbol),
        "ticker": info.get("ticker", ""),
        "exchange": info.get("exchange", ""),
        "source": "yahoo_finance",
        "last_refreshed": date.today().isoformat(),
        "annual": annual,
        "quarterly": quarterly,
    }


def main():
    parser = argparse.ArgumentParser(description="Refresh international financials via Yahoo Finance")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument("--isin", type=str, help="Refresh a single company by ISIN")
    args = parser.parse_args()

    with open(REGISTRY_PATH) as f:
        registry = yaml.safe_load(f)

    FINANCIALS_DIR.mkdir(parents=True, exist_ok=True)

    companies = registry.get("companies", {})
    total = 0
    errors = 0

    for isin, info in companies.items():
        if args.isin and isin != args.isin:
            continue

        yf_symbol = info.get("yf_symbol")
        if not yf_symbol:
            print(f"  ⚠ {isin}: no yf_symbol in registry, skipping")
            errors += 1
            continue

        print(f"  {info.get('name', isin)} ({yf_symbol})...")

        try:
            result = refresh_company(yf_symbol, info)
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            errors += 1
            continue

        if not result:
            print("    ⚠ No data returned")
            errors += 1
            continue

        result["isin"] = isin

        a_count = len(result["annual"])
        print(f"    → {a_count} annual periods")

        time.sleep(1.0)  # be polite to Yahoo

        if args.dry_run:
            total += 1
            continue

        # Merge with existing data
        json_path = FINANCIALS_DIR / f"{isin}.json"
        if json_path.exists():
            with open(json_path) as f:
                existing = json.load(f)
            # Skip legacy entries that lack period_end (old schema used "year")
            existing_periods = {
                e["period_end"]: e
                for e in existing.get("annual", [])
                if "period_end" in e
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
