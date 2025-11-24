"""
PDF loader using PyMuPDF for spatial-aware text extraction.

This module handles the conversion from PyMuPDF's raw data structures
to our spatial document model, preserving all bbox coordinates and
handling common MS Office PDF artifacts.
"""

import fitz  # PyMuPDF
from typing import Union, List, Dict, Any, Optional, Tuple, BinaryIO
from pathlib import Path
import logging

from ..core.document import Document, Page, Block, Word, FontInfo, FontStyle, ElementType
from ..core.bbox import BBox
from ..core.exceptions import PDFLoadError, QualityError


logger = logging.getLogger(__name__)


class PDFLoader:
    """
    Load PDFs using PyMuPDF and convert to spatial document structure.

    Handles various PDF formats and quality issues, with special attention
    to MS Office generated PDFs that have fragmented text and poor structure.
    """

    def __init__(
        self,
        merge_tolerance: float = 2.0,
        min_font_size: float = 4.0,
        max_font_size: float = 72.0,
        skip_invisible_text: bool = True,
        extract_images: bool = False,
        extract_drawings: bool = True
    ):
        """
        Initialize PDF loader with configuration.

        Args:
            merge_tolerance: Distance threshold for merging adjacent text fragments
            min_font_size: Minimum font size to consider (filters noise)
            max_font_size: Maximum font size to consider
            skip_invisible_text: Skip text with zero-size bboxes
            extract_images: Whether to extract image information
            extract_drawings: Whether to extract drawing/shape information
        """
        self.merge_tolerance = merge_tolerance
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size
        self.skip_invisible_text = skip_invisible_text
        self.extract_images = extract_images
        self.extract_drawings = extract_drawings

    def load(self, source: Union[str, Path, bytes, BinaryIO]) -> Document:
        """
        Load PDF from various sources and return Document.

        Args:
            source: PDF file path, bytes, or file-like object

        Returns:
            Document with spatial structure

        Raises:
            PDFLoadError: If PDF cannot be loaded or is corrupted
            QualityError: If PDF quality is too poor to process
        """
        try:
            # Handle different source types
            if isinstance(source, (str, Path)):
                source_path = str(source)
                doc = fitz.open(source_path)
            elif isinstance(source, bytes):
                source_path = None
                doc = fitz.open(stream=source, filetype="pdf")
            elif hasattr(source, 'read'):
                source_path = getattr(source, 'name', None)
                data = source.read()
                doc = fitz.open(stream=data, filetype="pdf")
            else:
                raise PDFLoadError("Unsupported source type", error_details=f"Type: {type(source)}")

            # Extract document metadata
            metadata = self._extract_metadata(doc)

            # Check document quality
            self._assess_quality(doc, metadata)

            # Convert pages
            pages = []
            for page_num in range(len(doc)):
                try:
                    page = self._convert_page(doc[page_num], page_num)
                    pages.append(page)
                except Exception as e:
                    logger.warning(f"Failed to process page {page_num}: {e}")
                    # Continue with other pages

            doc.close()

            if not pages:
                raise PDFLoadError("No pages could be processed")

            return Document(
                pages=pages,
                metadata=metadata,
                source_path=source_path
            )

        except fitz.FileDataError as e:
            raise PDFLoadError("Invalid or corrupted PDF file", error_details=str(e))
        except fitz.FileNotFoundError as e:
            raise PDFLoadError("PDF file not found", pdf_path=str(source), error_details=str(e))
        except Exception as e:
            raise PDFLoadError(f"Unexpected error loading PDF: {e}", error_details=str(e))

    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract document metadata from PyMuPDF document."""
        metadata = doc.metadata.copy() if doc.metadata else {}

        # Add technical information
        metadata.update({
            "page_count": len(doc),
            "needs_password": doc.needs_pass,
            "is_encrypted": doc.is_encrypted,
            "is_pdf": doc.is_pdf,
            "pdf_version": getattr(doc, 'pdf_version', None),
            "loader_config": {
                "merge_tolerance": self.merge_tolerance,
                "min_font_size": self.min_font_size,
                "max_font_size": self.max_font_size,
                "skip_invisible_text": self.skip_invisible_text,
                "extract_images": self.extract_images,
                "extract_drawings": self.extract_drawings
            }
        })

        return metadata

    def _assess_quality(self, doc: fitz.Document, metadata: Dict[str, Any]) -> None:
        """
        Assess PDF quality and raise QualityError if too poor.

        Checks for common issues that make PDFs difficult to process.
        """
        issues = []
        quality_score = 1.0

        # Check for password protection
        if doc.needs_pass:
            issues.append("Password protected")
            quality_score *= 0.0  # Cannot process

        # Check for very large documents (potential performance issues)
        if len(doc) > 1000:
            issues.append(f"Very large document ({len(doc)} pages)")
            quality_score *= 0.8

        # Sample first few pages for quality assessment
        sample_pages = min(3, len(doc))
        total_text_blocks = 0
        total_drawings = 0
        empty_pages = 0

        for page_num in range(sample_pages):
            try:
                page = doc[page_num]

                # Check for text content
                text_dict = page.get_text("dict")
                page_blocks = len(text_dict.get("blocks", []))
                total_text_blocks += page_blocks

                if page_blocks == 0:
                    empty_pages += 1

                # Check for drawings/graphics
                if self.extract_drawings:
                    drawings = page.get_drawings()
                    total_drawings += len(drawings)

            except Exception as e:
                issues.append(f"Error sampling page {page_num}: {e}")
                quality_score *= 0.9

        # Quality assessment
        if empty_pages == sample_pages:
            issues.append("No text content found")
            quality_score *= 0.2

        avg_blocks_per_page = total_text_blocks / sample_pages if sample_pages > 0 else 0
        if avg_blocks_per_page > 500:
            issues.append("Extremely fragmented text (possible OCR)")
            quality_score *= 0.7

        # Check producer for known problematic generators
        producer = metadata.get("producer", "").lower()
        if any(term in producer for term in ["microsoft", "excel", "word", "powerpoint"]):
            issues.append("MS Office generated (may have artifacts)")
            quality_score *= 0.8

        # Log assessment results
        logger.info(f"PDF quality assessment: score={quality_score:.2f}, issues={len(issues)}")

        # Raise error if quality is too poor
        if quality_score < 0.1:
            raise QualityError(
                f"PDF quality too poor to process (score: {quality_score:.2f})",
                quality_score=quality_score,
                issues=issues
            )

        # Store quality info in metadata
        metadata["quality_assessment"] = {
            "score": quality_score,
            "issues": issues,
            "avg_blocks_per_page": avg_blocks_per_page,
            "total_drawings": total_drawings,
            "empty_pages": empty_pages
        }

    def _convert_page(self, fitz_page: fitz.Page, page_number: int) -> Page:
        """Convert PyMuPDF page to our Page structure."""
        # Get page dimensions
        page_rect = fitz_page.rect
        page_bbox = BBox(page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1)

        # Extract text with detailed formatting
        text_dict = fitz_page.get_text("dict")

        # Convert text blocks to our structure
        blocks = self._convert_text_blocks(text_dict.get("blocks", []))

        # Extract additional elements if requested
        page_metadata = {
            "page_number": page_number,
            "dimensions": {
                "width": page_rect.width,
                "height": page_rect.height
            }
        }

        if self.extract_drawings:
            drawings = fitz_page.get_drawings()
            page_metadata["drawings"] = self._process_drawings(drawings)

        if self.extract_images:
            image_list = fitz_page.get_images()
            page_metadata["images"] = self._process_images(image_list, fitz_page)

        return Page(
            number=page_number,
            blocks=blocks,
            page_bbox=page_bbox,
            metadata=page_metadata
        )

    def _convert_text_blocks(self, fitz_blocks: List[Dict]) -> List[Block]:
        """Convert PyMuPDF text blocks to our Block structure."""
        blocks = []

        for block_dict in fitz_blocks:
            # Skip non-text blocks (images, etc.)
            if block_dict.get("type") != 0:  # 0 = text block
                continue

            # Extract lines from block
            lines = block_dict.get("lines", [])
            if not lines:
                continue

            # Convert lines to words
            words = []
            for line in lines:
                line_words = self._convert_line_to_words(line)
                words.extend(line_words)

            if words:
                # Create block from words
                block = Block(words=words, element_type=ElementType.TEXT)
                blocks.append(block)

        # Apply post-processing
        blocks = self._merge_fragmented_blocks(blocks)
        blocks = self._classify_blocks(blocks)

        return blocks

    def _convert_line_to_words(self, line_dict: Dict) -> List[Word]:
        """Convert PyMuPDF line to our Word structures."""
        words = []

        spans = line_dict.get("spans", [])
        for span in spans:
            # Extract font information
            font_info = self._extract_font_info(span)

            # Extract text and bbox
            text = span.get("text", "").strip()
            if not text:
                continue

            bbox_coords = span.get("bbox")
            if not bbox_coords or len(bbox_coords) != 4:
                continue

            bbox = BBox.from_tuple(bbox_coords)

            # Filter by size and visibility
            if self._should_skip_span(span, bbox, font_info):
                continue

            # Split span into individual words if needed
            # This helps with spatial analysis
            word_texts = text.split()
            if len(word_texts) <= 1:
                # Single word or no spaces
                words.append(Word(
                    text=text,
                    bbox=bbox,
                    font=font_info,
                    confidence=1.0,
                    element_type=ElementType.TEXT
                ))
            else:
                # Multiple words - estimate positions
                word_objs = self._split_span_into_words(text, bbox, font_info)
                words.extend(word_objs)

        return words

    def _extract_font_info(self, span: Dict) -> FontInfo:
        """Extract font information from PyMuPDF span."""
        font_name = span.get("font", "Unknown")
        font_size = span.get("size", 12.0)
        font_flags = span.get("flags", 0)

        # Decode font style from flags
        # PyMuPDF font flags: https://pymupdf.readthedocs.io/en/latest/page.html#span-dictionary
        is_bold = bool(font_flags & 2**4)  # bit 4
        is_italic = bool(font_flags & 2**1)  # bit 1

        if is_bold and is_italic:
            style = FontStyle.BOLD_ITALIC
        elif is_bold:
            style = FontStyle.BOLD
        elif is_italic:
            style = FontStyle.ITALIC
        else:
            style = FontStyle.NORMAL

        # Extract color if available
        color = span.get("color")
        color_hex = None
        if color is not None:
            # Convert color to hex format
            color_hex = f"#{color:06x}"

        return FontInfo(
            name=font_name,
            size=font_size,
            style=style,
            color=color_hex
        )

    def _should_skip_span(self, span: Dict, bbox: BBox, font_info: FontInfo) -> bool:
        """Determine if a span should be skipped based on quality filters."""
        # Skip invisible text
        if self.skip_invisible_text and (bbox.width == 0 or bbox.height == 0):
            return True

        # Skip very small or very large fonts
        if (font_info.size < self.min_font_size or
            font_info.size > self.max_font_size):
            return True

        # Skip if bbox is malformed
        if bbox.x0 >= bbox.x1 or bbox.y0 >= bbox.y1:
            return True

        return False

    def _split_span_into_words(self, text: str, span_bbox: BBox, font_info: FontInfo) -> List[Word]:
        """
        Split a multi-word span into individual words with estimated positions.

        This is necessary because PyMuPDF sometimes groups multiple words
        into a single span, but we need word-level granularity for spatial analysis.
        """
        words = []
        word_texts = text.split()

        if not word_texts:
            return words

        # Estimate character width
        char_width = span_bbox.width / len(text) if len(text) > 0 else 0

        current_x = span_bbox.x0
        for word_text in word_texts:
            # Estimate word width
            word_width = char_width * len(word_text)

            # Create bbox for this word
            word_bbox = BBox(
                current_x,
                span_bbox.y0,
                current_x + word_width,
                span_bbox.y1
            )

            words.append(Word(
                text=word_text,
                bbox=word_bbox,
                font=font_info,
                confidence=0.9,  # Slightly lower confidence for estimated positions
                element_type=ElementType.TEXT
            ))

            # Move to next position (word + space)
            current_x += word_width + char_width

        return words

    def _merge_fragmented_blocks(self, blocks: List[Block]) -> List[Block]:
        """
        Merge adjacent blocks that were artificially fragmented.

        This is especially important for MS Office PDFs which often
        split text unnecessarily.
        """
        if not blocks:
            return blocks

        merged_blocks = []
        current_block = blocks[0]

        for next_block in blocks[1:]:
            # Check if blocks should be merged
            if self._should_merge_blocks(current_block, next_block):
                # Merge next block into current
                current_block = current_block.merge_with(next_block)
            else:
                # Keep current block and start new one
                merged_blocks.append(current_block)
                current_block = next_block

        merged_blocks.append(current_block)
        return merged_blocks

    def _should_merge_blocks(self, block1: Block, block2: Block) -> bool:
        """Determine if two blocks should be merged."""
        bbox1 = block1.bbox
        bbox2 = block2.bbox

        if not bbox1 or not bbox2:
            return False

        # Check if blocks are on the same line
        if not bbox1.same_line(bbox2, tolerance=self.merge_tolerance):
            return False

        # Check if blocks are close horizontally
        horizontal_gap = bbox1.horizontal_distance(bbox2)
        if horizontal_gap > self.merge_tolerance * 3:
            return False

        # Check if fonts are compatible
        font1 = block1.dominant_font
        font2 = block2.dominant_font

        if font1 and font2:
            # Allow merging if fonts are very similar
            size_diff = abs(font1.size - font2.size)
            if size_diff > 1.0 or font1.style != font2.style:
                return False

        return True

    def _classify_blocks(self, blocks: List[Block]) -> List[Block]:
        """Classify blocks based on typography and position."""
        for block in blocks:
            # Update element type based on heuristics
            if block.is_likely_header():
                block.element_type = ElementType.HEADER
            elif block.is_likely_caption():
                block.element_type = ElementType.CAPTION
            # Keep default PARAGRAPH/TEXT for others

        return blocks

    def _process_drawings(self, drawings: List[Dict]) -> List[Dict[str, Any]]:
        """Process drawing elements for table detection."""
        processed = []

        for drawing in drawings:
            # Extract relevant drawing information
            items = drawing.get("items", [])
            for item in items:
                if item[0] == "re":  # Rectangle
                    # Rectangle coordinates: (x0, y0, x1, y1)
                    rect_data = item[1]
                    if len(rect_data) >= 4:
                        processed.append({
                            "type": "rectangle",
                            "bbox": BBox.from_tuple(rect_data[:4]).to_dict(),
                            "stroke": drawing.get("stroke", {}),
                            "fill": drawing.get("fill", {}),
                            "width": drawing.get("width", 0)
                        })
                elif item[0] == "l":  # Line
                    # Line coordinates: (x0, y0, x1, y1)
                    line_data = item[1]
                    if len(line_data) >= 4:
                        processed.append({
                            "type": "line",
                            "bbox": BBox.from_tuple(line_data[:4]).to_dict(),
                            "stroke": drawing.get("stroke", {}),
                            "width": drawing.get("width", 0)
                        })

        return processed

    def _process_images(self, image_list: List, fitz_page: fitz.Page) -> List[Dict[str, Any]]:
        """Process image information."""
        processed = []

        for img_index, img in enumerate(image_list):
            try:
                # Get image bbox
                img_rect = fitz_page.get_image_bbox(img[7])  # img[7] is the xref

                processed.append({
                    "index": img_index,
                    "bbox": BBox.from_tuple(img_rect).to_dict(),
                    "width": img[2],
                    "height": img[3],
                    "colorspace": img[4],
                    "bpc": img[5],  # bits per component
                    "xref": img[7]
                })
            except Exception as e:
                logger.warning(f"Failed to process image {img_index}: {e}")

        return processed


def load_pdf(source: Union[str, Path, bytes, BinaryIO], **kwargs) -> Document:
    """
    Convenience function to load a PDF with default settings.

    Args:
        source: PDF file path, bytes, or file-like object
        **kwargs: Additional arguments passed to PDFLoader

    Returns:
        Document with spatial structure
    """
    loader = PDFLoader(**kwargs)
    return loader.load(source)