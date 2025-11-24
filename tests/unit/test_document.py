"""
Unit tests for document structure classes.

Tests the hierarchical document model: Word -> Block -> Page -> Document
"""

import pytest
import json
from src.pdf2md.core.document import (
    Word, Block, Page, Document, FontInfo, FontStyle, ElementType
)
from src.pdf2md.core.bbox import BBox


class TestFontInfo:
    """Test FontInfo class."""

    def test_creation(self):
        """Test font info creation."""
        font = FontInfo("Arial", 12.0, FontStyle.BOLD, "#000000")
        assert font.name == "Arial"
        assert font.size == 12.0
        assert font.style == FontStyle.BOLD
        assert font.color == "#000000"

    def test_style_checks(self):
        """Test style checking methods."""
        normal = FontInfo("Arial", 12.0, FontStyle.NORMAL)
        bold = FontInfo("Arial", 12.0, FontStyle.BOLD)
        italic = FontInfo("Arial", 12.0, FontStyle.ITALIC)
        bold_italic = FontInfo("Arial", 12.0, FontStyle.BOLD_ITALIC)

        assert not normal.is_bold()
        assert not normal.is_italic()

        assert bold.is_bold()
        assert not bold.is_italic()

        assert not italic.is_bold()
        assert italic.is_italic()

        assert bold_italic.is_bold()
        assert bold_italic.is_italic()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        font = FontInfo("Arial", 12.0, FontStyle.BOLD, "#000000")
        expected = {
            "name": "Arial",
            "size": 12.0,
            "style": "bold",
            "color": "#000000"
        }
        assert font.to_dict() == expected


