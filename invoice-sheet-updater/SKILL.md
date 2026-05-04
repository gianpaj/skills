---
name: invoice-sheet-updater
description: Read forwarded invoice emails from gianpa@gmail.com, extract invoice details (date, number, amount, vendor, category), and automatically add entries to the Google Sheets "Purchases 2026" tab. Use when Gian forwards invoice emails (with subject like "Fwd: [Vendor] Invoice...") and needs them added to the expense tracking sheet with proper categorization and VAT information. Triggers on phrases like "add this invoice to the sheet", "update the purchases sheet with this invoice", "process this forwarded invoice", or when invoice emails are forwarded directly.
---

# Invoice Sheet Updater

Automate invoice processing: find forwarded emails from gianpa@gmail.com, extract invoice details, and update the Google Sheets expense tracker.

## Quick Start

When a forwarded invoice email arrives:

1. **Search Gmail** for the forwarded invoice using `gog gmail search`
2. **Extract details** from the email and/or PDF attachment (date, invoice #, amount, vendor, category)
3. **Map the vendor** to appropriate category (Cloud services, IT Hardware, Communication, etc.)
4. **Calculate VAT & totals** (columns I and J are NOT auto-calculated)
5. **Update the sheet** using pipe-separated values in one command
6. **Verify** the entry appears correctly in the Purchases 2026 tab

## Key Resources

- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) — 7-step workflow, common commands, troubleshooting
- **Vendor Mappings:** [references/vendors.md](references/vendors.md) — 20+ vendors with categories and VAT rates
- **Sheet Schema:** [references/sheet-schema.md](references/sheet-schema.md) — column structure, data formats, validation rules

## Workflow: Processing a Forwarded Invoice

### 1. Locate the Invoice Email

Use Gmail search to find the forwarded invoice:

```bash
gog gmail search "Fwd: {vendor_name}" --plain
```

The email subject will typically be: `Fwd: {Vendor} - Invoice {number}` or `Fwd: {Vendor} Invoice...`

Get the full email details:

```bash
gog gmail get "{message_id}" --plain
```

### 2. Extract Invoice Details

From the email body and/or PDF attachment, extract:

- **Date**: Invoice date (format: DD/MM/YYYY)
- **Invoice Number**: Unique invoice identifier
- **Amount**: Total amount (shown in invoice, use this to calculate backward)
- **Vendor Name**: Full vendor/company name
- **Category**: Maps to one of the predefined categories (see references/vendors.md)
- **Tax %**: VAT rate (21%, 19%, 4%, or blank for 0%)
- **Currency**: Note if invoice is in USD, GBP, or other non-EUR currency

**For PDF attachments:** Download using `gog gmail attachment` and read with `pdf` tool to extract structured data.

**Currency Conversion (if needed):**
- Sheet uses EUR (€) for all amounts
- If invoice is in USD: Get the closing rate for that invoice date from https://www.exchangerates.org.uk/USD-EUR-exchange-rate-history.html
- Example: X.AI invoice dated 03/05/2026 had closing rate 1 USD = 0.85222 EUR
- Calculate: USD amount × closing rate = EUR amount
- Once converted, treat as EUR amount in the sheet (no VAT for US digital services)

**Important notes:**
- The invoice total shown is usually WITH VAT (the final amount)
- Dates must be in DD/MM/YYYY format
- For EU vendors, assume 21% VAT unless invoice specifies otherwise
- Cloud services and international vendors may have 0% or different VAT rates
- US digital services (like X.AI API) have 0% VAT when charged to EU accounts

### 3. Map Vendor to Category

Refer to [references/vendors.md](references/vendors.md) for known vendor-category mappings. Categories include:

- **Cloud services** - Hosting, APIs, SaaS platforms (Vercel, Fly.io, Hetzner, X.AI, Google Cloud, etc.)
- **IT Hardware** - Equipment, peripherals, tools (Amazon purchases, cables, monitors, etc.)
- **Communication services** - Mobile, phone, telecom (DIGI SPAIN, etc.)
- **Books** - Professional development, learning materials (4% VAT)
- **Other** - Miscellaneous purchases

### 4. Calculate VAT and Total Amounts

**The sheet does NOT auto-calculate VAT or totals. You must calculate these manually.**

If invoice shows €3,00 total with 21% VAT:
1. Calculate amount WITHOUT VAT: €3,00 ÷ 1.21 = €2,48 (column G)
2. Calculate VAT amount: €2,48 × 0.21 = €0,52 (column I)
3. Total with VAT: €2,48 + €0,52 = €3,00 (column J)

