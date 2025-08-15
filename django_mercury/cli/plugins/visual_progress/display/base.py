"""
Base Mercury Visual Display class.

This module contains the core MercuryVisualDisplay class that coordinates
all display operations during test execution.
"""

import re
import sys
from typing import Any

from ..metrics_tracker import TestMetrics, get_global_tracker
from .capture import StdoutCapture
from .constants import (
    REFRESH_RATE,
    SYMBOLS,
    Console,
)
from .formatters import (
    format_test_name_for_display,
)
from .layout import create_display_layout
from .panels import (
    update_footer,
    update_header,
    update_learning_tips_panel,
    update_mercury_panel,
    update_progress,
    update_stats,
)
from .state import DisplayRenderState, OutputCaptureState, TestExecutionTracker
from .summary import show_final_summary as _show_final_summary


class MercuryVisualDisplay:
    """
    Rich visual display for Mercury test execution.

    This class manages the live display during test execution, showing
    progress, statistics, and performance insights in real-time.

    Uses composition to manage state complexity and maintain clean separation
    of concerns.
    """

    def __init__(self, console: Console, hints_enabled=False, profile='expert'):
        """
        Initialize the visual display.

        Args:
            console: Rich Console instance for rendering
            hints_enabled: Whether to show performance hints
            profile: User profile ('student', 'expert', 'agent')
        """
        # Configuration
        self.hints_enabled = hints_enabled
        self.profile = profile
        
        # Core composition objects
        self.test_tracker = TestExecutionTracker()
        self.display_state = DisplayRenderState(
            console, create_display_layout()
        )
        self.metrics_tracker = get_global_tracker()
        self.output_capture = OutputCaptureState()

    def start_live_display(self):
        """Start the live display."""
        self.add_to_log_buffer("Visual display ready")

        # Try to start the live display
        try:
            # Force stdout to be unbuffered for Rich
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(line_buffering=True)

            if self.display_state.start_live(REFRESH_RATE):
                self._update_display()
                self.display_state.refresh_live()
            else:
                self.add_to_log_buffer(f"{SYMBOLS['cross']} Display error")

        except Exception as e:
            self.add_to_log_buffer(
                f"{SYMBOLS['cross']} Display error: {str(e)[:40]}"
            )

    def stop_live_display(self):
        """Stop the live display and clear the screen."""
        self.display_state.stop_live()

    def on_discovery_start(self):
        """Called when test discovery starts."""
        self.add_to_log_buffer(f"{SYMBOLS['search']} Discovering tests...")
        self._update_header(f"{SYMBOLS['search']} Discovering tests...")
        self._update_display()

    def on_discovery_complete(self, test_count: int):
        """Called when test discovery completes."""
        self.add_to_log_buffer(f"{SYMBOLS['check']} Found {test_count} tests")
        self.test_tracker.stats["total"] = test_count
        self._update_header(f"Found {test_count} tests")
        self._update_display()

    def on_test_start(self, test_name: str, is_mercury: bool):
        """Called when a test starts."""
        # Only log Mercury tests and errors to reduce spam
        if is_mercury:
            self.add_to_log_buffer(
                f"{SYMBOLS['target']} Mercury: {test_name.split('.')[-1][:30]}"
            )
        elif "Error" in test_name:
            self.add_to_log_buffer(
                f"{SYMBOLS['warning']} Error: {test_name.split('.')[-1][:30]}"
            )

        # Update test tracker
        display_name = format_test_name_for_display(test_name)
        self.test_tracker.update_test_start(
            test_name, is_mercury, display_name
        )

        # Only update display every 10th test to reduce overhead
        if self.test_tracker.should_update_display(10):
            self._update_display(f"Running: {display_name}")

    def on_test_complete(
        self,
        test_name: str,
        duration: float,
        passed: bool,
        is_mercury: bool,
        metrics: dict[str, Any] | None = None,
    ):
        """Called when a test completes."""
        # Update test tracker
        self.test_tracker.update_test_complete(
            test_name, duration, passed, is_mercury
        )

        # Process Mercury metrics if available
        if is_mercury:
            if metrics:
                self._process_mercury_metrics(metrics, test_name)
            else:
                # Mercury test but no metrics captured - likely C extensions issue
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Mercury test {test_name} completed but no metrics captured")

        # Update display periodically
        if self.test_tracker.stats["completed"] % 5 == 0:
            self._update_display()

    def on_test_success(self, test_name: str):
        """Called when a test passes."""
        str(test_name)  # silence unused var
        self.test_tracker.record_success()
        stats = self.test_tracker.stats
        self._update_display(f"Passed: {stats['passed']}/{stats['total']}")

    def on_test_failure(self, test_name: str, err, isolation_issue=None):
        """Called when a test fails."""
        self.test_tracker.record_failure(test_name, isolation_issue)
        stats = self.test_tracker.stats
        self._update_display(f"Failed: {stats['failed']} tests")

    def on_test_error(self, test_name: str, err):
        """Called when a test has an error."""
        self.test_tracker.record_error(test_name)
        stats = self.test_tracker.stats
        self._update_display(f"Errors: {stats['errors']} tests")

    def on_test_skip(self, test_name: str, reason: str):
        """Called when a test is skipped."""
        self.test_tracker.record_skip()
        stats = self.test_tracker.stats
        self._update_display(f"Skipped: {stats['skipped']} tests")

    def _process_mercury_metrics(self, metrics: dict, test_name: str):
        """Process Mercury performance metrics."""
        # Create TestMetrics object for tracker
        test_metrics = TestMetrics(
            test_name=test_name,
            query_count=metrics.get("query_count", 0),
            response_time_ms=metrics.get("response_time_ms", 0),
            memory_usage_mb=metrics.get("memory_usage_mb", 0),
            cache_hits=metrics.get("cache_hits", 0),
            cache_misses=metrics.get("cache_misses", 0),
            n_plus_one_detected=metrics.get("n_plus_one_detected", False),
            grade=metrics.get("grade", ""),
        )

        # Add to metrics tracker (will be filtered if not meaningful)
        self.metrics_tracker.add_metrics(test_metrics)
        
        # Track that we saw a Mercury test even if metrics were empty
        # This is important for the summary display
        if test_name not in getattr(self, '_mercury_tests_seen', set()):
            if not hasattr(self, '_mercury_tests_seen'):
                self._mercury_tests_seen = set()
            self._mercury_tests_seen.add(test_name)

        # Update test tracker with Mercury metrics
        self.test_tracker.update_mercury_metrics(metrics)

        # Add insights for special cases
        if metrics.get("n_plus_one_detected"):
            self.test_tracker.add_mercury_insight(
                f"N+1 in {test_name.split('.')[-1]}"
            )
        elif metrics.get("query_count", 0) > 50:
            self.test_tracker.add_mercury_insight(
                f"High queries ({metrics['query_count']}) in {test_name.split('.')[-1]}"
            )

    def _update_display(self, fallback_message: str = "Running Tests"):
        """Update the live display."""
        if self.display_state.is_live_active():
            try:
                self._update_header()
                self._update_progress()
                self._update_stats()
                self._update_learning_tips_panel()
                self._update_mercury_panel()
                self._update_footer()
                self.display_state.refresh_live()
            except Exception:
                # If Rich display fails, use fallback
                self._fallback_display_update(fallback_message)
        else:
            # No live display, use fallback
            self._fallback_display_update(fallback_message)

    def _fallback_display_update(self, message: str):
        """Simple fallback visual update without Live display."""
        if not self.display_state.is_live_active():
            try:
                stats = self.test_tracker.stats
                completed = stats.get("completed", 0)
                total = stats.get("total", 0)

                if total > 0:
                    percent = (completed / total) * 100
                    print(
                        f"\r{SYMBOLS['rocket']} {message} - Progress: {completed}/{total} ({percent:.1f}%)",
                        end="",
                        flush=True,
                    )
                else:
                    print(
                        f"\r{SYMBOLS['rocket']} {message} - Progress: {completed}/{total}",
                        end="",
                        flush=True,
                    )
            except Exception:
                # Even fallback failed, just print normally
                stats = self.test_tracker.stats
                print(
                    f"{SYMBOLS['rocket']} {message} - Progress: {stats['completed']}/{stats['total']}"
                )

    def _update_header(self, message: str = None):
        """Update the header panel."""
        update_header(self, message)

    def _update_progress(self):
        """Update the progress panel."""
        update_progress(self)

    def _update_stats(self):
        """Update the statistics panel."""
        update_stats(self)

    def _update_learning_tips_panel(self):
        """Update the learning tips panel."""
        update_learning_tips_panel(self)

    def _update_mercury_panel(self):
        """Update the Mercury insights panel."""
        update_mercury_panel(self)

    def _update_footer(self):
        """Update the footer panel."""
        update_footer(self)

    def show_final_summary(self, failures: int):
        """Show final test summary."""
        _show_final_summary(self, failures)

    def add_to_log_buffer(self, message: str):
        """Add a message to the log buffer."""
        # Clean up ANSI escape codes and excessive whitespace
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        cleaned = ansi_escape.sub("", message).strip()
        if cleaned:
            self.display_state.add_log_message(cleaned)

    def capture_stdout(self):
        """Start capturing stdout/stderr."""
        if not self.output_capture.is_capturing():
            self.output_capture.set_originals(sys.stdout, sys.stderr)

            stdout_buffer = StdoutCapture(self)
            stderr_buffer = StdoutCapture(self, is_stderr=True)
            self.output_capture.set_buffers(stdout_buffer, stderr_buffer)

            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer

    def restore_stdout(self):
        """Restore original stdout/stderr."""
        if self.output_capture.is_capturing():
            sys.stdout = self.output_capture.original_stdout
            sys.stderr = self.output_capture.original_stderr
            self.output_capture.clear()

    # ===== Compatibility Properties =====
    # These properties provide backward compatibility with existing code
    # that directly accesses these attributes

    @property
    def console(self):
        """Get the console for compatibility."""
        return self.display_state.console

    @console.setter
    def console(self, value):
        """Set the console for compatibility."""
        self.display_state.console = value

    @property
    def layout(self):
        """Get the layout for compatibility."""
        return self.display_state.layout

    @property
    def live(self):
        """Get the live display for compatibility."""
        return self.display_state.live

    @property
    def stats(self):
        """Get stats for compatibility."""
        return self.test_tracker.stats

    @property
    def current_test(self):
        """Get current test for compatibility."""
        return self.test_tracker.current_test

    @property
    def test_history(self):
        """Get test history for compatibility."""
        return self.test_tracker.test_history

    @property
    def mercury_insights(self):
        """Get Mercury insights for compatibility."""
        return self.test_tracker.mercury_insights

    @property
    def failed_tests(self):
        """Get failed tests for compatibility."""
        return self.test_tracker.failed_tests

    @property
    def isolation_issues(self):
        """Get isolation issues for compatibility."""
        return self.test_tracker.isolation_issues

    @property
    def start_time(self):
        """Get start time for compatibility."""
        return self.test_tracker.start_time

    @property
    def last_test_update(self):
        """Get last test update time for compatibility."""
        return self.test_tracker.last_test_update

    @property
    def hanging_threshold(self):
        """Get hanging threshold for compatibility."""
        return self.display_state.hanging_threshold

    @property
    def warnings_shown(self):
        """Get warnings shown for compatibility."""
        return self.display_state.warnings_shown

    @property
    def log_buffer(self):
        """Get log buffer for compatibility."""
        return self.display_state.log_buffer

    @property
    def original_stdout(self):
        """Get original stdout for compatibility."""
        return self.output_capture.original_stdout

    @property
    def original_stderr(self):
        """Get original stderr for compatibility."""
        return self.output_capture.original_stderr

    @property
    def stdout_buffer(self):
        """Get stdout buffer for compatibility."""
        return self.output_capture.stdout_buffer

    @property
    def stderr_buffer(self):
        """Get stderr buffer for compatibility."""
        return self.output_capture.stderr_buffer
