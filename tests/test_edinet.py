#!/usr/bin/env python3
"""Validation tests for EDINET (Japanese) financial data.

Run: python tests/test_edinet.py
Validates JSON structure, freshness, and data quality for EDINET-sourced data.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
FINANCIALS_DIR = ROOT / "edinet" / "financials"

REQUIRED_FIELDS = ["edinet_code", "name", "last_refreshed", "annual"]
ENTRY_FIELDS = ["period_end", "filing_date", "form", "currency", "revenue_M"]


def _all_files():
    """Return all JSON files in edinet/financials/."""
    return sorted(FINANCIALS_DIR.glob("*.json"))


def test_all_json_valid():
    """Every .json file should parse without errors."""
    errors = []
    for f in _all_files():
        try:
            json.loads(f.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: {e}")
    assert not errors, errors


def test_required_fields():
    """Every JSON file should have the required top-level fields."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        for field in REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"{f.name}: missing '{field}'")
    assert not errors, errors


def test_annual_sorted_descending():
    """Annual entries should be sorted by period_end descending."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        periods = [e["period_end"] for e in data.get("annual", []) if "period_end" in e]
        if periods != sorted(periods, reverse=True):
            errors.append(f"{f.name}: annual not sorted descending")
    assert not errors, errors


def test_no_null_revenue_in_annual():
    """At least the most recent annual entry should have non-null revenue."""
    import warnings
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        annual = data.get("annual", [])
        if annual and annual[0].get("revenue_M") is None:
            errors.append(f"{f.name}: latest annual has null revenue")
    for e in errors:
        warnings.warn(e)


def test_edinet_code_matches_filename():
    """The EDINET code in JSON content should match the filename."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        expected = f.stem
        actual = data.get("edinet_code", "")
        if actual != expected:
            errors.append(f"{f.name}: edinet_code '{actual}' != filename '{expected}'")
    assert not errors, errors


def test_currency_is_jpy():
    """All entries should have currency=JPY."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        for entry in data.get("annual", []):
            if entry.get("currency") != "JPY":
                errors.append(f"{f.name}: {entry.get('period_end')} currency is '{entry.get('currency')}', expected 'JPY'")
                break
    assert not errors, errors


def test_freshness():
    """Warn if last_refreshed is more than 120 days old."""
    import warnings
    from datetime import date, timedelta
    threshold = date.today() - timedelta(days=120)
    for f in _all_files():
        data = json.loads(f.read_text())
        refreshed = data.get("last_refreshed", "")
        if refreshed and refreshed < threshold.isoformat():
            warnings.warn(f"{f.name}: last_refreshed={refreshed} (>120 days)")


def main():
    if not FINANCIALS_DIR.exists() or not list(_all_files()):
        print("⚠️  No edinet/financials/ data files found. Run refresh_edinet.py first.")
        return 0

    tests = [
        ("JSON parseable", test_all_json_valid, True),
        ("Required fields", test_required_fields, True),
        ("Annual sorted desc", test_annual_sorted_descending, True),
        ("Revenue not null", test_no_null_revenue_in_annual, False),
        ("EDINET code matches filename", test_edinet_code_matches_filename, True),
        ("Currency is JPY", test_currency_is_jpy, True),
        ("Freshness (<120 days)", test_freshness, False),
    ]

    total_errors = 0
    for name, test_fn, is_error in tests:
        issues = test_fn()
        if is_error:
            status = "✅" if not issues else "❌"
        else:
            status = "✅" if not issues else "⚠️"
        print(f"{status} {name}")
        for issue in issues:
            print(f"   {issue}")
            if is_error:
                total_errors += 1

    file_count = len(_all_files())
    print(f"\n{file_count} files checked. {total_errors} errors.")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
