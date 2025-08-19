"""
Final summary display for Mercury Visual Display.

This module handles displaying the final test summary after completion.
"""

import time
from typing import TYPE_CHECKING

from ..utils import format_time
from .constants import GRADE_COLORS, SYMBOLS, Console, Panel, Text

if TYPE_CHECKING:
    from .base import MercuryVisualDisplay


def show_final_summary(display: "MercuryVisualDisplay", failures: int) -> None:
    """
    Show the final test summary after all tests complete.

    Args:
        display: The visual display instance
        failures: Number of test failures
    """
    try:
        # Stop the live display first
        display.stop_live_display()

        # Create a fresh console if needed
        if not display.console or display.live is not None:
            display.console = Console()
    except Exception:
        # If there's any issue, create a new console
        display.console = Console()

    # Create summary panel
    summary = Text()

    if failures == 0:
        summary.append(f"{SYMBOLS['check']} ALL TESTS PASSED!\n\n", style="bold green")
    else:
        summary.append(f"{SYMBOLS['cross']} {failures} TESTS FAILED\n\n", style="bold red")

    # Add statistics
    _add_statistics(display, summary)

    # Add Mercury performance info
    _add_mercury_info(display, summary)

    # Add learning resources for students with educational plugins (always show, not just when Mercury tests detected)
    if display.profile == "student" and _has_educational_plugins(display):
        _add_learning_resources(summary)
        _add_contextual_learn_more(display, summary)

    # Add timing
    elapsed = time.time() - display.start_time
    summary.append(
        f"\n{SYMBOLS['timer']} Total Time: {format_time(elapsed)}\n",
        style="dim",
    )

    # Add isolation issues if detected
    _add_isolation_issues(display, summary)

    # Add failed tests
    _add_failed_tests(display, summary)

    # Display final panel
    panel = Panel(
        summary,
        title="Test Execution Complete",
        border_style="green" if failures == 0 else "red",
        padding=(1, 2),
    )

    try:
        display.console.print("\n")
        display.console.print(panel)
    except Exception:
        # Fallback to basic print if Rich fails
        _print_fallback_summary(display)

    # Show investigation hints
    _show_investigation_hints(display)

    # Show profile switch hint for students with educational plugins
    _show_profile_switch_hint(display)


def _add_statistics(display: "MercuryVisualDisplay", summary: Text) -> None:
    """Add test statistics to summary."""
    stats = display.stats
    summary.append(f"Total: {stats['total']} tests\n")
    summary.append(f"Passed: {stats['passed']}\n", style="green")
    summary.append(f"Failed: {stats['failed']}\n", style="red")
    summary.append(f"Errors: {stats['errors']}\n", style="red")
    summary.append(f"Skipped: {stats['skipped']}\n", style="yellow")


