#!/usr/bin/env python3
"""Refresh FRED macro indicator data for all tracked series.

Flow:
  1. Read registry.yaml for target series
  2. FRED API → fetch observations for each series
  3. Merge with existing JSON (keep all history, deduplicate by date)
  4. Write macro/fred/{series_id}.json

Usage:
    python macro/scripts/refresh_fred.py [--dry-run] [--series-id SERIES_ID]

Requires: FRED_API_KEY environment variable.
Rate limit: 120 requests/minute.
"""

import argparse
import json
import os
import time
import urllib.request
import urllib.parse
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = ROOT / "macro" / "registry.yaml"
FRED_DIR = ROOT / "macro" / "fred"

FRED_BASE = "https://api.stlouisfed.org/fred"
USER_AGENT = "PublicEconomicData public-economic-data@microsoft.com"


def _fred_get(endpoint: str, params: dict) -> dict:
    """Fetch JSON from FRED API."""
    qs = urllib.parse.urlencode(params)
    url = f"{FRED_BASE}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_series_info(series_id: str, api_key: str) -> dict:
    """Get metadata for a series (title, frequency, units)."""
    data = _fred_get("series", {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    })
    seriess = data.get("seriess", [])
    if not seriess:
        raise ValueError(f"Series {series_id} not found in FRED")
    s = seriess[0]
    return {
        "title": s.get("title", ""),
        "frequency": s.get("frequency_short", "").lower(),
        "units": s.get("units", ""),
    }


def fetch_observations(series_id: str, api_key: str) -> list[dict]:
    """Fetch all observations for a series.

    Returns list of {"date": "YYYY-MM-DD", "value": float} sorted by date descending.
    Skips entries where FRED reports "." (missing value).
    """
    data = _fred_get("series/observations", {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
    })
    observations = []
    for obs in data.get("observations", []):
        val_str = obs.get("value", ".")
        if val_str == ".":
            continue
        try:
            value = float(val_str)
        except (ValueError, TypeError):
            continue
        observations.append({
            "date": obs["date"],
            "value": value,
        })
    return observations


def refresh_series(
    series_id: str,
    registry_info: dict,
    api_key: str,
) -> dict:
    """Build full data file for one FRED series."""
    print(f"  {series_id} — {registry_info.get('title', '')}...")

    # Fetch live metadata from FRED
    info = fetch_series_info(series_id, api_key)
    time.sleep(0.5)  # rate limit

    # Fetch observations
    observations = fetch_observations(series_id, api_key)
    time.sleep(0.5)

    # Map FRED frequency codes to human-readable
    freq_map = {"q": "quarterly", "m": "monthly", "a": "annual",
                "w": "weekly", "d": "daily", "bw": "biweekly", "sa": "semiannual"}
    frequency = freq_map.get(info["frequency"], info["frequency"])

    output = {
        "series_id": series_id,
        "title": info["title"],
        "frequency": frequency,
        "units": info["units"],
        "last_refreshed": date.today().isoformat(),
        "observations": observations,
    }

    print(f"    → {len(observations)} observations")
    return output


def main():
    parser = argparse.ArgumentParser(description="Refresh FRED macro indicators")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument("--series-id", type=str, help="Refresh a single series")
    args = parser.parse_args()

    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("⚠ FRED_API_KEY environment variable not set")
        print("  Register at: https://fred.stlouisfed.org/docs/api/api_key.html")
        raise SystemExit(1)

    with open(REGISTRY_PATH) as f:
        registry = yaml.safe_load(f)

    FRED_DIR.mkdir(parents=True, exist_ok=True)

    series_map = registry.get("series", {})
    total = 0
    errors = 0

    for series_id, info in series_map.items():
        if args.series_id and series_id != args.series_id:
            continue

        try:
            result = refresh_series(series_id, info, api_key)
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            errors += 1
            continue

        if args.dry_run:
            total += 1
            continue

        # Merge with existing data (keep all history, deduplicate by date)
        json_path = FRED_DIR / f"{series_id}.json"
        if json_path.exists():
            with open(json_path) as f:
                existing = json.load(f)
            existing_by_date = {o["date"]: o for o in existing.get("observations", [])}
            for obs in result["observations"]:
                existing_by_date[obs["date"]] = obs  # newer data wins
            result["observations"] = sorted(
                existing_by_date.values(),
                key=lambda x: x["date"],
                reverse=True,
            )

        with open(json_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        total += 1

    if args.dry_run:
        print(f"\n[dry-run] Would write {total} JSON files. {errors} errors.")
    else:
        print(f"\nRefreshed {total} series → {FRED_DIR}/")
        if errors:
            print(f"⚠ {errors} errors occurred.")


if __name__ == "__main__":
    main()
