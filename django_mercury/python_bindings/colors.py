# backend/performance_testing/python_bindings/colors.py - Color Palette for Performance Visualization
# Defines a consistent and beautiful color scheme for visualizing performance metrics in the terminal.

# --- Standard Library Imports ---
import os
import sys
from enum import Enum
from typing import Dict, Optional, Tuple
from functools import lru_cache

# --- Local Imports ---
try:
    from .constants import ENV_VARS
    from .logging_config import get_logger
except ImportError:
    # Fallback for direct execution
    ENV_VARS = {
        "FORCE_COLOR": "FORCE_COLOR",
        "NO_COLOR": "NO_COLOR",
        "CLICOLOR": "CLICOLOR",
        "CLICOLOR_FORCE": "CLICOLOR_FORCE",
    }
    import logging

    get_logger = lambda name: logging.getLogger(name)

logger = get_logger("colors")

# --- Color Palette Definition ---


class EduLiteColorScheme:
    """
    A centralized color palette for EduLite's performance visualization tools.

        This class defines a consistent set of colors for different performance
        statuses, metrics, and UI components to ensure a clear and intuitive
        visual language.
    """

    # -- Performance Status Colors --
    EXCELLENT = "#73bed3"  # Light cyan-blue
    GOOD = "#4f8fba"  # Medium blue
    ACCEPTABLE = "#3c5e8b"  # Darker blue

    # -- Warning and Critical Colors --
    WARNING = "#de9e41"  # Golden yellow
    SLOW = "#be772b"  # Orange
    CRITICAL = "#a53030"  # Red

    # -- Analysis and Optimization Colors --
    SUCCESS = "#75a743"  # Green
    INFO = "#a8ca58"  # Light green
    OPTIMIZATION = "#468232"  # Dark green
    HINT = "#25562e"  # Very dark green

    # -- UI and Text Colors --
    BACKGROUND = "#151d28"  # Dark blue-gray
    TEXT = "#e7d5b3"  # Warm light text
    FADE = "#394a50"  # Medium gray
    BORDER = "#394a50"  # Medium gray
    ACCENT = "#c65197"  # Purple
    SECONDARY = "#577277"  # Secondary gray

    # -- Metric-Specific Colors --
    MEMORY_EXCELLENT = "#df84a5"
    MEMORY_GOOD = "#c65197"
    MEMORY_WARNING = "#a23e8c"
    MEMORY_CRITICAL = "#752438"
    QUERY_EFFICIENT = "#e8c170"
    QUERY_ACCEPTABLE = "#de9e41"
    QUERY_INEFFICIENT = "#be772b"
    QUERY_PROBLEMATIC = "#884b2b"

    # -- Trend Indicators --
    TRENDING_UP = "#a53030"  # Red (negative trend)
    TRENDING_DOWN = "#75a743"  # Green (positive trend)
    TRENDING_STABLE = "#4f8fba"  # Blue (stable trend)


class ColorMode(Enum):
    """
    Enumeration for terminal color output modes.

    Attributes:
        AUTO: Automatically detect if the terminal supports color.
        ALWAYS: Always output color codes.
        NEVER: Never output color codes.
        RICH: Use the `rich` library for color formatting.
    """

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"
    RICH = "rich"


# --- Colorization Utility ---


