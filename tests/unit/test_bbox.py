"""
Unit tests for BBox spatial operations.

Tests all the spatial operations, transformations, and utility methods
that form the foundation of spatial-aware PDF parsing.
"""

import pytest
import math
from src.pdf2md.core.bbox import BBox, merge_bboxes, cluster_bboxes_by_position


class TestBBoxCreation:
    """Test BBox creation and validation."""

    def test_basic_creation(self):
        """Test basic bbox creation."""
        bbox = BBox(10, 20, 30, 40)
        assert bbox.x0 == 10
        assert bbox.y0 == 20
        assert bbox.x1 == 30
        assert bbox.y1 == 40

    def test_from_tuple(self):
        """Test creation from tuple."""
        bbox = BBox.from_tuple((10, 20, 30, 40))
        assert bbox.x0 == 10
        assert bbox.y1 == 40

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"x0": 10, "y0": 20, "x1": 30, "y1": 40}
        bbox = BBox.from_dict(data)
        assert bbox.width == 20
        assert bbox.height == 20

    def test_from_center_size(self):
        """Test creation from center and size."""
        bbox = BBox.from_center_size(20, 30, 10, 20)
        assert bbox.x0 == 15
        assert bbox.y0 == 20
        assert bbox.x1 == 25
        assert bbox.y1 == 40

    def test_invalid_coordinates(self):
        """Test validation of invalid coordinates."""
        with pytest.raises(ValueError, match="x0.*must be.*x1"):
            BBox(30, 20, 10, 40)  # x0 > x1

        with pytest.raises(ValueError, match="y0.*must be.*y1"):
            BBox(10, 40, 30, 20)  # y0 > y1


class TestBBoxProperties:
    """Test BBox computed properties."""

    def setup_method(self):
        """Set up test bbox."""
        self.bbox = BBox(10, 20, 30, 50)  # width=20, height=30

    def test_dimensions(self):
        """Test width and height calculation."""
        assert self.bbox.width == 20
        assert self.bbox.height == 30
        assert self.bbox.area == 600

    def test_center(self):
        """Test center point calculation."""
        assert self.bbox.center_x == 20
        assert self.bbox.center_y == 35
        assert self.bbox.center == (20, 35)

    def test_corners(self):
        """Test corner coordinates."""
        assert self.bbox.top_left == (10, 50)
        assert self.bbox.top_right == (30, 50)
        assert self.bbox.bottom_left == (10, 20)
        assert self.bbox.bottom_right == (30, 20)

    def test_aspect_ratio(self):
        """Test aspect ratio calculation."""
        assert self.bbox.aspect_ratio() == 20/30

        # Test square bbox
        square = BBox(0, 0, 10, 10)
        assert square.aspect_ratio() == 1.0

        # Test zero height
        line = BBox(0, 0, 10, 0)
        assert line.aspect_ratio() == float('inf')


class TestSpatialRelationships:
    """Test spatial relationship methods."""

    def test_overlaps(self):
        """Test bbox overlap detection."""
        bbox1 = BBox(0, 0, 10, 10)
        bbox2 = BBox(5, 5, 15, 15)  # Overlapping
        bbox3 = BBox(20, 20, 30, 30)  # Non-overlapping

        assert bbox1.overlaps(bbox2)
        assert bbox2.overlaps(bbox1)
        assert not bbox1.overlaps(bbox3)
        assert not bbox3.overlaps(bbox1)

    def test_overlaps_with_tolerance(self):
        """Test overlap detection with tolerance."""
        bbox1 = BBox(0, 0, 10, 10)
        bbox2 = BBox(12, 12, 20, 20)  # 2 units apart

        assert not bbox1.overlaps(bbox2)
        assert bbox1.overlaps(bbox2, tolerance=3)

    def test_contains_point(self):
        """Test point containment."""
        bbox = BBox(10, 20, 30, 40)

        assert bbox.contains_point(20, 30)  # Inside
        assert bbox.contains_point(10, 20)  # On corner
        assert bbox.contains_point(30, 40)  # On opposite corner
        assert not bbox.contains_point(5, 30)  # Outside

    def test_contains_bbox(self):
        """Test bbox containment."""
        outer = BBox(0, 0, 20, 20)
        inner = BBox(5, 5, 15, 15)
        overlapping = BBox(10, 10, 30, 30)

        assert outer.contains_bbox(inner)
        assert not inner.contains_bbox(outer)
        assert not outer.contains_bbox(overlapping)

    def test_intersection(self):
        """Test bbox intersection calculation."""
        bbox1 = BBox(0, 0, 10, 10)
        bbox2 = BBox(5, 5, 15, 15)
        bbox3 = BBox(20, 20, 30, 30)

        # Overlapping bboxes
        intersection = bbox1.intersection(bbox2)
        assert intersection == BBox(5, 5, 10, 10)

        # Non-overlapping bboxes
        no_intersection = bbox1.intersection(bbox3)
        assert no_intersection is None

    def test_union(self):
        """Test bbox union calculation."""
        bbox1 = BBox(0, 0, 10, 10)
        bbox2 = BBox(5, 5, 15, 15)

        union = bbox1.union(bbox2)
        assert union == BBox(0, 0, 15, 15)

    def test_intersection_ratio(self):
        """Test intersection ratio calculation."""
        bbox1 = BBox(0, 0, 10, 10)  # Area = 100
        bbox2 = BBox(5, 5, 15, 15)  # Area = 100, intersection = 25

        ratio = bbox1.intersection_ratio(bbox2)
        assert ratio == 0.25  # 25/100


