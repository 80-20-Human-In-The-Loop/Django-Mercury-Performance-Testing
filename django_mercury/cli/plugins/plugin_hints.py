"""
Performance Hints Plugin for Mercury-Test CLI

Shows helpful performance tips when tests take too long.
Provides random hints to keep the experience educational and varied.
"""

import random
from argparse import ArgumentParser, Namespace
from django_mercury.cli.plugins.base import MercuryPlugin

# Try to import rich components
try:
    from rich.console import Console
    from rich.rule import Rule
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class PerformanceHintsPlugin(MercuryPlugin):
    """Plugin that shows performance tips for slow test runs."""
    
    name = "hints"
    description = "Show performance tips for slow tests"
    priority = 90  # Low priority - runs after tests
    version = "1.0.0"
    
    # Audience targeting
    audiences = ["student"]  # Educational content for learners
    complexity_level = 1  # Simple and easy to understand
    requires_capabilities = []  # Works with basic terminal
    
    def __init__(self):
        """Initialize the hints plugin."""
        super().__init__()
        self._isolation_detected = False  # Track if isolation issues were detected
        self._isolation_tests = []  # Track tests with isolation issues
    
    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register hint-related arguments."""
        parser.add_argument(
            '--no-hints',
            action='store_true',
            help='Disable performance hints'
        )
        
        parser.add_argument(
            '--hint-threshold',
            type=float,
            default=100.0,
            help='Minimum test time (seconds) to show hints (default: 100)'
        )
    
    def is_enabled(self, args: Namespace) -> bool:
        """Check if hints are enabled."""
        return not args.no_hints and super().is_enabled(args)
    
    def post_test_hook(self, args: Namespace, result: int, elapsed: float) -> None:
        """Show performance hints if tests took too long or isolation issues detected."""
        if not self.is_enabled(args):
            return
        
        # Check if isolation issues were detected
        if self._isolation_detected and self._isolation_tests:
            self._show_isolation_hint()
            return  # Show isolation hints instead of performance hints
        
        threshold = getattr(args, 'hint_threshold', 100.0)
        
        if elapsed > threshold:
            # If already using parallel, only show specific test hint
            if getattr(args, 'parallel', None):
                self._show_specific_test_hint(elapsed)
            else:
                # Randomly choose between hints (50/50 chance)
                if random.choice([True, False]):
                    self._show_parallel_hint(elapsed)
                else:
                    self._show_specific_test_hint(elapsed)
    
    def _show_parallel_hint(self, elapsed_time: float) -> None:
        """Show hint about using --parallel flag for faster tests."""
        if RICH_AVAILABLE:
            console = Console()
            console.print()
            console.print(Rule("💡 Performance Tip", style="yellow"))
            console.print(f"Your tests took {elapsed_time:.1f} seconds to complete.\\n")
            console.print("Speed up your tests by running them in parallel:\\n")
            
            # Create styled command text
            text = Text()
            text.append("  mercury-test ", style="white")
            text.append("--parallel", style="bold cyan")
            text.append(" ", style="white")
            text.append("4", style="bold yellow")
            console.print(text)
            
            console.print("\\nWhere the number is how many parallel processes to use")
            console.print("(typically 2-8 depending on your CPU cores)")
            console.print(Rule(style="yellow"))
        else:
            # Fallback to plain text
            print("\\n" + "=" * 60)
            print("💡 Performance Tip")
            print("=" * 60)
            print(f"Your tests took {elapsed_time:.1f} seconds to complete.\\n")
            print("Speed up your tests by running them in parallel:\\n")
            print("  mercury-test --parallel 4\\n")
            print("Where the number is how many parallel processes to use")
            print("(typically 2-8 depending on your CPU cores)")
            print("=" * 60)
    
    def _show_specific_test_hint(self, elapsed_time: float) -> None:
        """Show hint about testing specific modules for faster results."""
        if RICH_AVAILABLE:
            console = Console()
            console.print()
            console.print(Rule("💡 Performance Tip", style="yellow"))
            console.print(f"Your tests took {elapsed_time:.1f} seconds to complete.\\n")
            console.print("Test specific modules/files for faster results:\\n")
            
            # Create styled examples
            examples = [
                "  mercury-test users.tests",
                "  mercury-test users.tests.test_models",
                "  mercury-test users.tests.TestUserCreation"
            ]
            
            for example in examples:
                text = Text(example, style="green")
                console.print(text)
            
            console.print("\\nYou can specify app names, test modules, or even")
            console.print("individual test classes to run only what you need!")
            console.print(Rule(style="yellow"))
        else:
            # Fallback to plain text
            print("\\n" + "=" * 60)
            print("💡 Performance Tip")
            print("=" * 60)
            print(f"Your tests took {elapsed_time:.1f} seconds to complete.\\n")
            print("Test specific modules/files for faster results:\\n")
            print("  mercury-test users.tests")
            print("  mercury-test users.tests.test_models")
            print("  mercury-test users.tests.TestUserCreation\\n")
            print("You can specify app names, test modules, or even")
            print("individual test classes to run only what you need!")
            print("=" * 60)
    
    def _show_isolation_hint(self) -> None:
        """Show hint about test isolation issues."""
        if RICH_AVAILABLE:
            console = Console()
            console.print()
            console.print(Rule("⚠️ Test Isolation Issue Detected", style="yellow"))
            console.print("One or more tests failed possibly due to shared state between tests.\n")
            console.print("Common causes:", style="bold")
            console.print("  • Using setUpTestData() for mutable objects (friend requests, orders)")
            console.print("  • Tests modifying shared data without cleanup")
            console.print("  • Database state persisting between test methods\n")
            
            console.print("How to fix:", style="bold green")
            console.print("  1. Use setUp() instead of setUpTestData() for data that will be modified")
            console.print("  2. Use setUpTestData() only for read-only reference data (users, categories)")
            console.print("  3. Consider using TransactionTestCase for complex state management\n")
            
            # Check if learn plugin might be available
            console.print("Learn more:", style="bold yellow")
            console.print("  mercury-test --learn test-isolation", style="cyan")
            console.print(Rule(style="yellow"))
        else:
            # Fallback to plain text
            print("\n" + "=" * 60)
            print("⚠️ Test Isolation Issue Detected")
            print("=" * 60)
            print("One or more tests failed possibly due to shared state between tests.\n")
            print("Common causes:")
            print("  • Using setUpTestData() for mutable objects (friend requests, orders)")
            print("  • Tests modifying shared data without cleanup")
            print("  • Database state persisting between test methods\n")
            print("How to fix:")
            print("  1. Use setUp() instead of setUpTestData() for data that will be modified")
            print("  2. Use setUpTestData() only for read-only reference data (users, categories)")
            print("  3. Consider using TransactionTestCase for complex state management\n")
            print("Learn more: mercury-test --learn test-isolation")
            print("=" * 60)
    
    def mark_isolation_issue(self, test_name: str) -> None:
        """Mark that an isolation issue was detected for a test."""
        self._isolation_detected = True
        if test_name not in self._isolation_tests:
            self._isolation_tests.append(test_name)