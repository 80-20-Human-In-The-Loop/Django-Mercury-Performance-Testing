"""
Test suite for Django Mercury integration module.

This module tests the intelligent Django Mercury API Test Case framework
including performance baselines, operation profiles,
and the main Mercury test case functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call, mock_open
import tempfile
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from django_mercury.python_bindings.django_integration_mercury import (
    PerformanceBaseline,
    OperationProfile,
    TestExecutionSummary,
    MercuryThresholdOverride,
    DjangoMercuryAPITestCase
)
from django_mercury.python_bindings.monitor import EnhancedPerformanceMetrics_Python


class TestPerformanceBaseline(unittest.TestCase):
    """Test PerformanceBaseline dataclass functionality."""
    
    def test_performance_baseline_creation(self):
        """Test creating a PerformanceBaseline instance."""
        baseline = PerformanceBaseline(
            operation_type="list_view",
            avg_response_time=120.5,
            avg_memory_usage=25.0,
            avg_query_count=5.0,
            sample_count=10,
            last_updated="2023-01-01T00:00:00"
        )
        
        self.assertEqual(baseline.operation_type, "list_view")
        self.assertEqual(baseline.avg_response_time, 120.5)
        self.assertEqual(baseline.avg_memory_usage, 25.0)
        self.assertEqual(baseline.avg_query_count, 5.0)
        self.assertEqual(baseline.sample_count, 10)
        self.assertEqual(baseline.last_updated, "2023-01-01T00:00:00")
    
    def test_update_with_new_measurement(self):
        """Test updating baseline with new measurement."""
        baseline = PerformanceBaseline(
            operation_type="list_view",
            avg_response_time=100.0,
            avg_memory_usage=20.0,
            avg_query_count=4.0,
            sample_count=5,
            last_updated="2023-01-01T00:00:00"
        )
        
        # Mock metrics
        mock_metrics = Mock()
        mock_metrics.response_time = 200.0
        mock_metrics.memory_usage = 30.0
        mock_metrics.query_count = 6.0
        
        baseline.update_with_new_measurement(mock_metrics)
        
        # Should use weighted average with 10% weight for new measurement
        expected_response_time = 0.9 * 100.0 + 0.1 * 200.0  # 110.0
        expected_memory_usage = 0.9 * 20.0 + 0.1 * 30.0     # 21.0
        expected_query_count = 0.9 * 4.0 + 0.1 * 6.0        # 4.2
        
        self.assertAlmostEqual(baseline.avg_response_time, expected_response_time, places=2)
        self.assertAlmostEqual(baseline.avg_memory_usage, expected_memory_usage, places=2)
        self.assertAlmostEqual(baseline.avg_query_count, expected_query_count, places=2)
        self.assertEqual(baseline.sample_count, 6)
        # Updated timestamp will be current time, so just check it's a string
        self.assertIsInstance(baseline.last_updated, str)


class TestOperationProfile(unittest.TestCase):
    """Test OperationProfile dataclass functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profile = OperationProfile(
            operation_name="list_view",
            expected_query_range=(3, 25),
            response_time_baseline=200.0,
            memory_overhead_tolerance=30.0,
            complexity_factors={'pagination': True, 'serialization': 'moderate'}
        )
    
    def test_operation_profile_creation(self):
        """Test creating an OperationProfile instance."""
        self.assertEqual(self.profile.operation_name, "list_view")
        self.assertEqual(self.profile.expected_query_range, (3, 25))
        self.assertEqual(self.profile.response_time_baseline, 200.0)
        self.assertEqual(self.profile.memory_overhead_tolerance, 30.0)
        self.assertEqual(self.profile.complexity_factors, {'pagination': True, 'serialization': 'moderate'})
    
    def test_calculate_dynamic_thresholds_basic(self):
        """Test calculating basic dynamic thresholds without context."""
        thresholds = self.profile.calculate_dynamic_thresholds({})
        
        expected = {
            'response_time': 200.0,
            'memory_usage': 110.0,  # 80 + 30
            'query_count': 25,
        }
        
        self.assertEqual(thresholds, expected)
    
    def test_calculate_dynamic_thresholds_with_page_size(self):
        """Test calculating thresholds with page size context."""
        context = {'page_size': 50}
        thresholds = self.profile.calculate_dynamic_thresholds(context)
        
        # Response time should be scaled by (1 + 50/100) = 1.5
        expected_response_time = 200.0 * 1.5  # 300.0
        expected_memory_usage = 110.0 + 50 * 0.5  # 135.0
        
        self.assertEqual(thresholds['response_time'], expected_response_time)
        self.assertEqual(thresholds['memory_usage'], expected_memory_usage)
        self.assertEqual(thresholds['query_count'], 25)
    
    def test_calculate_dynamic_thresholds_with_relations(self):
        """Test calculating thresholds with include_relations context."""
        context = {'include_relations': True}
        thresholds = self.profile.calculate_dynamic_thresholds(context)
        
        expected_response_time = 200.0 * 1.5  # 300.0
        expected_query_count = 25 + 3         # 28
        expected_memory_usage = 110.0 + 10    # 120.0
        
        self.assertEqual(thresholds['response_time'], expected_response_time)
        self.assertEqual(thresholds['query_count'], expected_query_count)
        self.assertEqual(thresholds['memory_usage'], expected_memory_usage)
    
    def test_calculate_dynamic_thresholds_with_high_search_complexity(self):
        """Test calculating thresholds with high search complexity."""
        context = {'search_complexity': 'high'}
        thresholds = self.profile.calculate_dynamic_thresholds(context)
        
        expected_response_time = 200.0 * 2  # 400.0
        expected_query_count = 25 + 2       # 27
        
        self.assertEqual(thresholds['response_time'], expected_response_time)
        self.assertEqual(thresholds['query_count'], expected_query_count)
    
    def test_calculate_dynamic_thresholds_combined_context(self):
        """Test calculating thresholds with multiple context factors."""
        context = {
            'page_size': 20,
            'include_relations': True,
            'search_complexity': 'high'
        }
        thresholds = self.profile.calculate_dynamic_thresholds(context)
        
        # Apply all adjustments
        expected_response_time = 200.0 * (1 + 20/100) * 1.5 * 2  # 720.0
        expected_query_count = 25 + 3 + 2                         # 30
        expected_memory_usage = 110.0 + 20 * 0.5 + 10            # 130.0
        
        self.assertEqual(thresholds['response_time'], expected_response_time)
        self.assertEqual(thresholds['query_count'], expected_query_count)
        self.assertEqual(thresholds['memory_usage'], expected_memory_usage)


