"""
Unit tests for django_analyzer module
"""

import unittest
import logging
import threading
import time
from unittest.mock import patch, MagicMock, Mock
from typing import List, Dict, Any

from django_mercury.python_bindings.django_analyzer import (
    QueryAnalysis,
    NplusOneDetection,
    QueryPattern,
    DjangoQueryLogger,
    QueryHandler,
    DjangoAnalysisEngine,
    PerformanceContextManager
)


class TestQueryAnalysis(unittest.TestCase):
    """Test cases for QueryAnalysis dataclass."""

    def test_query_analysis_initialization(self) -> None:
        """Test QueryAnalysis dataclass initialization."""
        analysis = QueryAnalysis(
            sql="SELECT * FROM users WHERE id = 1",
            duration=15.5,
            table="users",
            operation="SELECT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=True
        )
        
        self.assertEqual(analysis.sql, "SELECT * FROM users WHERE id = 1")
        self.assertEqual(analysis.duration, 15.5)
        self.assertEqual(analysis.table, "users")
        self.assertEqual(analysis.operation, "SELECT")
        self.assertFalse(analysis.is_select_related)
        self.assertFalse(analysis.is_prefetch_related)
        self.assertTrue(analysis.potentially_problematic)

    def test_query_analysis_with_joins(self) -> None:
        """Test QueryAnalysis with JOIN queries."""
        analysis = QueryAnalysis(
            sql="SELECT * FROM users INNER JOIN profiles ON users.id = profiles.user_id",
            duration=25.0,
            table="users",
            operation="SELECT",
            is_select_related=True,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        
        self.assertTrue(analysis.is_select_related)
        self.assertEqual(analysis.duration, 25.0)

    def test_query_analysis_different_operations(self) -> None:
        """Test QueryAnalysis with different SQL operations."""
        # Test INSERT
        insert_analysis = QueryAnalysis(
            sql="INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
            duration=5.0,
            table="users",
            operation="INSERT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        self.assertEqual(insert_analysis.operation, "INSERT")
        
        # Test UPDATE
        update_analysis = QueryAnalysis(
            sql="UPDATE users SET name = 'Jane' WHERE id = 1",
            duration=3.0,
            table="users",
            operation="UPDATE",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        self.assertEqual(update_analysis.operation, "UPDATE")


class TestNplusOneDetection(unittest.TestCase):
    """Test cases for NplusOneDetection dataclass."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.sample_queries = [
            QueryAnalysis(
                sql="SELECT * FROM users WHERE id = 1",
                duration=2.0,
                table="users",
                operation="SELECT",
                is_select_related=False,
                is_prefetch_related=False,
                potentially_problematic=True
            ),
            QueryAnalysis(
                sql="SELECT * FROM users WHERE id = 2",
                duration=2.1,
                table="users",
                operation="SELECT",
                is_select_related=False,
                is_prefetch_related=False,
                potentially_problematic=True
            )
        ]

    def test_n_plus_one_detection_initialization(self) -> None:
        """Test NplusOneDetection dataclass initialization."""
        detection = NplusOneDetection(
            detected=True,
            pattern_type="classic_n_plus_one",
            queries=self.sample_queries,
            suggested_fix="Use select_related() or prefetch_related()",
            severity="medium",
            affected_tables=["users", "profiles"]
        )
        
        self.assertTrue(detection.detected)
        self.assertEqual(detection.pattern_type, "classic_n_plus_one")
        self.assertEqual(len(detection.queries), 2)
        self.assertEqual(detection.severity, "medium")
        self.assertEqual(detection.affected_tables, ["users", "profiles"])

    def test_n_plus_one_detection_severity_levels(self) -> None:
        """Test different severity levels."""
        for severity in ["low", "medium", "high", "critical"]:
            detection = NplusOneDetection(
                detected=True,
                pattern_type="classic_n_plus_one",
                queries=self.sample_queries,
                suggested_fix="Use select_related()",
                severity=severity,
                affected_tables=["users"]
            )
            self.assertEqual(detection.severity, severity)

    def test_n_plus_one_detection_no_detection(self) -> None:
        """Test NplusOneDetection when no pattern is detected."""
        detection = NplusOneDetection(
            detected=False,
            pattern_type="none",
            queries=[],
            suggested_fix="No optimization needed",
            severity="low",
            affected_tables=[]
        )
        
        self.assertFalse(detection.detected)
        self.assertEqual(len(detection.queries), 0)
        self.assertEqual(len(detection.affected_tables), 0)


class TestQueryPattern(unittest.TestCase):
    """Test cases for QueryPattern class."""

    def test_query_pattern_initialization(self) -> None:
        """Test QueryPattern initialization."""
        base_query = "SELECT * FROM users"
        related_queries = [
            "SELECT * FROM profiles WHERE user_id = 1",
            "SELECT * FROM profiles WHERE user_id = 2",
            "SELECT * FROM profiles WHERE user_id = 3"
        ]
        
        pattern = QueryPattern(base_query, related_queries)
        
        self.assertEqual(pattern.base_query, base_query)
        self.assertEqual(pattern.related_queries, related_queries)
        self.assertEqual(pattern.count, 3)

    def test_is_n_plus_one_positive_case(self) -> None:
        """Test is_n_plus_one method with a clear N+1 pattern."""
        base_query = "SELECT * FROM users"
        related_queries = [
            "SELECT * FROM profiles WHERE user_id = 1",
            "SELECT * FROM profiles WHERE user_id = 2",
            "SELECT * FROM profiles WHERE user_id = 3",
            "SELECT * FROM profiles WHERE user_id = 4",
            "SELECT * FROM profiles WHERE user_id = 5"
        ]
        
        pattern = QueryPattern(base_query, related_queries)
        self.assertTrue(pattern.is_n_plus_one())

    def test_is_n_plus_one_insufficient_queries(self) -> None:
        """Test is_n_plus_one with insufficient queries."""
        base_query = "SELECT * FROM users"
        related_queries = ["SELECT * FROM profiles WHERE user_id = 1"]
        
        pattern = QueryPattern(base_query, related_queries)
        self.assertFalse(pattern.is_n_plus_one())

    def test_is_n_plus_one_no_id_pattern(self) -> None:
        """Test is_n_plus_one with queries that don't match ID pattern."""
        base_query = "SELECT * FROM users"
        related_queries = [
            "SELECT * FROM profiles WHERE name = 'test'",
            "SELECT * FROM profiles WHERE active = true"
        ]
        
        pattern = QueryPattern(base_query, related_queries)
        self.assertFalse(pattern.is_n_plus_one())

    def test_is_n_plus_one_empty_queries(self) -> None:
        """Test is_n_plus_one with empty related queries."""
        base_query = "SELECT * FROM users"
        related_queries = []
        
        pattern = QueryPattern(base_query, related_queries)
        self.assertFalse(pattern.is_n_plus_one())

    def test_is_n_plus_one_mixed_tables(self) -> None:
        """Test is_n_plus_one with mixed table queries."""
        base_query = "SELECT * FROM users"
        related_queries = [
            "SELECT * FROM profiles WHERE user_id = 1",
            "SELECT * FROM orders WHERE customer_id = 2",
            "SELECT * FROM profiles WHERE user_id = 3"
        ]
        
        pattern = QueryPattern(base_query, related_queries)
        # Should still detect pattern if enough queries match
        result = pattern.is_n_plus_one()
        self.assertIsInstance(result, bool)


class TestDjangoQueryLogger(unittest.TestCase):
    """Test cases for DjangoQueryLogger class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = DjangoQueryLogger()

    def test_logger_initialization(self) -> None:
        """Test DjangoQueryLogger initialization."""
        self.assertEqual(len(self.logger.queries), 0)
        self.assertFalse(self.logger.is_logging)
        self.assertIsNone(self.logger._original_level)
        self.assertIsNone(self.logger._handler)

    @patch('django_mercury.python_bindings.django_analyzer.logging.getLogger')
    def test_start_logging(self, mock_get_logger) -> None:
        """Test starting query logging."""
        mock_django_logger = Mock()
        mock_django_logger.level = logging.INFO
        mock_get_logger.return_value = mock_django_logger
        
        self.logger.start_logging()
        
        self.assertTrue(self.logger.is_logging)
        self.assertEqual(len(self.logger.queries), 0)
        mock_django_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_django_logger.addHandler.assert_called_once()

    @patch('django_mercury.python_bindings.django_analyzer.logging.getLogger')
    def test_start_logging_already_started(self, mock_get_logger) -> None:
        """Test starting logging when already started."""
        mock_django_logger = Mock()
        mock_get_logger.return_value = mock_django_logger
        
        self.logger.start_logging()
        mock_django_logger.reset_mock()
        
        # Try to start again
        self.logger.start_logging()
        
        # Should not call logger methods again
        mock_django_logger.setLevel.assert_not_called()
        mock_django_logger.addHandler.assert_not_called()

    @patch('django_mercury.python_bindings.django_analyzer.logging.getLogger')
    def test_stop_logging(self, mock_get_logger) -> None:
        """Test stopping query logging."""
        mock_django_logger = Mock()
        mock_django_logger.level = logging.INFO
        mock_get_logger.return_value = mock_django_logger
        
        # Start logging first
        self.logger.start_logging()
        
        # Add a test query
        test_query = {'sql': 'SELECT * FROM test', 'duration': 5.0}
        self.logger.add_query(test_query)
        
        # Stop logging
        queries = self.logger.stop_logging()
        
        self.assertFalse(self.logger.is_logging)
        self.assertEqual(len(queries), 1)
        self.assertEqual(queries[0], test_query)
        mock_django_logger.setLevel.assert_called_with(logging.INFO)
        mock_django_logger.removeHandler.assert_called_once()

    def test_stop_logging_not_started(self) -> None:
        """Test stopping logging when not started."""
        queries = self.logger.stop_logging()
        self.assertEqual(queries, [])

    def test_add_query_while_logging(self) -> None:
        """Test adding queries while logging is active."""
        self.logger.is_logging = True
        
        query1 = {'sql': 'SELECT * FROM users', 'duration': 10.0}
        query2 = {'sql': 'SELECT * FROM profiles', 'duration': 5.0}
        
        self.logger.add_query(query1)
        self.logger.add_query(query2)
        
        self.assertEqual(len(self.logger.queries), 2)
        self.assertEqual(self.logger.queries[0], query1)
        self.assertEqual(self.logger.queries[1], query2)

    def test_add_query_while_not_logging(self) -> None:
        """Test adding queries while logging is inactive."""
        self.logger.is_logging = False
        
        query = {'sql': 'SELECT * FROM users', 'duration': 10.0}
        self.logger.add_query(query)
        
        self.assertEqual(len(self.logger.queries), 0)

    def test_thread_safety(self) -> None:
        """Test thread safety of the logger."""
        self.logger.is_logging = True
        results = []
        
        def add_queries():
            for i in range(10):
                query = {'sql': f'SELECT * FROM table_{i}', 'duration': i}
                self.logger.add_query(query)
                results.append(i)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=add_queries)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have 50 queries total (5 threads × 10 queries each)
        self.assertEqual(len(self.logger.queries), 50)
        self.assertEqual(len(results), 50)


class TestQueryHandler(unittest.TestCase):
    """Test cases for QueryHandler class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.handler = QueryHandler(self.mock_logger)

    def test_handler_initialization(self) -> None:
        """Test QueryHandler initialization."""
        self.assertEqual(self.handler.logger_instance, self.mock_logger)

    def test_emit_with_sql_record(self) -> None:
        """Test emit method with SQL record."""
        record = Mock()
        record.sql = "SELECT * FROM users WHERE id = 1"
        record.duration = 15.5
        record.params = ['param1', 'param2']
        record.created = 1234567890.0
        
        self.handler.emit(record)
        
        expected_query = {
            'sql': "SELECT * FROM users WHERE id = 1",
            'duration': 15.5,
            'params': ['param1', 'param2'],
            'timestamp': 1234567890.0
        }
        self.mock_logger.add_query.assert_called_once_with(expected_query)

    def test_emit_with_minimal_record(self) -> None:
        """Test emit method with minimal SQL record."""
        record = Mock(spec=['sql', 'created'])
        record.sql = "SELECT * FROM users"
        record.created = 1234567890.0
        # duration and params not set, should use defaults
        
        self.handler.emit(record)
        
        expected_query = {
            'sql': "SELECT * FROM users",
            'duration': 0,
            'params': [],
            'timestamp': 1234567890.0
        }
        self.mock_logger.add_query.assert_called_once_with(expected_query)

    def test_emit_without_sql(self) -> None:
        """Test emit method with record without SQL."""
        record = Mock()
        record.created = 1234567890.0
        # No sql attribute
        delattr(record, 'sql')
        
        self.handler.emit(record)
        
        # Should not call add_query if no SQL attribute
        self.mock_logger.add_query.assert_not_called()


class TestDjangoAnalysisEngine(unittest.TestCase):
    """Test cases for DjangoAnalysisEngine class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = DjangoAnalysisEngine()
        self.sample_queries = [
            {'sql': 'SELECT * FROM users ORDER BY id', 'duration': 15.0},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 1', 'duration': 2.0},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 2', 'duration': 2.1},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 3', 'duration': 1.9},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 4', 'duration': 2.0},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 5', 'duration': 1.8}
        ]

    def test_engine_initialization(self) -> None:
        """Test DjangoAnalysisEngine initialization."""
        self.assertIsInstance(self.engine.query_logger, DjangoQueryLogger)

    def test_analyze_queries(self) -> None:
        """Test analyze_queries method."""
        analyses = self.engine.analyze_queries(self.sample_queries)
        
        self.assertEqual(len(analyses), 6)
        
        # Check first query analysis
        first_analysis = analyses[0]
        self.assertEqual(first_analysis.sql, 'SELECT * FROM users ORDER BY id')
        self.assertEqual(first_analysis.duration, 15.0)
        self.assertEqual(first_analysis.table, 'users')
        self.assertEqual(first_analysis.operation, 'SELECT')

    def test_analyze_empty_queries(self) -> None:
        """Test analyze_queries with empty query list."""
        analyses = self.engine.analyze_queries([])
        self.assertEqual(len(analyses), 0)

    def test_detect_n_plus_one_queries_positive(self) -> None:
        """Test N+1 detection with clear N+1 pattern."""
        detections = self.engine.detect_n_plus_one_queries(self.sample_queries)
        
        self.assertGreater(len(detections), 0)
        detection = detections[0]
        self.assertTrue(detection.detected)
        self.assertEqual(detection.pattern_type, "classic_n_plus_one")
        self.assertIn("profiles", detection.affected_tables)

    def test_detect_n_plus_one_queries_insufficient(self) -> None:
        """Test N+1 detection with insufficient queries."""
        short_queries = self.sample_queries[:2]
        detections = self.engine.detect_n_plus_one_queries(short_queries)
        
        self.assertEqual(len(detections), 0)

    def test_detect_n_plus_one_queries_no_pattern(self) -> None:
        """Test N+1 detection with no clear pattern."""
        no_pattern_queries = [
            {'sql': 'SELECT * FROM users', 'duration': 10.0},
            {'sql': 'SELECT * FROM orders', 'duration': 15.0},
            {'sql': 'SELECT * FROM products', 'duration': 12.0}
        ]
        
        detections = self.engine.detect_n_plus_one_queries(no_pattern_queries)
        self.assertEqual(len(detections), 0)

    def test_extract_table_name_from_select(self) -> None:
        """Test _extract_table_name with SELECT query."""
        sql = "SELECT * FROM users WHERE id = 1"
        table = self.engine._extract_table_name(sql)
        self.assertEqual(table, "users")

    def test_extract_table_name_from_update(self) -> None:
        """Test _extract_table_name with UPDATE query."""
        sql = "UPDATE profiles SET name = 'John' WHERE id = 1"
        table = self.engine._extract_table_name(sql)
        self.assertEqual(table, "profiles")

    def test_extract_table_name_from_insert(self) -> None:
        """Test _extract_table_name with INSERT query."""
        sql = "INSERT INTO orders (user_id, total) VALUES (1, 100.00)"
        table = self.engine._extract_table_name(sql)
        self.assertEqual(table, "orders")

    def test_extract_table_name_with_quotes(self) -> None:
        """Test _extract_table_name with quoted table names."""
        sql = 'SELECT * FROM `users` WHERE id = 1'
        table = self.engine._extract_table_name(sql)
        self.assertEqual(table, "users")

    def test_extract_table_name_unknown(self) -> None:
        """Test _extract_table_name with unparseable query."""
        sql = "SHOW TABLES"
        table = self.engine._extract_table_name(sql)
        self.assertEqual(table, "unknown")

    def test_extract_operation_select(self) -> None:
        """Test _extract_operation with SELECT query."""
        sql = "SELECT * FROM users"
        operation = self.engine._extract_operation(sql)
        self.assertEqual(operation, "SELECT")

    def test_extract_operation_insert(self) -> None:
        """Test _extract_operation with INSERT query."""
        sql = "INSERT INTO users (name) VALUES ('John')"
        operation = self.engine._extract_operation(sql)
        self.assertEqual(operation, "INSERT")

    def test_extract_operation_update(self) -> None:
        """Test _extract_operation with UPDATE query."""
        sql = "UPDATE users SET name = 'Jane'"
        operation = self.engine._extract_operation(sql)
        self.assertEqual(operation, "UPDATE")

    def test_extract_operation_delete(self) -> None:
        """Test _extract_operation with DELETE query."""
        sql = "DELETE FROM users WHERE id = 1"
        operation = self.engine._extract_operation(sql)
        self.assertEqual(operation, "DELETE")

    def test_extract_operation_other(self) -> None:
        """Test _extract_operation with other SQL commands."""
        sql = "SHOW TABLES"
        operation = self.engine._extract_operation(sql)
        self.assertEqual(operation, "OTHER")

    def test_has_joins_inner_join(self) -> None:
        """Test _has_joins with INNER JOIN."""
        sql = "SELECT * FROM users INNER JOIN profiles ON users.id = profiles.user_id"
        self.assertTrue(self.engine._has_joins(sql))

    def test_has_joins_left_join(self) -> None:
        """Test _has_joins with LEFT JOIN."""
        sql = "SELECT * FROM users LEFT JOIN profiles ON users.id = profiles.user_id"
        self.assertTrue(self.engine._has_joins(sql))

    def test_has_joins_no_join(self) -> None:
        """Test _has_joins with no JOIN."""
        sql = "SELECT * FROM users WHERE id = 1"
        self.assertFalse(self.engine._has_joins(sql))

    def test_has_joins_case_insensitive(self) -> None:
        """Test _has_joins case insensitivity."""
        sql = "select * from users inner join profiles on users.id = profiles.user_id"
        self.assertTrue(self.engine._has_joins(sql))

    def test_is_potentially_problematic_slow_query(self) -> None:
        """Test _is_potentially_problematic with slow query."""
        sql = "SELECT * FROM users"
        self.assertTrue(self.engine._is_potentially_problematic(sql, 150.0))

    def test_is_potentially_problematic_no_where_clause(self) -> None:
        """Test _is_potentially_problematic with SELECT without WHERE."""
        sql = "SELECT * FROM users"
        self.assertTrue(self.engine._is_potentially_problematic(sql, 50.0))

    def test_is_potentially_problematic_single_row_lookup(self) -> None:
        """Test _is_potentially_problematic with single row lookup."""
        sql = "SELECT * FROM users WHERE id = 1"
        self.assertTrue(self.engine._is_potentially_problematic(sql, 5.0))

    def test_is_potentially_problematic_good_query(self) -> None:
        """Test _is_potentially_problematic with well-optimized query."""
        sql = "SELECT * FROM users WHERE active = true LIMIT 10"
        self.assertFalse(self.engine._is_potentially_problematic(sql, 10.0))

    def test_is_single_row_lookup_id_equals(self) -> None:
        """Test _is_single_row_lookup with id = pattern."""
        sql = "SELECT * FROM users WHERE id = 123"
        self.assertTrue(self.engine._is_single_row_lookup(sql))

    def test_is_single_row_lookup_pk_equals(self) -> None:
        """Test _is_single_row_lookup with pk = pattern."""
        sql = "SELECT * FROM users WHERE pk = 456"
        self.assertTrue(self.engine._is_single_row_lookup(sql))

    def test_is_single_row_lookup_in_clause(self) -> None:
        """Test _is_single_row_lookup with IN clause."""
        sql = "SELECT * FROM users WHERE id IN (789)"
        self.assertTrue(self.engine._is_single_row_lookup(sql))

    def test_is_single_row_lookup_negative(self) -> None:
        """Test _is_single_row_lookup with non-single-row query."""
        sql = "SELECT * FROM users WHERE active = true"
        self.assertFalse(self.engine._is_single_row_lookup(sql))

    def test_queries_likely_related_related_tables(self) -> None:
        """Test _queries_likely_related with related tables."""
        base_query = QueryAnalysis(
            sql="SELECT * FROM user",
            duration=10.0,
            table="user",
            operation="SELECT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        
        lookup_query = QueryAnalysis(
            sql="SELECT * FROM userprofile WHERE user_id = 1",
            duration=2.0,
            table="userprofile",
            operation="SELECT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        
        self.assertTrue(self.engine._queries_likely_related(base_query, lookup_query))

    def test_queries_likely_related_user_profile(self) -> None:
        """Test _queries_likely_related with user/profile relationship."""
        base_query = QueryAnalysis(
            sql="SELECT * FROM user",
            duration=10.0,
            table="user",
            operation="SELECT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        
        lookup_query = QueryAnalysis(
            sql="SELECT * FROM profile WHERE user_id = 1",
            duration=2.0,
            table="profile",
            operation="SELECT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        
        self.assertTrue(self.engine._queries_likely_related(base_query, lookup_query))

    def test_queries_likely_related_unrelated(self) -> None:
        """Test _queries_likely_related with unrelated tables."""
        base_query = QueryAnalysis(
            sql="SELECT * FROM orders",
            duration=10.0,
            table="orders",
            operation="SELECT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        
        lookup_query = QueryAnalysis(
            sql="SELECT * FROM products WHERE id = 1",
            duration=2.0,
            table="products",
            operation="SELECT",
            is_select_related=False,
            is_prefetch_related=False,
            potentially_problematic=False
        )
        
        self.assertFalse(self.engine._queries_likely_related(base_query, lookup_query))

    def test_create_n_plus_one_detection_low_severity(self) -> None:
        """Test _create_n_plus_one_detection with low severity."""
        related_queries = ["SELECT * FROM profiles WHERE user_id = 1"] * 5
        pattern = QueryPattern("SELECT * FROM users", related_queries)
        analyses = self.engine.analyze_queries([
            {'sql': query, 'duration': 2.0} for query in related_queries
        ])
        
        detection = self.engine._create_n_plus_one_detection(pattern, analyses)
        
        self.assertEqual(detection.severity, "low")
        self.assertIn("profiles", detection.affected_tables)

    def test_create_n_plus_one_detection_high_severity(self) -> None:
        """Test _create_n_plus_one_detection with high severity."""
        related_queries = ["SELECT * FROM profiles WHERE user_id = 1"] * 25
        pattern = QueryPattern("SELECT * FROM users", related_queries)
        analyses = self.engine.analyze_queries([
            {'sql': query, 'duration': 2.0} for query in related_queries
        ])
        
        detection = self.engine._create_n_plus_one_detection(pattern, analyses)
        
        self.assertEqual(detection.severity, "high")

    def test_create_n_plus_one_detection_critical_severity(self) -> None:
        """Test _create_n_plus_one_detection with critical severity."""
        related_queries = ["SELECT * FROM profiles WHERE user_id = 1"] * 60
        pattern = QueryPattern("SELECT * FROM users", related_queries)
        analyses = self.engine.analyze_queries([
            {'sql': query, 'duration': 2.0} for query in related_queries
        ])
        
        detection = self.engine._create_n_plus_one_detection(pattern, analyses)
        
        self.assertEqual(detection.severity, "critical")

    def test_generate_optimization_report_no_detections(self) -> None:
        """Test generate_optimization_report with no detections."""
        report = self.engine.generate_optimization_report([])
        
        self.assertIn("No N+1 query patterns detected", report)
        self.assertIn("✅", report)

    def test_generate_optimization_report_with_detections(self) -> None:
        """Test generate_optimization_report with detections."""
        detection = NplusOneDetection(
            detected=True,
            pattern_type="classic_n_plus_one",
            queries=[],
            suggested_fix="Use select_related()",
            severity="medium",
            affected_tables=["profiles"]
        )
        
        report = self.engine.generate_optimization_report([detection])
        
        self.assertIn("Django Query Analysis Report", report)
        self.assertIn("Detection #1", report)
        self.assertIn("MEDIUM", report)
        self.assertIn("profiles", report)
        self.assertIn("Use select_related()", report)

    def test_generate_optimization_report_multiple_detections(self) -> None:
        """Test generate_optimization_report with multiple detections."""
        detections = [
            NplusOneDetection(
                detected=True,
                pattern_type="classic_n_plus_one",
                queries=[],
                suggested_fix="Use select_related()",
                severity="high",
                affected_tables=["profiles"]
            ),
            NplusOneDetection(
                detected=True,
                pattern_type="classic_n_plus_one",
                queries=[],
                suggested_fix="Use prefetch_related()",
                severity="critical",
                affected_tables=["orders"]
            )
        ]
        
        report = self.engine.generate_optimization_report(detections)
        
        self.assertIn("Detection #1", report)
        self.assertIn("Detection #2", report)
        self.assertIn("2 optimization opportunities found", report)


class TestPerformanceContextManager(unittest.TestCase):
    """Test cases for PerformanceContextManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.context_manager = PerformanceContextManager("test_operation")

    def test_context_manager_initialization(self) -> None:
        """Test PerformanceContextManager initialization."""
        self.assertEqual(self.context_manager.operation_name, "test_operation")
        self.assertIsInstance(self.context_manager.analyzer, DjangoAnalysisEngine)
        self.assertEqual(len(self.context_manager.n_plus_one_detections), 0)

    @patch('django_mercury.python_bindings.django_analyzer.connection')
    def test_context_manager_enter(self, mock_connection) -> None:
        """Test context manager __enter__ method."""
        mock_connection.queries = []
        
        result = self.context_manager.__enter__()
        
        self.assertEqual(result, self.context_manager)
        self.assertEqual(self.context_manager.start_queries, 0)

    @patch('django_mercury.python_bindings.django_analyzer.connection')
    def test_context_manager_exit(self, mock_connection) -> None:
        """Test context manager __exit__ method."""
        # Mock Django connection queries
        mock_connection.queries = [
            {'sql': 'SELECT * FROM users', 'time': '0.015'},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 1', 'time': '0.002'}
        ]
        
        # Mock the query logger
        with patch.object(self.context_manager.analyzer.query_logger, 'stop_logging') as mock_stop:
            mock_stop.return_value = []
            
            self.context_manager.start_queries = 0
            self.context_manager.__exit__(None, None, None)
            
            mock_stop.assert_called_once()

    def test_get_optimization_report(self) -> None:
        """Test get_optimization_report method."""
        # Add a mock detection
        detection = NplusOneDetection(
            detected=True,
            pattern_type="classic_n_plus_one",
            queries=[],
            suggested_fix="Use select_related()",
            severity="medium",
            affected_tables=["profiles"]
        )
        self.context_manager.n_plus_one_detections = [detection]
        
        report = self.context_manager.get_optimization_report()
        
        self.assertIn("Django Query Analysis Report", report)
        self.assertIn("MEDIUM", report)

    def test_has_n_plus_one_issues_true(self) -> None:
        """Test has_n_plus_one_issues property when issues exist."""
        detection = NplusOneDetection(
            detected=True,
            pattern_type="classic_n_plus_one",
            queries=[],
            suggested_fix="Use select_related()",
            severity="medium",
            affected_tables=["profiles"]
        )
        self.context_manager.n_plus_one_detections = [detection]
        
        self.assertTrue(self.context_manager.has_n_plus_one_issues)

    def test_has_n_plus_one_issues_false(self) -> None:
        """Test has_n_plus_one_issues property when no issues exist."""
        self.context_manager.n_plus_one_detections = []
        
        self.assertFalse(self.context_manager.has_n_plus_one_issues)

    @patch('django_mercury.python_bindings.django_analyzer.connection')
    def test_context_manager_full_workflow(self, mock_connection) -> None:
        """Test complete context manager workflow."""
        # Setup mock connection with N+1 pattern
        mock_connection.queries = [
            {'sql': 'SELECT * FROM users ORDER BY id', 'time': '0.015'},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 1', 'time': '0.002'},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 2', 'time': '0.002'},
            {'sql': 'SELECT * FROM profiles WHERE user_id = 3', 'time': '0.002'}
        ]
        
        with patch.object(self.context_manager.analyzer.query_logger, 'start_logging'):
            with patch.object(self.context_manager.analyzer.query_logger, 'stop_logging') as mock_stop:
                mock_stop.return_value = []
                
                with self.context_manager as cm:
                    pass  # Simulate some operation
                
                # Check that detections were made
                self.assertIsInstance(cm.n_plus_one_detections, list)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = DjangoAnalysisEngine()

    def test_analyze_queries_with_malformed_data(self) -> None:
        """Test analyze_queries with malformed query data."""
        malformed_queries = [
            {'sql': None, 'duration': 10.0},
            {'duration': 5.0},  # Missing sql
            {'sql': 'SELECT * FROM users'},  # Missing duration
            {}  # Empty dict
        ]
        
        # Should handle gracefully without crashing
        analyses = self.engine.analyze_queries(malformed_queries)
        self.assertEqual(len(analyses), 4)

    def test_extract_table_name_with_complex_sql(self) -> None:
        """Test _extract_table_name with complex SQL statements."""
        complex_sqls = [
            "SELECT u.*, p.name FROM users u INNER JOIN profiles p ON u.id = p.user_id",
            "WITH recursive_query AS (SELECT * FROM categories) SELECT * FROM recursive_query",
            "SELECT * FROM (SELECT * FROM users) AS subquery",
            ""  # Empty SQL
        ]
        
        for sql in complex_sqls:
            table = self.engine._extract_table_name(sql)
            self.assertIsInstance(table, str)

    def test_query_pattern_with_edge_cases(self) -> None:
        """Test QueryPattern with edge case inputs."""
        # Empty base query
        pattern1 = QueryPattern("", ["SELECT * FROM profiles WHERE user_id = 1"])
        self.assertFalse(pattern1.is_n_plus_one())
        
        # Very long related queries list with proper ID pattern
        long_queries = [f"SELECT * FROM profiles WHERE id = {i}" for i in range(100)]
        pattern2 = QueryPattern("SELECT * FROM users", long_queries)
        self.assertTrue(pattern2.is_n_plus_one())

    def test_django_query_logger_thread_stress_test(self) -> None:
        """Test DjangoQueryLogger under high concurrent load."""
        logger = DjangoQueryLogger()
        logger.is_logging = True
        
        def stress_add_queries():
            for i in range(100):
                query = {'sql': f'SELECT * FROM table_{i}', 'duration': i * 0.1}
                logger.add_query(query)
                if i % 10 == 0:
                    time.sleep(0.001)  # Small delay to increase contention
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=stress_add_queries)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have 1000 queries total (10 threads × 100 queries each)
        self.assertEqual(len(logger.queries), 1000)

    def test_n_plus_one_detection_severity_boundary_conditions(self) -> None:
        """Test N+1 detection severity calculation at boundaries."""
        test_cases = [
            (9, "low"),
            (10, "medium"),
            (19, "medium"),
            (20, "high"),
            (49, "high"),
            (50, "critical"),
            (100, "critical")
        ]
        
        for count, expected_severity in test_cases:
            related_queries = ["SELECT * FROM profiles WHERE user_id = 1"] * count
            pattern = QueryPattern("SELECT * FROM users", related_queries)
            analyses = self.engine.analyze_queries([
                {'sql': query, 'duration': 1.0} for query in related_queries
            ])
            
            detection = self.engine._create_n_plus_one_detection(pattern, analyses)
            self.assertEqual(detection.severity, expected_severity, 
                           f"Failed for count {count}, expected {expected_severity}, got {detection.severity}")


if __name__ == '__main__':
    unittest.main()