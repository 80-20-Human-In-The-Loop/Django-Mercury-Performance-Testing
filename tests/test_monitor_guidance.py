"""
Tests for educational guidance methods in monitor.py
Focus on covering lines 1092-1149 and related guidance functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor


class TestEducationalGuidance(unittest.TestCase):
    """Test educational guidance generation methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EnhancedPerformanceMonitor("test_op")
        
        # Enable educational guidance (required for the methods to work)
        self.monitor.enable_educational_guidance()
        
        # Create mock metrics with various violation scenarios
        self.mock_metrics = Mock()
        self.mock_metrics.query_count = 15
        self.mock_metrics.response_time = 300.5
        self.mock_metrics.memory_usage = 150.0
        self.mock_metrics.memory_usage_mb = 150.0
    
    def test_generate_educational_guidance_query_violation_n_plus_one(self):
        """Test guidance generation for N+1 query violations."""
        self.monitor._metrics = self.mock_metrics
        self.monitor.operation_type = "detail_view"
        
        violations = ["Query count 15 > 10"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        self.assertIn("N+1 query issue detected", guidance)
        self.assertIn("select_related()", guidance)
        self.assertIn("prefetch_related()", guidance)
        self.assertIn("queryset = Model.objects.select_related", guidance)
    
    def test_generate_educational_guidance_query_violation_list_view(self):
        """Test guidance generation for list view query violations."""
        self.monitor._metrics = self.mock_metrics
        self.monitor.operation_type = "list_view"
        
        violations = ["Query count 15 > 10"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        self.assertIn("N+1 query issue detected", guidance)
        self.assertIn("pagination", guidance)
        self.assertIn("select_related()/prefetch_related()", guidance)
    
    def test_generate_educational_guidance_query_violation_low_count(self):
        """Test guidance generation for query violations with low count."""
        mock_metrics = Mock()
        mock_metrics.query_count = 5
        mock_metrics.response_time = 100.0
        mock_metrics.memory_usage = 50.0
        mock_metrics.memory_usage_mb = 50.0
        
        self.monitor._metrics = mock_metrics
        
        violations = ["Query count 5 > 3"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        self.assertIn("Query count exceeded", guidance)
        self.assertIn("review database access patterns", guidance)
        self.assertIn("query_count_max threshold", guidance)
    
    def test_generate_educational_guidance_response_time_violation(self):
        """Test guidance generation for response time violations."""
        self.monitor._metrics = self.mock_metrics
        
        violations = ["Response time 300.5ms > 200ms"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        self.assertIn("Response time exceeded", guidance)
        self.assertIn("optimize performance", guidance)
        self.assertIn("database indexes", guidance)
        self.assertIn("response_time_ms threshold", guidance)
    
    def test_generate_educational_guidance_memory_violation(self):
        """Test guidance generation for memory violations."""
        self.monitor._metrics = self.mock_metrics
        
        violations = ["Memory usage 150.0MB > 100MB"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        self.assertIn("Memory usage exceeded", guidance)
        self.assertIn("optimize memory consumption", guidance)
        self.assertIn("pagination", guidance)
        self.assertIn("memory_overhead_mb threshold", guidance)
    
    def test_generate_educational_guidance_multiple_violations(self):
        """Test guidance generation for multiple violations."""
        self.monitor._metrics = self.mock_metrics
        
        violations = [
            "Query count 15 > 10",
            "Response time 300.5ms > 200ms",
            "Memory usage 150.0MB > 100MB"
        ]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should include guidance for all violation types
        self.assertIn("N+1 query issue", guidance)
        self.assertIn("Response time exceeded", guidance)
        self.assertIn("Memory usage exceeded", guidance)
        
        # Should include threshold suggestions
        self.assertIn("set_performance_thresholds", guidance)
        self.assertIn("query_count_max", guidance)
        self.assertIn("response_time_ms", guidance)
        self.assertIn("memory_overhead_mb", guidance)
    
    def test_generate_educational_guidance_threshold_suggestions_query(self):
        """Test threshold suggestions for query violations."""
        self.monitor._metrics = self.mock_metrics
        
        violations = ["Query count 15 > 10"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should suggest query count threshold (15 + 2 = 17)
        self.assertIn("'query_count_max': 17", guidance)
    
    def test_generate_educational_guidance_threshold_suggestions_response_time(self):
        """Test threshold suggestions for response time violations."""
        self.monitor._metrics = self.mock_metrics
        
        violations = ["Response time 300.5ms > 200ms"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should suggest response time threshold (300.5 * 1.5 = 450.75, rounded to 450)
        self.assertIn("'response_time_ms': 450", guidance)
    
    def test_generate_educational_guidance_threshold_suggestions_memory(self):
        """Test threshold suggestions for memory violations."""
        self.monitor._metrics = self.mock_metrics
        
        violations = ["Memory usage 150.0MB > 100MB"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should suggest memory threshold (150.0 * 1.2 = 180)
        self.assertIn("'memory_overhead_mb': 180", guidance)
    
    def test_generate_educational_guidance_memory_fallback_attribute(self):
        """Test memory guidance when memory_usage_mb attribute is missing."""
        mock_metrics = Mock()
        mock_metrics.query_count = 5
        mock_metrics.response_time = 100.0
        mock_metrics.memory_usage = 120.0
        # Don't set memory_usage_mb to test fallback
        del mock_metrics.memory_usage_mb
        
        self.monitor._metrics = mock_metrics
        
        violations = ["Memory usage 120.0MB > 100MB"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should use fallback memory_usage attribute
        self.assertIn("'memory_overhead_mb': 144", guidance)  # 120 * 1.2 = 144
    
    def test_generate_educational_guidance_memory_default_fallback(self):
        """Test memory guidance when both memory attributes are missing."""
        mock_metrics = Mock()
        mock_metrics.query_count = 5
        mock_metrics.response_time = 100.0
        # Don't set any memory attributes to test default fallback
        del mock_metrics.memory_usage
        del mock_metrics.memory_usage_mb
        
        self.monitor._metrics = mock_metrics
        
        violations = ["Memory usage 80.0MB > 100MB"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should use default fallback (100 * 1.2 = 120)
        self.assertIn("'memory_overhead_mb': 120", guidance)
    
    def test_generate_educational_guidance_no_violations(self):
        """Test guidance generation with no violations."""
        guidance = self.monitor._generate_educational_guidance([])
        
        self.assertEqual(guidance, "")
    
    def test_generate_educational_guidance_no_metrics(self):
        """Test guidance generation when metrics are None."""
        self.monitor._metrics = None
        
        violations = ["Query count 15 > 10"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should still provide basic guidance even without metrics
        self.assertIn("Query count exceeded", guidance)
        
        # But shouldn't provide specific threshold suggestions
        self.assertNotIn("set_performance_thresholds", guidance)
    
    def test_generate_educational_guidance_disabled(self):
        """Test guidance generation when educational guidance is disabled."""
        # Create a new monitor with guidance disabled
        monitor = EnhancedPerformanceMonitor("test_op")
        # Don't enable guidance - it should be disabled by default
        
        violations = ["Query count 15 > 10"]
        
        guidance = monitor._generate_educational_guidance(violations)
        
        # Should return empty string when guidance is disabled
        self.assertEqual(guidance, "")
    
    @patch('django_mercury.python_bindings.monitor.colors')
    def test_generate_educational_guidance_coloring(self, mock_colors):
        """Test that guidance text is properly colored."""
        mock_colors.colorize.return_value = "colored_text"
        
        self.monitor._metrics = self.mock_metrics
        
        violations = ["Query count 15 > 10"]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should call colorize for each guidance line
        self.assertTrue(mock_colors.colorize.called)
        self.assertIn("colored_text", guidance)
    
    def test_generate_educational_guidance_minimum_threshold_values(self):
        """Test that minimum threshold values are enforced."""
        # Create metrics with very low values
        mock_metrics = Mock()
        mock_metrics.query_count = 2
        mock_metrics.response_time = 10.0
        mock_metrics.memory_usage_mb = 5.0
        
        self.monitor._metrics = mock_metrics
        
        violations = [
            "Query count 2 > 1",
            "Response time 10ms > 5ms",
            "Memory usage 5MB > 3MB"
        ]
        
        guidance = self.monitor._generate_educational_guidance(violations)
        
        # Should enforce minimum values
        self.assertIn("'query_count_max': 10", guidance)    # max(2+2, 10) = 10
        self.assertIn("'response_time_ms': 100", guidance)  # max(10*1.5, 100) = 100
        self.assertIn("'memory_overhead_mb': 50", guidance) # max(5*1.2, 50) = 50


if __name__ == '__main__':
    unittest.main()