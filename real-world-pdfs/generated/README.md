# Generated Test PDF Suite

This directory contains synthetically generated PDF files designed to test specific edge cases and scenarios that complement the real-world PDFs.

## Directory Structure

```
generated/
├── simple/              # Clean, well-structured PDFs
│   ├── single_column_typography.pdf    # Typography hierarchy test
│   └── semantic_table.pdf              # Proper table markup
├── complex/             # Multi-column and mixed content
│   ├── proper_multi_column.pdf         # Clean 2-column layout
│   └── mixed_content_layout.pdf        # Text + visual tables
└── edge_cases/          # Challenging scenarios
    ├── overlapping_text.pdf            # Overlapping text elements
    ├── extreme_multi_column.pdf        # 15-column layout
    └── tiny_fonts_spacing.pdf          # Small fonts, tight spacing
```

## Test Categories

### Simple PDFs
These should be parsed correctly by both traditional and spatial-aware parsers:

1. **single_column_typography.pdf**
   - Clean single-column layout
   - Typography hierarchy (title, subtitle, headers, body, captions)
   - Tests font-based structure detection

2. **semantic_table.pdf**
   - Properly structured table using PDF table markup
   - Should be easy for traditional parsers
   - Baseline for table parsing comparison

### Complex PDFs
These require spatial awareness but have clean structure:

1. **proper_multi_column.pdf**
   - Clean 2-column layout with clear boundaries
   - Tests column detection algorithms
   - Reading order preservation

2. **mixed_content_layout.pdf**
   - Mixed text and visual tables
   - Simulates financial/business reports
   - Tests table reconstruction from rectangles

### Edge Cases
These test specific algorithmic challenges:

1. **overlapping_text.pdf**
   - Overlapping text elements (different colors/fonts)
   - Misaligned baselines (common in MS Office)
   - Tests bbox conflict resolution

2. **extreme_multi_column.pdf**
   - 15-column layout (like shipping schedules)
   - Very narrow columns
   - Tests scalability of column detection

3. **tiny_fonts_spacing.pdf**
   - Very small fonts (4pt, 6pt)
   - Tight and wide spacing variations
   - Tests clustering threshold sensitivity

## Usage

These PDFs are designed to be used alongside the real-world PDFs for comprehensive testing:

```bash
# Analyze all PDFs including generated ones
python3 analyze_pdfs.py

# Test spatial algorithms on edge cases
python3 visualize_pdf_issues.py

# Compare extraction methods
python3 compare_extraction_methods.py
```

## Expected Outcomes

### Success Criteria

- **Simple PDFs**: 100% accuracy with both traditional and spatial parsers
- **Complex PDFs**: Spatial parsers should significantly outperform traditional
- **Edge Cases**: Spatial parsers should handle gracefully, traditional may fail

### Algorithm Validation

These PDFs help validate:
1. **Column detection** accuracy across different layouts
2. **Font hierarchy** parsing for structure
3. **Table reconstruction** from visual elements
4. **Text clustering** robustness
5. **Error handling** for edge cases

## Generating New Tests

To create additional test PDFs, run:

```bash
python3 generate_test_pdfs.py
```

The script is designed to be easily extensible for new test scenarios.
