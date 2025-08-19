"""
Panel update functions for Mercury Visual Display.

This module contains all the functions for updating individual display panels.
"""

import time
from typing import TYPE_CHECKING

from ..utils import format_time
from .constants import (
    GRADE_COLORS,
    SYMBOLS,
    Panel,
    Table,
    Text,
)
from .formatters import format_response_time, truncate_test_name
from ..enhanced_learning_tips import enhanced_learning_tips_db

if TYPE_CHECKING:
    from .base import MercuryVisualDisplay


def update_header(display: "MercuryVisualDisplay", message: str = None) -> None:
    """
    Update the header panel with title and message.

    Args:
        display: The visual display instance
        message: Optional message to show in header
    """
    if not display.layout:
        return

    header_text = Text()
    header_text.append("🚀 Django Mercury Visual Testing", style="bold cyan")

    # Add profile and hints status - use getattr for reliability
    profile = getattr(display, "profile", "expert")
    hints_enabled = getattr(display, "hints_enabled", False)

    status_parts = []

    # Add profile info if not default
    if profile != "expert":
        profile_name = profile.title()
        status_parts.append(f"📋 {profile_name} Profile")

    # Add hints status if enabled
    if hints_enabled:
        status_parts.append("💡 Hints Enabled")

    if status_parts:
        header_text.append(f"\n{' | '.join(status_parts)}", style="dim yellow")

    if message:
        header_text.append(f"\n{message}", style="dim")

    display.layout["header"].update(Panel(header_text, border_style="cyan"))


def update_progress(display: "MercuryVisualDisplay") -> None:
    """
    Update the progress bar and current test info.

    Args:
        display: The visual display instance
    """
    if not display.layout:
        return

    completed = display.stats["completed"]
    total = display.stats["total"]

    # Calculate progress
    if total > 0:
        progress = completed / total
        percent = progress * 100
    else:
        progress = 0
        percent = 0

    # Create progress bar
    bar_width = 60
    filled = int(bar_width * progress)
    bar = "█" * filled + "░" * (bar_width - filled)

    # Build progress panel content
    progress_text = Text()
    progress_text.append(f"Progress: {bar} {completed}/{total} ({percent:.1f}%)\n")

    # Show current test if available
    if display.current_test:
        elapsed = time.perf_counter() - display.current_test["start_time"]
        test_name = truncate_test_name(display.current_test["display_name"], 60)

        if display.current_test["is_mercury"]:
            progress_text.append(f"🎯 {test_name}", style="magenta")
        else:
            progress_text.append(f"Running: {test_name}")

        progress_text.append(f" ({elapsed:.1f}s)", style="dim")

    display.layout["progress"].update(
        Panel(progress_text, title="Test Progress", border_style="blue")
    )


def update_stats(display: "MercuryVisualDisplay") -> None:
    """
    Update the statistics panel.

    Args:
        display: The visual display instance
    """
    if not display.layout:
        return

    stats = display.stats

    # Create stats table
    table = Table(show_header=False, box=None, padding=0)
    table.add_column("Label", style="bold")
    table.add_column("Value", justify="right")

    # Add statistics rows
    table.add_row(f"{SYMBOLS['check']} Passed", str(stats["passed"]), style="green")
    table.add_row(f"{SYMBOLS['cross']} Failed", str(stats["failed"]), style="red")
    table.add_row(f"{SYMBOLS['fire']} Errors", str(stats["errors"]), style="red")
    table.add_row(f"{SYMBOLS['skip']} Skipped", str(stats["skipped"]), style="yellow")

    # Add performance metrics
    if stats["completed"] > 0:
        elapsed = time.time() - display.start_time
        rate = stats["completed"] / elapsed if elapsed > 0 else 0
        table.add_row("", "")  # Empty row for spacing
        table.add_row(f"{SYMBOLS['chart']} Rate", f"{rate:.1f}/s")

    # Add recent tests
    if display.test_history:
        table.add_row("", "")
        table.add_row("Recent Tests:", "")
        for test_info in list(display.test_history)[-3:]:
            name = truncate_test_name(test_info["name"], 40)
            time_str = format_response_time(test_info["time"] * 1000)
            table.add_row(f"  {name}", time_str, style="dim")

    display.layout["stats"].update(Panel(table, title="Test Statistics", border_style="green"))


