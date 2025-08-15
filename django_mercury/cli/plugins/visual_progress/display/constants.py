"""
Constants and common imports for Mercury Visual Display.

This module contains all the display constants, symbols, and Rich library imports.
"""

# Try to import rich for advanced visuals
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = object
    Layout = object
    Panel = object
    Live = object
    Table = object
    Text = object
    Rule = object

# Display symbols
SYMBOLS = {
    "check": "✅",
    "cross": "❌",
    "warning": "⚠️",
    "skip": "⏭️",
    "fire": "💥",
    "target": "🎯",
    "chart": "📈",
    "timer": "⏱️",
    "bulb": "💡",
    "book": "📚",
    "search": "🔍",
    "rocket": "🚀",
    "snail": "🐌",
    "red_circle": "🔴",
    "orange_circle": "🟠",
    "stats": "📊",
}

# Grade colors for Rich styling
GRADE_COLORS = {
    "S": "bright_cyan",
    "A+": "bright_green",
    "A": "green",
    "B": "yellow",
    "C": "orange1",
    "D": "red",
    "F": "bright_red",
}

# Display configuration
REFRESH_RATE = 1  # Updates per second for live display
HANGING_TEST_THRESHOLD = 30.0  # Seconds before warning about hanging test
LOG_BUFFER_SIZE = 3  # Number of log lines to keep in buffer
TEST_HISTORY_SIZE = 5  # Number of recent tests to show
MERCURY_INSIGHTS_SIZE = 5  # Number of insights to keep

# Layout sizes
HEADER_SIZE = 3
PROGRESS_SIZE = 4
MAIN_SIZE = 14
FOOTER_SIZE = 6
