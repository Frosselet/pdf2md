#!/usr/bin/env python3
"""
Comprehensive PDF Analysis Script
Analyzes real-world PDFs to understand their characteristics and challenges
"""

import fitz  # PyMuPDF
import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def analyze_pdf(pdf_path):
    """Analyze a single PDF file for various characteristics."""
    results = {
        'filename': os.path.basename(pdf_path),
        'path': pdf_path,
        'metadata': {},
        'structure': {},
        'text_quality': {},
        'layout_complexity': {},
        'fonts': {},
        'graphics': {},
        'issues': []
    }

    try:
        doc = fitz.open(pdf_path)

        # Basic metadata
        results['metadata'] = {
            'pages': len(doc),
            'file_size_kb': os.path.getsize(pdf_path) / 1024,
            'creation_date': doc.metadata.get('creationDate', 'Unknown'),
            'mod_date': doc.metadata.get('modDate', 'Unknown'),
            'producer': doc.metadata.get('producer', 'Unknown'),
            'creator': doc.metadata.get('creator', 'Unknown'),
            'title': doc.metadata.get('title', 'Unknown'),
            'format': doc.metadata.get('format', 'Unknown'),
            'encryption': doc.metadata.get('encryption', None)
        }

        # Check if it's MS Office generated
        producer = results['metadata']['producer'].lower()
        creator = results['metadata']['creator'].lower()
        if 'microsoft' in producer or 'microsoft' in creator or 'office' in producer:
            results['issues'].append('MS_OFFICE_GENERATED')

        # Analyze each page
        total_text_length = 0
        total_blocks = 0
        total_fonts = set()
        has_tables = False
        has_multi_column = False
        has_images = False
        has_drawings = False
        encoding_issues = []
        text_extraction_issues = []

        page_details = []

        for page_num, page in enumerate(doc):
            page_info = {
                'page_num': page_num + 1,
                'width': page.rect.width,
                'height': page.rect.height,
                'rotation': page.rotation
            }

            # Text extraction
            text = page.get_text()
            page_info['text_length'] = len(text)
            total_text_length += len(text)

            # Check for text extraction quality
            if text.strip():
                # Check for garbled characters
                garbled_count = sum(1 for c in text if ord(c) > 65535)
                if garbled_count > 0:
                    encoding_issues.append(f"Page {page_num + 1}: {garbled_count} garbled chars")

                # Check for excessive whitespace (layout issues)
                lines = text.split('\n')
                empty_lines = sum(1 for line in lines if not line.strip())
                if len(lines) > 0 and empty_lines / len(lines) > 0.5:
                    text_extraction_issues.append(f"Page {page_num + 1}: Excessive whitespace")

            # Text blocks analysis (for layout)
            blocks = page.get_text("dict")["blocks"]
            total_blocks += len(blocks)
            page_info['blocks'] = len(blocks)

            # Analyze text blocks for multi-column detection
            text_blocks = [b for b in blocks if b.get('type') == 0]  # type 0 = text
            if len(text_blocks) > 1:
                # Check x-coordinates for multiple columns
                x_coords = [b['bbox'][0] for b in text_blocks]
                x_coords_sorted = sorted(set(x_coords))
                if len(x_coords_sorted) > 2:
                    has_multi_column = True

            # Font analysis
            fonts_on_page = set()
            for block in blocks:
                if block.get('type') == 0:  # text block
                    for line in block.get('lines', []):
                        for span in line.get('spans', []):
                            font_info = f"{span.get('font', 'Unknown')}_{span.get('size', 0)}"
                            fonts_on_page.add(font_info)
                            total_fonts.add(font_info)

            page_info['fonts'] = len(fonts_on_page)

            # Image detection
            images = page.get_images()
            if images:
                has_images = True
                page_info['images'] = len(images)

            # Drawings and paths (lines, shapes, etc.)
            drawings = page.get_drawings()
            if drawings:
                has_drawings = True
                page_info['drawings'] = len(drawings)

                # Analyze drawing types
                path_types = defaultdict(int)
                for drawing in drawings:
                    for item in drawing.get('items', []):
                        path_types[item[0]] = path_types.get(item[0], 0) + 1

                page_info['drawing_types'] = dict(path_types)

            # Table detection (heuristic based on drawings)
            if drawings:
                # Look for rectangular patterns (lines)
                horizontal_lines = 0
                vertical_lines = 0
                for drawing in drawings:
                    for item in drawing.get('items', []):
                        if item[0] == 'l':  # line
                            x1, y1, x2, y2 = item[1], item[2], item[3], item[4]
                            if abs(y1 - y2) < 1:  # horizontal
                                horizontal_lines += 1
                            elif abs(x1 - x2) < 1:  # vertical
                                vertical_lines += 1

                if horizontal_lines > 2 and vertical_lines > 2:
                    has_tables = True
                    page_info['table_indicators'] = {
                        'h_lines': horizontal_lines,
                        'v_lines': vertical_lines
                    }

            page_details.append(page_info)

        # Structure summary
        results['structure'] = {
            'total_blocks': total_blocks,
            'avg_blocks_per_page': total_blocks / len(doc) if len(doc) > 0 else 0,
            'has_multi_column': has_multi_column,
            'has_tables': has_tables,
            'has_images': has_images,
            'has_drawings': has_drawings
        }

        # Text quality
        results['text_quality'] = {
            'total_text_length': total_text_length,
            'avg_text_per_page': total_text_length / len(doc) if len(doc) > 0 else 0,
            'encoding_issues': encoding_issues,
            'extraction_issues': text_extraction_issues
        }

        # Font analysis
        results['fonts'] = {
            'unique_fonts': len(total_fonts),
            'font_list': sorted(list(total_fonts))
        }

        # Graphics
        results['graphics'] = {
            'has_images': has_images,
            'has_drawings': has_drawings,
            'page_details': page_details
        }

        doc.close()

        # Identify issues
        if has_multi_column:
            results['issues'].append('MULTI_COLUMN_LAYOUT')
        if has_tables:
            results['issues'].append('TABLE_STRUCTURES')
        if len(total_fonts) > 10:
            results['issues'].append('EXCESSIVE_FONTS')
        if encoding_issues:
            results['issues'].append('ENCODING_PROBLEMS')
        if text_extraction_issues:
            results['issues'].append('WHITESPACE_ISSUES')
        if has_drawings:
            results['issues'].append('COMPLEX_GRAPHICS')
        if total_text_length == 0:
            results['issues'].append('NO_TEXT_EXTRACTED')

    except Exception as e:
        results['error'] = str(e)
        results['issues'].append('PROCESSING_ERROR')

    return results