class TestDistanceCalculations:
    """Test distance calculation methods."""

    def test_distance_to_point(self):
        """Test distance to point calculation."""
        bbox = BBox(0, 0, 10, 10)

        # Point inside bbox
        assert bbox.distance_to_point(5, 5) == 0.0

        # Point directly to the right
        assert bbox.distance_to_point(15, 5) == 5.0

        # Point diagonally away
        distance = bbox.distance_to_point(15, 15)
        expected = math.sqrt(5*5 + 5*5)  # Pythagorean theorem
        assert abs(distance - expected) < 0.001

    def test_distance_to_bbox(self):
        """Test distance between bboxes."""
        bbox1 = BBox(0, 0, 10, 10)
        bbox2 = BBox(20, 0, 30, 10)  # 10 units to the right
        bbox3 = BBox(5, 5, 15, 15)  # Overlapping

        assert bbox1.distance_to_bbox(bbox2) == 10.0
        assert bbox1.distance_to_bbox(bbox3) == 0.0  # Overlapping

    def test_horizontal_vertical_distance(self):
        """Test horizontal and vertical distance calculations."""
        bbox1 = BBox(0, 0, 10, 10)
        bbox2 = BBox(20, 15, 30, 25)

        assert bbox1.horizontal_distance(bbox2) == 10.0
        assert bbox1.vertical_distance(bbox2) == 5.0


class TestAlignment:
    """Test alignment detection methods."""

    def test_horizontally_aligned(self):
        """Test horizontal alignment detection."""
        bbox1 = BBox(0, 10, 5, 20)
        bbox2 = BBox(10, 11, 15, 21)  # Slightly offset Y
        bbox3 = BBox(20, 30, 25, 40)  # Different Y

        assert bbox1.horizontally_aligned(bbox2, tolerance=2)
        assert not bbox1.horizontally_aligned(bbox3, tolerance=2)

    def test_vertically_aligned(self):
        """Test vertical alignment detection."""
        bbox1 = BBox(10, 0, 20, 5)
        bbox2 = BBox(11, 10, 21, 15)  # Slightly offset X
        bbox3 = BBox(30, 20, 40, 25)  # Different X

        assert bbox1.vertically_aligned(bbox2, tolerance=2)
        assert not bbox1.vertically_aligned(bbox3, tolerance=2)

    def test_same_line(self):
        """Test same line detection for text."""
        bbox1 = BBox(0, 10, 50, 20)  # Text line
        bbox2 = BBox(60, 11, 110, 21)  # Same line, slight offset
        bbox3 = BBox(120, 30, 170, 40)  # Different line

        assert bbox1.same_line(bbox2)
        assert not bbox1.same_line(bbox3)

    def test_same_column(self):
        """Test same column detection."""
        bbox1 = BBox(10, 0, 20, 10)
        bbox2 = BBox(12, 20, 22, 30)  # Same column, slight offset
        bbox3 = BBox(50, 40, 60, 50)  # Different column

        assert bbox1.same_column(bbox2)
        assert not bbox1.same_column(bbox3)


class TestTransformations:
    """Test bbox transformation methods."""

    def test_translate(self):
        """Test translation transformation."""
        bbox = BBox(10, 20, 30, 40)
        translated = bbox.translate(5, -10)

        assert translated == BBox(15, 10, 35, 30)
        assert bbox == BBox(10, 20, 30, 40)  # Original unchanged

    def test_scale(self):
        """Test scaling transformation."""
        bbox = BBox(10, 10, 20, 30)  # Center at (15, 20), size 10x20
        scaled = bbox.scale(2.0, 0.5)

        # Should scale around center: width 20, height 10
        # Center stays at (15, 20), new width=20, new height=10
        # So new bbox: (15-10, 20-5, 15+10, 20+5) = (5, 15, 25, 25)
        expected = BBox(5, 15, 25, 25)
        assert abs(scaled.x0 - expected.x0) < 0.001
        assert abs(scaled.y0 - expected.y0) < 0.001
        assert abs(scaled.x1 - expected.x1) < 0.001
        assert abs(scaled.y1 - expected.y1) < 0.001

    def test_expand(self):
        """Test expansion transformation."""
        bbox = BBox(10, 20, 30, 40)
        expanded = bbox.expand(5)

        assert expanded == BBox(5, 15, 35, 45)

    def test_expand_to_grid(self):
        """Test grid expansion."""
        bbox = BBox(12.3, 17.8, 28.6, 33.2)
        gridded = bbox.expand_to_grid(5.0)

        assert gridded == BBox(10, 15, 30, 35)


