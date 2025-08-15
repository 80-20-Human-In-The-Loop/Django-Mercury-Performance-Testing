"""
Output Capture Module for Visual Progress Plugin

Captures all stdout/stderr output early in the process to prevent
it from interfering with the visual display.
"""

import io
import logging
import re
import sys
from collections import deque


class OutputCapture:
    """
    Captures and manages stdout/stderr output for the visual test runner.

    This class starts capturing output immediately when instantiated,
    preventing any output from appearing on screen before the visual
    display is ready.
    """

    def __init__(self, max_buffer_size: int = 1000):
        """
        Initialize the output capture system.

        Args:
            max_buffer_size: Maximum number of lines to buffer
        """
        self.max_buffer_size = max_buffer_size
        self.buffer = deque(maxlen=max_buffer_size)

        # Store original streams
        self.original_stdout = None
        self.original_stderr = None

        # Create capture streams
        self.stdout_capture = None
        self.stderr_capture = None

        # Patterns to suppress
        self.suppress_patterns = [
            r"✅ Mercury Framework loaded",
            r"System check identified",
            r"UnorderedObjectListWarning",
            r"Phase [AB]:",
            r"Friendship simulation complete",
            r"created user.*populated their profile",
            r"Not enough users to create friendships",
            r"WARNING:django",
            r"Ran \d+ tests in",
            r"FAILED \(failures=\d+\)",
            r"^OK$",
            r"^FAILED$",
            r"Successfully created user",
            r"request\(s\) were accepted",
            r"Phase A:",
            r"Phase B:",
            r"User creation finished",
            r"Attempting to create",
            r"populated their profile",
            r"/home/mathew/.local/lib",  # Suppress library warnings
            r"pagination\.py:\d+:",  # Suppress pagination warnings
            r"❌ Test Failure:",  # Suppress individual test failure messages
            r"💥 Test Import/Setup Error",  # Suppress error messages
            r"Creating test database",
            r"Destroying test database",
        ]

        # Control flags
        self.capturing = False
        self.suppress_all = False

        # Store all output for post-test display
        self.full_log = []
        self.save_to_file = False
        self.log_file_path = "test_output.log"

    def start_capture(
        self, suppress_all: bool = True, save_to_file: bool = False
    ):
        """
        Start capturing all output.

        Args:
            suppress_all: If True, suppress all output. If False, only suppress patterns.
            save_to_file: If True, save suppressed output to a log file.
        """
        if self.capturing:
            return

        self.suppress_all = suppress_all
        self.save_to_file = save_to_file

        # Store original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create capture objects
        self.stdout_capture = StreamCapture(self, is_stderr=False)
        self.stderr_capture = StreamCapture(self, is_stderr=True)

        # Replace system streams
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture

        # Also suppress Django logging
        logging.getLogger("django").setLevel(logging.CRITICAL)
        logging.getLogger("django.request").setLevel(logging.CRITICAL)
        logging.getLogger("django.db.backends").setLevel(logging.CRITICAL)

        self.capturing = True

    def stop_capture(self):
        """Stop capturing output and restore original streams."""
        if not self.capturing:
            return

        # Save logs to file if requested
        if self.save_to_file and self.full_log:
            try:
                with open(self.log_file_path, "w") as f:
                    f.write("\n".join(self.full_log))
                    f.write("\n")
            except Exception:
                pass  # Silently fail if can't write log file

        # Restore original streams
        if self.original_stdout:
            sys.stdout = self.original_stdout
            self.original_stdout = None

        if self.original_stderr:
            sys.stderr = self.original_stderr
            self.original_stderr = None

        self.capturing = False

    def should_suppress(self, text: str) -> bool:
        """
        Check if a line of text should be suppressed.

        Args:
            text: The text to check

        Returns:
            True if the text should be suppressed
        """
        if self.suppress_all:
            return True

        # Check against suppression patterns
        for pattern in self.suppress_patterns:
            if re.search(pattern, text):
                return True

        return False

    def add_line(self, line: str, is_stderr: bool = False):
        """
        Add a line to the buffer if not suppressed.

        Args:
            line: The line to add
            is_stderr: Whether this came from stderr
        """
        # Clean up the line
        line = line.strip()
        if not line:
            return

        # Always save to full log for later
        self.full_log.append(line)

        # Check if we should suppress this line from display
        if self.should_suppress(line):
            return

        # Add to buffer with stderr marker if needed
        if is_stderr:
            line = f"[stderr] {line}"

        self.buffer.append(line)

    def get_buffer(self) -> list[str]:
        """
        Get the current buffer contents.

        Returns:
            List of buffered lines
        """
        return list(self.buffer)

    def get_recent(self, n: int = 3) -> list[str]:
        """
        Get the most recent n lines from the buffer.

        Args:
            n: Number of lines to return

        Returns:
            List of recent lines
        """
        if len(self.buffer) <= n:
            return list(self.buffer)
        return list(self.buffer)[-n:]

    def clear_buffer(self):
        """Clear the buffer."""
        self.buffer.clear()

    def handoff_to_display(self, display):
        """
        Hand off output control to the visual display.

        Args:
            display: The visual display object to hand off to
        """
        # Transfer recent buffer contents to display
        recent_lines = self.get_recent(3)
        for line in recent_lines:
            if hasattr(display, "add_to_log_buffer"):
                display.add_to_log_buffer(line)

        # Stop our capture but let display take over
        self.stop_capture()

        # Clear the buffer
        self.clear_buffer()

    def __enter__(self):
        """Context manager entry."""
        self.start_capture()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_capture()


