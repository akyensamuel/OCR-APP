# Quick Fix Instructions

## What Was Fixed

1. **Added "Reprocess Document" button** to the document detail page
2. **Updated document detail template** to display table data (cells format) correctly
3. **Fixed upload and reprocess functions** to handle table detection fallback

## How to Fix Your Document

### Method 1: Use the Web Interface (Recommended)

1. Navigate to: http://127.0.0.1:8000/documents/3/
2. Click the **yellow "Reprocess Document"** button (in Quick Actions sidebar)
3. Confirm the reprocess operation
4. The page will reload and show the extracted table data

### Method 2: Use Python Script

Run this command in PowerShell:
```powershell
D:/code/optR/virtual/Scripts/python.exe D:/code/optR/OCR/test_reprocess_doc3.py
```

Then refresh the webpage to see the updated data.

## What You Should See After Reprocessing

**Before** (current state):
- "No extracted data available"
- 0 Fields badge

**After** (fixed):
- A table showing:
  - Row 1: Person | Height (headers in blue)
  - Row 2: Wendy | 5'6"
  - Row 3: Michael | 5'9"
  - Row 4: Rachael | 5'3"
  - Row 5: Allen | 5'11"
- Badge showing "10 cells"
- Confidence percentages for each cell
- Detected headers: Person, Height

## Export Options

After reprocessing, you can:
- **Export to PDF**: Full formatted table with confidence scores
- **Export to Excel**: Structured spreadsheet
- **Export to Word**: Formatted document
- **Export to CSV**: Raw data

## Troubleshooting

If reprocessing fails:
1. Check that the image file exists at: `D:\code\optR\OCR\media\uploads/documents/Screenshot 2025-10-02 142318.png`
2. Look at the Django server console for error messages
3. Try the Python script method to see detailed output

## Technical Details

The system now supports two extraction formats:

1. **Cells Format** (table detection - preferred):
```json
{
  "rows": 5,
  "cols": 2,
  "cells": [
    {"row": 0, "col": 0, "text": "Person", "confidence": 95.0},
    ...
  ]
}
```

2. **Fields Format** (old template processor):
```json
{
  "fields": [
    {"name": "Field1", "value": "Value1", "confidence": 95.0}
  ]
}
```

The document detail page now correctly displays both formats.
