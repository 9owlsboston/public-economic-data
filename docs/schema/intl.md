# International Financials — Data Dictionary

## Source

[Yahoo Finance](https://finance.yahoo.com/) via `yfinance` Python library.
No API key required. Data covers annual income statement items.

## File Layout

- **Registry:** `intl/registry.yaml` — company metadata, keyed by ISIN
- **Financial data:** `intl/financials/{isin}.json` — one file per company
- **Refresh script:** `intl/scripts/refresh_intl.py`
- **Helper module:** `intl/scripts/intl_financials.py` (also `helpers/intl_financials.py`)

## JSON Schema

### File-level fields

| Field | Type | Description |
|---|---|---|
| `isin` | `string` | International Securities Identification Number (e.g., `DE0007236101`) |
| `name` | `string` | Company name |
| `ticker` | `string` | Stock ticker symbol |
| `exchange` | `string` | Stock exchange (e.g., `XETRA`, `LSE`, `Euronext Paris`) |
| `source` | `string` | Always `"yahoo_finance"` |
| `last_refreshed` | `string` | ISO date (`YYYY-MM-DD`) of last data refresh |
| `annual` | `array` | Annual entries, sorted descending by `period_end` |
| `quarterly` | `array` | Quarterly entries (when available), sorted descending by `period_end` |

### Entry-level fields (each item in `annual[]` or `quarterly[]`)

| Field | Type | Unit | Description |
|---|---|---|---|
| `period_end` | `string` | — | Fiscal period end date (`YYYY-MM-DD`) |
| `currency` | `string` | — | ISO 4217 currency code for all monetary values in this entry. Varies by company — check per entry, do **not** assume USD. |
| `revenue_M` | `int \| null` | Millions | Total revenue (Yahoo Finance: `Total Revenue`). Converted from full units to millions. |
| `rnd_M` | `int \| null` | Millions | Research & development expense (Yahoo Finance: `Research And Development`). Often `null` for non-tech companies — many European companies do not report R&D as a separate line item via Yahoo Finance. |
| `cost_of_revenue_M` | `int \| null` | Millions | Cost of revenue (Yahoo Finance: `Cost Of Revenue`). |
| `net_income_M` | `int \| null` | Millions | Net income (Yahoo Finance: `Net Income`). Negative values = net loss. |
| `tags_used` | `object \| absent` | — | Source metadata. **Included on the first entry only.** Contains `source: "yahoo_finance"` and a `notes` field. |

### Null semantics

A value of `null` means Yahoo Finance did not return the line item for that period. Common cases:
- `rnd_M` is `null` for most non-technology companies (banks, industrials, utilities)
- Some companies have incomplete historical data

`null` ≠ zero. Display as "Not disclosed" in reports.

### Currency handling

Unlike SEC data (nearly always USD), international financials use **local currency**:

| Currency | Typical companies |
|---|---|
| `EUR` | German (BMW, Siemens, VW), French (L'Oréal, AXA), Dutch (Heineken), Spanish, Portuguese, Greek |
| `GBP` | UK (Rio Tinto, LSEG, Barclays, Vodafone) |
| `AUD` | Australian (CBA, Telstra) |
| `BRL` | Brazilian (Itaú, Bradesco, Vale, Banco do Brasil) |
| `INR` | Indian (Reliance, Infosys, TCS, Wipro) |
| `HKD` | Hong Kong (Lenovo, China Mobile) |
| `KRW` | South Korean (Samsung, SK Hynix, Hyundai) |
| `SEK` | Swedish (Ericsson) |
| `AED` | UAE (FAB) |
| `DKK` | Danish (Novo Nordisk) |
| `CAD` | Canadian (Thomson Reuters) |

**Do not mix currencies** when comparing companies. Use FRED FX rates from the macro module for normalization when needed. Suppress Azure % ratios when currency ≠ USD.

### Fields not collected

The following income statement items are **not** extracted from Yahoo Finance:
- Capital expenditures (`capex_M`)
- Operating cash flow (`operating_cash_flow_M`)
- SG&A expense (`sga_M`)
- Balance sheet items (`cash_M`, `total_debt_M`, `total_assets_M`)
- Operating income (`operating_income_M`)

## Registry Schema (`intl/registry.yaml`)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Company name |
| `ticker` | `string` | Yes | Stock ticker symbol |
| `exchange` | `string` | Yes | Stock exchange |
| `yf_symbol` | `string` | Yes | Yahoo Finance symbol (e.g., `SIE.DE`, `RIO.L`) — used by refresh script |
| `currency` | `string` | Yes | Default currency for this company |

## Coverage

39 companies across 15 countries. Geographic breakdown:

| Country | Count | Key companies |
|---|---|---|
| Germany | 11 | Siemens, SAP, BMW, VW, Mercedes, Deutsche Telekom, Allianz, BASF, Bayer |
| France | 4 | L'Oréal, AXA, Capgemini, Société Générale |
| UK | 5 | Rio Tinto, LSEG, Barclays, Vodafone |
| Spain | 5 | Amadeus, BBVA, Iberdrola, Inditex, Telefónica |
| India | 4 | Reliance, Infosys, TCS, Wipro |
| Brazil | 4 | Itaú, Bradesco, Vale, Banco do Brasil |
| Australia | 2 | CBA, Telstra |
| Others | 4 | Novo Nordisk (DK), Heineken (NL), Ericsson (SE), FAB (AE) |
