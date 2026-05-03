# Purchases 2026 Sheet Schema

Reference for the exact column structure and data entry format.

## Sheet Metadata

- **Google Sheet ID:** `153KRsiuskz2GFU0IRLywpmWoBH-us87Pb5f4OUMAQpk`
- **Tab Name:** `Purchases 2026`
- **Data Range:** Starts at row 2 (row 1 has headers)
- **Last Data Row:** Varies (check before inserting new entries)
- **Summary Section:** Begins 2-3 rows after last data entry (contains totals, tax calculations)

## Column Structure

| Col | Column Name | Data Type | Required? | Format | Notes |
|-----|-------------|-----------|-----------|--------|-------|
| A | To send to accountant | Checkbox | No | Leave empty | For manual review tracking |
| B | Date | Text | Yes | DD/MM/YYYY | Must match invoice date exactly |
| C | Invoice num | Text | Yes | Alphanumeric | Unique invoice identifier |
| D | Description / Invoice file name | Text | Yes | Text | Format: "{Vendor} - Invoice {#}" |
| E | Vendor | Text | Yes | Text | Full legal company name |
| F | Category | Text | Yes | Predefined | See vendor-category mappings |
| G | Amount EUR without VAT | Text | Yes | €XX,XX | Comma as decimal separator, € symbol |
| H | Tax % | Text | No | % value | 0%, 4%, 19%, 21%, or blank |
| I | VAT amount EUR | Auto-calculated | - | €XX,XX | Formula: G × H |
| J | Amount EUR with VAT | Auto-calculated | - | €XX,XX | Formula: G + I |
| K | Amount USD with VAT | Auto-calculated | - | $XX.xx | Calculated from J with exchange rate |

## Data Entry Rules

### Date (Column B)

- **Format:** DD/MM/YYYY (day/month/year, zero-padded)
- **Examples:** 3/05/2026 (May 3), 15/04/2026 (April 15), 01/01/2026 (January 1)
- **Source:** Invoice issue date (not email date)
- **Validation:** Must be in range 01/01/2026 - 31/12/2026

### Invoice Number (Column C)

- **Format:** Vendor's invoice reference (alphanumeric, may include letters, numbers, dashes)
- **Examples:** `081000858069`, `B2081410-0007`, `IN-59067839`, `5485443147`
- **Source:** From invoice document
- **Validation:** Non-empty, unique per vendor (but different vendors may reuse numbers)

### Description (Column D)

- **Format:** "{Vendor Name} - Invoice {Number}" or "{Vendor Name} - {Service} Invoice {Number}"
- **Examples:**
  - Hetzner Online GmbH - Invoice 081000858069
  - Google Cloud – Fee for Jan 2026
  - Cloud services (for simple entries)
  - Vercel - Next.js hosting - Invoice B2081410-0007
- **Length:** Keep under 100 characters if possible
- **Purpose:** Human-readable summary for accountant review

### Vendor (Column E)

- **Format:** Full legal company name
- **Examples:**
  - Hetzner Online GmbH (not "Hetzner")
  - Google Cloud EMEA Limited (not "Google Cloud")
  - Amazon EU S.à r.l. (not "Amazon")
  - X.AI LLC (not "X.AI")
- **Source:** Invoice "Bill From" or "Vendor" section
- **Validation:** Must match known vendor list or be a new vendor

### Category (Column F)

- **Allowed values:**
  - Cloud services
  - IT Hardware
  - Communication services
  - Books
  - (Other categories as defined in vendor reference)
- **Source:** From vendor-category mapping
- **Rules:** Must be exact match (case-sensitive in sheet)

### Amount EUR without VAT (Column G)

- **Format:** €XX,XX (Euro symbol, number, comma as decimal, 2 decimal places)
- **Examples:** €17,58, €3.071,38, €12,99, €104,13
- **Important:** Use comma (,) as decimal separator, not period (.)
- **Source:** Invoice subtotal (before tax)
- **Validation:** Must be > 0, max 5 digits before decimal

### Tax % (Column H)

- **Allowed values:** 0%, 4%, 19%, 21%, or blank (empty for 0% VAT)
- **Format:** Number with % symbol or just the number
- **Examples:** 21%, 19%, 4%, 0%, (blank)
- **Rules:**
  - Use blank or "0%" for zero VAT (digital services)
  - Use "4%" for books
  - Use "19%" or "21%" for physical goods and services
  - Do NOT use decimal notation (0.19, 19.0, etc.)
- **Source:** Invoice VAT section

## Auto-Calculated Columns

These columns are populated with formulas and should NOT be manually edited:

### Column I: VAT amount EUR

- **Formula:** G × (H ÷ 100)
- **Example:** If G = €17,58 and H = 19%, then I = €3,34
- **Auto-updated:** When G or H changes

### Column J: Amount EUR with VAT

- **Formula:** G + I
- **Example:** If G = €17,58 and I = €3,34, then J = €20,92
- **Auto-updated:** When G or I changes

### Column K: Amount USD with VAT

- **Formula:** J × (exchange rate from cell reference)
- **Example:** €17,58 × 1.16 ≈ $20.39
- **Exchange Rate:** Updated from external source (check top of sheet)
- **Auto-updated:** When J or exchange rate changes

## Finding the Next Available Row

Before inserting a new entry:

```bash
# Check rows 35-50 to find where data ends:
gog sheets get "SHEET_ID" "Purchases 2026!B35:B50" --plain

# Look for the first blank row after the last data entry
# (Data should be contiguous - no gaps)
```

Data structure example:
```
Row 2:  First entry (Jan 1, 2026)
...
Row 34: Last data entry
Row 35: Summary header or blank
Row 36: Total without VAT
Row 37: Total VAT amount
```

Insert new entries in the next available row before the summary section.

## Common Data Entry Mistakes

| Mistake | Example | Fix |
|---------|---------|-----|
| Wrong decimal separator | €17.58 | Use comma: €17,58 |
| Tax as decimal | 0.19 or 19.0 | Use: 19% |
| Wrong date format | 05/03/2026 or 2026-05-03 | Use: 03/05/2026 (DD/MM/YYYY) |
| Abbreviated vendor | "Amazon" | Use: "Amazon EU S.à r.l." |
| Mismatched category | "Hosting" | Use: "Cloud services" |
| Extra spaces | " €17,58 " | Remove spaces: €17,58 |
| Missing symbol | 17,58 | Include: €17,58 |

## Summary Section

After the last data entry, the sheet contains summary calculations:

```
Row N:   (blank)
Row N+1: "Total without VAT" | <SUM of column G>
Row N+2: "Total VAT amount" | <SUM of column I>
Row N+3: <more calculations>
```

**Do not insert new entries in the summary section.** Always add new entries before the summary starts.

---

**Last Updated:** May 3, 2026  
**Used by:** invoice-sheet-updater skill
