"""
Comprehensive tests for PythonPerformanceMonitor in pure_python.py
Tests performance monitoring without C extensions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from django_mercury.python_bindings.pure_python import (
    PythonPerformanceMonitor,
    PythonPerformanceMetrics,
    python_performance_monitor
)


class TestPythonPerformanceMetrics(unittest.TestCase):
    """Test the PythonPerformanceMetrics dataclass."""
    
    def test_metrics_initialization(self):
        """Test that metrics initialize with correct defaults."""
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
    
    def test_metrics_fields_mutable(self):
        """Test that metrics fields can be modified."""
        metrics = PythonPerformanceMetrics()
        
        metrics.response_time_ms = 100.5
        metrics.query_count = 5
        metrics.queries.append({'sql': 'SELECT * FROM test'})
        metrics.errors.append('Test error')
        
        self.assertEqual(metrics.response_time_ms, 100.5)
        self.assertEqual(metrics.query_count, 5)
        self.assertEqual(len(metrics.queries), 1)
        self.assertEqual(len(metrics.errors), 1)


class TestPythonPerformanceMonitor(unittest.TestCase):
    """Test the PythonPerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PythonPerformanceMonitor()
    
    def test_initialization(self):
        """Test monitor initializes correctly."""
        self.assertIsNotNone(self.monitor.metrics)
        self.assertIsNone(self.monitor._start_time)
        self.assertIsNone(self.monitor._start_memory)
        self.assertIsNone(self.monitor._tracemalloc_snapshot)
        self.assertFalse(self.monitor._monitoring)
    
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    @patch('django_mercury.python_bindings.pure_python.gc.collect')
    def test_start_monitoring(self, mock_gc, mock_time):
        """Test starting monitoring."""
        mock_time.return_value = 1000.0
        
        self.monitor.start_monitoring()
        
        self.assertTrue(self.monitor._monitoring)
        self.assertEqual(self.monitor._start_time, 1000.0)
        mock_gc.assert_called_once()
    
    def test_start_monitoring_when_already_started(self):
        """Test that starting monitoring twice doesn't reset."""
        self.monitor._monitoring = True
        self.monitor._start_time = 500.0
        
        self.monitor.start_monitoring()
        
        # Should not reset
        self.assertEqual(self.monitor._start_time, 500.0)
    
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_stop_monitoring(self, mock_time):
        """Test stopping monitoring calculates metrics."""
        mock_time.side_effect = [1000.0, 1001.5]  # Start and stop times
        
        self.monitor.start_monitoring()
        self.monitor.stop_monitoring()
        
        self.assertFalse(self.monitor._monitoring)
        self.assertEqual(self.monitor.metrics.response_time_ms, 1500.0)  # 1.5 seconds
    
    def test_stop_monitoring_when_not_started(self):
        """Test stopping when not monitoring does nothing."""
        self.monitor.stop_monitoring()
        
        self.assertFalse(self.monitor._monitoring)
        self.assertEqual(self.monitor.metrics.response_time_ms, 0.0)
    
    def test_track_query(self):
        """Test tracking database queries."""
        self.monitor.track_query("SELECT * FROM users", 0.025)
        
        self.assertEqual(self.monitor.metrics.query_count, 1)
        self.assertEqual(len(self.monitor.metrics.queries), 1)
        
        query = self.monitor.metrics.queries[0]
        self.assertEqual(query['sql'], "SELECT * FROM users")
        self.assertEqual(query['duration_ms'], 25.0)
        self.assertIn('timestamp', query)
    
    def test_track_multiple_queries(self):
        """Test tracking multiple queries."""
        self.monitor.track_query("SELECT * FROM users", 0.025)
        self.monitor.track_query("SELECT * FROM posts", 0.015)
        self.monitor.track_query("UPDATE users SET active=1", 0.005)
        
        self.assertEqual(self.monitor.metrics.query_count, 3)
        self.assertEqual(len(self.monitor.metrics.queries), 3)
    
    def test_track_cache_hits(self):
        """Test tracking cache hits."""
        self.monitor.track_cache(True)
        self.monitor.track_cache(True)
        
        self.assertEqual(self.monitor.metrics.cache_hits, 2)
        self.assertEqual(self.monitor.metrics.cache_misses, 0)
    
    def test_track_cache_misses(self):
        """Test tracking cache misses."""
        self.monitor.track_cache(False)
        self.monitor.track_cache(False)
        self.monitor.track_cache(False)
        
        self.assertEqual(self.monitor.metrics.cache_hits, 0)
        self.assertEqual(self.monitor.metrics.cache_misses, 3)
    
    def test_track_cache_mixed(self):
        """Test tracking mixed cache hits and misses."""
        self.monitor.track_cache(True)
        self.monitor.track_cache(False)
        self.monitor.track_cache(True)
        self.monitor.track_cache(False)
        
        self.assertEqual(self.monitor.metrics.cache_hits, 2)
        self.assertEqual(self.monitor.metrics.cache_misses, 2)
    
    def test_get_metrics(self):
        """Test getting metrics as dictionary."""
        self.monitor.metrics.response_time_ms = 100.0
        self.monitor.metrics.memory_usage_mb = 50.0
        self.monitor.metrics.query_count = 5
        
        metrics = self.monitor.get_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics['response_time_ms'], 100.0)
        self.assertEqual(metrics['memory_usage_mb'], 50.0)
        self.assertEqual(metrics['query_count'], 5)
        self.assertEqual(metrics['implementation'], 'pure_python')
    
    def test_reset(self):
        """Test resetting monitor state."""
        # Set some state
        self.monitor.metrics.query_count = 10
        self.monitor._start_time = 1000.0
        self.monitor._monitoring = True
        
        # Reset
        self.monitor.reset()
        
        # Check everything is reset
        self.assertEqual(self.monitor.metrics.query_count, 0)
        self.assertIsNone(self.monitor._start_time)
        self.assertFalse(self.monitor._monitoring)


