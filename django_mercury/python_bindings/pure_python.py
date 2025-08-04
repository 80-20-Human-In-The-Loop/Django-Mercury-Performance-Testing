"""
Pure Python fallback implementations for Django Mercury C extensions.

These implementations provide the same API as the C extensions but with
reduced performance. They ensure Django Mercury works on all platforms,
even when C extensions cannot be compiled or loaded.
"""

import time
import gc
import sys
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import tracemalloc

    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False


@dataclass
class PythonPerformanceMetrics:
    """Container for performance metrics collected by pure Python implementation."""

    response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    peak_memory_mb: float = 0.0
    query_count: int = 0
    queries: List[Dict[str, Any]] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0
    cpu_percent: float = 0.0
    errors: List[str] = field(default_factory=list)


class PythonPerformanceMonitor:
    """
    Pure Python implementation of performance monitoring.

    This provides the same interface as the C extension but uses
    Python libraries for measurement. Performance overhead is higher
    but functionality is identical.
    """

    def __init__(self):
        self.metrics = PythonPerformanceMetrics()
        self._start_time = None
        self._start_memory = None
        self._tracemalloc_snapshot = None
        self._process = None
        self._monitoring = False

        # Initialize process monitor if available
        if PSUTIL_AVAILABLE:
            try:
                self._process = psutil.Process()
            except Exception:
                pass

    def start_monitoring(self) -> None:
        """Start collecting performance metrics."""
        if self._monitoring:
            return

        self._monitoring = True
        self.metrics = PythonPerformanceMetrics()  # Reset metrics

        # Start timing
        self._start_time = time.perf_counter()

        # Garbage collect before measuring memory
        gc.collect()

        # Start memory tracking
        if TRACEMALLOC_AVAILABLE:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            self._tracemalloc_snapshot = tracemalloc.take_snapshot()

        # Get baseline memory usage
        if self._process:
            try:
                mem_info = self._process.memory_info()
                self._start_memory = mem_info.rss / 1024 / 1024  # Convert to MB
            except Exception:
                self._start_memory = 0

    def stop_monitoring(self) -> None:
        """Stop collecting metrics and calculate final values."""
        if not self._monitoring:
            return

        self._monitoring = False

        # Calculate response time
        if self._start_time:
            elapsed = time.perf_counter() - self._start_time
            self.metrics.response_time_ms = elapsed * 1000

        # Calculate memory usage
        if TRACEMALLOC_AVAILABLE and self._tracemalloc_snapshot:
            try:
                current_snapshot = tracemalloc.take_snapshot()
                stats = current_snapshot.compare_to(self._tracemalloc_snapshot, "lineno")

                # Calculate total memory difference
                total_diff = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
                self.metrics.memory_usage_mb = total_diff / 1024 / 1024
            except Exception as e:
                self.metrics.errors.append(f"Memory tracking error: {e}")

        # Get peak memory and CPU usage
        if self._process:
            try:
                # Memory
                mem_info = self._process.memory_info()
                current_memory = mem_info.rss / 1024 / 1024
                self.metrics.peak_memory_mb = max(current_memory, self._start_memory or 0)

                # CPU
                self.metrics.cpu_percent = self._process.cpu_percent()
            except Exception as e:
                self.metrics.errors.append(f"Process monitoring error: {e}")

    def track_query(self, sql: str, duration: float = 0.0) -> None:
        """
        Track a database query execution.

        Args:
            sql: The SQL query string
            duration: Query execution time in seconds
        """
        self.metrics.query_count += 1
        self.metrics.queries.append(
            {
                "sql": sql,
                "duration_ms": duration * 1000,
                "timestamp": time.time(),
            }
        )

    def track_cache(self, hit: bool) -> None:
        """
        Track cache access.

        Args:
            hit: True for cache hit, False for cache miss
        """
        if hit:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics as a dictionary.

        Returns:
            Dictionary containing all collected metrics
        """
        return {
            "response_time_ms": self.metrics.response_time_ms,
            "memory_usage_mb": self.metrics.memory_usage_mb,
            "peak_memory_mb": self.metrics.peak_memory_mb,
            "query_count": self.metrics.query_count,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cpu_percent": self.metrics.cpu_percent,
            "implementation": "pure_python",
            "errors": self.metrics.errors,
        }

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.metrics = PythonPerformanceMetrics()
        self._start_time = None
        self._start_memory = None
        self._tracemalloc_snapshot = None
        self._monitoring = False


class PythonMetricsEngine:
    """
    Pure Python implementation of metrics aggregation and analysis.
    """

    def __init__(self):
        self.metrics_history = []
        self.aggregated_metrics = {}

    def add_metrics(self, metrics: Dict[str, Any]) -> None:
        """Add metrics to history for aggregation."""
        self.metrics_history.append(
            {
                "timestamp": time.time(),
                "metrics": metrics,
            }
        )

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistical summaries of collected metrics."""
        if not self.metrics_history:
            return {
                "count": 0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std_dev": 0.0,
                "total_queries": 0,
                "implementation": "pure_python",
            }

        # Extract response times
        response_times = [m["metrics"].get("response_time_ms", 0) for m in self.metrics_history]

        # Extract query counts
        query_counts = [m["metrics"].get("query_count", 0) for m in self.metrics_history]

        # Calculate statistics
        count = len(response_times)
        if count == 0:
            mean = 0.0
            min_val = 0.0
            max_val = 0.0
            std_dev = 0.0
        else:
            mean = sum(response_times) / count
            min_val = min(response_times)
            max_val = max(response_times)

            # Calculate standard deviation
            variance = sum((x - mean) ** 2 for x in response_times) / count
            std_dev = variance**0.5

        return {
            "count": count,
            "mean": mean,
            "min": min_val,
            "max": max_val,
            "std_dev": std_dev,
            "total_queries": sum(query_counts),
            "implementation": "pure_python",
        }

    def detect_n_plus_one(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect N+1 query patterns.

        Args:
            queries: List of query dictionaries

        Returns:
            Dictionary with N+1 detection results
        """
        if not queries:
            return {"detected": False, "count": 0}

        # Group queries by pattern (simplified)
        query_patterns = {}
        for query in queries:
            sql = query.get("sql", "")
            # Simple pattern extraction (remove values)
            pattern = self._extract_pattern(sql)

            if pattern not in query_patterns:
                query_patterns[pattern] = []
            query_patterns[pattern].append(query)

        # Detect N+1 (same pattern repeated many times)
        n_plus_one_detected = False
        suspicious_patterns = []

        for pattern, pattern_queries in query_patterns.items():
            if len(pattern_queries) > 10:  # Threshold for N+1 detection
                n_plus_one_detected = True
                suspicious_patterns.append(
                    {
                        "pattern": pattern[:100],  # Truncate for display
                        "count": len(pattern_queries),
                        "total_time_ms": sum(q.get("duration_ms", 0) for q in pattern_queries),
                    }
                )

        return {
            "detected": n_plus_one_detected,
            "suspicious_patterns": suspicious_patterns,
            "total_patterns": len(query_patterns),
            "implementation": "pure_python",
        }

    def _extract_pattern(self, sql: str) -> str:
        """Extract pattern from SQL by removing values."""
        import re

        # Remove numbers
        pattern = re.sub(r"\b\d+\b", "?", sql)
        # Remove quoted strings
        pattern = re.sub(r"'[^']*'", "?", pattern)
        pattern = re.sub(r'"[^"]*"', "?", pattern)
        return pattern.strip()


class PythonQueryAnalyzer:
    """
    Pure Python implementation of SQL query analysis.
    """

    def __init__(self):
        self.queries = []
        self.analysis_cache = {}

    def analyze_query(self, sql: str) -> Dict[str, Any]:
        """
        Analyze a SQL query for performance issues.

        Args:
            sql: SQL query string

        Returns:
            Dictionary with analysis results
        """
        # Check cache
        if sql in self.analysis_cache:
            return self.analysis_cache[sql]

        analysis = {
            "query": sql[:200],  # Truncate for storage
            "type": self._get_query_type(sql),
            "tables": self._extract_tables(sql),
            "has_join": "JOIN" in sql.upper(),
            "has_subquery": "(SELECT" in sql.upper(),
            "has_order_by": "ORDER BY" in sql.upper(),
            "has_group_by": "GROUP BY" in sql.upper(),
            "estimated_complexity": self._estimate_complexity(sql),
            "recommendations": [],
            "implementation": "pure_python",
        }

        # Add recommendations
        if analysis["has_subquery"]:
            analysis["recommendations"].append("Consider using JOINs instead of subqueries")

        if not "LIMIT" in sql.upper() and analysis["type"] == "SELECT":
            analysis["recommendations"].append("Consider adding LIMIT for large result sets")

        if analysis["estimated_complexity"] >= 5:
            analysis["recommendations"].append("Query appears complex, consider optimization")

        # Cache the result
        self.analysis_cache[sql] = analysis

        return analysis

    def _get_query_type(self, sql: str) -> str:
        """Determine the type of SQL query."""
        sql_upper = sql.strip().upper()

        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        else:
            return "OTHER"

    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL query (simplified)."""
        import re

        # Simple regex to find table names after FROM and JOIN
        tables = []

        # Find tables after FROM
        from_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
        if from_match:
            tables.append(from_match.group(1))

        # Find tables after JOIN
        join_matches = re.findall(r"JOIN\s+(\w+)", sql, re.IGNORECASE)
        tables.extend(join_matches)

        return list(set(tables))  # Remove duplicates

    def _estimate_complexity(self, sql: str) -> int:
        """Estimate query complexity (0-10 scale)."""
        complexity = 1

        sql_upper = sql.upper()

        # Add complexity for various operations
        if "JOIN" in sql_upper:
            complexity += sql_upper.count("JOIN")
        if "SUBQUERY" in sql_upper or "(SELECT" in sql_upper:
            complexity += 2
        if "GROUP BY" in sql_upper:
            complexity += 1
        if "ORDER BY" in sql_upper:
            complexity += 1
        if "DISTINCT" in sql_upper:
            complexity += 1
        if "UNION" in sql_upper:
            complexity += 2

        return min(complexity, 10)  # Cap at 10


class PythonTestOrchestrator:
    """
    Pure Python implementation of test orchestration and coordination.
    """

    def __init__(self):
        self.test_results = []
        self.current_test = None
        self.monitors = {}

    def start_test(self, test_name: str) -> None:
        """Start monitoring a test."""
        self.current_test = {
            "name": test_name,
            "start_time": time.time(),
            "metrics": {},
            "status": "running",
        }

        # Create monitor for this test
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        self.monitors[test_name] = monitor

    def end_test(self, test_name: str, status: str = "passed") -> Dict[str, Any]:
        """
        End monitoring a test and collect results.

        Args:
            test_name: Name of the test
            status: Test status ('passed', 'failed', 'skipped')

        Returns:
            Dictionary with test results
        """
        if test_name not in self.monitors:
            return {}

        # Stop monitoring
        monitor = self.monitors[test_name]
        monitor.stop_monitoring()

        # Always clean up the monitor
        del self.monitors[test_name]

        # Collect results if this is the current test
        if self.current_test and self.current_test["name"] == test_name:
            self.current_test["end_time"] = time.time()
            self.current_test["duration"] = (
                self.current_test["end_time"] - self.current_test["start_time"]
            )
            self.current_test["status"] = status
            self.current_test["metrics"] = monitor.get_metrics()

            # Add to results
            self.test_results.append(self.current_test)

            # Clean up current test
            result = self.current_test.copy()
            self.current_test = None

            return result

        return {}

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        if not self.test_results:
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "implementation": "pure_python",
            }

        passed = sum(1 for t in self.test_results if t["status"] == "passed")
        failed = sum(1 for t in self.test_results if t["status"] == "failed")

        total_time = sum(t.get("duration", 0) for t in self.test_results)
        avg_response_time = (
            sum(t.get("metrics", {}).get("response_time_ms", 0) for t in self.test_results)
            / len(self.test_results)
            if self.test_results
            else 0
        )

        return {
            "total_tests": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "total_duration": total_time,
            "avg_response_time_ms": avg_response_time,
            "implementation": "pure_python",
        }


# Convenience context manager
@contextmanager
def python_performance_monitor():
    """Context manager for performance monitoring."""
    monitor = PythonPerformanceMonitor()
    monitor.start_monitoring()
    try:
        yield monitor
    finally:
        monitor.stop_monitoring()
