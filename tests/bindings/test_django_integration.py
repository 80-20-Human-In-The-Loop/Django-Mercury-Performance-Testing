"""
Tests for Django integration modules - django_integration.py and django_integration_mercury.py

This module tests the Django test case classes that provide performance monitoring
capabilities for Django REST Framework applications.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, create_autospec
import os
import sys
from typing import Dict, Any, Tuple
from dataclasses import dataclass

# Set environment to disable logging config issues
os.environ['MERCURY_DISABLE_LOGGING'] = '1'

# First, ensure Django is configured (test_runner.py should do this, but just in case)
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY="test-secret-key",
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "rest_framework",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
        django.setup()
except ImportError:
    # If Django is not available, mock it
    sys.modules['django'] = MagicMock()
    sys.modules['django.test'] = MagicMock()
    sys.modules['django.conf'] = MagicMock()
    sys.modules['rest_framework'] = MagicMock()
    sys.modules['rest_framework.test'] = MagicMock()
    sys.modules['rest_framework.response'] = MagicMock()

# Now import our modules
try:
    from django_mercury.python_bindings.django_integration import DjangoPerformanceAPITestCase
    from django_mercury.python_bindings.django_integration_mercury import (
        DjangoMercuryAPITestCase,
        OperationProfile,
        PerformanceBaseline,
        TestExecutionSummary,
        MercuryThresholdOverride
    )
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    # If imports fail, we'll skip these tests
    IMPORTS_SUCCESSFUL = False
    DjangoPerformanceAPITestCase = None
    DjangoMercuryAPITestCase = None
    OperationProfile = None
    PerformanceBaseline = None


@unittest.skipUnless(IMPORTS_SUCCESSFUL, "Django integration modules could not be imported")
class TestDjangoPerformanceAPITestCase(unittest.TestCase):
    """Test the DjangoPerformanceAPITestCase class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock monitor with properly configured metrics
        self.mock_monitor = Mock()
        
        # Create a mock metrics object with actual values
        mock_metrics = Mock()
        mock_metrics.response_time_ms = 100.0
        mock_metrics.response_time = 100.0  # Some methods use this
        mock_metrics.memory_usage_mb = 50.0
        mock_metrics.memory_usage = 50.0  # Some methods use this
        mock_metrics.query_count = 10
        mock_metrics.cache_hits = 8
        mock_metrics.cache_misses = 2
        mock_metrics.n_plus_one_detected = False
        mock_metrics.is_fast = True
        mock_metrics.is_slow = False
        
        # Set the metrics on the monitor
        self.mock_monitor.metrics = mock_metrics
        
        # Add assert_performance method to monitor (used internally)
        self.mock_monitor.assert_performance = Mock()
    
    def test_assert_performance_with_mock_test_case(self):
        """Test assertPerformance logic without instantiating the class."""
        # Create a mock instance
        test_instance = Mock(spec=DjangoPerformanceAPITestCase)
        test_instance.fail = Mock()
        
        # Call the actual method directly
        DjangoPerformanceAPITestCase.assertPerformance(
            test_instance,
            self.mock_monitor,
            max_response_time=200.0,
            max_memory_mb=100.0,
            max_queries=20,
            min_cache_hit_ratio=0.5
        )
        
        # Should not fail when thresholds are met
        test_instance.fail.assert_not_called()
    
    def test_assert_performance_fails_on_high_response_time(self):
        """Test assertPerformance fails when response time is too high."""
        test_instance = Mock(spec=DjangoPerformanceAPITestCase)
        test_instance.fail = Mock()
        
        # Set high response time
        self.mock_monitor.metrics.response_time_ms = 300.0
        
        # The assertPerformance method calls monitor.assert_performance internally
        # Make it raise an exception to trigger the fail path
        self.mock_monitor.assert_performance.side_effect = AssertionError("Performance threshold exceeded")
        
        # This should catch the exception and call fail
        try:
            DjangoPerformanceAPITestCase.assertPerformance(
                test_instance,
                self.mock_monitor,
                max_response_time=200.0
            )
        except AssertionError:
            pass  # Expected
        
        # Check that assert_performance was called with the right thresholds
        self.mock_monitor.assert_performance.assert_called_once()
    
    def test_assert_response_time_less(self):
        """Test assertResponseTimeLess method."""
        test_instance = Mock(spec=DjangoPerformanceAPITestCase)
        test_instance.fail = Mock()
        
        # Should pass with threshold > actual
        DjangoPerformanceAPITestCase.assertResponseTimeLess(
            test_instance,
            self.mock_monitor,
            200.0
        )
        test_instance.fail.assert_not_called()
        
        # Should fail with threshold < actual
        DjangoPerformanceAPITestCase.assertResponseTimeLess(
            test_instance,
            self.mock_monitor,
            50.0
        )
        test_instance.fail.assert_called()
    
    def test_assert_memory_less(self):
        """Test assertMemoryLess method."""
        test_instance = Mock(spec=DjangoPerformanceAPITestCase)
        test_instance.fail = Mock()
        
        # Should pass
        DjangoPerformanceAPITestCase.assertMemoryLess(
            test_instance,
            self.mock_monitor,
            100.0
        )
        test_instance.fail.assert_not_called()
        
        # Should fail
        DjangoPerformanceAPITestCase.assertMemoryLess(
            test_instance,
            self.mock_monitor,
            25.0
        )
        test_instance.fail.assert_called()
    
    def test_assert_queries_less(self):
        """Test assertQueriesLess method."""
        test_instance = Mock(spec=DjangoPerformanceAPITestCase)
        test_instance.fail = Mock()
        
        # Should pass
        DjangoPerformanceAPITestCase.assertQueriesLess(
            test_instance,
            self.mock_monitor,
            20
        )
        test_instance.fail.assert_not_called()
        
        # Should fail
        DjangoPerformanceAPITestCase.assertQueriesLess(
            test_instance,
            self.mock_monitor,
            5
        )
        test_instance.fail.assert_called()
    
    @patch('django_mercury.python_bindings.django_integration.monitor_django_view')
    def test_monitor_context_managers(self, mock_monitor_func):
        """Test that monitor methods return proper context managers."""
        test_instance = Mock(spec=DjangoPerformanceAPITestCase)
        mock_context = Mock()
        mock_monitor_func.return_value = mock_context
        
        result = DjangoPerformanceAPITestCase.monitor_django_view(
            test_instance,
            "test_operation"
        )
        
        mock_monitor_func.assert_called_once_with("test_operation")
        self.assertEqual(result, mock_context)


