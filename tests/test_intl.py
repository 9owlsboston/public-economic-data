#!/usr/bin/env python3
"""Validation tests for international company financial data.

Run: python tests/test_intl.py
Validates JSON structure, freshness, and data quality for Yahoo Finance-sourced data.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
FINANCIALS_DIR = ROOT / "intl" / "financials"

REQUIRED_FIELDS = ["isin", "name", "source", "last_refreshed", "annual"]
ENTRY_FIELDS = ["period_end", "currency", "revenue_M"]


def _all_files():
    """Return all JSON files in intl/financials/."""
    return sorted(FINANCIALS_DIR.glob("*.json"))


def test_all_json_valid():
    """Every .json file should parse without errors."""
    errors = []
    for f in _all_files():
        try:
            json.loads(f.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: {e}")
    return errors


def test_required_fields():
    """Every JSON file should have the required top-level fields."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        for field in REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"{f.name}: missing '{field}'")
    return errors


def test_annual_sorted_descending():
    """Annual entries should be sorted by period_end descending."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        periods = [e["period_end"] for e in data.get("annual", []) if "period_end" in e]
        if periods != sorted(periods, reverse=True):
            errors.append(f"{f.name}: annual not sorted descending")
    return errors


def test_no_null_revenue_in_annual():
    """At least the most recent annual entry should have non-null revenue."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        annual = data.get("annual", [])
        if annual and annual[0].get("revenue_M") is None:
            errors.append(f"{f.name}: latest annual has null revenue")
    return errors


def test_isin_matches_filename():
    """The ISIN in JSON content should match the filename."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        expected_isin = f.stem
        actual_isin = data.get("isin", "")
        if actual_isin != expected_isin:
            errors.append(f"{f.name}: ISIN '{actual_isin}' != filename '{expected_isin}'")
    return errors


def test_source_field():
    """All entries should have a source field."""
    errors = []
    for f in _all_files():
        data = json.loads(f.read_text())
        if not data.get("source"):
            errors.append(f"{f.name}: missing 'source' field")
    return errors


def test_freshness():
    """Warn if last_refreshed is more than 120 days old."""
    from datetime import date, timedelta
    threshold = date.today() - timedelta(days=120)
    warnings = []
    for f in _all_files():
        data = json.loads(f.read_text())
        refreshed = data.get("last_refreshed", "")
        if refreshed and refreshed < threshold.isoformat():
            warnings.append(f"{f.name}: last_refreshed={refreshed} (>120 days)")
    return warnings


def main():
    if not FINANCIALS_DIR.exists() or not list(_all_files()):
        print("⚠️  No intl/financials/ data files found. Run refresh_intl.py first.")
        return 0

    tests = [
        ("JSON parseable", test_all_json_valid, True),
        ("Required fields", test_required_fields, True),
        ("Annual sorted desc", test_annual_sorted_descending, True),
        ("Revenue not null", test_no_null_revenue_in_annual, False),
        ("ISIN matches filename", test_isin_matches_filename, True),
        ("Source field present", test_source_field, True),
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
