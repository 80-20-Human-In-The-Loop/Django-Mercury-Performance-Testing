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
import time
import random
from pathlib import Path

# Try to import rich components
try:
    from rich.console import Console
    from rich.rule import Rule
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


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


def show_parallel_hint(elapsed_time):
    """Show hint about using --parallel flag for faster tests."""
    if RICH_AVAILABLE:
        console = Console()
        console.print()
        console.print(Rule("💡 Performance Tip", style="yellow"))
        console.print(f"Your tests took {elapsed_time:.1f} seconds to complete.\n")
        console.print("Speed up your tests by running them in parallel:\n")
        
        # Create styled command text
        text = Text()
        text.append("  mercury-test ", style="white")
        text.append("--parallel", style="bold cyan")
        text.append(" ", style="white")
        text.append("4", style="bold yellow")
        console.print(text)
        
        console.print("\nWhere the number is how many parallel processes to use")
        console.print("(typically 2-8 depending on your CPU cores)")
        console.print(Rule(style="yellow"))
    else:
        # Fallback to plain text
        print("\n" + "=" * 60)
        print("💡 Performance Tip")
        print("=" * 60)
        print(f"Your tests took {elapsed_time:.1f} seconds to complete.\n")
        print("Speed up your tests by running them in parallel:\n")
        print("  mercury-test --parallel 4\n")
        print("Where the number is how many parallel processes to use")
        print("(typically 2-8 depending on your CPU cores)")
        print("=" * 60)


def show_specific_test_hint(elapsed_time):
    """Show hint about testing specific modules for faster results."""
    if RICH_AVAILABLE:
        console = Console()
        console.print()
        console.print(Rule("💡 Performance Tip", style="yellow"))
        console.print(f"Your tests took {elapsed_time:.1f} seconds to complete.\n")
        console.print("Test specific modules/files for faster results:\n")
        
        # Create styled examples
        examples = [
            "  mercury-test users.tests",
            "  mercury-test users.tests.test_models",
            "  mercury-test users.tests.TestUserCreation"
        ]
        
        for example in examples:
            text = Text(example, style="green")
            console.print(text)
        
        console.print("\nYou can specify app names, test modules, or even")
        console.print("individual test classes to run only what you need!")
        console.print(Rule(style="yellow"))
    else:
        # Fallback to plain text
        print("\n" + "=" * 60)
        print("💡 Performance Tip")
        print("=" * 60)
        print(f"Your tests took {elapsed_time:.1f} seconds to complete.\n")
        print("Test specific modules/files for faster results:\n")
        print("  mercury-test users.tests")
        print("  mercury-test users.tests.test_models")
        print("  mercury-test users.tests.TestUserCreation\n")
        print("You can specify app names, test modules, or even")
        print("individual test classes to run only what you need!")
        print("=" * 60)


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
    
    # C Extension verification
    parser.add_argument(
        '--ext',
        action='store_true',
        help='Check if C extensions are loaded and working'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance comparison between C extensions and pure Python (use with --ext)'
    )
    
    args = parser.parse_args()
    
    # Check C extensions if requested
    if args.ext:
        from .verify_extensions import verify_c_extensions
        return verify_c_extensions(benchmark=args.benchmark)
    
    # Set up Mercury educational environment
    os.environ['MERCURY_EDU'] = '1'
    os.environ['MERCURY_EDUCATIONAL_MODE'] = 'true'
    os.environ['MERCURY_EDU_LEVEL'] = args.level
    
    if args.no_pause:
        os.environ['MERCURY_NON_INTERACTIVE'] = '1'
    else:
        # Explicitly set interactive mode
        os.environ['MERCURY_INTERACTIVE'] = '1'
        # Make sure non-interactive is not set
        if 'MERCURY_NON_INTERACTIVE' in os.environ:
            del os.environ['MERCURY_NON_INTERACTIVE']
    
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
    
    # Execute Django test command with proper stdin/stdout/stderr handling
    import subprocess
    
    # Track test execution time
    start_time = time.time()
    
    # For interactive mode, we need to preserve TTY
    if not args.no_pause:
        # Pass through stdin/stdout/stderr to preserve TTY
        result = subprocess.run(
            cmd_args,
            stdin=sys.stdin,
            stdout=sys.stdout, 
            stderr=sys.stderr
        )
    else:
        # Non-interactive mode, normal subprocess
        result = subprocess.run(cmd_args)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Show performance hint if tests took over 100 seconds
    if elapsed_time > 100:
        if args.parallel:
            # Already using parallel, only show specific test hint
            show_specific_test_hint(elapsed_time)
        else:
            # Randomly choose between the two tips
            if random.choice([True, False]):
                show_parallel_hint(elapsed_time)
            else:
                show_specific_test_hint(elapsed_time)
    
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()