#!/usr/bin/env python
"""
Mercury Test Runner - Console Script for Educational Testing

This module provides a standalone command-line tool for running Django tests
with Mercury's educational mode enabled automatically.

Usage:
    mercury-test                    # Run all tests with educational mode
    mercury-test app.tests          # Run specific app tests
    mercury-test --level advanced   # Set education level
    mercury-test --help            # Show help
"""

import os
import sys
import argparse
from pathlib import Path


def find_manage_py():
    """Find manage.py in current or parent directories."""
    current = Path.cwd()
    
    # Check current directory and up to 3 parent directories
    for _ in range(4):
        manage_path = current / 'manage.py'
        if manage_path.exists():
            return str(manage_path)
        current = current.parent
        if current == current.parent:  # Reached root
            break
    
    return None


def main():
    """Main entry point for mercury-test command."""
    parser = argparse.ArgumentParser(
        description='Run Django tests with Mercury Educational Mode',
        prog='mercury-test',
        epilog='Examples:\n'
               '  mercury-test                  # Run all tests\n'
               '  mercury-test users.tests      # Run specific tests\n'
               '  mercury-test --level intermediate  # Set difficulty level',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Test labels (positional arguments)
    parser.add_argument(
        'test_labels',
        nargs='*',
        help='Test labels to run (e.g., app.tests.TestCase)'
    )
    
    # Educational options
    parser.add_argument(
        '--level',
        choices=['beginner', 'intermediate', 'advanced'],
        default='beginner',
        help='Educational difficulty level (default: beginner)'
    )
    
    parser.add_argument(
        '--no-pause',
        action='store_true',
        help='Disable interactive pauses (useful for CI)'
    )
    
    # Django test options (pass-through)
    parser.add_argument(
        '--failfast',
        action='store_true',
        help='Stop on first test failure'
    )
    
    parser.add_argument(
        '--keepdb',
        action='store_true',
        help='Preserve test database between runs'
    )
    
    parser.add_argument(
        '--parallel',
        type=int,
        metavar='N',
        help='Run tests in parallel'
    )
    
    parser.add_argument(
        '--verbosity',
        type=int,
        choices=[0, 1, 2, 3],
        default=1,
        help='Verbosity level'
    )
    
    parser.add_argument(
        '--settings',
        help='Settings module to use'
    )
    
    args = parser.parse_args()
    
    # Set up Mercury educational environment
    os.environ['MERCURY_EDU'] = '1'
    os.environ['MERCURY_EDUCATIONAL_MODE'] = 'true'
    os.environ['MERCURY_EDU_LEVEL'] = args.level
    
    if args.no_pause:
        os.environ['MERCURY_NON_INTERACTIVE'] = '1'
    
    # Find manage.py
    manage_py = find_manage_py()
    if not manage_py:
        print("Error: Could not find manage.py in current directory or parent directories.")
        print("Please run mercury-test from your Django project directory.")
        sys.exit(1)
    
    # Build command
    cmd_args = [sys.executable, manage_py, 'test']
    
    # Add test labels
    if args.test_labels:
        cmd_args.extend(args.test_labels)
    
    # Add Django options
    if args.failfast:
        cmd_args.append('--failfast')
    
    if args.keepdb:
        cmd_args.append('--keepdb')
    
    if args.parallel:
        cmd_args.extend(['--parallel', str(args.parallel)])
    
    if args.verbosity is not None:
        cmd_args.extend(['--verbosity', str(args.verbosity)])
    
    if args.settings:
        cmd_args.extend(['--settings', args.settings])
    
    # Show educational mode banner
    print("=" * 60)
    print("🎓 Django Mercury Educational Testing Mode")
    print("=" * 60)
    print(f"Level: {args.level.capitalize()}")
    print(f"Interactive: {'No' if args.no_pause else 'Yes'}")
    print(f"Running: {' '.join(cmd_args)}")
    print("=" * 60)
    print()
    
    # Execute Django test command
    import subprocess
    result = subprocess.run(cmd_args)
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()