class TestPythonPerformanceMonitorWithPsutil(unittest.TestCase):
    """Test PythonPerformanceMonitor with psutil available."""
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.psutil')
    def test_initialization_with_psutil(self, mock_psutil):
        """Test initialization when psutil is available."""
        mock_process = Mock()
        mock_psutil.Process.return_value = mock_process
        
        monitor = PythonPerformanceMonitor()
        
        self.assertEqual(monitor._process, mock_process)
        mock_psutil.Process.assert_called_once()
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.psutil')
    def test_initialization_with_psutil_error(self, mock_psutil):
        """Test initialization when psutil raises error."""
        mock_psutil.Process.side_effect = Exception("Process error")
        
        monitor = PythonPerformanceMonitor()
        
        self.assertIsNone(monitor._process)
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.psutil')
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_memory_tracking_with_psutil(self, mock_time, mock_psutil):
        """Test memory tracking when psutil is available."""
        mock_time.return_value = 1000.0
        
        # Mock process
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100 MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        mock_psutil.Process.return_value = mock_process
        
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        
        self.assertEqual(monitor._start_memory, 100.0)  # MB
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.psutil')
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_stop_monitoring_with_psutil(self, mock_time, mock_psutil):
        """Test stopping monitoring calculates memory and CPU metrics."""
        mock_time.side_effect = [1000.0, 1001.0]
        
        # Mock process
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 150 * 1024 * 1024  # 150 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 25.5
        mock_psutil.Process.return_value = mock_process
        
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        monitor.stop_monitoring()
        
        self.assertEqual(monitor.metrics.peak_memory_mb, 150.0)
        self.assertEqual(monitor.metrics.cpu_percent, 25.5)
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.psutil')
    def test_memory_tracking_error_handling(self, mock_psutil):
        """Test error handling in memory tracking."""
        # Mock process that throws error
        mock_process = Mock()
        mock_process.memory_info.side_effect = Exception("Memory error")
        mock_psutil.Process.return_value = mock_process
        
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        
        # Should handle error gracefully
        self.assertEqual(monitor._start_memory, 0)


