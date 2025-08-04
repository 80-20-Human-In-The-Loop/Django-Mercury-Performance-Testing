# backend/performance_testing/python_bindings/django_analyzer.py - Django Performance Analysis Engine
# Provides deep analysis of Django-specific performance patterns, including N+1 query detection.

# --- Standard Library Imports ---
import re
import logging
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# --- Third-Party Imports ---
from django.db import connection
from django.test.utils import override_settings

# --- Local Imports ---
try:
    from .colors import colors, get_status_icon, EduLiteColorScheme
except ImportError:
    from colors import colors, get_status_icon, EduLiteColorScheme

# --- Data Classes for Analysis ---


@dataclass
class QueryAnalysis:
    """
    A data class holding the analysis of a single database query.

    Attributes:
        sql (str): The raw SQL of the query.
        duration (float): The execution time in milliseconds.
        table (str): The primary table being operated on.
        operation (str): The SQL operation (e.g., SELECT, INSERT).
        is_select_related (bool): True if the query likely uses `select_related`.
        is_prefetch_related (bool): True if the query likely uses `prefetch_related`.
        potentially_problematic (bool): True if the query shows signs of being inefficient.
    """

    sql: str
    duration: float
    table: str
    operation: str
    is_select_related: bool
    is_prefetch_related: bool
    potentially_problematic: bool


@dataclass
class NplusOneDetection:
    """
    A data class representing the results of an N+1 query pattern detection.

    Attributes:
        detected (bool): True if an N+1 pattern was detected.
        pattern_type (str): The type of N+1 pattern identified.
        queries (List[QueryAnalysis]): A list of the queries involved in the pattern.
        suggested_fix (str): A human-readable suggestion for fixing the issue.
        severity (str): The severity of the issue (e.g., 'low', 'critical').
        affected_tables (List[str]): A list of database tables affected by the pattern.
    """

    detected: bool
    pattern_type: str
    queries: List[QueryAnalysis]
    suggested_fix: str
    severity: str
    affected_tables: List[str]


# --- Query Pattern Recognition ---


class QueryPattern:
    """
    Represents a detected pattern of related database queries.

    This class is used to identify potential N+1 issues by grouping a base query
    with a series of subsequent, similar queries.
    """

    def __init__(self, base_query: str, related_queries: List[str]):
        """
        Initializes a QueryPattern instance.

        Args:
            base_query (str): The initial query that is suspected of causing an N+1 problem.
            related_queries (List[str]): A list of subsequent queries that may be part of the N+1 pattern.
        """
        self.base_query = base_query
        self.related_queries = related_queries
        self.count = len(related_queries)

    def is_n_plus_one(self) -> bool:
        """
        Determines if this query pattern constitutes an N+1 problem.

        Returns:
            bool: True if the pattern is a likely N+1 scenario, False otherwise.
        """
        if self.count < 2 or not self.related_queries:
            return False

        first_query = self.related_queries[0]
        table_match = re.search(r'FROM ["`]?(\w+)["`]?', first_query, re.IGNORECASE)
        if not table_match:
            return False

        table_name = table_match.group(1)
        same_table_count = sum(
            1
            for query in self.related_queries
            if table_name.lower() in query.lower()
            and re.search(r'WHERE.*\b\w*id\s*=\s*["\\]?\d+["\\]?', query, re.IGNORECASE)
        )

        return same_table_count >= len(self.related_queries) * 0.8


# --- Query Logging ---


class DjangoQueryLogger:
    """
    A thread-safe logger for capturing Django database queries for analysis.
    """

    def __init__(self):
        """Initializes the query logger."""
        self.queries: List[Dict[str, Any]] = []
        self.is_logging = False
        self._lock = threading.Lock()
        self._original_level = None
        self._handler = None

    def start_logging(self) -> None:
        """Starts logging database queries by attaching a custom handler."""
        with self._lock:
            if self.is_logging:
                return
            self.queries.clear()
            self.is_logging = True
            logger = logging.getLogger("django.db.backends")
            self._original_level = logger.level
            logger.setLevel(logging.DEBUG)
            self._handler = QueryHandler(self)
            logger.addHandler(self._handler)

    def stop_logging(self) -> List[Dict[str, Any]]:
        """
        Stops logging and returns the list of captured queries.

        Returns:
            List[Dict[str, Any]]: A list of captured query data.
        """
        with self._lock:
            if not self.is_logging:
                return []
            self.is_logging = False
            logger = logging.getLogger("django.db.backends")
            if self._original_level is not None:
                logger.setLevel(self._original_level)
            if self._handler:
                logger.removeHandler(self._handler)
            return self.queries.copy()

    def add_query(self, query_data: Dict[str, Any]) -> None:
        """
        Adds a captured query to the internal log.

        Args:
            query_data (Dict[str, Any]): The query data to add.
        """
        with self._lock:
            if self.is_logging:
                self.queries.append(query_data)


