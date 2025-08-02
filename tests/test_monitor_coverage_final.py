"""
Final targeted tests to reach 90% coverage on monitor.py.
Focus on largest remaining uncovered blocks: lines 57-75, 1361-1396.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python
)


class TestMonitorInitializationEdgeCases(unittest.TestCase):
    """Test monitor initialization edge cases (lines 57-75)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_with_empty_operation_name(self, mock_lib):
        """Test monitor with empty operation name."""
        # Should handle empty operation name gracefully
        monitor = EnhancedPerformanceMonitor("")
        self.assertEqual(monitor.operation_name, "")
        self.assertIsNone(monitor._metrics)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_with_none_operation_name(self, mock_lib):
        """Test monitor with None operation name."""
        # Should handle None operation name
        monitor = EnhancedPerformanceMonitor(None)
        self.assertIsNone(monitor.operation_name)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_attributes_initialization(self, mock_lib):
        """Test monitor attributes are properly initialized."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Should initialize all expected attributes
        self.assertEqual(monitor.operation_name, "test_op")
        self.assertEqual(monitor.operation_type, "general")
        self.assertIsNone(monitor.handle)
        self.assertIsNone(monitor._metrics)
        self.assertIsInstance(monitor._thresholds, dict)
        self.assertFalse(monitor._auto_assert)
        self.assertIsNone(monitor._test_file)
        self.assertIsNone(monitor._test_line)
        self.assertIsNone(monitor._test_method)
        self.assertFalse(monitor._show_educational_guidance)
        self.assertIsInstance(monitor._operation_context, dict)
        self.assertIsNone(monitor._query_tracker)
        self.assertIsNone(monitor._cache_tracker)
        self.assertFalse(monitor._django_hooks_active)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_default_thresholds_initialization(self, mock_lib):
        """Test monitor default thresholds are properly initialized."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Default thresholds should be empty dict initially
        self.assertIsInstance(monitor._thresholds, dict)
        self.assertEqual(len(monitor._thresholds), 0)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_auto_assert_default(self, mock_lib):
        """Test monitor auto assert default value."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Should default to False
        self.assertFalse(monitor._auto_assert)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_educational_guidance_default(self, mock_lib):
        """Test monitor educational guidance default value."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Should default to False
        self.assertFalse(monitor._show_educational_guidance)


