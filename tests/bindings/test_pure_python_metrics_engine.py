"""
Comprehensive tests for PythonMetricsEngine in pure_python.py
Tests metrics aggregation and analysis without C extensions.
"""

import unittest
from unittest.mock import Mock, patch
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from django_mercury.python_bindings.pure_python import PythonMetricsEngine


class TestPythonMetricsEngine(unittest.TestCase):
    """Test the PythonMetricsEngine class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = PythonMetricsEngine()
    
    def test_initialization(self) -> None:
        """Test engine initializes correctly."""
        self.assertEqual(self.engine.metrics_history, [])
        self.assertEqual(self.engine.aggregated_metrics, {})
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    def test_add_metrics(self, mock_time) -> None:
        """Test adding metrics to history."""
        mock_time.return_value = 1234567890.0
        
        metrics = {
            'response_time_ms': 100.0,
            'query_count': 5,
            'memory_usage_mb': 50.0
        }
        
        self.engine.add_metrics(metrics)
        
        self.assertEqual(len(self.engine.metrics_history), 1)
        entry = self.engine.metrics_history[0]
        self.assertEqual(entry['timestamp'], 1234567890.0)
        self.assertEqual(entry['metrics'], metrics)
    
    def test_add_multiple_metrics(self) -> None:
        """Test adding multiple metrics entries."""
        metrics1 = {'response_time_ms': 100.0, 'query_count': 5}
        metrics2 = {'response_time_ms': 150.0, 'query_count': 8}
        metrics3 = {'response_time_ms': 75.0, 'query_count': 3}
        
        self.engine.add_metrics(metrics1)
        self.engine.add_metrics(metrics2)
        self.engine.add_metrics(metrics3)
        
        self.assertEqual(len(self.engine.metrics_history), 3)
    
    def test_calculate_statistics_empty(self) -> None:
        """Test statistics calculation with no metrics."""
        stats = self.engine.calculate_statistics()
        
        self.assertEqual(stats['count'], 0)
        self.assertEqual(stats['mean'], 0.0)
        self.assertEqual(stats['min'], 0.0)
        self.assertEqual(stats['max'], 0.0)
        self.assertEqual(stats['std_dev'], 0.0)
        self.assertEqual(stats['total_queries'], 0)
        self.assertEqual(stats['implementation'], 'pure_python')
    
    def test_calculate_statistics_single_metric(self) -> None:
        """Test statistics with single metric entry."""
        self.engine.add_metrics({'response_time_ms': 100.0, 'query_count': 5})
        
        stats = self.engine.calculate_statistics()
        
        self.assertEqual(stats['count'], 1)
        self.assertEqual(stats['mean'], 100.0)
        self.assertEqual(stats['min'], 100.0)
        self.assertEqual(stats['max'], 100.0)
        self.assertEqual(stats['std_dev'], 0.0)  # No variance with single value
        self.assertEqual(stats['total_queries'], 5)
    
    def test_calculate_statistics_multiple_metrics(self) -> None:
        """Test statistics with multiple metric entries."""
        self.engine.add_metrics({'response_time_ms': 100.0, 'query_count': 5})
        self.engine.add_metrics({'response_time_ms': 200.0, 'query_count': 10})
        self.engine.add_metrics({'response_time_ms': 150.0, 'query_count': 7})
        
        stats = self.engine.calculate_statistics()
        
        self.assertEqual(stats['count'], 3)
        self.assertEqual(stats['mean'], 150.0)  # (100 + 200 + 150) / 3
        self.assertEqual(stats['min'], 100.0)
        self.assertEqual(stats['max'], 200.0)
        self.assertAlmostEqual(stats['std_dev'], 40.82, places=1)  # Standard deviation
        self.assertEqual(stats['total_queries'], 22)  # 5 + 10 + 7
    
    def test_calculate_statistics_missing_fields(self) -> None:
        """Test statistics when some metrics don't have all fields."""
        self.engine.add_metrics({'response_time_ms': 100.0})  # No query_count
        self.engine.add_metrics({'query_count': 5})  # No response_time_ms
        self.engine.add_metrics({'response_time_ms': 200.0, 'query_count': 10})
        
        stats = self.engine.calculate_statistics()
        
        # Should handle missing fields gracefully
        self.assertEqual(stats['count'], 3)
        self.assertEqual(stats['mean'], 100.0)  # (100 + 0 + 200) / 3
        self.assertEqual(stats['total_queries'], 15)  # 0 + 5 + 10
    
    def test_detect_n_plus_one_empty(self) -> None:
        """Test N+1 detection with no queries."""
        result = self.engine.detect_n_plus_one([])
        
        self.assertFalse(result['detected'])
        self.assertEqual(result['count'], 0)
    
    def test_detect_n_plus_one_no_pattern(self) -> None:
        """Test N+1 detection with different queries."""
        queries = [
            {'sql': 'SELECT * FROM users', 'duration_ms': 10},
            {'sql': 'SELECT * FROM posts', 'duration_ms': 15},
            {'sql': 'UPDATE users SET active=1', 'duration_ms': 5},
        ]
        
        result = self.engine.detect_n_plus_one(queries)
        
        self.assertFalse(result['detected'])
        self.assertEqual(result['total_patterns'], 3)
    
    def test_detect_n_plus_one_detected(self) -> None:
        """Test N+1 detection with repeated pattern."""
        # Create 15 similar queries (above threshold of 10)
        queries = []
        for i in range(15):
            queries.append({
                'sql': f'SELECT * FROM posts WHERE user_id = {i}',
                'duration_ms': 5
            })
        
        result = self.engine.detect_n_plus_one(queries)
        
        self.assertTrue(result['detected'])
        self.assertEqual(len(result['suspicious_patterns']), 1)
        
        pattern = result['suspicious_patterns'][0]
        self.assertEqual(pattern['count'], 15)
        self.assertEqual(pattern['total_time_ms'], 75)  # 15 * 5
    
    def test_detect_n_plus_one_multiple_patterns(self) -> None:
        """Test N+1 detection with multiple suspicious patterns."""
        queries = []
        
        # Pattern 1: 12 similar user queries
        for i in range(12):
            queries.append({
                'sql': f'SELECT * FROM users WHERE id = {i}',
                'duration_ms': 3
            })
        
        # Pattern 2: 11 similar post queries
        for i in range(11):
            queries.append({
                'sql': f'SELECT * FROM posts WHERE author_id = {i}',
                'duration_ms': 4
            })
        
        # Some other queries
        queries.append({'sql': 'SELECT COUNT(*) FROM users', 'duration_ms': 2})
        
        result = self.engine.detect_n_plus_one(queries)
        
        self.assertTrue(result['detected'])
        self.assertEqual(len(result['suspicious_patterns']), 2)
    
    def test_extract_pattern_numbers(self) -> None:
        """Test pattern extraction removes numbers."""
        sql = "SELECT * FROM users WHERE id = 123 AND age > 25"
        pattern = self.engine._extract_pattern(sql)
        
        self.assertEqual(pattern, "SELECT * FROM users WHERE id = ? AND age > ?")
    
    def test_extract_pattern_single_quotes(self) -> None:
        """Test pattern extraction removes single-quoted strings."""
        sql = "SELECT * FROM users WHERE name = 'John Doe' AND status = 'active'"
        pattern = self.engine._extract_pattern(sql)
        
        self.assertEqual(pattern, "SELECT * FROM users WHERE name = ? AND status = ?")
    
    def test_extract_pattern_double_quotes(self) -> None:
        """Test pattern extraction removes double-quoted strings."""
        sql = 'SELECT * FROM users WHERE name = "John Doe" AND city = "New York"'
        pattern = self.engine._extract_pattern(sql)
        
        self.assertEqual(pattern, 'SELECT * FROM users WHERE name = ? AND city = ?')
    
    def test_extract_pattern_mixed(self) -> None:
        """Test pattern extraction with mixed values."""
        sql = "INSERT INTO logs (user_id, message, timestamp) VALUES (123, 'User logged in', 1234567890)"
        pattern = self.engine._extract_pattern(sql)
        
        self.assertEqual(
            pattern,
            "INSERT INTO logs (user_id, message, timestamp) VALUES (?, ?, ?)"
        )
    
    def test_detect_n_plus_one_below_threshold(self) -> None:
        """Test N+1 detection with repeated pattern below threshold."""
        # Create 9 similar queries (below threshold of 10)
        queries = []
        for i in range(9):
            queries.append({
                'sql': f'SELECT * FROM posts WHERE user_id = {i}',
                'duration_ms': 5
            })
        
        result = self.engine.detect_n_plus_one(queries)
        
        self.assertFalse(result['detected'])
        self.assertEqual(result['total_patterns'], 1)
    
    def test_detect_n_plus_one_pattern_truncation(self) -> None:
        """Test that long patterns are truncated in results."""
        # Create a very long SQL query
        long_sql = "SELECT " + ", ".join([f"column_{i}" for i in range(50)]) + " FROM very_long_table_name WHERE complex_condition = "
        
        queries = []
        for i in range(15):
            queries.append({
                'sql': long_sql + str(i),
                'duration_ms': 10
            })
        
        result = self.engine.detect_n_plus_one(queries)
        
        self.assertTrue(result['detected'])
        pattern = result['suspicious_patterns'][0]
        # Pattern should be truncated to 100 characters
        self.assertLessEqual(len(pattern['pattern']), 100)
    
    def test_statistics_with_zero_response_times(self) -> None:
        """Test statistics calculation handles zero values correctly."""
        self.engine.add_metrics({'response_time_ms': 0.0, 'query_count': 1})
        self.engine.add_metrics({'response_time_ms': 0.0, 'query_count': 2})
        self.engine.add_metrics({'response_time_ms': 0.0, 'query_count': 3})
        
        stats = self.engine.calculate_statistics()
        
        self.assertEqual(stats['count'], 3)
        self.assertEqual(stats['mean'], 0.0)
        self.assertEqual(stats['min'], 0.0)
        self.assertEqual(stats['max'], 0.0)
        self.assertEqual(stats['std_dev'], 0.0)
        self.assertEqual(stats['total_queries'], 6)
    
    def test_statistics_with_large_variance(self) -> None:
        """Test statistics with large variance in response times."""
        self.engine.add_metrics({'response_time_ms': 1.0})
        self.engine.add_metrics({'response_time_ms': 1000.0})
        self.engine.add_metrics({'response_time_ms': 2000.0})
        
        stats = self.engine.calculate_statistics()
        
        self.assertEqual(stats['count'], 3)
        self.assertAlmostEqual(stats['mean'], 1000.33, places=1)  # (1 + 1000 + 2000) / 3
        self.assertEqual(stats['min'], 1.0)
        self.assertEqual(stats['max'], 2000.0)
        self.assertGreater(stats['std_dev'], 800)  # Large standard deviation


if __name__ == '__main__':
    unittest.main()