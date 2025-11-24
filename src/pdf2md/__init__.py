"""
PDF2MD: Spatial-aware PDF to Markdown conversion using PyMuPDF.

A pure-engineering approach to PDF→Markdown conversion that preserves spatial
relationships and document structure through intelligent bbox analysis and
typography heuristics.
"""

# from .api import convert_pdf, PDFConverter  # TODO: implement
from .core.document import Document, Page, Block, Word
from .core.bbox import BBox

__version__ = "0.1.0"
__author__ = "François Rosselet"
__email__ = "francois@example.com"

__all__ = [
    # "convert_pdf",  # TODO: implement
    # "PDFConverter",  # TODO: implement
    "Document",
    "Page",
    "Block",
    "Word",
    "BBox",
]