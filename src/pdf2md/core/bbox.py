"""
BBox: Bounding box operations and spatial utilities.

This module provides the fundamental spatial primitive for the PDF2MD library.
Every text element, shape, and layout component has a bounding box that defines
its position and size in the 2D document space.
"""

from typing import Tuple, List, Optional, Union
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BBox:
    """
    Immutable bounding box representing a rectangle in 2D space.

    Uses PDF coordinate system where (0,0) is bottom-left of page.

    Attributes:
        x0: Left edge (minimum X coordinate)
        y0: Bottom edge (minimum Y coordinate)
        x1: Right edge (maximum X coordinate)
        y1: Top edge (maximum Y coordinate)
    """
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        """Validate bbox coordinates."""
        if self.x0 > self.x1:
            raise ValueError(f"x0 ({self.x0}) must be <= x1 ({self.x1})")
        if self.y0 > self.y1:
            raise ValueError(f"y0 ({self.y0}) must be <= y1 ({self.y1})")

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float, float, float]) -> "BBox":
        """Create BBox from (x0, y0, x1, y1) tuple."""
        return cls(*coords)

    @classmethod
    def from_dict(cls, data: dict) -> "BBox":
        """Create BBox from dictionary with x0, y0, x1, y1 keys."""
        return cls(data["x0"], data["y0"], data["x1"], data["y1"])

    @classmethod
    def from_corners(cls, left: float, bottom: float, right: float, top: float) -> "BBox":
        """Create BBox from corner coordinates (alias for main constructor)."""
        return cls(left, bottom, right, top)

    @classmethod
    def from_center_size(cls, center_x: float, center_y: float, width: float, height: float) -> "BBox":
        """Create BBox from center point and dimensions."""
        half_width = width / 2
        half_height = height / 2
        return cls(
            center_x - half_width,
            center_y - half_height,
            center_x + half_width,
            center_y + half_height
        )

    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        """Area of the bounding box."""
        return self.width * self.height

    @property
    def center_x(self) -> float:
        """X coordinate of the center point."""
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        """Y coordinate of the center point."""
        return (self.y0 + self.y1) / 2

    @property
    def center(self) -> Tuple[float, float]:
        """Center point as (x, y) tuple."""
        return (self.center_x, self.center_y)

    @property
    def top_left(self) -> Tuple[float, float]:
        """Top-left corner coordinates."""
        return (self.x0, self.y1)

    @property
    def top_right(self) -> Tuple[float, float]:
        """Top-right corner coordinates."""
        return (self.x1, self.y1)

    @property
    def bottom_left(self) -> Tuple[float, float]:
        """Bottom-left corner coordinates."""
        return (self.x0, self.y0)

    @property
    def bottom_right(self) -> Tuple[float, float]:
        """Bottom-right corner coordinates."""
        return (self.x1, self.y0)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to (x0, y0, x1, y1) tuple."""
        return (self.x0, self.y0, self.x1, self.y1)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}

    # Spatial relationship methods

    def overlaps(self, other: "BBox", tolerance: float = 0.0) -> bool:
        """
        Check if this bbox overlaps with another.

        Args:
            other: Another bounding box
            tolerance: Minimum overlap distance to consider as overlap

        Returns:
            True if bboxes overlap by at least tolerance distance
        """
        return (
            self.x0 <= other.x1 + tolerance and
            self.x1 >= other.x0 - tolerance and
            self.y0 <= other.y1 + tolerance and
            self.y1 >= other.y0 - tolerance
        )

    def contains_point(self, x: float, y: float, tolerance: float = 0.0) -> bool:
        """Check if bbox contains the given point."""
        return (
            self.x0 - tolerance <= x <= self.x1 + tolerance and
            self.y0 - tolerance <= y <= self.y1 + tolerance
        )

    def contains_bbox(self, other: "BBox", tolerance: float = 0.0) -> bool:
        """Check if this bbox completely contains another bbox."""
        return (
            self.x0 - tolerance <= other.x0 and
            self.y0 - tolerance <= other.y0 and
            self.x1 + tolerance >= other.x1 and
            self.y1 + tolerance >= other.y1
        )

    def intersection(self, other: "BBox") -> Optional["BBox"]:
        """
        Calculate intersection bbox with another bbox.

        Returns:
            BBox of intersection area, or None if no intersection
        """
        x0 = max(self.x0, other.x0)
        y0 = max(self.y0, other.y0)
        x1 = min(self.x1, other.x1)
        y1 = min(self.y1, other.y1)

        if x0 <= x1 and y0 <= y1:
            return BBox(x0, y0, x1, y1)
        return None

    def union(self, other: "BBox") -> "BBox":
        """Calculate union bbox that encompasses both bboxes."""
        return BBox(
            min(self.x0, other.x0),
            min(self.y0, other.y0),
            max(self.x1, other.x1),
            max(self.y1, other.y1)
        )

    def intersection_area(self, other: "BBox") -> float:
        """Calculate area of intersection with another bbox."""
        intersection = self.intersection(other)
        return intersection.area if intersection else 0.0

    def intersection_ratio(self, other: "BBox") -> float:
        """
        Calculate intersection ratio (intersection area / smaller bbox area).

        Returns:
            Ratio from 0.0 (no overlap) to 1.0 (complete overlap of smaller bbox)
        """
        intersection_area = self.intersection_area(other)
        if intersection_area == 0:
            return 0.0

        smaller_area = min(self.area, other.area)
        return intersection_area / smaller_area if smaller_area > 0 else 0.0

    # Distance and proximity methods

    def distance_to_point(self, x: float, y: float) -> float:
        """Calculate minimum distance from bbox to a point."""
        # If point is inside bbox, distance is 0
        if self.contains_point(x, y):
            return 0.0

        # Calculate distance to nearest edge/corner
        dx = max(0, max(self.x0 - x, x - self.x1))
        dy = max(0, max(self.y0 - y, y - self.y1))
        return math.sqrt(dx * dx + dy * dy)

    def distance_to_bbox(self, other: "BBox") -> float:
        """Calculate minimum distance between two bboxes."""
        # If bboxes overlap, distance is 0
        if self.overlaps(other):
            return 0.0

        # Calculate distance between closest points
        dx = max(0, max(self.x0 - other.x1, other.x0 - self.x1))
        dy = max(0, max(self.y0 - other.y1, other.y0 - self.y1))
        return math.sqrt(dx * dx + dy * dy)

    def horizontal_distance(self, other: "BBox") -> float:
        """Calculate horizontal distance between bboxes."""
        return max(0, max(self.x0 - other.x1, other.x0 - self.x1))

    def vertical_distance(self, other: "BBox") -> float:
        """Calculate vertical distance between bboxes."""
        return max(0, max(self.y0 - other.y1, other.y0 - self.y1))

    # Alignment detection methods

    def horizontally_aligned(self, other: "BBox", tolerance: float = 1.0) -> bool:
        """Check if bboxes are horizontally aligned (same Y coordinates)."""
        return (
            abs(self.y0 - other.y0) <= tolerance or
            abs(self.y1 - other.y1) <= tolerance or
            abs(self.center_y - other.center_y) <= tolerance
        )

    def vertically_aligned(self, other: "BBox", tolerance: float = 1.0) -> bool:
        """Check if bboxes are vertically aligned (same X coordinates)."""
        return (
            abs(self.x0 - other.x0) <= tolerance or
            abs(self.x1 - other.x1) <= tolerance or
            abs(self.center_x - other.center_x) <= tolerance
        )

    def same_line(self, other: "BBox", tolerance: float = 2.0) -> bool:
        """
        Check if bboxes are on the same text line.

        Uses more lenient vertical alignment check suitable for text lines.
        """
        # Check if Y-ranges overlap significantly
        y_overlap = max(0, min(self.y1, other.y1) - max(self.y0, other.y0))
        min_height = min(self.height, other.height)

        return y_overlap >= min_height * 0.5 or self.horizontally_aligned(other, tolerance)

    def same_column(self, other: "BBox", tolerance: float = 5.0) -> bool:
        """
        Check if bboxes are in the same column.

        Uses more lenient horizontal alignment check suitable for column detection.
        """
        # Check if X-ranges overlap significantly or are closely aligned
        x_overlap = max(0, min(self.x1, other.x1) - max(self.x0, other.x0))
        return (
            x_overlap > 0 or
            abs(self.x0 - other.x0) <= tolerance or
            abs(self.center_x - other.center_x) <= tolerance
        )

    # Transformation methods

    def translate(self, dx: float, dy: float) -> "BBox":
        """Return new bbox translated by (dx, dy)."""
        return BBox(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def scale(self, scale_x: float, scale_y: float = None) -> "BBox":
        """Return new bbox scaled from center point."""
        if scale_y is None:
            scale_y = scale_x

        center_x, center_y = self.center
        new_width = self.width * scale_x
        new_height = self.height * scale_y

        return BBox.from_center_size(center_x, center_y, new_width, new_height)

    def expand(self, margin: float) -> "BBox":
        """Return new bbox expanded by margin in all directions."""
        return BBox(
            self.x0 - margin,
            self.y0 - margin,
            self.x1 + margin,
            self.y1 + margin
        )

    def expand_to_grid(self, grid_size: float) -> "BBox":
        """Expand bbox to align with grid boundaries."""
        x0 = math.floor(self.x0 / grid_size) * grid_size
        y0 = math.floor(self.y0 / grid_size) * grid_size
        x1 = math.ceil(self.x1 / grid_size) * grid_size
        y1 = math.ceil(self.y1 / grid_size) * grid_size

        return BBox(x0, y0, x1, y1)

    # Utility methods for spatial analysis

    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width / height)."""
        return self.width / self.height if self.height > 0 else float('inf')

    def is_roughly_square(self, tolerance: float = 0.2) -> bool:
        """Check if bbox is roughly square."""
        ratio = self.aspect_ratio()
        return abs(ratio - 1.0) <= tolerance

    def is_horizontal_line(self, max_height: float = 3.0) -> bool:
        """Check if bbox represents a horizontal line (very short height)."""
        return self.height <= max_height and self.width > self.height

    def is_vertical_line(self, max_width: float = 3.0) -> bool:
        """Check if bbox represents a vertical line (very short width)."""
        return self.width <= max_width and self.height > self.width

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"BBox({self.x0:.1f}, {self.y0:.1f}, {self.x1:.1f}, {self.y1:.1f})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"BBox(x0={self.x0}, y0={self.y0}, x1={self.x1}, y1={self.y1}, "
                f"w={self.width:.1f}, h={self.height:.1f})")


