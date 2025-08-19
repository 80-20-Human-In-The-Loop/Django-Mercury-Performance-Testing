#!/usr/bin/env python3
"""
Script to fix Optional/None handling issues, especially for console operations.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_console_operations(filepath: Path) -> int:
    """Fix console operations that need None checks."""
    with open(filepath, "r") as f:
        content = f.read()

    original = content
    changes = 0

    # Fix patterns where console might be None
    patterns: List[Tuple[str, str]] = [
        # Find standalone console operations and wrap them
        (r"(\s+)(self\.console\.print\([^)]+\))\n", r"\1if self.console is not None:\n\1    \2\n"),
        (
            r"(\s+)(self\.console\.status\([^)]+\))",
            r"\1if self.console is not None:\n\1    with \2",
        ),
        # Fix console.print in elif/else blocks (needs special handling)
        (
            r"(\s+)else:\n(\s+)(self\.console\.print)",
            r"\1else:\n\2if self.console is not None:\n\2    \3",
        ),
    ]

    for pattern, replacement in patterns:
        # Skip if already has None check
        if "if self.console is not None" not in content:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Check if this specific match already has a None check nearby
                start = max(0, match.start() - 100)
                preceding = content[start : match.start()]
                if "if self.console is not None" not in preceding:
                    content = re.sub(pattern, replacement, content, count=1)
                    changes += 1

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Fixed {changes} Optional/None issues in {filepath}")
        return changes

    return 0


def main() -> int:
    """Main function."""
    total_changes = 0

    # Files known to have console issues
    files_to_fix = [
        Path("django_mercury/cli/educational/interactive_ui.py"),
        # Path("django_mercury/python_bindings/educational_monitor.py"), # Removed - functionality moved to CLI plugins
    ]

    for filepath in files_to_fix:
        if filepath.exists():
            changes = fix_console_operations(filepath)
            total_changes += changes

    print(f"\nTotal: Fixed {total_changes} Optional/None handling issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
