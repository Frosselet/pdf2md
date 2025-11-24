"""Core spatial data structures and operations."""

from .bbox import BBox
from .document import Document, Page, Block, Word
from .exceptions import PDF2MDError, QualityError, SpatialAnalysisError

__all__ = [
    "BBox",
    "Document",
    "Page",
    "Block",
    "Word",
    "PDF2MDError",
    "QualityError",
    "SpatialAnalysisError",
]