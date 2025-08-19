"""
Mercury Metrics Tracker

Tracks and analyzes performance metrics for Mercury tests,
providing detailed insights and identifying problematic tests.
"""

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class TestMetrics:
    """Metrics for a single test execution."""

    test_name: str
    query_count: int
    response_time_ms: float
    memory_usage_mb: float
    cache_hits: int = 0
    cache_misses: int = 0
    n_plus_one_detected: bool = False
    grade: str = ""

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class MetricsTracker:
    """
    Tracks and analyzes performance metrics across test execution.
    """

    def __init__(self):
        """Initialize the metrics tracker."""
        self.test_metrics: list[TestMetrics] = []
        self.mercury_test_count = 0
        self.n_plus_one_count = 0
        self.grade_distribution = defaultdict(int)

        # Track extremes for quick access
        self.slowest_test: TestMetrics | None = None
        self.most_queries_test: TestMetrics | None = None
        self.most_memory_test: TestMetrics | None = None

        # Track worst performers (D and F grades)
        self.worst_performers: list[TestMetrics] = []

        # Track ranges
        self.query_range: tuple[int, int] = (float("inf"), 0)
        self.time_range: tuple[float, float] = (float("inf"), 0)
        self.memory_range: tuple[float, float] = (float("inf"), 0)

    def add_metrics(self, metrics: TestMetrics):
        """
        Add metrics for a test execution.

        Args:
            metrics: TestMetrics instance with test performance data
        """
        # Check if metrics are meaningful (not just default/zero values)
        if not self._is_meaningful_metrics(metrics):
            # Don't count tests with empty metrics
            return

        self.test_metrics.append(metrics)
        self.mercury_test_count += 1

        # Update grade distribution
        if metrics.grade:
            self.grade_distribution[metrics.grade] += 1
            # Track worst performers (D and F grades)
            if metrics.grade in ["D", "F"]:
                self.worst_performers.append(metrics)

        # Track N+1 issues
        if metrics.n_plus_one_detected:
            self.n_plus_one_count += 1

        # Update extremes
        if not self.slowest_test or metrics.response_time_ms > self.slowest_test.response_time_ms:
            self.slowest_test = metrics

        if not self.most_queries_test or metrics.query_count > self.most_queries_test.query_count:
            self.most_queries_test = metrics

        if (
            not self.most_memory_test
            or metrics.memory_usage_mb > self.most_memory_test.memory_usage_mb
        ):
            self.most_memory_test = metrics

        # Update ranges
        self.query_range = (
            min(self.query_range[0], metrics.query_count),
            max(self.query_range[1], metrics.query_count),
        )
        self.time_range = (
            min(self.time_range[0], metrics.response_time_ms),
            max(self.time_range[1], metrics.response_time_ms),
        )
        self.memory_range = (
            min(self.memory_range[0], metrics.memory_usage_mb),
            max(self.memory_range[1], metrics.memory_usage_mb),
        )

    # REMOVED: generate_mock_metrics method
    # Mock metrics are useless and misleading
    # Only real metrics from actual test execution should be shown

    def _is_meaningful_metrics(self, metrics: TestMetrics) -> bool:
        """
        Check if metrics contain meaningful data.

        Metrics are considered meaningful if they have:
        - Non-zero query count, response time, or memory usage
        - A performance grade
        - N+1 detection
        - Cache activity

        Args:
            metrics: TestMetrics to check

        Returns:
            True if metrics are meaningful, False if they're empty/default
        """
        # Has a grade (indicates real assessment)
        if metrics.grade and metrics.grade.strip():
            return True

        # Has N+1 detection
        if metrics.n_plus_one_detected:
            return True

        # Has non-zero performance data
        if metrics.query_count > 0 or metrics.response_time_ms > 0 or metrics.memory_usage_mb > 0:
            return True

        # Has cache activity
        if metrics.cache_hits > 0 or metrics.cache_misses > 0:
            return True

        # All values are zero/default - not meaningful
        return False

    def get_insights(self) -> dict[str, any]:
        """
        Get performance insights for display.

        Returns:
            Dictionary with formatted insights
        """
        insights = {
            "mercury_test_count": self.mercury_test_count,
            "n_plus_one_count": self.n_plus_one_count,
            "grade_distribution": dict(self.grade_distribution),
        }

        # Add extremes if available
        if self.slowest_test:
            test_name = self.slowest_test.test_name.split(".")[-1][:20]
            insights["slowest_test"] = f"{test_name}: {self.slowest_test.response_time_ms:.0f}ms"

        if self.most_queries_test:
            test_name = self.most_queries_test.test_name.split(".")[-1][:20]
            insights["most_queries"] = f"{test_name}: {self.most_queries_test.query_count}Q"

        # Add ranges if we have data
        if self.test_metrics:
            if self.query_range[0] != float("inf"):
                insights["query_range"] = f"{self.query_range[0]}-{self.query_range[1]} queries"

            if self.time_range[0] != float("inf"):
                min_time = f"{self.time_range[0]:.0f}ms"
                max_time = f"{self.time_range[1]:.0f}ms"
                insights["time_range"] = f"{min_time}-{max_time}"

        # Calculate averages if we have data
        if self.test_metrics:
            total_queries = sum(m.query_count for m in self.test_metrics)
            total_time = sum(m.response_time_ms for m in self.test_metrics)
            insights["avg_queries"] = total_queries / len(self.test_metrics)
            insights["avg_response_time"] = total_time / len(self.test_metrics)

        return insights

    def get_top_offenders(self, limit: int = 3) -> list[str]:
        """
        Get the tests that need the most optimization.

        Args:
            limit: Maximum number of offenders to return

        Returns:
            List of formatted strings describing problematic tests
        """
        offenders = []

        # Sort tests by "badness" score
        scored_tests = []
        for metrics in self.test_metrics:
            # Calculate badness score (higher is worse)
            score = (
                metrics.response_time_ms / 100  # Normalize response time
                + metrics.query_count * 2  # Queries are bad
                + (50 if metrics.n_plus_one_detected else 0)  # N+1 is very bad
            )
            scored_tests.append((score, metrics))

        # Sort by score (worst first)
        scored_tests.sort(key=lambda x: x[0], reverse=True)

        # Format top offenders
        for _, metrics in scored_tests[:limit]:
            test_name = metrics.test_name.split(".")[-1][:25]

            if metrics.n_plus_one_detected:
                offenders.append(f"🔴 {test_name}: N+1 detected!")
            elif metrics.query_count > 20:
                offenders.append(f"⚠️ {test_name}: {metrics.query_count} queries")
            elif metrics.response_time_ms > 500:
                offenders.append(f"🐌 {test_name}: {metrics.response_time_ms:.0f}ms")
            else:
                offenders.append(f"📊 {test_name}: Grade {metrics.grade}")

        return offenders

    def get_worst_performers(self, limit: int = 3) -> list[str]:
        """
        Get tests with D or F grades that need immediate attention.

        Args:
            limit: Maximum number of worst performers to return

        Returns:
            List of formatted strings describing the worst performing tests
        """
        if not self.worst_performers:
            return []

        # Sort by grade (F first) then by response time
        sorted_worst = sorted(
            self.worst_performers,
            key=lambda m: (0 if m.grade == "F" else 1, -m.response_time_ms),
        )

        worst = []
        for metrics in sorted_worst[:limit]:
            # Get full test name parts - show class and method
            test_parts = metrics.test_name.split(".")
            if len(test_parts) >= 2:
                # Show last two parts: TestClass.test_method
                test_class = (
                    test_parts[-2] if len(test_parts[-2]) <= 30 else test_parts[-2][:27] + "..."
                )
                test_method = (
                    test_parts[-1] if len(test_parts[-1]) <= 40 else test_parts[-1][:37] + "..."
                )
                test_name = f"{test_class}.{test_method}"
            else:
                # Fallback to just the last part if structure is different
                test_name = (
                    test_parts[-1] if len(test_parts[-1]) <= 50 else test_parts[-1][:47] + "..."
                )

            # Identify the main issue - be more specific about what's poor
            issues = []

            # Always show both time and queries for context
            time_str = f"{metrics.response_time_ms:.0f}ms"
            query_str = f"{metrics.query_count}Q" if metrics.query_count > 0 else None

            # Check for specific performance problems
            high_queries = metrics.query_count > 20
            slow_response = metrics.response_time_ms > 200

            # Build the issue string showing both metrics
            if high_queries and slow_response:
                # Both are problematic
                issues.append(f"{time_str}, {metrics.query_count} queries")
            elif high_queries:
                # High query count is the main issue
                issues.append(f"{metrics.query_count} queries")
                if time_str:
                    issues.append(time_str)
            elif slow_response:
                # Slow response is the main issue
                issues.append(f"{time_str} response")
                if query_str:
                    issues.append(query_str)
            else:
                # Neither is particularly high, just show the values
                issues.append(time_str)
                if query_str:
                    issues.append(query_str)

            # Add N+1 detection if present
            if metrics.n_plus_one_detected:
                issues.append("N+1 detected")

            # Add memory if it's significant
            if hasattr(metrics, "memory_usage_mb") and metrics.memory_usage_mb > 100:
                issues.append(f"{metrics.memory_usage_mb:.0f}MB")

            issue_str = ", ".join(issues)

            if metrics.grade == "F":
                worst.append(f"❌ {test_name}: Grade F ({issue_str})")
            else:  # Grade D
                worst.append(f"⚠️ {test_name}: Grade D ({issue_str})")

        return worst

    def format_for_display(self) -> dict[str, str]:
        """
        Format metrics for visual display panel.

        Returns:
            Dictionary with formatted strings for display
        """
        insights = self.get_insights()
        display = {}

        # Format key metrics
        display["test_count"] = str(insights.get("mercury_test_count", 0))

        if "most_queries" in insights:
            display["most_queries"] = insights["most_queries"]

        if "slowest_test" in insights:
            display["slowest_test"] = insights["slowest_test"]

        if "query_range" in insights:
            display["query_range"] = insights["query_range"]

        if "time_range" in insights:
            display["time_range"] = insights["time_range"]

        # Format N+1 detection
        if insights.get("n_plus_one_count", 0) > 0:
            display["n_plus_one"] = str(insights["n_plus_one_count"])

        # Format grade distribution - include A+ grade!
        if insights.get("grade_distribution"):
            grades = []
            for grade in ["S", "A+", "A", "B", "C", "D", "F"]:
                count = insights["grade_distribution"].get(grade, 0)
                if count > 0:
                    grades.append(f"{grade}:{count}")
            if grades:
                display["grades"] = " ".join(grades)

        # Get worst performers if any
        worst = self.get_worst_performers(limit=3)
        if worst:
            display["worst_performers"] = worst

        return display