def _add_mercury_info(display: "MercuryVisualDisplay", summary: Text) -> None:
    """Add Mercury performance information to summary."""
    if display.stats["mercury_tests"] > 0:
        summary.append(f"\n{SYMBOLS['target']} Mercury Performance:\n", style="magenta")
        summary.append(f"Mercury Tests: {display.stats['mercury_tests']}\n")

        # Check if we have meaningful metrics captured
        has_meaningful_metrics = display.metrics_tracker.mercury_test_count > 0 and (
            display.metrics_tracker.grade_distribution or display.metrics_tracker.test_metrics
        )

        # Note if metrics weren't captured (likely using C extensions)
        if not has_meaningful_metrics:
            # Check if we saw Mercury tests but couldn't capture metrics
            mercury_tests_seen = getattr(display, "_mercury_tests_seen", set())
            if mercury_tests_seen or display.stats["mercury_tests"] > 0:
                summary.append(
                    "(Detailed metrics not captured)\n",
                    style="dim",
                )
            else:
                summary.append(
                    "(No metrics data available)\n",
                    style="dim",
                )

        # Get metrics summary from tracker
        display_metrics = display.metrics_tracker.format_for_display()

        # Show ranges
        if "query_range" in display_metrics:
            summary.append(f"Query Range: {display_metrics['query_range']}\n")
        if "time_range" in display_metrics:
            summary.append(f"Time Range: {display_metrics['time_range']}\n")

        # Show grade distribution
        if "grades" in display_metrics:
            summary.append("\nGrade Distribution:\n", style="bold")
            for grade_info in display_metrics["grades"].split():
                grade, count = grade_info.split(":")
                color = GRADE_COLORS.get(grade, "white")
                summary.append(f"  {grade}: {count} tests", style=color)
                summary.append("\n")

        # Show worst performers
        worst_performers = display.metrics_tracker.get_worst_performers(limit=10)
        if worst_performers:
            summary.append(
                f"\n{SYMBOLS['red_circle']} Tests That Need Optimization:\n",
                style="bold red",
            )

            # Import hints system
            from ..hints import PerformanceHints

            for i, worst in enumerate(worst_performers):
                # Parse the test name from the formatted string
                if ":" in worst:
                    parts = worst.split(":")
                    test_part = parts[0].strip().lstrip("❌").lstrip("⚠️").strip()
                    issue_part = ":".join(parts[1:]).strip()

                    # Make the issue description more actionable
                    if "Grade D" in issue_part or "Grade F" in issue_part:
                        # Extract the specific metrics from either parentheses or dash format
                        metrics_part = None
                        if "(" in issue_part and ")" in issue_part:
                            # Original format: "Grade D (28 queries, 22ms)"
                            grade_part = issue_part.split("(")[0].strip()
                            metrics_part = issue_part.split("(")[1].rstrip(")")
                        elif " - " in issue_part:
                            # Display format: "Grade D - 28 queries, 22ms"
                            grade_part = issue_part.split(" - ")[0].strip()
                            metrics_part = " - ".join(issue_part.split(" - ")[1:]).strip()
                        else:
                            # Fallback format
                            grade_part = issue_part

                        if metrics_part:
                            summary.append(
                                f"  • {test_part}: {grade_part} - {metrics_part}\n", style="red"
                            )

                            # Add hints if enabled and for top 3 worst performers
                            if display.hints_enabled and i < 3:
                                _add_performance_hints(summary, metrics_part, display.profile)
                        else:
                            summary.append(f"  • {test_part}: {issue_part}\n", style="red")
                    else:
                        summary.append(f"  • {test_part}: {issue_part}\n", style="red")
                else:
                    summary.append(f"  {worst}\n", style="red")

        # Show N+1 detection
        if display.stats["n_plus_one_detected"] > 0:
            summary.append(
                f"\n{SYMBOLS['warning']} N+1 Queries Found: {display.stats['n_plus_one_detected']}\n",
                style="bold red",
            )


def _add_isolation_issues(display: "MercuryVisualDisplay", summary: Text) -> None:
    """Add test isolation issues to summary."""
    if hasattr(display, "isolation_issues") and display.isolation_issues:
        summary.append(
            f"\n{SYMBOLS['warning']} Test Isolation Issues Detected:\n",
            style="bold yellow",
        )
        summary.append(
            "These tests may be failing due to shared state between tests:\n",
            style="dim",
        )
        for test_name, issue in list(display.isolation_issues.items())[:5]:
            short_name = test_name.split(".")[-1] if "." in test_name else test_name
            summary.append(f"  • {short_name}\n", style="yellow")
            summary.append(f"    Issue: {issue}\n", style="dim")
        if len(display.isolation_issues) > 5:
            summary.append(
                f"  ... and {len(display.isolation_issues) - 5} more\n",
                style="dim",
            )


def _add_failed_tests(display: "MercuryVisualDisplay", summary: Text) -> None:
    """Add failed tests to summary."""
    if display.failed_tests:
        summary.append(f"\n{SYMBOLS['cross']} Failed Tests:\n", style="red")
        for test in display.failed_tests[:10]:  # Show first 10
            if "[ISOLATION]" in test:
                # Remove the marker for display but show warning icon
                clean_test = test.replace(" [ISOLATION]", "")
                summary.append(f"  • {clean_test} {SYMBOLS['warning']}\n", style="yellow")
            else:
                summary.append(f"  • {test}\n")
        if len(display.failed_tests) > 10:
            summary.append(f"  ... and {len(display.failed_tests) - 10} more\n")