class PerformanceColors:
    """
    A utility class for applying colors to performance data based on the active color mode.
    """

    def __init__(self, mode: ColorMode = ColorMode.AUTO):
        """
        Initializes the PerformanceColors utility.

        Args:
            mode (ColorMode): The color mode to use for output.
        """
        self.mode = mode
        self._supports_color = self._detect_color_support()

    @lru_cache(maxsize=1)
    def _detect_color_support(self) -> bool:
        """Detects if the terminal environment supports color output.

        This method is cached to avoid repeated environment variable lookups.
        Respects standard color control environment variables:
        - NO_COLOR: Disables color output
        - FORCE_COLOR or CLICOLOR_FORCE: Forces color output
        - CLICOLOR: Enables/disables color (0 = disabled)
        """
        if self.mode == ColorMode.NEVER:
            logger.debug("Color mode set to NEVER")
            return False
        if self.mode in [ColorMode.ALWAYS, ColorMode.RICH]:
            logger.debug(f"Color mode set to {self.mode.value}")
            return True

        # Check environment variables
        if os.environ.get(ENV_VARS["FORCE_COLOR"]) or os.environ.get(ENV_VARS["CLICOLOR_FORCE"]):
            logger.debug("Color output forced by environment variable")
            return True
        if os.environ.get(ENV_VARS["NO_COLOR"]) or os.environ.get(ENV_VARS["CLICOLOR"]) == "0":
            logger.debug("Color output disabled by environment variable")
            return False

        # Check if output is a TTY
        is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        logger.debug(f"TTY detection: {is_tty}")
        return is_tty

    def colorize(self, text: str, color: str, bold: bool = False) -> str:
        """
        Applies color and optional bold styling to text.

        Args:
            text (str): The text to colorize.
            color (str): The hex color code (e.g., "#73bed3").
            bold (bool): Whether to apply bold styling.

        Returns:
            str: The colorized text, or plain text if colors are disabled.
        """
        if not self._supports_color:
            return text
        return (
            self._colorize_rich(text, color, bold)
            if self.mode == ColorMode.RICH
            else self._colorize_ansi(text, color, bold)
        )

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Converts a hex color string to an RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def _colorize_ansi(self, text: str, color: str, bold: bool = False) -> str:
        """Colorizes text using ANSI 24-bit color escape codes."""
        r, g, b = self._hex_to_rgb(color)
        color_code = f"\033[38;2;{r};{g};{b}m"
        bold_code = "\033[1m" if bold else ""
        reset_code = "\033[0m"
        return f"{bold_code}{color_code}{text}{reset_code}"

    def _colorize_rich(self, text: str, color: str, bold: bool = False) -> str:
        """Colorizes text using the `rich` library for better compatibility."""
        try:
            from rich.console import Console
            from rich.text import Text

            text_obj = Text(text)
            text_obj.stylize(f"color({color})")
            if bold:
                text_obj.stylize("bold")
            console = Console(file=None)
            with console.capture() as capture:
                console.print(text_obj, end="")
            return capture.get()
        except ImportError:
            return self._colorize_ansi(text, color, bold)  # Fallback to ANSI

    # -- Color Mapping Methods --

    def status_color(self, status: str) -> str:
        """
        Retrieves the appropriate color for a given performance status.

        Args:
            status (str): The performance status (e.g., 'excellent', 'critical').

        Returns:
            str: The hex color code for the status.
        """
        return getattr(EduLiteColorScheme, status.upper(), EduLiteColorScheme.TEXT)

    def trend_color(self, trend: str) -> str:
        """
        Retrieves the appropriate color for a performance trend.

        Args:
            trend (str): The trend direction (e.g., 'improving', 'degrading').

        Returns:
            str: The hex color code for the trend.
        """
        trend_map = {
            "up": EduLiteColorScheme.TRENDING_UP,
            "down": EduLiteColorScheme.TRENDING_DOWN,
            "stable": EduLiteColorScheme.TRENDING_STABLE,
            "improving": EduLiteColorScheme.TRENDING_DOWN,
            "degrading": EduLiteColorScheme.TRENDING_UP,
        }
        return trend_map.get(trend.lower(), EduLiteColorScheme.TEXT)

    def memory_color(self, memory_mb: float) -> str:
        """Determines the color for memory usage based on its value."""
        if memory_mb <= 20:
            return EduLiteColorScheme.MEMORY_EXCELLENT
        if memory_mb <= 50:
            return EduLiteColorScheme.MEMORY_GOOD
        if memory_mb <= 100:
            return EduLiteColorScheme.MEMORY_WARNING
        return EduLiteColorScheme.MEMORY_CRITICAL

    def query_color(self, query_count: int) -> str:
        """Determines the color for a database query count."""
        if query_count <= 3:
            return EduLiteColorScheme.QUERY_EFFICIENT
        if query_count <= 7:
            return EduLiteColorScheme.QUERY_ACCEPTABLE
        if query_count <= 15:
            return EduLiteColorScheme.QUERY_INEFFICIENT
        return EduLiteColorScheme.QUERY_PROBLEMATIC

    # -- Formatting Methods --

    def format_performance_status(self, status: str, bold: bool = True) -> str:
        """
        Formats a performance status string with the appropriate color.

        Args:
            status (str): The performance status string.
            bold (bool): Whether to apply bold styling.

        Returns:
            str: The formatted and colorized status text.
        """
        return self.colorize(status.upper(), self.status_color(status), bold)

    def format_metric_value(
        self, value: float, unit: str, threshold: Optional[float] = None
    ) -> str:
        """
        Formats and colorizes a metric value based on its unit and an optional threshold.

        Args:
            value (float): The metric value.
            unit (str): The unit of the metric (e.g., 'ms', 'MB').
            threshold (Optional[float]): An optional threshold to base the color on.

        Returns:
            str: The formatted and colorized metric string.
        """
        color = EduLiteColorScheme.TEXT
        unit_lower = unit.lower()
        if unit_lower in ["ms", "milliseconds"]:
            if value <= 50:
                color = EduLiteColorScheme.EXCELLENT
            elif value <= 100:
                color = EduLiteColorScheme.GOOD
            elif value <= 300:
                color = EduLiteColorScheme.ACCEPTABLE
            elif value <= 500:
                color = EduLiteColorScheme.SLOW
            else:
                color = EduLiteColorScheme.CRITICAL
        elif unit_lower in ["mb", "megabytes"]:
            color = self.memory_color(value)
        elif unit_lower in ["queries", "query", "q"]:
            color = self.query_color(int(value))

        if threshold is not None:
            if value <= threshold * 0.7:
                color = EduLiteColorScheme.EXCELLENT
            elif value <= threshold:
                color = EduLiteColorScheme.GOOD
            elif value <= threshold * 1.2:
                color = EduLiteColorScheme.WARNING
            else:
                color = EduLiteColorScheme.CRITICAL

        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
        return self.colorize(f"{formatted_value}{unit}", color)


