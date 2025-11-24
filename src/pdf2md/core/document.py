"""
Document structure classes for spatial-aware PDF parsing.

These classes represent the hierarchical structure of a PDF document:
Document -> Page -> Block -> Word

Each level maintains spatial information and relationships between elements.
"""

from typing import List, Optional, Dict, Any, Iterator, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from .bbox import BBox


class ElementType(Enum):
    """Types of document elements."""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    DRAWING = "drawing"
    HEADER = "header"
    FOOTER = "footer"
    TITLE = "title"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    CAPTION = "caption"
    CODE = "code"


class FontStyle(Enum):
    """Font style variations."""
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"


@dataclass
class FontInfo:
    """Font information for text elements."""
    name: str
    size: float
    style: FontStyle = FontStyle.NORMAL
    color: Optional[str] = None

    def is_bold(self) -> bool:
        """Check if font is bold."""
        return self.style in (FontStyle.BOLD, FontStyle.BOLD_ITALIC)

    def is_italic(self) -> bool:
        """Check if font is italic."""
        return self.style in (FontStyle.ITALIC, FontStyle.BOLD_ITALIC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "style": self.style.value,
            "color": self.color
        }


@dataclass
class Word:
    """
    Individual word with spatial and font information.

    Represents the smallest unit of text with consistent formatting.
    """
    text: str
    bbox: BBox
    font: FontInfo
    confidence: float = 1.0
    element_type: ElementType = ElementType.TEXT

    def __post_init__(self):
        """Validate word data."""
        if not self.text.strip():
            raise ValueError("Word text cannot be empty or whitespace only")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

    @property
    def is_whitespace(self) -> bool:
        """Check if word contains only whitespace."""
        return not self.text.strip()

    @property
    def is_punctuation(self) -> bool:
        """Check if word contains only punctuation."""
        return self.text.strip() and all(not c.isalnum() for c in self.text.strip())

    @property
    def is_number(self) -> bool:
        """Check if word is a number."""
        try:
            float(self.text.strip().replace(',', '').replace('$', '').replace('%', ''))
            return True
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "font": self.font.to_dict(),
            "confidence": self.confidence,
            "element_type": self.element_type.value
        }


@dataclass
class Block:
    """
    Block of related words forming a coherent text unit.

    Could be a paragraph, heading, table cell, caption, etc.
    """
    words: List[Word] = field(default_factory=list)
    element_type: ElementType = ElementType.PARAGRAPH
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate block data."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

    @property
    def text(self) -> str:
        """Get full text content of the block."""
        return " ".join(word.text for word in self.words if not word.is_whitespace)

    @property
    def bbox(self) -> Optional[BBox]:
        """Get bounding box encompassing all words."""
        if not self.words:
            return None

        word_bboxes = [word.bbox for word in self.words]
        if len(word_bboxes) == 1:
            return word_bboxes[0]

        result = word_bboxes[0]
        for bbox in word_bboxes[1:]:
            result = result.union(bbox)
        return result

    @property
    def font_info(self) -> List[FontInfo]:
        """Get unique font information from all words."""
        fonts = {}
        for word in self.words:
            key = (word.font.name, word.font.size, word.font.style)
            fonts[key] = word.font
        return list(fonts.values())

    @property
    def dominant_font(self) -> Optional[FontInfo]:
        """Get the most common font in the block."""
        if not self.words:
            return None

        font_counts = {}
        for word in self.words:
            key = (word.font.name, word.font.size, word.font.style)
            font_counts[key] = font_counts.get(key, 0) + 1

        if not font_counts:
            return None

        dominant_key = max(font_counts.keys(), key=lambda k: font_counts[k])
        # Find first word with this font to get the FontInfo object
        for word in self.words:
            if (word.font.name, word.font.size, word.font.style) == dominant_key:
                return word.font

        return None

    @property
    def avg_font_size(self) -> float:
        """Get average font size in the block."""
        if not self.words:
            return 0.0
        return sum(word.font.size for word in self.words) / len(self.words)

    @property
    def has_bold(self) -> bool:
        """Check if block contains any bold text."""
        return any(word.font.is_bold() for word in self.words)

    @property
    def has_italic(self) -> bool:
        """Check if block contains any italic text."""
        return any(word.font.is_italic() for word in self.words)

    @property
    def is_all_caps(self) -> bool:
        """Check if all text is uppercase."""
        text = self.text
        return text and text.isupper() and any(c.isalpha() for c in text)

    @property
    def word_count(self) -> int:
        """Get number of words (excluding whitespace)."""
        return len([w for w in self.words if not w.is_whitespace])

    def add_word(self, word: Word) -> None:
        """Add a word to the block."""
        self.words.append(word)

    def merge_with(self, other: "Block") -> "Block":
        """Merge this block with another block."""
        merged_words = self.words + other.words
        merged_metadata = {**self.metadata, **other.metadata}

        # Use the element type of the block with higher confidence
        if other.confidence > self.confidence:
            element_type = other.element_type
            confidence = other.confidence
        else:
            element_type = self.element_type
            confidence = self.confidence

        return Block(
            words=merged_words,
            element_type=element_type,
            confidence=confidence,
            metadata=merged_metadata
        )

    def is_likely_header(self) -> bool:
        """Heuristic to determine if block is likely a header."""
        if not self.words:
            return False

        dominant = self.dominant_font
        if not dominant:
            return False

        # Headers typically have:
        # - Larger font size
        # - Bold text
        # - Shorter text
        # - All caps or title case

        is_large = dominant.size >= 14
        is_bold = dominant.is_bold()
        is_short = len(self.text.split()) <= 10
        is_caps = self.is_all_caps

        # Score based on header characteristics
        score = sum([is_large, is_bold, is_short, is_caps])
        return score >= 2

    def is_likely_caption(self) -> bool:
        """Heuristic to determine if block is likely a caption."""
        if not self.words:
            return False

        dominant = self.dominant_font
        if not dominant:
            return False

        # Captions typically have:
        # - Smaller font size
        # - Italic text
        # - Start with "Figure", "Table", "Image", etc.

        is_small = dominant.size <= 10
        is_italic = dominant.is_italic()

        text_lower = self.text.lower()
        starts_with_label = any(
            text_lower.startswith(label)
            for label in ["figure", "table", "image", "chart", "graph", "diagram"]
        )

        return (is_small and is_italic) or starts_with_label

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "words": [word.to_dict() for word in self.words],
            "element_type": self.element_type.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "dominant_font": self.dominant_font.to_dict() if self.dominant_font else None,
            "analysis": {
                "word_count": self.word_count,
                "avg_font_size": self.avg_font_size,
                "has_bold": self.has_bold,
                "has_italic": self.has_italic,
                "is_all_caps": self.is_all_caps,
                "likely_header": self.is_likely_header(),
                "likely_caption": self.is_likely_caption()
            }
        }


