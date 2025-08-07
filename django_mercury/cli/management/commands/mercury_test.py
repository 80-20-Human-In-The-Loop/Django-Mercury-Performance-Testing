"""Django management command for Mercury educational testing.

This command extends Django's test command with interactive educational
features following the 80-20 Human-in-the-Loop philosophy.
"""

import json
import os
import sys
from typing import Any, List

from django.core.management.base import BaseCommand
from django.test.runner import DiscoverRunner

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, IntPrompt
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False



class EducationalTestRunner(DiscoverRunner):
    """Extended Django test runner with educational features."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize educational test runner with Mercury monitoring."""
        self.educational_mode = kwargs.pop("educational_mode", False)
        self.agent_mode = kwargs.pop("agent_mode", False)
        self.console = kwargs.pop("console", None)
        self.quiz_system = kwargs.pop("quiz_system", None)
        self.progress_tracker = kwargs.pop("progress_tracker", None)
        super().__init__(*args, **kwargs)

    def setup_test_environment(self, **kwargs: Any) -> None:
        """Set up test environment with educational features enabled."""
        super().setup_test_environment(**kwargs)

        # Enable Mercury monitoring
        os.environ["MERCURY_MONITORING"] = "true"

        if self.educational_mode:
            os.environ["MERCURY_EDUCATIONAL_MODE"] = "true"
            if self.console and RICH_AVAILABLE:
                self.console.print(
                    Panel(
                        "[bold cyan]🎓 Educational Mode Active[/bold cyan]\n"
                        "Tests will pause at learning moments",
                        border_style="green",
                    )
                )

        if self.agent_mode:
            os.environ["MERCURY_AGENT_MODE"] = "true"

    def run_tests(
        self, test_labels: List[str], **kwargs: Any
    ) -> int:
        """Run tests with educational interventions.

        Args:
            test_labels: Test labels to run
            **kwargs: Additional arguments

        Returns:
            Number of failed tests
        """
        if self.educational_mode and self.console:
            self.console.print(
                "\n[bold]Starting Educational Test Session[/bold]"
            )
            self.console.print(
                "I'll pause to explain performance issues and test your understanding.\n"
            )

        # Run the actual tests
        failures = super().run_tests(test_labels, **kwargs)

        # Show educational summary if in educational mode
        if self.educational_mode and not self.agent_mode:
            self._show_educational_summary(failures)

        return failures

    def _show_educational_summary(self, failures: int) -> None:
        """Display educational summary after test run."""
        if not self.console or not RICH_AVAILABLE:
            print("\n" + "=" * 50)
            print("Educational Summary")
            print("=" * 50)
            print(f"Tests completed with {failures} failures")
            return

        # Create summary table
        table = Table(title="🎓 Learning Session Complete", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Result", style="green" if failures == 0 else "yellow")

        table.add_row("Tests Run", str(self.testsRun) if hasattr(self, "testsRun") else "N/A")
        table.add_row("Failures", str(failures))

        if self.progress_tracker:
            concepts = self.progress_tracker.get_session_concepts()
            table.add_row("Concepts Covered", str(len(concepts)))

            if concepts:
                table.add_row("Topics", ", ".join(concepts[:3]))

        self.console.print("\n")
        self.console.print(table)

        if failures == 0:
            self.console.print(
                "\n[bold green]✅ Excellent work! All tests passed.[/bold green]"
            )
        else:
            self.console.print(
                f"\n[yellow]📚 {failures} test(s) need attention. "
                "Review the educational guidance above.[/yellow]"
            )


class Command(BaseCommand):
    """Django management command for Mercury educational testing."""

    help = "Run tests with Django Mercury's interactive educational mode"

    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument(
            "args",
            metavar="test_label",
            nargs="*",
            help="Module, TestCase or test method to run",
        )

        parser.add_argument(
            "--edu",
            "--educational",
            action="store_true",
            dest="educational",
            help="Enable interactive educational mode with pauses and quizzes",
        )

        parser.add_argument(
            "--agent",
            action="store_true",
            dest="agent",
            help="Enable agent mode with structured JSON output",
        )

        parser.add_argument(
            "--level",
            choices=["beginner", "intermediate", "advanced"],
            default="beginner",
            help="Set educational difficulty level (default: beginner)",
        )

        parser.add_argument(
            "--no-quiz",
            action="store_true",
            dest="no_quiz",
            help="Skip interactive quizzes (educational mode only)",
        )

        parser.add_argument(
            "--reset-progress",
            action="store_true",
            dest="reset_progress",
            help="Reset learning progress before running tests",
        )

        # Standard Django test options
        parser.add_argument(
            "--failfast",
            action="store_true",
            help="Stop on first test failure",
        )

        parser.add_argument(
            "--verbosity",
            type=int,
            choices=[0, 1, 2, 3],
            default=1,
            help="Verbosity level",
        )

        parser.add_argument(
            "--keepdb",
            action="store_true",
            help="Preserve test database between runs",
        )

    def handle(self, *test_labels: str, **options: Any) -> None:
        """Handle the mercury_test command.

        Args:
            *test_labels: Test labels to run
            **options: Command options
        """
        console = Console() if RICH_AVAILABLE else None
        educational_mode = options.get("educational", False)
        agent_mode = options.get("agent", False)
        level = options.get("level", "beginner")
        no_quiz = options.get("no_quiz", False)
        reset_progress = options.get("reset_progress", False)

        # Initialize components
        quiz_system = None
        progress_tracker = None

        if educational_mode or agent_mode:
            # Import educational components
            try:
                from django_mercury.cli.educational.progress_tracker import (
                    ProgressTracker,
                )
                from django_mercury.cli.educational.quiz_system import QuizSystem

                progress_tracker = ProgressTracker(level=level)

                if reset_progress:
                    progress_tracker.reset()
                    if console:
                        console.print(
                            "[green]✅ Learning progress reset![/green]"
                        )

                if educational_mode and not no_quiz:
                    quiz_system = QuizSystem(
                        console=console,
                        level=level,
                        progress_tracker=progress_tracker,
                    )

            except ImportError as e:
                if console:
                    console.print(
                        f"[yellow]Warning: Educational components not fully installed: {e}[/yellow]"
                    )

        if educational_mode and console:
            # Display welcome message
            welcome = Panel(
                Text.from_markup(
                    "[bold cyan]📚 Django Mercury Educational Testing[/bold cyan]\n\n"
                    f"[yellow]Level:[/yellow] {level.capitalize()}\n"
                    f"[yellow]Quiz Mode:[/yellow] {'Disabled' if no_quiz else 'Enabled'}\n\n"
                    "[italic]Making Testing a Learning Journey[/italic]"
                ),
                title="Welcome",
                border_style="cyan",
            )
            console.print(welcome)

        # Prepare test runner kwargs
        runner_kwargs = {
            "verbosity": options.get("verbosity", 1),
            "interactive": not agent_mode,
            "failfast": options.get("failfast", False),
            "keepdb": options.get("keepdb", False),
            "educational_mode": educational_mode,
            "agent_mode": agent_mode,
            "console": console,
            "quiz_system": quiz_system,
            "progress_tracker": progress_tracker,
        }

        # Create and configure the test runner
        runner = EducationalTestRunner(**runner_kwargs)

        # Run the tests
        failures = runner.run_tests(list(test_labels) or None)

        if agent_mode:
            # Output structured JSON for agents
            output = {
                "success": failures == 0,
                "failures": failures,
                "educational_mode": educational_mode,
                "level": level,
            }

            if progress_tracker:
                output["progress"] = {
                    "concepts_learned": progress_tracker.get_all_concepts(),
                    "session_concepts": progress_tracker.get_session_concepts(),
                }

            print(json.dumps(output, indent=2))

        # Save progress if we have a tracker
        if progress_tracker:
            progress_tracker.save()

        # Exit with appropriate code
        if failures:
            sys.exit(1)
