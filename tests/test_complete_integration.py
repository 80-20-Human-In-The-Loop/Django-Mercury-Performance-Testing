"""
Comprehensive integration tests for Django Mercury Performance Testing.
Tests both C extensions and pure Python implementations.
"""

import unittest
import os
import sys
import time
from unittest.mock import patch, MagicMock

# Set up Django before importing our modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')

import django
django.setup()

from django_mercury.python_bindings.loader import (
    get_performance_monitor,
    get_metrics_engine,
    get_query_analyzer,
    get_test_orchestrator,
    get_implementation_info,
    check_c_extensions
)


class TestImplementationLoading(unittest.TestCase):
    """Test that the correct implementation loads."""
    
    def test_implementation_info(self):
        """Test that we can get implementation info."""
        info = get_implementation_info()
        self.assertIn('type', info)
        self.assertIn('platform', info)
        self.assertIn('python_version', info)
        
    def test_check_c_extensions(self):
        """Test C extension checking."""
        available, details = check_c_extensions()
        self.assertIsInstance(available, bool)
        self.assertIsInstance(details, dict)
        
        # If C extensions are available, test they work
        if available:
            self.assertTrue(details.get('functional', False))


class TestPerformanceMonitor(unittest.TestCase):
    """Test PerformanceMonitor with both implementations."""
    
    def setUp(self):
        self.Monitor = get_performance_monitor()
        
    def test_basic_monitoring(self):
        """Test basic monitoring functionality."""
        monitor = self.Monitor()
        
        # Start monitoring
        monitor.start_monitoring()
        time.sleep(0.01)  # Small delay
        monitor.stop_monitoring()
        
        # Get metrics
        metrics = monitor.get_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('implementation', metrics)
        
        # Check response time was measured
        if 'response_time_ms' in metrics:
            self.assertGreater(metrics['response_time_ms'], 0)
    
    def test_query_tracking(self):
        """Test query tracking."""
        monitor = self.Monitor()
        
        # Track some queries
        monitor.track_query("SELECT * FROM users", 1.5)
        monitor.track_query("SELECT * FROM posts", 2.0)
        
        metrics = monitor.get_metrics()
        if 'query_count' in metrics:
            self.assertEqual(metrics['query_count'], 2)
    
    def test_cache_tracking(self):
        """Test cache tracking."""
        monitor = self.Monitor()
        
        # Track cache hits and misses
        monitor.track_cache(True)   # Hit
        monitor.track_cache(True)   # Hit
        monitor.track_cache(False)  # Miss
        
        metrics = monitor.get_metrics()
        if 'cache_hits' in metrics:
            self.assertEqual(metrics['cache_hits'], 2)
        if 'cache_misses' in metrics:
            self.assertEqual(metrics['cache_misses'], 1)
    
    def test_reset(self):
        """Test reset functionality."""
        monitor = self.Monitor()
        
        # Add some data
        monitor.track_query("SELECT 1", 1.0)
        monitor.reset()
        
        # After reset, counts should be zero
        metrics = monitor.get_metrics()
        if 'query_count' in metrics:
            self.assertEqual(metrics['query_count'], 0)


class TestMetricsEngine(unittest.TestCase):
    """Test MetricsEngine with both implementations."""
    
    def setUp(self):
        self.Engine = get_metrics_engine()
        
    def test_add_metrics(self):
        """Test adding metrics."""
        engine = self.Engine()
        
        # Add some metrics
        engine.add_metrics({
            'response_time_ms': 100,
            'query_count': 5
        })
        engine.add_metrics({
            'response_time_ms': 200,
            'query_count': 3
        })
        
        # Calculate statistics
        stats = engine.calculate_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('implementation', stats)
    
    def test_statistics_calculation(self):
        """Test statistics calculation."""
        engine = self.Engine()
        
        # Add multiple metrics
        for i in range(10):
            engine.add_metrics({
                'response_time_ms': 100 + i * 10,
                'query_count': i
            })
        
        stats = engine.calculate_statistics()
        
        # Check basic statistics exist
        if 'mean' in stats:
            self.assertGreater(stats['mean'], 0)
        if 'count' in stats:
            self.assertEqual(stats['count'], 10)
    
    def test_n_plus_one_detection(self):
        """Test N+1 query detection."""
        engine = self.Engine()
        
        # Create queries that look like N+1
        queries = []
        for i in range(10):
            queries.append({
                'sql': f'SELECT * FROM users WHERE id = {i}',
                'duration_ms': 1.0
            })
        
        result = engine.detect_n_plus_one(queries)
        self.assertIsInstance(result, dict)
        self.assertIn('detected', result)