def update_mercury_panel(display: "MercuryVisualDisplay") -> None:
    """
    Update the Mercury insights panel.

    Args:
        display: The visual display instance
    """
    if not display.layout:
        return

    content = Text()

    if display.stats["mercury_tests"] == 0:
        content.append("No Mercury tests detected yet...", style="dim")
    else:
        # Show Mercury test count
        content.append(f"Mercury Tests: {display.stats['mercury_tests']}\n")

        # Show metrics if available
        if display.metrics_tracker and display.metrics_tracker.mercury_test_count > 0:
            insights = display.metrics_tracker.get_insights()

            # Query stats
            if "query_range" in insights:
                content.append(f"\nQueries: {insights['query_range']}\n", style="cyan")

            # Response time stats
            if "time_range" in insights:
                content.append(f"Time: {insights['time_range']}\n", style="yellow")

            # N+1 detection
            if insights.get("n_plus_one_count", 0) > 0:
                content.append(
                    f"\n{SYMBOLS['warning']} N+1 Issues: {insights['n_plus_one_count']}\n",
                    style="red",
                )

            # Grade distribution
            if insights.get("grade_distribution"):
                content.append("\nGrades: ", style="bold")
                for grade, count in insights["grade_distribution"].items():
                    if count > 0:
                        color = GRADE_COLORS.get(grade, "white")
                        content.append(f"{grade}:{count} ", style=color)
        else:
            content.append("(Detailed metrics not captured)\n", style="dim")

        # Show recent Mercury insights
        if display.mercury_insights:
            content.append("\n\nRecent Insights:\n", style="bold")
            for insight in list(display.mercury_insights)[-3:]:
                content.append(f"• {insight}\n", style="dim")

    display.layout["mercury"].update(
        Panel(
            content,
            title=f"{SYMBOLS['target']} Mercury Insights",
            border_style="magenta",
        )
    )


def update_footer(display: "MercuryVisualDisplay") -> None:
    """
    Update the footer panel with log buffer and status.

    Args:
        display: The visual display instance
    """
    if not display.layout:
        return

    footer_content = Text()

    # Calculate elapsed time
    elapsed = time.time() - display.start_time

    # Add timing info
    footer_content.append(f"{SYMBOLS['timer']} Elapsed: {format_time(elapsed)}")

    # Add ETA if possible
    if display.stats["completed"] > 0 and display.stats["total"] > 0:
        rate = display.stats["completed"] / elapsed
        remaining = display.stats["total"] - display.stats["completed"]
        if rate > 0:
            eta = remaining / rate
            footer_content.append(f" | ETA: {format_time(eta)}")

    footer_content.append("\n")

    # Add separator
    footer_content.append("─" * 60 + "\n", style="dim")

    # Add log buffer
    if display.log_buffer:
        for log_line in display.log_buffer:
            footer_content.append(f"{log_line}\n", style="dim")
    else:
        footer_content.append("Waiting for test output...\n", style="dim")

    # Determine border style based on test status
    if display.stats["failed"] > 0 or display.stats["errors"] > 0:
        border_style = "red"
    elif display.stats["completed"] == display.stats["total"] and display.stats["total"] > 0:
        border_style = "green"
    else:
        border_style = "blue"

    display.layout["footer"].update(Panel(footer_content, border_style=border_style))


def update_learning_tips_panel(display: "MercuryVisualDisplay") -> None:
    """
    Update the learning tips panel for student mode.

    Args:
        display: The visual display instance
    """
    if not display.layout:
        return

    # Check if we should show learning tips (student mode)
    profile = getattr(display, "profile", "expert")
    if profile != "student":
        # For non-student modes, show placeholder or different content
        content = Text()
        content.append("Expert Mode\n\n", style="bold cyan")
        content.append("Advanced metrics\ncoming soon...", style="dim")

        display.layout["recent_tests"].update(
            Panel(content, title="⚡ Expert Panel", border_style="blue")
        )
        return

    # Get current test context for tips
    current_test_name = ""
    test_results = {}

    if display.current_test:
        current_test_name = display.current_test.get("name", "")
    elif hasattr(display, "test_history") and display.test_history:
        # Use most recent test if no current test
        current_test_name = display.test_history[-1].get("name", "")

    # Add some recent Mercury test results for context
    if hasattr(display, "metrics_tracker") and display.metrics_tracker:
        # Get recent performance data for context
        insights = display.metrics_tracker.get_insights()
        if insights:
            test_results = {
                "query_count": insights.get("avg_queries", 0),
                "grade": insights.get("worst_grade", "A"),
            }

    # Get contextual tip with enhanced data
    tip_data = enhanced_learning_tips_db.get_contextual_tip(current_test_name, test_results)
    countdown = enhanced_learning_tips_db.get_next_tip_countdown()

    # Build panel content
    content = Text()

    # Add the tip content (no duplicate header - panel title already shows it)
    content.append(tip_data["text"], style="white")

    # Track shown tips for final summary learn more section
    if not hasattr(display, "shown_tip_categories"):
        display.shown_tip_categories = set()
    display.shown_tip_categories.add(tip_data.get("category", "general"))

    # Add countdown
    if countdown > 0:
        content.append(f"\nNext tip in {countdown}s...", style="dim cyan")
    else:
        content.append(f"\nTip rotating...", style="dim cyan")

    display.layout["recent_tests"].update(
        Panel(content, title="📚 Learning Tips", border_style="yellow")
    )
