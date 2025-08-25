"""
Tests for pure Python performance monitoring implementation.

Tests the core orchestrator functionality that replaces C extensions.
This covers the heart of Django Mercury's pure Python fallback system.
"""

import unittest
from unittest.mock import Mock, patch
import time

from django_mercury.python_bindings.pure_python import (
    PythonPerformanceMetrics,
    PythonPerformanceMonitor,
    PythonTestOrchestrator,
    PythonQueryAnalyzer,
    PSUTIL_AVAILABLE,
    TRACEMALLOC_AVAILABLE,
)


class TestPythonPerformanceMetrics(unittest.TestCase):
    """Test the metrics data container."""

    def test_default_initialization(self):
        """Test metrics initialize with correct defaults."""
        metrics = PythonPerformanceMetrics()

        self.assertEqual(metrics.response_time_ms, 0.0)
        self.assertEqual(metrics.memory_usage_mb, 0.0)
        self.assertEqual(metrics.peak_memory_mb, 0.0)
        self.assertEqual(metrics.query_count, 0)
        self.assertEqual(metrics.queries, [])
        self.assertEqual(metrics.cache_hits, 0)
        self.assertEqual(metrics.cache_misses, 0)
        self.assertEqual(metrics.cpu_percent, 0.0)
        self.assertEqual(metrics.errors, [])

    def test_custom_initialization(self):
        """Test metrics can be initialized with custom values."""
        queries = [{"sql": "SELECT 1", "time": 0.1}]
        errors = ["Test error"]

        metrics = PythonPerformanceMetrics(
            response_time_ms=100.5,
            memory_usage_mb=50.2,
            query_count=1,
            queries=queries,
            errors=errors,
        )

        self.assertEqual(metrics.response_time_ms, 100.5)
        self.assertEqual(metrics.memory_usage_mb, 50.2)
        self.assertEqual(metrics.query_count, 1)
        self.assertEqual(metrics.queries, queries)
        self.assertEqual(metrics.errors, errors)


class TestPythonPerformanceMonitor(unittest.TestCase):
    """Test the performance monitoring implementation."""

    def setUp(self):
        """Set up test monitor."""
        self.monitor = PythonPerformanceMonitor()

    def test_initialization(self):
        """Test monitor initializes correctly."""
        self.assertIsInstance(self.monitor.metrics, PythonPerformanceMetrics)
        self.assertIsNone(self.monitor._start_time)
        self.assertIsNone(self.monitor._start_memory)
        self.assertFalse(self.monitor._monitoring)

    @patch("django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE", True)
    @patch("django_mercury.python_bindings.pure_python.psutil")
    def test_psutil_process_initialization(self, mock_psutil):
        """Test process initialization when psutil is available."""
        mock_process = Mock()
        mock_psutil.Process.return_value = mock_process

        monitor = PythonPerformanceMonitor()

        mock_psutil.Process.assert_called_once()
        self.assertEqual(monitor._process, mock_process)

    @patch("time.perf_counter", return_value=1000.0)
    @patch("gc.collect")
    def test_start_monitoring_basic(self, mock_gc, mock_time):
        """Test basic start monitoring functionality."""
        self.monitor.start_monitoring()

        self.assertTrue(self.monitor._monitoring)
        self.assertEqual(self.monitor._start_time, 1000.0)
        mock_gc.assert_called_once()

    @patch("time.perf_counter", side_effect=[1000.0, 1001.5])
    def test_stop_monitoring_basic(self, mock_time):
        """Test basic stop monitoring functionality."""
        # Start monitoring first
        self.monitor.start_monitoring()

        # Stop monitoring
        self.monitor.stop_monitoring()

        self.assertFalse(self.monitor._monitoring)
        self.assertEqual(self.monitor.metrics.response_time_ms, 1500.0)  # 1.5s * 1000

    def test_get_metrics(self):
        """Test getting current metrics."""
        test_metrics = PythonPerformanceMetrics(response_time_ms=100.0)
        self.monitor.metrics = test_metrics

        result = self.monitor.get_metrics()

        # get_metrics returns a dictionary, not the dataclass
        self.assertEqual(result["response_time_ms"], 100.0)
        self.assertEqual(result["implementation"], "pure_python")
        self.assertIsInstance(result, dict)


