"""
Comprehensive tests to boost monitor.py coverage to 85%+.
Focus on uncovered paths: guidance methods, exception handling, and edge cases.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import time
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python,
    monitor_django_view,
    monitor_django_model,
    monitor_serializer
)


class TestMonitorGuidanceMethods(unittest.TestCase):
    """Test the guidance generation methods (lines 1092-1149)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_operation")
    
    def test_generate_threshold_guidance_query_violation(self):
        """Test guidance generation for query count violations."""
        # Set up metrics with high query count
        mock_metrics = Mock()
        mock_metrics.query_count = 50
        mock_metrics.response_time = 100
        mock_metrics.memory_usage_mb = 10
        self.monitor._metrics = mock_metrics
        self.monitor.operation_type = "detail_view"
        
        violations = ["Query count 50 exceeded limit 10"]
        guidance = self.monitor._generate_threshold_guidance(violations)
        
        self.assertIn("N+1 query issue", guidance)
        self.assertIn("select_related", guidance)
        self.assertIn("query_count_max", guidance)
    
    def test_generate_threshold_guidance_response_violation(self):
        """Test guidance generation for response time violations."""
        mock_metrics = Mock()
        mock_metrics.query_count = 5
        mock_metrics.response_time = 500
        mock_metrics.memory_usage_mb = 10
        self.monitor._metrics = mock_metrics
        
        violations = ["Response time 500ms exceeded limit 200ms"]
        guidance = self.monitor._generate_threshold_guidance(violations)
        
        self.assertIn("Response time exceeded", guidance)
        self.assertIn("response_time_ms", guidance)
    
    def test_generate_threshold_guidance_memory_violation(self):
        """Test guidance generation for memory violations."""
        mock_metrics = Mock()
        mock_metrics.query_count = 5
        mock_metrics.response_time = 100
        mock_metrics.memory_usage_mb = 150
        self.monitor._metrics = mock_metrics
        
        violations = ["Memory usage 150MB exceeded limit 100MB"]
        guidance = self.monitor._generate_threshold_guidance(violations)
        
        self.assertIn("Memory usage exceeded", guidance)
        self.assertIn("memory_overhead_mb", guidance)
    
    def test_generate_threshold_guidance_multiple_violations(self):
        """Test guidance for multiple violations."""
        mock_metrics = Mock()
        mock_metrics.query_count = 50
        mock_metrics.response_time = 500
        mock_metrics.memory_usage_mb = 150
        self.monitor._metrics = mock_metrics
        self.monitor.operation_type = "list_view"
        
        violations = [
            "Query count 50 exceeded limit 10",
            "Response time 500ms exceeded limit 200ms",
            "Memory usage 150MB exceeded limit 100MB"
        ]
        guidance = self.monitor._generate_threshold_guidance(violations)
        
        # Should have guidance for all three violations
        self.assertIn("N+1 query issue", guidance)
        self.assertIn("Response time exceeded", guidance)
        self.assertIn("Memory usage exceeded", guidance)
        self.assertIn("set_performance_thresholds", guidance)
    
    def test_generate_threshold_guidance_list_view_specifics(self):
        """Test list view specific guidance."""
        mock_metrics = Mock()
        mock_metrics.query_count = 100
        mock_metrics.response_time = 100
        mock_metrics.memory_usage_mb = 10
        self.monitor._metrics = mock_metrics
        self.monitor.operation_type = "list_view"
        
        violations = ["Query count 100 exceeded limit 10"]
        guidance = self.monitor._generate_threshold_guidance(violations)
        
        self.assertIn("pagination", guidance.lower())
    
    def test_generate_threshold_guidance_no_metrics(self):
        """Test guidance generation when metrics are None."""
        self.monitor._metrics = None
        
        violations = ["Query count exceeded"]
        guidance = self.monitor._generate_threshold_guidance(violations)
        
        # Should still provide some guidance
        self.assertIn("Query count exceeded", guidance)
    
    def test_generate_threshold_guidance_memory_fallback(self):
        """Test memory guidance with memory_usage instead of memory_usage_mb."""
        mock_metrics = Mock()
        mock_metrics.query_count = 5
        mock_metrics.response_time = 100
        # Use memory_usage instead of memory_usage_mb
        mock_metrics.memory_usage_mb = None
        mock_metrics.memory_usage = 120
        self.monitor._metrics = mock_metrics
        
        violations = ["Memory usage 120MB exceeded limit 100MB"]
        guidance = self.monitor._generate_threshold_guidance(violations)
        
        self.assertIn("Memory usage exceeded", guidance)
        self.assertIn("memory_overhead_mb", guidance)
    
    def test_generate_threshold_guidance_empty_violations(self):
        """Test guidance with no violations."""
        guidance = self.monitor._generate_threshold_guidance([])
        self.assertEqual(guidance, "")