def categorize_pdf(analysis):
    """Categorize PDF based on complexity."""
    issues = analysis.get('issues', [])

    # Problematic: Multiple severe issues or specific problematic patterns
    problematic_indicators = [
        'MS_OFFICE_GENERATED',
        'NO_TEXT_EXTRACTED',
        'PROCESSING_ERROR',
        'ENCODING_PROBLEMS'
    ]

    # Complex: Multiple layout challenges
    complex_indicators = [
        'MULTI_COLUMN_LAYOUT',
        'TABLE_STRUCTURES',
        'COMPLEX_GRAPHICS',
        'EXCESSIVE_FONTS'
    ]

    problematic_count = sum(1 for issue in issues if issue in problematic_indicators)
    complex_count = sum(1 for issue in issues if issue in complex_indicators)

    if problematic_count > 0:
        return 'problematic'
    elif complex_count >= 2:
        return 'complex'
    elif complex_count == 1:
        return 'complex'
    else:
        return 'simple'


def generate_summary_report(all_results):
    """Generate a comprehensive summary report."""
    report = []
    report.append("=" * 80)
    report.append("REAL-WORLD PDF ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")

    # Overall statistics
    report.append("OVERALL STATISTICS")
    report.append("-" * 80)
    report.append(f"Total PDFs analyzed: {len(all_results)}")

    categories = defaultdict(list)
    for result in all_results:
        cat = categorize_pdf(result)
        categories[cat].append(result['filename'])

    for cat in ['simple', 'complex', 'problematic']:
        count = len(categories[cat])
        report.append(f"{cat.capitalize()}: {count} PDFs")

    report.append("")

    # Issue frequency
    all_issues = defaultdict(int)
    for result in all_results:
        for issue in result.get('issues', []):
            all_issues[issue] += 1

    report.append("COMMON ISSUES (Frequency)")
    report.append("-" * 80)
    for issue, count in sorted(all_issues.items(), key=lambda x: x[1], reverse=True):
        report.append(f"{issue}: {count} PDFs")

    report.append("")

    # Individual PDF details
    report.append("INDIVIDUAL PDF ANALYSIS")
    report.append("=" * 80)

    for result in sorted(all_results, key=lambda x: x['filename']):
        report.append("")
        report.append(f"FILE: {result['filename']}")
        report.append("-" * 80)

        # Categorization
        category = categorize_pdf(result)
        report.append(f"Current Category: {os.path.dirname(result['path']).split('/')[-1]}")
        report.append(f"Suggested Category: {category}")
        report.append("")

        # Metadata
        meta = result.get('metadata', {})
        report.append(f"Pages: {meta.get('pages', 'Unknown')}")
        report.append(f"File Size: {meta.get('file_size_kb', 0):.2f} KB")
        report.append(f"Producer: {meta.get('producer', 'Unknown')}")
        report.append(f"Creator: {meta.get('creator', 'Unknown')}")
        report.append("")

        # Check for processing error
        if 'error' in result:
            report.append(f"ERROR: {result['error']}")
            report.append("This PDF could not be fully analyzed due to processing errors.")
            report.append("")

        # Structure
        struct = result.get('structure', {})
        if struct:
            report.append("Layout Characteristics:")
            report.append(f"  - Blocks: {struct.get('total_blocks', 0)} total, {struct.get('avg_blocks_per_page', 0):.1f} per page")
            report.append(f"  - Multi-column: {'YES' if struct.get('has_multi_column') else 'NO'}")
            report.append(f"  - Tables: {'YES' if struct.get('has_tables') else 'NO'}")
            report.append(f"  - Images: {'YES' if struct.get('has_images') else 'NO'}")
            report.append(f"  - Drawings/Shapes: {'YES' if struct.get('has_drawings') else 'NO'}")
            report.append("")

        # Text quality
        text_q = result.get('text_quality', {})
        if text_q:
            report.append("Text Extraction:")
            report.append(f"  - Total characters: {text_q.get('total_text_length', 0)}")
            report.append(f"  - Avg per page: {text_q.get('avg_text_per_page', 0):.0f}")
            if text_q.get('encoding_issues'):
                report.append(f"  - Encoding issues: {len(text_q['encoding_issues'])}")
            if text_q.get('extraction_issues'):
                report.append(f"  - Extraction issues: {len(text_q['extraction_issues'])}")
            report.append("")

        # Fonts
        fonts = result.get('fonts', {})
        if fonts:
            report.append(f"Fonts: {fonts.get('unique_fonts', 0)} unique font/size combinations")
            if fonts.get('unique_fonts', 0) <= 5 and fonts.get('font_list'):
                for font in fonts['font_list']:
                    report.append(f"  - {font}")
            report.append("")

        # Issues
        if result.get('issues'):
            report.append("Issues Detected:")
            for issue in result['issues']:
                report.append(f"  - {issue}")
            report.append("")

        # Key challenges
        report.append("KEY CHALLENGES FOR TRADITIONAL PARSERS:")
        challenges = []

        if 'error' in result:
            challenges.append("  - PDF structure is malformed or uses non-standard encoding")
            challenges.append("  - Traditional parsers fail to even open/process this file correctly")

        if struct.get('has_multi_column'):
            challenges.append("  - Multi-column layout requires spatial awareness to maintain reading order")

        if struct.get('has_tables'):
            challenges.append("  - Table structures need cell boundary detection and alignment")

        if struct.get('has_drawings'):
            graphics = result.get('graphics', {})
            page_details = graphics.get('page_details', [])
            if page_details:
                page_with_most_drawings = max(page_details,
                                             key=lambda p: p.get('drawings', 0),
                                             default={'drawings': 0})
                if page_with_most_drawings.get('drawings', 0) > 0:
                    challenges.append(f"  - Complex graphics/shapes ({page_with_most_drawings.get('drawings', 0)} max per page) can interfere with text extraction")

        if fonts.get('unique_fonts', 0) > 10:
            challenges.append(f"  - Excessive font variations ({fonts['unique_fonts']}) indicate complex formatting")

        if 'MS_OFFICE_GENERATED' in result.get('issues', []):
            challenges.append("  - MS Office PDFs may have non-standard text positioning and spacing")

        if text_q.get('encoding_issues'):
            challenges.append("  - Character encoding problems will corrupt output")

        if text_q.get('avg_text_per_page', 0) < 100 and text_q.get('avg_text_per_page', 0) > 0:
            challenges.append("  - Low text density suggests image-heavy or form-based content")

        if not challenges:
            challenges.append("  - (Relatively straightforward PDF)")

        for challenge in challenges:
            report.append(challenge)

        report.append("")

    # Summary of spatial layout challenges
    report.append("=" * 80)
    report.append("SPATIAL LAYOUT CHALLENGES SUMMARY")
    report.append("=" * 80)
    report.append("")
    report.append("Traditional parsers fail on these PDFs because they:")
    report.append("")
    report.append("1. IGNORE SPATIAL POSITIONING:")
    report.append("   - Cannot handle multi-column layouts (text extracted in wrong order)")
    report.append("   - Fail to recognize table structures without explicit markup")
    report.append("   - Mix up headers, footers, and body text")
    report.append("")
    report.append("2. LACK STRUCTURE AWARENESS:")
    report.append("   - Cannot distinguish between background graphics and content")
    report.append("   - Fail to group related text blocks")
    report.append("   - Cannot infer semantic meaning from layout")
    report.append("")
    report.append("3. POOR HANDLING OF MS OFFICE ARTIFACTS:")
    report.append("   - MS Office PDFs have quirky spacing and positioning")
    report.append("   - Text may be split into many small fragments")
    report.append("   - Font embedding issues common")
    report.append("")
    report.append("4. TEXT EXTRACTION ISSUES:")
    report.append("   - Encoding problems with special characters")
    report.append("   - Excessive whitespace from poor layout understanding")
    report.append("   - Missing text from image-based content")
    report.append("")
    report.append("OUR SPATIAL-AWARE APPROACH ADDRESSES THESE BY:")
    report.append("")
    report.append("1. Analyzing X/Y coordinates of all text elements")
    report.append("2. Detecting columns, tables, and structured regions")
    report.append("3. Maintaining reading order based on spatial layout")
    report.append("4. Separating background elements from content")
    report.append("5. Using font and position to infer document structure")
    report.append("")

    return "\n".join(report)


def main():
    # Find all PDFs
    base_dir = Path("/Volumes/WD Green/dev/git/pdf2md/pdf2md/real-world-pdfs")
    pdf_files = list(base_dir.glob("**/*.pdf"))

    print(f"Found {len(pdf_files)} PDF files to analyze\n")

    all_results = []

    for pdf_path in sorted(pdf_files):
        print(f"Analyzing: {pdf_path.name}...")
        result = analyze_pdf(str(pdf_path))
        all_results.append(result)

    # Generate detailed JSON report
    json_output = {
        'analysis_date': datetime.now().isoformat(),
        'total_pdfs': len(all_results),
        'results': all_results
    }

    json_path = base_dir / "analysis_detailed.json"
    with open(json_path, 'w') as f:
        json.dump(json_output, f, indent=2)

    print(f"\nDetailed JSON report saved to: {json_path}")

    # Generate summary report
    summary = generate_summary_report(all_results)

    summary_path = base_dir / "analysis_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(summary)

    print(f"Summary report saved to: {summary_path}")
    print("\n" + "=" * 80)
    print(summary)


if __name__ == "__main__":
    main()
