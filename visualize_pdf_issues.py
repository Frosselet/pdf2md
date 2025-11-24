#!/usr/bin/env python3
"""
Create detailed visualizations and text extraction comparisons
to demonstrate why traditional parsers fail on these PDFs
"""

import fitz  # PyMuPDF
import os
from pathlib import Path


def analyze_spatial_layout(pdf_path, output_dir):
    """Analyze and document the spatial layout issues in a PDF."""
    filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(filename)[0]

    report = []
    report.append(f"=" * 80)
    report.append(f"DETAILED SPATIAL ANALYSIS: {filename}")
    report.append(f"=" * 80)
    report.append("")

    try:
        doc = fitz.open(pdf_path)

        for page_num, page in enumerate(doc):
            report.append(f"PAGE {page_num + 1}")
            report.append("-" * 80)
            report.append(f"Dimensions: {page.rect.width:.2f} x {page.rect.height:.2f} points")
            report.append("")

            # Get text with position information
            text_dict = page.get_text("dict")
            blocks = text_dict["blocks"]

            # Analyze text block positioning
            text_blocks = [b for b in blocks if b.get('type') == 0]

            if text_blocks:
                report.append(f"Text Blocks: {len(text_blocks)}")
                report.append("")

                # Extract x-coordinates to detect columns
                x_positions = []
                for block in text_blocks:
                    bbox = block['bbox']
                    x_positions.append({
                        'x0': bbox[0],
                        'x1': bbox[2],
                        'y0': bbox[1],
                        'y1': bbox[3],
                        'width': bbox[2] - bbox[0],
                        'height': bbox[3] - bbox[1]
                    })

                # Sort by Y position first, then X (reading order)
                x_positions_sorted = sorted(x_positions, key=lambda p: (p['y0'], p['x0']))

                # Detect columns
                x_starts = sorted(set([int(p['x0'] / 10) * 10 for p in x_positions]))
                if len(x_starts) > 2:
                    report.append(f"COLUMN DETECTION: Found {len(x_starts)} distinct X-positions")
                    report.append(f"  X-positions: {x_starts}")
                    report.append("  This indicates multi-column layout!")
                    report.append("")

                # Show first few blocks with coordinates
                report.append("First 5 text blocks (with coordinates):")
                for i, block in enumerate(text_blocks[:5]):
                    bbox = block['bbox']
                    text = ""
                    for line in block.get('lines', []):
                        for span in line.get('spans', []):
                            text += span.get('text', '')
                    text = text.strip().replace('\n', ' ')[:60]
                    report.append(f"  Block {i+1}: [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]")
                    report.append(f"    Text: \"{text}...\"")
                report.append("")

            # Analyze drawings (lines, shapes, table borders)
            drawings = page.get_drawings()
            if drawings:
                report.append(f"Drawings/Shapes: {len(drawings)} items")

                # Count line types
                h_lines = []
                v_lines = []
                rectangles = []

                for drawing in drawings:
                    for item in drawing.get('items', []):
                        if item[0] == 'l':  # line
                            x1, y1, x2, y2 = item[1], item[2], item[3], item[4]
                            if abs(y1 - y2) < 1:  # horizontal
                                h_lines.append((x1, y1, x2, y2))
                            elif abs(x1 - x2) < 1:  # vertical
                                v_lines.append((x1, y1, x2, y2))
                        elif item[0] == 're':  # rectangle
                            rectangles.append(item[1])

                report.append(f"  Horizontal lines: {len(h_lines)}")
                report.append(f"  Vertical lines: {len(v_lines)}")
                report.append(f"  Rectangles: {len(rectangles)}")

                if len(h_lines) > 3 and len(v_lines) > 3:
                    report.append("  ** TABLE STRUCTURE DETECTED **")
                    report.append("  Traditional parsers cannot detect these visual table borders!")

                report.append("")

            # Show raw text extraction (what traditional parsers get)
            report.append("RAW TEXT EXTRACTION (Traditional Parser Output):")
            report.append("-" * 80)
            raw_text = page.get_text()
            lines = raw_text.split('\n')[:20]  # First 20 lines
            for i, line in enumerate(lines):
                report.append(f"{i+1:3d}: {line}")
            if len(raw_text.split('\n')) > 20:
                report.append(f"... ({len(raw_text.split('\n')) - 20} more lines)")
            report.append("")

            # Show structured text with coordinates
            report.append("SPATIAL TEXT EXTRACTION (with coordinates):")
            report.append("-" * 80)
            blocks_sorted = sorted(text_blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]))
            for i, block in enumerate(blocks_sorted[:10]):  # First 10 blocks
                bbox = block['bbox']
                text = ""
                for line in block.get('lines', []):
                    for span in line.get('spans', []):
                        text += span.get('text', '')
                text = text.strip().replace('\n', ' ')[:80]
                report.append(f"Block at ({bbox[0]:.0f}, {bbox[1]:.0f}): {text}")
            if len(blocks_sorted) > 10:
                report.append(f"... ({len(blocks_sorted) - 10} more blocks)")
            report.append("")
            report.append("")

        doc.close()

    except Exception as e:
        report.append(f"ERROR: {str(e)}")
        report.append("")

    return "\n".join(report)


def main():
    base_dir = Path("/Volumes/WD Green/dev/git/pdf2md/pdf2md/real-world-pdfs")
    output_dir = base_dir / "detailed_analysis"
    output_dir.mkdir(exist_ok=True)

    pdf_files = list(base_dir.glob("**/*.pdf"))

    print(f"Creating detailed spatial analysis for {len(pdf_files)} PDFs...")
    print()

    all_reports = []

    for pdf_path in sorted(pdf_files):
        print(f"Analyzing: {pdf_path.name}...")
        report = analyze_spatial_layout(str(pdf_path), str(output_dir))
        all_reports.append(report)

        # Save individual report
        report_filename = output_dir / f"{pdf_path.stem}_spatial_analysis.txt"
        with open(report_filename, 'w') as f:
            f.write(report)

    # Save combined report
    combined_path = output_dir / "combined_spatial_analysis.txt"
    with open(combined_path, 'w') as f:
        f.write("\n\n".join(all_reports))

    print()
    print(f"Detailed reports saved to: {output_dir}")
    print(f"Combined report: {combined_path}")


if __name__ == "__main__":
    main()