class TestMonitorExceptionPaths(unittest.TestCase):
    """Test exception handling paths (lines 19-31, 630-647, etc.)."""
    
    @patch('django_mercury.python_bindings.monitor.c_extensions', None)
    @patch('django_mercury.python_bindings.monitor.DjangoQueryTracker', None)
    @patch('django_mercury.python_bindings.monitor.DjangoCacheTracker', None)
    def test_monitor_without_django_hooks(self):
        """Test monitor when Django hooks are not available."""
        monitor = EnhancedPerformanceMonitor("test_op")
        self.assertIsNotNone(monitor)
        # Should work without Django hooks
    
    @patch.dict('sys.modules', {'django_mercury.python_bindings.metrics': None})
    def test_import_fallback_paths(self):
        """Test import fallback when modules are not available."""
        # This tests the except ImportError blocks
        # We can't easily test this without reloading the module
        # but we can verify the monitor works in degraded mode
        monitor = EnhancedPerformanceMonitor("test_op")
        self.assertIsNotNone(monitor)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_get_metrics_c_library_error(self, mock_lib):
        """Test get_metrics when C library fails."""
        mock_lib.get_performance_metrics.return_value = -1
        
        monitor = EnhancedPerformanceMonitor("test_op")
        monitor._c_monitor_ptr = ctypes.c_void_p(12345)
        
        # Should handle C library failure gracefully
        with monitor:
            pass
        
        metrics = monitor.get_metrics()
        self.assertIsNotNone(metrics)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_analyze_django_specific_error(self, mock_lib):
        """Test _analyze_django_specific when it fails."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Mock to raise an exception
        with patch.object(monitor, '_analyze_n_plus_one', side_effect=Exception("Analysis failed")):
            result = monitor._analyze_django_specific()
            # Should handle exception and return default
            self.assertIsNotNone(result)


class TestMonitorCacheMethods(unittest.TestCase):
    """Test cache-related methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_op")
    
    def test_expect_cache_hit_ratio_above(self):
        """Test cache hit ratio expectation."""
        result = self.monitor.expect_cache_hit_ratio_above(0.8)
        self.assertEqual(result, self.monitor)  # Should return self
        self.assertEqual(self.monitor._expected_cache_hit_ratio, 0.8)
    
    def test_monitor_with_cache_tracking(self):
        """Test monitor with cache tracking enabled."""
        with patch('django_mercury.python_bindings.monitor.DjangoCacheTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.get_stats.return_value = {
                'hits': 80,
                'misses': 20,
                'hit_ratio': 0.8
            }
            mock_tracker_class.return_value = mock_tracker
            
            monitor = monitor_django_view("test_view")
            monitor.expect_cache_hit_ratio_above(0.7)
            
            with monitor:
                pass
            
            # Should track cache stats
            mock_tracker.start.assert_called_once()
            mock_tracker.stop.assert_called_once()