**Formulas:**
- Column G (without VAT): Total ÷ (1 + Tax%/100)
- Column I (VAT): G × Tax% ÷ 100
- Column J (with VAT): G + I

Example: If invoice is €3,00 with 21% tax:
- G = 3.00 ÷ 1.21 = 2.48
- I = 2.48 × 0.21 = 0.52
- J = 2.48 + 0.52 = 3.00

### 5. Update Google Sheets

The Purchases 2026 sheet has this structure:

```
Col A: To send to accountant (checkbox, leave empty)
Col B: Date (DD/MM/YYYY)
Col C: Invoice num (text)
Col D: Description (text)
Col E: Vendor (text)
Col F: Category (text)
Col G: Amount EUR without VAT (numeric: 2.48 displays as €2,48)
Col H: Tax % (text: 21%, or blank for 0%)
Col I: VAT amount EUR (numeric: 0.52 displays as €0,52)
Col J: Total EUR with VAT (numeric: 3.00 displays as €3,00)
Col K: Amount USD with VAT (auto-calculated)
```

**CRITICAL FINDING:** Columns I and J are NOT auto-calculated by formulas. They must be manually calculated and entered.

Find the next available row in the Purchases 2026 tab, then update the entire row in one command:

```bash
# Find next empty row by checking current data with:
gog sheets get "SHEET_ID" "Purchases 2026!B40:B50" --plain

# Update entire row at once using pipe-separated values:
# Format: Empty|Date|InvoiceNum|Description|Vendor|Category|Amount|Tax%|VATAmount|TotalWithVAT
# CRITICAL: Use decimal numbers (2.48, 0.52, 3.00) NOT formatted text (€2,48)
gog sheets update "SHEET_ID" "Purchases 2026!A{row}:J{row}" "|27/04/2026|DGFC2613042959|DIGI SPAIN TELECOM - Mobile Invoice April 2026|DIGI SPAIN TELECOM S.L.U.|Communication services|2.48|21%|0.52|3.00"
```

### 6. Verify the Entry

Check that all fields were entered correctly:

```bash
gog sheets get "SHEET_ID" "Purchases 2026!B{row}:J{row}" --plain
```

Verify:
- Date is in DD/MM/YYYY format
- Amount shows correct value without VAT (2.48)
- VAT amount shows correct percentage (21%)
- VAT amount is calculated correctly (0.52)
- Total with VAT is correct (3.00)
- Category matches the vendor

## Critical Data Entry Rules

### Column G (Amount without VAT)
**Enter as decimal number (e.g., `2.48` NOT `€2,48`)**

- The sheet applies € currency formatting automatically
- Use period (.) as decimal separator, not comma
- The display will show as currency (€2,48)
- Do NOT include the € symbol when entering via CLI

### Column H (Tax %)
**Enter with percent sign (e.g., `21%`, `0%`, or blank)**

- Valid values: `21%`, `19%`, `4%`, `0%`, or leave blank
- Do NOT use decimal notation (0.21, 19.0, etc.)
- Do NOT use just the number (21, not 21%)

### Column I (VAT Amount)
**Calculate and enter as decimal (e.g., `0.52`)**

- Formula: Amount (G) × Tax% (H) ÷ 100
- Example: 2.48 × 21 ÷ 100 = 0.52
- Enter as plain number without currency symbol
- Round to 2 decimal places

### Column J (Total with VAT)
**Calculate and enter as decimal (e.g., `3.00`)**

- Formula: Amount (G) + VAT Amount (I)
- Example: 2.48 + 0.52 = 3.00
- Enter as plain number without currency symbol
- Round to 2 decimal places

## Why Decimals Instead of €XX,XX Format?

The `gog sheets` CLI tool has quirks with formatted currency:
- Values entered with € and commas may be truncated (€2,48 becomes €2,00)
- The comma character is interpreted as a field separator
- The € symbol is sometimes stripped or mishandled

**Solution:** Enter plain decimal numbers (2.48, 0.52, 3.00). The sheet's built-in number formatting applies the € symbol and comma automatically, so the display shows correctly (€2,48, €0,52, €3,00).

## Common Invoice Types

### Cloud Services (€ varies, 0-19% VAT)

Examples: Vercel, Fly.io, Hetzner, Google Cloud, X.AI, Cloudflare, Replicate

