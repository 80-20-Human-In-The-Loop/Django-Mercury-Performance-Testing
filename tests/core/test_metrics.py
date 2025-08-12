"""
Unit tests for metrics module
"""

import unittest
from dataclasses import FrozenInstanceError

from django_mercury.python_bindings.metrics import (
    PerformanceStatus,
    PerformanceMetrics,
    ComparisonReport
)


class TestPerformanceStatus(unittest.TestCase):
    """Test cases for the PerformanceStatus enum."""

    def test_performance_status_values(self) -> None:
        """Test that PerformanceStatus enum has all required values."""
        expected_statuses = ['excellent', 'good', 'acceptable', 'slow', 'critical']
        
        for status_name in ['EXCELLENT', 'GOOD', 'ACCEPTABLE', 'SLOW', 'CRITICAL']:
            status = getattr(PerformanceStatus, status_name)
            self.assertIn(status.value, expected_statuses)

    def test_performance_status_enum_consistency(self) -> None:
        """Test PerformanceStatus enum consistency."""
        self.assertEqual(PerformanceStatus.EXCELLENT.value, 'excellent')
        self.assertEqual(PerformanceStatus.GOOD.value, 'good')
        self.assertEqual(PerformanceStatus.ACCEPTABLE.value, 'acceptable')
        self.assertEqual(PerformanceStatus.SLOW.value, 'slow')
        self.assertEqual(PerformanceStatus.CRITICAL.value, 'critical')


