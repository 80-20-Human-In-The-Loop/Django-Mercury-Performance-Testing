"""
Unit tests for monitor module
"""

import unittest
import ctypes
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from dataclasses import dataclass

from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python,
    NPlusOneAnalysis,
    DjangoPerformanceIssues,
    PerformanceScore,
    monitor_django_view,
    monitor_django_model,
    monitor_serializer,
    monitor_database_query,
    EnhancedPerformanceMetrics
)


class MockLibForTesting:
    """Mock library for testing purposes."""
    def __getattr__(self, name):
        def mock_function(*args, **kwargs):
            if name.startswith('get_'):
                return 0.0 if 'ratio' in name else 0
            elif name.startswith('has_') or name.startswith('detect_'):
                return 0
            elif name == 'start_performance_monitoring_enhanced':
                return -1
            return None
        return mock_function


class TestMockLib(unittest.TestCase):
    """Test cases for MockLib fallback."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_lib = MockLibForTesting()

    def test_mock_lib_get_functions(self) -> None:
        """Test mock lib returns sensible defaults for get_ functions."""
        # get_ functions should return numeric values
        self.assertEqual(self.mock_lib.get_elapsed_time_ms(), 0.0)
        self.assertEqual(self.mock_lib.get_memory_usage_mb(), 0.0)
        self.assertEqual(self.mock_lib.get_query_count(), 0)
        self.assertEqual(self.mock_lib.get_cache_hit_ratio(), 0.0)

    def test_mock_lib_has_functions(self) -> None:
        """Test mock lib returns 0 for has_ and detect_ functions."""
        self.assertEqual(self.mock_lib.has_n_plus_one_pattern(), 0)
        self.assertEqual(self.mock_lib.has_poor_cache_performance(), 0)
        self.assertEqual(self.mock_lib.detect_n_plus_one_severe(), 0)

    def test_mock_lib_start_function(self) -> None:
        """Test mock lib returns -1 for start function."""
        result = self.mock_lib.start_performance_monitoring_enhanced()
        self.assertEqual(result, -1)

    def test_mock_lib_other_functions(self) -> None:
        """Test mock lib returns None for other functions."""
        self.assertIsNone(self.mock_lib.increment_query_count())
        self.assertIsNone(self.mock_lib.increment_cache_hits())
        self.assertIsNone(self.mock_lib.stop_performance_monitoring_enhanced())


class TestEnhancedPerformanceMetrics(unittest.TestCase):
    """Test cases for EnhancedPerformanceMetrics C structure."""

    def test_structure_fields(self) -> None:
        """Test C structure has correct fields."""
        fields = [field[0] for field in EnhancedPerformanceMetrics._fields_]
        
        expected_fields = [
            'start_time_ns', 'end_time_ns', 'memory_start_bytes',
            'memory_peak_bytes', 'memory_end_bytes', 'query_count_start',
            'query_count_end', 'cache_hits', 'cache_misses',
            'operation_name', 'operation_type'
        ]
        
        for field in expected_fields:
            self.assertIn(field, fields)

    def test_structure_field_types(self) -> None:
        """Test C structure field types are correct."""
        field_types = {field[0]: field[1] for field in EnhancedPerformanceMetrics._fields_}
        
        # Test a few key field types
        self.assertEqual(field_types['start_time_ns'], ctypes.c_uint64)
        self.assertEqual(field_types['memory_start_bytes'], ctypes.c_size_t)
        self.assertEqual(field_types['query_count_start'], ctypes.c_uint32)
        self.assertEqual(field_types['cache_hits'], ctypes.c_uint32)

    def test_structure_string_fields(self) -> None:
        """Test string fields have correct sizes."""
        field_info = {field[0]: field[1] for field in EnhancedPerformanceMetrics._fields_}
        
        # operation_name should be 256 chars
        operation_name_type = field_info['operation_name']
        self.assertEqual(operation_name_type._length_, 256)
        
        # operation_type should be 64 chars
        operation_type_type = field_info['operation_type']
        self.assertEqual(operation_type_type._length_, 64)


class TestNPlusOneAnalysis(unittest.TestCase):
    """Test cases for NPlusOneAnalysis dataclass."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.analysis = NPlusOneAnalysis(
            has_severe=True,
            has_moderate=True,
            has_pattern=True,
            severity_level=3,
            estimated_cause=2,
            fix_suggestion="Add select_related() to QuerySet",
            query_count=15
        )

    def test_analysis_creation(self) -> None:
        """Test NPlusOneAnalysis creation."""
        self.assertTrue(self.analysis.has_severe)
        self.assertTrue(self.analysis.has_moderate)
        self.assertTrue(self.analysis.has_pattern)
        self.assertEqual(self.analysis.severity_level, 3)
        self.assertEqual(self.analysis.estimated_cause, 2)
        self.assertEqual(self.analysis.query_count, 15)

    def test_severity_text_property(self) -> None:
        """Test severity text property mapping."""
        test_cases = [
            (0, "NONE"),
            (1, "MILD"),
            (2, "MODERATE"),
            (3, "HIGH"),
            (4, "SEVERE"),
            (5, "CRITICAL"),
            (10, "CRITICAL")  # Should cap at CRITICAL
        ]
        
        for severity, expected_text in test_cases:
            analysis = NPlusOneAnalysis(
                has_severe=False, has_moderate=False, has_pattern=False,
                severity_level=severity, estimated_cause=0,
                fix_suggestion="", query_count=0
            )
            self.assertEqual(analysis.severity_text, expected_text)

    def test_cause_text_property(self) -> None:
        """Test cause text property mapping."""
        test_cases = [
            (0, "No N+1 detected"),
            (1, "Serializer N+1 (SerializerMethodField)"),
            (2, "Related model N+1 (Missing select_related)"),
            (3, "Foreign key N+1 (Deep relationship access)"),
            (4, "Complex relationship N+1 (Multiple table joins)"),
            (5, "CASCADE deletion cleanup (Expected for DELETE operations)"),
            (10, "CASCADE deletion cleanup (Expected for DELETE operations)")  # Should cap
        ]
        
        for cause, expected_text in test_cases:
            analysis = NPlusOneAnalysis(
                has_severe=False, has_moderate=False, has_pattern=False,
                severity_level=0, estimated_cause=cause,
                fix_suggestion="", query_count=0
            )
            self.assertEqual(analysis.cause_text, expected_text)


