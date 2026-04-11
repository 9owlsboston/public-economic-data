"""Helper module for reading SEC financial data.

Reads per-company JSON files from sec/financials/{cik}.json.
Works both locally (file path) and via GitHub raw URL.

Usage:
    from sec_financials import SECFinancials

    sec = SECFinancials()  # local mode
    sec = SECFinancials(github_url="https://raw.githubusercontent.com/...")

    data = sec.get("0000796343")                  # by CIK
    latest = sec.latest_annual("0000796343")
    yoy = sec.yoy_revenue_growth("0000796343")
"""

import json
import urllib.request
from pathlib import Path


class SECFinancials:
    """Read SEC financial data from local JSON files or GitHub raw URLs."""

    def __init__(
        self,
        local_dir: str | Path | None = None,
        github_url: str | None = None,
        github_token: str | None = None,
    ):
        """Initialize data source.

        Args:
            local_dir: Path to sec/financials/ directory (default: auto-detect).
            github_url: Base raw URL (e.g., https://raw.githubusercontent.com/org/repo/main/sec/financials).
            github_token: PAT for private repo access.
        """
        if github_url:
            self._mode = "github"
            self._github_url = github_url.rstrip("/")
            self._github_token = github_token
        else:
            self._mode = "local"
            if local_dir:
                self._dir = Path(local_dir)
            else:
                # Auto-detect: look relative to this file
                self._dir = Path(__file__).parent.parent / "sec" / "financials"
                if not self._dir.exists():
                    self._dir = Path(__file__).parent / "financials"
        self._cache: dict[str, dict] = {}

    def get(self, cik: str) -> dict | None:
        """Load full financial data for a company by CIK.

        Returns the parsed JSON or None if not found.
        """
        if cik in self._cache:
            return self._cache[cik]

        data = None
        if self._mode == "local":
            path = self._dir / f"{cik}.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
        elif self._mode == "github":
            url = f"{self._github_url}/{cik}.json"
            headers = {"User-Agent": "SECFinancials"}
            if self._github_token:
                headers["Authorization"] = f"token {self._github_token}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError:
                data = None

        if data:
            self._cache[cik] = data
        return data

    def latest_annual(self, cik: str) -> dict | None:
        """Get the most recent annual filing data.

        For companies with amended filings, returns the entry with the
        latest filing_date for the most recent period_end.
        """
        data = self.get(cik)
        if not data or not data.get("annual"):
            return None
        # annual is sorted by period_end desc; first entry is most recent
        # If multiple entries share the same period_end (original + amended),
        # pick the one with the latest filing_date
        latest_period = data["annual"][0]["period_end"]
        candidates = [e for e in data["annual"] if e["period_end"] == latest_period]
        return max(candidates, key=lambda e: e.get("filing_date", ""))

    def latest_quarter(self, cik: str) -> dict | None:
        """Get the most recent quarterly filing data."""
        data = self.get(cik)
        if not data or not data.get("quarterly"):
            return None
        latest_period = data["quarterly"][0]["period_end"]
        candidates = [e for e in data["quarterly"] if e["period_end"] == latest_period]
        return max(candidates, key=lambda e: e.get("filing_date", ""))

    def yoy_revenue_growth(self, cik: str) -> float | None:
        """Compute YoY revenue growth from the two most recent annual periods.

        Returns growth as a decimal (e.g., 0.08 = 8% growth), or None.
        """
        data = self.get(cik)
        if not data:
            return None
        annuals = [e for e in data.get("annual", []) if e.get("revenue_M") is not None]
        # Deduplicate: keep latest filing per period_end
        by_period: dict[str, dict] = {}
        for e in annuals:
            p = e["period_end"]
            if p not in by_period or e.get("filing_date", "") > by_period[p].get("filing_date", ""):
                by_period[p] = e
        periods = sorted(by_period.values(), key=lambda x: x["period_end"], reverse=True)
        if len(periods) < 2:
            return None
        current = periods[0]["revenue_M"]
        prior = periods[1]["revenue_M"]
        if prior == 0:
            return None
        return round((current - prior) / prior, 4)

    def rnd_intensity(self, cik: str) -> float | None:
        """R&D as % of revenue for the latest annual period.

        Returns as decimal (e.g., 0.195 = 19.5%), or None.
        """
        latest = self.latest_annual(cik)
        if not latest:
            return None
        rev = latest.get("revenue_M")
        rnd = latest.get("rnd_M")
        if not rev or not rnd:
            return None
        return round(rnd / rev, 4)

    def revenue_trend(self, cik: str, periods: int = 5) -> list[dict]:
        """Get annual revenue trend (most recent N periods).

        Returns list of {"period_end", "revenue_M", "currency"}.
        """
        data = self.get(cik)
        if not data:
            return []
        # Deduplicate by period_end
        by_period: dict[str, dict] = {}
        for e in data.get("annual", []):
            if e.get("revenue_M") is None:
                continue
            p = e["period_end"]
            if p not in by_period or e.get("filing_date", "") > by_period[p].get("filing_date", ""):
                by_period[p] = e
        sorted_periods = sorted(by_period.values(), key=lambda x: x["period_end"], reverse=True)
        return [
            {"period_end": e["period_end"], "revenue_M": e["revenue_M"], "currency": e.get("currency", "USD")}
            for e in sorted_periods[:periods]
        ]

    # ── V2 derived metrics ───────────────────────────────────────────────

    def free_cash_flow(self, cik: str) -> int | None:
        """Operating cash flow minus capex for latest annual period (in millions).

        Returns None if either field is missing.
        """
        latest = self.latest_annual(cik)
        if not latest:
            return None
        ocf = latest.get("operating_cash_flow_M")
        capex = latest.get("capex_M")
        if ocf is None or capex is None:
            return None
        return ocf - capex

    def net_cash(self, cik: str) -> int | None:
        """Cash minus total debt for latest annual period (in millions).

        Returns None if either field is missing.
        """
        latest = self.latest_annual(cik)
        if not latest:
            return None
        cash = latest.get("cash_M")
        debt = latest.get("total_debt_M")
        if cash is None or debt is None:
            return None
        return cash - debt

    def capex_intensity(self, cik: str) -> float | None:
        """Capex as % of revenue for latest annual period.

        Returns as decimal (e.g., 0.11 = 11%), or None.
        """
        latest = self.latest_annual(cik)
        if not latest:
            return None
        capex = latest.get("capex_M")
        rev = latest.get("revenue_M")
        if not capex or not rev:
            return None
        return round(capex / rev, 4)

    def operating_cash_flow_margin(self, cik: str) -> float | None:
        """Operating cash flow as % of revenue for latest annual period.

        Returns as decimal (e.g., 0.49 = 49%), or None.
        """
        latest = self.latest_annual(cik)
        if not latest:
            return None
        ocf = latest.get("operating_cash_flow_M")
        rev = latest.get("revenue_M")
        if not ocf or not rev:
            return None
        return round(ocf / rev, 4)

    # ── Segment methods ──────────────────────────────────────────────────

    def get_segments(self, cik: str) -> dict | None:
        """Load segment data for a company by CIK.

        Returns the parsed JSON from {cik}_segments.json, or None if not found.
        """
        cache_key = f"{cik}_segments"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = None
        if self._mode == "local":
            path = self._dir / f"{cik}_segments.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
        elif self._mode == "github":
            url = f"{self._github_url}/{cik}_segments.json"
            headers = {"User-Agent": "SECFinancials"}
            if self._github_token:
                headers["Authorization"] = f"token {self._github_token}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError:
                data = None

        if data:
            self._cache[cache_key] = data
        return data

    def segment_names(self, cik: str) -> list[str]:
        """List available segment names for a company."""
        data = self.get_segments(cik)
        if not data or "segments" not in data:
            return []
        return list(data["segments"].keys())

    def latest_segment_annual(self, cik: str, segment: str) -> dict | None:
        """Get the most recent annual entry for a specific segment.

        Annual entries are identified as those with ~365 day duration.
        """
        data = self.get_segments(cik)
        if not data or segment not in data.get("segments", {}):
            return None

        entries = data["segments"][segment]
        # Filter to annual-like entries (duration > 300 days)
        annual = []
        for e in entries:
            start = e.get("start", "")
            end = e.get("end", "")
            if start and end:
                from datetime import datetime
                try:
                    days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
                    if days > 300:
                        annual.append(e)
                except ValueError:
                    continue

        if not annual:
            return None
        # Return most recent by period_end
        return max(annual, key=lambda e: e.get("period_end", ""))