class StreamCapture(io.StringIO):
    """
    Custom stream that captures output and sends it to the OutputCapture.
    """

    def __init__(self, capture: OutputCapture, is_stderr: bool = False):
        """
        Initialize the stream capture.

        Args:
            capture: The OutputCapture instance
            is_stderr: Whether this is capturing stderr
        """
        super().__init__()
        self.capture = capture
        self.is_stderr = is_stderr
        self.line_buffer = ""

    def write(self, text: str) -> int:
        """
        Capture writes and send to the output capture.

        Args:
            text: Text to write

        Returns:
            Number of characters written
        """
        # If capturing is disabled, write to original stream
        if not self.capture.capturing:
            original = (
                self.capture.original_stderr
                if self.is_stderr
                else self.capture.original_stdout
            )
            if original:
                return original.write(text)
            return len(text)

        # Buffer lines and send complete lines to capture
        self.line_buffer += text
        while "\n" in self.line_buffer:
            line, self.line_buffer = self.line_buffer.split("\n", 1)
            if line.strip():  # Only add non-empty lines
                self.capture.add_line(line, self.is_stderr)

        return len(text)

    def flush(self):
        """Flush any buffered content."""
        # If there's content in the line buffer, add it
        if self.line_buffer and self.line_buffer.strip():
            self.capture.add_line(self.line_buffer, self.is_stderr)
            self.line_buffer = ""

        # Flush original stream if available
        original = (
            self.capture.original_stderr
            if self.is_stderr
            else self.capture.original_stdout
        )
        if original and hasattr(original, "flush"):
            original.flush()

    def isatty(self) -> bool:
        """Check if this is a TTY (needed for some libraries)."""
        original = (
            self.capture.original_stderr
            if self.is_stderr
            else self.capture.original_stdout
        )
        if original and hasattr(original, "isatty"):
            return original.isatty()
        return False

    def fileno(self) -> int:
        """Get file descriptor (needed for some operations)."""
        original = (
            self.capture.original_stderr
            if self.is_stderr
            else self.capture.original_stdout
        )
        if original and hasattr(original, "fileno"):
            return original.fileno()
        raise io.UnsupportedOperation("fileno")


# Global instance for early capture
_global_capture: OutputCapture | None = None


def get_global_capture() -> OutputCapture:
    """Get or create the global output capture instance."""
    global _global_capture
    if _global_capture is None:
        _global_capture = OutputCapture()
    return _global_capture


def start_early_capture(save_to_file: bool = False):
    """Start capturing output as early as possible."""
    capture = get_global_capture()
    capture.start_capture(suppress_all=True, save_to_file=save_to_file)
    return capture


def show_suppressed_logs(limit: int = 50):
    """Show the suppressed logs after tests complete."""
    capture = get_global_capture()
    if capture and capture.full_log:
        print("\n" + "=" * 60)
        print(f"SUPPRESSED TEST OUTPUT (last {limit} lines):")
        print("=" * 60)
        for line in capture.full_log[-limit:]:
            print(line)
        print("=" * 60)
        if capture.save_to_file:
            print(f"Full log saved to: {capture.log_file_path}")
        print("=" * 60 + "\n")


def stop_early_capture():
    """Stop the early capture."""
    global _global_capture
    if _global_capture:
        _global_capture.stop_capture()
        _global_capture = None
