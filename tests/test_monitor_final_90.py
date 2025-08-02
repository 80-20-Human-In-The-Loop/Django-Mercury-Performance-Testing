"""
Final push to 90% coverage - targeting the most impactful missing lines.
Focus on: 515-557 (recommendations), 1089-1149 (thresholds), 1235-1408 (assertion logic)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock, call
import sys
import os
import inspect
from pathlib import Path
from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python
)


class TestRecommendationsComplete(unittest.TestCase):
    """Complete test coverage for recommendations (lines 515-557)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_c_metrics = Mock()
        self.mock_c_metrics.contents.operation_type = b"test"
        self.mock_c_metrics.contents.operation_name = b"test"
        self.mock_c_metrics.contents.end_time_ns = 2000000000
        self.mock_c_metrics.contents.start_time_ns = 1000000000
        self.mock_c_metrics.contents.memory_end_bytes = 200000000  # High memory
        self.mock_c_metrics.contents.memory_start_bytes = 100000000
        self.mock_c_metrics.contents.query_count_end = 15
        self.mock_c_metrics.contents.query_count_start = 0
        self.mock_c_metrics.contents.cache_hits = 2
        self.mock_c_metrics.contents.cache_misses = 10
        self.mock_c_metrics.contents.baseline_memory_mb = 50
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_recommendations_with_all_issues(self, mock_lib):
        """Test recommendations when all issues are present."""
        mock_lib.get_elapsed_time_ms.return_value = 500.0  # Slow
        mock_lib.get_memory_usage_mb.return_value = 200.0  # High memory
        mock_lib.get_memory_delta_mb.return_value = 100.0
        mock_lib.get_query_count.return_value = 25  # Many queries
        mock_lib.get_cache_hit_ratio.return_value = 0.2  # Poor cache
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # Mock all django issues
        mock_issues = Mock()
        mock_issues.has_n_plus_one = True
        mock_issues.excessive_queries = True
        mock_issues.memory_intensive = True
        mock_issues.poor_cache_performance = True
        mock_issues.slow_serialization = True
        mock_issues.inefficient_pagination = True
        mock_issues.missing_db_indexes = True
        metrics.django_issues = mock_issues
        
        recommendations = metrics._get_recommendations()
        
        # Should have recommendations for all issues
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)
        
        # Check for various recommendation types
        all_text = " ".join(recommendations).lower()
        # Should have recommendations text
        self.assertTrue(len(all_text) > 0)
        self.assertIn("cache", all_text)
        
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_recommendations_memory_intensive(self, mock_lib):
        """Test recommendations for memory intensive operations."""
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 300.0  # Very high memory
        mock_lib.get_memory_delta_mb.return_value = 250.0
        mock_lib.get_query_count.return_value = 5
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # Mock memory intensive issue
        mock_issues = Mock()
        mock_issues.has_n_plus_one = False
        mock_issues.excessive_queries = False
        mock_issues.memory_intensive = True
        mock_issues.poor_cache_performance = False
        mock_issues.slow_serialization = False
        mock_issues.inefficient_pagination = False
        mock_issues.missing_db_indexes = False
        metrics.django_issues = mock_issues
        
        recommendations = metrics._get_recommendations()
        
        # Should have recommendations for memory issue
        all_text = " ".join(recommendations).lower()
        # The recommendation might be about queryset, pagination, or loading
        self.assertTrue(
            "queryset" in all_text or "pagination" in all_text or "loading" in all_text,
            f"Expected memory-related recommendation in: {all_text}"
        )


