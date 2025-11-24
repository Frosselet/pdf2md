#!/usr/bin/env python3
"""
Quick test script to verify PDF loader functionality.

Tests the PDF loader against one of our real-world challenging PDFs.
"""

import sys
from pathlib import Path
from src.pdf2md.api import convert_pdf, analyze_pdf_structure

def test_pdf_loader():
    """Test PDF loader with a real-world PDF."""
    print("🧪 Testing PDF2MD Loader...")

    # Find a test PDF
    pdf_dir = Path("real-world-pdfs/generated/simple")
    test_pdf = None

    # Try generated PDFs first (they should work)
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if pdf_files:
            test_pdf = pdf_files[0]
            print(f"📄 Using generated test PDF: {test_pdf.name}")

    if not test_pdf:
        # Try real-world PDFs
        pdf_dir = Path("real-world-pdfs/complex")
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            if pdf_files:
                test_pdf = pdf_files[0]
                print(f"📄 Using real-world PDF: {test_pdf.name}")

    if not test_pdf:
        print("❌ No test PDFs found")
        return False

    try:
        print(f"\n🔍 Analyzing structure of {test_pdf.name}...")

        # Test document analysis
        doc = analyze_pdf_structure(test_pdf)

        print(f"✅ Document loaded successfully!")
        print(f"   📊 Pages: {doc.page_count}")
        print(f"   📝 Total blocks: {doc.total_block_count}")
        print(f"   🔤 Total words: {doc.total_word_count}")
        print(f"   🎨 Unique fonts: {len(doc.all_unique_fonts)}")

        # Analyze first page
        if doc.pages:
            first_page = doc.pages[0]
            print(f"\n📄 First page analysis:")
            print(f"   📐 Blocks: {first_page.block_count}")
            print(f"   📏 Dimensions: {first_page.page_bbox}")

            columns = first_page.detect_columns()
            print(f"   📊 Detected columns: {len(columns)}")

            # Show some blocks
            print(f"\n📝 Sample blocks:")
            for i, block in enumerate(first_page.blocks[:3]):
                print(f"   {i+1}. [{block.element_type.value}] \"{block.text[:50]}...\"")
                print(f"      📐 BBox: {block.bbox}")
                if block.dominant_font:
                    font = block.dominant_font
                    print(f"      🎨 Font: {font.name} {font.size}pt {font.style.value}")

        # Test markdown conversion
        print(f"\n📝 Converting to markdown...")
        markdown = convert_pdf(test_pdf)

        print(f"✅ Markdown conversion successful!")
        print(f"   📊 Markdown length: {len(markdown)} characters")
        print(f"   📄 Sample output:")
        print("   " + "-" * 50)

        # Show first few lines of markdown
        lines = markdown.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"   {line[:70]}...")

        print("   " + "-" * 50)

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_loader()
    sys.exit(0 if success else 1)