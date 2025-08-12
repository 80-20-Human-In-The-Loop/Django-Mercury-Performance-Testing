"""
Test suite for Django hooks module.

This module tests Django-specific performance monitoring hooks including
query tracking, cache tracking, and the performance context manager.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import threading
import time
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

from django_mercury.python_bindings.django_hooks import (
    QueryInfo,
    DjangoQueryTracker,
    DjangoCacheTracker,
    PerformanceContextManager,
    DJANGO_AVAILABLE
)


class TestQueryInfo(unittest.TestCase):
    """Test QueryInfo dataclass functionality."""
    
    def test_query_info_creation_minimal(self) -> None:
        """Test creating a QueryInfo instance with minimal parameters."""
        query = QueryInfo(sql="SELECT * FROM users", time=0.05)
        
        self.assertEqual(query.sql, "SELECT * FROM users")
        self.assertEqual(query.time, 0.05)
        self.assertIsNone(query.params)
        self.assertEqual(query.alias, 'default')
    
    def test_query_info_creation_complete(self) -> None:
        """Test creating a QueryInfo instance with all parameters."""
        params = ('user1', 123)
        query = QueryInfo(
            sql="SELECT * FROM users WHERE name = %s AND id = %s",
            time=0.15,
            params=params,
            alias='secondary'
        )
        
        self.assertEqual(query.sql, "SELECT * FROM users WHERE name = %s AND id = %s")
        self.assertEqual(query.time, 0.15)
        self.assertEqual(query.params, params)
        self.assertEqual(query.alias, 'secondary')
    
    def test_query_info_equality(self) -> None:
        """Test QueryInfo equality comparison."""
        query1 = QueryInfo("SELECT * FROM users", 0.05, ('param1',), 'default')
        query2 = QueryInfo("SELECT * FROM users", 0.05, ('param1',), 'default')
        query3 = QueryInfo("SELECT * FROM posts", 0.05, ('param1',), 'default')
        
        self.assertEqual(query1, query2)
        self.assertNotEqual(query1, query3)
    
    def test_query_info_with_none_params(self) -> None:
        """Test QueryInfo with None parameters."""
        query = QueryInfo("SELECT 1", 0.01, None, 'test')
        
        self.assertIsNone(query.params)
        self.assertEqual(query.alias, 'test')


class TestDjangoQueryTracker(unittest.TestCase):
    """Test DjangoQueryTracker functionality."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.tracker = DjangoQueryTracker()
    
    def test_tracker_initialization(self) -> None:
        """Test DjangoQueryTracker initialization."""
        self.assertEqual(len(self.tracker.queries), 0)
        self.assertEqual(self.tracker.query_count, 0)
        self.assertEqual(self.tracker.total_time, 0.0)
        self.assertFalse(self.tracker.is_active)
        self.assertIsNone(self.tracker._original_execute)
        self.assertIsNone(self.tracker._original_executemany)
    
    @patch('django_mercury.python_bindings.django_hooks.DJANGO_AVAILABLE', True)
    @patch('django_mercury.python_bindings.django_hooks.django')
    def test_start_tracking(self, mock_django) -> None:
        """Test starting query tracking."""
        # Mock Django's CursorWrapper
        mock_cursor_wrapper = Mock()
        mock_django.db.backends.utils.CursorWrapper = mock_cursor_wrapper
        
        self.tracker.start()
        
        self.assertTrue(self.tracker.is_active)
        self.assertEqual(len(self.tracker.queries), 0)
        self.assertEqual(self.tracker.query_count, 0)
        self.assertEqual(self.tracker.total_time, 0.0)
    
    @patch('django_mercury.python_bindings.django_hooks.DJANGO_AVAILABLE', False)
    def test_start_tracking_django_unavailable(self) -> None:
        """Test starting tracking when Django is not available."""
        self.tracker.start()
        
        # Should not activate when Django is unavailable
        self.assertFalse(self.tracker.is_active)
    
    @patch('django_mercury.python_bindings.django_hooks.DJANGO_AVAILABLE', True)
    @patch('django_mercury.python_bindings.django_hooks.django')
    def test_stop_tracking(self, mock_django) -> None:
        """Test stopping query tracking."""
        # Mock Django's CursorWrapper
        mock_cursor_wrapper = Mock()
        mock_cursor_wrapper._original_execute = Mock()
        mock_cursor_wrapper._original_executemany = Mock()
        mock_django.db.backends.utils.CursorWrapper = mock_cursor_wrapper
        
        # Start tracking first
        self.tracker.start()
        self.assertTrue(self.tracker.is_active)
        
        # Stop tracking
        self.tracker.stop()
        self.assertFalse(self.tracker.is_active)
    
    def test_stop_tracking_when_not_active(self) -> None:
        """Test stopping tracking when not active."""
        self.assertFalse(self.tracker.is_active)
        self.tracker.stop()  # Should not raise any exception
        self.assertFalse(self.tracker.is_active)
    
    def test_record_query_when_active(self) -> None:
        """Test recording queries when tracking is active."""
        self.tracker.is_active = True
        
        sql = "SELECT * FROM users WHERE id = %s"
        params = (1,)
        time_taken = 0.05
        alias = 'primary'
        
        self.tracker.record_query(sql, params, time_taken, alias)
        
        self.assertEqual(len(self.tracker.queries), 1)
        self.assertEqual(self.tracker.query_count, 1)
        self.assertEqual(self.tracker.total_time, time_taken)
        
        query = self.tracker.queries[0]
        self.assertEqual(query.sql, sql)
        self.assertEqual(query.params, params)
        self.assertEqual(query.time, time_taken)
        self.assertEqual(query.alias, alias)
    
    def test_record_query_when_not_active(self) -> None:
        """Test recording queries when tracking is not active."""
        self.tracker.is_active = False
        
        self.tracker.record_query("SELECT 1", None, 0.01)
        
        self.assertEqual(len(self.tracker.queries), 0)
        self.assertEqual(self.tracker.query_count, 0)
        self.assertEqual(self.tracker.total_time, 0.0)
    
    def test_record_multiple_queries(self) -> None:
        """Test recording multiple queries."""
        self.tracker.is_active = True
        
        queries_data = [
            ("SELECT * FROM users", None, 0.05, 'default'),
            ("SELECT * FROM posts WHERE user_id = %s", (1,), 0.03, 'default'),
            ("INSERT INTO logs (message) VALUES (%s)", ('test',), 0.02, 'default')
        ]
        
        for sql, params, time_taken, alias in queries_data:
            self.tracker.record_query(sql, params, time_taken, alias)
        
        self.assertEqual(len(self.tracker.queries), 3)
        self.assertEqual(self.tracker.query_count, 3)
        self.assertEqual(self.tracker.total_time, 0.10)
    
    @patch('django_mercury.python_bindings.django_hooks.C_EXTENSIONS_AVAILABLE', False)
    @patch('django_mercury.python_bindings.django_hooks.ctypes.CDLL')
    @patch('django_mercury.python_bindings.django_hooks.Path.exists')
    def test_record_query_with_c_library(self, mock_exists, mock_cdll) -> None:
        """Test recording query with legacy C library integration when new extensions unavailable."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        
        self.tracker.is_active = True
        self.tracker.record_query("SELECT 1", None, 0.01)
        
        mock_lib.increment_query_count.assert_called_once()
    
    @patch('django_mercury.python_bindings.django_hooks.c_extensions')
    def test_record_query_with_new_c_extensions(self, mock_c_extensions) -> None:
        """Test recording query with new C extension integration."""
        # Runtime check for pure Python mode
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
            self.skipTest("Pure Python mode - C extensions not available")
        
        # Mock the C extension functions
        mock_query_analyzer = Mock()
        mock_metrics_engine = Mock()
        mock_c_extensions.query_analyzer = mock_query_analyzer
        mock_c_extensions.metrics_engine = mock_metrics_engine
        
        self.tracker.is_active = True
        self.tracker.record_query("SELECT 1", None, 0.01)
        
        # Verify C extension functions were called
        mock_query_analyzer.analyze_query.assert_called_once()
        mock_metrics_engine.increment_query_count.assert_called_once()
        
        # Verify Python fallback still works
        self.assertEqual(len(self.tracker.queries), 1)
    
    @patch('django_mercury.python_bindings.django_hooks.ctypes.CDLL')
    @patch('django_mercury.python_bindings.django_hooks.Path.exists')
    def test_record_query_c_library_exception(self, mock_exists, mock_cdll) -> None:
        """Test recording query when C library raises exception."""
        mock_exists.return_value = True
        mock_cdll.side_effect = Exception("C library error")
        
        self.tracker.is_active = True
        
        # Should not raise exception even if C library fails
        self.tracker.record_query("SELECT 1", None, 0.01)
        
        self.assertEqual(len(self.tracker.queries), 1)
    
    def test_normalize_query_with_numbers(self) -> None:
        """Test query normalization with numeric literals."""
        sql = "SELECT * FROM users WHERE id = 123 AND age > 25"
        normalized = self.tracker._normalize_query(sql)
        expected = "SELECT * FROM users WHERE id = ? AND age > ?"
        
        self.assertEqual(normalized, expected)
    
    def test_normalize_query_with_strings(self) -> None:
        """Test query normalization with string literals."""
        sql = "SELECT * FROM users WHERE name = 'John' AND city = \"New York\""
        normalized = self.tracker._normalize_query(sql)
        expected = "SELECT * FROM users WHERE name = ? AND city = ?"
        
        self.assertEqual(normalized, expected)
    
    def test_normalize_query_mixed_literals(self) -> None:
        """Test query normalization with mixed literal types."""
        sql = "SELECT * FROM orders WHERE total > 100.50 AND status = 'active'"
        normalized = self.tracker._normalize_query(sql)
        expected = "SELECT * FROM orders WHERE total > ? AND status = ?"
        
        self.assertEqual(normalized, expected)
    
    def test_get_duplicate_queries_none(self) -> None:
        """Test getting duplicate queries when none exist."""
        self.tracker.is_active = True
        
        # Add unique queries
        self.tracker.record_query("SELECT * FROM users", None, 0.01)
        self.tracker.record_query("SELECT * FROM posts", None, 0.02)
        
        duplicates = self.tracker.get_duplicate_queries()
        self.assertEqual(len(duplicates), 0)
    
    def test_get_duplicate_queries_found(self) -> None:
        """Test getting duplicate queries when they exist."""
        self.tracker.is_active = True
        
        # Add duplicate queries with different parameters
        self.tracker.record_query("SELECT * FROM users WHERE id = 1", None, 0.01)
        self.tracker.record_query("SELECT * FROM users WHERE id = 2", None, 0.01)
        self.tracker.record_query("SELECT * FROM users WHERE id = 3", None, 0.01)
        
        duplicates = self.tracker.get_duplicate_queries()
        self.assertEqual(len(duplicates), 1)
        
        # Should have normalized the query
        normalized_key = "SELECT * FROM users WHERE id = ?"
        self.assertIn(normalized_key, duplicates)
        self.assertEqual(len(duplicates[normalized_key]), 3)
    
    def test_detect_n_plus_one_no_pattern(self) -> None:
        """Test N+1 detection when no pattern exists."""
        self.tracker.is_active = True
        
        # Reset C extension state if available
        try:
            from django_mercury.python_bindings.c_bindings import c_extensions
            if c_extensions.query_analyzer:
                c_extensions.query_analyzer.reset_query_analyzer()
        except:
            pass
        
        # Add few unique queries
        self.tracker.record_query("SELECT * FROM users", None, 0.01)
        self.tracker.record_query("SELECT * FROM posts", None, 0.02)
        
        patterns = self.tracker.detect_n_plus_one()
        self.assertEqual(len(patterns), 0)
    
    def test_detect_n_plus_one_pattern_found(self) -> None:
        """Test N+1 detection when pattern exists."""
        self.tracker.is_active = True
        
        # Add queries that form an N+1 pattern
        for i in range(5):
            self.tracker.record_query(f"SELECT * FROM profiles WHERE user_id = {i}", None, 0.01)
        
        patterns = self.tracker.detect_n_plus_one()
        self.assertEqual(len(patterns), 1)
        # Accept both C extension format and Python fallback format
        self.assertTrue(
            "N+1 Pattern Detected:" in patterns[0] or  # C extension format
            "Potential N+1" in patterns[0]  # Python fallback format
        )
    
    def test_get_slow_queries_none(self) -> None:
        """Test getting slow queries when none exist."""
        self.tracker.is_active = True
        
        # Add fast queries
        self.tracker.record_query("SELECT 1", None, 0.05)  # 50ms
        self.tracker.record_query("SELECT 2", None, 0.08)  # 80ms
        
        slow_queries = self.tracker.get_slow_queries(100.0)  # 100ms threshold
        self.assertEqual(len(slow_queries), 0)
    
    def test_get_slow_queries_found(self) -> None:
        """Test getting slow queries when they exist."""
        self.tracker.is_active = True
        
        # Add queries with different speeds
        self.tracker.record_query("SELECT 1", None, 0.05)   # 50ms - fast
        self.tracker.record_query("SELECT 2", None, 0.15)   # 150ms - slow
        self.tracker.record_query("SELECT 3", None, 0.20)   # 200ms - slow
        
        slow_queries = self.tracker.get_slow_queries(100.0)  # 100ms threshold
        self.assertEqual(len(slow_queries), 2)
        self.assertEqual(slow_queries[0].time, 0.15)
        self.assertEqual(slow_queries[1].time, 0.20)
    
    def test_get_slow_queries_custom_threshold(self) -> None:
        """Test getting slow queries with custom threshold."""
        self.tracker.is_active = True
        
        self.tracker.record_query("SELECT 1", None, 0.03)   # 30ms
        self.tracker.record_query("SELECT 2", None, 0.06)   # 60ms
        
        # Very low threshold
        slow_queries = self.tracker.get_slow_queries(50.0)   # 50ms threshold
        self.assertEqual(len(slow_queries), 1)
        self.assertEqual(slow_queries[0].time, 0.06)
    
    def test_get_query_summary_empty(self) -> None:
        """Test getting query summary when no queries exist."""
        summary = self.tracker.get_query_summary()
        
        expected = {
            'total_queries': 0, 'total_time': 0.0, 'avg_time': 0.0,
            'slow_queries': 0, 'duplicate_groups': 0, 'n_plus_one_patterns': []
        }
        self.assertEqual(summary, expected)
    
    def test_get_query_summary_with_data(self) -> None:
        """Test getting query summary with query data."""
        self.tracker.is_active = True
        
        # Add various queries
        self.tracker.record_query("SELECT * FROM users WHERE id = 1", None, 0.05)
        self.tracker.record_query("SELECT * FROM users WHERE id = 2", None, 0.03)
        self.tracker.record_query("SELECT * FROM users WHERE id = 3", None, 0.04)
        self.tracker.record_query("SELECT * FROM posts", None, 0.15)  # Slow query
        
        summary = self.tracker.get_query_summary()
        
        self.assertEqual(summary['total_queries'], 4)
        self.assertEqual(summary['total_time'], 0.27)
        self.assertEqual(summary['avg_time'], 0.0675)
        self.assertEqual(summary['max_time'], 0.15)
        self.assertEqual(summary['min_time'], 0.03)
        self.assertEqual(summary['slow_queries'], 1)  # One query > 100ms
        self.assertEqual(summary['duplicate_groups'], 1)  # Users queries are duplicates
        # With C extensions, N+1 detection may trigger with fewer queries
        # Accept either 0 (Python fallback: >3 queries needed) or 1 (C extension: may detect with 3)
        self.assertIn(len(summary['n_plus_one_patterns']), [0, 1])


class TestDjangoCacheTracker(unittest.TestCase):
    """Test DjangoCacheTracker functionality."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.tracker = DjangoCacheTracker()
    
    def test_tracker_initialization(self) -> None:
        """Test DjangoCacheTracker initialization."""
        self.assertEqual(len(self.tracker.operations), 0)
        self.assertEqual(self.tracker.hits, 0)
        self.assertEqual(self.tracker.misses, 0)
        self.assertEqual(self.tracker.sets, 0)
        self.assertEqual(self.tracker.deletes, 0)
        self.assertFalse(self.tracker.is_active)
    
    @patch('django_mercury.python_bindings.django_hooks.DJANGO_AVAILABLE', True)
    def test_start_tracking(self) -> None:
        """Test starting cache tracking."""
        self.tracker.start()
        
        self.assertTrue(self.tracker.is_active)
        self.assertEqual(len(self.tracker.operations), 0)
        self.assertEqual(self.tracker.hits, 0)
        self.assertEqual(self.tracker.misses, 0)
        self.assertEqual(self.tracker.sets, 0)
        self.assertEqual(self.tracker.deletes, 0)
    
    @patch('django_mercury.python_bindings.django_hooks.DJANGO_AVAILABLE', False)
    def test_start_tracking_django_unavailable(self) -> None:
        """Test starting tracking when Django is not available."""
        self.tracker.start()
        
        # Should not activate when Django is unavailable
        self.assertFalse(self.tracker.is_active)
    
    def test_stop_tracking(self) -> None:
        """Test stopping cache tracking."""
        self.tracker.is_active = True
        self.tracker.stop()
        
        self.assertFalse(self.tracker.is_active)
    
    def test_stop_tracking_when_not_active(self) -> None:
        """Test stopping tracking when not active."""
        self.assertFalse(self.tracker.is_active)
        self.tracker.stop()  # Should not raise any exception
        self.assertFalse(self.tracker.is_active)
    
    def test_record_cache_hit(self) -> None:
        """Test recording cache hit operation."""
        self.tracker.is_active = True
        
        self.tracker.record_cache_operation('hit', 'user:123', 0.001)
        
        self.assertEqual(len(self.tracker.operations), 1)
        self.assertEqual(self.tracker.hits, 1)
        self.assertEqual(self.tracker.misses, 0)
        
        operation = self.tracker.operations[0]
        self.assertEqual(operation['operation'], 'hit')
        self.assertEqual(operation['key'], 'user:123')
        self.assertEqual(operation['time'], 0.001)
    
    def test_record_cache_miss(self) -> None:
        """Test recording cache miss operation."""
        self.tracker.is_active = True
        
        self.tracker.record_cache_operation('miss', 'user:456', 0.002)
        
        self.assertEqual(len(self.tracker.operations), 1)
        self.assertEqual(self.tracker.hits, 0)
        self.assertEqual(self.tracker.misses, 1)
    
    def test_record_cache_set(self) -> None:
        """Test recording cache set operation."""
        self.tracker.is_active = True
        
        self.tracker.record_cache_operation('set', 'user:789', 0.003)
        
        self.assertEqual(len(self.tracker.operations), 1)
        self.assertEqual(self.tracker.sets, 1)
    
    def test_record_cache_delete(self) -> None:
        """Test recording cache delete operation."""
        self.tracker.is_active = True
        
        self.tracker.record_cache_operation('delete', 'user:000', 0.001)
        
        self.assertEqual(len(self.tracker.operations), 1)
        self.assertEqual(self.tracker.deletes, 1)
    
    def test_record_operation_when_not_active(self) -> None:
        """Test recording operations when tracking is not active."""
        self.tracker.is_active = False
        
        self.tracker.record_cache_operation('hit', 'test', 0.001)
        
        self.assertEqual(len(self.tracker.operations), 0)
        self.assertEqual(self.tracker.hits, 0)
    
    @patch('django_mercury.python_bindings.django_hooks.ctypes.CDLL')
    @patch('django_mercury.python_bindings.django_hooks.Path.exists')
    def test_update_c_counter_hit(self, mock_exists, mock_cdll) -> None:
        """Test updating C counter for cache hit."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        
        self.tracker.is_active = True
        self.tracker.record_cache_operation('hit', 'test', 0.001)
        
        mock_lib.increment_cache_hits.assert_called_once()
    
    @patch('django_mercury.python_bindings.django_hooks.ctypes.CDLL')
    @patch('django_mercury.python_bindings.django_hooks.Path.exists')
    def test_update_c_counter_miss(self, mock_exists, mock_cdll) -> None:
        """Test updating C counter for cache miss."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        
        self.tracker.is_active = True
        self.tracker.record_cache_operation('miss', 'test', 0.001)
        
        mock_lib.increment_cache_misses.assert_called_once()
    
    @patch('django_mercury.python_bindings.django_hooks.ctypes.CDLL')
    @patch('django_mercury.python_bindings.django_hooks.Path.exists')
    def test_update_c_counter_exception(self, mock_exists, mock_cdll) -> None:
        """Test C counter update when exception occurs."""
        mock_exists.return_value = True
        mock_cdll.side_effect = Exception("C library error")
        
        self.tracker.is_active = True
        
        # Should not raise exception even if C library fails
        self.tracker.record_cache_operation('hit', 'test', 0.001)
        
        self.assertEqual(self.tracker.hits, 1)
    
    def test_get_cache_summary_empty(self) -> None:
        """Test getting cache summary when no operations exist."""
        summary = self.tracker.get_cache_summary()
        
        expected = {
            'total_operations': 0,
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'hit_ratio': 0.0,
            'total_gets': 0
        }
        self.assertEqual(summary, expected)
    
    def test_get_cache_summary_with_data(self) -> None:
        """Test getting cache summary with operation data."""
        self.tracker.is_active = True
        
        # Record various operations
        self.tracker.record_cache_operation('hit', 'key1', 0.001)
        self.tracker.record_cache_operation('hit', 'key2', 0.001)
        self.tracker.record_cache_operation('miss', 'key3', 0.002)
        self.tracker.record_cache_operation('set', 'key4', 0.003)
        self.tracker.record_cache_operation('delete', 'key5', 0.001)
        
        summary = self.tracker.get_cache_summary()
        
        self.assertEqual(summary['total_operations'], 5)
        self.assertEqual(summary['hits'], 2)
        self.assertEqual(summary['misses'], 1)
        self.assertEqual(summary['sets'], 1)
        self.assertEqual(summary['deletes'], 1)
        self.assertEqual(summary['total_gets'], 3)  # hits + misses
        self.assertAlmostEqual(summary['hit_ratio'], 2/3, places=2)  # 2 hits out of 3 gets
    
    def test_get_cache_summary_perfect_hit_ratio(self) -> None:
        """Test cache summary with perfect hit ratio."""
        self.tracker.is_active = True
        
        # Only hits, no misses
        self.tracker.record_cache_operation('hit', 'key1', 0.001)
        self.tracker.record_cache_operation('hit', 'key2', 0.001)
        
        summary = self.tracker.get_cache_summary()
        self.assertEqual(summary['hit_ratio'], 1.0)
    
    def test_get_cache_summary_zero_hit_ratio(self) -> None:
        """Test cache summary with zero hit ratio."""
        self.tracker.is_active = True
        
        # Only misses, no hits
        self.tracker.record_cache_operation('miss', 'key1', 0.002)
        self.tracker.record_cache_operation('miss', 'key2', 0.002)
        
        summary = self.tracker.get_cache_summary()
        self.assertEqual(summary['hit_ratio'], 0.0)