@dataclass
class Page:
    """
    Single page containing blocks and layout information.

    Maintains spatial organization and page-level metadata.
    """
    number: int
    blocks: List[Block] = field(default_factory=list)
    page_bbox: Optional[BBox] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate page data."""
        if self.number < 0:
            raise ValueError("Page number must be non-negative")

    @property
    def text(self) -> str:
        """Get full text content of the page."""
        return "\n\n".join(block.text for block in self.blocks if block.text.strip())

    @property
    def word_count(self) -> int:
        """Get total word count on the page."""
        return sum(block.word_count for block in self.blocks)

    @property
    def block_count(self) -> int:
        """Get number of blocks on the page."""
        return len(self.blocks)

    @property
    def all_words(self) -> List[Word]:
        """Get all words from all blocks."""
        words = []
        for block in self.blocks:
            words.extend(block.words)
        return words

    @property
    def unique_fonts(self) -> List[FontInfo]:
        """Get unique font information from all words."""
        fonts = {}
        for word in self.all_words:
            key = (word.font.name, word.font.size, word.font.style)
            fonts[key] = word.font
        return list(fonts.values())

    def add_block(self, block: Block) -> None:
        """Add a block to the page."""
        self.blocks.append(block)

    def get_blocks_by_type(self, element_type: ElementType) -> List[Block]:
        """Get all blocks of a specific type."""
        return [block for block in self.blocks if block.element_type == element_type]

    def get_blocks_in_bbox(self, bbox: BBox, overlap_threshold: float = 0.5) -> List[Block]:
        """Get blocks that significantly overlap with the given bbox."""
        matching_blocks = []
        for block in self.blocks:
            if block.bbox and block.bbox.intersection_ratio(bbox) >= overlap_threshold:
                matching_blocks.append(block)
        return matching_blocks

    def sort_blocks_reading_order(self) -> None:
        """Sort blocks in reading order (top-to-bottom, left-to-right)."""
        def reading_order_key(block: Block) -> tuple:
            if not block.bbox:
                return (0, 0)  # Put blocks without bbox at the beginning

            # Primary sort: top to bottom (higher Y values first in PDF coordinates)
            # Secondary sort: left to right
            return (-block.bbox.center_y, block.bbox.center_x)

        self.blocks.sort(key=reading_order_key)

    def detect_columns(self, tolerance: float = 10.0) -> List[List[Block]]:
        """
        Detect column layout and group blocks by column.

        Args:
            tolerance: Maximum horizontal distance for blocks to be in same column

        Returns:
            List of columns, each containing blocks in that column
        """
        if not self.blocks:
            return []

        # Get blocks with bboxes
        blocks_with_bbox = [b for b in self.blocks if b.bbox]
        if not blocks_with_bbox:
            return []

        # Sort by X position
        blocks_with_bbox.sort(key=lambda b: b.bbox.center_x)

        columns = []
        current_column = [blocks_with_bbox[0]]

        for block in blocks_with_bbox[1:]:
            # Check if block belongs to current column
            if any(
                abs(block.bbox.center_x - existing.bbox.center_x) <= tolerance
                for existing in current_column
            ):
                current_column.append(block)
            else:
                columns.append(current_column)
                current_column = [block]

        columns.append(current_column)

        # Sort blocks within each column by Y position (top to bottom)
        for column in columns:
            column.sort(key=lambda b: -b.bbox.center_y)

        return columns

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "number": self.number,
            "blocks": [block.to_dict() for block in self.blocks],
            "page_bbox": self.page_bbox.to_dict() if self.page_bbox else None,
            "metadata": self.metadata,
            "analysis": {
                "word_count": self.word_count,
                "block_count": self.block_count,
                "unique_fonts": [font.to_dict() for font in self.unique_fonts],
                "detected_columns": len(self.detect_columns())
            }
        }


@dataclass
class Document:
    """
    Complete document containing all pages and document-level metadata.

    Provides high-level operations across the entire document.
    """
    pages: List[Page] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_path: Optional[str] = None

    @property
    def page_count(self) -> int:
        """Get number of pages in the document."""
        return len(self.pages)

    @property
    def total_word_count(self) -> int:
        """Get total word count across all pages."""
        return sum(page.word_count for page in self.pages)

    @property
    def total_block_count(self) -> int:
        """Get total block count across all pages."""
        return sum(page.block_count for page in self.pages)

    @property
    def all_unique_fonts(self) -> List[FontInfo]:
        """Get unique font information from entire document."""
        fonts = {}
        for page in self.pages:
            for font in page.unique_fonts:
                key = (font.name, font.size, font.style)
                fonts[key] = font
        return list(fonts.values())

    def add_page(self, page: Page) -> None:
        """Add a page to the document."""
        self.pages.append(page)

    def get_page(self, number: int) -> Optional[Page]:
        """Get page by number (0-indexed)."""
        if 0 <= number < len(self.pages):
            return self.pages[number]
        return None

    def get_text(self, page_separator: str = "\n\n---\n\n") -> str:
        """Get full text content of the document."""
        return page_separator.join(page.text for page in self.pages if page.text.strip())

    def analyze_typography_hierarchy(self) -> Dict[str, Any]:
        """Analyze font usage to determine document structure hierarchy."""
        fonts = self.all_unique_fonts
        if not fonts:
            return {"error": "No fonts found"}

        # Group fonts by size
        size_groups = {}
        for font in fonts:
            size = font.size
            if size not in size_groups:
                size_groups[size] = []
            size_groups[size].append(font)

        # Sort sizes in descending order
        sorted_sizes = sorted(size_groups.keys(), reverse=True)

        hierarchy = {}
        for i, size in enumerate(sorted_sizes):
            level = f"level_{i + 1}"
            hierarchy[level] = {
                "size": size,
                "fonts": [f.to_dict() for f in size_groups[size]],
                "likely_role": _infer_typography_role(size, sorted_sizes, i)
            }

        return {
            "hierarchy": hierarchy,
            "total_font_variations": len(fonts),
            "size_range": {
                "min": min(sorted_sizes) if sorted_sizes else 0,
                "max": max(sorted_sizes) if sorted_sizes else 0
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pages": [page.to_dict() for page in self.pages],
            "metadata": self.metadata,
            "source_path": self.source_path,
            "analysis": {
                "page_count": self.page_count,
                "total_word_count": self.total_word_count,
                "total_block_count": self.total_block_count,
                "typography_hierarchy": self.analyze_typography_hierarchy(),
                "unique_fonts": [font.to_dict() for font in self.all_unique_fonts]
            }
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def __iter__(self) -> Iterator[Page]:
        """Iterate over pages."""
        return iter(self.pages)

    def __len__(self) -> int:
        """Get number of pages."""
        return len(self.pages)

    def __getitem__(self, index: int) -> Page:
        """Get page by index."""
        return self.pages[index]


def _infer_typography_role(size: float, all_sizes: List[float], position: int) -> str:
    """Infer the likely role of a font size in the document hierarchy."""
    if position == 0 and size >= 18:
        return "main_title"
    elif position == 0:
        return "title"
    elif position == 1 and size >= 14:
        return "section_header"
    elif position <= 2 and size >= 12:
        return "subsection_header"
    elif size <= 10:
        return "caption_or_footnote"
    else:
        return "body_text"