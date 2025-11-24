"""
Markdown exporter for spatial-aware document structures.

Converts our Document model to clean markdown while preserving
spatial relationships and document structure.
"""

from typing import List, Dict, Any, Optional
import re
from io import StringIO

from ..core.document import Document, Page, Block, Word, ElementType
from ..core.bbox import BBox


class MarkdownExporter:
    """
    Export Document structure to markdown format.

    Handles hierarchical structure, tables, and maintains reading order
    based on spatial analysis.
    """

    def __init__(
        self,
        preserve_columns: bool = True,
        table_detection: bool = True,
        include_metadata: bool = False,
        max_line_length: int = None,
        heading_style: str = "atx"  # "atx" (#) or "setext" (===)
    ):
        """
        Initialize markdown exporter.

        Args:
            preserve_columns: Maintain column structure in output
            table_detection: Attempt to detect and format tables
            include_metadata: Include document metadata as frontmatter
            max_line_length: Maximum line length for text wrapping
            heading_style: Heading style ("atx" or "setext")
        """
        self.preserve_columns = preserve_columns
        self.table_detection = table_detection
        self.include_metadata = include_metadata
        self.max_line_length = max_line_length
        self.heading_style = heading_style

    def export(self, document: Document) -> str:
        """Export document to markdown string."""
        output = StringIO()

        # Add metadata frontmatter if requested
        if self.include_metadata and document.metadata:
            self._write_frontmatter(output, document.metadata)

        # Process each page
        for page_index, page in enumerate(document.pages):
            if page_index > 0:
                output.write("\n\n---\n\n")  # Page separator

            page_markdown = self._export_page(page)
            output.write(page_markdown)

        return output.getvalue()

    def _write_frontmatter(self, output: StringIO, metadata: Dict[str, Any]) -> None:
        """Write YAML frontmatter with document metadata."""
        output.write("---\n")

        # Include relevant metadata
        relevant_keys = [
            "title", "author", "subject", "creator", "producer",
            "creation_date", "modification_date", "page_count"
        ]

        for key in relevant_keys:
            if key in metadata and metadata[key]:
                value = metadata[key]
                if isinstance(value, str):
                    # Escape quotes in YAML
                    value = value.replace('"', '\\"')
                    output.write(f'{key}: "{value}"\n')
                else:
                    output.write(f'{key}: {value}\n')

        output.write("---\n\n")

    def _export_page(self, page: Page) -> str:
        """Export a single page to markdown."""
        if not page.blocks:
            return ""

        # Sort blocks in reading order if not already done
        sorted_blocks = self._sort_blocks_for_export(page)

        # Group blocks by columns if preserving column structure
        if self.preserve_columns:
            columns = page.detect_columns()
            if len(columns) > 1:
                return self._export_multi_column_page(columns)

        # Regular single-column export
        output = StringIO()
        for block in sorted_blocks:
            block_markdown = self._export_block(block)
            if block_markdown.strip():
                output.write(block_markdown)
                output.write("\n\n")

        return output.getvalue()

    def _sort_blocks_for_export(self, page: Page) -> List[Block]:
        """Sort blocks in optimal reading order."""
        blocks = page.blocks.copy()

        # Sort by reading order (top to bottom, left to right)
        def reading_order_key(block: Block) -> tuple:
            if not block.bbox:
                return (0, 0)
            # Primary: Y coordinate (top to bottom, higher Y first in PDF)
            # Secondary: X coordinate (left to right)
            return (-block.bbox.center_y, block.bbox.center_x)

        blocks.sort(key=reading_order_key)
        return blocks

    def _export_multi_column_page(self, columns: List[List[Block]]) -> str:
        """Export page with multiple columns."""
        output = StringIO()

        # Export each column separately
        for column_index, column_blocks in enumerate(columns):
            if column_index > 0:
                output.write("\n\n<!-- Column Break -->\n\n")

            for block in column_blocks:
                block_markdown = self._export_block(block)
                if block_markdown.strip():
                    output.write(block_markdown)
                    output.write("\n\n")

        return output.getvalue()

    def _export_block(self, block: Block) -> str:
        """Export a single block to markdown."""
        if not block.text.strip():
            return ""

        text = block.text.strip()

        # Handle different element types
        if block.element_type == ElementType.HEADER:
            return self._format_header(text, block)
        elif block.element_type == ElementType.TITLE:
            return self._format_title(text, block)
        elif block.element_type == ElementType.CAPTION:
            return self._format_caption(text, block)
        elif block.element_type == ElementType.CODE:
            return self._format_code(text, block)
        elif block.element_type == ElementType.LIST_ITEM:
            return self._format_list_item(text, block)
        else:
            # Regular paragraph
            return self._format_paragraph(text, block)

    def _format_header(self, text: str, block: Block) -> str:
        """Format text as markdown header."""
        # Determine header level based on font size
        level = self._determine_header_level(block)

        if self.heading_style == "atx":
            return f"{'#' * level} {text}"
        else:  # setext
            if level == 1:
                return f"{text}\n{'=' * len(text)}"
            elif level == 2:
                return f"{text}\n{'-' * len(text)}"
            else:
                # Fall back to atx for level 3+
                return f"{'#' * level} {text}"

    def _format_title(self, text: str, block: Block) -> str:
        """Format text as main title."""
        if self.heading_style == "setext":
            return f"{text}\n{'=' * len(text)}"
        else:
            return f"# {text}"

    def _format_caption(self, text: str, block: Block) -> str:
        """Format text as caption."""
        return f"*{text}*"

    def _format_code(self, text: str, block: Block) -> str:
        """Format text as code block."""
        # Detect if it's inline or block code
        if '\n' in text or len(text) > 60:
            return f"```\n{text}\n```"
        else:
            return f"`{text}`"

    def _format_list_item(self, text: str, block: Block) -> str:
        """Format text as list item."""
        return f"- {text}"

    def _format_paragraph(self, text: str, block: Block) -> str:
        """Format text as regular paragraph."""
        # Apply text wrapping if specified
        if self.max_line_length:
            text = self._wrap_text(text, self.max_line_length)

        # Handle emphasis from font styles
        if block.has_bold and not block.has_italic:
            text = f"**{text}**"
        elif block.has_italic and not block.has_bold:
            text = f"*{text}*"
        elif block.has_bold and block.has_italic:
            text = f"***{text}***"

        return text

    def _determine_header_level(self, block: Block) -> int:
        """Determine appropriate header level based on font characteristics."""
        font = block.dominant_font
        if not font:
            return 2  # Default level

        # Base level on font size
        if font.size >= 24:
            return 1  # Main title
        elif font.size >= 18:
            return 2  # Section header
        elif font.size >= 14:
            return 3  # Subsection
        else:
            return 4  # Sub-subsection

    def _wrap_text(self, text: str, max_length: int) -> str:
        """Wrap text to specified maximum line length."""
        words = text.split()
        if not words:
            return text

        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            # If adding this word would exceed max length, start new line
            if current_length + word_length + len(current_line) > max_length:
                if current_line:  # Don't create empty lines
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Single word longer than max_length
                    lines.append(word)
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)


