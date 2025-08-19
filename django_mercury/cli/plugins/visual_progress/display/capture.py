"""
Output capture utilities for Mercury Visual Display.

This module handles capturing and redirecting stdout/stderr during test execution.
"""

import io
import re
import sys
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .base import MercuryVisualDisplay


class StdoutCapture(io.StringIO):
    """
    Custom StringIO that captures stdout and feeds it to the display.

    This allows us to capture print statements from tests and show them
    in the visual display's log buffer.
    """

    def __init__(self, display: "MercuryVisualDisplay", is_stderr: bool = False):
        """
        Initialize the capture stream.

        Args:
            display: The visual display instance
            is_stderr: Whether this is capturing stderr (vs stdout)
        """
        super().__init__()
        self.display = display
        self.is_stderr = is_stderr

    def write(self, text: str) -> int:
        """
        Capture written text and add to display log buffer.

        Args:
            text: Text being written to stdout/stderr

        Returns:
            Number of characters written
        """
        if text and text.strip():
            # Clean up the text and add to log buffer
            cleaned = clean_ansi_codes(text.strip())
            if cleaned and not should_filter_output(cleaned):
                self.display.add_to_log_buffer(cleaned[:100])  # Limit length
        return super().write(text)

    def flush(self) -> None:
        """Flush the buffer."""
        pass


def clean_ansi_codes(text: str) -> str:
    """
    Remove ANSI escape codes from text.

    Args:
        text: Text potentially containing ANSI codes

    Returns:
        Cleaned text without ANSI codes
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def should_filter_output(text: str) -> bool:
    """
    Check if output should be filtered from the log.

    Some outputs are noisy and not useful for the visual display.

    Args:
        text: Output text to check

    Returns:
        True if the output should be filtered out
    """
    # Filter out common noise
    filters = [
        "DEBUG:",  # Debug messages from our own code
        "Creating test database",
        "Destroying test database",
        "Using existing test database",
        "Type 'yes' if you would like to try",
        "Got an error creating the test database",
    ]

    return any(f in text for f in filters)


class OutputCapture:
    """
    Context manager for capturing stdout/stderr during test execution.
    """

    def __init__(self, display: Optional["MercuryVisualDisplay"] = None):
        """
        Initialize output capture.

        Args:
            display: Optional visual display to send captured output to
        """
        self.display = display
        self.original_stdout = None
        self.original_stderr = None
        self.stdout_capture = None
        self.stderr_capture = None

    def __enter__(self):
        """Start capturing output."""
        if self.display:
            self.original_stdout = sys.stdout
            self.original_stderr = sys.stderr
            self.stdout_capture = StdoutCapture(self.display, is_stderr=False)
            self.stderr_capture = StdoutCapture(self.display, is_stderr=True)
            sys.stdout = self.stdout_capture
            sys.stderr = self.stderr_capture
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop capturing output."""
        if self.display and self.original_stdout:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
