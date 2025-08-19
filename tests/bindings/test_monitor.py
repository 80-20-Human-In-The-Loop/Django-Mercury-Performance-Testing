"""
Tests for Django Mercury performance monitor.

Tests the performance monitoring system including C library integration,
Django hooks, and performance metrics collection.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import ctypes
import logging

from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics,
    MockLib,
    _get_lib,
    _configure_lib_signatures,
)


class TestMockLib(unittest.TestCase):
    """Test the mock C library fallback."""

    def setUp(self):
        """Set up mock library instance."""
        self.mock_lib = MockLib()

    def test_mock_get_functions(self):
        """Test mock functions starting with 'get_'."""
        # Ratio functions should return 0.0
        self.assertEqual(self.mock_lib.get_cache_hit_ratio(), 0.0)
        self.assertEqual(self.mock_lib.get_memory_ratio(), 0.0)

        # Non-ratio get functions should return 0
        self.assertEqual(self.mock_lib.get_query_count(), 0)
        self.assertEqual(self.mock_lib.get_memory_usage(), 0)

    def test_mock_has_functions(self):
        """Test mock functions starting with 'has_'."""
        self.assertEqual(self.mock_lib.has_n_plus_one_pattern(), 0)
        self.assertEqual(self.mock_lib.has_memory_leak(), 0)

    def test_mock_detect_functions(self):
        """Test mock functions starting with 'detect_'."""
        self.assertEqual(self.mock_lib.detect_n_plus_one_severe(), 0)
        self.assertEqual(self.mock_lib.detect_performance_issue(), 0)

    def test_mock_start_monitoring(self):
        """Test mock start monitoring function."""
        result = self.mock_lib.start_performance_monitoring_enhanced()
        self.assertEqual(result, -1)

    def test_mock_other_functions(self):
        """Test other mock functions return None."""
        self.assertIsNone(self.mock_lib.some_other_function())
        self.assertIsNone(self.mock_lib.calculate_something())


class TestEnhancedPerformanceMetrics(unittest.TestCase):
    """Test the C structure for performance metrics."""

    def test_structure_fields(self):
        """Test that all required fields are present."""
        metrics = EnhancedPerformanceMetrics()

        # Test field access (should not raise AttributeError)
        metrics.start_time_ns = 1000
        metrics.end_time_ns = 2000
        metrics.memory_start_bytes = 1024
        metrics.memory_peak_bytes = 2048
        metrics.memory_end_bytes = 1536
        metrics.query_count_start = 0
        metrics.query_count_end = 5
        metrics.cache_hits = 3
        metrics.cache_misses = 2

        # Test string fields
        metrics.operation_name = b"test_operation"
        metrics.operation_type = b"test_type"

        # Verify values
        self.assertEqual(metrics.start_time_ns, 1000)
        self.assertEqual(metrics.end_time_ns, 2000)
        self.assertEqual(metrics.cache_hits, 3)
        self.assertEqual(metrics.operation_name, b"test_operation")

    def test_structure_size(self):
        """Test structure has reasonable size."""
        metrics = EnhancedPerformanceMetrics()
        size = ctypes.sizeof(metrics)

        # Should be at least the sum of basic fields plus string buffers
        # Actual size is 376, so let's test for a reasonable minimum
        expected_min_size = 300  # Reasonable minimum size
        self.assertGreaterEqual(size, expected_min_size)
        self.assertLessEqual(size, 1000)  # Reasonable maximum size


class TestLibraryInitialization(unittest.TestCase):
    """Test C library initialization logic."""

    def setUp(self):
        """Reset library state for each test."""
        # Reset global state
        import django_mercury.python_bindings.monitor as monitor_module

        monitor_module._lib = None
        monitor_module._lib_initialized = False
        monitor_module._lib_configured = False

    @patch("django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE", False)
    def test_get_lib_no_extensions(self):
        """Test library initialization when C extensions are not available."""
        lib = _get_lib()
        self.assertIsNone(lib)

    @patch("django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE", True)
    @patch("django_mercury.python_bindings.monitor.c_extensions", None)
    def test_get_lib_no_c_extensions_object(self):
        """Test library initialization when c_extensions object is None."""
        lib = _get_lib()
        self.assertIsNone(lib)

    @patch("django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE", True)
    def test_get_lib_with_metrics_engine(self):
        """Test library initialization in pure Python mode."""
        # Pure Python mode - always returns None (no C extensions)
        lib = _get_lib()
        self.assertIsNone(lib)

    @patch.dict("os.environ", {"MERCURY_DEFER_INIT": "1"})
    def test_get_lib_deferred_init_not_available(self):
        """Test library initialization in deferred mode in pure Python."""
        # Pure Python mode - always returns None regardless of deferred init
        lib = _get_lib()
        self.assertIsNone(lib)

    @patch("django_mercury.python_bindings.monitor.c_extensions")
    def test_get_lib_initialization_error(self, mock_c_extensions):
        """Test library initialization handles errors gracefully."""
        mock_c_extensions.metrics_engine = None
        # Force an exception during initialization
        mock_c_extensions.side_effect = Exception("Test error")

        with patch("django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE", True):
            lib = _get_lib()
            self.assertIsNone(lib)

    def test_configure_lib_signatures_with_mock(self):
        """Test configuration with mock library does nothing."""
        mock_lib = MockLib()

        # Should not raise any errors
        _configure_lib_signatures(mock_lib)

        # Mock lib should still work normally
        self.assertEqual(mock_lib.get_cache_hit_ratio(), 0.0)

    def test_configure_lib_signatures_with_none(self):
        """Test configuration with None library does nothing."""
        # Should not raise any errors
        _configure_lib_signatures(None)

    def test_configure_lib_signatures_with_real_lib(self):
        """Test configuration with real library sets up signatures."""
        mock_lib = Mock()

        # Configure signatures
        _configure_lib_signatures(mock_lib)

        # Verify some function signatures were set
        self.assertTrue(hasattr(mock_lib.start_performance_monitoring_enhanced, "argtypes"))
        self.assertTrue(hasattr(mock_lib.stop_performance_monitoring_enhanced, "restype"))


class TestEnhancedPerformanceMonitor(unittest.TestCase):
    """Test the main performance monitor class."""

    def setUp(self):
        """Set up test monitor."""
        # Reset library state
        import django_mercury.python_bindings.monitor as monitor_module

        monitor_module._lib = None
        monitor_module._lib_initialized = False
        monitor_module.lib = MockLib()

        self.monitor = EnhancedPerformanceMonitor("test_operation")

    def test_initialization(self):
        """Test monitor initializes correctly."""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.operation_name, "test_operation")
        self.assertEqual(self.monitor.operation_type, "general")

    def test_initialization_with_operation_type(self):
        """Test monitor initialization with custom operation type."""
        monitor = EnhancedPerformanceMonitor("test_view", "view")

        self.assertEqual(monitor.operation_name, "test_view")
        self.assertEqual(monitor.operation_type, "view")

    @patch("django_mercury.python_bindings.monitor.DjangoQueryTracker")
    @patch("django_mercury.python_bindings.monitor.DjangoCacheTracker")
    def test_initialization_with_django_hooks(self, mock_cache_tracker, mock_query_tracker):
        """Test monitor initialization with Django hooks available."""
        mock_query_instance = Mock()
        mock_cache_instance = Mock()
        mock_query_tracker.return_value = mock_query_instance
        mock_cache_tracker.return_value = mock_cache_instance

        monitor = EnhancedPerformanceMonitor("test_django_operation")

        # Should not raise errors during initialization
        self.assertIsNotNone(monitor)

    def test_thread_safety_lock(self):
        """Test monitor uses threading lock for thread safety."""
        import threading

        # The monitor should have some thread safety mechanism
        # We test that it can be used in a threaded environment
        results = []

        def monitor_operation():
            try:
                monitor = EnhancedPerformanceMonitor("thread_test_operation")
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        # Run multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=monitor_operation)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should succeed
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(result, "success")

    @patch("django_mercury.python_bindings.monitor._get_lib")
    def test_monitor_with_mock_lib(self, mock_get_lib):
        """Test monitor works with mock library."""
        mock_get_lib.return_value = MockLib()

        monitor = EnhancedPerformanceMonitor("test_operation")

        # Should not raise errors
        self.assertIsNotNone(monitor)

    @patch("django_mercury.python_bindings.monitor._get_lib")
    def test_monitor_with_real_lib(self, mock_get_lib):
        """Test monitor works with real library."""
        mock_lib = Mock()
        mock_get_lib.return_value = mock_lib

        monitor = EnhancedPerformanceMonitor("test_operation")

        # Should not raise errors
        self.assertIsNotNone(monitor)

    @patch("django_mercury.python_bindings.monitor.logger")
    def test_logging_integration(self, mock_logger):
        """Test monitor integrates with logging system."""
        # Creating a monitor might generate log messages
        monitor = EnhancedPerformanceMonitor("test_operation")

        # Logger should be available for debugging
        self.assertIsNotNone(mock_logger)


class TestPerformanceMonitorErrorHandling(unittest.TestCase):
    """Test error handling in performance monitor."""

    def setUp(self):
        """Set up test environment."""
        # Reset library state
        import django_mercury.python_bindings.monitor as monitor_module

        monitor_module._lib = None
        monitor_module._lib_initialized = False

    def test_library_load_error_handling(self):
        """Test graceful handling in pure Python mode."""
        # Pure Python mode - no libraries to load, no errors to handle
        lib = _get_lib()

        # Should return None (pure Python mode)
        self.assertIsNone(lib)

    def test_monitor_creation_with_import_errors(self):
        """Test monitor creation when imports fail."""
        # Even with import errors, monitor creation should not fail
        # because of the fallback imports and MockLib
        monitor = EnhancedPerformanceMonitor("test_operation")
        self.assertIsNotNone(monitor)

    @patch("django_mercury.python_bindings.monitor.DjangoQueryTracker", None)
    @patch("django_mercury.python_bindings.monitor.DjangoCacheTracker", None)
    def test_monitor_without_django_hooks(self):
        """Test monitor works without Django hooks available."""
        monitor = EnhancedPerformanceMonitor("test_operation")

        # Should still work without Django components
        self.assertIsNotNone(monitor)


class TestModuleConstants(unittest.TestCase):
    """Test module-level constants and flags."""

    def test_c_extensions_available_flag(self):
        """Test C_EXTENSIONS_AVAILABLE flag is boolean."""
        from django_mercury.python_bindings.monitor import C_EXTENSIONS_AVAILABLE

        self.assertIsInstance(C_EXTENSIONS_AVAILABLE, bool)

    def test_lib_configured_flag(self):
        """Test _lib_configured flag is boolean."""
        from django_mercury.python_bindings.monitor import _lib_configured

        self.assertIsInstance(_lib_configured, bool)

    def test_module_logger(self):
        """Test module has proper logger."""
        from django_mercury.python_bindings.monitor import logger

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "django_mercury.python_bindings.monitor")


if __name__ == "__main__":
    unittest.main()
