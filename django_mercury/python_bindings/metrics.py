# backend/performance_testing/python_bindings/metrics.py - Performance metrics classes
# Defines data structures for capturing and analyzing performance metrics with a modern, type-safe API.

# --- Standard Library Imports ---
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

# --- Enums and Data Classes ---


class PerformanceStatus(Enum):
    """
    Enumeration for performance status indicators.
    """

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    SLOW = "slow"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """
    A data class for storing and analyzing performance metrics.

    This class provides a type-safe structure for performance data and includes
    methods for evaluating performance against predefined thresholds.

    Attributes:
        response_time (float): The response time in milliseconds.
        memory_usage (float): The memory usage in megabytes.
        query_count (int): The number of database queries executed.
        operation_name (str): The name of the operation being measured.
    """

    response_time: float
    memory_usage: float
    query_count: int = 0
    operation_name: str = ""

    _response_time_thresholds: Dict[str, float] = None
    _memory_thresholds: Dict[str, float] = None

    def __post_init__(self):
        """Initializes default performance thresholds after the object is created."""
        if self._response_time_thresholds is None:
            self._response_time_thresholds = {
                "excellent": 50.0,
                "good": 100.0,
                "acceptable": 300.0,
                "slow": 500.0,
            }

        if self._memory_thresholds is None:
            self._memory_thresholds = {
                "excellent": 20.0,
                "good": 50.0,
                "acceptable": 100.0,
                "slow": 200.0,
            }

    def __str__(self) -> str:
        """Returns a human-readable string representation of the metrics."""
        status_icon = self._get_status_icon()
        return f"{status_icon} {self.operation_name}: {self.response_time:.2f}ms, {self.memory_usage:.2f}MB"

    def __repr__(self) -> str:
        """Returns a developer-friendly, unambiguous representation of the object."""
        return (
            f"PerformanceMetrics(response_time={self.response_time:.2f}, "
            f"memory_usage={self.memory_usage:.2f}, operation_name='{self.operation_name}')"
        )

    # -- Property Methods for Status Checks --

    @property
    def is_fast(self) -> bool:
        """Returns True if the response time is considered fast (under 100ms)."""
        return self.response_time < self._response_time_thresholds["good"]

    @property
    def is_slow(self) -> bool:
        """Returns True if the response time is considered slow (over 500ms)."""
        return self.response_time > self._response_time_thresholds["slow"]

    @property
    def is_memory_intensive(self) -> bool:
        """Returns True if memory usage is high (over 100MB)."""
        return self.memory_usage > self._memory_thresholds["acceptable"]

    @property
    def has_query_issues(self) -> bool:
        """Returns True if the query count is high (suggesting N+1 problems)."""
        return self.query_count > 10

    @property
    def performance_status(self) -> PerformanceStatus:
        """Assesses and returns the overall performance status based on response time."""
        if self.response_time <= self._response_time_thresholds["excellent"]:
            return PerformanceStatus.EXCELLENT
        if self.response_time <= self._response_time_thresholds["good"]:
            return PerformanceStatus.GOOD
        if self.response_time <= self._response_time_thresholds["acceptable"]:
            return PerformanceStatus.ACCEPTABLE
        if self.response_time <= self._response_time_thresholds["slow"]:
            return PerformanceStatus.SLOW
        return PerformanceStatus.CRITICAL

    @property
    def memory_status(self) -> PerformanceStatus:
        """Assesses and returns the memory usage status."""
        if self.memory_usage <= self._memory_thresholds["excellent"]:
            return PerformanceStatus.EXCELLENT
        if self.memory_usage <= self._memory_thresholds["good"]:
            return PerformanceStatus.GOOD
        if self.memory_usage <= self._memory_thresholds["acceptable"]:
            return PerformanceStatus.ACCEPTABLE
        if self.memory_usage <= self._memory_thresholds["slow"]:
            return PerformanceStatus.SLOW
        return PerformanceStatus.CRITICAL

    def _get_status_icon(self) -> str:
        """Returns a visual icon representing the performance status."""
        status = self.performance_status
        icons = {
            PerformanceStatus.EXCELLENT: "🚀",
            PerformanceStatus.GOOD: "✅",
            PerformanceStatus.ACCEPTABLE: "⚠️",
            PerformanceStatus.SLOW: "🐌",
            PerformanceStatus.CRITICAL: "🚨",
        }
        return icons.get(status, "📊")

    # -- Reporting and Analysis Methods --

    def detailed_report(self) -> str:
        """
        Generates a detailed, human-readable performance report.

        Returns:
            str: A formatted string with a detailed performance breakdown and recommendations.
        """
        lines = [
            f"📊 Performance Report: {self.operation_name}",
            f"   - Response Time: {self.response_time:.2f}ms ({self.performance_status.value})",
            f"   - Memory Usage: {self.memory_usage:.2f}MB ({self.memory_status.value})",
        ]

        if self.query_count > 0:
            lines.append(f"   - Database Queries: {self.query_count}")

        recommendations = self._get_recommendations()
        if recommendations:
            lines.append("   - Recommendations:")
            for rec in recommendations:
                lines.append(f"     • {rec}")

        return "\n".join(lines)

    def _get_recommendations(self) -> List[str]:
        """Generates a list of performance optimization recommendations."""
        recommendations = []
        if self.is_slow:
            recommendations.append("Optimize database queries or implement caching.")
        if self.is_memory_intensive:
            recommendations.append("Review memory usage; consider pagination or data limiting.")
        if self.has_query_issues:
            recommendations.append(
                "Check for N+1 query patterns; use select_related/prefetch_related."
            )
        return recommendations

    def meets_thresholds(
        self,
        max_response_time: Optional[float] = None,
        max_memory_mb: Optional[float] = None,
        max_queries: Optional[int] = None,
    ) -> bool:
        """
        Checks if performance metrics are within specified thresholds.

        Args:
            max_response_time (Optional[float]): Maximum allowed response time in ms.
            max_memory_mb (Optional[float]): Maximum allowed memory usage in MB.
            max_queries (Optional[int]): Maximum allowed number of database queries.

        Returns:
            bool: True if all metrics are within the given thresholds, False otherwise.
        """
        if max_response_time is not None and self.response_time > max_response_time:
            return False
        if max_memory_mb is not None and self.memory_usage > max_memory_mb:
            return False
        if max_queries is not None and self.query_count > max_queries:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the performance metrics to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the metrics.
        """
        return {
            "response_time": self.response_time,
            "memory_usage": self.memory_usage,
            "query_count": self.query_count,
            "operation_name": self.operation_name,
            "performance_status": self.performance_status.value,
            "memory_status": self.memory_status.value,
            "is_fast": self.is_fast,
            "is_slow": self.is_slow,
            "is_memory_intensive": self.is_memory_intensive,
            "has_query_issues": self.has_query_issues,
        }


# --- Comparison Reporting ---


@dataclass
class ComparisonReport:
    """
    A data class for comparing two sets of performance metrics.

    This is useful for identifying performance regressions or improvements between
    a baseline and a new set of metrics.

    Attributes:
        baseline (PerformanceMetrics): The baseline metrics for comparison.
        current (PerformanceMetrics): The current metrics being compared.
    """

    baseline: PerformanceMetrics
    current: PerformanceMetrics

    @property
    def response_time_change(self) -> float:
        """Calculates the percentage change in response time."""
        if self.baseline.response_time == 0:
            return 0.0
        return (
            (self.current.response_time - self.baseline.response_time) / self.baseline.response_time
        ) * 100

    @property
    def memory_change(self) -> float:
        """Calculates the percentage change in memory usage."""
        if self.baseline.memory_usage == 0:
            return 0.0
        return (
            (self.current.memory_usage - self.baseline.memory_usage) / self.baseline.memory_usage
        ) * 100

    @property
    def is_regression(self) -> bool:
        """Returns True if performance has significantly degraded ( > 20% increase)."""
        return self.response_time_change > 20 or self.memory_change > 20

    @property
    def is_improvement(self) -> bool:
        """Returns True if performance has significantly improved ( > 10% decrease)."""
        return self.response_time_change < -10 or self.memory_change < -10

    def __str__(self) -> str:
        """Returns a human-readable string summarizing the performance comparison."""
        response_symbol = "📈" if self.response_time_change > 0 else "📉"
        memory_symbol = "📈" if self.memory_change > 0 else "📉"

        return (
            f"🔄 Performance Comparison: {self.current.operation_name}\n"
            f"   - Response Time: {response_symbol} {self.response_time_change:+.1f}%\n"
            f"   - Memory Usage:  {memory_symbol} {self.memory_change:+.1f}%"
        )


# --- Test Execution ---

if __name__ == "__main__":
    # Example usage and demonstration of the metrics classes.
    metrics = PerformanceMetrics(
        response_time=85.5, memory_usage=45.2, operation_name="UserListView.get"
    )

    print(metrics)
    print("\n--- Detailed Report ---")
    print(metrics.detailed_report())

    print("\n--- Status Checks ---")
    print(f"Is fast: {metrics.is_fast}")
    print(f"Is slow: {metrics.is_slow}")
    print(f"Performance status: {metrics.performance_status}")
    print(f"Meets thresholds (100ms, 50MB): {metrics.meets_thresholds(100, 50)}")
