# Quick Reference - Invoice Sheet Updater

## 7-Step Workflow

### 📧 Step 1: Find the Email
```bash
gog gmail search "Fwd: {Vendor}" --plain
```

Example:
```bash
gog gmail search "Fwd: Hetzner" --plain
# Returns: message_id = 19ded6bbc666ae24
```

### 2️⃣ Step 2: Get Email Details
```bash
gog gmail get "{message_id}" --plain
```

Extract these fields:
- **Date:** Invoice issue date (DD/MM/YYYY)
- **Invoice #:** Alphanumeric identifier from invoice
- **Amount:** Total amount shown on invoice
- **Currency:** USD, GBP, EUR, or other
- **Vendor:** Full company/legal name
- **Tax %:** VAT percentage stated on invoice

**If amount is in USD:**
- Check similar vendor entries in the sheet for historical exchange rate
- Example: X.AI invoices typically use ~0.858 EUR/USD
- **When uncertain, ask the user for the correct rate instead of guessing**

### 📊 Step 3: Find Next Row in Sheet
```bash
gog sheets get "153KRsiuskz2GFU0IRLywpmWoBH-us87Pb5f4OUMAQpk" "Purchases 2026!B35:B50" --plain
```

Find first blank row after last data entry. **Data must be contiguous - no gaps.**

### 🏷️ Step 4: Map Vendor to Category

| Category | Examples |
|----------|----------|
| Cloud services | Vercel, Fly.io, Hetzner, Google Cloud, X.AI, Cloudflare, Replicate |
| IT Hardware | Amazon purchases, cables, monitors, peripherals |
| Communication | DIGI SPAIN, mobile providers |
| Books | Amazon books, educational materials (4% VAT) |

See `references/vendors.md` for complete vendor list.

### ⚠️ Step 5: Calculate VAT & Validate Data

**Important:** Invoice shows total WITH VAT. Calculate amounts without VAT first.

If invoice is €3,00 with 21% VAT:
- Amount without VAT: €3,00 ÷ 1.21 = €2,48
- VAT amount: €2,48 × 0.21 = €0,52

**Validation checklist:**
- ✅ Date format: DD/MM/YYYY (e.g., 27/04/2026)
- ✅ Amount: Decimal without €/comma (e.g., 2.48, not €2,48)
- ✅ Tax: Percent sign (e.g., 21%, 19%, 4%, or blank)
- ✅ Vendor: Full legal name, no abbreviations
- ✅ Category: From predefined list

### 📝 Step 6: Update Sheet (All Columns A-J in One Command)

**CRITICAL:** Use decimal numbers for amounts, NOT currency format.

Format: `|Date|InvoiceNum|Description|Vendor|Category|Amount|Tax%|VATAmount|TotalWithVAT`

```bash
gog sheets update "153KRsiuskz2GFU0IRLywpmWoBH-us87Pb5f4OUMAQpk" "Purchases 2026!A{row}:J{row}" "|27/04/2026|DGFC2613042959|DIGI SPAIN TELECOM - Mobile Invoice|DIGI SPAIN TELECOM S.L.U.|Communication services|2.48|21%|0.52|3.00"
```

**First pipe (|) represents empty column A** (checkbox for accountant).

### 🔍 Step 7: Verify
```bash
gog sheets get "153KRsiuskz2GFU0IRLywpmWoBH-us87Pb5f4OUMAQpk" "Purchases 2026!B{row}:J{row}" --plain
```

Confirm all fields match invoice data exactly.

---

## Column Reference

| Col | Name | Format | Example |
|-----|------|--------|---------|
| A | To send to accountant | Empty | (blank) |
| B | Date | DD/MM/YYYY | 27/04/2026 |
| C | Invoice num | Text | DGFC2613042959 |
| D | Description | Text | DIGI SPAIN TELECOM - Mobile Invoice |
| E | Vendor | Full legal name | DIGI SPAIN TELECOM S.L.U. |
| F | Category | Predefined | Communication services |
| G | Amount without VAT | Decimal | 2.48 (displays as €2,48) |
| H | Tax % | Percent | 21% |
| I | VAT amount | Decimal | 0.52 (displays as €0,52) |
| J | Total with VAT | Decimal | 3.00 (displays as €3,00) |
| K | USD amount | Auto | (auto-calculated) |

