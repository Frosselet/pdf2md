#!/usr/bin/env python3
"""
Generate synthetic test PDFs to complement real-world test cases.

This script creates PDFs with specific challenging characteristics that help
test and develop spatial parsing algorithms. These PDFs are designed to
test edge cases and specific scenarios that complement the real-world PDFs.
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import black, red, blue, green, gray
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def create_output_dirs():
    """Create output directories for generated PDFs."""
    base_dir = Path("real-world-pdfs")

    (base_dir / "generated" / "simple").mkdir(parents=True, exist_ok=True)
    (base_dir / "generated" / "complex").mkdir(parents=True, exist_ok=True)
    (base_dir / "generated" / "edge_cases").mkdir(parents=True, exist_ok=True)

    return base_dir


def generate_simple_single_column():
    """Generate a clean single-column document with typography hierarchy."""
    filename = "real-world-pdfs/generated/simple/single_column_typography.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "Document Title")

    # Subtitle
    c.setFont("Helvetica", 16)
    c.drawString(100, height - 140, "A subtitle explaining the content")

    # Section Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 200, "Section 1: Introduction")

    # Body text
    c.setFont("Helvetica", 12)
    y_pos = height - 240
    paragraphs = [
        "This is the first paragraph of body text. It demonstrates normal",
        "typography in a single-column layout. The text should flow naturally",
        "and be easy to parse with traditional methods.",
        "",
        "This is a second paragraph with some emphasis. Notice how the",
        "spacing and font sizes create a clear hierarchy that should be",
        "preserved in the markdown output."
    ]

    for para in paragraphs:
        c.drawString(100, y_pos, para)
        y_pos -= 20

    # Caption example
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(100, y_pos - 20, "Figure 1: This is an italic caption example")

    c.save()
    return filename


def generate_simple_basic_table():
    """Generate a document with a semantic table (proper table markup)."""
    filename = "real-world-pdfs/generated/simple/semantic_table.pdf"

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph("Document with Semantic Table", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Description
    desc = Paragraph("This document contains a properly structured table using PDF table markup, "
                    "which should be easily parsed by traditional methods.", styles['Normal'])
    story.append(desc)
    story.append(Spacer(1, 12))

    # Table data
    data = [
        ['Name', 'Age', 'Department', 'Salary'],
        ['John Smith', '28', 'Engineering', '$75,000'],
        ['Jane Doe', '32', 'Marketing', '$68,000'],
        ['Bob Johnson', '45', 'Sales', '$82,000'],
        ['Alice Brown', '29', 'Engineering', '$77,000']
    ]

    # Create table
    table = Table(data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(table)
    doc.build(story)
    return filename


def generate_complex_multi_column():
    """Generate a document with proper multi-column layout."""
    filename = "real-world-pdfs/generated/complex/proper_multi_column.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Define column boundaries
    col1_left = 50
    col1_right = width/2 - 20
    col2_left = width/2 + 20
    col2_right = width - 50

    # Title spanning both columns
    c.setFont("Helvetica-Bold", 20)
    c.drawString(col1_left, height - 80, "Multi-Column Document Layout")

    # Column 1 content
    c.setFont("Helvetica-Bold", 14)
    c.drawString(col1_left, height - 120, "Left Column")

    c.setFont("Helvetica", 10)
    y_pos = height - 150
    col1_text = [
        "This is the left column of a two-column",
        "layout. The text should flow naturally",
        "within the column boundaries and not",
        "interfere with the right column.",
        "",
        "Spatial parsing algorithms need to",
        "correctly identify column boundaries",
        "and maintain proper reading order:",
        "top-to-bottom within each column,",
        "then left-to-right across columns."
    ]

    for line in col1_text:
        c.drawString(col1_left, y_pos, line)
        y_pos -= 15

    # Column 2 content
    c.setFont("Helvetica-Bold", 14)
    c.drawString(col2_left, height - 120, "Right Column")

    c.setFont("Helvetica", 10)
    y_pos = height - 150
    col2_text = [
        "This is the right column content.",
        "It should be parsed after the left",
        "column content is complete, not",
        "interleaved with it.",
        "",
        "Traditional parsers often fail here",
        "because they extract text in the",
        "order it appears in the PDF stream,",
        "which may not match the visual",
        "reading order."
    ]

    for line in col2_text:
        c.drawString(col2_left, y_pos, line)
        y_pos -= 15

    # Add column divider line
    c.setStrokeColor(gray)
    c.line(width/2, height - 100, width/2, height - 400)

    c.save()
    return filename


def generate_complex_mixed_content():
    """Generate a document with mixed text, tables, and multiple font sizes."""
    filename = "real-world-pdfs/generated/complex/mixed_content_layout.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Main title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 80, "Financial Report Q3 2024")

    # Subtitle
    c.setFont("Helvetica", 14)
    c.drawString(100, height - 110, "Executive Summary and Key Metrics")

    # Section 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 160, "Revenue Overview")

    c.setFont("Helvetica", 12)
    y_pos = height - 190
    revenue_text = [
        "Total revenue for Q3 2024 reached $2.4M, representing a 15% increase",
        "over the previous quarter. Key drivers included expanded market reach",
        "and improved operational efficiency."
    ]

    for line in revenue_text:
        c.drawString(100, y_pos, line)
        y_pos -= 20

    # Create a visual table using rectangles (like MS Office does)
    table_y = y_pos - 40

    # Table headers
    c.setFillColor(colors.lightgrey)
    c.rect(100, table_y, 100, 25, fill=1)
    c.rect(200, table_y, 100, 25, fill=1)
    c.rect(300, table_y, 100, 25, fill=1)

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(120, table_y + 8, "Quarter")
    c.drawString(230, table_y + 8, "Revenue")
    c.drawString(330, table_y + 8, "Growth")

    # Table data
    c.setFillColor(colors.white)
    table_data = [
        ("Q1 2024", "$1.9M", "5%"),
        ("Q2 2024", "$2.1M", "8%"),
        ("Q3 2024", "$2.4M", "15%")
    ]

    y_offset = 25
    for quarter, revenue, growth in table_data:
        c.rect(100, table_y - y_offset, 100, 25, fill=1)
        c.rect(200, table_y - y_offset, 100, 25, fill=1)
        c.rect(300, table_y - y_offset, 100, 25, fill=1)

        c.setFillColor(black)
        c.setFont("Helvetica", 11)
        c.drawString(120, table_y - y_offset + 8, quarter)
        c.drawString(230, table_y - y_offset + 8, revenue)
        c.drawString(330, table_y - y_offset + 8, growth)

        c.setFillColor(colors.white)
        y_offset += 25

    # Add borders
    c.setFillColor(black)
    for i in range(4):  # 4 rows including header
        for j in range(3):  # 3 columns
            x = 100 + j * 100
            y = table_y - i * 25
            c.rect(x, y, 100, 25, fill=0)

    c.save()
    return filename


def generate_edge_case_overlapping_text():
    """Generate a PDF with overlapping text elements (edge case)."""
    filename = "real-world-pdfs/generated/edge_cases/overlapping_text.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 80, "Overlapping Text Elements Test")

    # Normal text
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 120, "This is normal text that should be parsed correctly.")

    # Overlapping text scenario
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 160, "Background text that might be covered")

    # Overlapping text in different color
    c.setFillColor(red)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(120, height - 160, "Overlaid text")

    c.setFillColor(black)
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 200, "This tests how spatial algorithms handle overlapping bboxes.")

    # Text at same Y coordinate but different X (should be same line)
    c.drawString(100, height - 240, "Start of line")
    c.drawString(200, height - 240, "middle part")
    c.drawString(300, height - 240, "end of line")

    # Slightly offset Y coordinates (common in MS Office PDFs)
    c.drawString(100, height - 280, "Slightly")
    c.drawString(150, height - 281, "misaligned")
    c.drawString(220, height - 279, "text elements")

    c.save()
    return filename


def generate_edge_case_extreme_columns():
    """Generate a PDF with many columns (like CBH shipping stem)."""
    filename = "real-world-pdfs/generated/edge_cases/extreme_multi_column.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 60, "15-Column Shipping Schedule (Synthetic)")

    # Define 15 narrow columns
    col_width = (width - 100) / 15
    headers = ["ID", "Vessel", "ETA", "ETD", "Cargo", "Qty", "Port", "Agent",
              "Status", "Berth", "Draft", "LOA", "Beam", "Flag", "Notes"]

    # Draw headers
    c.setFont("Helvetica-Bold", 8)
    for i, header in enumerate(headers):
        x = 50 + i * col_width
        c.drawString(x, height - 90, header[:6])  # Truncate to fit

    # Draw data rows
    c.setFont("Helvetica", 7)
    data_rows = [
        ["001", "ATLANTIC", "12:00", "18:00", "WHEAT", "50000", "MELB", "XYZ", "LOAD", "1", "12.5", "180", "32", "AU", "OK"],
        ["002", "PACIFIC", "14:30", "20:00", "CORN", "45000", "SYDN", "ABC", "WAIT", "2", "11.8", "175", "30", "SG", "DEL"],
        ["003", "NORTHERN", "16:00", "22:30", "RICE", "38000", "BRIS", "DEF", "DONE", "3", "10.2", "165", "28", "JP", "CPL"]
    ]

    y_pos = height - 110
    for row in data_rows:
        for i, cell in enumerate(row):
            x = 50 + i * col_width
            c.drawString(x, y_pos, str(cell)[:8])  # Truncate to fit
        y_pos -= 15

    # Add grid lines
    c.setStrokeColor(gray)
    # Vertical lines
    for i in range(16):  # 15 columns = 16 lines
        x = 50 + i * col_width
        c.line(x, height - 80, x, height - 160)

    # Horizontal lines
    for i in range(5):  # Header + 3 data rows + bottom
        y = height - 80 - i * 20
        c.line(50, y, width - 50, y)

    c.save()
    return filename


def generate_edge_case_tiny_fonts():
    """Generate a PDF with very small fonts and spacing."""
    filename = "real-world-pdfs/generated/edge_cases/tiny_fonts_spacing.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 80, "Tiny Fonts and Spacing Test")

    # Very small font size
    c.setFont("Helvetica", 6)
    c.drawString(100, height - 120, "This text is only 6pt font size - very small")

    # Even smaller
    c.setFont("Helvetica", 4)
    c.drawString(100, height - 135, "This text is 4pt font size - extremely small")

    # Tight spacing
    c.setFont("Helvetica", 8)
    y_pos = height - 160
    tight_lines = [
        "These lines have very tight spacing between them",
        "Only 9 points between baselines instead of normal 12+",
        "This can confuse text clustering algorithms",
        "Because the Y-coordinate gaps are very small"
    ]

    for line in tight_lines:
        c.drawString(100, y_pos, line)
        y_pos -= 9  # Very tight spacing

    # Wide spacing
    c.setFont("Helvetica", 10)
    y_pos -= 30
    wide_lines = [
        "These lines have very wide spacing",
        "",
        "Large gaps between elements",
        "",
        "Can break paragraph detection"
    ]

    for line in wide_lines:
        c.drawString(100, y_pos, line)
        y_pos -= 25  # Wide spacing

    c.save()
    return filename


def create_test_suite_readme():
    """Create documentation for the generated test PDFs."""
    content = """# Generated Test PDF Suite

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
"""

    with open("real-world-pdfs/generated/README.md", "w") as f:
        f.write(content)


def main():
    """Generate all test PDFs and documentation."""
    print("🏗️  Generating synthetic test PDF suite...")

    # Create directories
    base_dir = create_output_dirs()

    generated_files = []

    try:
        # Generate simple PDFs
        print("📄 Creating simple PDFs...")
        generated_files.append(generate_simple_single_column())
        generated_files.append(generate_simple_basic_table())

        # Generate complex PDFs
        print("📊 Creating complex PDFs...")
        generated_files.append(generate_complex_multi_column())
        generated_files.append(generate_complex_mixed_content())

        # Generate edge case PDFs
        print("🎯 Creating edge case PDFs...")
        generated_files.append(generate_edge_case_overlapping_text())
        generated_files.append(generate_edge_case_extreme_columns())
        generated_files.append(generate_edge_case_tiny_fonts())

        # Create documentation
        print("📚 Creating documentation...")
        create_test_suite_readme()

        print(f"\n✅ Successfully generated {len(generated_files)} test PDFs:")
        for file in generated_files:
            print(f"   📁 {file}")

        print(f"\n📋 Documentation created: real-world-pdfs/generated/README.md")
        print("\n🧪 Test suite ready! You can now run analysis scripts to examine all PDFs.")

    except ImportError as e:
        print(f"\n❌ Error: Missing required library for PDF generation")
        print(f"   Please install reportlab: pip install reportlab")
        print(f"   Error details: {e}")
        return False

    except Exception as e:
        print(f"\n❌ Error generating test PDFs: {e}")
        return False

    return True


if __name__ == "__main__":
    main()