class QueryHandler(logging.Handler):
    """
    A custom logging handler that directs Django query logs to our logger instance.
    """

    def __init__(self, logger_instance: DjangoQueryLogger):
        """
        Initializes the handler.

        Args:
            logger_instance (DjangoQueryLogger): The logger instance to which queries will be sent.
        """
        super().__init__()
        self.logger_instance = logger_instance

    def emit(self, record: logging.LogRecord) -> None:
        """
        Captures a query from a log record and adds it to the logger instance.

        Args:
            record (logging.LogRecord): The log record to process.
        """
        if hasattr(record, "sql"):
            self.logger_instance.add_query(
                {
                    "sql": record.sql,
                    "duration": getattr(record, "duration", 0),
                    "params": getattr(record, "params", []),
                    "timestamp": record.created,
                }
            )


# --- Analysis Engine ---


class DjangoAnalysisEngine:
    """
    An engine for advanced, Django-specific performance analysis.
    """

    def __init__(self):
        """Initializes the analysis engine."""
        self.query_logger = DjangoQueryLogger()

    def analyze_queries(self, queries: List[Dict[str, Any]]) -> List[QueryAnalysis]:
        """
        Analyzes a list of raw query data and returns structured analysis.

        Args:
            queries (List[Dict[str, Any]]): A list of query data dictionaries.

        Returns:
            List[QueryAnalysis]: A list of structured query analysis objects.
        """
        return [
            QueryAnalysis(
                sql=(sql := query_data.get("sql", "")),
                duration=float(duration := query_data.get("duration", 0)),
                table=self._extract_table_name(sql),
                operation=self._extract_operation(sql),
                is_select_related=self._has_joins(sql),
                is_prefetch_related=False,  # Context-dependent, hard to detect here
                potentially_problematic=self._is_potentially_problematic(sql, duration),
            )
            for query_data in queries
        ]

    def detect_n_plus_one_queries(self, queries: List[Dict[str, Any]]) -> List[NplusOneDetection]:
        """
        Detects N+1 query patterns from a list of queries.

        Args:
            queries (List[Dict[str, Any]]): The list of queries to analyze.

        Returns:
            List[NplusOneDetection]: A list of detected N+1 patterns.
        """
        if len(queries) < 3:
            return []

        query_analyses = self.analyze_queries(queries)
        patterns = self._group_queries_by_pattern(query_analyses)
        return [
            self._create_n_plus_one_detection(p, query_analyses)
            for p in patterns
            if p.is_n_plus_one()
        ]

    def _group_queries_by_pattern(self, analyses: List[QueryAnalysis]) -> List[QueryPattern]:
        """Groups queries into patterns to facilitate N+1 detection."""
        patterns = []
        base_queries = [
            a for a in analyses if a.operation == "SELECT" and not self._is_single_row_lookup(a.sql)
        ]

        for i, base_query in enumerate(base_queries):
            related_queries = []
            for subsequent_query in analyses[i + 1 :]:
                if subsequent_query.operation == "SELECT":
                    if self._is_single_row_lookup(
                        subsequent_query.sql
                    ) and self._queries_likely_related(base_query, subsequent_query):
                        related_queries.append(subsequent_query.sql)
                    else:
                        break  # Stop if we hit another broad query
            if related_queries:
                patterns.append(QueryPattern(base_query.sql, related_queries))
        return patterns

    def _is_single_row_lookup(self, sql: str) -> bool:
        """Checks if a query is a single-row lookup, a key indicator of N+1 issues."""
        if sql is None:
            return False

        patterns = [
            r'WHERE.*\b\w*id\s*=\s*["\\]?\w+["\\]?',
            r'WHERE.*\bpk\s*=\s*["\\]?\w+["\\]?',
            r'WHERE.*\s+IN\s*\(["\\]?\w+["\\]?\)',  # Single item IN clause
        ]
        return any(re.search(p, sql, re.IGNORECASE) for p in patterns)

    def _queries_likely_related(
        self, base_query: QueryAnalysis, lookup_query: QueryAnalysis
    ) -> bool:
        """Heuristically determines if two queries are likely related."""
        base_table, lookup_table = base_query.table.lower(), lookup_query.table.lower()
        related_patterns = [f"{base_table}_", f"_{base_table}"]
        if base_table in ["user", "users"]:
            related_patterns.extend(["profile", "profiles", "userprofile"])
        return any(p and p in lookup_table for p in related_patterns)

    def _create_n_plus_one_detection(
        self, pattern: QueryPattern, analyses: List[QueryAnalysis]
    ) -> NplusOneDetection:
        """Creates an N+1 detection result object from a query pattern."""
        severity = "low"
        if pattern.count >= 50:
            severity = "critical"
        elif pattern.count >= 20:
            severity = "high"
        elif pattern.count >= 10:
            severity = "medium"

        affected_tables = list(set(self._extract_table_name(q) for q in pattern.related_queries))
        main_table = self._extract_table_name(pattern.base_query)

        if affected_tables:
            suggested_fix = f"Use `select_related('{affected_tables[0].lower()}')` or `prefetch_related()` in your `{main_table}` query."
        else:
            suggested_fix = (
                "Consider using `select_related()` or `prefetch_related()` to reduce query count."
            )

        return NplusOneDetection(
            detected=True,
            pattern_type="classic_n_plus_one",
            queries=[a for a in analyses if a.sql in pattern.related_queries],
            suggested_fix=suggested_fix,
            severity=severity,
            affected_tables=affected_tables,
        )

    def _extract_table_name(self, sql: str) -> str:
        """Extracts the primary table name from an SQL query.

        Args:
            sql: The SQL query string to parse.

        Returns:
            str: The primary table name, or 'unknown' if not found.
        """
        if sql is None:
            return "unknown"

        patterns = [
            r'FROM\s+["`]?(\w+)["`]?',
            r'UPDATE\s+["`]?(\w+)["`]?',
            r'INSERT\s+INTO\s+["`]?(\w+)["`]?',
        ]
        for pattern in patterns:
            match = re.search(pattern, sql, re.IGNORECASE)
            if match:
                return match.group(1)
        return "unknown"

    def _extract_operation(self, sql: str) -> str:
        """Extracts the SQL operation type from a query string.

        Args:
            sql: The SQL query string to parse.

        Returns:
            str: The operation type (SELECT, INSERT, UPDATE, DELETE, or OTHER).
        """
        if sql is None:
            return "OTHER"

        sql_upper = sql.strip().upper()
        for op in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
            if sql_upper.startswith(op):
                return op
        return "OTHER"

    def _has_joins(self, sql: str) -> bool:
        """Checks if an SQL query contains any JOIN clauses.

        Args:
            sql: The SQL query string to check.

        Returns:
            bool: True if the query contains JOIN clauses, False otherwise.
        """
        if sql is None:
            return False

        return bool(re.search(r"\b(INNER|LEFT|RIGHT|OUTER)?\s?JOIN\b", sql, re.IGNORECASE))

    def _is_potentially_problematic(self, sql: str, duration: float) -> bool:
        """Identifies if a query is potentially problematic based on common anti-patterns.

        Args:
            sql: The SQL query string to analyze.
            duration: Query execution time in milliseconds.

        Returns:
            bool: True if the query shows signs of being problematic.
        """
        if duration > 100:
            return True

        if sql is None:
            return False

        if (
            sql.strip().upper().startswith("SELECT")
            and "WHERE" not in sql.upper()
            and "LIMIT" not in sql.upper()
        ):
            return True
        return self._is_single_row_lookup(sql)

    def generate_optimization_report(self, detections: List[NplusOneDetection]) -> str:
        """
        Generates a colored, human-readable optimization report.

        Args:
            detections (List[NplusOneDetection]): A list of N+1 detections.

        Returns:
            str: A formatted report string.
        """
        if not detections:
            return colors.colorize(
                "✅ No N+1 query patterns detected!", EduLiteColorScheme.SUCCESS, bold=True
            )

        lines = [
            colors.colorize(
                "🔍 Django Query Analysis Report", EduLiteColorScheme.ACCENT, bold=True
            ),
            "=" * 50,
        ]
        severity_map = {
            "low": (EduLiteColorScheme.WARNING, "⚠️"),
            "medium": (EduLiteColorScheme.SLOW, "🐌"),
            "high": (EduLiteColorScheme.CRITICAL, "🚨"),
            "critical": (EduLiteColorScheme.CRITICAL, "💥"),
        }

        for i, detection in enumerate(detections, 1):
            color, icon = severity_map[detection.severity]
            lines.extend(
                [
                    f"\n{icon} Detection #{i} - {colors.colorize(detection.severity.upper(), color, bold=True)}",
                    f"   - Pattern: {colors.colorize(detection.pattern_type, EduLiteColorScheme.INFO)}",
                    f"   - Queries: {colors.colorize(str(len(detection.queries)), EduLiteColorScheme.TEXT)} repetitive queries",
                    f"   - Tables: {colors.colorize(', '.join(detection.affected_tables), EduLiteColorScheme.SECONDARY)}",
                    f"   - 💡 {colors.colorize('Fix:', EduLiteColorScheme.OPTIMIZATION, bold=True)} {detection.suggested_fix}",
                ]
            )

        lines.append(
            f"\n{colors.colorize('🎯 Summary:', EduLiteColorScheme.ACCENT, bold=True)} {len(detections)} optimization opportunities found."
        )
        return "\n".join(lines)