class TestPerformanceMetrics(unittest.TestCase):
    """Test cases for the PerformanceMetrics class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.fast_metrics = PerformanceMetrics(
            response_time=45.0,
            memory_usage=30.0,
            query_count=2,
            operation_name="fast_operation"
        )
        
        self.slow_metrics = PerformanceMetrics(
            response_time=750.0,
            memory_usage=250.0,  # Above 200MB threshold for critical
            query_count=25,
            operation_name="slow_operation"
        )
        
        self.medium_metrics = PerformanceMetrics(
            response_time=120.0,
            memory_usage=75.0,
            query_count=5,
            operation_name="medium_operation"
        )

    def test_performance_metrics_creation(self) -> None:
        """Test creating PerformanceMetrics instances."""
        metrics = PerformanceMetrics(
            response_time=100.0,
            memory_usage=50.0,
            query_count=3,
            operation_name="test_operation"
        )
        
        self.assertEqual(metrics.response_time, 100.0)
        self.assertEqual(metrics.memory_usage, 50.0)
        self.assertEqual(metrics.query_count, 3)
        self.assertEqual(metrics.operation_name, "test_operation")

    def test_performance_metrics_defaults(self) -> None:
        """Test default values for PerformanceMetrics."""
        metrics = PerformanceMetrics(response_time=50.0, memory_usage=25.0)
        
        self.assertEqual(metrics.query_count, 0)
        self.assertEqual(metrics.operation_name, "")

    def test_post_init_thresholds_initialization(self) -> None:
        """Test that post_init initializes thresholds correctly."""
        metrics = PerformanceMetrics(response_time=50.0, memory_usage=25.0)
        
        self.assertIsNotNone(metrics._response_time_thresholds)
        self.assertIsNotNone(metrics._memory_thresholds)
        
        # Check some expected threshold values
        self.assertIn('excellent', metrics._response_time_thresholds)
        self.assertIn('good', metrics._response_time_thresholds)
        self.assertIn('excellent', metrics._memory_thresholds)
        self.assertIn('good', metrics._memory_thresholds)

    def test_str_representation(self) -> None:
        """Test string representation of PerformanceMetrics."""
        str_repr = str(self.fast_metrics)
        
        self.assertIn("fast_operation", str_repr)
        self.assertIn("45.00ms", str_repr)
        self.assertIn("30.00MB", str_repr)
        # Should contain status icon
        self.assertTrue(any(char in str_repr for char in "🚀✅⚠️🐌🚨"))

    def test_repr_representation(self) -> None:
        """Test repr representation of PerformanceMetrics."""
        repr_str = repr(self.fast_metrics)
        
        self.assertIn("PerformanceMetrics", repr_str)
        self.assertIn("response_time=45.00", repr_str)
        self.assertIn("memory_usage=30.00", repr_str)
        self.assertIn("operation_name='fast_operation'", repr_str)

    def test_is_fast_property(self) -> None:
        """Test is_fast property."""
        self.assertTrue(self.fast_metrics.is_fast)
        self.assertFalse(self.slow_metrics.is_fast)
        self.assertFalse(self.medium_metrics.is_fast)

    def test_is_slow_property(self) -> None:
        """Test is_slow property."""
        self.assertFalse(self.fast_metrics.is_slow)
        self.assertTrue(self.slow_metrics.is_slow)
        self.assertFalse(self.medium_metrics.is_slow)

    def test_is_memory_intensive_property(self) -> None:
        """Test is_memory_intensive property."""
        self.assertFalse(self.fast_metrics.is_memory_intensive)
        self.assertTrue(self.slow_metrics.is_memory_intensive)
        self.assertFalse(self.medium_metrics.is_memory_intensive)

    def test_has_query_issues_property(self) -> None:
        """Test has_query_issues property."""
        self.assertFalse(self.fast_metrics.has_query_issues)
        self.assertTrue(self.slow_metrics.has_query_issues)
        self.assertFalse(self.medium_metrics.has_query_issues)

    def test_performance_status_property(self) -> None:
        """Test performance_status property assessment."""
        self.assertEqual(self.fast_metrics.performance_status, PerformanceStatus.EXCELLENT)
        self.assertEqual(self.slow_metrics.performance_status, PerformanceStatus.CRITICAL)
        self.assertEqual(self.medium_metrics.performance_status, PerformanceStatus.ACCEPTABLE)

    def test_memory_status_property(self) -> None:
        """Test memory_status property assessment."""
        self.assertEqual(self.fast_metrics.memory_status, PerformanceStatus.GOOD)
        self.assertEqual(self.slow_metrics.memory_status, PerformanceStatus.CRITICAL)
        self.assertEqual(self.medium_metrics.memory_status, PerformanceStatus.ACCEPTABLE)

    def test_performance_status_thresholds(self) -> None:
        """Test performance status threshold boundaries."""
        test_cases = [
            (25.0, PerformanceStatus.EXCELLENT),   # <= 50ms
            (75.0, PerformanceStatus.GOOD),        # <= 100ms
            (200.0, PerformanceStatus.ACCEPTABLE), # <= 300ms
            (400.0, PerformanceStatus.SLOW),       # <= 500ms
            (600.0, PerformanceStatus.CRITICAL)    # > 500ms
        ]
        
        for response_time, expected_status in test_cases:
            with self.subTest(response_time=response_time):
                metrics = PerformanceMetrics(
                    response_time=response_time,
                    memory_usage=50.0,
                    operation_name="threshold_test"
                )
                self.assertEqual(metrics.performance_status, expected_status)

    def test_memory_status_thresholds(self) -> None:
        """Test memory status threshold boundaries."""
        test_cases = [
            (10.0, PerformanceStatus.EXCELLENT),   # <= 20MB
            (35.0, PerformanceStatus.GOOD),        # <= 50MB
            (75.0, PerformanceStatus.ACCEPTABLE),  # <= 100MB
            (150.0, PerformanceStatus.SLOW),       # <= 200MB
            (250.0, PerformanceStatus.CRITICAL)    # > 200MB
        ]
        
        for memory_usage, expected_status in test_cases:
            with self.subTest(memory_usage=memory_usage):
                metrics = PerformanceMetrics(
                    response_time=100.0,
                    memory_usage=memory_usage,
                    operation_name="memory_test"
                )
                self.assertEqual(metrics.memory_status, expected_status)

    def test_get_status_icon_method(self) -> None:
        """Test _get_status_icon method returns appropriate icons."""
        test_cases = [
            (self.fast_metrics, "🚀"),    # Excellent
            (self.slow_metrics, "🚨"),    # Critical
            (self.medium_metrics, "⚠️")   # Acceptable
        ]
        
        for metrics, expected_icon in test_cases:
            with self.subTest(metrics=metrics.operation_name):
                icon = metrics._get_status_icon()
                self.assertEqual(icon, expected_icon)

    def test_detailed_report_method(self) -> None:
        """Test detailed_report method."""
        report = self.fast_metrics.detailed_report()
        
        self.assertIn("📊 Performance Report", report)
        self.assertIn("fast_operation", report)
        self.assertIn("45.00ms", report)
        self.assertIn("30.00MB", report)
        self.assertIn("2", report)  # query count
        self.assertIn("excellent", report)

    def test_detailed_report_with_recommendations(self) -> None:
        """Test detailed_report includes recommendations for poor performance."""
        report = self.slow_metrics.detailed_report()
        
        self.assertIn("Recommendations", report)
        self.assertIn("Optimize database queries", report)
        self.assertIn("Review memory usage", report)
        self.assertIn("N+1 query patterns", report)

    def test_detailed_report_no_recommendations(self) -> None:
        """Test detailed_report without recommendations for good performance."""
        report = self.fast_metrics.detailed_report()
        
        # Should not include recommendations section for good performance
        self.assertNotIn("Recommendations", report)

    def test_get_recommendations_method(self) -> None:
        """Test _get_recommendations method."""
        fast_recommendations = self.fast_metrics._get_recommendations()
        slow_recommendations = self.slow_metrics._get_recommendations()
        
        # Fast metrics should have no recommendations
        self.assertEqual(len(fast_recommendations), 0)
        
        # Slow metrics should have recommendations
        self.assertGreater(len(slow_recommendations), 0)
        self.assertTrue(any("database queries" in rec for rec in slow_recommendations))
        self.assertTrue(any("memory usage" in rec for rec in slow_recommendations))
        self.assertTrue(any("N+1 query" in rec for rec in slow_recommendations))

    def test_meets_thresholds_method(self) -> None:
        """Test meets_thresholds method."""
        # Fast metrics should meet reasonable thresholds
        self.assertTrue(self.fast_metrics.meets_thresholds(
            max_response_time=100.0,
            max_memory_mb=50.0,
            max_queries=5
        ))
        
        # Slow metrics should not meet strict thresholds
        self.assertFalse(self.slow_metrics.meets_thresholds(
            max_response_time=100.0,
            max_memory_mb=50.0,
            max_queries=5
        ))

    def test_meets_thresholds_partial_checks(self) -> None:
        """Test meets_thresholds with partial threshold checks."""
        # Only check response time
        self.assertTrue(self.fast_metrics.meets_thresholds(max_response_time=100.0))
        self.assertFalse(self.slow_metrics.meets_thresholds(max_response_time=100.0))
        
        # Only check memory
        self.assertTrue(self.fast_metrics.meets_thresholds(max_memory_mb=50.0))
        self.assertFalse(self.slow_metrics.meets_thresholds(max_memory_mb=50.0))
        
        # Only check queries
        self.assertTrue(self.fast_metrics.meets_thresholds(max_queries=5))
        self.assertFalse(self.slow_metrics.meets_thresholds(max_queries=5))

    def test_meets_thresholds_none_values(self) -> None:
        """Test meets_thresholds handles None values correctly."""
        # Should return True when all thresholds are None
        self.assertTrue(self.slow_metrics.meets_thresholds())
        self.assertTrue(self.fast_metrics.meets_thresholds())

    def test_to_dict_method(self) -> None:
        """Test to_dict serialization method."""
        metrics_dict = self.fast_metrics.to_dict()
        
        expected_keys = [
            'response_time', 'memory_usage', 'query_count', 'operation_name',
            'performance_status', 'memory_status', 'is_fast', 'is_slow',
            'is_memory_intensive', 'has_query_issues'
        ]
        
        for key in expected_keys:
            self.assertIn(key, metrics_dict)
        
        # Check values
        self.assertEqual(metrics_dict['response_time'], 45.0)
        self.assertEqual(metrics_dict['memory_usage'], 30.0)
        self.assertEqual(metrics_dict['query_count'], 2)
        self.assertEqual(metrics_dict['operation_name'], "fast_operation")
        self.assertEqual(metrics_dict['performance_status'], 'excellent')
        self.assertEqual(metrics_dict['memory_status'], 'good')
        self.assertTrue(metrics_dict['is_fast'])
        self.assertFalse(metrics_dict['is_slow'])


class TestComparisonReport(unittest.TestCase):
    """Test cases for the ComparisonReport class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.baseline = PerformanceMetrics(
            response_time=100.0,
            memory_usage=50.0,
            query_count=3,
            operation_name="baseline_operation"
        )
        
        self.improved = PerformanceMetrics(
            response_time=80.0,   # 20% improvement
            memory_usage=40.0,    # 20% improvement
            query_count=2,
            operation_name="improved_operation"
        )
        
        self.regressed = PerformanceMetrics(
            response_time=130.0,  # 30% regression
            memory_usage=65.0,    # 30% regression
            query_count=5,
            operation_name="regressed_operation"
        )
        
        self.minor_change = PerformanceMetrics(
            response_time=105.0,  # 5% regression
            memory_usage=52.0,    # 4% regression
            query_count=3,
            operation_name="minor_change_operation"
        )

    def test_comparison_report_creation(self) -> None:
        """Test creating ComparisonReport instances."""
        report = ComparisonReport(baseline=self.baseline, current=self.improved)
        
        self.assertEqual(report.baseline, self.baseline)
        self.assertEqual(report.current, self.improved)

    def test_response_time_change_calculation(self) -> None:
        """Test response time change percentage calculation."""
        improved_report = ComparisonReport(baseline=self.baseline, current=self.improved)
        regressed_report = ComparisonReport(baseline=self.baseline, current=self.regressed)
        
        self.assertAlmostEqual(improved_report.response_time_change, -20.0, places=1)
        self.assertAlmostEqual(regressed_report.response_time_change, 30.0, places=1)

    def test_memory_change_calculation(self) -> None:
        """Test memory usage change percentage calculation."""
        improved_report = ComparisonReport(baseline=self.baseline, current=self.improved)
        regressed_report = ComparisonReport(baseline=self.baseline, current=self.regressed)
        
        self.assertAlmostEqual(improved_report.memory_change, -20.0, places=1)
        self.assertAlmostEqual(regressed_report.memory_change, 30.0, places=1)

    def test_response_time_change_zero_baseline(self) -> None:
        """Test response time change with zero baseline."""
        zero_baseline = PerformanceMetrics(
            response_time=0.0,
            memory_usage=50.0,
            operation_name="zero_baseline"
        )
        report = ComparisonReport(baseline=zero_baseline, current=self.improved)
        
        self.assertEqual(report.response_time_change, 0.0)

    def test_memory_change_zero_baseline(self) -> None:
        """Test memory change with zero baseline."""
        zero_baseline = PerformanceMetrics(
            response_time=100.0,
            memory_usage=0.0,
            operation_name="zero_baseline"
        )
        report = ComparisonReport(baseline=zero_baseline, current=self.improved)
        
        self.assertEqual(report.memory_change, 0.0)

    def test_is_regression_property(self) -> None:
        """Test is_regression property detection."""
        improved_report = ComparisonReport(baseline=self.baseline, current=self.improved)
        regressed_report = ComparisonReport(baseline=self.baseline, current=self.regressed)
        minor_report = ComparisonReport(baseline=self.baseline, current=self.minor_change)
        
        self.assertFalse(improved_report.is_regression)
        self.assertTrue(regressed_report.is_regression)  # 30% > 20% threshold
        self.assertFalse(minor_report.is_regression)     # 5% < 20% threshold

    def test_is_improvement_property(self) -> None:
        """Test is_improvement property detection."""
        improved_report = ComparisonReport(baseline=self.baseline, current=self.improved)
        regressed_report = ComparisonReport(baseline=self.baseline, current=self.regressed)
        minor_report = ComparisonReport(baseline=self.baseline, current=self.minor_change)
        
        self.assertTrue(improved_report.is_improvement)  # -20% < -10% threshold
        self.assertFalse(regressed_report.is_improvement)
        self.assertFalse(minor_report.is_improvement)    # 5% > -10% threshold

    def test_str_representation(self) -> None:
        """Test string representation of ComparisonReport."""
        improved_report = ComparisonReport(baseline=self.baseline, current=self.improved)
        regressed_report = ComparisonReport(baseline=self.baseline, current=self.regressed)
        
        improved_str = str(improved_report)
        regressed_str = str(regressed_report)
        
        # Check structure
        self.assertIn("🔄 Performance Comparison", improved_str)
        self.assertIn("improved_operation", improved_str)
        self.assertIn("-20.0%", improved_str)  # Improvement
        self.assertIn("📉", improved_str)       # Down arrow for improvement
        
        self.assertIn("🔄 Performance Comparison", regressed_str)
        self.assertIn("regressed_operation", regressed_str)
        self.assertIn("+30.0%", regressed_str)  # Regression
        self.assertIn("📈", regressed_str)       # Up arrow for regression

    def test_regression_and_improvement_edge_cases(self) -> None:
        """Test edge cases for regression and improvement detection."""
        # Exactly 20% regression (should be True)
        exactly_20_regressed = PerformanceMetrics(
            response_time=120.0,  # Exactly 20% increase
            memory_usage=50.0,
            operation_name="exactly_20_regressed"
        )
        report_20 = ComparisonReport(baseline=self.baseline, current=exactly_20_regressed)
        self.assertFalse(report_20.is_regression)  # > 20%, not >= 20%
        
        # Exactly 10% improvement (should be True)
        exactly_10_improved = PerformanceMetrics(
            response_time=90.0,   # Exactly 10% decrease
            memory_usage=50.0,
            operation_name="exactly_10_improved"
        )
        report_10 = ComparisonReport(baseline=self.baseline, current=exactly_10_improved)
        self.assertFalse(report_10.is_improvement)  # < -10%, not <= -10%


class TestMetricsEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for metrics."""

    def test_zero_values(self) -> None:
        """Test metrics with zero values."""
        zero_metrics = PerformanceMetrics(
            response_time=0.0,
            memory_usage=0.0,
            query_count=0,
            operation_name="zero_test"
        )
        
        self.assertTrue(zero_metrics.is_fast)  # 0 < 100
        self.assertFalse(zero_metrics.is_slow)  # 0 < 500
        self.assertEqual(zero_metrics.performance_status, PerformanceStatus.EXCELLENT)
        self.assertEqual(zero_metrics.memory_status, PerformanceStatus.EXCELLENT)

    def test_very_large_values(self) -> None:
        """Test metrics with very large values."""
        large_metrics = PerformanceMetrics(
            response_time=10000.0,
            memory_usage=1000.0,
            query_count=100,
            operation_name="large_test"
        )
        
        self.assertFalse(large_metrics.is_fast)
        self.assertTrue(large_metrics.is_slow)
        self.assertTrue(large_metrics.is_memory_intensive)
        self.assertTrue(large_metrics.has_query_issues)
        self.assertEqual(large_metrics.performance_status, PerformanceStatus.CRITICAL)
        self.assertEqual(large_metrics.memory_status, PerformanceStatus.CRITICAL)

    def test_boundary_values(self) -> None:
        """Test metrics at exact threshold boundaries."""
        # Test exact threshold boundaries
        boundary_cases = [
            (50.0, PerformanceStatus.EXCELLENT),  # Exactly at excellent threshold
            (100.0, PerformanceStatus.GOOD),      # Exactly at good threshold
            (300.0, PerformanceStatus.ACCEPTABLE), # Exactly at acceptable threshold
            (500.0, PerformanceStatus.SLOW),      # Exactly at slow threshold
        ]
        
        for response_time, expected_status in boundary_cases:
            with self.subTest(response_time=response_time):
                metrics = PerformanceMetrics(
                    response_time=response_time,
                    memory_usage=50.0,
                    operation_name=f"boundary_test_{response_time}"
                )
                self.assertEqual(metrics.performance_status, expected_status)


if __name__ == '__main__':
    unittest.main()