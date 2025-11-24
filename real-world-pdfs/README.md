# Real-World PDF Test Suite

This directory contains real-world PDF files that demonstrate why traditional PDF parsers fail and what spatial-aware approaches must handle.

## Directory Structure

```
real-world-pdfs/
├── README.md                          # This file
├── ANALYSIS_SUMMARY.md                # Comprehensive analysis findings
├── analysis_summary.txt               # Text report of all findings
├── analysis_detailed.json             # Complete structured analysis data
├── complex/                           # PDFs with spatial complexity
│   └── document (1).pdf              # Multi-column layout (1 PDF)
├── problematic/                       # PDFs with MS Office + spatial issues
│   ├── 2857439.pdf                   # FileMaker, processing errors
│   ├── Bunge_loadingstatement_2025-09-25.pdf
│   ├── CBH Shipping Stem 26092025.pdf
│   ├── Loading-Statement-for-Web-Portal-20250923.pdf
│   ├── Shipping-Stem-2025-09-30.pdf
│   ├── shipping-stem-2025-11-13.pdf
│   └── shipping_stem-accc-30092025-1.pdf
├── detailed_analysis/                 # Per-PDF spatial analysis
│   ├── combined_spatial_analysis.txt
│   └── [individual spatial analysis files]
└── extraction_comparison/             # Traditional vs spatial extraction
    └── [comparison reports]
```

## Analysis Scripts

Located in parent directory (`pdf2md/`):

1. **analyze_pdfs.py** - Comprehensive PDF analysis
2. **visualize_pdf_issues.py** - Spatial layout analysis
3. **compare_extraction_methods.py** - Extraction comparison
4. **reorganize_pdfs.py** - Auto-categorization

## Quick Start

### Run Full Analysis

```bash
cd /path/to/pdf2md
python3 analyze_pdfs.py              # Generate analysis reports
python3 visualize_pdf_issues.py      # Create spatial analysis
python3 compare_extraction_methods.py # Compare extraction methods
```

### Read Key Reports

1. **Start here:** `ANALYSIS_SUMMARY.md` - Executive summary and key findings
2. **Technical details:** `analysis_summary.txt` - Complete analysis report
3. **Comparisons:** `extraction_comparison/` - See why traditional parsers fail
4. **Per-PDF details:** `detailed_analysis/` - Deep dive into each file

## Key Findings

### PDF Characteristics

| Metric | Value |
|--------|-------|
| Total PDFs | 8 |
| Problematic (MS Office + spatial) | 7 (88%) |
| Complex (spatial only) | 1 (12%) |
| Simple (traditional parser OK) | 0 (0%) |
| MS Office generated | 6 (75%) |
| Multi-column layout | 8 (100%) |
| Visual table structures | 5 (63%) |
| Processing errors | 2 (25%) |

### Why Traditional Parsers Fail

All 8 PDFs defeat traditional parsers because:

1. **Spatial Ignorance** (100% of PDFs)
   - Text extracted in stream order, not visual order
   - 9-15 column positions per page
   - Reading order completely wrong

2. **MS Office Artifacts** (75% of PDFs)
   - Non-standard text positioning
   - CIDFont encoding issues
   - Text fragmented into tiny blocks
   - 176-243 rectangle drawings per page

3. **Visual Tables** (63% of PDFs)
   - No semantic table markup
   - Tables created with rectangle drawings
   - Cell boundaries not defined
   - Headers mixed with data

## Example: CBH Shipping Stem 26092025.pdf

This is our primary test case - the most challenging PDF:

### Characteristics:
- **Producer:** Microsoft® Excel® for Microsoft 365
- **Text Blocks:** 97
- **Drawings:** 176 rectangles (table borders)
- **Columns:** 9 distinct X-positions

### Traditional Parser Output:
```
As of 26/09/2025
9292
DARYA KRISHNA
10:21
...
```
**Result:** Complete gibberish. Table structure destroyed.

### Spatial-Aware Output:
```
Detected 9 columns
--- Column 1 ---
  VNA #
  9292
  9276
--- Column 2 ---
  Vessel Name
  DARYA KRISHNA
  NIKOLAOS
```
**Result:** Structured, readable, preserves relationships.

## Test Suite Goals

These PDFs define our success criteria:

### Must Pass:
1. **Multi-column detection** - Identify all column positions
2. **Reading order** - Extract text top-to-bottom within columns
3. **Table reconstruction** - Convert rectangles + text to markdown tables
4. **MS Office handling** - Process Excel/Print-to-PDF correctly
5. **Error recovery** - Handle malformed PDFs gracefully

### Success Metrics:
- **Accuracy:** 90%+ column relationship preservation
- **Completeness:** 95%+ text extraction coverage
- **Structure:** 80%+ table cell accuracy
- **Readability:** Human-readable markdown output

## Adding New Test Files

When adding new PDFs:
1. Place in appropriate category (complex/problematic)
2. Run `python3 analyze_pdfs.py` to update reports
3. Run `python3 visualize_pdf_issues.py` for spatial analysis
4. Update this README if needed

## Privacy Note

These PDFs are real-world examples used for testing purposes. Ensure all files contain only public information or properly anonymized data.