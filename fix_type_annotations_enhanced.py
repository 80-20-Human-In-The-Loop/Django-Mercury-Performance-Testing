#!/usr/bin/env python3
"""
Enhanced script to automatically fix common type annotation issues.
This helps reduce mypy errors by adding proper type hints.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

def add_typing_imports(content: str) -> str:
    """Add necessary typing imports if not present."""
    has_typing = 'from typing import' in content or 'import typing' in content
    
    # Check what we need to import
    needs_list = 'List[' in content or ': List[' in content
    needs_dict = 'Dict[' in content or ': Dict[' in content
    needs_optional = 'Optional[' in content
    needs_any = 'Any' in content and not has_typing
    
    if not has_typing and (needs_list or needs_dict or needs_optional or needs_any):
        # Find the right place to add import
        lines = content.split('\n')
        import_line = -1
        
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_line = i
                break
        
        imports = []
        if needs_list: imports.append('List')
        if needs_dict: imports.append('Dict')
        if needs_optional: imports.append('Optional')
        if needs_any: imports.append('Any')
        
        if imports and import_line >= 0:
            import_statement = f"from typing import {', '.join(imports)}"
            lines.insert(import_line + 1, import_statement)
            content = '\n'.join(lines)
    
    return content

def fix_file(filepath: Path) -> int:
    """Fix type annotations in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    changes = 0
    
    # Patterns to fix (method signature -> fixed signature)
    patterns: List[Tuple[str, str]] = [
        # All __init__ methods need -> None
        (r'(\s+def __init__\(self[^)]*\)):', r'\1 -> None:'),
        
        # Property setters need -> None
        (r'(\s+def set_\w+\(self[^)]*\)):', r'\1 -> None:'),
        
        # Boolean methods
        (r'(\s+def is_\w+\(self[^)]*\)):', r'\1 -> bool:'),
        (r'(\s+def has_\w+\(self[^)]*\)):', r'\1 -> bool:'),
        (r'(\s+def can_\w+\(self[^)]*\)):', r'\1 -> bool:'),
        (r'(\s+def should_\w+\(self[^)]*\)):', r'\1 -> bool:'),
        
        # String methods
        (r'(\s+def __str__\(self\)):', r'\1 -> str:'),
        (r'(\s+def __repr__\(self\)):', r'\1 -> str:'),
        
        # Common None-returning methods
        (r'(\s+def start\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def stop\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def close\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def cleanup\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def reset\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def clear\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def update\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def save\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def load\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def run\(self[^)]*\)):', r'\1 -> None:'),
        (r'(\s+def execute\(self[^)]*\)):', r'\1 -> None:'),
        
        # Context managers
        (r'(\s+def __enter__\(self\)):', r'\1 -> "Self":'),
        (r'(\s+def __exit__\(self[^)]*\)):', r'\1 -> None:'),
        
        # Note: Removed generic type patterns as they were causing issues
    ]
    
    for pattern, replacement in patterns:
        # Check if pattern exists without the return type already
        if re.search(pattern, content):
            # Make sure we're not replacing already typed methods
            if ' -> ' not in pattern:
                new_content = re.sub(pattern, replacement, content)
                changes += len(re.findall(pattern, content))
                content = new_content
    
    # Add typing imports if needed
    if content != original:
        content = add_typing_imports(content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {changes} annotations in {filepath}")
        return changes
    
    return 0

def main() -> int:
    """Main function to process all Python files."""
    total_changes = 0
    
    # Find all Python files (excluding venv, migrations, etc.)
    exclude_dirs = {'.venv', 'venv', '__pycache__', 'migrations', 'build', 'dist'}
    
    python_files: List[Path] = []
    for py_file in Path('.').rglob('*.py'):
        # Skip if in excluded directory
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue
        python_files.append(py_file)
    
    print(f"Found {len(python_files)} Python files to process")
    
    for filepath in python_files:
        try:
            changes = fix_file(filepath)
            total_changes += changes
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print(f"\nTotal: Fixed {total_changes} type annotations")
    return 0

if __name__ == "__main__":
    sys.exit(main())