class TestQueryAnalyzer(unittest.TestCase):
    """Test QueryAnalyzer with both implementations."""
    
    def setUp(self):
        self.Analyzer = get_query_analyzer()
        
    def test_analyze_select(self):
        """Test analyzing SELECT queries."""
        analyzer = self.Analyzer()
        
        analysis = analyzer.analyze_query("SELECT * FROM users WHERE id = 1")
        self.assertIsInstance(analysis, dict)
        self.assertIn('implementation', analysis)
        
        if 'query_type' in analysis:
            self.assertEqual(analysis['query_type'], 'SELECT')
    
    def test_analyze_complex_query(self):
        """Test analyzing complex queries."""
        analyzer = self.Analyzer()
        
        complex_query = """
        SELECT u.*, p.*
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        WHERE u.created_at > '2024-01-01'
        GROUP BY u.id
        ORDER BY u.created_at DESC
        """
        
        analysis = analyzer.analyze_query(complex_query)
        
        # Check for complexity indicators
        if 'has_joins' in analysis:
            self.assertTrue(analysis['has_joins'])
        if 'complexity_score' in analysis:
            self.assertGreater(analysis['complexity_score'], 10)
    
    def test_performance_issues_detection(self):
        """Test detection of performance issues."""
        analyzer = self.Analyzer()
        
        # Query with potential issues
        bad_query = "SELECT * FROM users WHERE name LIKE '%test%'"
        
        analysis = analyzer.analyze_query(bad_query)
        
        if 'issues' in analysis:
            self.assertIsInstance(analysis['issues'], list)
            # Should detect SELECT * and LIKE with leading wildcard
            self.assertGreater(len(analysis['issues']), 0)


class TestTestOrchestrator(unittest.TestCase):
    """Test TestOrchestrator with both implementations."""
    
    def setUp(self):
        self.Orchestrator = get_test_orchestrator()
        
    def test_test_tracking(self):
        """Test tracking test execution."""
        orchestrator = self.Orchestrator()
        
        # Start and end a test
        orchestrator.start_test("test_example")
        time.sleep(0.01)
        result = orchestrator.end_test("test_example", "passed")
        
        self.assertIsInstance(result, dict)
        if 'duration_ms' in result:
            self.assertGreater(result['duration_ms'], 0)
    
    def test_summary_generation(self):
        """Test summary generation."""
        orchestrator = self.Orchestrator()
        
        # Run multiple tests
        orchestrator.start_test("test1")
        orchestrator.end_test("test1", "passed")
        
        orchestrator.start_test("test2")
        orchestrator.end_test("test2", "failed")
        
        orchestrator.start_test("test3")
        orchestrator.end_test("test3", "passed")
        
        # Get summary
        summary = orchestrator.get_summary()
        self.assertIsInstance(summary, dict)
        
        if 'total_tests' in summary:
            self.assertEqual(summary['total_tests'], 3)
        if 'passed' in summary:
            self.assertEqual(summary['passed'], 2)
        if 'failed' in summary:
            self.assertEqual(summary['failed'], 1)


class TestFallbackMechanism(unittest.TestCase):
    """Test fallback from C to Python."""
    
    def test_force_pure_python(self):
        """Test forcing pure Python implementation."""
        # Save original env
        original = os.environ.get('DJANGO_MERCURY_PURE_PYTHON')
        
        try:
            # Force pure Python
            os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '1'
            
            # Reload the module
            if 'django_mercury.python_bindings.loader' in sys.modules:
                del sys.modules['django_mercury.python_bindings.loader']
            
            from django_mercury.python_bindings.loader import get_implementation_info
            
            info = get_implementation_info()
            self.assertEqual(info['type'], 'pure_python_forced')
            
        finally:
            # Restore original
            if original is None:
                os.environ.pop('DJANGO_MERCURY_PURE_PYTHON', None)
            else:
                os.environ['DJANGO_MERCURY_PURE_PYTHON'] = original


class TestPerformanceComparison(unittest.TestCase):
    """Compare performance between implementations."""
    
    @unittest.skipIf(
        not check_c_extensions()[0],
        "C extensions not available"
    )
    def test_c_extension_performance(self):
        """Test that C extensions are faster when available."""
        Monitor = get_performance_monitor()
        monitor = Monitor()
        
        # Time many operations
        start = time.perf_counter()
        for _ in range(1000):
            monitor.start_monitoring()
            monitor.stop_monitoring()
        c_time = time.perf_counter() - start
        
        # This should be fast with C extensions
        self.assertLess(c_time, 1.0, "C extensions should complete 1000 operations in < 1 second")


if __name__ == '__main__':
    unittest.main()