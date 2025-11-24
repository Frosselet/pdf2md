# PDF2MD: Spatial-Aware PDF to Markdown Conversion

A pure-engineering approach to PDF�Markdown conversion that preserves spatial relationships and document structure through intelligent bbox analysis and typography heuristics.

## Features

- **Spatial-First Processing**: Uses PyMuPDF's bbox coordinates to maintain true 2D document understanding
- **Background Element Intelligence**: Leverages lines, colors, and shapes for enhanced table detection
- **Typography-Based Structure**: Analyzes fonts to derive headings, captions, and document hierarchy
- **Quality-Aware Pipeline**: Assesses and sanitizes problematic PDFs (especially MS Office generated)
- **Human-Like Perception**: Implements heuristics that mimic visual document understanding
- **Pure Engineering**: No ML dependencies - fast, reliable, and debuggable

## Installation

```bash
pip install pdf2md
```

For development:
```bash
git clone https://github.com/francoisrosselet/pdf2md
cd pdf2md
pip install -e ".[dev]"
```

## Quick Start

```python
from pdf2md import convert_pdf

# Convert from file path
markdown = convert_pdf("document.pdf")

# Convert from bytes
with open("document.pdf", "rb") as f:
    markdown = convert_pdf(f.read())

# Advanced usage with options
from pdf2md import PDFConverter

converter = PDFConverter(
    quality_threshold=0.8,
    enable_sanitization=True,
    optimize_for_genai=True
)
markdown = converter.convert("document.pdf")
```

## Architecture

The conversion pipeline follows these steps:

1. **Loading**: Accept PDF paths or bytes
2. **Quality Assessment**: Analyze text extraction quality and detect issues
3. **Sanitization**: Fix common problems (MS Office artifacts, encoding issues)
4. **First Pass Generation**: Spatial analysis � Initial markdown
5. **Second Pass Refinement**: Table enhancement and structure optimization
6. **GenAI Optimization**: Optional token reduction while preserving semantics
7. **Export**: Clean markdown output

## Key Innovations

### Spatial Clustering
- Groups elements by bbox proximity
- Detects column boundaries and reading flow
- Handles multi-column layouts intelligently

### Typography Intelligence
- Builds font hierarchy maps for structure detection
- Identifies headings, captions, and emphasis patterns
- Maintains consistent spacing analysis

### Background Element Analysis
- Uses PyMuPDF's drawing instructions for table detection
- Leverages colored rectangles for zebra striping and headers
- Combines visual and textual evidence for robust parsing

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/pdf2md

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## Development

This project uses modern Python development tools:
- **Black**: Code formatting
- **Ruff**: Fast linting
- **MyPy**: Type checking
- **Pytest**: Testing framework

```bash
# Setup pre-commit hooks
pre-commit install

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and code is properly formatted
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built on top of [PyMuPDF](https://github.com/pymupdf/PyMuPDF) for robust PDF parsing capabilities.