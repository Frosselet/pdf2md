#!/usr/bin/env python3
"""
Reorganize PDFs based on analysis recommendations
"""

import json
import shutil
import os
from pathlib import Path


def reorganize_pdfs():
    """Move PDFs to their recommended categories."""
    base_dir = Path("/Volumes/WD Green/dev/git/pdf2md/pdf2md/real-world-pdfs")
    json_path = base_dir / "analysis_detailed.json"

    with open(json_path, 'r') as f:
        data = json.load(f)

    moves = []

    for result in data['results']:
        current_path = result['path']
        filename = result['filename']
        current_dir = os.path.dirname(current_path)
        current_category = os.path.basename(current_dir)

        # Determine suggested category
        issues = result.get('issues', [])
        problematic_indicators = [
            'MS_OFFICE_GENERATED',
            'NO_TEXT_EXTRACTED',
            'PROCESSING_ERROR',
            'ENCODING_PROBLEMS'
        ]
        complex_indicators = [
            'MULTI_COLUMN_LAYOUT',
            'TABLE_STRUCTURES',
            'COMPLEX_GRAPHICS',
            'EXCESSIVE_FONTS'
        ]

        problematic_count = sum(1 for issue in issues if issue in problematic_indicators)
        complex_count = sum(1 for issue in issues if issue in complex_indicators)

        if problematic_count > 0:
            suggested_category = 'problematic'
        elif complex_count >= 2:
            suggested_category = 'complex'
        elif complex_count == 1:
            suggested_category = 'complex'
        else:
            suggested_category = 'simple'

        if current_category != suggested_category:
            new_path = os.path.join(base_dir, suggested_category, filename)
            moves.append({
                'filename': filename,
                'from': current_category,
                'to': suggested_category,
                'current_path': current_path,
                'new_path': new_path
            })

    if not moves:
        print("No files need to be moved. All PDFs are in the correct categories.")
        return

    print(f"Found {len(moves)} files to reorganize:")
    print()

    for move in moves:
        print(f"  {move['filename']}")
        print(f"    {move['from']} -> {move['to']}")
        print()

    response = input("Proceed with moving files? (yes/no): ")
    if response.lower() == 'yes':
        for move in moves:
            shutil.move(move['current_path'], move['new_path'])
            print(f"Moved: {move['filename']}")
        print()
        print("Reorganization complete!")
    else:
        print("Reorganization cancelled.")


if __name__ == "__main__":
    reorganize_pdfs()