class TestTestExecutionSummary(unittest.TestCase):
    """Test TestExecutionSummary dataclass functionality."""
    
    def test_test_execution_summary_creation(self):
        """Test creating a TestExecutionSummary instance."""
        summary = TestExecutionSummary(
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            average_score=85.5,
            grade_distribution={'A': 5, 'B': 3, 'C': 2},
            critical_issues=['N+1 queries in user list'],
            optimization_opportunities=['Add caching', 'Optimize queries'],
            performance_trends={'response_time': 'increasing'},
            execution_time=120.5,
            recommendations=['Use select_related', 'Add indexes']
        )
        
        self.assertEqual(summary.total_tests, 10)
        self.assertEqual(summary.passed_tests, 8)
        self.assertEqual(summary.failed_tests, 2)
        self.assertEqual(summary.average_score, 85.5)
        self.assertEqual(summary.grade_distribution, {'A': 5, 'B': 3, 'C': 2})
        self.assertEqual(summary.critical_issues, ['N+1 queries in user list'])
        self.assertEqual(summary.optimization_opportunities, ['Add caching', 'Optimize queries'])
        self.assertEqual(summary.performance_trends, {'response_time': 'increasing'})
        self.assertEqual(summary.execution_time, 120.5)
        self.assertEqual(summary.recommendations, ['Use select_related', 'Add indexes'])




