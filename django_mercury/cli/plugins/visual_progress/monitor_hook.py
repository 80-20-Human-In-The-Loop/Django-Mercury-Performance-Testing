"""
Mercury Monitor Hook Integration

Provides hooks into the Mercury monitoring system to capture real metrics
from tests using monitor_django_view context managers.
"""

import logging
import os
import threading
from dataclasses import dataclass
from typing import Any

# Enable debug logging if MERCURY_DEBUG is set
if os.environ.get("MERCURY_DEBUG"):
    logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


@dataclass
class CapturedMetrics:
    """Captured metrics from a Mercury monitor."""

    test_name: str
    query_count: int
    response_time_ms: float
    memory_usage_mb: float
    cache_hits: int
    cache_misses: int
    n_plus_one_detected: bool
    grade: str
    django_issues: Any | None = None
    performance_score: Any | None = None


class MercuryMonitorHook:
    """
    Global hook system for capturing Mercury performance metrics.

    This hooks into the Mercury monitoring system to capture metrics
    from tests that use monitor_django_view context managers.
    """

    def __init__(self):
        self._metrics_store: dict[str, list[CapturedMetrics]] = {}
        self._lock = threading.Lock()
        self._enabled = False
        self._original_monitor_exit = None

        # Global query tracking using Django's connection.queries
        self._query_tracking: dict[str, dict[str, Any]] = {}
        self._current_test_start_queries = 0
        
        # Track the currently running test
        self._current_test_name = None

    def enable(self):
        """Enable the monitoring hook."""
        if self._enabled:
            logger.debug("Monitor hook already enabled")
            return

        try:
            # Try to hook into EnhancedPerformanceMonitor.__exit__
            from django_mercury.python_bindings.monitor import (
                EnhancedPerformanceMonitor,
            )

            logger.debug("Found EnhancedPerformanceMonitor class")

            # Store original __exit__ method
            self._original_monitor_exit = EnhancedPerformanceMonitor.__exit__
            logger.debug(f"Stored original __exit__ method: {self._original_monitor_exit}")

            # Create hooked version
            def hooked_exit(monitor_self, exc_type, exc_val, exc_tb):
                operation_name = getattr(monitor_self, 'operation_name', 'unknown')
                logger.debug(f"Hooked __exit__ called for operation: {operation_name}")
                logger.debug(f"Monitor attributes: {[attr for attr in dir(monitor_self) if not attr.startswith('__')]}")
                
                # Call original exit first
                result = self._original_monitor_exit(
                    monitor_self, exc_type, exc_val, exc_tb
                )

                # Capture metrics if available
                if hasattr(monitor_self, "_metrics") and monitor_self._metrics:
                    logger.debug(f"Monitor has _metrics attribute, capturing...")
                    logger.debug(f"Metrics type: {type(monitor_self._metrics)}")
                    logger.debug(f"Metrics attributes: {dir(monitor_self._metrics) if hasattr(monitor_self._metrics, '__dict__') else 'No __dict__'}")
                    self._capture_metrics_from_monitor(monitor_self)
                else:
                    logger.debug(f"Monitor has no _metrics attribute or it's None")
                    logger.debug(f"Available attributes: {[attr for attr in dir(monitor_self) if '_' in attr]}")

                # ALSO capture query count from the monitor's query tracker
                if (
                    hasattr(monitor_self, "_query_tracker")
                    and monitor_self._query_tracker
                ):
                    query_tracker = monitor_self._query_tracker
                    if hasattr(query_tracker, "query_count"):
                        # Store this globally for the test
                        operation_name = getattr(
                            monitor_self, "operation_name", "unknown"
                        )
                        with self._lock:
                            if operation_name not in self._query_tracking:
                                self._query_tracking[operation_name] = {}
                            self._query_tracking[operation_name][
                                "tracker_query_count"
                            ] = query_tracker.query_count
                            logger.debug(
                                f"Captured {query_tracker.query_count} queries from monitor's query tracker for {operation_name}"
                            )

                return result

            # Replace with hooked version
            EnhancedPerformanceMonitor.__exit__ = hooked_exit
            self._enabled = True
            logger.debug("Mercury monitor hook enabled")

        except ImportError:
            logger.warning("Could not import Mercury monitor for hooking")
        except Exception as e:
            logger.error(f"Failed to enable Mercury monitor hook: {e}")

    def disable(self):
        """Disable the monitoring hook."""
        if not self._enabled:
            return

        try:
            # Restore original __exit__ method
            if self._original_monitor_exit:
                from django_mercury.python_bindings.monitor import (
                    EnhancedPerformanceMonitor,
                )

                EnhancedPerformanceMonitor.__exit__ = (
                    self._original_monitor_exit
                )

            self._enabled = False
            logger.debug("Mercury monitor hook disabled")

        except Exception as e:
            logger.error(f"Failed to disable Mercury monitor hook: {e}")

    def _capture_metrics_from_monitor(self, monitor):
        """Capture metrics from a monitor instance."""
        try:
            logger.debug(f"Attempting to capture metrics from monitor for {monitor.operation_name}")
            logger.debug(f"Monitor type: {type(monitor)}")
            
            metrics = monitor._metrics
            if not metrics:
                logger.debug(f"No metrics found on monitor for {monitor.operation_name}")
                logger.debug(f"Monitor._metrics is: {metrics}")
                return
            
            logger.debug(f"Found metrics: {metrics}")
            logger.debug(f"Metrics type: {type(metrics)}")

            # Extract relevant data
            captured = CapturedMetrics(
                test_name=monitor.operation_name,
                query_count=getattr(metrics, "query_count", 0),
                response_time_ms=getattr(metrics, "response_time", 0),
                memory_usage_mb=getattr(metrics, "memory_usage", 0),
                cache_hits=getattr(metrics, "cache_hits", 0),
                cache_misses=getattr(metrics, "cache_misses", 0),
                n_plus_one_detected=False,
                grade="",
                django_issues=getattr(metrics, "django_issues", None),
                performance_score=getattr(metrics, "performance_score", None),
            )

            # Extract N+1 detection
            if captured.django_issues and hasattr(
                captured.django_issues, "has_n_plus_one"
            ):
                captured.n_plus_one_detected = (
                    captured.django_issues.has_n_plus_one
                )

            # Extract grade
            if captured.performance_score:
                if hasattr(captured.performance_score, "grade"):
                    captured.grade = captured.performance_score.grade
                elif hasattr(captured.performance_score, "letter_grade"):
                    captured.grade = captured.performance_score.letter_grade

            # Store metrics by operation name
            with self._lock:
                if monitor.operation_name not in self._metrics_store:
                    self._metrics_store[monitor.operation_name] = []
                self._metrics_store[monitor.operation_name].append(captured)
                
                # ALSO store by current test name if we know it
                if self._current_test_name:
                    if self._current_test_name not in self._metrics_store:
                        self._metrics_store[self._current_test_name] = []
                    # Create a copy with the test name
                    test_captured = CapturedMetrics(
                        test_name=self._current_test_name,
                        query_count=captured.query_count,
                        response_time_ms=captured.response_time_ms,
                        memory_usage_mb=captured.memory_usage_mb,
                        cache_hits=captured.cache_hits,
                        cache_misses=captured.cache_misses,
                        n_plus_one_detected=captured.n_plus_one_detected,
                        grade=captured.grade,
                        django_issues=captured.django_issues,
                        performance_score=captured.performance_score,
                    )
                    self._metrics_store[self._current_test_name].append(test_captured)
                    logger.debug(
                        f"Also stored metrics for test '{self._current_test_name}'"
                    )
                
                # Debug: log what we're storing
                logger.debug(
                    f"Captured metrics for '{monitor.operation_name}': "
                    f"{captured.query_count}Q, {captured.response_time_ms:.1f}ms, "
                    f"grade={captured.grade}"
                )

        except Exception as e:
            logger.error(f"Failed to capture metrics from monitor: {e}")

    def get_metrics_for_test(self, test_name: str) -> CapturedMetrics | None:
        """Get the most recent metrics for a test."""
        with self._lock:
            # Debug: log what we're looking for and what's available
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Looking for metrics for test: {test_name}")
                logger.debug(f"Available operation names: {list(self._metrics_store.keys())}")
            
            # Try exact match first
            if (
                test_name in self._metrics_store
                and self._metrics_store[test_name]
            ):
                logger.debug(f"Found exact match for {test_name}")
                return self._metrics_store[test_name][-1]
            
            # Try with .comprehensive suffix (Mercury tests use this)
            comprehensive_name = f"{test_name}.comprehensive"
            if (
                comprehensive_name in self._metrics_store
                and self._metrics_store[comprehensive_name]
            ):
                logger.debug(f"Found match with .comprehensive suffix: {comprehensive_name}")
                return self._metrics_store[comprehensive_name][-1]

            # Try partial match (test name might be in operation name)
            for op_name, metrics_list in self._metrics_store.items():
                if test_name in op_name and metrics_list:
                    logger.debug(f"Found partial match: {op_name} contains {test_name}")
                    return metrics_list[-1]
            
            logger.debug(f"No metrics found for {test_name}")

        return None

    def get_all_metrics(self) -> dict[str, list[CapturedMetrics]]:
        """Get all captured metrics."""
        with self._lock:
            return dict(self._metrics_store)

    def clear(self):
        """Clear all captured metrics and close any open query contexts."""
        with self._lock:
            # Close any open query contexts before clearing
            for test_name, tracking in self._query_tracking.items():
                if tracking.get("query_context"):
                    try:
                        tracking["query_context"].__exit__(None, None, None)
                        logger.debug(
                            f"Closed query context for {test_name} during clear"
                        )
                    except Exception as e:
                        logger.debug(
                            f"Error closing context for {test_name}: {e}"
                        )

            # Clear all tracking data
            self._metrics_store.clear()
            self._query_tracking.clear()

            # Also try to reset Django's global queries
            try:
                from django.db import reset_queries

                reset_queries()
                logger.debug("Reset Django queries during clear")
            except:
                try:
                    from django.db import connection

                    if hasattr(connection, "queries"):
                        connection.queries.clear()
                        logger.debug(
                            "Manually cleared Django queries during clear"
                        )
                except:
                    pass

    def start_test_query_tracking(self, test_name: str):
        """
        Start tracking queries for a test using Django's connection.queries.

        This records the current number of queries so we can calculate
        how many queries are executed during the test.
        """
        # Store the current test name for metric association
        with self._lock:
            self._current_test_name = test_name
            logger.debug(f"Set current test name to: {test_name}")
        
        try:
            from django.conf import settings
            from django.db import connection, reset_queries
            from django.test.utils import CaptureQueriesContext

            # CRITICAL FIX: Clear any previous query contexts to prevent accumulation
            # Close any existing context that wasn't properly closed
            with self._lock:
                for (
                    tracked_test,
                    tracking_data,
                ) in self._query_tracking.items():
                    if (
                        tracking_data.get("query_context")
                        and tracked_test != test_name
                    ):
                        try:
                            tracking_data["query_context"].__exit__(
                                None, None, None
                            )
                            tracking_data["query_context"] = None
                            logger.debug(
                                f"Closed unclosed context for {tracked_test}"
                            )
                        except:
                            pass

            # Initialize tracking for this test
            with self._lock:
                self._query_tracking[test_name] = {
                    "start_count": 0,
                    "end_count": None,
                    "query_count": 0,
                    "query_context": None,
                }

            # CRITICAL FIX: Reset Django's global query list to start fresh for this test
            # This prevents accumulation of queries from previous tests
            try:
                reset_queries()  # Django's built-in function to clear connection.queries
                logger.debug(f"Reset connection.queries for {test_name}")
            except:
                # If reset_queries is not available, try to clear manually
                if hasattr(connection, "queries"):
                    connection.queries.clear()
                    logger.debug(
                        f"Manually cleared connection.queries for {test_name}"
                    )

            # Method 1: Try to use Django's query tracking (should now be 0 after reset)
            if hasattr(connection, "queries"):
                start_count = len(connection.queries)
                with self._lock:
                    self._query_tracking[test_name][
                        "start_count"
                    ] = start_count
                logger.debug(
                    f"Django connection.queries available, start count after reset: {start_count}"
                )

            # Method 2: Start a CaptureQueriesContext to track queries for this test
            try:
                capture_context = CaptureQueriesContext(connection)
                capture_context.__enter__()
                with self._lock:
                    self._query_tracking[test_name][
                        "query_context"
                    ] = capture_context
                logger.debug(f"Started CaptureQueriesContext for {test_name}")
            except Exception as e:
                logger.debug(f"Could not start CaptureQueriesContext: {e}")

            logger.debug(f"Started query tracking for {test_name}")

        except ImportError as e:
            logger.debug(f"Django not available for query tracking: {e}")
        except Exception as e:
            logger.debug(f"Error starting query tracking: {e}")

    def stop_test_query_tracking(self, test_name: str) -> int:
        """
        Stop tracking queries for a test and return the query count.

        Returns the number of queries executed during the test.
        """
        # Clear current test name
        with self._lock:
            self._current_test_name = None
            logger.debug(f"Cleared current test name (was: {test_name})")
        
        try:
            from django.conf import settings
            from django.db import connection, connections, reset_queries

            # Try multiple approaches to get query count
            query_count = 0

            with self._lock:
                if test_name not in self._query_tracking:
                    logger.debug(f"No query tracking found for {test_name}")
                    return 0

                tracking = self._query_tracking[test_name]

                # Method 1: PREFERRED - Check if we have a CaptureQueriesContext
                # This is the most accurate as it's isolated to this test only
                if tracking.get("query_context"):
                    try:
                        capture_context = tracking["query_context"]
                        capture_context.__exit__(None, None, None)
                        query_count = len(capture_context.captured_queries)
                        logger.debug(
                            f"CaptureQueriesContext captured {query_count} queries for {test_name}"
                        )
                        tracking["query_count"] = query_count
                        tracking["query_context"] = None  # Clear reference

                        # CRITICAL: Reset queries after capturing to prevent accumulation
                        try:
                            reset_queries()
                            logger.debug(
                                f"Reset queries after capturing for {test_name}"
                            )
                        except:
                            if hasattr(connection, "queries"):
                                connection.queries.clear()

                        return query_count
                    except Exception as e:
                        logger.debug(
                            f"Error getting queries from CaptureQueriesContext: {e}"
                        )

                # Method 2: FALLBACK - Use connection.queries if CaptureQueriesContext failed
                if hasattr(connection, "queries"):
                    end_count = len(connection.queries)
                    logger.debug(f"connection.queries end count: {end_count}")

                    # Calculate difference from start
                    start_count = tracking.get("start_count", 0)
                    query_count = end_count - start_count

                    # Sanity check - if we get a negative or huge number, something's wrong
                    if query_count < 0:
                        logger.warning(
                            f"Negative query count detected ({query_count}), using absolute count"
                        )
                        query_count = end_count
                    elif query_count > 500:
                        logger.warning(
                            f"Unusually high query count ({query_count}) for {test_name}, "
                            f"possible accumulation issue"
                        )

                    tracking["end_count"] = end_count
                    tracking["query_count"] = query_count

                    logger.debug(
                        f"Stopped query tracking for {test_name}: {query_count} queries "
                        f"(from {start_count} to {end_count})"
                    )

                    # CRITICAL: Reset queries after capturing to prevent accumulation
                    try:
                        reset_queries()
                        logger.debug(
                            f"Reset queries after capturing for {test_name}"
                        )
                    except:
                        if hasattr(connection, "queries"):
                            connection.queries.clear()

                    return query_count

                # Method 3: LAST RESORT - Check all connections (in case of multiple databases)
                # Only use this if the above methods failed
                total_queries = 0
                for alias in connections:
                    conn = connections[alias]
                    if hasattr(conn, "queries"):
                        conn_queries = len(conn.queries)
                        total_queries += conn_queries
                        logger.debug(
                            f"Connection '{alias}' has {conn_queries} queries"
                        )
                        # Clear queries on this connection too
                        try:
                            conn.queries.clear()
                        except:
                            pass

                if total_queries > 0:
                    logger.debug(
                        f"Total queries across all connections: {total_queries}"
                    )
                    tracking["query_count"] = total_queries
                    return total_queries

                return 0

        except ImportError as e:
            logger.debug(f"Django not available for query tracking: {e}")
            return 0
        except Exception as e:
            logger.debug(f"Error stopping query tracking: {e}")
            return 0

    def get_query_count_for_test(self, test_name: str) -> int:
        """Get the recorded query count for a test."""
        with self._lock:
            if test_name in self._query_tracking:
                tracking = self._query_tracking[test_name]
                # First check if we captured from the monitor's query tracker
                if "tracker_query_count" in tracking:
                    return tracking["tracker_query_count"]
                # Otherwise use our tracked count
                return tracking.get("query_count", 0)

            # Also check by operation name patterns (Mercury often uses operation names)
            for key, tracking in self._query_tracking.items():
                if test_name in key or key in test_name:
                    if "tracker_query_count" in tracking:
                        return tracking["tracker_query_count"]
                    return tracking.get("query_count", 0)
        return 0

    def extract_metrics_from_test(self, test) -> dict | None:
        """
        Extract Mercury metrics from a test instance.

        Tries multiple approaches:
        1. Check test class for _test_executions
        2. Check test instance for _last_metrics
        3. Check captured metrics by test name
        4. Use our tracked query count as fallback
        """
        metrics = {}
        test_name = f"{test.__class__.__name__}.{getattr(test, '_testMethodName', 'unknown')}"

        # Debug: Check if C extensions are in use
        try:
            from django_mercury.python_bindings.c_bindings import c_extensions

            if c_extensions and (
                c_extensions.metrics_engine or c_extensions.query_analyzer
            ):
                logger.debug(f"C extensions detected for test {test_name}")
                logger.debug(
                    f"  metrics_engine: {c_extensions.metrics_engine is not None}"
                )
                logger.debug(
                    f"  query_analyzer: {c_extensions.query_analyzer is not None}"
                )
        except ImportError:
            logger.debug("Could not import c_extensions")

        # Debug: Log what attributes the test has
        logger.debug(f"Test {test_name} attributes:")
        for attr in dir(test):
            if (
                attr.startswith("_mercury")
                or attr.startswith("_test")
                or "metrics" in attr.lower()
            ):
                logger.debug(f"  {attr}: {hasattr(test, attr)}")

        # Also check class attributes
        logger.debug(f"Test class {test.__class__.__name__} attributes:")
        for attr in dir(test.__class__):
            if (
                attr.startswith("_mercury")
                or attr.startswith("_test")
                or "metrics" in attr.lower()
            ):
                logger.debug(f"  {attr}: {hasattr(test.__class__, attr)}")

        # Method 1: Check test class for _test_executions
        if (
            hasattr(test.__class__, "_test_executions")
            and test.__class__._test_executions
        ):
            try:
                # Get the most recent execution
                last_execution = test.__class__._test_executions[-1]

                # Extract metrics from execution
                metrics = {
                    "query_count": getattr(last_execution, "query_count", 0),
                    "response_time_ms": getattr(
                        last_execution, "response_time", 0
                    ),
                    "memory_usage_mb": getattr(
                        last_execution, "memory_usage", 0
                    ),
                    "cache_hits": getattr(last_execution, "cache_hits", 0),
                    "cache_misses": getattr(last_execution, "cache_misses", 0),
                    "n_plus_one_detected": False,
                    "grade": "",
                }

                # Check for N+1
                if hasattr(last_execution, "django_issues"):
                    django_issues = last_execution.django_issues
                    if hasattr(django_issues, "has_n_plus_one"):
                        metrics["n_plus_one_detected"] = (
                            django_issues.has_n_plus_one
                        )

                # Get grade
                if hasattr(last_execution, "performance_score"):
                    score = last_execution.performance_score
                    if hasattr(score, "grade"):
                        metrics["grade"] = score.grade

                logger.debug(
                    f"Extracted metrics from _test_executions: {metrics}"
                )
                return metrics

            except Exception as e:
                logger.debug(f"Failed to extract from _test_executions: {e}")

        # Method 2: Check captured metrics from the hook
        test_name = f"{test.__class__.__name__}.{getattr(test, '_testMethodName', 'unknown')}"
        captured = self.get_metrics_for_test(test_name)
        if captured:
            metrics = {
                "query_count": captured.query_count,
                "response_time_ms": captured.response_time_ms,
                "memory_usage_mb": captured.memory_usage_mb,
                "cache_hits": captured.cache_hits,
                "cache_misses": captured.cache_misses,
                "n_plus_one_detected": captured.n_plus_one_detected,
                "grade": captured.grade,
            }
            logger.debug(f"Extracted metrics from captured store: {metrics}")
            return metrics

        # No metrics found
        return None if not metrics else metrics


# Global hook instance
_global_hook = MercuryMonitorHook()


def get_mercury_hook() -> MercuryMonitorHook:
    """Get the global Mercury monitor hook."""
    return _global_hook


def enable_mercury_hook():
    """Enable the global Mercury monitor hook."""
    _global_hook.enable()


def disable_mercury_hook():
    """Disable the global Mercury monitor hook."""
    _global_hook.disable()


def extract_mercury_metrics(test) -> dict | None:
    """
    Extract Mercury metrics from a test instance.

    This is a convenience function that uses the global hook.
    """
    return _global_hook.extract_metrics_from_test(test)
