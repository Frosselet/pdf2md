"""
Main API interface for PDF2MD library.

Provides simple functions for converting PDFs to markdown while
leveraging spatial-aware analysis for superior quality.
"""

from typing import Union, Optional, BinaryIO
from pathlib import Path

from .core.document import Document
from .io.loader import PDFLoader, load_pdf
from .io.exporter import MarkdownExporter, export_to_markdown


class PDFConverter:
    """
    High-level interface for PDF to Markdown conversion.

    Combines PDF loading, spatial analysis, and markdown generation
    with intelligent defaults for high-quality output.
    """

    def __init__(
        self,
        # Loader options
        merge_tolerance: float = 2.0,
        min_font_size: float = 4.0,
        max_font_size: float = 72.0,
        skip_invisible_text: bool = True,
        extract_images: bool = False,
        extract_drawings: bool = True,
        # Exporter options
        preserve_columns: bool = True,
        table_detection: bool = True,
        include_metadata: bool = False,
        max_line_length: Optional[int] = None,
        heading_style: str = "atx"
    ):
        """
        Initialize PDF converter with configuration options.

        Args:
            # PDF Loading options
            merge_tolerance: Distance threshold for merging fragmented text
            min_font_size: Minimum font size to consider (filters noise)
            max_font_size: Maximum font size to consider
            skip_invisible_text: Skip zero-size text elements
            extract_images: Extract image information
            extract_drawings: Extract drawing/shape information for tables

            # Markdown Export options
            preserve_columns: Maintain column structure in output
            table_detection: Attempt to detect and format tables
            include_metadata: Include document metadata as frontmatter
            max_line_length: Maximum line length for text wrapping
            heading_style: Heading style ("atx" for # or "setext" for ===)
        """
        self.loader = PDFLoader(
            merge_tolerance=merge_tolerance,
            min_font_size=min_font_size,
            max_font_size=max_font_size,
            skip_invisible_text=skip_invisible_text,
            extract_images=extract_images,
            extract_drawings=extract_drawings
        )

        self.exporter = MarkdownExporter(
            preserve_columns=preserve_columns,
            table_detection=table_detection,
            include_metadata=include_metadata,
            max_line_length=max_line_length,
            heading_style=heading_style
        )

    def convert(self, source: Union[str, Path, bytes, BinaryIO]) -> str:
        """
        Convert PDF to markdown string.

        Args:
            source: PDF file path, bytes, or file-like object

        Returns:
            Markdown string with preserved spatial structure

        Raises:
            PDFLoadError: If PDF cannot be loaded
            QualityError: If PDF quality is too poor to process
        """
        # Load PDF with spatial analysis
        document = self.loader.load(source)

        # Convert to markdown
        markdown = self.exporter.export(document)

        return markdown

    def convert_to_document(self, source: Union[str, Path, bytes, BinaryIO]) -> Document:
        """
        Convert PDF to Document object for further analysis.

        Args:
            source: PDF file path, bytes, or file-like object

        Returns:
            Document with spatial structure
        """
        return self.loader.load(source)

    def document_to_markdown(self, document: Document) -> str:
        """
        Convert Document object to markdown string.

        Args:
            document: Document with spatial structure

        Returns:
            Markdown string
        """
        return self.exporter.export(document)


def convert_pdf(
    source: Union[str, Path, bytes, BinaryIO],
    **kwargs
) -> str:
    """
    Convert PDF to markdown with default settings.

    This is the main convenience function for simple PDF to markdown conversion.
    For more control over the conversion process, use PDFConverter class.

    Args:
        source: PDF file path, bytes, or file-like object
        **kwargs: Additional options passed to PDFConverter

    Returns:
        Markdown string with preserved spatial structure

    Examples:
        # Convert file by path
        markdown = convert_pdf("document.pdf")

        # Convert with custom options
        markdown = convert_pdf(
            "document.pdf",
            preserve_columns=False,
            include_metadata=True
        )

        # Convert from bytes
        with open("document.pdf", "rb") as f:
            markdown = convert_pdf(f.read())
    """
    converter = PDFConverter(**kwargs)
    return converter.convert(source)


def analyze_pdf_structure(
    source: Union[str, Path, bytes, BinaryIO],
    **kwargs
) -> Document:
    """
    Analyze PDF structure without converting to markdown.

    Returns the spatial document structure for inspection or further processing.

    Args:
        source: PDF file path, bytes, or file-like object
        **kwargs: Additional options passed to PDFLoader

    Returns:
        Document with spatial structure

    Examples:
        # Analyze document structure
        doc = analyze_pdf_structure("document.pdf")

        # Inspect pages and blocks
        for page in doc.pages:
            print(f"Page {page.number}: {page.block_count} blocks")
            columns = page.detect_columns()
            print(f"Detected {len(columns)} columns")

        # Check typography hierarchy
        hierarchy = doc.analyze_typography_hierarchy()
        print("Font hierarchy:", hierarchy)
    """
    loader = PDFLoader(**kwargs)
    return loader.load(source)