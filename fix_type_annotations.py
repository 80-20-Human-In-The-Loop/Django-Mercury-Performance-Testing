#!/usr/bin/env python3
"""
Script to automatically add -> None return type annotations to common methods.
This helps reduce mypy errors for missing return type annotations.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

def fix_file(filepath: Path) -> int:
    """Fix type annotations in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    changes = 0
    
    # Patterns to fix (method signature -> fixed signature)
    patterns: List[Tuple[str, str]] = [
        # Test methods
        (r'(\s+def test_\w+\(self[^)]*\)):', r'\1 -> None:'),
        # Setup/teardown methods
        (r'(\s+def setUp\(self\)):', r'\1 -> None:'),
        (r'(\s+def tearDown\(self\)):', r'\1 -> None:'),
        (r'(\s+def setUpClass\(cls\)):', r'\1 -> None:'),
        (r'(\s+def tearDownClass\(cls\)):', r'\1 -> None:'),
        # Django test methods
        (r'(\s+def setUpTestData\(cls\)):', r'\1 -> None:'),
        # Common private methods
        (r'(\s+def _setUp\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def _tearDown\(self[^)]*\)):', r'\1 -> None:'),
    ]
    
    for pattern, replacement in patterns:
        # Check if pattern exists without -> None already
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes += len(re.findall(pattern, original))
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {changes} annotations in {filepath}")
        return changes
    
    return 0

def main() -> int:
    """Main function to process all Python test files."""
    total_changes = 0
    
    # Find all test files
    test_dirs = [
        Path("tests"),
        Path("django_mercury/tests"),
    ]
    
    test_files: List[Path] = []
    for test_dir in test_dirs:
        if test_dir.exists():
            test_files.extend(test_dir.rglob("test_*.py"))
            test_files.extend(test_dir.rglob("*_test.py"))
    
    print(f"Found {len(test_files)} test files to process")
    
    for filepath in test_files:
        changes = fix_file(filepath)
        total_changes += changes
    
    print(f"\nTotal: Fixed {total_changes} type annotations")
    return 0 if total_changes > 0 else 1

if __name__ == "__main__":
    sys.exit(main())