class TestPythonQueryAnalyzer(unittest.TestCase):
    """Test the query analysis functionality."""

    def setUp(self):
        """Set up test analyzer."""
        self.analyzer = PythonQueryAnalyzer()

    def test_initialization(self):
        """Test analyzer initializes correctly."""
        self.assertEqual(self.analyzer.queries, [])
        self.assertEqual(self.analyzer.analysis_cache, {})

    def test_analyze_select_query(self):
        """Test analyzing a SELECT query."""
        sql = "SELECT id, name FROM users WHERE age > 25 ORDER BY name"

        result = self.analyzer.analyze_query(sql)

        self.assertEqual(result["type"], "SELECT")
        self.assertTrue(result["has_order_by"])
        self.assertFalse(result["has_group_by"])
        self.assertFalse(result["has_join"])
        self.assertFalse(result["has_subquery"])
        self.assertIn("users", result["tables"])
        self.assertEqual(result["implementation"], "pure_python")

    def test_analyze_query_with_join(self):
        """Test analyzing a query with JOIN."""
        sql = "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id"

        result = self.analyzer.analyze_query(sql)

        self.assertEqual(result["type"], "SELECT")
        self.assertTrue(result["has_join"])
        self.assertIn("users", result["tables"])
        self.assertIn("posts", result["tables"])

    def test_analyze_query_with_subquery(self):
        """Test analyzing a query with subquery."""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM posts)"

        result = self.analyzer.analyze_query(sql)

        self.assertEqual(result["type"], "SELECT")
        self.assertTrue(result["has_subquery"])
        self.assertIn("Consider using JOINs instead of subqueries", result["recommendations"])

    def test_analyze_query_without_limit(self):
        """Test recommendation for missing LIMIT."""
        sql = "SELECT * FROM users WHERE active = 1"

        result = self.analyzer.analyze_query(sql)

        self.assertIn("Consider adding LIMIT for large result sets", result["recommendations"])

    def test_query_type_detection(self):
        """Test different query types are detected correctly."""
        test_cases = [
            ("SELECT * FROM users", "SELECT"),
            ("INSERT INTO users (name) VALUES ('test')", "INSERT"),
            ("UPDATE users SET name = 'test'", "UPDATE"),
            ("DELETE FROM users WHERE id = 1", "DELETE"),
            ("CREATE TABLE test (id INT)", "OTHER"),
        ]

        for sql, expected_type in test_cases:
            result = self.analyzer.analyze_query(sql)
            self.assertEqual(result["type"], expected_type, f"Failed for SQL: {sql}")

    def test_analysis_caching(self):
        """Test that analysis results are cached."""
        sql = "SELECT * FROM users"

        # First call
        result1 = self.analyzer.analyze_query(sql)

        # Second call should return cached result
        result2 = self.analyzer.analyze_query(sql)

        self.assertIs(result1, result2)  # Same object reference
        self.assertIn(sql, self.analyzer.analysis_cache)


class TestPythonTestOrchestrator(unittest.TestCase):
    """Test the test orchestration functionality."""

    def setUp(self):
        """Set up test orchestrator."""
        self.orchestrator = PythonTestOrchestrator()

    def test_initialization(self):
        """Test orchestrator initializes correctly."""
        self.assertIsNone(self.orchestrator.current_test)
        self.assertEqual(self.orchestrator.test_results, [])
        self.assertEqual(self.orchestrator.contexts, {})
        self.assertEqual(self.orchestrator.monitors, {})

    @patch("time.time", return_value=1234567890.0)
    def test_start_test(self, mock_time):
        """Test starting a test."""
        test_name = "test_example"

        self.orchestrator.start_test(test_name)

        self.assertIsNotNone(self.orchestrator.current_test)
        self.assertEqual(self.orchestrator.current_test["name"], test_name)
        self.assertEqual(self.orchestrator.current_test["start_time"], 1234567890.0)
        self.assertIn(test_name, self.orchestrator.monitors)

    @patch("time.time", return_value=1234567895.0)
    def test_end_test_success(self, mock_time):
        """Test ending a test successfully."""
        test_name = "test_example"

        # Setup: start a test first
        with patch("time.time", return_value=1234567890.0):
            self.orchestrator.start_test(test_name)

        # End the test
        result = self.orchestrator.end_test(test_name, "passed")

        self.assertIsNone(self.orchestrator.current_test)
        self.assertEqual(result["name"], test_name)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["duration"], 5.0)  # 5 seconds
        self.assertNotIn(test_name, self.orchestrator.monitors)

    def test_end_test_no_current_test(self):
        """Test ending test when no test is running."""
        result = self.orchestrator.end_test("test_example", "passed")

        self.assertEqual(result, {})  # Empty result

    def test_end_test_wrong_name(self):
        """Test ending test with wrong name."""
        # Start a test
        self.orchestrator.start_test("actual_test")

        # Try to end different test
        result = self.orchestrator.end_test("wrong_test", "passed")

        self.assertEqual(result, {})  # Empty result
        # Current test should remain
        self.assertIsNotNone(self.orchestrator.current_test)
        self.assertEqual(self.orchestrator.current_test["name"], "actual_test")

    def test_get_summary_empty(self):
        """Test getting summary with no tests."""
        summary = self.orchestrator.get_summary()

        self.assertEqual(summary["total_tests"], 0)
        self.assertEqual(summary["passed"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["implementation"], "pure_python")

    def test_get_summary_with_tests(self):
        """Test getting summary with completed tests."""
        # Add some test data
        self.orchestrator.test_results = [
            {"status": "passed", "duration": 1.0, "response_time_ms": 100},
            {"status": "failed", "duration": 2.0, "response_time_ms": 200},
            {"status": "passed", "duration": 3.0, "response_time_ms": 300},
        ]

        summary = self.orchestrator.get_summary()

        self.assertEqual(summary["total_tests"], 3)
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["total_duration"], 6.0)

    def test_get_orchestrator_statistics(self):
        """Test getting orchestrator statistics."""
        # Add some test history
        self.orchestrator.total_tests_executed = 5
        self.orchestrator.total_violations = 2
        self.orchestrator.total_n_plus_one_detected = 1

        stats = self.orchestrator.get_orchestrator_statistics()

        self.assertEqual(stats[0], 5)  # total_tests_executed
        self.assertEqual(stats[1], 2)  # total_violations
        self.assertEqual(stats[2], 1)  # total_n_plus_one_detected


if __name__ == "__main__":
    unittest.main()