class IsolationIssueDetector:
    """
    Detects potential test isolation issues based on error patterns.

    Test isolation issues occur when tests share mutable state and interfere
    with each other. Common in Django when using setUpTestData() incorrectly.
    """

    # Error patterns that suggest isolation issues
    ISOLATION_PATTERNS = {
        "DoesNotExist": "Data expected by test was deleted or modified by another test",
        "does not exist": "Data expected by test was deleted or modified by another test",
        "already accepted": "Shared state was modified by another test",
        "already exists": "Data conflicts due to shared state between tests",
        "Permission denied": "User context or permissions changed between tests",
        "IntegrityError": "Database constraints violated due to shared state",
        "duplicate key": "Attempting to create data that already exists from another test",
        "UNIQUE constraint failed": "Data uniqueness violated due to test interference",
        "Cannot delete": "Referenced by data from another test",
    }

    def __init__(self):
        """Initialize the isolation detector."""
        self.detected_issues = {}  # Track issues per test
        self.isolation_candidates = set()  # Tests likely having isolation issues

    def analyze_failure(self, test_name: str, error: str) -> str | None:
        """
        Analyze a test failure to detect potential isolation issues.

        Args:
            test_name: Full test name (e.g., TestClass.test_method)
            error: Error message or traceback

        Returns:
            Description of isolation issue if detected, None otherwise
        """
        error_str = str(error).lower()

        # Check each pattern
        for pattern, description in self.ISOLATION_PATTERNS.items():
            if pattern.lower() in error_str:
                # Store detection for this test
                if test_name not in self.detected_issues:
                    self.detected_issues[test_name] = []
                self.detected_issues[test_name].append(
                    {"pattern": pattern, "description": description}
                )
                self.isolation_candidates.add(test_name)
                return description

        return None

    def is_likely_isolation_issue(self, test_name: str) -> bool:
        """
        Check if a test likely has isolation issues.

        Args:
            test_name: Test name to check

        Returns:
            True if test likely has isolation issues
        """
        return test_name in self.isolation_candidates

    def get_isolation_summary(self) -> dict[str, list[str]]:
        """
        Get a summary of all detected isolation issues.

        Returns:
            Dictionary mapping test names to list of issue descriptions
        """
        summary = {}
        for test_name, issues in self.detected_issues.items():
            summary[test_name] = list({issue["description"] for issue in issues})
        return summary

    def get_fix_suggestions(self, test_name: str) -> list[str]:
        """
        Get specific fix suggestions for a test with isolation issues.

        Args:
            test_name: Test name

        Returns:
            List of suggested fixes
        """
        if test_name not in self.detected_issues:
            return []

        suggestions = []
        patterns = {issue["pattern"] for issue in self.detected_issues[test_name]}

        if "DoesNotExist" in patterns or "does not exist" in patterns:
            suggestions.extend(
                [
                    "Move mutable test data from setUpTestData() to setUp()",
                    "Create fresh instances for data that will be modified",
                    "Check if other tests are deleting shared data",
                ]
            )

        if "already accepted" in patterns or "already exists" in patterns:
            suggestions.extend(
                [
                    "Use setUp() instead of setUpTestData() for friend requests",
                    "Create unique test data for each test method",
                    "Consider using factory methods for test data creation",
                ]
            )

        if "Permission denied" in patterns:
            suggestions.extend(
                [
                    "Ensure each test sets up its own user context",
                    "Don't modify shared user permissions in tests",
                    "Use separate test users for different permission scenarios",
                ]
            )

        if "IntegrityError" in patterns or "UNIQUE constraint" in patterns:
            suggestions.extend(
                [
                    "Use unique values for each test (e.g., timestamps, UUIDs)",
                    "Clean up test data properly in tearDown() if needed",
                    "Consider using TransactionTestCase for complex scenarios",
                ]
            )

        return list(set(suggestions))  # Remove duplicates


# Global tracker instance
_global_tracker: MetricsTracker | None = None


def get_global_tracker() -> MetricsTracker:
    """Get or create the global metrics tracker."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = MetricsTracker()
    return _global_tracker


def reset_global_tracker():
    """Reset the global metrics tracker."""
    global _global_tracker
    _global_tracker = MetricsTracker()
