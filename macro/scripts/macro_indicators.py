"""Helper module for reading FRED macro indicator data.

Reads per-series JSON files from macro/fred/{series_id}.json.
Works both locally (file path) and via GitHub raw URL.

Usage:
    from macro_indicators import MacroIndicators

    macro = MacroIndicators()  # local mode
    macro = MacroIndicators(github_url="https://raw.githubusercontent.com/...")

    gdp = macro.latest("GDPC1")
    growth = macro.yoy_growth("GDPC1")
    trend = macro.trend("PCU518210518210", 12)
"""

import json
import urllib.request
from pathlib import Path


class MacroIndicators:
    """Read FRED macro indicator data from local JSON files or GitHub raw URLs."""

    def __init__(
        self,
        local_dir: str | Path | None = None,
        github_url: str | None = None,
        github_token: str | None = None,
    ):
        if github_url:
            self._mode = "github"
            self._github_url = github_url.rstrip("/")
            self._github_token = github_token
        else:
            self._mode = "local"
            if local_dir:
                self._dir = Path(local_dir)
            else:
                self._dir = Path(__file__).parent.parent / "macro" / "fred"
                if not self._dir.exists():
                    self._dir = Path(__file__).parent / "fred"
        self._cache: dict[str, dict] = {}

    def get(self, series_id: str) -> dict | None:
        """Load full data for a FRED series.

        Returns the parsed JSON or None if not found.
        """
        if series_id in self._cache:
            return self._cache[series_id]

        data = None
        if self._mode == "local":
            path = self._dir / f"{series_id}.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
        elif self._mode == "github":
            url = f"{self._github_url}/{series_id}.json"
            headers = {"User-Agent": "MacroIndicators"}
            if self._github_token:
                headers["Authorization"] = f"token {self._github_token}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError:
                data = None

        if data:
            self._cache[series_id] = data
        return data

    def latest(self, series_id: str) -> dict | None:
        """Get the most recent observation for a series.

        Returns {"date": "YYYY-MM-DD", "value": float} or None.
        """
        data = self.get(series_id)
        if not data or not data.get("observations"):
            return None
        return data["observations"][0]

    def yoy_growth(self, series_id: str, target_date: str | None = None) -> float | None:
        """Compute YoY growth for a series.

        If target_date is given, finds the observation closest to that date
        and compares to 12 months prior. Otherwise uses the most recent observation.

        Returns growth as a decimal (e.g., 0.042 = 4.2%), or None.
        """
        data = self.get(series_id)
        if not data:
            return None
        obs = data.get("observations", [])
        if len(obs) < 2:
            return None

        freq = data.get("frequency", "monthly")

        if target_date:
            # Find closest observation to target_date
            current = min(obs, key=lambda o: abs(_date_diff(o["date"], target_date)))
        else:
            current = obs[0]

        # Find observation ~1 year earlier
        prior_target = _year_ago(current["date"])
        prior = min(obs, key=lambda o: abs(_date_diff(o["date"], prior_target)))

        # Sanity: prior must be roughly 1 year earlier (within 60 days for monthly, 120 for quarterly)
        tolerance = 120 if freq == "quarterly" else 60
        if abs(_date_diff(prior["date"], prior_target)) > tolerance:
            return None
        if prior["value"] == 0:
            return None

        return round((current["value"] - prior["value"]) / prior["value"], 4)

    def trend(self, series_id: str, n: int = 12) -> list[dict]:
        """Get the last N observations for a series.

        Returns list of {"date", "value"}, most recent first.
        """
        data = self.get(series_id)
        if not data:
            return []
        return data.get("observations", [])[:n]

    def series_list(self) -> list[str]:
        """List all available series IDs."""
        if self._mode == "local":
            return sorted(f.stem for f in self._dir.glob("*.json"))
        return []


def _date_diff(d1: str, d2: str) -> int:
    """Difference in days between two YYYY-MM-DD date strings."""
    from datetime import datetime
    dt1 = datetime.strptime(d1, "%Y-%m-%d")
    dt2 = datetime.strptime(d2, "%Y-%m-%d")
    return (dt1 - dt2).days


def _year_ago(d: str) -> str:
    """Return the date string ~1 year before d."""
    from datetime import datetime, timedelta
    dt = datetime.strptime(d, "%Y-%m-%d")
    # Handle leap year: go back 365 days (close enough for matching)
    prior = dt - timedelta(days=365)
    return prior.strftime("%Y-%m-%d")