class TestMercuryThresholdOverride(unittest.TestCase):
    """Test MercuryThresholdOverride context manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_test_instance = Mock()
        self.mock_test_instance._per_test_thresholds = {'original': 'threshold'}
        self.override = MercuryThresholdOverride(self.mock_test_instance)
    
    def test_threshold_override_call(self):
        """Test calling the threshold override with thresholds."""
        thresholds = {'response_time_ms': 1000, 'query_count_max': 50}
        result = self.override(thresholds)
        
        self.assertEqual(result, self.override)
        self.assertEqual(self.override.override_thresholds, thresholds)
    
    def test_context_manager_enter_exit(self):
        """Test context manager enter and exit functionality."""
        original_thresholds = {'original': 'threshold'}
        override_thresholds = {'response_time_ms': 1000}
        
        self.mock_test_instance._per_test_thresholds = original_thresholds
        self.override.override_thresholds = override_thresholds
        
        # Test enter
        with self.override as ctx:
            self.assertEqual(ctx, self.override)
            self.assertEqual(self.override.original_thresholds, original_thresholds)
            self.assertEqual(self.mock_test_instance._per_test_thresholds, override_thresholds)
        
        # Test exit (should restore original thresholds)
        self.assertEqual(self.mock_test_instance._per_test_thresholds, original_thresholds)
    
    def test_context_manager_with_exception(self):
        """Test context manager behavior when exception occurs."""
        original_thresholds = {'original': 'threshold'}
        override_thresholds = {'response_time_ms': 1000}
        
        self.mock_test_instance._per_test_thresholds = original_thresholds
        self.override.override_thresholds = override_thresholds
        
        try:
            with self.override:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should still restore original thresholds despite exception
        self.assertEqual(self.mock_test_instance._per_test_thresholds, original_thresholds)


class TestDjangoMercuryAPITestCase(unittest.TestCase):
    """Test DjangoMercuryAPITestCase functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_case = DjangoMercuryAPITestCase()
        
        # Reset class variables for clean testing
        DjangoMercuryAPITestCase._mercury_enabled = True
        DjangoMercuryAPITestCase._auto_scoring = True
        DjangoMercuryAPITestCase._auto_threshold_adjustment = True
        DjangoMercuryAPITestCase._generate_summaries = True
        DjangoMercuryAPITestCase._verbose_reporting = False
        DjangoMercuryAPITestCase._educational_guidance = True
        DjangoMercuryAPITestCase._summary_generated = False
        DjangoMercuryAPITestCase._custom_thresholds = None
        DjangoMercuryAPITestCase._test_executions = []
        DjangoMercuryAPITestCase._test_failures = []
        DjangoMercuryAPITestCase._optimization_recommendations = []
    
    def test_test_case_initialization(self):
        """Test DjangoMercuryAPITestCase initialization."""
        test_case = DjangoMercuryAPITestCase()
        
        self.assertIsInstance(test_case._operation_profiles, dict)
        self.assertIsInstance(test_case._test_context, dict)
        
        # Check operation profiles are initialized
        expected_profiles = ['list_view', 'detail_view', 'create_view', 'update_view', 'delete_view', 'search_view', 'authentication']
        for profile_name in expected_profiles:
            self.assertIn(profile_name, test_case._operation_profiles)
            self.assertIsInstance(test_case._operation_profiles[profile_name], OperationProfile)
    
    def test_configure_mercury(self):
        """Test configure_mercury class method."""
        DjangoMercuryAPITestCase.configure_mercury(
            enabled=False,
            auto_scoring=False,
            auto_threshold_adjustment=False,
            generate_summaries=False,
            verbose_reporting=True,
            educational_guidance=False
        )
        
        self.assertFalse(DjangoMercuryAPITestCase._mercury_enabled)
        self.assertFalse(DjangoMercuryAPITestCase._auto_scoring)
        self.assertFalse(DjangoMercuryAPITestCase._auto_threshold_adjustment)
        self.assertFalse(DjangoMercuryAPITestCase._generate_summaries)
        self.assertTrue(DjangoMercuryAPITestCase._verbose_reporting)
        self.assertFalse(DjangoMercuryAPITestCase._educational_guidance)
        
        # Check that tracking variables were reset
        self.assertEqual(DjangoMercuryAPITestCase._test_executions, [])
        self.assertEqual(DjangoMercuryAPITestCase._test_failures, [])
        self.assertEqual(DjangoMercuryAPITestCase._optimization_recommendations, [])
        self.assertFalse(DjangoMercuryAPITestCase._summary_generated)
    
    def test_detect_operation_type_method_name_patterns(self):
        """Test operation type detection from method names."""
        test_cases = [
            ('test_user_list', None, 'list_view'),
            ('test_user_detail', None, 'detail_view'),
            ('test_create_user', None, 'create_view'),
            ('test_update_user', None, 'update_view'),
            ('test_delete_user', None, 'delete_view'),
            ('test_search_users', None, 'search_view'),
            ('test_can_delete_user', None, 'delete_view'),  # Permission test with delete
            ('test_can_update_user', None, 'update_view'),  # Permission test with update
            ('test_unknown_pattern', None, 'detail_view'),  # Default fallback
        ]
        
        for method_name, test_function, expected_type in test_cases:
            with self.subTest(method_name=method_name):
                result = self.test_case._detect_operation_type(method_name, test_function)
                self.assertEqual(result, expected_type)
    
    def test_detect_operation_type_source_analysis(self):
        """Test operation type detection from function source code."""
        # Mock functions with different client method calls
        def mock_get_function():
            response = self.client.get('/api/users/')
            return response
        
        def mock_post_function():
            response = self.client.post('/api/users/', data={'name': 'test'})
            return response
        
        def mock_delete_function():
            response = self.client.delete('/api/users/1/')
            return response
        
        result_get = self.test_case._detect_operation_type('test_generic', mock_get_function)
        # The function sees '/api/users/' path and considers it a detail view due to the slash
        self.assertEqual(result_get, 'detail_view')
        
        result_post = self.test_case._detect_operation_type('test_generic', mock_post_function)
        self.assertEqual(result_post, 'create_view')
        
        result_delete = self.test_case._detect_operation_type('test_generic', mock_delete_function)
        self.assertEqual(result_delete, 'delete_view')
    
    def test_extract_test_context_basic(self):
        """Test extracting test context from function source."""
        def mock_function_with_pagination():
            response = self.client.get('/api/users/?page_size=50')
            return response
        
        context = self.test_case._extract_test_context(mock_function_with_pagination)
        self.assertEqual(context.get('page_size'), 50)
    
    def test_extract_test_context_relations(self):
        """Test extracting context for relations."""
        def mock_function_with_relations():
            # Test uses select_related
            queryset = User.objects.select_related('profile')
            return queryset
        
        context = self.test_case._extract_test_context(mock_function_with_relations)
        self.assertTrue(context.get('include_relations'))
    
    def test_extract_test_context_search_complexity(self):
        """Test extracting search complexity context."""
        def mock_function_with_complex_search():
            # Complex search with Q objects
            results = User.objects.filter(Q(name__icontains='test') | Q(email__in=['a@test.com']))
            return results
        
        context = self.test_case._extract_test_context(mock_function_with_complex_search)
        self.assertEqual(context.get('search_complexity'), 'high')
    
    def test_calculate_intelligent_thresholds_per_test_override(self):
        """Test threshold calculation with per-test overrides."""
        self.test_case._per_test_thresholds = {
            'response_time_ms': 1000,
            'memory_overhead_mb': 100,
            'query_count_max': 50
        }
        
        thresholds = self.test_case._calculate_intelligent_thresholds('list_view', {})
        
        expected = {
            'response_time': 1000,
            'memory_usage': 180,  # 80 + 100
            'query_count': 50
        }
        self.assertEqual(thresholds, expected)
    
    def test_calculate_intelligent_thresholds_custom_class_thresholds(self):
        """Test threshold calculation with custom class thresholds."""
        self.test_case._per_test_thresholds = None
        self.test_case._custom_thresholds = {
            'response_time_ms': 800,
            'memory_overhead_mb': 60,
            'query_count_max': 30
        }
        
        thresholds = self.test_case._calculate_intelligent_thresholds('list_view', {})
        
        expected = {
            'response_time': 800,
            'memory_usage': 140,  # 80 + 60
            'query_count': 30
        }
        self.assertEqual(thresholds, expected)
    
    def test_calculate_intelligent_thresholds_operation_profile(self):
        """Test threshold calculation using operation profile."""
        self.test_case._per_test_thresholds = None
        self.test_case._custom_thresholds = None
        
        thresholds = self.test_case._calculate_intelligent_thresholds('list_view', {})
        
        # Should use list_view profile defaults
        expected = {
            'response_time': 200.0,
            'memory_usage': 110.0,  # 80 + 30 (tolerance)
            'query_count': 25
        }
        self.assertEqual(thresholds, expected)
    
    def test_generate_contextual_recommendations_list_view(self):
        """Test generating recommendations for list view operations."""
        # Mock metrics with issues
        mock_metrics = Mock()
        mock_metrics.query_count = 10  # High query count
        mock_metrics.response_time = 250  # Slow response
        mock_metrics.memory_overhead = 20  # Normal memory
        mock_metrics._get_recommendations = Mock(return_value=['Base recommendation'])
        
        recommendations = self.test_case._generate_contextual_recommendations(mock_metrics, 'list_view')
        
        self.assertIn('Base recommendation', recommendations)
        
        # Should include list view specific recommendations
        list_view_recommendations = [r for r in recommendations if 'List View:' in r]
        self.assertGreater(len(list_view_recommendations), 0)
    
    def test_generate_contextual_recommendations_create_view(self):
        """Test generating recommendations for create view operations."""
        mock_metrics = Mock()
        mock_metrics.query_count = 12  # High query count for create
        mock_metrics.response_time = 350  # Slow response
        mock_metrics.memory_overhead = 15
        mock_metrics._get_recommendations = Mock(return_value=[])
        
        recommendations = self.test_case._generate_contextual_recommendations(mock_metrics, 'create_view')
        
        # Should include create view specific recommendations
        create_view_recommendations = [r for r in recommendations if 'Create View:' in r]
        self.assertGreater(len(create_view_recommendations), 0)
    
    def test_generate_contextual_recommendations_n_plus_one_executive(self):
        """Test generating executive recommendations for critical N+1 issues."""
        mock_metrics = Mock()
        mock_metrics.query_count = 5
        mock_metrics.response_time = 100
        mock_metrics.memory_overhead = 10
        mock_metrics._get_recommendations = Mock(return_value=[])
        
        # Mock critical N+1 issue
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = True
        mock_n_plus_one_analysis = Mock()
        mock_n_plus_one_analysis.severity_text = 'CRITICAL'
        mock_django_issues.n_plus_one_analysis = mock_n_plus_one_analysis
        mock_metrics.django_issues = mock_django_issues
        
        recommendations = self.test_case._generate_contextual_recommendations(mock_metrics, 'list_view')
        
        # Should have executive priority recommendations at the top
        self.assertIn('EXECUTIVE PRIORITY', recommendations[0])
        self.assertIn('Business Impact', recommendations[1])
    
    def test_set_test_performance_thresholds(self):
        """Test setting per-test performance thresholds."""
        thresholds = {
            'response_time_ms': 1000,
            'query_count_max': 50,
            'memory_overhead_mb': 100
        }
        
        with patch('django_mercury.python_bindings.django_integration_mercury.logger') as mock_logger:
            self.test_case.set_test_performance_thresholds(thresholds)
            
            self.assertEqual(self.test_case._per_test_thresholds, thresholds)
            
            # Should log the threshold settings
            mock_logger.info.assert_called()
            self.assertGreater(mock_logger.info.call_count, 1)
    
    def test_assert_mercury_performance_excellent_success(self):
        """Test asserting excellent performance (success case)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 85.0
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 75.0
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = False
        mock_metrics.django_issues = mock_django_issues
        
        # Should not raise any exception
        self.test_case.assert_mercury_performance_excellent(mock_metrics)
    
    def test_assert_mercury_performance_excellent_failure_score(self):
        """Test asserting excellent performance (score failure)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 75.0  # Below 80 threshold
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 75.0
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = False
        mock_metrics.django_issues = mock_django_issues
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assert_mercury_performance_excellent(mock_metrics)
        
        self.assertIn("Performance score 75.0 below excellent threshold", str(context.exception))
    
    def test_assert_mercury_performance_excellent_failure_response_time(self):
        """Test asserting excellent performance (response time failure)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 85.0
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 150.0  # Above 100ms threshold
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = False
        mock_metrics.django_issues = mock_django_issues
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assert_mercury_performance_excellent(mock_metrics)
        
        self.assertIn("Response time should be under 100ms", str(context.exception))
    
    def test_assert_mercury_performance_excellent_failure_n_plus_one(self):
        """Test asserting excellent performance (N+1 failure)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 85.0
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 75.0
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = True  # Has N+1 issues
        mock_metrics.django_issues = mock_django_issues
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assert_mercury_performance_excellent(mock_metrics)
        
        self.assertIn("N+1 queries prevent excellent performance", str(context.exception))
    
    def test_assert_mercury_performance_production_ready_success(self):
        """Test asserting production-ready performance (success case)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 70.0
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 250.0
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = False
        mock_metrics.django_issues = mock_django_issues
        
        # Should not raise any exception
        self.test_case.assert_mercury_performance_production_ready(mock_metrics)
    
    def test_assert_mercury_performance_production_ready_failure_score(self):
        """Test asserting production-ready performance (score failure)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 50.0  # Below 60 threshold
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 250.0
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = False
        mock_metrics.django_issues = mock_django_issues
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assert_mercury_performance_production_ready(mock_metrics)
        
        self.assertIn("Performance score 50.0 below production threshold", str(context.exception))
    
    def test_assert_mercury_performance_production_ready_failure_response_time(self):
        """Test asserting production-ready performance (response time failure)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 70.0
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 350.0  # Above 300ms threshold
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = False
        mock_metrics.django_issues = mock_django_issues
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assert_mercury_performance_production_ready(mock_metrics)
        
        self.assertIn("Response time should be under 300ms", str(context.exception))
    
    def test_assert_mercury_performance_production_ready_failure_n_plus_one_severity(self):
        """Test asserting production-ready performance (N+1 severity failure)."""
        mock_metrics = Mock()
        mock_performance_score = Mock()
        mock_performance_score.total_score = 70.0
        mock_metrics.performance_score = mock_performance_score
        mock_metrics.response_time = 250.0
        
        mock_django_issues = Mock()
        mock_django_issues.has_n_plus_one = True
        mock_n_plus_one_analysis = Mock()
        mock_n_plus_one_analysis.severity_level = 5  # Too high for production
        mock_django_issues.n_plus_one_analysis = mock_n_plus_one_analysis
        mock_metrics.django_issues = mock_django_issues
        
        with self.assertRaises(AssertionError) as context:
            self.test_case.assert_mercury_performance_production_ready(mock_metrics)
        
        self.assertIn("N+1 severity 5 too high for production", str(context.exception))


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_case = DjangoMercuryAPITestCase()
    
    def test_operation_profile_with_empty_context(self):
        """Test OperationProfile with empty context."""
        profile = OperationProfile(
            operation_name="test_op",
            expected_query_range=(1, 10),
            response_time_baseline=100.0,
            memory_overhead_tolerance=20.0,
            complexity_factors={}
        )
        
        thresholds = profile.calculate_dynamic_thresholds({})
        
        self.assertEqual(thresholds['response_time'], 100.0)
        self.assertEqual(thresholds['memory_usage'], 100.0)  # 80 + 20
        self.assertEqual(thresholds['query_count'], 10)
    
    
    def test_detect_operation_type_with_exception_in_source_analysis(self):
        """Test operation type detection when source analysis fails."""
        def problematic_function():
            # This function might cause issues in source analysis
            pass
        
        # Mock inspect.getsource to raise an exception
        with patch('inspect.getsource', side_effect=OSError("Source not available")):
            result = self.test_case._detect_operation_type('test_method', problematic_function)
            
            # Should fall back gracefully
            self.assertEqual(result, 'detail_view')
    
    def test_extract_test_context_with_exception(self):
        """Test context extraction when source analysis fails."""
        def mock_function():
            pass
        
        with patch('inspect.getsource', side_effect=Exception("Analysis failed")):
            context = self.test_case._extract_test_context(mock_function)
            
            # Should return empty context without crashing
            self.assertEqual(context, {})
    


if __name__ == '__main__':
    unittest.main()