class TestDjangoPerformanceIssues(unittest.TestCase):
    """Test cases for DjangoPerformanceIssues dataclass."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.n_plus_one_analysis = NPlusOneAnalysis(
            has_severe=True, has_moderate=False, has_pattern=True,
            severity_level=4, estimated_cause=1,
            fix_suggestion="Review SerializerMethodField usage",
            query_count=20
        )
        
        self.issues = DjangoPerformanceIssues(
            has_n_plus_one=True,
            excessive_queries=True,
            memory_intensive=False,
            poor_cache_performance=True,
            slow_serialization=False,
            inefficient_pagination=False,
            missing_db_indexes=True,
            n_plus_one_analysis=self.n_plus_one_analysis
        )

    def test_issues_creation(self) -> None:
        """Test DjangoPerformanceIssues creation."""
        self.assertTrue(self.issues.has_n_plus_one)
        self.assertTrue(self.issues.excessive_queries)
        self.assertFalse(self.issues.memory_intensive)
        self.assertTrue(self.issues.poor_cache_performance)

    def test_has_issues_property_true(self) -> None:
        """Test has_issues property returns True when issues exist."""
        self.assertTrue(self.issues.has_issues)

    def test_has_issues_property_false(self) -> None:
        """Test has_issues property returns False when no issues exist."""
        no_issues = DjangoPerformanceIssues(
            has_n_plus_one=False,
            excessive_queries=False,
            memory_intensive=False,
            poor_cache_performance=False,
            slow_serialization=False,
            inefficient_pagination=False,
            missing_db_indexes=False,
            n_plus_one_analysis=NPlusOneAnalysis(
                has_severe=False, has_moderate=False, has_pattern=False,
                severity_level=0, estimated_cause=0, fix_suggestion="", query_count=0
            )
        )
        self.assertFalse(no_issues.has_issues)

    def test_get_issue_summary(self) -> None:
        """Test get_issue_summary returns correct list of issues."""
        summary = self.issues.get_issue_summary()
        
        # Should contain specific issues that are True
        summary_text = " ".join(summary)
        self.assertIn("N+1 Queries", summary_text)
        self.assertIn("SEVERE", summary_text)
        self.assertIn("20 queries", summary_text)
        self.assertIn("Excessive database queries", summary_text)
        self.assertIn("Poor cache hit ratio", summary_text)
        self.assertIn("missing database indexes", summary_text)
        
        # Should not contain issues that are False
        self.assertNotIn("High memory usage", summary_text)
        self.assertNotIn("Slow serialization", summary_text)
        self.assertNotIn("Inefficient pagination", summary_text)

    def test_get_issue_summary_empty(self) -> None:
        """Test get_issue_summary returns empty list when no issues."""
        no_issues = DjangoPerformanceIssues(
            has_n_plus_one=False,
            excessive_queries=False,
            memory_intensive=False,
            poor_cache_performance=False,
            slow_serialization=False,
            inefficient_pagination=False,
            missing_db_indexes=False,
            n_plus_one_analysis=NPlusOneAnalysis(
                has_severe=False, has_moderate=False, has_pattern=False,
                severity_level=0, estimated_cause=0, fix_suggestion="", query_count=0
            )
        )
        
        summary = no_issues.get_issue_summary()
        self.assertEqual(summary, [])


class TestPerformanceScore(unittest.TestCase):
    """Test cases for PerformanceScore dataclass."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.score = PerformanceScore(
            total_score=85.5,
            grade="A",
            response_time_score=25.0,
            query_efficiency_score=35.0,
            memory_efficiency_score=18.0,
            n_plus_one_penalty=5.0,
            cache_performance_score=8.0,
            points_lost=["Response time penalty: -5pts"],
            points_gained=["Query efficiency: +35pts"],
            optimization_impact={"n_plus_one_fix": 5.0}
        )

    def test_score_creation(self) -> None:
        """Test PerformanceScore creation."""
        self.assertEqual(self.score.total_score, 85.5)
        self.assertEqual(self.score.grade, "A")
        self.assertEqual(self.score.response_time_score, 25.0)
        self.assertEqual(self.score.query_efficiency_score, 35.0)
        self.assertEqual(self.score.memory_efficiency_score, 18.0)
        self.assertEqual(self.score.n_plus_one_penalty, 5.0)
        self.assertEqual(self.score.cache_performance_score, 8.0)

    def test_score_lists_and_dicts(self) -> None:
        """Test score lists and dictionaries."""
        self.assertIsInstance(self.score.points_lost, list)
        self.assertIsInstance(self.score.points_gained, list)
        self.assertIsInstance(self.score.optimization_impact, dict)
        
        self.assertIn("Response time penalty: -5pts", self.score.points_lost)
        self.assertIn("Query efficiency: +35pts", self.score.points_gained)
        self.assertEqual(self.score.optimization_impact["n_plus_one_fix"], 5.0)


