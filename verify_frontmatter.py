#!/usr/bin/env python3
"""Verify that all output files have valid YAML frontmatter compatible with MkDocs"""

import sys
sys.path.insert(0, '.venv/Lib/site-packages')

import frontmatter
import glob
from pathlib import Path

def verify_frontmatter():
    """Verify all markdown files have valid frontmatter"""
    files = glob.glob('test_output/**/*.md', recursive=True)
    print(f"Found {len(files)} markdown files\n")

    errors = []
    success_count = 0

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                metadata = post.metadata

                # Check required fields
                required_fields = ['title', 'category', 'url']
                missing_fields = [field for field in required_fields if field not in metadata]

                if missing_fields:
                    errors.append(f"{file_path}: Missing fields {missing_fields}")
                else:
                    success_count += 1
                    print(f"✓ {Path(file_path).relative_to('test_output')}")
                    print(f"  - title: {metadata.get('title')}")
                    print(f"  - category: {metadata.get('category')}")
                    print(f"  - description: {metadata.get('description', 'N/A')[:50]}...")
                    print()

        except Exception as e:
            errors.append(f"{file_path}: {str(e)}")

    print("=" * 60)
    print(f"Verification Results:")
    print(f"  Total files: {len(files)}")
    print(f"  Valid: {success_count}")
    print(f"  Errors: {len(errors)}")

    if errors:
        print("\nErrors found:")
        for error in errors:
            print(f"  ✗ {error}")
        return False
    else:
        print("\n✓ All files have valid MkDocs-compatible frontmatter!")
        return True

if __name__ == "__main__":
    success = verify_frontmatter()
    sys.exit(0 if success else 1)