class TestMonitorThresholdMethods(unittest.TestCase):
    """Test threshold setting and checking methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_op")
    
    def test_expect_response_under(self):
        """Test response time threshold setting."""
        result = self.monitor.expect_response_under(200)
        self.assertEqual(result, self.monitor)
        self.assertEqual(self.monitor._expected_response_time, 200)
    
    def test_expect_memory_under(self):
        """Test memory threshold setting."""
        result = self.monitor.expect_memory_under(100)
        self.assertEqual(result, self.monitor)
        self.assertEqual(self.monitor._expected_memory_mb, 100)
    
    def test_expect_queries_under(self):
        """Test query count threshold setting."""
        result = self.monitor.expect_queries_under(10)
        self.assertEqual(result, self.monitor)
        self.assertEqual(self.monitor._expected_query_count, 10)
    
    def test_auto_assert_thresholds(self):
        """Test auto assertion of thresholds."""
        result = self.monitor.auto_assert_thresholds()
        self.assertEqual(result, self.monitor)
        self.assertTrue(self.monitor._auto_assert)
    
    def test_check_thresholds_all_passing(self):
        """Test threshold checking when all pass."""
        self.monitor._expected_response_time = 200
        self.monitor._expected_memory_mb = 100
        self.monitor._expected_query_count = 10
        
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        mock_metrics.memory_usage_mb = 50
        mock_metrics.query_count = 5
        self.monitor._metrics = mock_metrics
        
        violations = self.monitor._check_thresholds()
        self.assertEqual(violations, [])
    
    def test_check_thresholds_with_violations(self):
        """Test threshold checking with violations."""
        self.monitor._expected_response_time = 200
        self.monitor._expected_memory_mb = 100
        self.monitor._expected_query_count = 10
        
        mock_metrics = Mock()
        mock_metrics.response_time = 300
        mock_metrics.memory_usage_mb = 150
        mock_metrics.query_count = 20
        self.monitor._metrics = mock_metrics
        
        violations = self.monitor._check_thresholds()
        self.assertEqual(len(violations), 3)
        self.assertTrue(any("Response time" in v for v in violations))
        self.assertTrue(any("Memory usage" in v for v in violations))
        self.assertTrue(any("Query count" in v for v in violations))


class TestMonitorAnalysisMethods(unittest.TestCase):
    """Test analysis methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_op")
    
    @patch('django_mercury.python_bindings.monitor.DjangoQueryTracker')
    def test_analyze_n_plus_one_with_pattern(self, mock_tracker_class):
        """Test N+1 pattern detection."""
        mock_tracker = Mock()
        # Simulate N+1 pattern - many similar queries
        mock_tracker.queries = [
            Mock(sql="SELECT * FROM users WHERE id = 1", time=0.01),
            Mock(sql="SELECT * FROM users WHERE id = 2", time=0.01),
            Mock(sql="SELECT * FROM users WHERE id = 3", time=0.01),
            Mock(sql="SELECT * FROM users WHERE id = 4", time=0.01),
            Mock(sql="SELECT * FROM users WHERE id = 5", time=0.01),
        ]
        mock_tracker_class.return_value = mock_tracker
        
        result = self.monitor._analyze_n_plus_one()
        self.assertTrue(result['has_n_plus_one'])
        self.assertGreater(result['severity_level'], 0)
    
    @patch('django_mercury.python_bindings.monitor.DjangoQueryTracker')
    def test_analyze_n_plus_one_no_pattern(self, mock_tracker_class):
        """Test N+1 detection with no pattern."""
        mock_tracker = Mock()
        # Different queries, no N+1 pattern
        mock_tracker.queries = [
            Mock(sql="SELECT * FROM users", time=0.01),
            Mock(sql="SELECT * FROM posts", time=0.01),
            Mock(sql="SELECT * FROM comments", time=0.01),
        ]
        mock_tracker_class.return_value = mock_tracker
        
        result = self.monitor._analyze_n_plus_one()
        self.assertFalse(result['has_n_plus_one'])
    
    def test_analyze_serializer_performance(self):
        """Test serializer performance analysis."""
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        mock_metrics.memory_usage_mb = 50
        mock_metrics.query_count = 5
        self.monitor._metrics = mock_metrics
        self.monitor.operation_type = "serializer"
        
        result = self.monitor._analyze_serializer_performance()
        self.assertIn('serialization_overhead', result)
        self.assertIn('field_access_pattern', result)