def _print_fallback_summary(display: "MercuryVisualDisplay") -> None:
    """Print a basic summary if Rich fails."""
    print("\n" + "=" * 60)
    print("Test Execution Complete")
    print("=" * 60)
    print(f"Total: {display.stats['total']} tests")
    print(f"Passed: {display.stats['passed']}")
    print(f"Failed: {display.stats['failed']}")
    print(f"Errors: {display.stats['errors']}")
    print(f"Skipped: {display.stats['skipped']}")
    print("=" * 60)


def _show_investigation_hints(display: "MercuryVisualDisplay") -> None:
    """Show hints for investigating test failures."""
    if not display.failed_tests:
        try:
            display.console.print("\n")
        except Exception:
            print("")
        return

    first_test = display.failed_tests[0]

    # Clean isolation marker if present
    is_isolation = "[ISOLATION]" in first_test
    first_test = first_test.replace(" [ISOLATION]", "")

    # Extract just the test method name for -k pattern
    if "." in first_test:
        test_method = first_test.split(".")[1]  # Get method name after the dot
    else:
        test_method = first_test

    try:
        display.console.print("")  # Empty line for spacing

        if is_isolation:
            display.console.print(
                f"{SYMBOLS['bulb']} Possible test isolation issue detected!",
                style="bold yellow",
            )
            display.console.print(
                "To verify if this is an isolation issue, run the test alone:",
                style="yellow",
            )
            display.console.print(
                f"    python manage.py test -k {test_method}",
                style="bold cyan",
            )
            display.console.print(
                "\nIf it passes alone but fails in the suite, it's an isolation issue.",
                style="dim",
            )

            # Suggest learning resource
            display.console.print(
                f"\n{SYMBOLS['book']} Learn how to fix test isolation issues:",
                style="yellow",
            )
            display.console.print(
                "    mercury-test --learn test-isolation",
                style="bold yellow",
            )
        else:
            display.console.print(
                f"{SYMBOLS['bulb']} To investigate the failure, run:",
                style="yellow",
            )
            display.console.print(
                f"    python manage.py test -k {test_method}",
                style="bold cyan",
            )

        display.console.print("")  # Empty line at end
    except Exception:
        # Fallback to basic print for investigation hints
        print("\nTo investigate the failure, run:")
        print(f"    python manage.py test -k {test_method}")
        if is_isolation:
            print(f"\n{SYMBOLS['book']} Learn how to fix test isolation issues:")
            print("    mercury-test --learn test-isolation")


def _add_performance_hints(summary: Text, metrics_part: str, profile: str) -> None:
    """Add performance hints based on test metrics."""
    from ..hints import PerformanceHints
    import re

    # Parse metrics from various formats:
    # "45Q, 250ms" or "28 queries, 22ms" or "N+1 detected, 30Q, 200ms"
    query_count = 0
    response_time_ms = 0
    memory_mb = 0
    n_plus_one = False

    # Extract query count - handle both "30Q" and "28 queries" formats
    query_patterns = [
        r"(\d+)Q",  # "30Q"
        r"(\d+)\s+queries?",  # "28 queries" or "1 query"
    ]

    for pattern in query_patterns:
        query_match = re.search(pattern, metrics_part, re.IGNORECASE)
        if query_match:
            query_count = int(query_match.group(1))
            break

    # Extract response time - handle both "250ms" and "22ms" formats
    time_match = re.search(r"(\d+(?:\.\d+)?)\s*ms", metrics_part, re.IGNORECASE)
    if time_match:
        response_time_ms = float(time_match.group(1))

    # Extract memory usage
    memory_match = re.search(r"(\d+(?:\.\d+)?)\s*MB", metrics_part, re.IGNORECASE)
    if memory_match:
        memory_mb = float(memory_match.group(1))

    # Check for N+1 indicators
    if "N+1" in metrics_part or "n+1" in metrics_part.lower():
        n_plus_one = True

    # Get relevant hints
    hints = PerformanceHints.get_hints_for_metrics(
        query_count=query_count,
        response_time_ms=response_time_ms,
        memory_mb=memory_mb,
        n_plus_one=n_plus_one,
        profile=profile,
    )

    # Display hints
    if hints:
        summary.append(f"    💡 Tip: {hints[0]}\n", style="dim cyan")