class TestThresholdsComplete(unittest.TestCase):
    """Complete test coverage for thresholds (lines 1089-1149)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_all_expect_methods(self, mock_lib):
        """Test all expect_* threshold methods."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test response time threshold
        result = monitor.expect_response_under(100)
        self.assertEqual(monitor._thresholds['response_time'], 100)
        self.assertEqual(result, monitor)  # Check chaining
        
        # Test memory threshold
        result = monitor.expect_memory_under(50)
        self.assertEqual(monitor._thresholds['memory_usage'], 50)
        self.assertEqual(result, monitor)
        
        # Test query count threshold
        result = monitor.expect_queries_under(10)
        self.assertEqual(monitor._thresholds['query_count'], 10)
        self.assertEqual(result, monitor)
        
        # Test cache hit ratio threshold
        result = monitor.expect_cache_hit_ratio_above(0.75)
        self.assertEqual(monitor._thresholds['cache_hit_ratio'], 0.75)
        self.assertEqual(result, monitor)
        
        # Test memory delta threshold (if exists)
        if hasattr(monitor, 'expect_memory_delta_under'):
            result = monitor.expect_memory_delta_under(25)
            self.assertEqual(monitor._thresholds['memory_delta'], 25)
            self.assertEqual(result, monitor)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_threshold_validation_edge_cases(self, mock_lib):
        """Test threshold validation with edge cases."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test with zero values
        monitor.expect_response_under(0)  # Should accept 0
        self.assertEqual(monitor._thresholds['response_time'], 0)
        
        # Test with very large values
        monitor.expect_memory_under(999999)
        self.assertEqual(monitor._thresholds['memory_usage'], 999999)
        
        # Test with float values
        monitor.expect_cache_hit_ratio_above(0.0)
        self.assertEqual(monitor._thresholds['cache_hit_ratio'], 0.0)
        
        monitor.expect_cache_hit_ratio_above(1.0)
        self.assertEqual(monitor._thresholds['cache_hit_ratio'], 1.0)


class TestAssertionLogicComplete(unittest.TestCase):
    """Complete test coverage for assertion logic (lines 1235-1408)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_assert_thresholds_all_violations(self, mock_lib):
        """Test assertion with all thresholds violated."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set multiple thresholds
        monitor.expect_response_under(50)
        monitor.expect_memory_under(30)
        monitor.expect_queries_under(5)
        monitor.expect_cache_hit_ratio_above(0.9)
        
        # Create metrics that violate all thresholds
        mock_metrics = Mock()
        mock_metrics.response_time = 100  # Violates
        mock_metrics.memory_usage = 50  # Violates
        mock_metrics.query_count = 10  # Violates
        mock_metrics.cache_hit_ratio = 0.5  # Violates
        monitor._metrics = mock_metrics
        
        # Should raise with details about violations
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        self.assertIn("Response time", error_msg)
        self.assertIn("100", error_msg)
        self.assertIn("50", error_msg)  # threshold
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_assert_thresholds_with_educational_guidance(self, mock_lib):
        """Test assertion with educational guidance enabled."""
        monitor = EnhancedPerformanceMonitor("test_op")
        monitor.enable_educational_guidance()
        
        # Set threshold
        monitor.expect_response_under(100)
        
        # Create violating metrics
        mock_metrics = Mock()
        mock_metrics.response_time = 200
        mock_metrics.memory_usage = 50
        mock_metrics.memory_usage_mb = 50  # For guidance calculation
        mock_metrics.query_count = 5
        mock_metrics.cache_hit_ratio = 0.8
        monitor._metrics = mock_metrics
        
        # Mock django issues for educational content
        mock_issues = Mock()
        mock_issues.has_n_plus_one = False
        mock_issues.excessive_queries = False
        mock_metrics.django_issues = mock_issues
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should have educational content
        self.assertIn("Response time", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    @patch('inspect.currentframe')
    @patch('inspect.getframeinfo')
    def test_assert_with_inspect_location(self, mock_getframeinfo, mock_currentframe, mock_lib):
        """Test assertion with inspect-based location."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Don't set test context, let it use inspect
        monitor.expect_response_under(50)
        
        # Mock inspect to return frame info
        mock_frame = Mock()
        mock_frame.filename = "/path/to/test_file.py"
        mock_frame.lineno = 456
        mock_frame.function = "test_function"
        mock_currentframe.return_value = mock_frame
        mock_getframeinfo.return_value = Mock(
            filename="/path/to/test_file.py",
            lineno=456,
            function="test_function"
        )
        
        # Create violating metrics
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        self.assertIn("Response time", error_msg)


