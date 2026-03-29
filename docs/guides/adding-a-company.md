# Adding a New Company

## Prerequisites

- The company must be a **SEC filer** (has a CIK number)
- You need the company's **CIK** from SEC EDGAR

## Step 1: Find the CIK

Search on SEC EDGAR: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany

Or use the ticker lookup:
```bash
python3 -c "
import json, urllib.request
url = 'https://www.sec.gov/files/company_tickers.json'
req = urllib.request.Request(url, headers={'User-Agent': 'PublicEconomicData'})
data = json.loads(urllib.request.urlopen(req).read())
for v in data.values():
    if v['ticker'] == 'ADBE':  # replace with target ticker
        print(f\"{v['ticker']}: CIK {str(v['cik_str']).zfill(10)} — {v['title']}\")
"
```

## Step 2: Add to Registry

Edit `sec/registry.yaml`:

```yaml
  "0001234567":  # CIK
    name: "Company Name"
    ticker: "TICK"
    exchange: "NYSE"
```

Optional fields:
- `ai_keywords: ["keyword1", "keyword2"]` — for AI signal section in reports
- `tag_overrides: { revenue_tag: "us-gaap:Revenues" }` — force a specific XBRL tag

## Step 3: Run Refresh

```bash
python sec/scripts/refresh.py --cik 0001234567
```

This fetches all historical filings from SEC EDGAR and writes `sec/financials/0001234567.json`.

## Step 4: Verify

```bash
python3 -c "
import json
with open('sec/financials/0001234567.json') as f:
    d = json.load(f)
print(f'Annual: {len(d[\"annual\"])} periods')
print(f'Quarterly: {len(d[\"quarterly\"])} periods')
if d['annual']:
    latest = d['annual'][0]
    print(f'Latest FY: {latest[\"period_end\"]} Rev \${latest[\"revenue_M\"]}M ({latest[\"currency\"]})')
"
```

## Step 5: Commit

```bash
git add sec/registry.yaml sec/financials/0001234567.json
git commit -m "feat: add Company Name (CIK 0001234567)"
git push
```

## Troubleshooting

**No data extracted:**
- Check if the company files 10-K/10-Q (domestic) or 20-F (foreign). The script supports both.
- Some foreign filers (e.g., TD Bank, Manulife) have XBRL period-end mismatches — their XBRL facts don't match the `reportDate` in submissions.
- Try adding `tag_overrides` if the standard tag list doesn't match the company's XBRL taxonomy.

**Stale or wrong data:**
- Revenue looks cumulative (YTD instead of single quarter)? The duration disambiguation should handle this, but check if the company has unusual fiscal period structures.
- Run with `--dry-run` first to preview without writing.

**Non-US company not found in ticker lookup:**
- Check if they file 20-F with SEC (many ADR issuers do)
- The ticker might differ from their home exchange (e.g., SAP on NYSE vs SAP.DE on Frankfurt)