# --- Global Instance and Helper Functions ---

colors = PerformanceColors()


def get_status_icon(status: str) -> str:
    """
    Retrieves an emoji icon for a given performance status.

    Args:
        status (str): The performance status string.

    Returns:
            str: A single emoji character representing the status.
    """
    status_icons = {
        "excellent": "🚀",
        "good": "✅",
        "acceptable": "⚠️",
        "warning": "⚠️",
        "slow": "🐌",
        "critical": "🚨",
        "success": "🎯",
        "info": "💡",
        "optimization": "🔧",
        "trending_up": "📈",
        "trending_down": "📉",
        "trending_stable": "➡️",
    }
    return status_icons.get(status.lower(), "📊")


# --- Test Execution ---

if __name__ == "__main__":
    # Example usage to demonstrate the color system.
    print("🎨 EduLite Color Palette Test")
    print("=" * 50)

    for mode in [ColorMode.ALWAYS, ColorMode.NEVER]:
        color_instance = PerformanceColors(mode)
        print(f"\n--- Mode: {mode.value} ---")

        statuses = ["excellent", "good", "acceptable", "slow", "critical"]
        for status in statuses:
            colored_status = color_instance.format_performance_status(status)
            icon = get_status_icon(status)
            print(f"  {icon} {colored_status}")

        print("\n--- Metric Examples ---")
        print(f"  - Response time: {color_instance.format_metric_value(45.2, 'ms')}")
        print(f"  - Memory usage: {color_instance.format_metric_value(67.8, 'MB')}")
        print(f"  - Query count: {color_instance.format_metric_value(3, 'queries')}")

    print(f"\n🎨 Palette Preview:")
    print(
        f"  - Excellence: {colors.colorize(EduLiteColorScheme.EXCELLENT, EduLiteColorScheme.EXCELLENT)}"
    )
    print(f"  - Success: {colors.colorize(EduLiteColorScheme.SUCCESS, EduLiteColorScheme.SUCCESS)}")
    print(f"  - Warning: {colors.colorize(EduLiteColorScheme.WARNING, EduLiteColorScheme.WARNING)}")
    print(
        f"  - Critical: {colors.colorize(EduLiteColorScheme.CRITICAL, EduLiteColorScheme.CRITICAL)}"
    )
