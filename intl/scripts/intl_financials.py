"""Helper module for reading international company financial data.

Reads per-company JSON files from intl/financials/{isin}.json.
Works both locally (file path) and via GitHub raw URL.

Usage:
    from intl_financials import IntlFinancials

    intl = IntlFinancials()  # local mode
    intl = IntlFinancials(github_url="https://raw.githubusercontent.com/...")

    data = intl.get("DE0007236101")                # by ISIN
    latest = intl.latest_annual("DE0007236101")
    yoy = intl.yoy_revenue_growth("DE0007236101")
"""

import json
import urllib.request
from pathlib import Path


class IntlFinancials:
    """Read international financial data from local JSON files or GitHub raw URLs."""

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
                self._dir = Path(__file__).parent.parent / "intl" / "financials"
                if not self._dir.exists():
                    self._dir = Path(__file__).parent / "financials"
        self._cache: dict[str, dict] = {}

    def get(self, isin: str) -> dict | None:
        """Load full financial data for a company by ISIN."""
        if isin in self._cache:
            return self._cache[isin]

        data = None
        if self._mode == "local":
            path = self._dir / f"{isin}.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
        elif self._mode == "github":
            url = f"{self._github_url}/{isin}.json"
            headers = {"User-Agent": "IntlFinancials"}
            if self._github_token:
                headers["Authorization"] = f"token {self._github_token}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError:
                data = None

        if data:
            self._cache[isin] = data
        return data

    def latest_annual(self, isin: str) -> dict | None:
        """Get the most recent annual entry."""
        data = self.get(isin)
        if not data or not data.get("annual"):
            return None
        return data["annual"][0]

    def yoy_revenue_growth(self, isin: str) -> float | None:
        """Compute YoY revenue growth from the two most recent annual periods.

        Returns growth as a decimal (e.g., 0.08 = 8% growth), or None.
        """
        data = self.get(isin)
        if not data:
            return None
        annuals = [e for e in data.get("annual", []) if e.get("revenue_M") is not None]
        if len(annuals) < 2:
            return None
        current = annuals[0]["revenue_M"]
        prior = annuals[1]["revenue_M"]
        if prior == 0:
            return None
        return round((current - prior) / prior, 4)

    def rnd_intensity(self, isin: str) -> float | None:
        """R&D as % of revenue for the latest annual period."""
        latest = self.latest_annual(isin)
        if not latest:
            return None
        rev = latest.get("revenue_M")
        rnd = latest.get("rnd_M")
        if not rev or not rnd:
            return None
        return round(rnd / rev, 4)

    def revenue_trend(self, isin: str, periods: int = 5) -> list[dict]:
        """Get annual revenue trend (most recent N periods)."""
        data = self.get(isin)
        if not data:
            return []
        annuals = [e for e in data.get("annual", []) if e.get("revenue_M") is not None]
        return [
            {"period_end": e["period_end"], "revenue_M": e["revenue_M"], "currency": e.get("currency", "EUR")}
            for e in annuals[:periods]
        ]
