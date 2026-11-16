# Create Notion "Strategy Lab" Database

Since the Notion integration token is stored in Hermes' credential store (not accessible), please create the database manually in Notion:

## Steps:
1. Open Notion → Go to "strategys by hermes" page (https://app.notion.com/p/strategys-by-hermes-3e88e778f7be800aa113f930d5d86ad6)
2. Type `/database` → Select "Database - Inline"
3. Name: **🧪 Strategy Lab**
4. Add these properties (exact names matter for MCP population):

| Property Name | Type | Options/Config |
|--------------|------|----------------|
| **Name** | Title | (default) |
| **Status** | Select | Verified (green), Promising (blue), Rejected (red), Incomplete (gray) |
| **Indicators** | Multi-select | (leave empty - will be populated) |
| **Parameters** | Text | (rich text) |
| **Timeframe** | Select | M1, M5, M15, M30, H1, H4, D1 |
| **Pairs** | Multi-select | (leave empty) |
| **Win Rate** | Number | Format: Percent |
| **Profit Factor** | Number | Format: Number |
| **Max DD** | Number | Format: Percent |
| **Trades** | Number | Format: Number |
| **OOS Result** | Text | (rich text) |
| **Source URL** | URL | |
| **Date Found** | Date | |
| **Notes** | Text | (rich text) |

5. Once created, copy the **Database ID** from the URL: `https://app.notion.com/v/<workspace>/<DATABASE_ID>?v=...`
6. Paste it here, then I'll populate all 25 validation results.

---

## Database ID Format
The database ID is a 32-char hex string (with dashes) in the Notion URL.
Example: `3e88e778-f7be-800a-a113-f930d5d86ad6` (this is the parent page ID)

After you create the database, the URL will look like:
`https://app.notion.com/p/Strategy-Lab-<DATABASE_ID>?v=...`

**Provide the DATABASE_ID and I'll populate it automatically.**

---

## Data to Populate (25 validation results)

### VERIFIED (1)
- STRAT-003 | XAUUSD | M15 | 1774 trades | 24.5% WR | 2.37 PF | 19.6% DD | 2.73 OOS PF | 24.5% OOS WR | Verified

### PROMISING (18) - High PF/OOS but DD > 20%
- STRAT-001 | XAUUSD | M15 | 2757 | 58.4% | 3.13 | 149.6% | 3.11 | Promising
- STRAT-001 | XAUUSD | M5 | 11926 | 55.6% | 2.58 | 206.6% | 2.77 | Promising
- STRAT-003 | XAUUSD | H1 | 4078 | 20.8% | 1.71 | 78.2% | 1.82 | Promising
- STRAT-003 | EURUSD | M15 | 1713 | 19.7% | 1.32 | 158.3% | 1.14 | Promising
- STRAT-003 | GBPJPY | M15 | 1843 | 20.3% | 1.35 | 158.0% | 1.34 | Promising
- STRAT-014 | XAUUSD | H1 | 3914 | 33.0% | 1.76 | 31.5% | 1.84 | Promising
- STRAT-014 | USDJPY | H1 | 3857 | 33.2% | 1.49 | 1812.8% | 1.60 | Promising
- STRAT-014 | GBPJPY | H1 | 3993 | 32.8% | 1.41 | 397.7% | 1.33 | Promising
- STRAT-014 | EURUSD | H1 | 4000 | 32.3% | 1.27 | 64.2% | 1.18 | Promising
- STRAT-014 | GBPUSD | H1 | 3992 | 32.2% | 1.31 | 1600.4% | 1.19 | Promising
- STRAT-015 | XAUUSD | H1 | 3023 | 33.0% | 1.46 | 829.5% | 1.44 | Promising
- STRAT-015 | USDJPY | H1 | 2915 | 32.6% | 1.27 | 253.5% | 1.30 | Promising
- STRAT-015 | EURUSD | H1 | 2979 | 32.6% | 1.21 | 43.3% | 1.17 | Promising
- STRAT-015 | GBPJPY | H1 | 2979 | 32.5% | 1.22 | 512.7% | 1.17 | Promising
- STRAT-015 | GBPUSD | H1 | 2986 | 31.5% | 1.17 | 10380% | 1.07 | Promising
- STRAT-009 | XAUUSD | H4 | 171 | 26.3% | 1.50 | 86.4% | 1.72 | Promising
- STRAT-009 | USDJPY | H4 | 166 | 27.7% | 1.21 | 485.3% | 2.23 | Promising
- STRAT-009 | EURUSD | H4 | 166 | 21.7% | 1.22 | 99.3% | 1.12 | Promising

### REJECTED (6)
- STRAT-012 | XAUUSD | M5 | 5019 | 55.3% | 0.98 | 58264% | 1.01 | Rejected
- STRAT-003 | GBPUSD | M15 | 8060 | 14.3% | 0.75 | 6352% | 0.76 | Rejected
- STRAT-003 | USDJPY | M15 | 7728 | 15.5% | 0.87 | 4619% | 0.86 | Rejected
- STRAT-009 | GBPUSD | H4 | 157 | 23.6% | 0.91 | 77215% | 1.60 | Rejected
- STRAT-009 | GBPJPY | H4 | 172 | 20.9% | 0.79 | 633.5% | 0.71 | Rejected
- STRAT-001 | XAUUSD | M5 (dup) | 11926 | 55.6% | 2.58 | 206.6% | 2.77 | Rejected (DD)

