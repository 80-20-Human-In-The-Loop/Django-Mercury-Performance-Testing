"""
Integration tests for pure Python implementations.
Tests components working together and fallback behavior.
"""

import unittest
from unittest.mock import patch, Mock
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from django_mercury.python_bindings.pure_python import (
    PythonPerformanceMonitor,
    PythonMetricsEngine,
    PythonQueryAnalyzer,
    PythonTestOrchestrator,
    python_performance_monitor
)


class TestPurePythonIntegration(unittest.TestCase):
    """Integration tests for pure Python components."""
    
    def test_monitor_and_metrics_engine_integration(self):
        """Test monitor working with metrics engine."""
        monitor = PythonPerformanceMonitor()
        engine = PythonMetricsEngine()
        
        # Run multiple monitoring sessions
        for i in range(3):
            monitor.start_monitoring()
            monitor.track_query(f"SELECT * FROM table_{i}", 0.01 * (i + 1))
            monitor.track_cache(i % 2 == 0)  # Alternate hits and misses
            time.sleep(0.001)  # Small delay
            monitor.stop_monitoring()
            
            # Add metrics to engine
            engine.add_metrics(monitor.get_metrics())
            monitor.reset()
        
        # Analyze aggregated metrics
        stats = engine.calculate_statistics()
        
        self.assertEqual(stats['count'], 3)
        self.assertEqual(stats['total_queries'], 3)
        self.assertGreater(stats['mean'], 0)
        self.assertEqual(stats['implementation'], 'pure_python')
    
    def test_monitor_and_query_analyzer_integration(self):
        """Test monitor tracking queries analyzed by analyzer."""
        monitor = PythonPerformanceMonitor()
        analyzer = PythonQueryAnalyzer()
        
        queries = [
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM posts JOIN users ON posts.user_id = users.id",
            "INSERT INTO logs (message) VALUES ('test')",
        ]
        
        monitor.start_monitoring()
        
        for sql in queries:
            # Analyze query
            analysis = analyzer.analyze_query(sql)
            
            # Track in monitor with complexity-based duration
            simulated_duration = 0.01 * analysis['estimated_complexity']
            monitor.track_query(sql, simulated_duration)
        
        monitor.stop_monitoring()
        metrics = monitor.get_metrics()
        
        self.assertEqual(metrics['query_count'], 3)
        self.assertEqual(len(monitor.metrics.queries), 3)
    
    def test_orchestrator_full_workflow(self):
        """Test orchestrator managing complete test workflow."""
        orchestrator = PythonTestOrchestrator()
        analyzer = PythonQueryAnalyzer()
        
        # Simulate running multiple tests
        test_scenarios = [
            ('test_simple_query', ['SELECT * FROM users'], 'passed'),
            ('test_complex_query', [
                'SELECT * FROM posts JOIN users ON posts.user_id = users.id',
                'SELECT * FROM comments WHERE post_id IN (SELECT id FROM posts)'
            ], 'passed'),
            ('test_failed_query', ['DELETE FROM important_table'], 'failed'),
        ]
        
        for test_name, queries, status in test_scenarios:
            orchestrator.start_test(test_name)
            
            # Get the monitor for this test
            monitor = orchestrator.monitors.get(test_name)
            if monitor:
                for sql in queries:
                    analysis = analyzer.analyze_query(sql)
                    monitor.track_query(sql, 0.01)
            
            orchestrator.end_test(test_name, status)
        
        # Get summary
        summary = orchestrator.get_summary()
        
        self.assertEqual(summary['total_tests'], 3)
        self.assertEqual(summary['passed'], 2)
        self.assertEqual(summary['failed'], 1)
    
    def test_n_plus_one_detection_workflow(self):
        """Test N+1 query detection in a realistic workflow."""
        monitor = PythonPerformanceMonitor()
        engine = PythonMetricsEngine()
        
        monitor.start_monitoring()
        
        # Simulate N+1 query pattern
        monitor.track_query("SELECT * FROM users", 0.02)
        
        # Then multiple similar queries (N+1 pattern)
        for user_id in range(15):
            monitor.track_query(f"SELECT * FROM posts WHERE user_id = {user_id}", 0.005)
        
        monitor.stop_monitoring()
        
        # Detect N+1
        queries = monitor.metrics.queries
        result = engine.detect_n_plus_one(queries)
        
        self.assertTrue(result['detected'])
        self.assertEqual(len(result['suspicious_patterns']), 1)
        self.assertEqual(result['suspicious_patterns'][0]['count'], 15)
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.TRACEMALLOC_AVAILABLE', True)
    @patch('django_mercury.python_bindings.pure_python.psutil')
    @patch('django_mercury.python_bindings.pure_python.tracemalloc')
    def test_full_monitoring_with_dependencies(self, mock_tracemalloc, mock_psutil):
        """Test full monitoring with all optional dependencies available."""
        # Set up mocks
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 25.0
        mock_psutil.Process.return_value = mock_process
        
        mock_tracemalloc.is_tracing.return_value = False
        
        # Create two snapshots - initial and final
        initial_snapshot = Mock()
        final_snapshot = Mock()
        
        # The final snapshot compares to initial and shows 5MB difference
        mock_stat = Mock(size_diff=5 * 1024 * 1024)  # 5 MB
        final_snapshot.compare_to.return_value = [mock_stat]
        
        # take_snapshot is called twice: once in start_monitoring, once in stop_monitoring
        mock_tracemalloc.take_snapshot.side_effect = [initial_snapshot, final_snapshot]
        
        # Run monitoring
        with python_performance_monitor() as monitor:
            monitor.track_query("SELECT * FROM users", 0.01)
            monitor.track_cache(True)
            monitor.track_cache(False)
            time.sleep(0.001)
        
        metrics = monitor.get_metrics()
        
        # Check all metrics are collected
        self.assertGreater(metrics['response_time_ms'], 0)
        self.assertEqual(metrics['memory_usage_mb'], 5.0)
        self.assertEqual(metrics['peak_memory_mb'], 100.0)
        self.assertEqual(metrics['query_count'], 1)
        self.assertEqual(metrics['cache_hits'], 1)
        self.assertEqual(metrics['cache_misses'], 1)
        self.assertEqual(metrics['cpu_percent'], 25.0)
    
    @patch('django_mercury.python_bindings.pure_python.PSUTIL_AVAILABLE', False)
    @patch('django_mercury.python_bindings.pure_python.TRACEMALLOC_AVAILABLE', False)
    def test_fallback_without_dependencies(self):
        """Test that monitoring works without optional dependencies."""
        with python_performance_monitor() as monitor:
            monitor.track_query("SELECT * FROM users", 0.01)
            monitor.track_cache(True)
            time.sleep(0.001)
        
        metrics = monitor.get_metrics()
        
        # Basic metrics should still work
        self.assertGreater(metrics['response_time_ms'], 0)
        self.assertEqual(metrics['query_count'], 1)
        self.assertEqual(metrics['cache_hits'], 1)
        
        # Memory and CPU metrics will be default values
        self.assertEqual(metrics['memory_usage_mb'], 0.0)
        self.assertEqual(metrics['cpu_percent'], 0.0)
    
    def test_complex_sql_analysis_workflow(self):
        """Test analyzing complex SQL queries through the workflow."""
        analyzer = PythonQueryAnalyzer()
        engine = PythonMetricsEngine()
        
        complex_queries = [
            """
            SELECT u.name, COUNT(p.id) as post_count, AVG(c.rating) as avg_rating
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE u.created_at > '2023-01-01'
            GROUP BY u.id, u.name
            HAVING COUNT(p.id) > 5
            ORDER BY avg_rating DESC
            LIMIT 10
            """,
            """
            SELECT * FROM orders
            WHERE customer_id IN (
                SELECT id FROM customers
                WHERE country = 'USA'
                AND total_spent > (
                    SELECT AVG(total_spent) FROM customers
                )
            )
            """
        ]
        
        analyzed_queries = []
        for sql in complex_queries:
            analysis = analyzer.analyze_query(sql)
            analyzed_queries.append({
                'sql': sql,
                'duration_ms': 10 * analysis['estimated_complexity']
            })
        
        # Check for N+1 (shouldn't detect in this case)
        n_plus_one_result = engine.detect_n_plus_one(analyzed_queries)
        self.assertFalse(n_plus_one_result['detected'])
        
        # Add metrics
        for query_info in analyzed_queries:
            engine.add_metrics({
                'response_time_ms': query_info['duration_ms'],
                'query_count': 1
            })
        
        stats = engine.calculate_statistics()
        self.assertEqual(stats['count'], 2)
        self.assertGreater(stats['mean'], 0)
    
    def test_test_suite_simulation(self):
        """Simulate running a test suite with pure Python components."""
        orchestrator = PythonTestOrchestrator()
        
        # Simulate a test suite run
        test_suite = [
            ('test_user_creation', 0.05, 'passed', 3),
            ('test_user_authentication', 0.02, 'passed', 2),
            ('test_post_creation', 0.08, 'passed', 5),
            ('test_comment_spam_filter', 0.15, 'failed', 10),
            ('test_email_notification', 0.03, 'passed', 1),
        ]
        
        for test_name, duration, status, query_count in test_suite:
            orchestrator.start_test(test_name)
            
            monitor = orchestrator.monitors.get(test_name)
            if monitor:
                # Simulate queries
                for i in range(query_count):
                    monitor.track_query(f"Query {i} for {test_name}", duration / query_count)
                
                # Simulate cache usage
                monitor.track_cache(True)  # One hit
                monitor.track_cache(False)  # One miss
            
            # Simulate test duration
            time.sleep(0.001)
            
            orchestrator.end_test(test_name, status)
        
        summary = orchestrator.get_summary()
        
        self.assertEqual(summary['total_tests'], 5)
        self.assertEqual(summary['passed'], 4)
        self.assertEqual(summary['failed'], 1)
        self.assertGreater(summary['total_duration'], 0)
        self.assertGreater(summary['avg_response_time_ms'], 0)
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        monitor = PythonPerformanceMonitor()
        analyzer = PythonQueryAnalyzer()
        engine = PythonMetricsEngine()
        
        # Test with invalid inputs
        monitor.track_query("", 0)  # Empty query
        monitor.track_query(None, -1)  # None query, negative duration
        
        # Analyzer with malformed SQL
        result = analyzer.analyze_query("NOT VALID SQL AT ALL")
        self.assertEqual(result['type'], 'OTHER')
        
        # Engine with empty metrics
        engine.add_metrics({})
        stats = engine.calculate_statistics()
        # Should handle gracefully
        self.assertEqual(stats['count'], 1)
    
    def test_performance_comparison_workflow(self):
        """Test comparing performance across multiple runs."""
        engine = PythonMetricsEngine()
        
        # Simulate multiple runs of the same operation
        runs = [
            {'response_time_ms': 100.0, 'memory_usage_mb': 50.0},
            {'response_time_ms': 95.0, 'memory_usage_mb': 48.0},
            {'response_time_ms': 105.0, 'memory_usage_mb': 52.0},
            {'response_time_ms': 98.0, 'memory_usage_mb': 49.0},
            {'response_time_ms': 102.0, 'memory_usage_mb': 51.0},
        ]
        
        for metrics in runs:
            engine.add_metrics(metrics)
        
        stats = engine.calculate_statistics()
        
        # Check statistical analysis
        self.assertEqual(stats['count'], 5)
        self.assertAlmostEqual(stats['mean'], 100.0, delta=1.0)
        self.assertEqual(stats['min'], 95.0)
        self.assertEqual(stats['max'], 105.0)
        self.assertGreater(stats['std_dev'], 0)  # Should have some variance


if __name__ == '__main__':
    unittest.main()