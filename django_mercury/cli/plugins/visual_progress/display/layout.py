"""
Layout management for Mercury Visual Display.

This module handles creating and configuring the Rich layout structure.
"""

from .constants import (
    FOOTER_SIZE,
    HEADER_SIZE,
    MAIN_SIZE,
    PROGRESS_SIZE,
    RICH_AVAILABLE,
    Layout,
)


def create_display_layout() -> Layout:
    """
    Create the Rich layout structure for the visual display.

    Returns:
        Configured Layout object with header, progress, main, and footer sections
    """
    if not RICH_AVAILABLE:
        return None

    layout = Layout()

    # Split into vertical sections
    layout.split_column(
        Layout(name="header", size=HEADER_SIZE),
        Layout(name="progress", size=PROGRESS_SIZE),
        Layout(name="main", size=MAIN_SIZE),
        Layout(name="footer", size=FOOTER_SIZE),
    )

    # Split main into three panels: stats, learning tips, mercury
    # Give learning tips more space so educational content isn't cut off
    layout["main"].split_row(
        Layout(name="stats", ratio=2),
        Layout(name="recent_tests", ratio=2),  # More space for learning tips
        Layout(name="mercury", ratio=1),
    )

    return layout


def create_simple_layout() -> Layout:
    """
    Create a simplified layout for minimal displays.

    Returns:
        Simplified Layout with fewer sections
    """
    if not RICH_AVAILABLE:
        return None

    layout = Layout()

    # Simple two-panel layout
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
    )

    return layout


def update_layout_sizes(layout: Layout, test_count: int) -> None:
    """
    Dynamically adjust layout sizes based on test count.

    Args:
        layout: Layout to adjust
        test_count: Number of tests to run
    """
    if not layout:
        return

    # Adjust sizes for very large test suites
    if test_count > 1000:
        # Make progress bar smaller for large suites
        try:
            layout["progress"].size = 3
            layout["main"].size = MAIN_SIZE + 1
        except KeyError:
            pass  # Layout section might not exist
    elif test_count < 10:
        # Make main area larger for small suites
        try:
            layout["main"].size = MAIN_SIZE + 2
            layout["footer"].size = FOOTER_SIZE - 2
        except KeyError:
            pass
