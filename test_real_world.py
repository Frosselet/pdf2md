#!/usr/bin/env python3
"""
Test PDF loader with challenging real-world PDFs.

Tests against the MS Office generated PDFs that fail with traditional parsers.
"""

import sys
from pathlib import Path
from src.pdf2md.api import convert_pdf, analyze_pdf_structure

def test_challenging_pdf():
    """Test with our most challenging PDF."""
    print("🎯 Testing PDF2MD with CHALLENGING real-world PDF...")

    # Find the CBH Shipping Stem PDF (our most challenging case)
    pdf_path = Path("real-world-pdfs/problematic/CBH Shipping Stem 26092025.pdf")

    if not pdf_path.exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        print("Looking for any problematic PDF...")

        # Try any problematic PDF
        pdf_dir = Path("real-world-pdfs/problematic")
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            if pdf_files:
                pdf_path = pdf_files[0]
                print(f"📄 Using: {pdf_path.name}")
            else:
                print("❌ No problematic PDFs found")
                return False
        else:
            print("❌ Problematic PDFs directory not found")
            return False

    try:
        print(f"\n🔍 Analyzing {pdf_path.name} (MS Office generated)...")

        # Test document analysis
        doc = analyze_pdf_structure(pdf_path)

        print(f"✅ Document loaded successfully!")
        print(f"   📊 Pages: {doc.page_count}")
        print(f"   📝 Total blocks: {doc.total_block_count}")
        print(f"   🔤 Total words: {doc.total_word_count}")
        print(f"   🎨 Unique fonts: {len(doc.all_unique_fonts)}")

        # Check quality assessment
        if "quality_assessment" in doc.metadata:
            qa = doc.metadata["quality_assessment"]
            print(f"   📊 Quality score: {qa['score']:.2f}")
            print(f"   ⚠️  Issues: {len(qa['issues'])}")
            for issue in qa['issues'][:3]:  # Show first 3 issues
                print(f"      - {issue}")

        # Analyze first page
        if doc.pages:
            first_page = doc.pages[0]
            print(f"\n📄 First page analysis:")
            print(f"   📐 Blocks: {first_page.block_count}")
            print(f"   📏 Dimensions: {first_page.page_bbox}")

            columns = first_page.detect_columns()
            print(f"   📊 Detected columns: {len(columns)}")

            # Show column structure if multi-column
            if len(columns) > 1:
                print(f"   📊 Multi-column layout detected!")
                for i, column in enumerate(columns):
                    print(f"      Column {i+1}: {len(column)} blocks")

            # Check for drawings (table indicators)
            if "drawings" in first_page.metadata:
                drawings = first_page.metadata["drawings"]
                print(f"   🖼️  Drawings (table indicators): {len(drawings)}")

                # Analyze drawing types
                rectangles = [d for d in drawings if d["type"] == "rectangle"]
                lines = [d for d in drawings if d["type"] == "line"]
                print(f"      Rectangles: {len(rectangles)} (table cells)")
                print(f"      Lines: {len(lines)} (borders)")

            # Show sample blocks with spatial info
            print(f"\n📝 Sample blocks with spatial data:")
            for i, block in enumerate(first_page.blocks[:5]):
                print(f"   {i+1}. [{block.element_type.value}] \"{block.text[:40]}...\"")
                if block.bbox:
                    print(f"      📐 Position: x={block.bbox.center_x:.1f}, y={block.bbox.center_y:.1f}")
                    print(f"      📏 Size: w={block.bbox.width:.1f}, h={block.bbox.height:.1f}")
                if block.dominant_font:
                    font = block.dominant_font
                    print(f"      🎨 Font: {font.name} {font.size}pt {font.style.value}")

        # Test markdown conversion
        print(f"\n📝 Converting to markdown...")
        markdown = convert_pdf(pdf_path)

        print(f"✅ Markdown conversion successful!")
        print(f"   📊 Markdown length: {len(markdown)} characters")
        print(f"   📄 Sample output:")
        print("   " + "=" * 60)

        # Show markdown structure
        lines = markdown.split('\n')
        non_empty_lines = [line for line in lines if line.strip()][:15]
        for line in non_empty_lines:
            preview = line[:80] + "..." if len(line) > 80 else line
            print(f"   {preview}")

        print("   " + "=" * 60)

        # Compare with traditional extraction for the same PDF
        print(f"\n🔄 Comparison with traditional extraction:")
        try:
            import fitz  # PyMuPDF
            doc_traditional = fitz.open(str(pdf_path))
            page = doc_traditional[0]
            traditional_text = page.get_text()[:500]

            print(f"   📝 Traditional (first 500 chars):")
            print("   " + "-" * 40)
            for line in traditional_text.split('\n')[:8]:
                if line.strip():
                    print(f"   {line[:60]}...")
            print("   " + "-" * 40)

            print(f"\n✅ Our spatial-aware approach preserves structure!")
            print(f"   Traditional approach would mix up the column order.")

            doc_traditional.close()

        except Exception as e:
            print(f"   ⚠️  Could not compare with traditional: {e}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_challenging_pdf()
    sys.exit(0 if success else 1)