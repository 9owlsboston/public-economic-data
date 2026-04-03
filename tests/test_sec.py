#!/usr/bin/env python3
"""Validation tests for SEC financial data.

Run: python tests/test_sec.py
These are data validation tests, not unit tests — they verify the
integrity of the JSON data files, not the refresh script logic.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
FINANCIALS_DIR = ROOT / "sec" / "financials"

REQUIRED_FIELDS = ["cik", "name", "last_refreshed", "annual", "quarterly"]
ENTRY_FIELDS = ["period_end", "filing_date", "form", "revenue_M"]


def _standard_files():
    """Return standard company financials files, excluding segment files."""
    return sorted(f for f in FINANCIALS_DIR.glob("*.json") if "_segments" not in f.stem)


def test_all_json_valid():
    """Every .json file should parse without errors."""
    errors = []
    for f in sorted(FINANCIALS_DIR.glob("*.json")):
        try:
            json.loads(f.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: {e}")
    return errors


def test_required_fields():
    """Every standard JSON file should have the required top-level fields."""
    errors = []
    for f in _standard_files():
        data = json.loads(f.read_text())
        for field in REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"{f.name}: missing '{field}'")
    return errors


def test_annual_sorted_descending():
    """Annual entries should be sorted by period_end descending."""
    errors = []
    for f in _standard_files():
        data = json.loads(f.read_text())
        periods = [e["period_end"] for e in data.get("annual", []) if "period_end" in e]
        if periods != sorted(periods, reverse=True):
            errors.append(f"{f.name}: annual not sorted descending")
    return errors


def test_no_null_revenue_in_annual():
    """At least the most recent annual entry should have non-null revenue."""
    errors = []
    for f in _standard_files():
        data = json.loads(f.read_text())
        annual = data.get("annual", [])
        if annual and annual[0].get("revenue_M") is None:
            errors.append(f"{f.name}: latest annual has null revenue (not disclosed)")
    return errors


def test_cik_matches_filename():
    """The CIK in JSON content should match the filename."""
    errors = []
    for f in _standard_files():
        data = json.loads(f.read_text())
        expected_cik = f.stem
        actual_cik = data.get("cik", "")
        if actual_cik != expected_cik:
            errors.append(f"{f.name}: CIK '{actual_cik}' != filename '{expected_cik}'")
    return errors


def test_freshness():
    """Warn if last_refreshed is more than 120 days old."""
    from datetime import date, timedelta
    threshold = date.today() - timedelta(days=120)
    warnings = []
    for f in _standard_files():
        data = json.loads(f.read_text())
        refreshed = data.get("last_refreshed", "")
        if refreshed and refreshed < threshold.isoformat():
            warnings.append(f"{f.name}: last_refreshed={refreshed} (>120 days)")
    return warnings


def main():
    tests = [
        ("JSON parseable", test_all_json_valid, True),
        ("Required fields", test_required_fields, True),
        ("Annual sorted desc", test_annual_sorted_descending, True),
        ("Revenue not null", test_no_null_revenue_in_annual, False),
        ("CIK matches filename", test_cik_matches_filename, True),
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

    file_count = len(list(FINANCIALS_DIR.glob("*.json")))
    print(f"\n{file_count} files checked. {total_errors} errors.")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