def merge_bboxes(bboxes: List[BBox]) -> Optional[BBox]:
    """
    Merge multiple bboxes into a single bbox that encompasses all.

    Args:
        bboxes: List of bounding boxes to merge

    Returns:
        Single bbox containing all input bboxes, or None if list is empty
    """
    if not bboxes:
        return None

    result = bboxes[0]
    for bbox in bboxes[1:]:
        result = result.union(bbox)

    return result


def cluster_bboxes_by_position(
    bboxes: List[BBox],
    direction: str = "horizontal",
    tolerance: float = 5.0
) -> List[List[BBox]]:
    """
    Cluster bboxes by their position in the specified direction.

    Args:
        bboxes: List of bounding boxes to cluster
        direction: "horizontal" (by Y position) or "vertical" (by X position)
        tolerance: Maximum distance between bboxes to be in same cluster

    Returns:
        List of clusters, each containing bboxes at similar positions
    """
    if not bboxes:
        return []

    # Sort by primary coordinate
    if direction == "horizontal":
        sorted_bboxes = sorted(bboxes, key=lambda b: b.center_y, reverse=True)
    else:  # vertical
        sorted_bboxes = sorted(bboxes, key=lambda b: b.center_x)

    clusters = []
    current_cluster = [sorted_bboxes[0]]

    for bbox in sorted_bboxes[1:]:
        # Check if bbox belongs to current cluster
        if direction == "horizontal":
            distance = abs(bbox.center_y - current_cluster[-1].center_y)
        else:
            distance = abs(bbox.center_x - current_cluster[-1].center_x)

        if distance <= tolerance:
            current_cluster.append(bbox)
        else:
            clusters.append(current_cluster)
            current_cluster = [bbox]

    clusters.append(current_cluster)
    return clusters