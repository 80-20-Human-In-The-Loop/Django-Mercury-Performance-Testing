"""
Mercury Visual Display Module.

A modular display system for showing test execution progress with Rich.
"""

# Import main classes for backward compatibility
from .base import MercuryVisualDisplay
from .capture import OutputCapture, StdoutCapture
from .constants import GRADE_COLORS, RICH_AVAILABLE, SYMBOLS
from .formatters import (
    calculate_simple_mercury_grade,
    format_query_info,
    format_response_time,
    format_test_name_for_display,
    guess_test_module_path,
    truncate_test_name,
)
from .layout import create_display_layout, create_simple_layout
from .state import DisplayRenderState, OutputCaptureState, TestExecutionTracker
from .summary import show_final_summary

# For convenience, also export Rich components if available
if RICH_AVAILABLE:
    from .constants import Console, Layout, Live, Panel, Table, Text

__all__ = [
    # Main display class
    "MercuryVisualDisplay",
    # Capture utilities
    "StdoutCapture",
    "OutputCapture",
    # Constants
    "RICH_AVAILABLE",
    "SYMBOLS",
    "GRADE_COLORS",
    # Formatters
    "format_test_name_for_display",
    "guess_test_module_path",
    "calculate_simple_mercury_grade",
    "format_query_info",
    "format_response_time",
    "truncate_test_name",
    # Layout
    "create_display_layout",
    "create_simple_layout",
    # Summary
    "show_final_summary",
]

# Add Rich components to exports if available
if RICH_AVAILABLE:
    __all__.extend(["Console", "Layout", "Live", "Panel", "Table", "Text"])