class TestUtilityMethods:
    """Test utility and classification methods."""

    def test_is_roughly_square(self):
        """Test square detection."""
        square = BBox(0, 0, 10, 10)
        near_square = BBox(0, 0, 10, 11)
        rectangle = BBox(0, 0, 20, 10)

        assert square.is_roughly_square()
        assert near_square.is_roughly_square(tolerance=0.2)
        assert not rectangle.is_roughly_square()

    def test_is_horizontal_line(self):
        """Test horizontal line detection."""
        line = BBox(0, 10, 100, 12)  # Height = 2
        not_line = BBox(0, 0, 20, 20)

        assert line.is_horizontal_line()
        assert not not_line.is_horizontal_line()

    def test_is_vertical_line(self):
        """Test vertical line detection."""
        line = BBox(10, 0, 12, 100)  # Width = 2
        not_line = BBox(0, 0, 20, 20)

        assert line.is_vertical_line()
        assert not not_line.is_vertical_line()

    def test_string_representation(self):
        """Test string representations."""
        bbox = BBox(10.123, 20.456, 30.789, 40.012)

        str_repr = str(bbox)
        assert "10.1" in str_repr
        assert "20.5" in str_repr

        repr_repr = repr(bbox)
        assert "x0=10.123" in repr_repr
        assert "w=20.7" in repr_repr


class TestBBoxUtilities:
    """Test utility functions for working with multiple bboxes."""

    def test_merge_bboxes_empty(self):
        """Test merging empty list."""
        result = merge_bboxes([])
        assert result is None

    def test_merge_bboxes_single(self):
        """Test merging single bbox."""
        bbox = BBox(10, 20, 30, 40)
        result = merge_bboxes([bbox])
        assert result == bbox

    def test_merge_bboxes_multiple(self):
        """Test merging multiple bboxes."""
        bbox1 = BBox(0, 0, 10, 10)
        bbox2 = BBox(20, 30, 40, 50)
        bbox3 = BBox(5, 5, 15, 15)

        result = merge_bboxes([bbox1, bbox2, bbox3])
        assert result == BBox(0, 0, 40, 50)

    def test_cluster_bboxes_horizontal(self):
        """Test horizontal clustering (by Y position)."""
        # Create bboxes at different Y levels
        bboxes = [
            BBox(0, 50, 10, 60),   # Top line
            BBox(20, 51, 30, 61),  # Same line (within tolerance)
            BBox(0, 30, 10, 40),   # Middle line
            BBox(0, 10, 10, 20),   # Bottom line
            BBox(20, 31, 30, 41),  # Same as middle (within tolerance)
        ]

        clusters = cluster_bboxes_by_position(bboxes, "horizontal", tolerance=5)

        assert len(clusters) == 3  # Three distinct Y levels

        # Check that similar Y positions are clustered together
        top_cluster = next(c for c in clusters if any(b.center_y > 50 for b in c))
        assert len(top_cluster) == 2  # Two boxes at top

    def test_cluster_bboxes_vertical(self):
        """Test vertical clustering (by X position)."""
        bboxes = [
            BBox(10, 0, 20, 10),   # Left column
            BBox(11, 20, 21, 30),  # Same column (within tolerance)
            BBox(50, 0, 60, 10),   # Right column
            BBox(51, 20, 61, 30),  # Same as right (within tolerance)
            BBox(100, 0, 110, 10), # Far right column
        ]

        clusters = cluster_bboxes_by_position(bboxes, "vertical", tolerance=5)

        assert len(clusters) == 3  # Three distinct X levels

    def test_cluster_bboxes_empty(self):
        """Test clustering empty list."""
        clusters = cluster_bboxes_by_position([], "horizontal")
        assert clusters == []


class TestBBoxConversions:
    """Test data conversion methods."""

    def test_to_tuple(self):
        """Test conversion to tuple."""
        bbox = BBox(10, 20, 30, 40)
        assert bbox.to_tuple() == (10, 20, 30, 40)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        bbox = BBox(10, 20, 30, 40)
        expected = {"x0": 10, "y0": 20, "x1": 30, "y1": 40}
        assert bbox.to_dict() == expected

    def test_roundtrip_conversion(self):
        """Test roundtrip conversion preserves data."""
        original = BBox(12.34, 34.56, 90.12, 56.78)  # Fix invalid coordinates

        # Tuple roundtrip
        tuple_roundtrip = BBox.from_tuple(original.to_tuple())
        assert tuple_roundtrip == original

        # Dict roundtrip
        dict_roundtrip = BBox.from_dict(original.to_dict())
        assert dict_roundtrip == original