# --- Context Manager for Performance Monitoring ---


class PerformanceContextManager:
    """
    A context manager that combines performance monitoring with Django query analysis.
    """

    def __init__(self, operation_name: str):
        """
        Initializes the context manager.

        Args:
            operation_name (str): A name for the operation being monitored.
        """
        self.operation_name = operation_name
        self.analyzer = DjangoAnalysisEngine()
        self.start_queries = 0
        self.n_plus_one_detections: List[NplusOneDetection] = []

    def __enter__(self) -> "PerformanceContextManager":
        """Starts the query logger and records the initial query count."""
        self.analyzer.query_logger.start_logging()
        self.start_queries = len(connection.queries)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Stops the query logger, analyzes the captured queries, and detects N+1 patterns.
        """
        captured_queries = self.analyzer.query_logger.stop_logging()
        if hasattr(connection, "queries"):
            django_queries = connection.queries[self.start_queries :]
            for query in django_queries:
                captured_queries.append(
                    {
                        "sql": query["sql"],
                        "duration": float(query["time"]) * 1000,
                        "params": [],
                        "timestamp": 0,
                    }
                )
        self.n_plus_one_detections = self.analyzer.detect_n_plus_one_queries(captured_queries)

    def get_optimization_report(self) -> str:
        """Generates and returns a colored optimization report."""
        return self.analyzer.generate_optimization_report(self.n_plus_one_detections)

    @property
    def has_n_plus_one_issues(self) -> bool:
        """Returns True if any N+1 issues were detected."""
        return bool(self.n_plus_one_detections)


# --- Test Execution ---

if __name__ == "__main__":
    # Example usage to demonstrate the analysis engine.
    print("🔍 Django Analysis Engine Test")
    print("=" * 40)

    sample_queries = [
        {"sql": "SELECT * FROM auth_user ORDER BY date_joined DESC LIMIT 10", "duration": 15.2},
        {"sql": "SELECT * FROM users_userprofile WHERE user_id = 1", "duration": 2.1},
        {"sql": "SELECT * FROM users_userprofile WHERE user_id = 2", "duration": 2.3},
        {"sql": "SELECT * FROM users_userprofile WHERE user_id = 3", "duration": 2.0},
        {"sql": "SELECT * FROM users_userprofile WHERE user_id = 4", "duration": 2.4},
        {"sql": "SELECT * FROM users_userprofile WHERE user_id = 5", "duration": 1.9},
    ]

    analyzer = DjangoAnalysisEngine()
    detections = analyzer.detect_n_plus_one_queries(sample_queries)
    report = analyzer.generate_optimization_report(detections)
    print(report)
