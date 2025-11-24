# Real-World PDF Test Files

This directory contains real-world PDF files for testing the pdf2md library.

## Categories

### Simple Documents
- Single-column text documents
- Basic tables
- Simple typography hierarchies

### Complex Layouts
- Multi-column documents
- Mixed content (text, images, tables)
- Academic papers
- Financial reports

### Problematic PDFs
- Microsoft Office generated PDFs
- Scanned documents with OCR
- Poor encoding or font embedding
- Complex table structures

## Usage

These files are used by the test suite to validate the spatial analysis
and markdown conversion algorithms against real-world document structures.

## Adding New Test Files

When adding new PDFs:
1. Place them in the appropriate category subdirectory
2. Add corresponding expected markdown outputs in `tests/fixtures/expected_outputs/`
3. Update test cases to include the new files
4. Document any specific issues or features the PDF tests

## Privacy Note

Ensure all PDF files contain only public information or properly anonymized data.