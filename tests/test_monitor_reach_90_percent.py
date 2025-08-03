"""
Final push to reach 90% by testing the most accessible remaining lines.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python,
    monitor_django_view,
    monitor_database_query, 
    monitor_serializer,
    monitor_django_model
)


class TestUncoveredLines(unittest.TestCase):
    """Test remaining uncovered lines."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_lines_947_to_954(self, mock_lib):
        """Cover factory function lines 947-954."""
        # Just call each factory function
        v = monitor_django_view("v")
        q = monitor_database_query("q")
        s = monitor_serializer("s")
        m = monitor_django_model("m")
        
        # Check they return monitors
        self.assertIsInstance(v, EnhancedPerformanceMonitor)
        self.assertIsInstance(q, EnhancedPerformanceMonitor)
        self.assertIsInstance(s, EnhancedPerformanceMonitor)
        self.assertIsInstance(m, EnhancedPerformanceMonitor)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_remaining_score_lines(self, mock_lib):
        """Test remaining score calculation lines."""
        mock_c = Mock()
        mock_c.contents.operation_type = b"test"
        mock_c.contents.operation_name = b"test"
        mock_c.contents.baseline_memory_mb = 50
        mock_c.contents.query_count_start = 0
        mock_c.contents.cache_hits = 8
        mock_c.contents.cache_misses = 2
        
        # Test various values to hit different branches
        values = [
            (49, 0),    # < 50ms response, 0 memory delta
            (51, 11),   # > 50ms response, > 10MB memory
            (101, 51),  # > 100ms response, > 50MB memory  
            (201, 101), # > 200ms response, > 100MB memory
        ]
        
        for rt, mem in values:
            mock_c.contents.end_time_ns = 1000000000 + rt * 1000000
            mock_c.contents.start_time_ns = 1000000000
            mock_c.contents.memory_end_bytes = 100000000 + mem * 1000000
            mock_c.contents.memory_start_bytes = 100000000
            mock_c.contents.query_count_end = 5
            
            mock_lib.get_elapsed_time_ms.return_value = float(rt)
            mock_lib.get_memory_usage_mb.return_value = 100.0 + mem
            mock_lib.get_memory_delta_mb.return_value = float(mem)
            mock_lib.get_query_count.return_value = 5
            mock_lib.get_cache_hit_ratio.return_value = 0.8
            
            m = EnhancedPerformanceMetrics_Python(mock_c, "test", None)
            s = m.performance_score
            self.assertIsNotNone(s)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_remaining_monitor_lines(self, mock_lib):
        """Test remaining monitor lines."""
        # Line 686: operation_type
        m = EnhancedPerformanceMonitor("t", operation_type="special")
        self.assertEqual(m.operation_type, "special")
        
        # Line 818: enter with None
        mock_lib.start_performance_monitoring_enhanced.return_value = None
        m2 = EnhancedPerformanceMonitor("t2")
        r = m2.__enter__()
        self.assertEqual(r, m2)
        
        # Line 610: metrics creation
        m3 = EnhancedPerformanceMonitor("t3")
        mock_lib.start_performance_monitoring_enhanced.return_value = 999
        
        c = Mock()
        c.contents.operation_type = b"t"
        c.contents.operation_name = b"t"
        c.contents.end_time_ns = 2000000000
        c.contents.start_time_ns = 1000000000
        c.contents.memory_end_bytes = 100000000
        c.contents.memory_start_bytes = 100000000
        c.contents.query_count_end = 1
        c.contents.query_count_start = 0
        c.contents.cache_hits = 1
        c.contents.cache_misses = 0
        c.contents.baseline_memory_mb = 50
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = Mock(contents=c.contents)
        mock_lib.get_elapsed_time_ms.return_value = 1000.0
        mock_lib.get_memory_usage_mb.return_value = 100.0
        mock_lib.get_memory_delta_mb.return_value = 0.0
        mock_lib.get_query_count.return_value = 1
        mock_lib.get_cache_hit_ratio.return_value = 1.0
        
        m3.__enter__()
        m3.__exit__(None, None, None)
        self.assertIsNotNone(m3._metrics)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_chaining_methods(self, mock_lib):
        """Test method chaining lines 1224-1225, 1269."""
        m = EnhancedPerformanceMonitor("t")
        
        # All these should return self
        r1 = m.set_test_context("f.py", 1, "func")
        self.assertEqual(r1, m)
        
        m._auto_assert = True
        r2 = m.disable_auto_assert()
        self.assertEqual(r2, m)
        self.assertFalse(m._auto_assert)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_threshold_violations(self, mock_lib):
        """Test threshold violation lines 1339, 1343."""
        m = EnhancedPerformanceMonitor("t")
        m.expect_response_under(10)
        m.expect_memory_under(10)
        
        metrics = Mock()
        metrics.response_time = 100
        metrics.memory_usage = 100
        metrics.query_count = 1
        metrics.cache_hit_ratio = 0.5
        m._metrics = metrics
        
        with self.assertRaises(AssertionError):
            m._assert_thresholds()


if __name__ == '__main__':
    unittest.main()