@unittest.skipUnless(IMPORTS_SUCCESSFUL, "Django integration modules could not be imported")
class TestDjangoMercuryAPITestCase(unittest.TestCase):
    """Test the DjangoMercuryAPITestCase class."""
    
    def test_operation_profile_initialization(self):
        """Test OperationProfile class initialization with correct signature."""
        profile = OperationProfile(
            operation_name="list_view",
            expected_query_range=(5, 20),
            response_time_baseline=100.0,
            memory_overhead_tolerance=50.0,
            complexity_factors={"pagination": True}
        )
        
        self.assertEqual(profile.operation_name, "list_view")
        self.assertEqual(profile.expected_query_range, (5, 20))
        self.assertEqual(profile.response_time_baseline, 100.0)
        self.assertEqual(profile.memory_overhead_tolerance, 50.0)
        self.assertEqual(profile.complexity_factors, {"pagination": True})
    
    def test_operation_profile_calculate_thresholds(self):
        """Test OperationProfile.calculate_dynamic_thresholds method."""
        profile = OperationProfile(
            operation_name="list_view",
            expected_query_range=(5, 20),
            response_time_baseline=100.0,
            memory_overhead_tolerance=50.0,
            complexity_factors={}
        )
        
        # Test with context
        context = {"pagination": {"page_size": 20}}
        thresholds = profile.calculate_dynamic_thresholds(context)
        
        self.assertIsInstance(thresholds, dict)
        # The actual implementation returns these keys
        self.assertIn("response_time", thresholds)
        self.assertIn("memory_usage", thresholds)
        self.assertIn("query_count", thresholds)
    
    def test_performance_baseline_initialization(self):
        """Test PerformanceBaseline with correct signature."""
        baseline = PerformanceBaseline(
            operation_type="list_view",
            avg_response_time=100.0,
            avg_memory_usage=50.0,
            avg_query_count=10.0,
            sample_count=5,
            last_updated="2024-01-01"
        )
        
        self.assertEqual(baseline.operation_type, "list_view")
        self.assertEqual(baseline.avg_response_time, 100.0)
        self.assertEqual(baseline.avg_memory_usage, 50.0)
        self.assertEqual(baseline.avg_query_count, 10.0)
        self.assertEqual(baseline.sample_count, 5)
        self.assertEqual(baseline.last_updated, "2024-01-01")
    
    def test_performance_baseline_update(self):
        """Test PerformanceBaseline.update_with_new_measurement."""
        baseline = PerformanceBaseline(
            operation_type="list_view",
            avg_response_time=100.0,
            avg_memory_usage=50.0,
            avg_query_count=10.0,
            sample_count=1,
            last_updated="2024-01-01"
        )
        
        # Create a mock metrics with actual float values
        # The implementation expects metrics.response_time, not response_time_ms
        metrics = Mock()
        metrics.response_time = 200.0  # Changed from response_time_ms
        metrics.memory_usage = 60.0   # Changed from memory_usage_mb
        metrics.query_count = 20
        
        # Update baseline
        baseline.update_with_new_measurement(metrics)
        
        # Check averages were updated (using exponential moving average)
        self.assertEqual(baseline.sample_count, 2)
        # The implementation uses 0.9 * old + 0.1 * new
        expected_response = 0.9 * 100.0 + 0.1 * 200.0
        self.assertAlmostEqual(baseline.avg_response_time, expected_response, places=1)
        expected_memory = 0.9 * 50.0 + 0.1 * 60.0
        self.assertAlmostEqual(baseline.avg_memory_usage, expected_memory, places=1)
        expected_queries = 0.9 * 10.0 + 0.1 * 20.0
        self.assertAlmostEqual(baseline.avg_query_count, expected_queries, places=1)
    
    def test_calculate_overall_grade_static_method(self):
        """Test _calculate_overall_grade static method."""
        # Test S grade (>= 95)
        grade = DjangoMercuryAPITestCase._calculate_overall_grade(95.0)
        self.assertEqual(grade, "S")
        
        # Test A+ grade (>= 90)
        grade = DjangoMercuryAPITestCase._calculate_overall_grade(92.0)
        self.assertEqual(grade, "A+")
        
        # Test A grade (>= 85)
        grade = DjangoMercuryAPITestCase._calculate_overall_grade(87.0)
        self.assertEqual(grade, "A")
        
        # Test B grade (>= 75)
        grade = DjangoMercuryAPITestCase._calculate_overall_grade(78.0)
        self.assertEqual(grade, "B")
        
        # Test C grade (>= 65)
        grade = DjangoMercuryAPITestCase._calculate_overall_grade(68.0)
        self.assertEqual(grade, "C")
        
        # Test D grade (>= 50)
        grade = DjangoMercuryAPITestCase._calculate_overall_grade(55.0)
        self.assertEqual(grade, "D")
        
        # Test F grade (< 50)
        grade = DjangoMercuryAPITestCase._calculate_overall_grade(45.0)
        self.assertEqual(grade, "F")
    
    def test_detect_operation_type(self):
        """Test _detect_operation_type method."""
        # Create a mock instance
        test_instance = Mock(spec=DjangoMercuryAPITestCase)
        
        # Test function mock
        test_func = Mock()
        test_func.__name__ = "test_user_list"
        test_func.__doc__ = ""
        
        # Test list view detection
        op_type = DjangoMercuryAPITestCase._detect_operation_type(
            test_instance,
            "test_user_list",
            test_func
        )
        self.assertEqual(op_type, "list_view")
        
        # Test detail view detection
        test_func.__name__ = "test_user_detail"
        op_type = DjangoMercuryAPITestCase._detect_operation_type(
            test_instance,
            "test_user_detail",
            test_func
        )
        self.assertEqual(op_type, "detail_view")
        
        # Test create view detection
        test_func.__name__ = "test_create_user"
        op_type = DjangoMercuryAPITestCase._detect_operation_type(
            test_instance,
            "test_create_user",
            test_func
        )
        self.assertEqual(op_type, "create_view")
    
    def test_set_performance_thresholds_class_method(self):
        """Test set_performance_thresholds class method."""
        # Save original value
        original = getattr(DjangoMercuryAPITestCase, '_custom_thresholds', {})
        
        try:
            thresholds = {
                "response_time_ms": 100,
                "memory_overhead_mb": 50,
                "query_count_max": 10
            }
            
            # The set_performance_thresholds method exists on DjangoMercuryAPITestCase
            DjangoMercuryAPITestCase.set_performance_thresholds(thresholds)
            self.assertEqual(DjangoMercuryAPITestCase._custom_thresholds, thresholds)
        finally:
            # Restore original value
            DjangoMercuryAPITestCase._custom_thresholds = original
    
    def test_configure_mercury_class_method(self):
        """Test configure_mercury class method."""
        # Save original values
        original_enabled = DjangoMercuryAPITestCase._mercury_enabled
        original_scoring = DjangoMercuryAPITestCase._auto_scoring
        
        try:
            # Test enabling Mercury
            DjangoMercuryAPITestCase.configure_mercury(
                enabled=True,
                auto_scoring=False
            )
            
            self.assertTrue(DjangoMercuryAPITestCase._mercury_enabled)
            self.assertFalse(DjangoMercuryAPITestCase._auto_scoring)
            
            # Test disabling Mercury
            DjangoMercuryAPITestCase.configure_mercury(enabled=False)
            self.assertFalse(DjangoMercuryAPITestCase._mercury_enabled)
        finally:
            # Restore original values
            DjangoMercuryAPITestCase._mercury_enabled = original_enabled
            DjangoMercuryAPITestCase._auto_scoring = original_scoring
    
    def test_mercury_threshold_override(self):
        """Test MercuryThresholdOverride context manager."""
        # Create a mock test instance
        test_instance = Mock()
        test_instance._per_test_thresholds = {"response_time_ms": 100}
        
        # Create override
        override = MercuryThresholdOverride(test_instance)
        
        # Test the callable functionality - it just stores the thresholds
        new_thresholds = {"response_time_ms": 200}
        result = override(new_thresholds)
        # Calling the override returns self and stores thresholds internally
        self.assertEqual(result, override)
        self.assertEqual(override.override_thresholds, new_thresholds)
        
        # Test context manager - it applies and restores thresholds
        test_instance._per_test_thresholds = {"response_time_ms": 100}
        with override:
            # __enter__ should have applied the override thresholds
            self.assertEqual(test_instance._per_test_thresholds, new_thresholds)
        
        # __exit__ should have restored the original thresholds
        self.assertEqual(test_instance._per_test_thresholds, {"response_time_ms": 100})


class TestDjangoIntegrationHelpers(unittest.TestCase):
    """Test helper classes and functions."""
    
    @unittest.skipUnless(IMPORTS_SUCCESSFUL, "Django integration modules could not be imported")
    def test_test_execution_summary(self):
        """Test TestExecutionSummary dataclass."""
        summary = TestExecutionSummary(
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            average_score=85.5,
            grade_distribution={"A": 5, "B": 3, "C": 2},
            critical_issues=["N+1 queries detected"],
            optimization_opportunities=["Use select_related"],
            performance_trends={"response_time": "improving"},
            execution_time=1.5,
            recommendations=["Use prefetch_related", "Add database indexes"]
        )
        
        self.assertEqual(summary.total_tests, 10)
        self.assertEqual(summary.passed_tests, 8)
        self.assertEqual(summary.failed_tests, 2)
        self.assertEqual(summary.average_score, 85.5)
        self.assertEqual(summary.grade_distribution["A"], 5)
        self.assertEqual(summary.execution_time, 1.5)
        self.assertIn("Use prefetch_related", summary.recommendations)


if __name__ == "__main__":
    unittest.main()