class TestPerformanceContextManager(unittest.TestCase):
    """Test PerformanceContextManager functionality."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.context_manager = PerformanceContextManager("test_operation")
    
    def test_context_manager_initialization(self) -> None:
        """Test PerformanceContextManager initialization."""
        self.assertEqual(self.context_manager.operation_name, "test_operation")
        self.assertIsInstance(self.context_manager.query_tracker, DjangoQueryTracker)
        self.assertIsInstance(self.context_manager.cache_tracker, DjangoCacheTracker)
        self.assertIsNone(self.context_manager._start_time)
        self.assertIsNone(self.context_manager._end_time)
    
    def test_context_manager_enter(self) -> None:
        """Test context manager __enter__ method."""
        with patch.object(self.context_manager.query_tracker, 'start') as mock_query_start, \
             patch.object(self.context_manager.cache_tracker, 'start') as mock_cache_start:
            
            result = self.context_manager.__enter__()
            
            self.assertEqual(result, self.context_manager)
            self.assertIsNotNone(self.context_manager._start_time)
            mock_query_start.assert_called_once()
            mock_cache_start.assert_called_once()
    
    def test_context_manager_exit(self) -> None:
        """Test context manager __exit__ method."""
        # First enter the context
        self.context_manager._start_time = time.time()
        
        with patch.object(self.context_manager.query_tracker, 'stop') as mock_query_stop, \
             patch.object(self.context_manager.cache_tracker, 'stop') as mock_cache_stop:
            
            self.context_manager.__exit__(None, None, None)
            
            self.assertIsNotNone(self.context_manager._end_time)
            mock_query_stop.assert_called_once()
            mock_cache_stop.assert_called_once()
    
    def test_context_manager_full_workflow(self) -> None:
        """Test complete context manager workflow."""
        with patch.object(self.context_manager.query_tracker, 'start'), \
             patch.object(self.context_manager.query_tracker, 'stop'), \
             patch.object(self.context_manager.cache_tracker, 'start'), \
             patch.object(self.context_manager.cache_tracker, 'stop'):
            
            with self.context_manager as ctx:
                self.assertEqual(ctx, self.context_manager)
                self.assertIsNotNone(ctx._start_time)
            
            self.assertIsNotNone(self.context_manager._end_time)
    
    def test_context_manager_exception_handling(self) -> None:
        """Test context manager behavior with exceptions."""
        with patch.object(self.context_manager.query_tracker, 'start'), \
             patch.object(self.context_manager.query_tracker, 'stop'), \
             patch.object(self.context_manager.cache_tracker, 'start'), \
             patch.object(self.context_manager.cache_tracker, 'stop'):
            
            try:
                with self.context_manager:
                    raise ValueError("Test exception")
            except ValueError:
                pass
            
            # Should still have called stop methods despite exception
            self.assertIsNotNone(self.context_manager._end_time)
    
    def test_get_optimization_report_no_queries_no_cache(self) -> None:
        """Test optimization report with no queries and no cache operations."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 0, 'n_plus_one_patterns': [], 'slow_queries': 0
            }
            mock_cache_summary.return_value = {'total_gets': 0}
            
            report = self.context_manager.get_optimization_report()
            
            self.assertIn("No database queries detected", report)
            self.assertIn("ℹ️", report)
    
    def test_get_optimization_report_efficient_queries(self) -> None:
        """Test optimization report with efficient queries."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 5, 'n_plus_one_patterns': [], 'slow_queries': 0
            }
            mock_cache_summary.return_value = {'total_gets': 0}
            
            report = self.context_manager.get_optimization_report()
            
            self.assertIn("5 queries executed efficiently", report)
            self.assertIn("✅", report)
    
    def test_get_optimization_report_n_plus_one_detected(self) -> None:
        """Test optimization report with N+1 patterns detected."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 10,
                'n_plus_one_patterns': [
                    "Potential N+1: 5 similar queries - SELECT * FROM profiles WHERE user_id = ?..."
                ],
                'slow_queries': 0
            }
            mock_cache_summary.return_value = {'total_gets': 0}
            
            report = self.context_manager.get_optimization_report()
            
            self.assertIn("N+1 Query Patterns Detected", report)
            self.assertIn("🚨", report)
            self.assertIn("Potential N+1: 5 similar queries", report)
    
    def test_get_optimization_report_good_cache_ratio(self) -> None:
        """Test optimization report with good cache hit ratio."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 3, 'n_plus_one_patterns': [], 'slow_queries': 0
            }
            mock_cache_summary.return_value = {'total_gets': 10, 'hit_ratio': 0.85}
            
            report = self.context_manager.get_optimization_report()
            
            self.assertIn("Good cache hit ratio: 85.0%", report)
            self.assertIn("✅", report)
    
    def test_get_optimization_report_low_cache_ratio(self) -> None:
        """Test optimization report with low cache hit ratio."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 3, 'n_plus_one_patterns': [], 'slow_queries': 0
            }
            mock_cache_summary.return_value = {'total_gets': 10, 'hit_ratio': 0.5}
            
            report = self.context_manager.get_optimization_report()
            
            self.assertIn("Low cache hit ratio: 50.0%", report)
            self.assertIn("⚠️", report)
            self.assertIn("consider optimizing cache usage", report)
    
    def test_get_optimization_report_slow_queries(self) -> None:
        """Test optimization report with slow queries detected."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 5, 'n_plus_one_patterns': [], 'slow_queries': 2
            }
            mock_cache_summary.return_value = {'total_gets': 0}
            
            report = self.context_manager.get_optimization_report()
            
            self.assertIn("2 slow queries detected", report)
            self.assertIn("> 100ms", report)
            self.assertIn("⚠️", report)
    
    def test_get_optimization_report_multiple_issues(self) -> None:
        """Test optimization report with multiple performance issues."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 10,
                'n_plus_one_patterns': ["N+1 pattern detected"],
                'slow_queries': 3
            }
            mock_cache_summary.return_value = {'total_gets': 5, 'hit_ratio': 0.4}
            
            report = self.context_manager.get_optimization_report()
            
            # Should contain all issues
            self.assertIn("N+1 Query Patterns Detected", report)
            self.assertIn("Low cache hit ratio", report)
            self.assertIn("3 slow queries detected", report)
    
    def test_get_optimization_report_no_issues(self) -> None:
        """Test optimization report when no performance issues are detected."""
        with patch.object(self.context_manager.query_tracker, 'get_query_summary') as mock_query_summary, \
             patch.object(self.context_manager.cache_tracker, 'get_cache_summary') as mock_cache_summary:
            
            mock_query_summary.return_value = {
                'total_queries': 0, 'n_plus_one_patterns': [], 'slow_queries': 0
            }
            mock_cache_summary.return_value = {'total_gets': 0}
            
            report = self.context_manager.get_optimization_report()
            
            # When only "no queries detected" message, it should not show "no issues"
            self.assertIn("No database queries detected", report)


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of Django hooks components."""
    
    def test_query_tracker_thread_safety(self) -> None:
        """Test that DjangoQueryTracker is thread-safe."""
        tracker = DjangoQueryTracker()
        tracker.is_active = True
        results = []
        
        def record_queries():
            for i in range(50):
                tracker.record_query(f"SELECT * FROM table_{i}", (i,), 0.01)
                results.append(i)
        
        threads = []
        for _ in range(4):
            thread = threading.Thread(target=record_queries)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have 200 queries total (4 threads × 50 queries each)
        self.assertEqual(len(tracker.queries), 200)
        self.assertEqual(tracker.query_count, 200)
        self.assertEqual(len(results), 200)
    
    def test_cache_tracker_thread_safety(self) -> None:
        """Test that DjangoCacheTracker is thread-safe."""
        tracker = DjangoCacheTracker()
        tracker.is_active = True
        results = []
        
        def record_operations():
            operations = ['hit', 'miss', 'set', 'delete']
            for i in range(25):
                op = operations[i % 4]
                tracker.record_cache_operation(op, f"key_{i}", 0.001)
                results.append(i)
        
        threads = []
        for _ in range(4):
            thread = threading.Thread(target=record_operations)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have 100 operations total (4 threads × 25 operations each)
        self.assertEqual(len(tracker.operations), 100)
        # Each thread does 6-7 of each operation type (25/4 rounded)
        self.assertGreater(tracker.hits, 0)
        self.assertGreater(tracker.misses, 0)
        self.assertGreater(tracker.sets, 0)
        self.assertGreater(tracker.deletes, 0)
        self.assertEqual(len(results), 100)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios."""
    
    def test_query_tracker_with_empty_sql(self) -> None:
        """Test query tracker with empty SQL string."""
        tracker = DjangoQueryTracker()
        tracker.is_active = True
        
        tracker.record_query("", None, 0.01)
        
        self.assertEqual(len(tracker.queries), 1)
        self.assertEqual(tracker.queries[0].sql, "")
    
    def test_query_tracker_with_none_sql(self) -> None:
        """Test query tracker with None SQL."""
        tracker = DjangoQueryTracker()
        tracker.is_active = True
        
        # This might happen in error conditions
        tracker.record_query(None, None, 0.01)
        
        self.assertEqual(len(tracker.queries), 1)
        self.assertIsNone(tracker.queries[0].sql)
    
    def test_cache_tracker_with_empty_key(self) -> None:
        """Test cache tracker with empty cache key."""
        tracker = DjangoCacheTracker()
        tracker.is_active = True
        
        tracker.record_cache_operation('hit', '', 0.001)
        
        self.assertEqual(len(tracker.operations), 1)
        self.assertEqual(tracker.operations[0]['key'], '')
    
    def test_normalize_query_edge_cases(self) -> None:
        """Test query normalization with edge cases."""
        tracker = DjangoQueryTracker()
        
        test_cases = [
            ("", ""),  # Empty string
            ("SELECT 1", "SELECT ?"),  # Single number
            ("SELECT 'a'", "SELECT ?"),  # Single char string
            ("SELECT \"\"", "SELECT ?"),  # Empty quoted string
            ("SELECT * FROM 'table'", "SELECT * FROM ?"),  # Table name in quotes
        ]
        
        for input_sql, expected in test_cases:
            with self.subTest(input_sql=input_sql):
                normalized = tracker._normalize_query(input_sql)
                self.assertEqual(normalized, expected)
    
    def test_performance_context_manager_timing(self) -> None:
        """Test that performance context manager records timing correctly."""
        context_manager = PerformanceContextManager("timing_test")
        
        with patch.object(context_manager.query_tracker, 'start'), \
             patch.object(context_manager.query_tracker, 'stop'), \
             patch.object(context_manager.cache_tracker, 'start'), \
             patch.object(context_manager.cache_tracker, 'stop'):
            
            start_time = time.time()
            with context_manager:
                time.sleep(0.01)  # Small delay
            end_time = time.time()
            
            # Should have recorded timing
            self.assertIsNotNone(context_manager._start_time)
            self.assertIsNotNone(context_manager._end_time)
            self.assertGreaterEqual(context_manager._start_time, start_time)
            self.assertLessEqual(context_manager._end_time, end_time)
            self.assertGreater(context_manager._end_time, context_manager._start_time)


if __name__ == '__main__':
    unittest.main()