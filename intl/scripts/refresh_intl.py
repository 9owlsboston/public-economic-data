#!/usr/bin/env python3
"""Refresh international company financial data via Yahoo Finance (yfinance).

Fetches income statements, balance sheets, and cash flow statements
for companies listed in intl/registry.yaml and writes per-company JSON
to intl/financials/{isin}.json.

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
    """Fetch annual and quarterly financials for a company via yfinance.

    Pulls income statement, balance sheet, and cash flow statement.
    Returns a dict matching the repo's standard schema, or None on error.
    """
    ticker = yf.Ticker(yf_symbol)
    inc = ticker.financials  # columns = dates, rows = line items

    if inc is None or inc.empty:
        return None

    bs = ticker.balance_sheet
    cf = ticker.cashflow

    currency = info.get("currency", "EUR")

    def _extract_entries(inc_df, bs_df, cf_df):
        """Extract financial entries by merging income, balance sheet, and cash flow."""
        entries = []
        if inc_df is None or inc_df.empty:
            return entries

        # Build lookup for balance sheet and cash flow by period_end
        bs_by_period = {}
        if bs_df is not None and not bs_df.empty:
            for col in bs_df.columns:
                bs_by_period[col.date().isoformat()] = bs_df[col]

        cf_by_period = {}
        if cf_df is not None and not cf_df.empty:
            for col in cf_df.columns:
                cf_by_period[col.date().isoformat()] = cf_df[col]

        for i, col in enumerate(inc_df.columns):
            period_end = col.date().isoformat()

            def _get(label, _df=inc_df, _col=col):
                return _df.loc[label, _col] if label in _df.index else None

            bs_col = bs_by_period.get(period_end)
            cf_col = cf_by_period.get(period_end)

            def _bs(label):
                if bs_col is None:
                    return None
                return bs_col.loc[label] if label in bs_col.index else None

            def _cf(label):
                if cf_col is None:
                    return None
                return cf_col.loc[label] if label in cf_col.index else None

            # Capex is reported as negative in yfinance; store as positive
            capex_raw = _cf("Capital Expenditure")
            capex_M = _to_millions(abs(capex_raw)) if capex_raw is not None and not (isinstance(capex_raw, float) and math.isnan(capex_raw)) else None

            entry = {
                "period_end": period_end,
                "currency": currency,
                "revenue_M": _to_millions(_get("Total Revenue")),
                "rnd_M": _to_millions(_get("Research And Development")),
                "cost_of_revenue_M": _to_millions(_get("Cost Of Revenue")),
                "net_income_M": _to_millions(_get("Net Income")),
                "operating_income_M": _to_millions(_get("Operating Income")),
                "sga_M": _to_millions(_get("Selling General And Administration")),
                "capex_M": capex_M,
                "operating_cash_flow_M": _to_millions(_cf("Operating Cash Flow")),
                "cash_M": _to_millions(_bs("Cash And Cash Equivalents")),
                "total_debt_M": _to_millions(_bs("Total Debt")),
                "total_assets_M": _to_millions(_bs("Total Assets")),
            }
            if i == 0:
                entry["tags_used"] = {
                    "source": "yahoo_finance",
                    "notes": "Income statement + balance sheet + cash flow, converted to millions",
                }
            entries.append(entry)
        entries.sort(key=lambda x: x["period_end"], reverse=True)
        return entries

    annual = _extract_entries(inc, bs, cf)

    # Quarterly financials
    q_inc = ticker.quarterly_financials
    q_bs = ticker.quarterly_balance_sheet
    q_cf = ticker.quarterly_cashflow
    quarterly = _extract_entries(q_inc, q_bs, q_cf)

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
            for section in ("annual", "quarterly"):
                # Skip legacy entries that lack period_end (old schema used "year")
                existing_periods = {
                    e["period_end"]: e
                    for e in existing.get(section, [])
                    if "period_end" in e
                }
                for entry in result.get(section, []):
                    existing_periods[entry["period_end"]] = entry  # newer wins
                result[section] = sorted(
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
