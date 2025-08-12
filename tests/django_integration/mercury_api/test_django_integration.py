"""
Test suite for Django integration module.

This module tests the DjangoPerformanceAPITestCase class which provides
performance-aware testing capabilities for Django applications.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
from typing import Any, Dict, Optional, Union, Callable

from django_mercury.python_bindings.django_integration import (
    DjangoPerformanceAPITestCase
)
from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python
)


class TestDjangoPerformanceAPITestCase(unittest.TestCase):
    """Test DjangoPerformanceAPITestCase functionality."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_case = DjangoPerformanceAPITestCase()
        
        # Mock metrics for testing
        self.mock_metrics = Mock(spec=EnhancedPerformanceMetrics_Python)
        self.mock_metrics.response_time = 50.0
        self.mock_metrics.memory_usage = 10.0
        self.mock_metrics.query_count = 3
        self.mock_metrics.cache_hit_ratio = 0.85
        self.mock_metrics.is_fast = True
        self.mock_metrics.is_slow = False
        self.mock_metrics.is_memory_intensive = False
        
        # Mock Django issues
        self.mock_django_issues = Mock()
        self.mock_django_issues.has_n_plus_one = False
        self.mock_django_issues.has_issues = False
        self.mock_django_issues.get_issue_summary.return_value = []
        self.mock_metrics.django_issues = self.mock_django_issues
        
        # Mock performance status
        self.mock_performance_status = Mock()
        self.mock_performance_status.value = "fast"
        self.mock_metrics.performance_status = self.mock_performance_status
        
        # Mock monitor
        self.mock_monitor = Mock(spec=EnhancedPerformanceMonitor)
        self.mock_monitor.metrics = self.mock_metrics
    
    def test_test_case_inheritance(self) -> None:
        """Test that DjangoPerformanceAPITestCase inherits from APITestCase."""
        from rest_framework.test import APITestCase
        self.assertIsInstance(self.test_case, APITestCase)
    
    def test_assert_performance_success(self) -> None:
        """Test assertPerformance with successful performance metrics."""
        # Mock the monitor's assert_performance method
        self.mock_monitor.assert_performance = Mock()
        
        self.test_case.assertPerformance(
            self.mock_monitor,
            max_response_time=100.0,
            max_memory_mb=20.0,
            max_queries=5,
            min_cache_hit_ratio=0.7
        )
        
        self.mock_monitor.assert_performance.assert_called_once_with(
            100.0, 20.0, 5, 0.7
        )
    
    def test_assert_performance_failure(self) -> None:
        """Test assertPerformance with failing performance metrics."""
        # Mock the monitor to raise AssertionError
        self.mock_monitor.assert_performance = Mock(side_effect=AssertionError("Performance failed"))
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertPerformance(self.mock_monitor)
        
        self.assertIn("Performance failed", str(context.exception))
    
    def test_assert_performance_failure_with_custom_message(self) -> None:
        """Test assertPerformance with custom failure message."""
        self.mock_monitor.assert_performance = Mock(side_effect=AssertionError("Response time exceeded"))
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertPerformance(self.mock_monitor, msg="Custom test failed")
        
        self.assertIn("Custom test failed", str(context.exception))
        self.assertIn("Response time exceeded", str(context.exception))
    
    def test_assert_response_time_less_success_with_monitor(self) -> None:
        """Test assertResponseTimeLess with monitor object (success)."""
        self.mock_metrics.response_time = 50.0
        
        # Should not raise any exception
        self.test_case.assertResponseTimeLess(self.mock_monitor, 100.0)
    
    def test_assert_response_time_less_success_with_metrics(self) -> None:
        """Test assertResponseTimeLess with metrics object (success)."""
        self.mock_metrics.response_time = 75.0
        
        # Should not raise any exception
        self.test_case.assertResponseTimeLess(self.mock_metrics, 100.0)
    
    def test_assert_response_time_less_failure(self) -> None:
        """Test assertResponseTimeLess with failing response time."""
        self.mock_metrics.response_time = 150.0
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertResponseTimeLess(self.mock_monitor, 100.0)
        
        self.assertIn("Response time 150.00ms is not less than 100.0ms", str(context.exception))
    
    def test_assert_response_time_less_failure_with_message(self) -> None:
        """Test assertResponseTimeLess with custom failure message."""
        self.mock_metrics.response_time = 150.0
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertResponseTimeLess(self.mock_monitor, 100.0, "API too slow")
        
        self.assertIn("API too slow", str(context.exception))
    
    def test_assert_memory_less_success(self) -> None:
        """Test assertMemoryLess with successful memory usage."""
        self.mock_metrics.memory_usage = 15.0
        
        # Should not raise any exception
        self.test_case.assertMemoryLess(self.mock_monitor, 20.0)
    
    def test_assert_memory_less_failure(self) -> None:
        """Test assertMemoryLess with failing memory usage."""
        self.mock_metrics.memory_usage = 25.0
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertMemoryLess(self.mock_monitor, 20.0)
        
        self.assertIn("Memory usage 25.00MB is not less than 20.0MB", str(context.exception))
    
    def test_assert_queries_less_success(self) -> None:
        """Test assertQueriesLess with successful query count."""
        self.mock_metrics.query_count = 3
        
        # Should not raise any exception
        self.test_case.assertQueriesLess(self.mock_monitor, 5)
    
    def test_assert_queries_less_failure(self) -> None:
        """Test assertQueriesLess with failing query count."""
        self.mock_metrics.query_count = 8
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertQueriesLess(self.mock_monitor, 5)
        
        self.assertIn("Query count 8 is not less than 5", str(context.exception))
    
    def test_assert_queries_less_no_query_count_attribute(self) -> None:
        """Test assertQueriesLess when metrics has no query_count attribute."""
        delattr(self.mock_metrics, 'query_count')
        
        # Should use default value of 0 and pass
        self.test_case.assertQueriesLess(self.mock_monitor, 5)
    
    def test_assert_performance_fast_success(self) -> None:
        """Test assertPerformanceFast with fast performance."""
        self.mock_metrics.is_fast = True
        
        # Should not raise any exception
        self.test_case.assertPerformanceFast(self.mock_monitor)
    
    def test_assert_performance_fast_failure(self) -> None:
        """Test assertPerformanceFast with non-fast performance."""
        self.mock_metrics.is_fast = False
        self.mock_metrics.response_time = 250.0
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertPerformanceFast(self.mock_monitor)
        
        self.assertIn("Performance is not fast: 250.00ms", str(context.exception))
    
    def test_assert_performance_not_slow_success(self) -> None:
        """Test assertPerformanceNotSlow with non-slow performance."""
        self.mock_metrics.is_slow = False
        
        # Should not raise any exception
        self.test_case.assertPerformanceNotSlow(self.mock_monitor)
    
    def test_assert_performance_not_slow_failure(self) -> None:
        """Test assertPerformanceNotSlow with slow performance."""
        self.mock_metrics.is_slow = True
        self.mock_metrics.response_time = 750.0
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertPerformanceNotSlow(self.mock_monitor)
        
        self.assertIn("Performance is slow: 750.00ms", str(context.exception))
    
    def test_assert_memory_efficient_success(self) -> None:
        """Test assertMemoryEfficient with efficient memory usage."""
        self.mock_metrics.is_memory_intensive = False
        
        # Should not raise any exception
        self.test_case.assertMemoryEfficient(self.mock_monitor)
    
    def test_assert_memory_efficient_failure(self) -> None:
        """Test assertMemoryEfficient with intensive memory usage."""
        self.mock_metrics.is_memory_intensive = True
        self.mock_metrics.memory_usage = 128.0
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertMemoryEfficient(self.mock_monitor)
        
        self.assertIn("Memory usage is intensive: 128.00MB", str(context.exception))
    
    def test_assert_no_n_plus_one_success(self) -> None:
        """Test assertNoNPlusOne with no N+1 issues."""
        self.mock_django_issues.has_n_plus_one = False
        
        # Should not raise any exception
        self.test_case.assertNoNPlusOne(self.mock_monitor)
    
    def test_assert_no_n_plus_one_failure(self) -> None:
        """Test assertNoNPlusOne with N+1 issues detected."""
        self.mock_django_issues.has_n_plus_one = True
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertNoNPlusOne(self.mock_monitor)
        
        self.assertIn("N+1 query pattern detected", str(context.exception))
    
    def test_assert_no_n_plus_one_no_django_issues(self) -> None:
        """Test assertNoNPlusOne when metrics has no django_issues attribute."""
        delattr(self.mock_metrics, 'django_issues')
        
        # Should not raise any exception when attribute is missing
        self.test_case.assertNoNPlusOne(self.mock_monitor)
    
    def test_assert_good_cache_performance_success(self) -> None:
        """Test assertGoodCachePerformance with good cache ratio."""
        self.mock_metrics.cache_hit_ratio = 0.85
        
        # Should not raise any exception
        self.test_case.assertGoodCachePerformance(self.mock_monitor, min_hit_ratio=0.7)
    
    def test_assert_good_cache_performance_failure(self) -> None:
        """Test assertGoodCachePerformance with poor cache ratio."""
        self.mock_metrics.cache_hit_ratio = 0.5
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assertGoodCachePerformance(self.mock_monitor, min_hit_ratio=0.7)
        
        self.assertIn("Cache hit ratio 50.0% is below 70.0%", str(context.exception))
    
    def test_assert_good_cache_performance_no_cache_attribute(self) -> None:
        """Test assertGoodCachePerformance when metrics has no cache_hit_ratio attribute."""
        delattr(self.mock_metrics, 'cache_hit_ratio')
        
        # Should not raise any exception when attribute is missing
        self.test_case.assertGoodCachePerformance(self.mock_monitor)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_monitor_django_view(self, mock_monitor_function) -> None:
        """Test monitor_django_view method."""
        mock_monitor_instance = Mock()
        mock_monitor_function.return_value = mock_monitor_instance
        
        result = self.test_case.monitor_django_view("test_view")
        
        mock_monitor_function.assert_called_once_with("test_view")
        self.assertEqual(result, mock_monitor_instance)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_model')
    def test_monitor_django_model(self, mock_monitor_function) -> None:
        """Test monitor_django_model method."""
        mock_monitor_instance = Mock()
        mock_monitor_function.return_value = mock_monitor_instance
        
        result = self.test_case.monitor_django_model("test_model")
        
        mock_monitor_function.assert_called_once_with("test_model")
        self.assertEqual(result, mock_monitor_instance)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_serializer')
    def test_monitor_serializer(self, mock_monitor_function) -> None:
        """Test monitor_serializer method."""
        mock_monitor_instance = Mock()
        mock_monitor_function.return_value = mock_monitor_instance
        
        result = self.test_case.monitor_serializer("test_serializer")
        
        mock_monitor_function.assert_called_once_with("test_serializer")
        self.assertEqual(result, mock_monitor_instance)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_measure_django_view_get(self, mock_monitor_function) -> None:
        """Test measure_django_view with GET request."""
        # Setup mock monitor and client
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor_function.return_value = mock_monitor
        
        # Mock client
        mock_response = Mock()
        self.test_case.client = Mock()
        self.test_case.client.get = Mock(return_value=mock_response)
        
        result = self.test_case.measure_django_view('/api/users/', 'GET')
        
        # Verify the monitor was created and used correctly
        mock_monitor_function.assert_called_once_with('GET /api/users/')
        self.test_case.client.get.assert_called_once_with('/api/users/')
        self.assertEqual(result, self.mock_metrics)
        self.assertEqual(self.mock_metrics._response, mock_response)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_measure_django_view_post_with_data(self, mock_monitor_function) -> None:
        """Test measure_django_view with POST request and data."""
        # Setup mock monitor
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor_function.return_value = mock_monitor
        
        # Mock client
        mock_response = Mock()
        self.test_case.client = Mock()
        self.test_case.client.post = Mock(return_value=mock_response)
        
        test_data = {'name': 'Test User'}
        result = self.test_case.measure_django_view(
            '/api/users/', 'POST', data=test_data, format='json'
        )
        
        # Verify the monitor was created and used correctly
        mock_monitor_function.assert_called_once_with('POST /api/users/')
        self.test_case.client.post.assert_called_once_with(
            '/api/users/', data=test_data, format='json'
        )
        self.assertEqual(result, self.mock_metrics)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_measure_django_view_custom_operation_name(self, mock_monitor_function) -> None:
        """Test measure_django_view with custom operation name."""
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor_function.return_value = mock_monitor
        
        self.test_case.client = Mock()
        self.test_case.client.get = Mock(return_value=Mock())
        
        result = self.test_case.measure_django_view(
            '/api/users/', operation_name='Custom User List'
        )
        
        mock_monitor_function.assert_called_once_with('Custom User List')
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_run_comprehensive_analysis_basic(self, mock_logger, mock_monitor_function) -> None:
        """Test run_comprehensive_analysis with basic parameters."""
        # Setup mock monitor
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor.expect_response_under = Mock()
        mock_monitor.expect_memory_under = Mock()
        mock_monitor.expect_queries_under = Mock()
        mock_monitor.expect_cache_hit_ratio_above = Mock()
        mock_monitor.set_test_context = Mock()
        mock_monitor.enable_educational_guidance = Mock()
        mock_monitor_function.return_value = mock_monitor
        
        # Mock test function
        test_result = "test_result"
        test_function = Mock(return_value=test_result)
        
        # Mock metrics methods
        self.mock_metrics.get_performance_report_with_scoring = Mock(return_value="Performance report")
        self.mock_metrics.detailed_report = Mock(return_value="Detailed report")
        
        result = self.test_case.run_comprehensive_analysis(
            "test_operation",
            test_function,
            expect_response_under=100.0,
            expect_memory_under=50.0,
            expect_queries_under=5,
            expect_cache_hit_ratio_above=0.8
        )
        
        # Verify monitor setup
        mock_monitor_function.assert_called_once_with("test_operation.comprehensive", operation_type="general")
        mock_monitor.expect_response_under.assert_called_once_with(100.0)
        mock_monitor.expect_memory_under.assert_called_once_with(50.0)
        mock_monitor.expect_queries_under.assert_called_once_with(5)
        mock_monitor.expect_cache_hit_ratio_above.assert_called_once_with(0.8)
        
        # Verify test function was called
        test_function.assert_called_once()
        
        # Verify result
        self.assertEqual(result, self.mock_metrics)
        self.assertEqual(self.mock_metrics._test_result, test_result)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_run_comprehensive_analysis_with_test_context(self, mock_logger, mock_monitor_function) -> None:
        """Test run_comprehensive_analysis with test context."""
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor.set_test_context = Mock()
        mock_monitor_function.return_value = mock_monitor
        
        test_function = Mock(return_value="result")
        self.mock_metrics.get_performance_report_with_scoring = Mock(return_value="report")
        
        self.test_case.run_comprehensive_analysis(
            "test_operation",
            test_function,
            test_file="/path/to/test.py",
            test_line=100,
            test_method="test_method"
        )
        
        mock_monitor.set_test_context.assert_called_once_with("/path/to/test.py", 100, "test_method")
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_run_comprehensive_analysis_with_educational_guidance(self, mock_logger, mock_monitor_function) -> None:
        """Test run_comprehensive_analysis with educational guidance enabled."""
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor.enable_educational_guidance = Mock()
        mock_monitor_function.return_value = mock_monitor
        
        test_function = Mock(return_value="result")
        self.mock_metrics.get_performance_report_with_scoring = Mock(return_value="report")
        
        operation_context = {"view_type": "list"}
        
        self.test_case.run_comprehensive_analysis(
            "test_operation",
            test_function,
            enable_educational_guidance=True,
            operation_context=operation_context
        )
        
        mock_monitor.enable_educational_guidance.assert_called_once_with(operation_context)
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    @patch('django_mercury.python_bindings.django_integration.logger')
    @patch('django_mercury.python_bindings.django_integration.colors')
    def test_run_comprehensive_analysis_n_plus_one_detection(self, mock_colors, mock_logger, mock_monitor_function) -> None:
        """Test run_comprehensive_analysis with N+1 detection."""
        # Setup N+1 detection
        mock_n_plus_one_analysis = Mock()
        mock_n_plus_one_analysis.severity_level = 2
        mock_n_plus_one_analysis.severity_text = "Medium"
        mock_n_plus_one_analysis.query_count = 15
        mock_n_plus_one_analysis.cause_text = "Missing select_related"
        mock_n_plus_one_analysis.fix_suggestion = "Use select_related('profile')"
        
        self.mock_django_issues.has_n_plus_one = True
        self.mock_django_issues.n_plus_one_analysis = mock_n_plus_one_analysis
        
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor_function.return_value = mock_monitor
        
        test_function = Mock(return_value="result")
        self.mock_metrics.get_performance_report_with_scoring = Mock(return_value="report")
        mock_colors.colorize = Mock(return_value="colored text")
        
        self.test_case.run_comprehensive_analysis(
            "test_operation",
            test_function,
            auto_detect_n_plus_one=True
        )
        
        # Verify N+1 detection logging
        mock_logger.warning.assert_called_once()
        self.assertIn("N+1 query pattern detected", mock_logger.warning.call_args[0][0])
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_run_comprehensive_analysis_no_print(self, mock_monitor_function) -> None:
        """Test run_comprehensive_analysis with print_analysis=False."""
        mock_monitor = Mock()
        mock_monitor.__enter__ = Mock(return_value=mock_monitor)
        mock_monitor.__exit__ = Mock(return_value=None)
        mock_monitor.metrics = self.mock_metrics
        mock_monitor_function.return_value = mock_monitor
        
        test_function = Mock(return_value="result")
        
        with patch('builtins.print') as mock_print:
            self.test_case.run_comprehensive_analysis(
                "test_operation",
                test_function,
                print_analysis=False
            )
            
            # Should not print anything
            mock_print.assert_not_called()
    
    def test_create_enhanced_performance_dashboard_with_scoring(self) -> None:
        """Test create_enhanced_performance_dashboard_with_scoring."""
        self.mock_metrics.get_performance_report_with_scoring = Mock(return_value="Scoring report")
        
        with patch('builtins.print') as mock_print:
            self.test_case.create_enhanced_performance_dashboard_with_scoring(
                self.mock_metrics, "Test Dashboard"
            )
            
            mock_print.assert_called_once_with("Scoring report")
    
    @patch('django_mercury.python_bindings.django_integration.colors')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_create_enhanced_dashboard_basic(self, mock_logger, mock_colors) -> None:
        """Test create_enhanced_dashboard with basic metrics."""
        # Mock colors methods
        mock_colors.colorize = Mock(return_value="colored text")
        mock_colors.format_performance_status = Mock(return_value="fast")
        mock_colors.format_metric_value = Mock(side_effect=lambda val, unit: f"{val}{unit}")
        
        with patch('builtins.print') as mock_print:
            self.test_case.create_enhanced_dashboard(self.mock_metrics, "Test Dashboard")
            
            # Verify print was called multiple times for dashboard
            self.assertGreater(mock_print.call_count, 5)
            
            # Verify dashboard content
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            dashboard_content = " ".join(print_calls)
            
            # Should contain key dashboard elements
            self.assertIn("colored text", dashboard_content)  # Title and borders
    
    @patch('django_mercury.python_bindings.django_integration.colors')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_create_enhanced_dashboard_with_response_data(self, mock_logger, mock_colors) -> None:
        """Test create_enhanced_dashboard with response data."""
        # Add test result with response data
        mock_test_result = Mock()
        mock_test_result.data = {"users": ["user1", "user2"], "count": 2}
        self.mock_metrics._test_result = mock_test_result
        
        mock_colors.colorize = Mock(return_value="colored text")
        mock_colors.format_performance_status = Mock(return_value="fast")
        mock_colors.format_metric_value = Mock(side_effect=lambda val, unit: f"{val}{unit}")
        
        with patch('builtins.print') as mock_print:
            self.test_case.create_enhanced_dashboard(self.mock_metrics)
            
            # Verify dashboard was printed
            self.assertGreater(mock_print.call_count, 0)
    
    @patch('django_mercury.python_bindings.django_integration.colors')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_create_enhanced_dashboard_with_django_issues(self, mock_logger, mock_colors) -> None:
        """Test create_enhanced_dashboard with Django issues."""
        # Setup Django issues
        self.mock_django_issues.has_issues = True
        self.mock_django_issues.get_issue_summary.return_value = [
            "N+1 query detected in user profiles",
            "Slow query in user search"
        ]
        
        mock_colors.colorize = Mock(return_value="colored text")
        mock_colors.format_performance_status = Mock(return_value="slow")
        mock_colors.format_metric_value = Mock(side_effect=lambda val, unit: f"{val}{unit}")
        
        with patch('builtins.print') as mock_print:
            self.test_case.create_enhanced_dashboard(self.mock_metrics)
            
            # Verify Django issues section was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            dashboard_content = " ".join(print_calls)
            
            # Should contain Django issues
            self.assertIn("colored text", dashboard_content)  # Issues would be colored
    
    @patch('django_mercury.python_bindings.django_integration.colors')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_create_enhanced_dashboard_response_size_calculation(self, mock_logger, mock_colors) -> None:
        """Test create_enhanced_dashboard response size calculation."""
        # Test with large response (>1KB)
        large_data = {"data": "x" * 2000}  # More than 1KB
        mock_test_result = Mock()
        mock_test_result.data = large_data
        self.mock_metrics._test_result = mock_test_result
        
        mock_colors.colorize = Mock(return_value="colored text")
        mock_colors.format_performance_status = Mock(return_value="fast")
        mock_colors.format_metric_value = Mock(side_effect=lambda val, unit: f"{val}{unit}")
        
        with patch('builtins.print') as mock_print:
            self.test_case.create_enhanced_dashboard(self.mock_metrics)
            
            # Should calculate size correctly
            self.assertGreater(mock_print.call_count, 0)
    
    @patch('django_mercury.python_bindings.django_integration.colors')
    @patch('django_mercury.python_bindings.django_integration.logger')
    def test_create_enhanced_dashboard_exception_handling(self, mock_logger, mock_colors) -> None:
        """Test create_enhanced_dashboard handles exceptions in response processing."""
        # Setup test result that will cause exception
        mock_test_result = Mock()
        mock_test_result.data = Mock(side_effect=Exception("JSON error"))
        self.mock_metrics._test_result = mock_test_result
        
        mock_colors.colorize = Mock(return_value="colored text")
        mock_colors.format_performance_status = Mock(return_value="fast")
        mock_colors.format_metric_value = Mock(side_effect=lambda val, unit: f"{val}{unit}")
        
        # Should not raise exception
        with patch('builtins.print') as mock_print:
            self.test_case.create_enhanced_dashboard(self.mock_metrics)
            
            # Should still print dashboard
            self.assertGreater(mock_print.call_count, 0)


class TestAssertionEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for assertion methods."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_case = DjangoPerformanceAPITestCase()
    
    def test_assertion_with_equal_values(self) -> None:
        """Test assertions when values are exactly equal to thresholds."""
        mock_metrics = Mock()
        mock_metrics.response_time = 100.0  # Exactly equal to threshold
        mock_metrics.memory_usage = 20.0    # Exactly equal to threshold
        mock_metrics.query_count = 5        # Exactly equal to threshold
        
        mock_monitor = Mock()
        mock_monitor.metrics = mock_metrics
        
        # Should fail when value equals threshold (not less than)
        with self.assertRaises(AssertionError):
            self.test_case.assertResponseTimeLess(mock_monitor, 100.0)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertMemoryLess(mock_monitor, 20.0)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertQueriesLess(mock_monitor, 5)
    
    def test_assertion_with_none_values(self) -> None:
        """Test assertions with None values in metrics."""
        mock_metrics = Mock()
        mock_metrics.response_time = None
        mock_metrics.memory_usage = None
        mock_metrics.cache_hit_ratio = None
        
        mock_monitor = Mock()
        mock_monitor.metrics = mock_metrics
        
        # Should handle None values gracefully (might raise TypeError)
        with self.assertRaises((AssertionError, TypeError)):
            self.test_case.assertResponseTimeLess(mock_monitor, 100.0)
    
    def test_assertion_with_negative_values(self) -> None:
        """Test assertions with negative values."""
        mock_metrics = Mock()
        mock_metrics.response_time = -10.0
        mock_metrics.memory_usage = -5.0
        
        mock_monitor = Mock()
        mock_monitor.metrics = mock_metrics
        
        # Negative values should pass "less than" assertions
        self.test_case.assertResponseTimeLess(mock_monitor, 100.0)
        self.test_case.assertMemoryLess(mock_monitor, 20.0)
    
    def test_assertion_with_zero_values(self) -> None:
        """Test assertions with zero values."""
        mock_metrics = Mock()
        mock_metrics.response_time = 0.0
        mock_metrics.memory_usage = 0.0
        mock_metrics.query_count = 0
        mock_metrics.cache_hit_ratio = 0.0
        
        mock_monitor = Mock()
        mock_monitor.metrics = mock_metrics
        
        # Zero values should pass appropriate assertions
        self.test_case.assertResponseTimeLess(mock_monitor, 100.0)
        self.test_case.assertMemoryLess(mock_monitor, 20.0)
        self.test_case.assertQueriesLess(mock_monitor, 5)
        
        # Zero cache hit ratio should fail good cache performance
        with self.assertRaises(AssertionError):
            self.test_case.assertGoodCachePerformance(mock_monitor, min_hit_ratio=0.5)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios combining multiple features."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_case = DjangoPerformanceAPITestCase()
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_full_workflow_scenario(self, mock_monitor_function) -> None:
        """Test a complete workflow scenario with multiple assertions."""
        # Setup mock monitor and metrics
        mock_metrics = Mock()
        mock_metrics.response_time = 75.0
        mock_metrics.memory_usage = 15.0
        mock_metrics.query_count = 3
        mock_metrics.cache_hit_ratio = 0.85
        mock_metrics.is_fast = True
        mock_metrics.is_slow = False
        mock_metrics.is_memory_intensive = False
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = False
        mock_django_issues.has_issues = False
        mock_metrics.django_issues = mock_django_issues
        
        mock_monitor = Mock()
        mock_monitor.metrics = mock_metrics
        mock_monitor.assert_performance = Mock()
        mock_monitor_function.return_value = mock_monitor
        
        # Test monitor creation
        monitor = self.test_case.monitor_django_view("test_view")
        self.assertEqual(monitor, mock_monitor)
        
        # Test multiple assertions (should all pass)
        self.test_case.assertResponseTimeLess(monitor, 100.0)
        self.test_case.assertMemoryLess(monitor, 20.0)
        self.test_case.assertQueriesLess(monitor, 5)
        self.test_case.assertPerformanceFast(monitor)
        self.test_case.assertPerformanceNotSlow(monitor)
        self.test_case.assertMemoryEfficient(monitor)
        self.test_case.assertNoNPlusOne(monitor)
        self.test_case.assertGoodCachePerformance(monitor, min_hit_ratio=0.8)
        
        # Test comprehensive performance assertion
        self.test_case.assertPerformance(
            monitor,
            max_response_time=100.0,
            max_memory_mb=20.0,
            max_queries=5,
            min_cache_hit_ratio=0.8
        )
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_performance_failure_scenario(self, mock_monitor_function) -> None:
        """Test scenario where performance metrics fail various assertions."""
        # Setup mock monitor with poor performance
        mock_metrics = Mock()
        mock_metrics.response_time = 750.0  # Slow
        mock_metrics.memory_usage = 128.0   # High memory
        mock_metrics.query_count = 25       # Many queries
        mock_metrics.cache_hit_ratio = 0.3  # Poor cache
        mock_metrics.is_fast = False
        mock_metrics.is_slow = True
        mock_metrics.is_memory_intensive = True
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = True
        mock_metrics.django_issues = mock_django_issues
        
        mock_monitor = Mock()
        mock_monitor.metrics = mock_metrics
        mock_monitor_function.return_value = mock_monitor
        
        monitor = self.test_case.monitor_django_view("slow_view")
        
        # All these assertions should fail
        with self.assertRaises(AssertionError):
            self.test_case.assertResponseTimeLess(monitor, 100.0)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertMemoryLess(monitor, 50.0)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertQueriesLess(monitor, 10)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertPerformanceFast(monitor)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertPerformanceNotSlow(monitor)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertMemoryEfficient(monitor)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertNoNPlusOne(monitor)
        
        with self.assertRaises(AssertionError):
            self.test_case.assertGoodCachePerformance(monitor, min_hit_ratio=0.7)


if __name__ == '__main__':
    unittest.main()