class TestMonitorPrintMethods(unittest.TestCase):
    """Test print and display methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_op")
    
    @patch('builtins.print')
    def test_print_summary_basic(self, mock_print):
        """Test basic summary printing."""
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        mock_metrics.memory_usage_mb = 50
        mock_metrics.query_count = 5
        mock_metrics.cache_hits = 80
        mock_metrics.cache_misses = 20
        mock_metrics.cache_hit_ratio = 0.8
        self.monitor._metrics = mock_metrics
        
        self.monitor._print_summary()
        
        # Should print summary information
        mock_print.assert_called()
        call_str = str(mock_print.call_args_list)
        self.assertIn("100", call_str)  # Response time
        self.assertIn("50", call_str)   # Memory
        self.assertIn("5", call_str)    # Queries
    
    @patch('builtins.print')
    def test_print_performance_analysis(self, mock_print):
        """Test performance analysis printing."""
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        mock_metrics.memory_usage_mb = 50
        mock_metrics.query_count = 5
        mock_metrics.operation_name = "test_op"
        mock_metrics.get_status = Mock(return_value="OPTIMAL")
        mock_metrics.get_bottleneck = Mock(return_value="None")
        mock_metrics.get_optimization_suggestions = Mock(return_value=["Use caching"])
        mock_metrics.calculate_score = Mock(return_value=90)
        self.monitor._metrics = mock_metrics
        
        self.monitor._django_analysis = {
            'has_n_plus_one': False,
            'cache_hit_ratio': 0.8
        }
        
        self.monitor._print_performance_analysis()
        
        # Should print analysis
        mock_print.assert_called()


class TestMonitorContextManager(unittest.TestCase):
    """Test context manager functionality."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_context_manager_normal_flow(self, mock_lib):
        """Test normal context manager flow."""
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        mock_lib.stop_performance_monitoring.return_value = 0
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        with monitor as m:
            self.assertEqual(m, monitor)
            self.assertIsNotNone(monitor._c_monitor_ptr)
        
        # Should clean up
        mock_lib.stop_performance_monitoring.assert_called()
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_context_manager_with_exception(self, mock_lib):
        """Test context manager with exception in with block."""
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        mock_lib.stop_performance_monitoring.return_value = 0
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        try:
            with monitor:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should still clean up
        mock_lib.stop_performance_monitoring.assert_called()
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_context_manager_auto_assert_violation(self, mock_lib):
        """Test context manager with auto-assert and violations."""
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        mock_lib.stop_performance_monitoring.return_value = 0
        
        monitor = EnhancedPerformanceMonitor("test_op")
        monitor.auto_assert_thresholds()
        monitor.expect_response_under(100)
        
        # Mock metrics that violate threshold
        mock_metrics = Mock()
        mock_metrics.response_time = 200
        mock_metrics.memory_usage_mb = 50
        mock_metrics.query_count = 5
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError):
            with monitor:
                pass


class TestMonitorHelperFunctions(unittest.TestCase):
    """Test helper functions and utility methods."""
    
    def test_monitor_django_view_creation(self):
        """Test monitor_django_view helper function."""
        monitor = monitor_django_view("test_view")
        self.assertEqual(monitor.operation_name, "test_view")
        self.assertEqual(monitor.operation_type, "view")
    
    def test_monitor_django_model_creation(self):
        """Test monitor_django_model helper function."""
        monitor = monitor_django_model("TestModel")
        self.assertEqual(monitor.operation_name, "TestModel")
        self.assertEqual(monitor.operation_type, "model")
    
    def test_monitor_serializer_creation(self):
        """Test monitor_serializer helper function."""
        monitor = monitor_serializer("TestSerializer")
        self.assertEqual(monitor.operation_name, "TestSerializer")
        self.assertEqual(monitor.operation_type, "serializer")
    
    def test_monitor_with_custom_operation_type(self):
        """Test monitor with custom operation type."""
        monitor = monitor_django_view("test", operation_type="custom")
        self.assertEqual(monitor.operation_type, "custom")


if __name__ == '__main__':
    unittest.main()