- Category: **Cloud services**
- Date: From invoice date
- Tax: Usually 0% (EU digital services exemption), but check invoice
- Format: "{Vendor} - Invoice {Number}" or "{Vendor} {Service} Invoice"
- Amount entry: Use decimal (e.g., 17.58)

### Hardware & Physical Goods (21% VAT)

Examples: Amazon purchases, cables, monitors, peripherals, 3D printer filament

- Category: **IT Hardware**
- Date: Order/delivery date (from invoice or email)
- Tax: **21%** (standard EU VAT)
- Format: Product name, quantity if relevant
- Amount entry: Use decimal

### Mobile/Telecom (21% VAT)

Examples: DIGI SPAIN, mobile providers

- Category: **Communication services**
- Date: Invoice date
- Tax: **21%**
- Format: "Mobile service - {Provider} - {Month}"
- Amount entry: Use decimal (e.g., 2.48)

### Books & Learning (4% VAT)

Examples: Amazon book purchases

- Category: **Books**
- Date: Purchase/delivery date
- Tax: **4%** (reduced EU VAT for books)
- Format: Book title, author, ISBN if available
- Amount entry: Use decimal

## Data Validation Checklist

Before saving, verify:

- ✅ Date is DD/MM/YYYY format (no spaces, correct separators)
- ✅ Amount is decimal number (2.48, not €2,48)
- ✅ Invoice number is non-empty and matches the email
- ✅ Vendor name is full legal name (not abbreviation)
- ✅ Category is from the predefined list
- ✅ Tax % is 21%, 19%, 4%, 0%, or blank
- ✅ VAT amount is calculated correctly
- ✅ Total with VAT is calculated correctly
- ✅ No leading/trailing spaces in any field

## Example: Complete Invoice Processing

**Scenario:** Email from DIGI forwarded on May 3, 2026 with invoice €3,00 (21% VAT)

```bash
# 1. Find the email
gog gmail search "Fwd: DIGI" --plain
# Returns: message_id = 19ded81f4c97f99a

# 2. Get full email
gog gmail get "19ded81f4c97f99a" --plain
# Extract: date=27/04/2026, invoice=DGFC2613042959, total=€3.00, tax=21%

# 3. Calculate amounts
# Amount without VAT: 3.00 / 1.21 = 2.48
# VAT amount: 2.48 * 0.21 = 0.52
# Total with VAT: 2.48 + 0.52 = 3.00

# 4. Check next available row in sheet
gog sheets get "SHEET_ID" "Purchases 2026!B35:B40" --plain
# Last entry at row 35, so use row 36

# 5. Update the sheet - entire row in one command
gog sheets update "SHEET_ID" "Purchases 2026!A36:J36" "|27/04/2026|DGFC2613042959|DIGI SPAIN TELECOM - Mobile Invoice April 2026|DIGI SPAIN TELECOM S.L.U.|Communication services|2.48|21%|0.52|3.00"

# 6. Verify
gog sheets get "SHEET_ID" "Purchases 2026!B36:J36" --plain
```

## Error Handling

If data entry fails or shows wrong values:

1. **Check the row number** - Make sure you're updating the correct row
2. **Verify the data format** - Ensure amounts are decimals (2.48 not €2,48), tax is percent (21%)
3. **Re-verify the sheet** - Fetch the range again to see what was actually written
4. **Correct individual cells** - If one field is wrong, update just that cell
5. **Recalculate totals** - If amount changes, recalculate VAT and total

Example of fixing a single cell:

```bash
# Check what's in the row:
gog sheets get "SHEET_ID" "Purchases 2026!B42:J42" --plain

# If amount is wrong, update just that cell:
gog sheets update "SHEET_ID" "Purchases 2026!G42" "2.48"

# Verify again:
gog sheets get "SHEET_ID" "Purchases 2026!B42:J42" --plain
```

## Sheet Details

**Google Sheet ID:** `153KRsiuskz2GFU0IRLywpmWoBH-us87Pb5f4OUMAQpk`

**Tab Name:** `Purchases 2026`

**Key Notes:**
- Column J (total with VAT) is NOT auto-calculated - must enter manually
- Column K (USD equivalent) appears to auto-calculate from column J
- Date format must be strict: DD/MM/YYYY (e.g., 27/04/2026, not 04/27/2026)
- Amount format strict: decimal with period (e.g., 2.48, not 2,48)
- Data is contiguous - don't skip rows
- Summary rows (totals) appear after the last data entry

---

**Last Updated:** May 3, 2026  
**Learned:** Columns I and J require manual VAT/total calculation; use decimals not formatted currency
