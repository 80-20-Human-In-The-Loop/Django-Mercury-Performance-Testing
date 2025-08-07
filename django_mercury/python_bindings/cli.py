"""Django Mercury CLI - Interactive Educational Testing Framework.

This module provides the command-line interface for Django Mercury's
educational testing mode, embodying the 80-20 Human-in-the-Loop philosophy.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from django_mercury import __version__ as VERSION
from django_mercury.python_bindings.educational_guidance import (
    EduLiteColorScheme,
)


class MercuryEducationalCLI:
    """Interactive educational CLI for Django Mercury performance testing."""

    def __init__(self) -> None:
        """Initialize the educational CLI with rich console if available."""
        self.console = Console() if RICH_AVAILABLE else None
        self.color_scheme = EduLiteColorScheme()
        self.progress_file = Path.home() / ".django_mercury" / "progress.json"
        self.progress_data: Dict[str, Any] = self._load_progress()
        self.educational_mode = False
        self.agent_mode = False

    def _load_progress(self) -> Dict[str, Any]:
        """Load user's learning progress from local storage."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "concepts_learned": [],
            "quiz_scores": {},
            "optimization_attempts": 0,
            "level": "beginner",
        }

    def _save_progress(self) -> None:
        """Save user's learning progress to local storage."""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, "w") as f:
            json.dump(self.progress_data, f, indent=2)

    def display_welcome(self) -> None:
        """Display welcome message with EduLite branding."""
        if not self.console:
            print("\n📚 Django Mercury Educational Mode\n" + "=" * 40)
            return

        welcome_text = Text()
        welcome_text.append("📚 ", style="bold yellow")
        welcome_text.append("Django Mercury ", style="bold cyan")
        welcome_text.append("Educational Mode\n", style="bold green")
        welcome_text.append("\nMaking Testing a Learning Journey", style="italic")

        panel = Panel(
            welcome_text,
            title="[bold]Welcome to Interactive Learning[/bold]",
            border_style="cyan",
            expand=False,
        )
        self.console.print(panel)

    def run_educational_test(self, test_path: Optional[str] = None) -> int:
        """Run tests in educational mode with interactive learning.

        Args:
            test_path: Optional specific test path to run

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        self.display_welcome()

        if self.console:
            self.console.print(
                f"\n[bold]Your Learning Level:[/bold] {self.progress_data['level'].capitalize()}"
            )
            self.console.print(
                f"[bold]Concepts Mastered:[/bold] {len(self.progress_data['concepts_learned'])}"
            )

        # Import Django test runner here to avoid circular imports
        try:
            import django
            from django.conf import settings
            from django.test.utils import get_runner

            django.setup()
            TestRunner = get_runner(settings)
        except ImportError:
            if self.console:
                self.console.print(
                    "[red]Error:[/red] Django is not installed or configured."
                )
            else:
                print("Error: Django is not installed or configured.")
            return 1

        # Create custom test runner with educational hooks
        class EducationalTestRunner(TestRunner):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                self.cli = kwargs.get("cli_instance")

            def setup_test_environment(self, **kwargs: Any) -> None:
                """Set up test environment with educational mode enabled."""
                super().setup_test_environment(**kwargs)
                # Enable educational guidance globally
                os.environ["MERCURY_EDUCATIONAL_MODE"] = "true"
                if self.cli and self.cli.agent_mode:
                    os.environ["MERCURY_AGENT_MODE"] = "true"

        # Run tests with educational runner
        runner = EducationalTestRunner(
            verbosity=2,
            interactive=True,
            cli_instance=self,
        )

        test_labels = [test_path] if test_path else []
        failures = runner.run_tests(test_labels)

        # Save progress after test run
        self._save_progress()

        if self.console:
            self.console.print(
                "\n[bold green]✅ Learning session complete![/bold green]"
            )
            self._show_learning_summary()

        return 0 if failures == 0 else 1

    def _show_learning_summary(self) -> None:
        """Display a summary of what was learned in this session."""
        if not self.console:
            return

        table = Table(title="Learning Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Concepts Learned", str(len(self.progress_data["concepts_learned"])))
        table.add_row("Current Level", self.progress_data["level"].capitalize())
        table.add_row(
            "Optimization Attempts", str(self.progress_data["optimization_attempts"])
        )

        if self.progress_data["quiz_scores"]:
            avg_score = sum(self.progress_data["quiz_scores"].values()) / len(
                self.progress_data["quiz_scores"]
            )
            table.add_row("Average Quiz Score", f"{avg_score:.1f}%")

        self.console.print(table)

    def run_agent_mode(self, test_path: Optional[str] = None) -> int:
        """Run tests in agent mode with structured JSON output.

        Args:
            test_path: Optional specific test path to run

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        self.agent_mode = True
        os.environ["MERCURY_AGENT_MODE"] = "true"

        # Structured output for agents
        output = {
            "version": VERSION,
            "mode": "agent",
            "educational_content": {},
            "performance_metrics": {},
            "optimization_suggestions": [],
        }

        try:
            # Run tests and capture results
            result = self.run_educational_test(test_path)
            output["success"] = result == 0
        except Exception as e:
            output["success"] = False
            output["error"] = str(e)

        # Output structured JSON for agent consumption
        print(json.dumps(output, indent=2))
        return 0 if output.get("success") else 1


def main() -> None:
    """Main entry point for Django Mercury CLI."""
    parser = argparse.ArgumentParser(
        description="Django Mercury - Performance Testing with Educational Guidance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mercury-analyze --edu                  # Run all tests in educational mode
  mercury-analyze --edu myapp.tests      # Run specific tests educationally
  mercury-analyze --agent                # Run in agent mode (JSON output)
  mercury-analyze --version              # Show version information

Learn more at: https://github.com/smattymatty/Django-Mercury-Performance-Testing
        """,
    )

    parser.add_argument(
        "test_path",
        nargs="?",
        help="Specific test module or TestCase to run",
    )

    parser.add_argument(
        "--edu",
        "--educational",
        action="store_true",
        help="Enable interactive educational mode with quizzes and tutorials",
    )

    parser.add_argument(
        "--agent",
        action="store_true",
        help="Enable agent mode with structured JSON output for automation",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Django Mercury {VERSION}",
        help="Show version information",
    )

    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Reset learning progress and start fresh",
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = MercuryEducationalCLI()

    # Handle progress reset
    if args.reset_progress:
        cli.progress_data = {
            "concepts_learned": [],
            "quiz_scores": {},
            "optimization_attempts": 0,
            "level": "beginner",
        }
        cli._save_progress()
        if cli.console:
            cli.console.print("[green]✅ Learning progress reset successfully![/green]")
        else:
            print("✅ Learning progress reset successfully!")
        return

    # Determine mode and run
    if args.agent:
        sys.exit(cli.run_agent_mode(args.test_path))
    elif args.edu:
        cli.educational_mode = True
        sys.exit(cli.run_educational_test(args.test_path))
    else:
        # Default to standard test run with basic educational guidance
        if cli.console:
            cli.console.print(
                "[yellow]Tip:[/yellow] Use --edu flag for interactive learning mode!"
            )
        else:
            print("Tip: Use --edu flag for interactive learning mode!")
        sys.exit(cli.run_educational_test(args.test_path))


if __name__ == "__main__":
    main()