def _add_learning_resources(summary: Text) -> None:
    """Add learning resources for student profile."""
    from ..hints import PerformanceHints

    summary.append(f"\n{SYMBOLS['book']} Learning Resources:\n", style="bold cyan")

    resources = PerformanceHints.get_learning_resources("student")
    if resources:
        # Show first 2 resources to avoid overwhelming
        for resource in resources[:2]:
            summary.append(f"  • {resource}\n", style="dim cyan")

    # Always show the learn command
    summary.append("  • mercury-test --learn performance\n", style="dim cyan")


def _has_educational_plugins(display) -> bool:
    """Check if educational plugins (hints or learn) are enabled."""
    try:
        # Check if display has the necessary attributes to determine plugin status
        if hasattr(display, "hints_enabled"):
            return display.hints_enabled

        # Fallback: check if config manager is available and has educational plugins
        if hasattr(display, "config_manager"):
            enabled_plugins = display.config_manager.get_enabled_plugins()
            return "hints" in enabled_plugins or "learn" in enabled_plugins

        # For student profile, always default to True to ensure educational content shows
        # This ensures that even if plugin detection fails, students get educational content
        if display.profile == "student":
            return True

        return False
    except Exception:
        # Fallback: show educational content for student profile
        return display.profile == "student"


def _add_contextual_learn_more(display, summary: Text) -> None:
    """Add contextual learn more commands based on shown tip categories."""
    # For student mode, always show learning suggestions (not just when Mercury tests detected)
    if display.profile != "student":
        return

    summary.append(f"\n{SYMBOLS['bulb']} Continue Learning:\n", style="bold yellow")

    # Generate learn more commands based on shown categories (if any)
    learn_more_commands = set()

    # If we have shown tip categories, add contextual suggestions
    if hasattr(display, "shown_tip_categories") and display.shown_tip_categories:
        for category in display.shown_tip_categories:
            if category == "performance":
                learn_more_commands.update(
                    [
                        "mercury-test --learn django-orm",
                        "mercury-test --learn query-optimization",
                        "mercury-test --learn n-plus-one-patterns",
                    ]
                )
            elif category == "testing":
                learn_more_commands.update(
                    [
                        "mercury-test --learn testing-patterns",
                        "mercury-test --learn test-organization",
                        "mercury-test --learn test-data-patterns",
                    ]
                )
            elif category == "api":
                learn_more_commands.update(
                    [
                        "mercury-test --learn drf-optimization",
                        "mercury-test --learn api-design",
                        "mercury-test --learn serializer-optimization",
                    ]
                )
            elif category == "django":
                learn_more_commands.update(
                    [
                        "mercury-test --learn django-models",
                        "mercury-test --learn django-best-practices",
                        "mercury-test --learn django-signals",
                    ]
                )

    # Always add general learning commands for student mode
    learn_more_commands.update(
        [
            "mercury-test --learn django-models",
            "mercury-test --learn django-signals",
            "mercury-test --learn django-best-practices",
            "mercury-test --learn user-optimization",
        ]
    )

    # Show up to 4 commands to avoid overwhelming
    for cmd in list(learn_more_commands)[:4]:
        summary.append(f"  • {cmd}\n", style="dim yellow")


def _show_profile_switch_hint(display: "MercuryVisualDisplay") -> None:
    """Show hint to switch to expert profile for students with educational plugins."""
    # Only show for student mode with educational plugins enabled
    if display.profile == "student" and _has_educational_plugins(display):
        try:
            display.console.print(
                f"\n💡 Switch to Expert Profile for faster tests but less education! mercury-test --profile expert",
                style="dim cyan",
            )
        except Exception:
            # Fallback to basic print
            print(
                "\n💡 Switch to Expert Profile for faster tests but less education! mercury-test --profile expert"
            )