class TestPythonPerformanceMonitorWithTracemalloc(unittest.TestCase):
    """Test PythonPerformanceMonitor with tracemalloc available."""
    
    @patch('django_mercury.python_bindings.pure_python.TRACEMALLOC_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.tracemalloc')
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_memory_tracking_with_tracemalloc(self, mock_time, mock_tracemalloc):
        """Test memory tracking with tracemalloc."""
        mock_time.return_value = 1000.0
        mock_tracemalloc.is_tracing.return_value = False
        mock_snapshot = Mock()
        mock_tracemalloc.take_snapshot.return_value = mock_snapshot
        
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        
        mock_tracemalloc.start.assert_called_once()
        mock_tracemalloc.take_snapshot.assert_called_once()
        self.assertEqual(monitor._tracemalloc_snapshot, mock_snapshot)
    
    @patch('django_mercury.python_bindings.pure_python.TRACEMALLOC_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.tracemalloc')
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_memory_tracking_already_tracing(self, mock_time, mock_tracemalloc):
        """Test when tracemalloc is already tracing."""
        mock_time.return_value = 1000.0
        mock_tracemalloc.is_tracing.return_value = True
        mock_snapshot = Mock()
        mock_tracemalloc.take_snapshot.return_value = mock_snapshot
        
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        
        mock_tracemalloc.start.assert_not_called()  # Should not start again
        mock_tracemalloc.take_snapshot.assert_called_once()
    
    @patch('django_mercury.python_bindings.pure_python.TRACEMALLOC_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.tracemalloc')
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_stop_monitoring_with_tracemalloc(self, mock_time, mock_tracemalloc):
        """Test calculating memory usage with tracemalloc."""
        mock_time.side_effect = [1000.0, 1001.0]
        
        # Mock snapshots and stats
        mock_start_snapshot = Mock()
        mock_end_snapshot = Mock()
        mock_tracemalloc.take_snapshot.side_effect = [mock_start_snapshot, mock_end_snapshot]
        
        mock_stat1 = Mock(size_diff=1024 * 1024)  # 1 MB
        mock_stat2 = Mock(size_diff=2048 * 1024)  # 2 MB
        mock_stat3 = Mock(size_diff=-512 * 1024)  # -0.5 MB (ignored)
        mock_end_snapshot.compare_to.return_value = [mock_stat1, mock_stat2, mock_stat3]
        
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        monitor.stop_monitoring()
        
        # Should sum only positive diffs: 1 MB + 2 MB = 3 MB
        self.assertEqual(monitor.metrics.memory_usage_mb, 3.0)
    
    @patch('django_mercury.python_bindings.pure_python.TRACEMALLOC_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.tracemalloc')
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_tracemalloc_error_handling(self, mock_time, mock_tracemalloc):
        """Test error handling in tracemalloc operations."""
        mock_time.side_effect = [1000.0, 1001.0]
        
        mock_snapshot = Mock()
        mock_tracemalloc.take_snapshot.side_effect = [mock_snapshot, Exception("Snapshot error")]
        
        monitor = PythonPerformanceMonitor()
        monitor.start_monitoring()
        monitor.stop_monitoring()
        
        # Should handle error and add to errors list
        self.assertEqual(len(monitor.metrics.errors), 1)
        self.assertIn("Memory tracking error", monitor.metrics.errors[0])


class TestPythonPerformanceMonitorWithoutDependencies(unittest.TestCase):
    """Test PythonPerformanceMonitor without psutil or tracemalloc."""
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', False)
    @patch('django_mercury.python_bindings.pure_python.TRACEMALLOC_AVAILABLE', False)
    def test_monitoring_without_dependencies(self):
        """Test monitoring works without optional dependencies."""
        monitor = PythonPerformanceMonitor()
        
        self.assertIsNone(monitor._process)
        
        monitor.start_monitoring()
        self.assertTrue(monitor._monitoring)
        
        monitor.stop_monitoring()
        self.assertFalse(monitor._monitoring)
        
        # Should still track basic metrics
        metrics = monitor.get_metrics()
        self.assertIn('response_time_ms', metrics)
        self.assertIn('memory_usage_mb', metrics)


class TestPythonPerformanceContextManager(unittest.TestCase):
    """Test the python_performance_monitor context manager."""
    
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_context_manager_basic_usage(self, mock_time):
        """Test basic context manager usage."""
        mock_time.side_effect = [1000.0, 1001.0]
        
        with python_performance_monitor() as monitor:
            self.assertIsInstance(monitor, PythonPerformanceMonitor)
            self.assertTrue(monitor._monitoring)
        
        # Should be stopped after exiting
        self.assertFalse(monitor._monitoring)
        self.assertEqual(monitor.metrics.response_time_ms, 1000.0)
    
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_context_manager_with_exception(self, mock_time):
        """Test context manager handles exceptions properly."""
        mock_time.side_effect = [1000.0, 1001.0]
        
        try:
            with python_performance_monitor() as monitor:
                self.assertTrue(monitor._monitoring)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should still stop monitoring
        self.assertFalse(monitor._monitoring)
        self.assertEqual(monitor.metrics.response_time_ms, 1000.0)
    
    @patch('django_mercury.python_bindings.pure_python.time.perf_counter')
    def test_context_manager_with_operations(self, mock_time):
        """Test context manager with tracking operations."""
        mock_time.side_effect = [1000.0, 1001.5]
        
        with python_performance_monitor() as monitor:
            # Track some operations
            monitor.track_query("SELECT * FROM users", 0.025)
            monitor.track_query("SELECT * FROM posts", 0.015)
            monitor.track_cache(True)
            monitor.track_cache(False)
        
        metrics = monitor.get_metrics()
        self.assertEqual(metrics['response_time_ms'], 1500.0)
        self.assertEqual(metrics['query_count'], 2)
        self.assertEqual(metrics['cache_hits'], 1)
        self.assertEqual(metrics['cache_misses'], 1)


if __name__ == '__main__':
    unittest.main()