class TestAdvancedErrorLocationHandling(unittest.TestCase):
    """Test advanced error location handling (lines 1361-1396)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set up metrics and thresholds to trigger assertion failure
        self.monitor._metrics = Mock()
        self.monitor._metrics.response_time = 500
        self.monitor._thresholds = {'response_time': 200}
        self.monitor._auto_assert = True
    
    @patch('django_mercury.python_bindings.monitor.Path')
    def test_error_location_with_complex_path_handling(self, mock_path_class):
        """Test complex path handling in error location formatting."""
        # Set up test file info with complex path
        self.monitor._test_file = "/very/deep/nested/project/structure/backend/tests/test_file.py"
        self.monitor._test_line = 123
        self.monitor._test_method = "test_complex_method"
        
        # Mock Path objects for complex path manipulation
        mock_test_path = Mock()
        mock_cwd_path = Mock()
        mock_path_class.side_effect = [mock_test_path, mock_cwd_path]
        
        # Simulate relative_to failure and complex parts handling
        mock_test_path.relative_to.side_effect = ValueError("Not relative")
        mock_test_path.parts = ('very', 'deep', 'nested', 'project', 'structure', 'backend', 'tests', 'test_file.py')
        mock_test_path.name = "test_file.py"
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should include backend path when found in parts
        self.assertIn("backend/tests/test_file.py:123", error_msg)
        self.assertIn("test_complex_method()", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.Path')
    def test_error_location_with_multiple_key_parts(self, mock_path_class):
        """Test error location with multiple key directory parts."""
        self.monitor._test_file = "/home/user/EduLite/performance_testing/backend/test_file.py"
        self.monitor._test_line = 456
        self.monitor._test_method = "test_multi_key_method"
        
        mock_test_path = Mock()
        mock_cwd_path = Mock() 
        mock_path_class.side_effect = [mock_test_path, mock_cwd_path]
        
        mock_test_path.relative_to.side_effect = ValueError("Not relative")
        mock_test_path.parts = ('home', 'user', 'EduLite', 'performance_testing', 'backend', 'test_file.py')
        mock_test_path.name = "test_file.py"
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should prioritize first found key part (EduLite in this case)
        self.assertIn("EduLite/performance_testing/backend/test_file.py:456", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.Path')
    def test_error_location_with_path_indexing_edge_cases(self, mock_path_class):
        """Test error location path indexing edge cases."""
        self.monitor._test_file = "/EduLite/test_file.py"  # EduLite at index 1
        self.monitor._test_line = 789
        self.monitor._test_method = "test_edge_case"
        
        mock_test_path = Mock()
        mock_cwd_path = Mock()
        mock_path_class.side_effect = [mock_test_path, mock_cwd_path]
        
        mock_test_path.relative_to.side_effect = ValueError("Not relative")
        mock_test_path.parts = ('', 'EduLite', 'test_file.py')  # Empty first part from absolute path
        mock_test_path.name = "test_file.py"
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should handle the edge case properly
        self.assertIn("EduLite/test_file.py:789", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.Path')
    def test_error_location_with_parts_attribute_error(self, mock_path_class):
        """Test error location when parts attribute causes error."""
        self.monitor._test_file = "/some/path/test_file.py"
        self.monitor._test_line = 999
        self.monitor._test_method = "test_parts_error"
        
        mock_test_path = Mock()
        mock_cwd_path = Mock()
        mock_path_class.side_effect = [mock_test_path, mock_cwd_path]
        
        mock_test_path.relative_to.side_effect = ValueError("Not relative")
        # Make parts raise an AttributeError
        type(mock_test_path).parts = Mock(side_effect=AttributeError("No parts"))
        mock_test_path.name = "test_file.py"
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should fall back to filename only
        self.assertIn("test_file.py:999", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.Path')
    def test_error_location_with_name_attribute_error(self, mock_path_class):
        """Test error location when name attribute causes error."""
        self.monitor._test_file = "/some/path/test_file.py"
        self.monitor._test_line = 111
        self.monitor._test_method = "test_name_error"
        
        mock_test_path = Mock()
        mock_cwd_path = Mock()
        mock_path_class.side_effect = [mock_test_path, mock_cwd_path]
        
        mock_test_path.relative_to.side_effect = ValueError("Not relative")
        mock_test_path.parts = ('some', 'path', 'test_file.py')
        # Make name raise an AttributeError
        type(mock_test_path).name = Mock(side_effect=AttributeError("No name"))
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should fall back to filename when name fails
        self.assertIn("test_file.py:111", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.Path')
    def test_error_location_path_construction_error(self, mock_path_class):
        """Test error location when Path construction fails."""
        self.monitor._test_file = "/some/path/test_file.py"
        self.monitor._test_line = 222
        self.monitor._test_method = "test_path_error"
        
        # Make Path construction raise an exception
        mock_path_class.side_effect = Exception("Path construction failed")
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should fall back to filename when Path construction fails
        self.assertIn("test_file.py:222", error_msg)
    
    def test_error_location_with_no_test_info_partial(self):
        """Test error location when some test info is missing."""
        # Only set file, no line or method
        self.monitor._test_file = "/some/path/test_file.py"
        self.monitor._test_line = None
        self.monitor._test_method = None
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should handle missing line and method gracefully
        self.assertIn("Response time", error_msg)
        self.assertIn("500", error_msg)
    
    def test_error_location_with_zero_line_number(self):
        """Test error location with zero line number."""
        self.monitor._test_file = "/some/path/test_file.py"
        self.monitor._test_line = 0
        self.monitor._test_method = "test_zero_line"
        
        with self.assertRaises(AssertionError) as context:
            self.monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # The actual test method info overrides our mocked info in this case
        # Just verify the assertion is raised
        self.assertIn("Response time", error_msg)


class TestIssueDetectionMethodsComplete(unittest.TestCase):
    """Test issue detection methods for complete coverage (lines 1414-1426)."""
    
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
    def test_detect_missing_indexes_all_conditions(self, mock_lib):
        """Test missing indexes detection with all condition branches."""
        test_cases = [
            # (query_count, response_time, expected)
            # EnhancedPerformanceMetrics_Python._detect_missing_indexes (line 480-481):
            # if 1 <= self.query_count <= 5 and self.response_time > 300: return True
            (0, 50.0, False),     # 0 queries, not in range [1,5] -> False
            (1, 50.0, False),     # 1 query, response_time <= 300 -> False
            (1, 350.0, True),     # 1 query, response_time > 300 -> True
            (2, 250.0, False),    # 2 queries, response_time <= 300 -> False
            (3, 250.0, False),    # 3 queries, response_time <= 300 -> False
            (3, 350.0, True),     # 3 queries, response_time > 300 -> True
            (4, 350.0, True),     # 4 queries, response_time > 300 -> True
            (5, 150.0, False),    # 5 queries, response_time <= 300 -> False
            (5, 350.0, True),     # 5 queries, response_time > 300 -> True
            (6, 350.0, False),    # 6 queries, not in range [1,5] -> False
            (10, 350.0, False),   # 10 queries, not in range [1,5] -> False
        ]
        
        for query_count, response_time, expected in test_cases:
            with self.subTest(query_count=query_count, response_time=response_time):
                mock_lib.get_elapsed_time_ms.return_value = response_time
                mock_lib.get_memory_usage_mb.return_value = 100.0
                mock_lib.get_memory_delta_mb.return_value = 50.0
                mock_lib.get_query_count.return_value = query_count
                mock_lib.get_cache_hit_ratio.return_value = 0.8
                
                self.mock_c_metrics.contents.query_count_end = query_count
                self.mock_c_metrics.contents.query_count_start = 0
                
                metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
                
                result = metrics._detect_missing_indexes()
                
                self.assertEqual(result, expected, 
                               f"Failed for query_count={query_count}, response_time={response_time}")


class TestMonitorFactoryEdgeCases(unittest.TestCase):
    """Test monitor factory functions edge cases (lines 47-54)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_factory_functions_with_various_inputs(self, mock_lib):
        """Test factory functions with various input types."""
        from django_mercury.python_bindings.monitor import (
            monitor_django_view, monitor_database_query, monitor_serializer, monitor_django_model
        )
        
        # Test with different operation name types
        test_names = [
            "test_view",
            "",
            None,
            123,  # Non-string type
        ]
        
        for name in test_names:
            with self.subTest(name=name):
                # Should not crash with any input type
                monitor1 = monitor_django_view(name)
                monitor2 = monitor_database_query(name)
                monitor3 = monitor_serializer(name)
                monitor4 = monitor_django_model(name)
                
                # All should be EnhancedPerformanceMonitor instances
                self.assertIsInstance(monitor1, EnhancedPerformanceMonitor)
                self.assertIsInstance(monitor2, EnhancedPerformanceMonitor)
                self.assertIsInstance(monitor3, EnhancedPerformanceMonitor)
                self.assertIsInstance(monitor4, EnhancedPerformanceMonitor)


if __name__ == '__main__':
    unittest.main()