class TestEnhancedPerformanceMetricsPython(unittest.TestCase):
    """Test cases for EnhancedPerformanceMetrics_Python class."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked C library."""
        # Create a mock C metrics structure
        self.mock_c_metrics = MagicMock()
        self.mock_c_metrics.contents.operation_type = b"view"
        
        # Patch the library functions
        self.lib_patcher = patch('django_mercury.python_bindings.monitor.lib')
        self.mock_lib = self.lib_patcher.start()
        
        # Also patch C_EXTENSIONS_AVAILABLE to prevent segfaults with mocks
        self.c_ext_patcher = patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
        self.c_ext_patcher.start()
        
        # Configure mock returns
        self.mock_lib.get_elapsed_time_ms.return_value = 150.0
        self.mock_lib.get_memory_usage_mb.return_value = 95.0
        self.mock_lib.get_memory_delta_mb.return_value = 15.0
        self.mock_lib.get_query_count.return_value = 8
        self.mock_lib.get_cache_hit_count.return_value = 10
        self.mock_lib.get_cache_miss_count.return_value = 2
        self.mock_lib.get_cache_hit_ratio.return_value = 0.83
        
        # N+1 analysis mocks
        self.mock_lib.detect_n_plus_one_severe.return_value = 0
        self.mock_lib.detect_n_plus_one_moderate.return_value = 1
        self.mock_lib.detect_n_plus_one_pattern_by_count.return_value = 1
        self.mock_lib.calculate_n_plus_one_severity.return_value = 2
        self.mock_lib.estimate_n_plus_one_cause.return_value = 2
        self.mock_lib.get_n_plus_one_fix_suggestion.return_value = b"Add select_related()"
        self.mock_lib.has_n_plus_one_pattern.return_value = 1
        self.mock_lib.is_memory_intensive.return_value = 0
        self.mock_lib.has_poor_cache_performance.return_value = 0

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.lib_patcher.stop()
        self.c_ext_patcher.stop()

    def test_metrics_creation(self) -> None:
        """Test EnhancedPerformanceMetrics_Python creation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        
        self.assertEqual(metrics.operation_name, "test_operation")
        self.assertEqual(metrics.response_time, 150.0)
        self.assertEqual(metrics.memory_usage, 95.0)
        self.assertEqual(metrics.memory_delta, 15.0)
        self.assertEqual(metrics.query_count, 8)
        self.assertEqual(metrics.cache_hits, 10)
        self.assertEqual(metrics.cache_misses, 2)
        self.assertEqual(metrics.cache_hit_ratio, 0.83)

    def test_memory_baseline_calculation(self) -> None:
        """Test memory baseline and overhead calculation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        
        # Should calculate overhead above baseline
        self.assertEqual(metrics.baseline_memory_mb, 80.0)
        self.assertEqual(metrics.memory_overhead, 15.0)  # 95 - 80

    def test_operation_type_decoding(self) -> None:
        """Test operation type decoding from C structure."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertEqual(metrics.operation_type, "view")

    def test_operation_type_decode_error_handling(self) -> None:
        """Test operation type decode error handling."""
        # Mock decode error by making decode raise an exception
        mock_operation_type = MagicMock()
        mock_operation_type.decode.side_effect = UnicodeDecodeError(
            'utf-8', b'', 0, 1, 'invalid'
        )
        self.mock_c_metrics.contents.operation_type = mock_operation_type
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertEqual(metrics.operation_type, "unknown")

    def test_performance_status_assessment(self) -> None:
        """Test performance status assessment."""
        # Test different response times
        test_cases = [
            (45.0, "excellent"),
            (75.0, "good"),
            (250.0, "acceptable"),
            (450.0, "slow"),
            (600.0, "critical")
        ]
        
        for response_time, expected_status in test_cases:
            self.mock_lib.get_elapsed_time_ms.return_value = response_time
            metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
            self.assertEqual(metrics.performance_status.value, expected_status)

    def test_is_fast_property(self) -> None:
        """Test is_fast property."""
        self.mock_lib.get_elapsed_time_ms.return_value = 50.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics.is_fast)
        
        self.mock_lib.get_elapsed_time_ms.return_value = 150.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertFalse(metrics.is_fast)

    def test_is_slow_property(self) -> None:
        """Test is_slow property."""
        self.mock_lib.get_elapsed_time_ms.return_value = 300.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertFalse(metrics.is_slow)
        
        self.mock_lib.get_elapsed_time_ms.return_value = 600.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics.is_slow)

    def test_is_memory_intensive_property(self) -> None:
        """Test is_memory_intensive property."""
        # Low memory usage
        self.mock_lib.get_memory_usage_mb.return_value = 85.0
        self.mock_lib.get_memory_delta_mb.return_value = 5.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertFalse(metrics.is_memory_intensive)
        
        # High memory usage
        self.mock_lib.get_memory_usage_mb.return_value = 150.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics.is_memory_intensive)
        
        # High memory delta
        self.mock_lib.get_memory_usage_mb.return_value = 85.0
        self.mock_lib.get_memory_delta_mb.return_value = 60.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics.is_memory_intensive)

    def test_detect_slow_serialization(self) -> None:
        """Test slow serialization detection."""
        # Case 1: Few queries, high response time
        self.mock_lib.get_query_count.return_value = 1
        self.mock_lib.get_elapsed_time_ms.return_value = 150.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics._detect_slow_serialization())
        
        # Case 2: No queries, moderate response time
        self.mock_lib.get_query_count.return_value = 0
        self.mock_lib.get_elapsed_time_ms.return_value = 75.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics._detect_slow_serialization())
        
        # Case 3: Many queries, high response time (not serialization)
        self.mock_lib.get_query_count.return_value = 10
        self.mock_lib.get_elapsed_time_ms.return_value = 200.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertFalse(metrics._detect_slow_serialization())

    def test_detect_inefficient_pagination(self) -> None:
        """Test inefficient pagination detection."""
        # Case 1: Moderate queries, high response time
        self.mock_lib.get_query_count.return_value = 5
        self.mock_lib.get_elapsed_time_ms.return_value = 200.0
        self.mock_lib.get_memory_delta_mb.return_value = 10.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics._detect_inefficient_pagination())
        
        # Case 2: High memory delta, moderate queries
        self.mock_lib.get_query_count.return_value = 4
        self.mock_lib.get_elapsed_time_ms.return_value = 100.0
        self.mock_lib.get_memory_delta_mb.return_value = 25.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics._detect_inefficient_pagination())
        
        # Case 3: Low queries, low response time (not pagination issue)
        self.mock_lib.get_query_count.return_value = 2
        self.mock_lib.get_elapsed_time_ms.return_value = 50.0
        self.mock_lib.get_memory_delta_mb.return_value = 5.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertFalse(metrics._detect_inefficient_pagination())

    def test_detect_missing_indexes(self) -> None:
        """Test missing indexes detection."""
        # Case 1: Few queries, very high response time
        self.mock_lib.get_query_count.return_value = 3
        self.mock_lib.get_elapsed_time_ms.return_value = 400.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertTrue(metrics._detect_missing_indexes())
        
        # Case 2: Few queries, normal response time (no issue)
        self.mock_lib.get_query_count.return_value = 2
        self.mock_lib.get_elapsed_time_ms.return_value = 100.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        self.assertFalse(metrics._detect_missing_indexes())

    def test_n_plus_one_analysis_creation(self) -> None:
        """Test N+1 analysis creation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        
        analysis = metrics.django_issues.n_plus_one_analysis
        self.assertFalse(analysis.has_severe)  # Mock returns 0
        self.assertTrue(analysis.has_moderate)  # Mock returns 1
        self.assertTrue(analysis.has_pattern)   # Mock returns 1
        self.assertEqual(analysis.severity_level, 2)
        self.assertEqual(analysis.estimated_cause, 2)
        self.assertEqual(analysis.fix_suggestion, "Add select_related()")

    def test_django_issues_analysis(self) -> None:
        """Test Django issues analysis."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        issues = metrics.django_issues
        
        self.assertTrue(issues.has_n_plus_one)  # Mock returns 1
        self.assertFalse(issues.memory_intensive)  # Mock returns 0
        self.assertFalse(issues.poor_cache_performance)  # Mock returns 0
        
        # These are calculated based on metrics
        self.assertFalse(issues.excessive_queries)  # 8 queries < 20
        self.assertFalse(issues.slow_serialization)  # Not matching criteria
        self.assertFalse(issues.inefficient_pagination)  # Not matching criteria
        self.assertFalse(issues.missing_db_indexes)  # Not matching criteria

    def test_memory_breakdown_estimation(self) -> None:
        """Test memory breakdown estimation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        breakdown = metrics.memory_breakdown
        
        # Should have all expected components
        expected_components = [
            'python_interpreter', 'django_framework', 'database_connections',
            'test_framework', 'drf_framework', 'application_code',
            'payload_data', 'temporary_objects'
        ]
        
        for component in expected_components:
            self.assertIn(component, breakdown)
        
        # Temporary objects should be overhead above baseline
        self.assertEqual(breakdown['temporary_objects'], 15.0)  # 95 - 80

    def test_memory_payload_efficiency_calculation(self) -> None:
        """Test memory payload efficiency calculation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        
        # Calculate efficiency with response size
        metrics.calculate_memory_payload_efficiency(10.0)  # 10KB response
        
        self.assertEqual(metrics.payload_size_kb, 10.0)
        self.assertEqual(metrics.memory_per_kb_payload, 1.5)  # 15MB overhead / 10KB
        
        # Estimated payload memory should be ~40KB (10KB * 4)
        estimated_payload_mb = (10.0 * 4) / 1024
        self.assertAlmostEqual(metrics.memory_breakdown['payload_data'], estimated_payload_mb, places=3)

    def test_get_memory_analysis_report(self) -> None:
        """Test memory analysis report generation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        metrics.calculate_memory_payload_efficiency(5.0)
        
        report = metrics.get_memory_analysis_report()
        
        # Should contain key information
        self.assertIn("Memory Usage Analysis", report)
        self.assertIn("95.0MB", report)  # Total memory
        self.assertIn("80.0MB", report)  # Baseline
        self.assertIn("+15.0MB", report)  # Overhead
        self.assertIn("Memory Breakdown", report)
        self.assertIn("Payload Efficiency", report)
        self.assertIn("5.0KB", report)  # Response size

    def test_performance_score_calculation(self) -> None:
        """Test performance score calculation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        score = metrics.performance_score
        
        self.assertIsInstance(score, PerformanceScore)
        self.assertIsInstance(score.total_score, float)
        self.assertIsInstance(score.grade, str)
        self.assertGreaterEqual(score.total_score, 0.0)
        self.assertLessEqual(score.total_score, 100.0)

    def test_detailed_report_generation(self) -> None:
        """Test detailed report generation."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        report = metrics.detailed_report()
        
        # Should contain key metrics
        self.assertIn("Enhanced Performance Report", report)
        self.assertIn("test_operation", report)
        self.assertIn("150.00ms", report)  # Response time
        self.assertIn("95.0MB", report)   # Memory usage
        self.assertIn("8", report)        # Query count
        self.assertIn("83.0%", report)    # Cache hit ratio

    def test_get_performance_report_with_scoring(self) -> None:
        """Test performance report with scoring."""
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test_operation")
        report = metrics.get_performance_report_with_scoring()
        
        # Should contain scoring information
        self.assertIn("Performance Grade", report)
        self.assertIn("Score Breakdown", report)
        self.assertIn("Response Time:", report)
        self.assertIn("Query Efficiency:", report)
        self.assertIn("Memory Efficiency:", report)
        self.assertIn("Cache Performance:", report)


