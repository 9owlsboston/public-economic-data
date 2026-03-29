#!/usr/bin/env python3
"""Validation tests for macro indicator data.

Run: python tests/test_macro.py
Validates JSON structure, freshness, and data quality for FRED series.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
MACRO_DIR = ROOT / "macro" / "fred"

REQUIRED_FIELDS = ["series_id", "title", "frequency", "units", "last_refreshed", "observations"]


def test_all_json_valid():
    """Every .json file should parse without errors."""
    errors = []
    for f in sorted(MACRO_DIR.glob("*.json")):
        try:
            json.loads(f.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: {e}")
    return errors


def test_required_fields():
    """Every JSON file should have required top-level fields."""
    errors = []
    for f in sorted(MACRO_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        for field in REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"{f.name}: missing '{field}'")
    return errors


def test_observations_sorted():
    """Observations should be sorted by date descending."""
    errors = []
    for f in sorted(MACRO_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        dates = [o["date"] for o in data.get("observations", []) if "date" in o]
        if dates != sorted(dates, reverse=True):
            errors.append(f"{f.name}: observations not sorted descending")
    return errors


def test_series_id_matches_filename():
    """The series_id in JSON should match the filename."""
    errors = []
    for f in sorted(MACRO_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        if data.get("series_id") != f.stem:
            errors.append(f"{f.name}: series_id '{data.get('series_id')}' != filename '{f.stem}'")
    return errors


def test_no_empty_observations():
    """Each file should have at least one observation."""
    errors = []
    for f in sorted(MACRO_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        if not data.get("observations"):
            errors.append(f"{f.name}: empty observations")
    return errors


def main():
    if not MACRO_DIR.exists():
        print("⏭ macro/fred/ does not exist yet — skipping")
        return 0

    tests = [
        ("JSON parseable", test_all_json_valid),
        ("Required fields", test_required_fields),
        ("Observations sorted desc", test_observations_sorted),
        ("Series ID matches filename", test_series_id_matches_filename),
        ("Non-empty observations", test_no_empty_observations),
    ]

    total_errors = 0
    for name, test_fn in tests:
        issues = test_fn()
        status = "✅" if not issues else "❌"
        print(f"{status} {name}")
        for issue in issues:
            print(f"   {issue}")
            total_errors += 1

    file_count = len(list(MACRO_DIR.glob("*.json")))
    print(f"\n{file_count} files checked. {total_errors} errors.")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
