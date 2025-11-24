"""Pytest configuration and fixtures for PDF2MD tests."""

import pytest
from pathlib import Path
from typing import Generator

# Test data paths
TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"
REAL_WORLD_DIR = TEST_DIR.parent / "real-world-pdfs"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def real_world_dir() -> Path:
    """Path to real-world PDFs directory."""
    return REAL_WORLD_DIR


@pytest.fixture
def sample_bbox_data():
    """Sample bbox data for testing spatial operations."""
    return {
        "title": {"x0": 100, "y0": 50, "x1": 400, "y1": 80},
        "paragraph1": {"x0": 100, "y0": 100, "x1": 500, "y1": 150},
        "paragraph2": {"x0": 100, "y0": 170, "x1": 500, "y1": 220},
        "table_cell": {"x0": 100, "y0": 250, "x1": 200, "y1": 280},
    }


@pytest.fixture
def sample_font_data():
    """Sample font data for typography analysis testing."""
    return {
        "title": {"size": 24, "weight": "bold", "family": "Arial"},
        "heading": {"size": 18, "weight": "bold", "family": "Arial"},
        "body": {"size": 12, "weight": "normal", "family": "Arial"},
        "caption": {"size": 10, "weight": "italic", "family": "Arial"},
    }