class TableDetector:
    """
    Detect and format tables from spatial layout and background elements.

    This class analyzes spatial relationships and drawing elements
    to reconstruct table structures that were created visually.
    """

    def __init__(
        self,
        min_rows: int = 2,
        min_columns: int = 2,
        alignment_tolerance: float = 5.0,
        border_tolerance: float = 2.0
    ):
        """
        Initialize table detector.

        Args:
            min_rows: Minimum number of rows to consider as table
            min_columns: Minimum number of columns to consider as table
            alignment_tolerance: Tolerance for column alignment detection
            border_tolerance: Tolerance for border line detection
        """
        self.min_rows = min_rows
        self.min_columns = min_columns
        self.alignment_tolerance = alignment_tolerance
        self.border_tolerance = border_tolerance

    def detect_tables_in_page(self, page: Page) -> List[Dict[str, Any]]:
        """
        Detect tables in a page based on spatial layout and drawings.

        Returns:
            List of table dictionaries with structure and content
        """
        tables = []

        # Method 1: Grid-based detection using drawing elements
        if "drawings" in page.metadata:
            grid_tables = self._detect_tables_from_drawings(page)
            tables.extend(grid_tables)

        # Method 2: Alignment-based detection
        alignment_tables = self._detect_tables_from_alignment(page)
        tables.extend(alignment_tables)

        # Remove duplicates and filter by quality
        tables = self._filter_and_merge_tables(tables)

        return tables

    def _detect_tables_from_drawings(self, page: Page) -> List[Dict[str, Any]]:
        """Detect tables using drawing elements (lines and rectangles)."""
        drawings = page.metadata.get("drawings", [])
        if not drawings:
            return []

        # Separate lines and rectangles
        lines = [d for d in drawings if d["type"] == "line"]
        rectangles = [d for d in drawings if d["type"] == "rectangle"]

        tables = []

        # Look for grid patterns in lines
        if lines:
            grid_tables = self._analyze_line_grid(lines, page.blocks)
            tables.extend(grid_tables)

        # Look for table cells in rectangles
        if rectangles:
            rect_tables = self._analyze_rectangle_cells(rectangles, page.blocks)
            tables.extend(rect_tables)

        return tables

    def _detect_tables_from_alignment(self, page: Page) -> List[Dict[str, Any]]:
        """Detect tables based on text alignment patterns."""
        # Group blocks by approximate Y position (rows)
        y_groups = self._group_blocks_by_y(page.blocks)

        potential_tables = []

        for y_group in y_groups:
            if len(y_group) < self.min_columns:
                continue

            # Check if blocks are aligned in columns
            if self._is_tabular_alignment(y_group):
                # Found potential table row
                potential_tables.append(y_group)

        # Group consecutive table rows
        if len(potential_tables) >= self.min_rows:
            return [self._build_table_from_rows(potential_tables)]

        return []

    def _group_blocks_by_y(self, blocks: List[Block]) -> List[List[Block]]:
        """Group blocks by Y coordinate (horizontal alignment)."""
        if not blocks:
            return []

        # Sort blocks by Y coordinate
        sorted_blocks = sorted(
            [b for b in blocks if b.bbox],
            key=lambda b: -b.bbox.center_y
        )

        groups = []
        current_group = [sorted_blocks[0]]

        for block in sorted_blocks[1:]:
            # Check if block is on same horizontal line
            if current_group[0].bbox.horizontally_aligned(
                block.bbox,
                tolerance=self.alignment_tolerance
            ):
                current_group.append(block)
            else:
                groups.append(current_group)
                current_group = [block]

        groups.append(current_group)

        # Sort blocks within each group by X coordinate
        for group in groups:
            group.sort(key=lambda b: b.bbox.center_x)

        return groups

    def _is_tabular_alignment(self, blocks: List[Block]) -> bool:
        """Check if blocks show tabular alignment patterns."""
        if len(blocks) < self.min_columns:
            return False

        # Check for consistent spacing
        x_positions = [b.bbox.center_x for b in blocks]
        spacings = [x_positions[i + 1] - x_positions[i] for i in range(len(x_positions) - 1)]

        # Look for relatively consistent column widths
        if spacings:
            avg_spacing = sum(spacings) / len(spacings)
            consistent_spacing = all(
                abs(spacing - avg_spacing) < avg_spacing * 0.5
                for spacing in spacings
            )
            return consistent_spacing

        return False

    def _analyze_line_grid(self, lines: List[Dict], blocks: List[Block]) -> List[Dict[str, Any]]:
        """Analyze line patterns to detect table grids."""
        # Extract horizontal and vertical lines
        horizontal_lines = []
        vertical_lines = []

        for line in lines:
            bbox_dict = line["bbox"]
            bbox = BBox.from_dict(bbox_dict)

            if bbox.is_horizontal_line():
                horizontal_lines.append(bbox)
            elif bbox.is_vertical_line():
                vertical_lines.append(bbox)

        # Find intersecting grid pattern
        if len(horizontal_lines) >= 2 and len(vertical_lines) >= 2:
            return [self._build_table_from_grid(horizontal_lines, vertical_lines, blocks)]

        return []

    def _analyze_rectangle_cells(self, rectangles: List[Dict], blocks: List[Block]) -> List[Dict[str, Any]]:
        """Analyze rectangle patterns to detect table cells."""
        # Convert rectangles to bboxes
        rect_bboxes = [BBox.from_dict(r["bbox"]) for r in rectangles]

        # Look for rectangular grid pattern
        # Group rectangles by rows and columns
        y_groups = {}
        x_groups = {}

        for rect in rect_bboxes:
            # Group by Y position (rows)
            y_key = round(rect.center_y / self.alignment_tolerance) * self.alignment_tolerance
            if y_key not in y_groups:
                y_groups[y_key] = []
            y_groups[y_key].append(rect)

            # Group by X position (columns)
            x_key = round(rect.center_x / self.alignment_tolerance) * self.alignment_tolerance
            if x_key not in x_groups:
                x_groups[x_key] = []
            x_groups[x_key].append(rect)

        # Check if we have enough rows and columns
        if len(y_groups) >= self.min_rows and len(x_groups) >= self.min_columns:
            return [self._build_table_from_rectangles(rect_bboxes, blocks)]

        return []

    def _build_table_from_grid(
        self,
        h_lines: List[BBox],
        v_lines: List[BBox],
        blocks: List[Block]
    ) -> Dict[str, Any]:
        """Build table structure from grid lines."""
        # Sort lines
        h_lines.sort(key=lambda l: l.center_y, reverse=True)  # Top to bottom
        v_lines.sort(key=lambda l: l.center_x)  # Left to right

        # Create grid cells
        rows = []
        for i in range(len(h_lines) - 1):
            row = []
            for j in range(len(v_lines) - 1):
                # Define cell boundaries
                cell_bbox = BBox(
                    v_lines[j].center_x,
                    h_lines[i + 1].center_y,
                    v_lines[j + 1].center_x,
                    h_lines[i].center_y
                )

                # Find text blocks in this cell
                cell_text = self._extract_text_from_bbox(cell_bbox, blocks)
                row.append(cell_text)

            rows.append(row)

        return {
            "type": "table",
            "rows": rows,
            "source": "grid_lines",
            "confidence": 0.9
        }

    def _build_table_from_rectangles(
        self,
        rectangles: List[BBox],
        blocks: List[Block]
    ) -> Dict[str, Any]:
        """Build table structure from rectangle cells."""
        # Sort rectangles into grid
        rectangles.sort(key=lambda r: (-r.center_y, r.center_x))

        # Group into rows
        rows = []
        current_row = []
        current_y = None

        for rect in rectangles:
            if current_y is None:
                current_y = rect.center_y
                current_row = [rect]
            elif abs(rect.center_y - current_y) <= self.alignment_tolerance:
                current_row.append(rect)
            else:
                # Sort current row by X position
                current_row.sort(key=lambda r: r.center_x)
                rows.append(current_row)
                current_row = [rect]
                current_y = rect.center_y

        if current_row:
            current_row.sort(key=lambda r: r.center_x)
            rows.append(current_row)

        # Extract text from each cell
        table_rows = []
        for row_rects in rows:
            table_row = []
            for rect in row_rects:
                cell_text = self._extract_text_from_bbox(rect, blocks)
                table_row.append(cell_text)
            table_rows.append(table_row)

        return {
            "type": "table",
            "rows": table_rows,
            "source": "rectangles",
            "confidence": 0.8
        }

    def _build_table_from_rows(self, row_groups: List[List[Block]]) -> Dict[str, Any]:
        """Build table from aligned text rows."""
        # Determine column positions from all rows
        all_x_positions = []
        for row in row_groups:
            for block in row:
                all_x_positions.append(block.bbox.center_x)

        # Cluster X positions to find column boundaries
        column_positions = self._cluster_positions(all_x_positions)

        # Build table rows
        table_rows = []
        for row_blocks in row_groups:
            table_row = [""] * len(column_positions)

            for block in row_blocks:
                # Find which column this block belongs to
                col_index = self._find_column_index(block.bbox.center_x, column_positions)
                if 0 <= col_index < len(table_row):
                    if table_row[col_index]:
                        table_row[col_index] += " " + block.text
                    else:
                        table_row[col_index] = block.text

            table_rows.append(table_row)

        return {
            "type": "table",
            "rows": table_rows,
            "source": "alignment",
            "confidence": 0.7
        }

    def _extract_text_from_bbox(self, bbox: BBox, blocks: List[Block]) -> str:
        """Extract text from blocks that overlap with given bbox."""
        text_parts = []

        for block in blocks:
            if not block.bbox:
                continue

            # Check if block overlaps with cell
            if block.bbox.overlaps(bbox):
                text_parts.append(block.text)

        return " ".join(text_parts).strip()

    def _cluster_positions(self, positions: List[float]) -> List[float]:
        """Cluster similar positions to find column boundaries."""
        if not positions:
            return []

        sorted_positions = sorted(set(positions))
        clusters = [sorted_positions[0]]

        for pos in sorted_positions[1:]:
            # If position is close to last cluster center, merge
            if abs(pos - clusters[-1]) <= self.alignment_tolerance:
                clusters[-1] = (clusters[-1] + pos) / 2  # Average
            else:
                clusters.append(pos)

        return clusters

    def _find_column_index(self, x_position: float, column_positions: List[float]) -> int:
        """Find which column a position belongs to."""
        for i, col_pos in enumerate(column_positions):
            if abs(x_position - col_pos) <= self.alignment_tolerance:
                return i
        return -1  # Not found

    def _filter_and_merge_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out low-quality tables and merge overlapping ones."""
        if not tables:
            return []

        # Sort by confidence
        tables.sort(key=lambda t: t.get("confidence", 0), reverse=True)

        # Filter by minimum quality
        filtered_tables = [t for t in tables if t.get("confidence", 0) >= 0.5]

        # TODO: Implement table merging for overlapping detections

        return filtered_tables


def export_to_markdown(document: Document, **kwargs) -> str:
    """
    Convenience function to export document to markdown.

    Args:
        document: Document to export
        **kwargs: Additional arguments passed to MarkdownExporter

    Returns:
        Markdown string
    """
    exporter = MarkdownExporter(**kwargs)
    return exporter.export(document)