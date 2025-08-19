"""
Mercury Visual Test Result Handler

Provides real-time test result updates to the visual display.
Handles both regular tests and Mercury performance tests.
"""

import os
import time
import unittest


class MercuryVisualTestResult(unittest.TestResult):
    """
    Custom TestResult that sends real-time updates to the visual display.
    """

    def __init__(
        self,
        stream=None,
        descriptions=None,
        verbosity=None,
        visual_display=None,
    ):
        super().__init__(stream, descriptions, verbosity)
        self.visual_display = visual_display
        self.current_test = None
        self.test_start_time = None
        self._shown_errors = set()  # Track which errors we've shown
        self._failure_count = 0

        # Initialize isolation detector
        from .metrics_tracker import IsolationIssueDetector

        self.isolation_detector = IsolationIssueDetector()

    def startTest(self, test):
        """Called when a test starts."""
        super().startTest(test)
        self.test_start_time = time.perf_counter()

        # Track failure count at test start to detect new failures
        self._failure_count = len(self.failures) + len(self.errors)

        # Extract test information safely (handles _ErrorHolder objects)
        test_class = test.__class__.__name__

        # Check if this is an _ErrorHolder object (created for test import/setup errors)
        if test_class == "_ErrorHolder":
            # _ErrorHolder objects don't have _testMethodName, use id() instead
            test_name = str(test.id()) if hasattr(test, "id") else f"ErrorHolder.{test_class}"
            print(f"🚨 Encountered test import/setup error: {test_name}")
            is_mercury = False  # Error holders are never Mercury tests
        else:
            # Regular test object - safely access _testMethodName
            test_method = getattr(test, "_testMethodName", "unknown_method")
            test_name = f"{test_class}.{test_method}"

            if test_method == "unknown_method":
                print(f"⚠️  Warning: Test object missing _testMethodName: {test_class}")

            # Detect if it's a Mercury test
            is_mercury = self._is_mercury_test(test)

        self.current_test = {
            "name": test_name,
            "test": test,
            "is_mercury": is_mercury,
            "start_time": self.test_start_time,
            "is_error_holder": test_class == "_ErrorHolder",
        }

        # Start query tracking for this test
        from .monitor_hook import get_mercury_hook

        get_mercury_hook().start_test_query_tracking(test_name)

        if self.visual_display:
            self.visual_display.on_test_start(test_name, is_mercury)
        else:
            print(f"⚠️  No visual_display available in startTest for: {test_name}")

    def stopTest(self, test):
        """Called when a test completes."""
        super().stopTest(test)

        if self.test_start_time:
            duration = time.perf_counter() - self.test_start_time
        else:
            duration = 0

        # Stop query tracking and get the actual query count
        from .monitor_hook import get_mercury_hook

        test_name = self.current_test["name"] if self.current_test else self._get_test_name(test)
        actual_query_count = get_mercury_hook().stop_test_query_tracking(test_name)

        # Extract Mercury metrics if available
        mercury_metrics = self._extract_mercury_metrics(test)

        # If we got metrics but query_count is 0 or missing, use our tracked count
        if mercury_metrics and actual_query_count > 0:
            if mercury_metrics.get("query_count", 0) == 0:
                mercury_metrics["query_count"] = actual_query_count

        # Store the actual query count for later use
        if self.current_test:
            self.current_test["actual_query_count"] = actual_query_count

        if self.visual_display and self.current_test:
            # Determine if test passed (no failures or errors added during this test)
            passed = not self._test_had_failure_or_error()

            self.visual_display.on_test_complete(
                self.current_test["name"],
                duration,
                passed,
                self.current_test["is_mercury"],
                mercury_metrics,
            )

        self.current_test = None
        self.test_start_time = None

    def addSuccess(self, test):
        """Called when a test passes."""
        super().addSuccess(test)
        test_name = self._get_test_name(test)

        if self.visual_display:
            self.visual_display.on_test_success(test_name)
        else:
            print(f"⚠️  No visual_display available for test success: {test_name}")

    def addError(self, test, err):
        """Called when a test has an error."""
        super().addError(test, err)
        test_name = self._get_test_name(test)

        # Enhanced debugging for _ErrorHolder objects (but less verbose)
        if test.__class__.__name__ == "_ErrorHolder":
            # Only show the first error of each type to reduce spam
            error_key = f"{err[0].__name__ if err and len(err) > 0 else 'Unknown'}"
            if error_key not in self._shown_errors:
                self._shown_errors.add(error_key)

                print(f"💥 Test Import/Setup Error: {test_name}")
                print(f"   Error Type: {error_key}")
                if err and len(err) > 1 and err[1]:
                    error_msg = str(err[1])
                    # Show first line of error for quick understanding
                    first_line = error_msg.split("\n")[0] if error_msg else "No error message"
                    print(f"   Message: {first_line}")

                    # Check for common import errors
                    if "OperationalError" in str(err[0]) and "readonly" in first_line:
                        print("   💡 Fix: Run './fix_test_db.sh' in your project directory")
                        # Set flag for main process to show database tips
                        os.environ["MERCURY_DB_ERROR_DETECTED"] = "1"
                    elif "OperationalError" in str(err[0]) and "no such table" in first_line:
                        print("   💡 Database not set up properly - migrations may need to run")
                        os.environ["MERCURY_DB_ERROR_DETECTED"] = "1"
                    elif "ImportError" in str(err[0]) or "ModuleNotFoundError" in str(err[0]):
                        print("   💡 Hint: Check if all required packages are installed")

                    # Show that we're suppressing duplicate errors
                    print(f"   (Suppressing further {error_key} errors to reduce output)")

        if self.visual_display:
            self.visual_display.on_test_error(test_name, err)

    def addFailure(self, test, err):
        """Called when a test fails."""
        super().addFailure(test, err)
        test_name = self._get_test_name(test)

        # Check for isolation issues
        isolation_issue = None
        if err and len(err) > 1:
            error_msg = str(err[1]) if err[1] else ""
            isolation_issue = self.isolation_detector.analyze_failure(test_name, error_msg)

        # Only print failure details for non-bulk failures to reduce spam
        self._failure_count += 1

        # Only show first few failures in detail
        if self._failure_count <= 3:
            if test.__class__.__name__ == "_ErrorHolder":
                print(f"❌ Test Import/Setup Failure: {test_name}")
            else:
                if isolation_issue:
                    print(f"❌ Test Failure: {test_name} ⚠️ [Possible Isolation Issue]")
                    print(f"   Issue: {isolation_issue}")
                else:
                    print(f"❌ Test Failure: {test_name}")
        elif self._failure_count == 4:
            print("   (Suppressing further failure output, see summary at end)")

        if self.visual_display:
            # Pass isolation info to display
            self.visual_display.on_test_failure(test_name, err, isolation_issue=isolation_issue)

    def addSkip(self, test, reason):
        """Called when a test is skipped."""
        super().addSkip(test, reason)
        test_name = self._get_test_name(test)

        # Don't print skip messages - they're usually not important
        # The visual display will still track them

        if self.visual_display:
            self.visual_display.on_test_skip(test_name, reason)

    def _test_had_failure_or_error(self):
        """Check if the current test had a failure or error."""
        # Track the test result based on failure/error count
        # This is a simple approach - the test passed if no new failures/errors were added
        current_failures = len(self.failures) + len(self.errors)
        return current_failures > self._failure_count

    def _is_mercury_test(self, test):
        """Check if test is a Mercury test case."""
        # Check class hierarchy for Mercury test cases
        test_class = test.__class__
        mercury_classes = [
            "DjangoMercuryAPITestCase",
            "DjangoPerformanceAPITestCase",
            "MercuryTestCase",
        ]

        for cls in test_class.__mro__:
            if cls.__name__ in mercury_classes:
                return True

        # Check if test has Mercury attributes
        return hasattr(test, "_mercury_enabled") or hasattr(test, "_mercury_metrics")

    def _extract_mercury_metrics(self, test):
        """Extract Mercury performance metrics from test if available."""
        import logging

        logger = logging.getLogger(__name__)
        test_name = f"{test.__class__.__name__}.{getattr(test, '_testMethodName', 'unknown')}"

        logger.debug(f"Extracting metrics for {test_name}")
        logger.debug(f"Test class: {test.__class__.__name__}")
        logger.debug(
            f"Test attributes: {[attr for attr in dir(test) if attr.startswith('_mercury') or attr.startswith('_test')]}"
        )
        logger.debug(
            f"Test class attributes: {[attr for attr in dir(test.__class__) if attr.startswith('_mercury') or attr.startswith('_test')]}"
        )

        # Check if this is actually a Mercury test
        is_mercury = self._is_mercury_test(test)
        logger.debug(f"Is Mercury test: {is_mercury}")

        if not is_mercury:
            logger.debug(f"Not a Mercury test, skipping extraction")
            return None

        # Use the monitor hook to extract metrics
        from .monitor_hook import extract_mercury_metrics, get_mercury_hook

        # Try to get metrics from the hook system first
        logger.debug("Trying hook system...")
        metrics = extract_mercury_metrics(test)
        if metrics:
            logger.debug(f"Found metrics from hook: {metrics}")
            return metrics
        else:
            logger.debug("No metrics from hook system")

        # NEW: Try to get metrics directly from the hook's store using test name
        hook = get_mercury_hook()
        captured = hook.get_metrics_for_test(test_name)
        if captured:
            logger.debug(f"Found metrics from hook store for {test_name}")
            # Convert CapturedMetrics to dict format
            metrics = {
                "query_count": captured.query_count,
                "response_time_ms": captured.response_time_ms,
                "memory_usage_mb": captured.memory_usage_mb,
                "cache_hits": captured.cache_hits,
                "cache_misses": captured.cache_misses,
                "n_plus_one_detected": captured.n_plus_one_detected,
                "grade": captured.grade,
            }
            logger.debug(f"Converted captured metrics: {metrics}")
            return metrics

        # Fallback to original extraction methods
        metrics = None
        logger.debug("Checking Mercury attributes...")

        # Show what Mercury-related attributes exist
        mercury_attrs = [attr for attr in dir(test) if "mercury" in attr.lower()]
        test_attrs = [attr for attr in dir(test) if attr.startswith("_test")]
        logger.debug(f"Mercury attrs on instance: {mercury_attrs}")
        logger.debug(f"Test attrs on instance: {test_attrs}")

        class_mercury_attrs = [attr for attr in dir(test.__class__) if "mercury" in attr.lower()]
        class_test_attrs = [attr for attr in dir(test.__class__) if attr.startswith("_test")]
        logger.debug(f"Mercury attrs on class: {class_mercury_attrs}")
        logger.debug(f"Test attrs on class: {class_test_attrs}")

        # Try multiple ways Mercury might store metrics

        # 1. Direct _mercury_metrics attribute (if set by Mercury)
        if hasattr(test, "_mercury_metrics"):
            logger.debug(f"Found _mercury_metrics: {test._mercury_metrics}")
            metrics = test._mercury_metrics

        # 2. Test executions list on the CLASS (Mercury stores history here)
        if not metrics and hasattr(test.__class__, "_test_executions"):
            executions = test.__class__._test_executions
            logger.debug(f"Found _test_executions with {len(executions)} items")
            if executions:
                # Get the most recent execution
                last_execution = executions[-1]
                logger.debug(f"Last execution type: {type(last_execution)}")
                logger.debug(
                    f"Last execution attributes: {dir(last_execution) if hasattr(last_execution, '__dict__') else 'No __dict__'}"
                )

                if hasattr(last_execution, "__dict__"):
                    # Convert execution object to dict - match the actual attribute names
                    logger.debug(f"Converting execution object to dict")

                    # Extract response time (stored as response_time, convert to ms)
                    response_time = getattr(last_execution, "response_time", 0)
                    response_time_ms = response_time if response_time else 0

                    # Extract memory usage (stored as memory_usage, already in MB)
                    memory_usage = getattr(last_execution, "memory_usage", 0)
                    memory_usage_mb = memory_usage if memory_usage else 0

                    metrics = {
                        "response_time_ms": response_time_ms,
                        "query_count": getattr(last_execution, "query_count", 0),
                        "memory_usage_mb": memory_usage_mb,
                        "cache_hits": getattr(last_execution, "cache_hits", 0),
                        "cache_misses": getattr(last_execution, "cache_misses", 0),
                        "n_plus_one_detected": False,
                        "grade": None,
                    }
                    logger.debug(f"Extracted metrics from execution: {metrics}")

                    # Check for N+1
                    if hasattr(last_execution, "django_issues"):
                        django_issues = last_execution.django_issues
                        if hasattr(django_issues, "has_n_plus_one"):
                            metrics["n_plus_one_detected"] = django_issues.has_n_plus_one

                    # Get grade from performance score
                    if hasattr(last_execution, "performance_score"):
                        score = last_execution.performance_score
                        if hasattr(score, "grade"):
                            metrics["grade"] = score.grade
                            logger.debug(f"Found grade: {score.grade}")
                        elif hasattr(score, "letter_grade"):
                            metrics["grade"] = score.letter_grade
                            logger.debug(f"Found letter_grade: {score.letter_grade}")
                    else:
                        logger.debug("No performance_score attribute found")
                else:
                    # If it's a dict already
                    metrics = last_execution

        # 3. Test executions list on the INSTANCE (fallback)
        if not metrics and hasattr(test, "_test_executions") and test._test_executions:
            logger.debug(f"Found instance _test_executions with {len(test._test_executions)} items")
            # Get the most recent execution
            last_execution = test._test_executions[-1]
            if hasattr(last_execution, "__dict__"):
                # Convert execution object to dict - match actual attribute names
                response_time = getattr(last_execution, "response_time", 0)
                memory_usage = getattr(last_execution, "memory_usage", 0)

                metrics = {
                    "response_time_ms": response_time if response_time else 0,
                    "query_count": getattr(last_execution, "query_count", 0),
                    "memory_usage_mb": memory_usage if memory_usage else 0,
                    "cache_hits": getattr(last_execution, "cache_hits", 0),
                    "cache_misses": getattr(last_execution, "cache_misses", 0),
                    "grade": None,
                    "n_plus_one_detected": False,
                }

                # Extract grade from performance score
                if hasattr(last_execution, "performance_score"):
                    score = last_execution.performance_score
                    if hasattr(score, "grade"):
                        metrics["grade"] = score.grade
                    elif hasattr(score, "letter_grade"):
                        metrics["grade"] = score.letter_grade

                # Extract N+1 detection
                if hasattr(last_execution, "django_issues"):
                    django_issues = last_execution.django_issues
                    if hasattr(django_issues, "has_n_plus_one"):
                        metrics["n_plus_one_detected"] = django_issues.has_n_plus_one
            else:
                # If it's a dict already
                metrics = last_execution

        # 4. Last metrics attribute
        if not metrics and hasattr(test, "_last_metrics"):
            logger.debug("Found _last_metrics attribute")
            last_metrics = test._last_metrics
            if hasattr(last_metrics, "__dict__"):
                response_time = getattr(last_metrics, "response_time", 0)
                memory_usage = getattr(last_metrics, "memory_usage", 0)

                metrics = {
                    "response_time_ms": response_time if response_time else 0,
                    "query_count": getattr(last_metrics, "query_count", 0),
                    "memory_usage_mb": memory_usage if memory_usage else 0,
                    "cache_hits": getattr(last_metrics, "cache_hits", 0),
                    "cache_misses": getattr(last_metrics, "cache_misses", 0),
                    "grade": None,
                    "n_plus_one_detected": False,
                }

                # Extract grade
                if hasattr(last_metrics, "performance_score"):
                    score = last_metrics.performance_score
                    if hasattr(score, "grade"):
                        metrics["grade"] = score.grade
                    elif hasattr(score, "letter_grade"):
                        metrics["grade"] = score.letter_grade
                elif hasattr(last_metrics, "grade"):
                    metrics["grade"] = last_metrics.grade

                # Extract N+1 detection
                if hasattr(last_metrics, "django_issues"):
                    django_issues = last_metrics.django_issues
                    if hasattr(django_issues, "has_n_plus_one"):
                        metrics["n_plus_one_detected"] = django_issues.has_n_plus_one
                elif hasattr(last_metrics, "n_plus_one_detected"):
                    metrics["n_plus_one_detected"] = last_metrics.n_plus_one_detected
            else:
                metrics = last_metrics

        # 5. Mercury monitor attribute
        if (
            not metrics
            and hasattr(test, "mercury_monitor")
            and hasattr(test.mercury_monitor, "metrics")
        ):
            logger.debug("Found mercury_monitor attribute")
            monitor = test.mercury_monitor
            monitor_metrics = monitor.metrics

            response_time = getattr(monitor_metrics, "response_time", 0)
            memory_usage = getattr(monitor_metrics, "memory_usage", 0)

            metrics = {
                "response_time_ms": response_time if response_time else 0,
                "query_count": getattr(monitor_metrics, "query_count", 0),
                "memory_usage_mb": memory_usage if memory_usage else 0,
                "cache_hits": getattr(monitor_metrics, "cache_hits", 0),
                "cache_misses": getattr(monitor_metrics, "cache_misses", 0),
                "grade": None,
                "n_plus_one_detected": False,
            }

            # Extract grade
            if hasattr(monitor_metrics, "performance_score"):
                score = monitor_metrics.performance_score
                if hasattr(score, "grade"):
                    metrics["grade"] = score.grade
                elif hasattr(score, "letter_grade"):
                    metrics["grade"] = score.letter_grade
            elif hasattr(monitor_metrics, "grade"):
                metrics["grade"] = monitor_metrics.grade

            # Extract N+1 detection
            if hasattr(monitor_metrics, "django_issues"):
                django_issues = monitor_metrics.django_issues
                if hasattr(django_issues, "has_n_plus_one"):
                    metrics["n_plus_one_detected"] = django_issues.has_n_plus_one
            elif hasattr(monitor_metrics, "n_plus_one_detected"):
                metrics["n_plus_one_detected"] = monitor_metrics.n_plus_one_detected

        # 6. Check if test has a get_metrics method
        if not metrics and hasattr(test, "get_metrics"):
            try:
                metrics = test.get_metrics()
            except:
                pass

        # Return None if no metrics found, otherwise filter out None values
        if not metrics:
            return None

        # Filter out None values
        filtered_metrics = {k: v for k, v in metrics.items() if v is not None}

        # Check if the filtered metrics are meaningful
        # (not just all zeros/defaults)
        has_meaningful_data = (
            filtered_metrics.get("query_count", 0) > 0
            or filtered_metrics.get("response_time_ms", 0) > 0
            or filtered_metrics.get("memory_usage_mb", 0) > 0
            or filtered_metrics.get("cache_hits", 0) > 0
            or filtered_metrics.get("cache_misses", 0) > 0
            or filtered_metrics.get("n_plus_one_detected", False)
            or (filtered_metrics.get("grade") and filtered_metrics.get("grade").strip())
        )

        # Debug log what we're returning
        if has_meaningful_data:
            logger.debug(f"Returning meaningful metrics for {test_name}: {filtered_metrics}")
            return filtered_metrics
        else:
            logger.debug(f"No meaningful metrics found for {test_name}, returning None")
            return None

    def _get_test_name(self, test):
        """Get formatted test name, handling _ErrorHolder objects safely."""
        test_class = test.__class__.__name__

        # Handle _ErrorHolder objects (created for test import/setup errors)
        if test_class == "_ErrorHolder":
            # _ErrorHolder objects don't have _testMethodName, use id() instead
            if hasattr(test, "id"):
                return str(test.id())
            else:
                return f"ErrorHolder.{test_class}"

        # Regular test object - safely access _testMethodName
        test_method = getattr(test, "_testMethodName", "unknown_method")
        return f"{test_class}.{test_method}"