class TestWord:
    """Test Word class."""

    def setup_method(self):
        """Set up test word."""
        self.font = FontInfo("Arial", 12.0, FontStyle.NORMAL)
        self.bbox = BBox(10, 20, 50, 32)
        self.word = Word("Hello", self.bbox, self.font)

    def test_creation(self):
        """Test word creation."""
        assert self.word.text == "Hello"
        assert self.word.bbox == self.bbox
        assert self.word.font == self.font
        assert self.word.confidence == 1.0

    def test_invalid_creation(self):
        """Test invalid word creation."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            Word("   ", self.bbox, self.font)

        with pytest.raises(ValueError, match="Confidence must be between"):
            Word("Hello", self.bbox, self.font, confidence=1.5)

    def test_content_classification(self):
        """Test content type classification."""
        # Note: Whitespace-only words are not allowed by design validation

        # Punctuation
        punct = Word("!", self.bbox, self.font)
        assert punct.is_punctuation

        # Number
        number = Word("123.45", self.bbox, self.font)
        assert number.is_number

        currency = Word("$1,234.56", self.bbox, self.font)
        assert currency.is_number

        # Regular text
        assert not self.word.is_punctuation
        assert not self.word.is_number

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = self.word.to_dict()
        assert result["text"] == "Hello"
        assert result["bbox"] == self.bbox.to_dict()
        assert result["font"] == self.font.to_dict()
        assert result["confidence"] == 1.0
        assert result["element_type"] == "text"


class TestBlock:
    """Test Block class."""

    def setup_method(self):
        """Set up test block."""
        self.font = FontInfo("Arial", 12.0, FontStyle.NORMAL)
        self.words = [
            Word("Hello", BBox(10, 20, 30, 32), self.font),
            Word("world", BBox(35, 20, 55, 32), self.font),
            Word("!", BBox(60, 20, 65, 32), self.font)
        ]
        self.block = Block(self.words)

    def test_creation(self):
        """Test block creation."""
        assert len(self.block.words) == 3
        assert self.block.element_type == ElementType.PARAGRAPH
        assert self.block.confidence == 1.0

    def test_text_property(self):
        """Test text aggregation."""
        assert self.block.text == "Hello world !"

    def test_bbox_property(self):
        """Test bbox calculation."""
        bbox = self.block.bbox
        assert bbox == BBox(10, 20, 65, 32)

    def test_empty_block_bbox(self):
        """Test bbox for empty block."""
        empty_block = Block([])
        assert empty_block.bbox is None

    def test_font_analysis(self):
        """Test font analysis methods."""
        # All words have same font
        fonts = self.block.font_info
        assert len(fonts) == 1
        assert fonts[0] == self.font

        dominant = self.block.dominant_font
        assert dominant == self.font

        avg_size = self.block.avg_font_size
        assert avg_size == 12.0

    def test_mixed_fonts(self):
        """Test block with mixed fonts."""
        bold_font = FontInfo("Arial", 14.0, FontStyle.BOLD)
        mixed_words = [
            Word("Normal", BBox(0, 0, 20, 12), self.font),
            Word("Bold", BBox(25, 0, 40, 14), bold_font),
            Word("text", BBox(45, 0, 60, 12), self.font),
        ]
        mixed_block = Block(mixed_words)

        fonts = mixed_block.font_info
        assert len(fonts) == 2

        # Normal font appears twice, should be dominant
        dominant = mixed_block.dominant_font
        assert dominant == self.font

        assert mixed_block.has_bold
        assert not mixed_block.has_italic

    def test_style_detection(self):
        """Test style detection methods."""
        assert not self.block.has_bold
        assert not self.block.has_italic
        assert not self.block.is_all_caps

        # All caps block
        caps_words = [Word("TITLE", BBox(0, 0, 20, 12), self.font)]
        caps_block = Block(caps_words)
        assert caps_block.is_all_caps

    def test_word_count(self):
        """Test word counting."""
        assert self.block.word_count == 3

    def test_add_word(self):
        """Test adding words to block."""
        new_word = Word("test", BBox(70, 20, 90, 32), self.font)
        self.block.add_word(new_word)

        assert len(self.block.words) == 4
        assert self.block.text == "Hello world ! test"

    def test_merge_blocks(self):
        """Test merging blocks."""
        other_words = [Word("merged", BBox(100, 20, 140, 32), self.font)]
        other_block = Block(other_words, confidence=0.8)

        merged = self.block.merge_with(other_block)

        assert len(merged.words) == 4
        assert merged.text == "Hello world ! merged"
        assert merged.confidence == 1.0  # Higher confidence wins

    def test_header_detection(self):
        """Test header detection heuristics."""
        # Large, bold text
        large_font = FontInfo("Arial", 18.0, FontStyle.BOLD)
        header_words = [Word("CHAPTER", BBox(0, 0, 50, 18), large_font)]
        header_block = Block(header_words)

        assert header_block.is_likely_header()

        # Normal text should not be detected as header
        assert not self.block.is_likely_header()

    def test_caption_detection(self):
        """Test caption detection heuristics."""
        # Small italic text
        small_italic = FontInfo("Arial", 9.0, FontStyle.ITALIC)
        caption_words = [Word("Figure", BBox(0, 0, 30, 9), small_italic)]
        caption_block = Block(caption_words)

        assert caption_block.is_likely_caption()

        # Text starting with figure label
        figure_words = [Word("Figure 1: Description", BBox(0, 0, 100, 12), self.font)]
        figure_block = Block(figure_words)

        assert figure_block.is_likely_caption()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = self.block.to_dict()

        assert result["text"] == "Hello world !"
        assert "bbox" in result
        assert len(result["words"]) == 3
        assert result["element_type"] == "paragraph"
        assert "analysis" in result
        assert result["analysis"]["word_count"] == 3


class TestPage:
    """Test Page class."""

    def setup_method(self):
        """Set up test page."""
        font = FontInfo("Arial", 12.0, FontStyle.NORMAL)

        # Create some blocks
        self.block1 = Block([
            Word("First", BBox(10, 50, 30, 62), font),
            Word("block", BBox(35, 50, 55, 62), font)
        ])

        self.block2 = Block([
            Word("Second", BBox(10, 30, 40, 42), font),
            Word("block", BBox(45, 30, 65, 42), font)
        ])

        self.page = Page(0, [self.block1, self.block2])

    def test_creation(self):
        """Test page creation."""
        assert self.page.number == 0
        assert len(self.page.blocks) == 2

    def test_invalid_page_number(self):
        """Test invalid page number."""
        with pytest.raises(ValueError, match="Page number must be non-negative"):
            Page(-1, [])

    def test_text_aggregation(self):
        """Test text aggregation."""
        text = self.page.text
        assert "First block" in text
        assert "Second block" in text

    def test_statistics(self):
        """Test page statistics."""
        assert self.page.word_count == 4
        assert self.page.block_count == 2

        all_words = self.page.all_words
        assert len(all_words) == 4

    def test_add_block(self):
        """Test adding block to page."""
        font = FontInfo("Arial", 12.0, FontStyle.NORMAL)
        new_block = Block([Word("New", BBox(0, 0, 20, 12), font)])

        self.page.add_block(new_block)
        assert len(self.page.blocks) == 3

    def test_get_blocks_by_type(self):
        """Test filtering blocks by type."""
        # Change one block type
        self.block1.element_type = ElementType.HEADER

        headers = self.page.get_blocks_by_type(ElementType.HEADER)
        paragraphs = self.page.get_blocks_by_type(ElementType.PARAGRAPH)

        assert len(headers) == 1
        assert len(paragraphs) == 1

    def test_get_blocks_in_bbox(self):
        """Test spatial block filtering."""
        search_bbox = BBox(0, 45, 70, 65)  # Should overlap with block1

        overlapping = self.page.get_blocks_in_bbox(search_bbox, overlap_threshold=0.3)
        assert len(overlapping) == 1
        assert overlapping[0] == self.block1

    def test_sort_reading_order(self):
        """Test reading order sorting."""
        # Create blocks in mixed order
        font = FontInfo("Arial", 12.0, FontStyle.NORMAL)

        # Bottom block (should be last in reading order)
        bottom_block = Block([Word("Bottom", BBox(10, 10, 40, 22), font)])

        # Top-right block (should be second)
        top_right_block = Block([Word("TopRight", BBox(50, 50, 90, 62), font)])

        # Top-left block (should be first)
        top_left_block = Block([Word("TopLeft", BBox(10, 50, 40, 62), font)])

        page = Page(0, [bottom_block, top_right_block, top_left_block])
        page.sort_blocks_reading_order()

        # Check order: top-left, top-right, bottom
        assert page.blocks[0] == top_left_block
        assert page.blocks[1] == top_right_block
        assert page.blocks[2] == bottom_block

    def test_detect_columns(self):
        """Test column detection."""
        font = FontInfo("Arial", 12.0, FontStyle.NORMAL)

        # Create blocks in two columns
        left_col_blocks = [
            Block([Word("Left1", BBox(10, 50, 40, 62), font)]),
            Block([Word("Left2", BBox(10, 30, 40, 42), font)])
        ]

        right_col_blocks = [
            Block([Word("Right1", BBox(100, 50, 130, 62), font)]),
            Block([Word("Right2", BBox(100, 30, 130, 42), font)])
        ]

        all_blocks = left_col_blocks + right_col_blocks
        page = Page(0, all_blocks)

        columns = page.detect_columns(tolerance=20)

        assert len(columns) == 2
        # Each column should have 2 blocks
        assert len(columns[0]) == 2
        assert len(columns[1]) == 2

    def test_unique_fonts(self):
        """Test unique font detection."""
        # Both blocks use same font
        fonts = self.page.unique_fonts
        assert len(fonts) == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = self.page.to_dict()

        assert result["number"] == 0
        assert len(result["blocks"]) == 2
        assert "analysis" in result
        assert result["analysis"]["word_count"] == 4
        assert result["analysis"]["block_count"] == 2


class TestDocument:
    """Test Document class."""

    def setup_method(self):
        """Set up test document."""
        font = FontInfo("Arial", 12.0, FontStyle.NORMAL)

        # Create pages with blocks
        page1_block = Block([Word("Page1", BBox(0, 0, 30, 12), font)])
        page2_block = Block([Word("Page2", BBox(0, 0, 30, 12), font)])

        self.page1 = Page(0, [page1_block])
        self.page2 = Page(1, [page2_block])

        self.document = Document([self.page1, self.page2])

    def test_creation(self):
        """Test document creation."""
        assert len(self.document.pages) == 2
        assert self.document.page_count == 2

    def test_statistics(self):
        """Test document statistics."""
        assert self.document.total_word_count == 2
        assert self.document.total_block_count == 2

    def test_add_page(self):
        """Test adding page to document."""
        font = FontInfo("Arial", 12.0, FontStyle.NORMAL)
        new_block = Block([Word("Page3", BBox(0, 0, 30, 12), font)])
        new_page = Page(2, [new_block])

        self.document.add_page(new_page)
        assert self.document.page_count == 3

    def test_get_page(self):
        """Test page retrieval."""
        assert self.document.get_page(0) == self.page1
        assert self.document.get_page(1) == self.page2
        assert self.document.get_page(5) is None  # Out of range

    def test_get_text(self):
        """Test full text extraction."""
        text = self.document.get_text()
        assert "Page1" in text
        assert "Page2" in text
        assert "---" in text  # Default separator

        custom_text = self.document.get_text(page_separator=" | ")
        assert " | " in custom_text

    def test_unique_fonts(self):
        """Test unique font collection across document."""
        fonts = self.document.all_unique_fonts
        assert len(fonts) == 1  # Both pages use same font

    def test_typography_hierarchy(self):
        """Test typography analysis."""
        # Add some variety in font sizes
        large_font = FontInfo("Arial", 18.0, FontStyle.BOLD)
        small_font = FontInfo("Arial", 9.0, FontStyle.ITALIC)

        large_block = Block([Word("Title", BBox(0, 0, 30, 18), large_font)])
        small_block = Block([Word("Caption", BBox(0, 0, 30, 9), small_font)])

        varied_page = Page(2, [large_block, small_block])
        self.document.add_page(varied_page)

        hierarchy = self.document.analyze_typography_hierarchy()

        assert "hierarchy" in hierarchy
        assert "total_font_variations" in hierarchy
        assert hierarchy["total_font_variations"] == 3  # Original + large + small

        # Check size range
        size_range = hierarchy["size_range"]
        assert size_range["min"] == 9.0
        assert size_range["max"] == 18.0

    def test_iteration(self):
        """Test document iteration."""
        pages = list(self.document)
        assert len(pages) == 2
        assert pages[0] == self.page1
        assert pages[1] == self.page2

    def test_indexing(self):
        """Test document indexing."""
        assert self.document[0] == self.page1
        assert self.document[1] == self.page2

    def test_length(self):
        """Test document length."""
        assert len(self.document) == 2

    def test_to_dict_and_json(self):
        """Test conversion to dictionary and JSON."""
        result = self.document.to_dict()

        assert len(result["pages"]) == 2
        assert "analysis" in result
        assert result["analysis"]["page_count"] == 2

        # Test JSON conversion doesn't raise errors
        json_str = self.document.to_json()
        parsed = json.loads(json_str)
        assert len(parsed["pages"]) == 2


class TestElementTypeEnum:
    """Test ElementType enumeration."""

    def test_enum_values(self):
        """Test enum values."""
        assert ElementType.TEXT.value == "text"
        assert ElementType.HEADER.value == "header"
        assert ElementType.TABLE.value == "table"

    def test_enum_usage(self):
        """Test enum usage in classes."""
        font = FontInfo("Arial", 12.0)
        word = Word("Test", BBox(0, 0, 20, 12), font, element_type=ElementType.HEADER)

        assert word.element_type == ElementType.HEADER
        assert word.to_dict()["element_type"] == "header"