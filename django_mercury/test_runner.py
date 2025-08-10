"""
Django Mercury Educational Test Runner

This module provides a custom Django test runner that adds interactive
educational features following the 80-20 Human-in-the-Loop philosophy.

Usage in settings.py:
    import sys
    if '--edu' in sys.argv:
        TEST_RUNNER = 'django_mercury.test_runner.EducationalTestRunner'

Then run:
    python manage.py test --edu
"""

import os
import sys
from typing import Any, List, Optional
from unittest import TestSuite, TextTestResult

from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment, teardown_test_environment

# Check for rich availability
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


class EducationalTestResult(TextTestResult):
    """Custom test result that tracks educational metrics."""
    
    def __init__(self, *args, educational_monitor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.educational_monitor = educational_monitor
        self.performance_issues = []
        self.concepts_covered = set()
        self.quiz_results = []
    
    def addFailure(self, test, err):
        """Override to capture performance-related failures."""
        super().addFailure(test, err)
        
        # Check if this is a performance failure
        if self.educational_monitor and err and len(err) > 1:
            exc_info = err[1]
            if "Performance threshold exceeded" in str(exc_info):
                self.performance_issues.append({
                    'test': test,
                    'error': str(exc_info),
                    'type': self._detect_issue_type(str(exc_info))
                })
                
                # Trigger educational intervention if in interactive mode
                if self.educational_monitor.interactive_mode:
                    self.educational_monitor.handle_performance_issue(test, str(exc_info))
    
    def _detect_issue_type(self, error_msg: str) -> str:
        """Detect the type of performance issue from error message."""
        if "Query count" in error_msg:
            return "n_plus_one"
        elif "Response time" in error_msg:
            return "slow_response"
        elif "Memory" in error_msg:
            return "memory_leak"
        elif "Cache" in error_msg:
            return "cache_miss"
        else:
            return "general_performance"


class EducationalTestRunner(DiscoverRunner):
    """
    Custom Django test runner with interactive educational features.
    
    This runner adds educational interventions during test execution,
    helping developers learn about performance optimization while testing.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the educational test runner."""
        # Check for --edu flag OR MERCURY_EDU environment variable
        self.educational_mode = '--edu' in sys.argv or os.environ.get('MERCURY_EDU') == '1'
        
        # Remove --edu from argv so Django doesn't complain
        if '--edu' in sys.argv:
            sys.argv = [arg for arg in sys.argv if arg != '--edu']
            
        # Initialize parent
        super().__init__(*args, **kwargs)
        
        # Educational components
        self.console = None
        self.quiz_system = None
        self.progress_tracker = None
        self.educational_monitor = None
        
        if self.educational_mode:
            self._setup_educational_mode()
    
    def _setup_educational_mode(self):
        """Set up educational components and environment."""
        # Set environment variable for other components to detect
        os.environ['MERCURY_EDUCATIONAL_MODE'] = 'true'
        os.environ['MERCURY_MONITORING'] = 'true'
        
        # Initialize console if rich is available
        if RICH_AVAILABLE:
            self.console = Console()
        
        # Try to initialize educational components
        try:
            from django_mercury.cli.educational.quiz_system import QuizSystem
            from django_mercury.cli.educational.progress_tracker import ProgressTracker
            from django_mercury.python_bindings.educational_monitor import EducationalMonitor
            
            # Determine difficulty level from environment or default
            level = os.environ.get('MERCURY_EDU_LEVEL', 'beginner')
            
            # Initialize components
            self.progress_tracker = ProgressTracker(level=level)
            
            if self.console:
                self.quiz_system = QuizSystem(
                    console=self.console,
                    level=level,
                    progress_tracker=self.progress_tracker
                )
            
            self.educational_monitor = EducationalMonitor(
                console=self.console,
                quiz_system=self.quiz_system,
                progress_tracker=self.progress_tracker,
                interactive_mode=not self.failfast  # Don't pause if failfast is set
            )
            
            # Show welcome message
            self._show_welcome_message(level)
            
        except ImportError as e:
            if self.verbosity >= 1:
                print(f"Warning: Some educational components not available: {e}")
                print("Educational mode will run with limited features.")
    
    def _show_welcome_message(self, level: str):
        """Display welcome message for educational mode."""
        if self.console and RICH_AVAILABLE:
            welcome_panel = Panel(
                Text.from_markup(
                    "[bold cyan]🎓 Django Mercury Educational Testing Mode[/bold cyan]\n\n"
                    "[yellow]Interactive Learning Experience Active[/yellow]\n\n"
                    f"📚 Difficulty Level: [green]{level.capitalize()}[/green]\n"
                    f"🎯 Performance Monitoring: [green]Active[/green]\n"
                    f"🧠 Interactive Quizzes: [green]{'Enabled' if self.quiz_system else 'Limited'}[/green]\n"
                    f"📊 Progress Tracking: [green]{'Enabled' if self.progress_tracker else 'Disabled'}[/green]\n\n"
                    "[italic]Tests will pause at learning moments to help you understand\n"
                    "performance issues and learn optimization techniques.[/italic]\n\n"
                    "[dim]Tip: Set MERCURY_EDU_LEVEL=intermediate or advanced for more depth[/dim]"
                ),
                title="[bold]Welcome to Educational Testing[/bold]",
                border_style="cyan",
                padding=(1, 2)
            )
            self.console.print(welcome_panel)
            self.console.print()
        else:
            print("\n" + "="*60)
            print("🎓 Django Mercury Educational Testing Mode")
            print("="*60)
            print(f"Level: {level.capitalize()}")
            print("Tests will pause at learning moments")
            print("="*60 + "\n")
    
    def setup_test_environment(self, **kwargs):
        """Set up the test environment with educational features."""
        super().setup_test_environment(**kwargs)
        
        if self.educational_mode and self.console:
            self.console.print("[dim]Setting up test environment...[/dim]")
    
    def build_suite(self, test_labels=None, **kwargs):
        """Build test suite with educational annotations."""
        suite = super().build_suite(test_labels, **kwargs)
        
        if self.educational_mode and self.console:
            test_count = suite.countTestCases()
            self.console.print(
                f"[green]✓[/green] Found [cyan]{test_count}[/cyan] test(s) to run\n"
            )
        
        return suite
    
    def run_suite(self, suite, **kwargs):
        """Run test suite with educational interventions."""
        # Create custom result class if in educational mode
        if self.educational_mode:
            # Store the educational monitor reference
            educational_monitor = self.educational_monitor
            
            # Create a custom test result that includes educational monitor
            class CustomEducationalTestResult(EducationalTestResult):
                def __init__(self, stream, descriptions, verbosity):
                    super().__init__(stream, descriptions, verbosity, 
                                   educational_monitor=educational_monitor)
            
            # Use our custom result class
            kwargs['resultclass'] = CustomEducationalTestResult
        
        # Run the tests
        result = super().run_suite(suite, **kwargs)
        
        # Show educational summary
        if self.educational_mode:
            self._show_educational_summary(result)
        
        return result
    
    def _show_educational_summary(self, result):
        """Display educational summary after test run."""
        if not self.educational_mode:
            return
        
        # Extract educational metrics
        performance_issues = getattr(result, 'performance_issues', [])
        concepts = getattr(result, 'concepts_covered', set())
        quiz_results = getattr(result, 'quiz_results', [])
        
        if self.console and RICH_AVAILABLE:
            # Create summary table
            table = Table(
                title="🎓 Educational Testing Summary",
                show_header=True,
                title_style="bold cyan"
            )
            table.add_column("Metric", style="cyan", width=30)
            table.add_column("Value", style="green")
            
            # Add metrics
            table.add_row("Total Tests Run", str(result.testsRun))
            table.add_row("Tests Passed", str(result.testsRun - len(result.failures) - len(result.errors)))
            table.add_row("Tests Failed", str(len(result.failures)))
            table.add_row("Tests with Errors", str(len(result.errors)))
            
            if performance_issues:
                table.add_row("Performance Issues Found", str(len(performance_issues)))
                
                # Count issue types
                issue_types = {}
                for issue in performance_issues:
                    issue_type = issue.get('type', 'unknown')
                    issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                
                for issue_type, count in issue_types.items():
                    table.add_row(f"  - {issue_type.replace('_', ' ').title()}", str(count))
            
            if self.progress_tracker:
                session_concepts = self.progress_tracker.get_session_concepts()
                if session_concepts:
                    table.add_row("Concepts Covered", str(len(session_concepts)))
                    table.add_row("Topics", ", ".join(list(session_concepts)[:3]))
                
                # Show quiz performance if available
                if quiz_results:
                    correct = sum(1 for r in quiz_results if r.get('correct', False))
                    accuracy = (correct / len(quiz_results)) * 100 if quiz_results else 0
                    table.add_row("Quiz Accuracy", f"{accuracy:.0f}%")
            
            self.console.print("\n")
            self.console.print(table)
            
            # Show motivational message
            if len(result.failures) == 0 and len(result.errors) == 0:
                self.console.print(
                    "\n[bold green]🎉 Excellent! All tests passed![/bold green]"
                )
            elif performance_issues:
                self.console.print(
                    f"\n[yellow]📚 Found {len(performance_issues)} learning opportunities. "
                    "Review the guidance above to improve performance.[/yellow]"
                )
            
            # Save progress
            if self.progress_tracker:
                self.progress_tracker.save()
                self.console.print(
                    "\n[dim]Progress saved to ~/.django_mercury/learning_progress.json[/dim]"
                )
        else:
            # Simple text output
            print("\n" + "="*60)
            print("Educational Testing Summary")
            print("="*60)
            print(f"Tests Run: {result.testsRun}")
            print(f"Failures: {len(result.failures)}")
            print(f"Errors: {len(result.errors)}")
            
            if performance_issues:
                print(f"Performance Issues: {len(performance_issues)}")
            
            print("="*60)
    
    def teardown_test_environment(self, **kwargs):
        """Clean up test environment."""
        super().teardown_test_environment(**kwargs)
        
        # Clean up educational mode environment variable
        if self.educational_mode:
            os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)
            
            if self.console:
                self.console.print(
                    "\n[dim]Educational testing session complete.[/dim]\n"
                )


# Convenience function for backwards compatibility
def run_tests_with_education(test_labels=None, verbosity=1, interactive=True, **kwargs):
    """
    Run tests with educational mode enabled.
    
    This is a convenience function that can be called directly.
    """
    # Force educational mode
    os.environ['MERCURY_EDUCATIONAL_MODE'] = 'true'
    
    # Create runner
    runner = EducationalTestRunner(
        verbosity=verbosity,
        interactive=interactive,
        **kwargs
    )
    
    # Run tests
    failures = runner.run_tests(test_labels or [])
    
    return failures