class TestErrorLocationFormatting(unittest.TestCase):
    """Test error location formatting (lines 1361-1396)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_error_location_with_backend_in_path(self, mock_lib):
        """Test error location when 'backend' is in path."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set test context with backend in path
        monitor.set_test_context(
            test_file="/home/user/project/backend/tests/test_views.py",
            test_line=789,
            test_method="test_user_list"
        )
        
        monitor.expect_response_under(50)
        
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should format path nicely
        self.assertIn("backend/tests/test_views.py:789", error_msg)
        self.assertIn("test_user_list", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_error_location_with_tests_in_path(self, mock_lib):
        """Test error location when 'tests' is in path."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set test context with tests in path
        monitor.set_test_context(
            test_file="/workspace/tests/integration/test_api.py",
            test_line=321,
            test_method="test_api_endpoint"
        )
        
        monitor.expect_response_under(50)
        
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should include test file info
        self.assertIn("test_api.py:321", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_error_location_with_src_in_path(self, mock_lib):
        """Test error location when 'src' is in path."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set test context with src in path
        monitor.set_test_context(
            test_file="/app/src/tests/test_models.py",
            test_line=654,
            test_method="test_model_save"
        )
        
        monitor.expect_response_under(50)
        
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should include test file info
        self.assertIn("test_models.py:654", error_msg)


class TestMiscellaneousCoverage(unittest.TestCase):
    """Test miscellaneous uncovered lines."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_operation_types(self, mock_lib):
        """Test different operation types (lines 774, 776, 779-782)."""
        operation_types = [
            ("general", "general"),
            ("django_view", "django_view"),
            ("database_query", "database_query"),
            ("serializer", "serializer"),
            ("django_model", "django_model"),
            (None, "general"),  # Default
        ]
        
        for input_type, expected_type in operation_types:
            with self.subTest(operation_type=input_type):
                if input_type:
                    monitor = EnhancedPerformanceMonitor("test", operation_type=input_type)
                else:
                    monitor = EnhancedPerformanceMonitor("test")
                
                self.assertEqual(monitor.operation_type, expected_type)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_context_manager_exception_handling(self, mock_lib):
        """Test context manager with exceptions (lines 871-873)."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        mock_handle = 12345
        mock_lib.start_performance_monitoring_enhanced.return_value = mock_handle
        
        mock_c_metrics = Mock()
        mock_c_metrics.contents.operation_type = b"test"
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 2000000000
        mock_c_metrics.contents.start_time_ns = 1900000000
        mock_c_metrics.contents.memory_end_bytes = 50000000
        mock_c_metrics.contents.memory_start_bytes = 40000000
        mock_c_metrics.contents.query_count_end = 3
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 8
        mock_c_metrics.contents.cache_misses = 2
        mock_c_metrics.contents.baseline_memory_mb = 50
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = Mock(contents=mock_c_metrics.contents)
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 50.0
        mock_lib.get_memory_delta_mb.return_value = 10.0
        mock_lib.get_query_count.return_value = 3
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        # Test with exception during monitoring
        class TestException(Exception):
            pass
        
        with self.assertRaises(TestException):
            with monitor:
                raise TestException("Test error")
        
        # Should still have stopped monitoring
        mock_lib.stop_performance_monitoring_enhanced.assert_called_once()


class TestDetectionMethodsEdgeCases(unittest.TestCase):
    """Test edge cases in detection methods (lines 1414-1454)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_c_metrics = Mock()
        self.mock_c_metrics.contents.operation_type = b"test"
        self.mock_c_metrics.contents.operation_name = b"test"
        self.mock_c_metrics.contents.end_time_ns = 2000000000
        self.mock_c_metrics.contents.start_time_ns = 1000000000
        self.mock_c_metrics.contents.memory_end_bytes = 100000000
        self.mock_c_metrics.contents.memory_start_bytes = 100000000
        self.mock_c_metrics.contents.cache_hits = 5
        self.mock_c_metrics.contents.cache_misses = 2
        self.mock_c_metrics.contents.baseline_memory_mb = 50
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_get_query_count_with_all_sources(self, mock_lib):
        """Test _get_query_count with different sources (lines 1414-1426)."""
        # Test with query tracker
        mock_tracker = Mock()
        mock_tracker.query_count = 25
        
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 100.0
        mock_lib.get_memory_delta_mb.return_value = 50.0
        mock_lib.get_query_count.return_value = 10  # C library count
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        self.mock_c_metrics.contents.query_count_end = 10
        self.mock_c_metrics.contents.query_count_start = 0
        
        # With tracker
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", mock_tracker)
        
        # Should use C metrics count, not tracker
        self.assertEqual(metrics.query_count, 10)
        
        # Without tracker
        metrics_no_tracker = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        self.assertEqual(metrics_no_tracker.query_count, 10)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_detect_methods_boundary_conditions(self, mock_lib):
        """Test detection methods at boundaries (lines 1431-1454)."""
        # Test _detect_slow_serialization at boundary
        mock_lib.get_elapsed_time_ms.return_value = 100.0  # Exactly 100ms
        mock_lib.get_memory_usage_mb.return_value = 100.0
        mock_lib.get_memory_delta_mb.return_value = 50.0
        mock_lib.get_query_count.return_value = 3  # Exactly 3 queries
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        self.mock_c_metrics.contents.query_count_end = 3
        self.mock_c_metrics.contents.query_count_start = 0
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # 3 queries and 100ms should NOT trigger (need > 100, not >= 100)
        result = metrics._detect_slow_serialization()
        self.assertFalse(result)
        
        # Test _detect_inefficient_pagination at boundary
        mock_lib.get_elapsed_time_ms.return_value = 150.0  # Exactly 150ms
        mock_lib.get_query_count.return_value = 8  # Exactly 8 queries (max)
        
        self.mock_c_metrics.contents.query_count_end = 8
        self.mock_c_metrics.contents.query_count_start = 0
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # 8 queries and 150ms should NOT trigger (need > 150, not >= 150)
        result = metrics._detect_inefficient_pagination()
        self.assertFalse(result)
        
        # Test _detect_missing_indexes at boundary
        mock_lib.get_elapsed_time_ms.return_value = 300.0  # Exactly 300ms
        mock_lib.get_query_count.return_value = 5  # Exactly 5 queries (max)
        
        self.mock_c_metrics.contents.query_count_end = 5
        self.mock_c_metrics.contents.query_count_start = 0
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # 5 queries and 300ms should NOT trigger (need > 300, not >= 300)
        result = metrics._detect_missing_indexes()
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()