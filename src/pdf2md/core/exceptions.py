"""
Custom exceptions for the PDF2MD library.

These exceptions provide specific error types for different failure modes
in the PDF to Markdown conversion process.
"""


class PDF2MDError(Exception):
    """Base exception for all PDF2MD library errors."""
    pass


class QualityError(PDF2MDError):
    """Raised when PDF quality assessment fails or quality is too poor to process."""

    def __init__(self, message: str, quality_score: float = None, issues: list = None):
        super().__init__(message)
        self.quality_score = quality_score
        self.issues = issues or []


class SpatialAnalysisError(PDF2MDError):
    """Raised when spatial analysis or layout detection fails."""

    def __init__(self, message: str, page_number: int = None, bbox_count: int = None):
        super().__init__(message)
        self.page_number = page_number
        self.bbox_count = bbox_count


class PDFLoadError(PDF2MDError):
    """Raised when PDF cannot be loaded or is corrupted."""

    def __init__(self, message: str, pdf_path: str = None, error_details: str = None):
        super().__init__(message)
        self.pdf_path = pdf_path
        self.error_details = error_details


class SanitizationError(PDF2MDError):
    """Raised when PDF sanitization fails."""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class MarkdownGenerationError(PDF2MDError):
    """Raised when markdown generation fails."""

    def __init__(self, message: str, page_number: int = None, element_count: int = None):
        super().__init__(message)
        self.page_number = page_number
        self.element_count = element_count


class TypographyAnalysisError(PDF2MDError):
    """Raised when typography analysis fails to detect document structure."""

    def __init__(self, message: str, font_count: int = None, size_variations: int = None):
        super().__init__(message)
        self.font_count = font_count
        self.size_variations = size_variations


class TableDetectionError(PDF2MDError):
    """Raised when table detection or reconstruction fails."""

    def __init__(self, message: str, drawing_count: int = None, text_blocks: int = None):
        super().__init__(message)
        self.drawing_count = drawing_count
        self.text_blocks = text_blocks


class ColumnDetectionError(SpatialAnalysisError):
    """Raised when column detection fails."""

    def __init__(self, message: str, detected_columns: int = None, x_positions: list = None):
        super().__init__(message)
        self.detected_columns = detected_columns
        self.x_positions = x_positions or []