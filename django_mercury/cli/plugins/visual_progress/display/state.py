"""
State management classes for Mercury Visual Display.

This module provides composition classes to manage different aspects of
display state, reducing the complexity of the main MercuryVisualDisplay class.
"""

import time
from collections import deque
from typing import Any

from .constants import (
    HANGING_TEST_THRESHOLD,
    LOG_BUFFER_SIZE,
    MERCURY_INSIGHTS_SIZE,
    TEST_HISTORY_SIZE,
    Console,
    Layout,
    Live,
)


class TestExecutionTracker:
    """
    Tracks test execution state and history.

    This class manages all test-related state including statistics,
    current test info, history, and failure tracking.
    """

    def __init__(self):
        """Initialize test execution tracker."""
        # Statistics dictionary
        self.stats = {
            "total": 0,
            "completed": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "mercury_tests": 0,
            "total_queries": 0,
            "total_response_time": 0,
            "n_plus_one_detected": 0,
            "performance_grades": {
                "S": 0,
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0,
                "F": 0,
            },
            "test_counter": 0,  # For display update frequency
        }

        # Test tracking
        self.current_test: dict[str, Any] | None = None
        self.test_history = deque(maxlen=TEST_HISTORY_SIZE)
        self.failed_tests: list[str] = []
        self.isolation_issues: dict[str, str] = {}

        # Mercury insights
        self.mercury_insights = deque(maxlen=MERCURY_INSIGHTS_SIZE)

        # Timing
        self.start_time = time.time()
        self.last_test_update = time.time()

    def update_test_start(self, test_name: str, is_mercury: bool, display_name: str) -> None:
        """
        Update state when a test starts.

        Args:
            test_name: Full test name
            is_mercury: Whether this is a Mercury test
            display_name: Formatted display name
        """
        self.current_test = {
            "name": test_name,
            "is_mercury": is_mercury,
            "start_time": time.perf_counter(),
            "display_name": display_name,
        }

        self.last_test_update = time.time()

        if is_mercury:
            self.stats["mercury_tests"] += 1

        # Increment test counter for display update frequency
        self.stats["test_counter"] += 1

    def update_test_complete(
        self,
        test_name: str,
        duration: float,
        passed: bool,
        is_mercury: bool = False,
    ) -> None:
        """
        Update state when a test completes.

        Args:
            test_name: Full test name
            duration: Test execution time
            passed: Whether test passed
            is_mercury: Whether this was a Mercury test
        """
        self.stats["completed"] += 1

        # Add to test history
        self.test_history.append(
            {
                "name": test_name.split(".")[-1],
                "time": duration,
                "passed": passed,
            }
        )

    def record_success(self) -> None:
        """Record a test success."""
        self.stats["passed"] += 1

    def record_failure(self, test_name: str, isolation_issue: str | None = None) -> None:
        """
        Record a test failure.

        Args:
            test_name: Full test name
            isolation_issue: Optional isolation issue description
        """
        self.stats["failed"] += 1

        if isolation_issue:
            # Mark as isolation issue
            self.failed_tests.append(f"{test_name} [ISOLATION]")
            self.isolation_issues[test_name] = isolation_issue
        else:
            self.failed_tests.append(test_name)

    def record_error(self, test_name: str) -> None:
        """
        Record a test error.

        Args:
            test_name: Full test name
        """
        self.stats["errors"] += 1
        self.failed_tests.append(test_name)

    def record_skip(self) -> None:
        """Record a test skip."""
        self.stats["skipped"] += 1

    def add_mercury_insight(self, insight: str) -> None:
        """
        Add a Mercury performance insight.

        Args:
            insight: Insight message
        """
        self.mercury_insights.append(insight)

    def update_mercury_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Update Mercury-specific metrics.

        Args:
            metrics: Dictionary of Mercury metrics
        """
        self.stats["total_queries"] += metrics.get("query_count", 0)
        self.stats["total_response_time"] += metrics.get("response_time_ms", 0)

        if metrics.get("n_plus_one_detected"):
            self.stats["n_plus_one_detected"] += 1

        # Track grade distribution
        grade = metrics.get("grade", "")
        if grade and grade in self.stats["performance_grades"]:
            self.stats["performance_grades"][grade] += 1

    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since start.

        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time

    def should_update_display(self, frequency: int = 10) -> bool:
        """
        Check if display should be updated based on test counter.

        Args:
            frequency: Update every N tests

        Returns:
            True if display should update
        """
        return self.stats["test_counter"] % frequency == 0

    def get_progress_percent(self) -> float:
        """
        Get test progress percentage.

        Returns:
            Progress percentage (0-100)
        """
        total = self.stats["total"]
        if total > 0:
            return (self.stats["completed"] / total) * 100
        return 0.0


class DisplayRenderState:
    """
    Manages display and UI rendering state.

    This class handles all Rich display components and visual state.
    """

    def __init__(self, console: Console, layout: Layout):
        """
        Initialize display render state.

        Args:
            console: Rich Console instance
            layout: Rich Layout structure
        """
        self.console = console
        self.layout = layout
        self.live: Live | None = None

        # Log buffer for messages
        self.log_buffer = deque(maxlen=LOG_BUFFER_SIZE)

        # Hanging test detection
        self.hanging_threshold = HANGING_TEST_THRESHOLD
        self.warnings_shown: set[str] = set()

    def start_live(self, refresh_rate: int = 1) -> bool:
        """
        Start the Rich live display.

        Args:
            refresh_rate: Refresh rate in Hz

        Returns:
            True if live display started successfully
        """
        try:
            self.live = Live(
                self.layout,
                console=self.console,
                refresh_per_second=refresh_rate,
                transient=False,
                auto_refresh=True,
            )
            self.live.start()
            time.sleep(0.1)  # Give display time to initialize
            return True
        except Exception:
            self.live = None
            return False

    def stop_live(self) -> None:
        """Stop the Rich live display."""
        if self.live:
            try:
                self.live.stop()
                self.console.clear()
                time.sleep(0.1)  # Ensure display is cleared
            except Exception:
                pass
            finally:
                self.live = None

    def refresh_live(self) -> None:
        """Force a refresh of the live display."""
        if self.live:
            try:
                self.live.refresh()
            except Exception:
                pass

    def add_log_message(self, message: str, max_length: int = 100) -> None:
        """
        Add a message to the log buffer.

        Args:
            message: Message to add
            max_length: Maximum message length
        """
        if message:
            self.log_buffer.append(message[:max_length])

    def should_warn_hanging(self, last_update: float) -> bool:
        """
        Check if we should warn about a hanging test.

        Args:
            last_update: Timestamp of last test update

        Returns:
            True if test appears to be hanging
        """
        return (time.time() - last_update) > self.hanging_threshold

    def mark_warning_shown(self, warning_id: str) -> bool:
        """
        Mark that a warning has been shown.

        Args:
            warning_id: Unique identifier for the warning

        Returns:
            True if this is the first time showing this warning
        """
        if warning_id not in self.warnings_shown:
            self.warnings_shown.add(warning_id)
            return True
        return False

    def is_live_active(self) -> bool:
        """
        Check if live display is active.

        Returns:
            True if live display is running
        """
        return self.live is not None

    def reset_console(self) -> None:
        """Reset the console to a fresh state."""
        try:
            self.console = Console()
        except Exception:
            pass


class OutputCaptureState:
    """
    Manages stdout/stderr capture state.

    This class encapsulates the output capture variables to further
    reduce instance variables in the main class.
    """

    def __init__(self):
        """Initialize output capture state."""
        self.original_stdout = None
        self.original_stderr = None
        self.stdout_buffer = None
        self.stderr_buffer = None

    def set_originals(self, stdout, stderr) -> None:
        """
        Set the original stdout and stderr.

        Args:
            stdout: Original sys.stdout
            stderr: Original sys.stderr
        """
        self.original_stdout = stdout
        self.original_stderr = stderr

    def set_buffers(self, stdout_buffer, stderr_buffer) -> None:
        """
        Set the capture buffers.

        Args:
            stdout_buffer: Buffer for stdout capture
            stderr_buffer: Buffer for stderr capture
        """
        self.stdout_buffer = stdout_buffer
        self.stderr_buffer = stderr_buffer

    def clear(self) -> None:
        """Clear all capture state."""
        self.original_stdout = None
        self.original_stderr = None
        self.stdout_buffer = None
        self.stderr_buffer = None

    def is_capturing(self) -> bool:
        """
        Check if output is being captured.

        Returns:
            True if capture is active
        """
        return self.original_stdout is not None