class TestEnhancedPerformanceMonitor(unittest.TestCase):
    """Test cases for EnhancedPerformanceMonitor class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_operation", "view")

    def test_monitor_creation(self) -> None:
        """Test monitor creation."""
        self.assertEqual(self.monitor.operation_name, "test_operation")
        self.assertEqual(self.monitor.operation_type, "view")
        self.assertIsNone(self.monitor.handle)
        self.assertIsNone(self.monitor._metrics)
        self.assertEqual(self.monitor._thresholds, {})
        self.assertFalse(self.monitor._auto_assert)

    def test_expect_response_under(self) -> None:
        """Test expect_response_under method."""
        result = self.monitor.expect_response_under(100.0)
        
        self.assertIs(result, self.monitor)  # Should return self for chaining
        self.assertEqual(self.monitor._thresholds['response_time'], 100.0)
        self.assertTrue(self.monitor._auto_assert)

    def test_expect_memory_under(self) -> None:
        """Test expect_memory_under method."""
        result = self.monitor.expect_memory_under(120.0)
        
        self.assertIs(result, self.monitor)
        self.assertEqual(self.monitor._thresholds['memory_usage'], 120.0)
        self.assertTrue(self.monitor._auto_assert)

    def test_expect_queries_under(self) -> None:
        """Test expect_queries_under method."""
        result = self.monitor.expect_queries_under(5)
        
        self.assertIs(result, self.monitor)
        self.assertEqual(self.monitor._thresholds['query_count'], 5)
        self.assertTrue(self.monitor._auto_assert)

    def test_expect_cache_hit_ratio_above(self) -> None:
        """Test expect_cache_hit_ratio_above method."""
        result = self.monitor.expect_cache_hit_ratio_above(0.8)
        
        self.assertIs(result, self.monitor)
        self.assertEqual(self.monitor._thresholds['cache_hit_ratio'], 0.8)
        self.assertTrue(self.monitor._auto_assert)

    def test_disable_auto_assert(self) -> None:
        """Test disable_auto_assert method."""
        self.monitor._auto_assert = True
        result = self.monitor.disable_auto_assert()
        
        self.assertIs(result, self.monitor)
        self.assertFalse(self.monitor._auto_assert)

    def test_enable_django_hooks(self) -> None:
        """Test enable_django_hooks method."""
        with patch('django_mercury.python_bindings.monitor.DjangoQueryTracker'), \
             patch('django_mercury.python_bindings.monitor.DjangoCacheTracker'):
            result = self.monitor.enable_django_hooks()
            
            self.assertIs(result, self.monitor)
            self.assertTrue(self.monitor._django_hooks_active)

    def test_enable_django_hooks_not_available(self) -> None:
        """Test enable_django_hooks when Django components not available."""
        with patch('django_mercury.python_bindings.monitor.DjangoQueryTracker', None), \
             patch('django_mercury.python_bindings.monitor.DjangoCacheTracker', None):
            result = self.monitor.enable_django_hooks()
            
            self.assertIs(result, self.monitor)
            self.assertFalse(self.monitor._django_hooks_active)

    def test_method_chaining(self) -> None:
        """Test method chaining works correctly."""
        result = (self.monitor
                 .expect_response_under(100.0)
                 .expect_memory_under(120.0)
                 .expect_queries_under(5)
                 .expect_cache_hit_ratio_above(0.8)
                 .disable_auto_assert())
        
        self.assertIs(result, self.monitor)
        self.assertEqual(self.monitor._thresholds['response_time'], 100.0)
        self.assertEqual(self.monitor._thresholds['memory_usage'], 120.0)
        self.assertEqual(self.monitor._thresholds['query_count'], 5)
        self.assertEqual(self.monitor._thresholds['cache_hit_ratio'], 0.8)
        self.assertFalse(self.monitor._auto_assert)

    @patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_context_manager_enter_success(self, mock_lib) -> None:
        """Test context manager __enter__ method success."""
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        
        result = self.monitor.__enter__()
        
        self.assertIs(result, self.monitor)
        self.assertEqual(self.monitor.handle, 12345)
        mock_lib.start_performance_monitoring_enhanced.assert_called_once_with(
            b'test_operation', b'view'
        )

    @patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_context_manager_enter_failure(self, mock_lib) -> None:
        """Test context manager __enter__ method graceful degradation."""
        mock_lib.start_performance_monitoring_enhanced.return_value = -1
        
        # Should NOT raise RuntimeError anymore, instead gracefully degrade
        result = self.monitor.__enter__()
        
        # Should return self (successful context manager entry)
        self.assertIs(result, self.monitor)
        
        # Should set handle to None for fallback mode
        self.assertIsNone(self.monitor.handle)

    @patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_context_manager_exit_success(self, mock_lib) -> None:
        """Test context manager __exit__ method success."""
        # Set up the monitor as if it was started
        self.monitor.handle = 12345
        
        # Mock the C metrics structure
        mock_c_metrics = MagicMock()
        mock_c_metrics.contents.operation_type = b"view"
        mock_lib.stop_performance_monitoring_enhanced.return_value = mock_c_metrics
        
        # Mock all the metric getter functions
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 90.0
        mock_lib.get_memory_delta_mb.return_value = 10.0
        mock_lib.get_query_count.return_value = 3
        mock_lib.get_cache_hit_count.return_value = 5
        mock_lib.get_cache_miss_count.return_value = 1
        mock_lib.get_cache_hit_ratio.return_value = 0.83
        
        # N+1 analysis mocks
        mock_lib.detect_n_plus_one_severe.return_value = 0
        mock_lib.detect_n_plus_one_moderate.return_value = 0
        mock_lib.detect_n_plus_one_pattern_by_count.return_value = 0
        mock_lib.calculate_n_plus_one_severity.return_value = 0
        mock_lib.estimate_n_plus_one_cause.return_value = 0
        mock_lib.get_n_plus_one_fix_suggestion.return_value = b"No issues"
        mock_lib.has_n_plus_one_pattern.return_value = 0
        mock_lib.is_memory_intensive.return_value = 0
        mock_lib.has_poor_cache_performance.return_value = 0
        
        # Call __exit__
        self.monitor.__exit__(None, None, None)
        
        # Verify calls
        mock_lib.stop_performance_monitoring_enhanced.assert_called_once_with(12345)
        # Note: free_metrics is NOT called because we're using MockLib
        
        # Verify metrics were created
        self.assertIsNotNone(self.monitor._metrics)
        self.assertIsNone(self.monitor.handle)

    def test_context_manager_exit_no_handle(self) -> None:
        """Test context manager __exit__ when no handle set."""
        # Should not raise exception
        self.monitor.__exit__(None, None, None)
        self.assertIsNone(self.monitor.handle)

    def test_metrics_property_before_completion(self) -> None:
        """Test metrics property raises error before monitoring completion."""
        with self.assertRaises(RuntimeError) as context:
            _ = self.monitor.metrics
        
        self.assertIn("Performance monitoring not completed", str(context.exception))

    @patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_assert_performance_success(self, mock_lib) -> None:
        """Test assert_performance method success."""
        # Set up mock metrics
        self.monitor._metrics = MagicMock()
        self.monitor._metrics.response_time = 80.0
        self.monitor._metrics.memory_usage = 110.0
        self.monitor._metrics.query_count = 4
        self.monitor._metrics.cache_hit_ratio = 0.85
        
        # Should not raise exception
        self.monitor.assert_performance(
            max_response_time=100.0,
            max_memory_mb=120.0,
            max_queries=5,
            min_cache_hit_ratio=0.8
        )

    def test_assert_performance_failures(self) -> None:
        """Test assert_performance method with failures."""
        # Set up mock metrics that exceed thresholds
        self.monitor._metrics = MagicMock()
        self.monitor._metrics.response_time = 150.0
        self.monitor._metrics.memory_usage = 130.0
        self.monitor._metrics.query_count = 8
        self.monitor._metrics.cache_hit_ratio = 0.6
        
        with self.assertRaises(AssertionError) as context:
            self.monitor.assert_performance(
                max_response_time=100.0,
                max_memory_mb=120.0,
                max_queries=5,
                min_cache_hit_ratio=0.8
            )
        
        error_message = str(context.exception)
        self.assertIn("response time 150.00ms > 100.0ms", error_message)
        self.assertIn("memory usage 130.00MB > 120.0MB", error_message)
        self.assertIn("query count 8 > 5", error_message)
        self.assertIn("cache hit ratio 60.0% < 80.0%", error_message)

    def test_assert_performance_no_metrics(self) -> None:
        """Test assert_performance raises error when no metrics available."""
        with self.assertRaises(RuntimeError) as context:
            self.monitor.assert_performance(max_response_time=100.0)
        
        self.assertIn("Performance monitoring not completed", str(context.exception))


class TestFactoryFunctions(unittest.TestCase):
    """Test cases for factory functions."""

    def test_monitor_django_view(self) -> None:
        """Test monitor_django_view factory function."""
        monitor = monitor_django_view("test_view", "list_view")
        
        self.assertIsInstance(monitor, EnhancedPerformanceMonitor)
        self.assertEqual(monitor.operation_name, "test_view")
        self.assertEqual(monitor.operation_type, "list_view")

    def test_monitor_django_view_default_type(self) -> None:
        """Test monitor_django_view with default operation type."""
        monitor = monitor_django_view("test_view")
        
        self.assertEqual(monitor.operation_type, "view")

    def test_monitor_django_model(self) -> None:
        """Test monitor_django_model factory function."""
        monitor = monitor_django_model("test_model")
        
        self.assertIsInstance(monitor, EnhancedPerformanceMonitor)
        self.assertEqual(monitor.operation_name, "test_model")
        self.assertEqual(monitor.operation_type, "model")

    def test_monitor_serializer(self) -> None:
        """Test monitor_serializer factory function."""
        monitor = monitor_serializer("test_serializer")
        
        self.assertIsInstance(monitor, EnhancedPerformanceMonitor)
        self.assertEqual(monitor.operation_name, "test_serializer")
        self.assertEqual(monitor.operation_type, "serializer")

    def test_monitor_database_query(self) -> None:
        """Test monitor_database_query factory function."""
        monitor = monitor_database_query("test_query")
        
        self.assertIsInstance(monitor, EnhancedPerformanceMonitor)
        self.assertEqual(monitor.operation_name, "test_query")
        self.assertEqual(monitor.operation_type, "query")


class TestMonitorIntegration(unittest.TestCase):
    """Integration tests for monitor functionality."""

    @patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_full_monitoring_cycle(self, mock_lib) -> None:
        """Test complete monitoring cycle."""
        # Set up mocks
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        
        mock_c_metrics = MagicMock()
        mock_c_metrics.contents.operation_type = b"integration_test"
        mock_lib.stop_performance_monitoring_enhanced.return_value = mock_c_metrics
        
        # Configure metric returns
        mock_lib.get_elapsed_time_ms.return_value = 75.0
        mock_lib.get_memory_usage_mb.return_value = 85.0
        mock_lib.get_memory_delta_mb.return_value = 5.0
        mock_lib.get_query_count.return_value = 2
        mock_lib.get_cache_hit_count.return_value = 8
        mock_lib.get_cache_miss_count.return_value = 2
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        # N+1 analysis mocks (no issues)
        mock_lib.detect_n_plus_one_severe.return_value = 0
        mock_lib.detect_n_plus_one_moderate.return_value = 0
        mock_lib.detect_n_plus_one_pattern_by_count.return_value = 0
        mock_lib.calculate_n_plus_one_severity.return_value = 0
        mock_lib.estimate_n_plus_one_cause.return_value = 0
        mock_lib.get_n_plus_one_fix_suggestion.return_value = b"No issues detected"
        mock_lib.has_n_plus_one_pattern.return_value = 0
        mock_lib.is_memory_intensive.return_value = 0
        mock_lib.has_poor_cache_performance.return_value = 0
        
        # Test the full cycle
        monitor = EnhancedPerformanceMonitor("integration_test")
        
        with monitor:
            # Simulate some work
            time.sleep(0.001)
        
        # Verify metrics are available
        metrics = monitor.metrics
        self.assertEqual(metrics.response_time, 75.0)
        self.assertEqual(metrics.memory_usage, 85.0)
        self.assertEqual(metrics.query_count, 2)
        self.assertEqual(metrics.cache_hit_ratio, 0.8)
        
        # Verify reports can be generated
        detailed_report = metrics.detailed_report()
        scoring_report = metrics.get_performance_report_with_scoring()
        
        self.assertIn("integration_test", detailed_report)
        self.assertIn("Performance Grade", scoring_report)

    def test_chained_configuration(self) -> None:
        """Test chained method configuration."""
        monitor = (EnhancedPerformanceMonitor("chained_test")
                  .expect_response_under(100.0)
                  .expect_memory_under(120.0)
                  .expect_queries_under(5)
                  .expect_cache_hit_ratio_above(0.7)
                  .enable_django_hooks())
        
        # Verify all configurations were applied
        self.assertEqual(monitor._thresholds['response_time'], 100.0)
        self.assertEqual(monitor._thresholds['memory_usage'], 120.0)
        self.assertEqual(monitor._thresholds['query_count'], 5)
        self.assertEqual(monitor._thresholds['cache_hit_ratio'], 0.7)
        self.assertTrue(monitor._auto_assert)


if __name__ == '__main__':
    unittest.main()