---

## Useful Commands

### Gmail
```bash
# Search for invoice
gog gmail search "Fwd: {Vendor Name}" --plain

# Get full email with body
gog gmail get "{message_id}" --plain

# Download attachment
gog gmail attachment "{message_id}" "{attachment_name}" > output.pdf
```

### Google Sheets
```bash
# Check current data range
gog sheets get "SHEET_ID" "Purchases 2026!B40:H50" --plain

# Update single cell
gog sheets update "SHEET_ID" "Purchases 2026!G40" "17.58"

# Update multiple cells (pipe-separated)
gog sheets update "SHEET_ID" "Purchases 2026!A40:J40" "|date|num|desc|vendor|cat|amt|tax|vat|total"
```

### PDF Reading (if needed)
```bash
pdf "invoice.pdf" --prompt "Extract invoice details: date, number, amount, vendor"
```

---

## Error Recovery

If data entry fails or shows wrong values:

**1. Check what was written:**
```bash
gog sheets get "SHEET_ID" "Purchases 2026!B{row}:J{row}" --plain
```

**2. Fix individual cells:**
```bash
# Fix amount in column G
gog sheets update "SHEET_ID" "Purchases 2026!G40" "17.58"

# Fix VAT in column I
gog sheets update "SHEET_ID" "Purchases 2026!I40" "3.69"

# Fix total in column J
gog sheets update "SHEET_ID" "Purchases 2026!J40" "21.27"
```

**3. Re-verify after corrections:**
```bash
gog sheets get "SHEET_ID" "Purchases 2026!B{row}:J{row}" --plain
```

---

## Common Issues

### Amount Shows as €2,00 Instead of €2,48
- **Cause:** Entered as "€2,48" instead of decimal "2.48"
- **Solution:** Use decimal format (2.48), sheet's number formatting adds € automatically
- **Why:** The CLI tool misinterprets € and commas

### VAT Amount or Total Column Empty
- **Cause:** These columns are NOT auto-calculated, they need manual entry
- **Solution:** Calculate and enter both values in columns I and J
- **Formula:** VAT = Amount × Tax% ÷ 100, Total = Amount + VAT

### Row Number Off by One
- **Cause:** Using range A:H instead of A:J (missing VAT columns)
- **Solution:** Always use A:J range for full row updates

---

## Quick Example: Complete Invoice Processing

**Scenario:** DIGI invoice €3,00 with 21% VAT on 27/04/2026

```bash
# 1. Search Gmail
gog gmail search "Fwd: DIGI" --plain

# 2. Get details
gog gmail get "19ded81f4c97f99a" --plain
# Extract: invoice DGFC2613042959, amount €3.00, tax 21%

# 3. Check next row
gog sheets get "SHEET_ID" "Purchases 2026!B35:B40" --plain
# Last entry row 35, use row 36

# 4. Calculate (€3.00 ÷ 1.21 = €2.48, 2.48 × 0.21 = 0.52)

# 5. Update entire row
gog sheets update "SHEET_ID" "Purchases 2026!A36:J36" "|27/04/2026|DGFC2613042959|DIGI SPAIN TELECOM - Mobile Invoice April 2026|DIGI SPAIN TELECOM S.L.U.|Communication services|2.48|21%|0.52|3.00"

# 6. Verify
gog sheets get "SHEET_ID" "Purchases 2026!B36:J36" --plain
```

**Expected result:**
```
27/04/2026  DGFC2613042959  DIGI SPAIN TELECOM...  DIGI SPAIN TELECOM S.L.U.  Communication services  2.48  21%  0.52  3.00
```

---

## Sheet Details

- **Sheet ID:** `153KRsiuskz2GFU0IRLywpmWoBH-us87Pb5f4OUMAQpk`
- **Tab:** `Purchases 2026`
- **Currency:** EUR (columns G, I, J display with € and comma formatting)
- **VAT:** Columns I & J are NOT auto-calculated - enter manually
- **Contiguity:** Data must have no gaps between rows

See `SKILL.md` for comprehensive workflow and `references/vendors.md` for vendor mappings.
