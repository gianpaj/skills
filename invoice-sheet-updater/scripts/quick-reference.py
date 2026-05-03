#!/usr/bin/env python3
"""
Quick reference script for invoice processing workflow
Usage: Run this to see the step-by-step process
"""

WORKFLOW = """
╔════════════════════════════════════════════════════════════════╗
║         INVOICE SHEET UPDATER - QUICK REFERENCE                ║
╚════════════════════════════════════════════════════════════════╝

📧 STEP 1: FIND THE EMAIL
────────────────────────────────────────────────────────────────
gog gmail search "Fwd: {Vendor}" --plain

Example:
  gog gmail search "Fwd: Hetzner" --plain
  → Returns: message_id = 19ded6bbc666ae24

💾 STEP 2: GET EMAIL DETAILS
────────────────────────────────────────────────────────────────
gog gmail get "{message_id}" --plain

Extract:
  • Date: Invoice issue date (DD/MM/YYYY)
  • Invoice #: Alphanumeric identifier
  • Amount: Total amount (€XX,XX format)
  • Vendor: Full company name
  • Tax %: VAT percentage from invoice

📊 STEP 3: FIND NEXT ROW IN SHEET
────────────────────────────────────────────────────────────────
gog sheets get "SHEET_ID" "Purchases 2026!B35:B50" --plain

SHEET_ID = 153KRsiuskz2GFU0IRLywpmWoBH-us87Pb5f4OUMAQpk

Look for first blank row after last data entry.
(Data must be contiguous - no gaps)

🏷️  STEP 4: MAP VENDOR TO CATEGORY
────────────────────────────────────────────────────────────────
Use vendor-to-category mapping:

  Cloud services  → Vercel, Fly.io, Hetzner, Google Cloud, X.AI
  IT Hardware     → Amazon purchases, cables, monitors
  Communication   → DIGI SPAIN, mobile providers
  Books           → Amazon books (4% VAT)
  Other           → Document in references/vendors.md

⚠️  STEP 5: VALIDATE DATA
────────────────────────────────────────────────────────────────
✓ Date format: DD/MM/YYYY (e.g., 3/05/2026)
✓ Amount format: €XX,XX (comma decimal, € symbol)
✓ Tax format: XX% (e.g., 21%, 19%, 4%, or blank for 0%)
✓ Vendor: Full legal name (not abbreviation)
✓ Category: From predefined list

📝 STEP 6: UPDATE SHEET (ENTIRE ROW IN ONE COMMAND)
────────────────────────────────────────────────────────────────
Use pipe-separated values for multiple columns:

gog sheets update "SHEET_ID" "Purchases 2026!A{row}:H{row}" "|Date|InvoiceNum|Description|Vendor|Category|Amount|Tax%"

Example:
gog sheets update "SHEET_ID" "Purchases 2026!A35:H35" "|3/05/2026|081000858069|Hetzner Online GmbH - Invoice 081000858069|Hetzner Online GmbH|Cloud services|€17,58|19%"

Note: First pipe (|) represents empty column A (checkbox)

🔍 STEP 7: VERIFY
────────────────────────────────────────────────────────────────
gog sheets get "SHEET_ID" "Purchases 2026!B{row}:H{row}" --plain

Confirm all fields match invoice data.

╔════════════════════════════════════════════════════════════════╗
║                    COLUMN REFERENCE                            ║
╚════════════════════════════════════════════════════════════════╝

A | To send to accountant  | Leave empty (checkbox)
B | Date                    | DD/MM/YYYY format
C | Invoice num             | Vendor invoice #
D | Description             | "{Vendor} - Invoice {#}"
E | Vendor                  | Full legal name
F | Category                | Predefined category
G | Amount EUR without VAT  | €XX,XX format
H | Tax %                   | 0%, 4%, 19%, 21%, or blank
I | VAT amount EUR          | Auto-calculated
J | Amount EUR with VAT     | Auto-calculated
K | Amount USD with VAT     | Auto-calculated

╔════════════════════════════════════════════════════════════════╗
║                  COMMON VENDORS & CATEGORIES                   ║
╚════════════════════════════════════════════════════════════════╝

CLOUD SERVICES (0-19% VAT):
  Vercel, Fly.io, Hetzner, Google Cloud, X.AI, Cloudflare,
  Replicate, fal, Spaceship

IT HARDWARE (21% VAT):
  Amazon EU, cables, monitors, peripherals, equipment

COMMUNICATION (21% VAT):
  DIGI SPAIN, mobile providers

BOOKS (4% VAT):
  Amazon books, educational materials

╔════════════════════════════════════════════════════════════════╗
║                       ERROR RECOVERY                           ║
╚════════════════════════════════════════════════════════════════╝

If data entry fails or is incorrect:

1. Check the row: gog sheets get "SHEET_ID" "Purchases 2026!B{row}:H{row}" --plain
2. Update the problematic cell using pipe format
3. Re-run verify command

Example - fix just the amount in column G:

gog sheets update "SHEET_ID" "Purchases 2026!G40" "€17,58"

╔════════════════════════════════════════════════════════════════╗
║                     USEFUL COMMANDS                            ║
╚════════════════════════════════════════════════════════════════╝

Search for invoice:
  gog gmail search "Fwd: {Vendor Name}" --plain

Get full email:
  gog gmail get "{message_id}" --plain

Download attachment:
  gog gmail attachment "{message_id}" "{attachment_name}" > output.pdf

Read PDF (if needed):
  pdf "{pdf_path}" --prompt "Extract invoice details: date, number, amount"

Check sheet data:
  gog sheets get "SHEET_ID" "Purchases 2026!B40:H50" --plain

Single cell update:
  gog sheets update "SHEET_ID" "Purchases 2026!G40" "€17,58"

For vendor not in list:
  Add to references/vendors.md with category and typical VAT
"""

print(WORKFLOW)
