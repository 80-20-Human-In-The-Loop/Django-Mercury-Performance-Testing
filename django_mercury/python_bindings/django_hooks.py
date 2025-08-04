# backend/performance_testing/python_bindings/django_hooks.py - Django-specific performance monitoring hooks
# Contains trackers for database queries and cache operations, along with a context manager for performance analysis.

# --- Standard Library Imports ---
import time
import re
import ctypes
import threading
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable

# --- Third-Party Imports ---
try:
    from django.db import connections, connection
    from django.core.cache import cache
    from django.db.backends.utils import CursorWrapper
    from django.test.utils import override_settings
    import django.db.backends.utils

    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

# --- C Extension Integration ---
try:
    from .c_bindings import c_extensions

    C_EXTENSIONS_AVAILABLE = c_extensions.query_analyzer is not None
except ImportError:
    C_EXTENSIONS_AVAILABLE = False

# --- Data Classes ---


@dataclass
class QueryInfo:
    """
    Holds information about a single database query.

        Attributes:
            sql (str): The SQL query string.
            time (float): The execution time of the query in seconds.
            params (Optional[tuple]): The parameters used in the query.
            alias (str): The database alias used for the query.
    """

    sql: str
    time: float
    params: Optional[Tuple[Any, ...]] = None
    alias: str = "default"


# --- Query Tracking ---


class DjangoQueryTracker:
    """
    Tracks and analyzes Django ORM queries for performance monitoring.

        This class patches Django's database cursor to intercept and record all
        SQL queries executed during its active period. It provides methods to
        detect common performance issues like N+1 query patterns and slow queries.
    """

    def __init__(self) -> None:
        """Initializes the DjangoQueryTracker."""
        self.queries: List[QueryInfo] = []
        self.query_count: int = 0
        self.total_time: float = 0.0
        self.is_active: bool = False
        self._original_execute: Optional[callable] = None
        self._original_executemany: Optional[callable] = None

    def start(self) -> None:
        """
        Starts tracking Django queries by patching the cursor's execute methods.

        This method monkey-patches Django's CursorWrapper to intercept all SQL
        queries. It's safe to call multiple times - subsequent calls are no-ops
        if tracking is already active.

        Raises:
            RuntimeError: If Django is not available.
        """
        if not DJANGO_AVAILABLE:
            return

        self.is_active = True
        self.queries.clear()
        self.query_count = 0
        self.total_time = 0.0

        # Reset C extension query analyzer for fresh test state
        if C_EXTENSIONS_AVAILABLE:
            try:
                c_extensions.query_analyzer.reset_query_analyzer()
            except Exception:
                pass  # Ignore reset errors

        if not hasattr(django.db.backends.utils.CursorWrapper, "_original_execute"):
            django.db.backends.utils.CursorWrapper._original_execute = (
                django.db.backends.utils.CursorWrapper.execute
            )
            django.db.backends.utils.CursorWrapper._original_executemany = (
                django.db.backends.utils.CursorWrapper.executemany
            )

        tracker = self

        def tracked_execute(
            self_cursor: CursorWrapper, sql: str, params: Optional[Tuple[Any, ...]] = None
        ) -> Any:
            """Wrapper for CursorWrapper.execute to track query execution."""
            start_time = time.time()
            try:
                result = django.db.backends.utils.CursorWrapper._original_execute(
                    self_cursor, sql, params
                )
                execution_time = time.time() - start_time
                tracker.record_query(sql, params, execution_time, self_cursor.db.alias)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                tracker.record_query(f"FAILED: {sql}", params, execution_time, self_cursor.db.alias)
                raise

        def tracked_executemany(
            self_cursor: CursorWrapper, sql: str, param_list: List[Tuple[Any, ...]]
        ) -> Any:
            """Wrapper for CursorWrapper.executemany to track query execution."""
            start_time = time.time()
            try:
                result = django.db.backends.utils.CursorWrapper._original_executemany(
                    self_cursor, sql, param_list
                )
                execution_time = time.time() - start_time
                tracker.record_query(f"MANY: {sql}", None, execution_time, self_cursor.db.alias)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                tracker.record_query(
                    f"FAILED MANY: {sql}", None, execution_time, self_cursor.db.alias
                )
                raise

        django.db.backends.utils.CursorWrapper.execute = tracked_execute
        django.db.backends.utils.CursorWrapper.executemany = tracked_executemany

    def stop(self) -> None:
        """
        Stops tracking queries and restores the original cursor methods.
        """
        if not DJANGO_AVAILABLE or not self.is_active:
            return

        self.is_active = False

        if hasattr(django.db.backends.utils.CursorWrapper, "_original_execute"):
            django.db.backends.utils.CursorWrapper.execute = (
                django.db.backends.utils.CursorWrapper._original_execute
            )
            django.db.backends.utils.CursorWrapper.executemany = (
                django.db.backends.utils.CursorWrapper._original_executemany
            )

    def record_query(
        self, sql: str, params: Optional[Tuple[Any, ...]], time: float, alias: str = "default"
    ) -> None:
        """
        Records a single query execution and updates performance counters.

        Args:
            sql (str): The SQL query string.
            params (Optional[Tuple[Any, ...]]): The parameters used in the query.
            time (float): The execution time in seconds.
            alias (str): The database alias used.
        """
        if not self.is_active:
            return

        # Use C extension for high-performance query analysis if available
        if C_EXTENSIONS_AVAILABLE:
            try:
                # Send query to C extension for analysis (time in seconds)
                c_extensions.query_analyzer.analyze_query(sql.encode("utf-8"), time)
                # Increment the metrics engine counter
                if c_extensions.metrics_engine:
                    c_extensions.metrics_engine.increment_query_count()
            except Exception as e:
                # Log error but continue with Python fallback
                import logging

                logging.getLogger(__name__).debug(f"C extension query analysis failed: {e}")
        else:
            # Legacy C library support (for backward compatibility)
            try:
                current_dir = Path(__file__).parent
                lib_path = current_dir.parent / "c_core" / "libperformance.so"
                if lib_path.exists():
                    lib = ctypes.CDLL(str(lib_path))
                    lib.increment_query_count()
            except Exception:
                pass  # Silently fail if C library is not available

        # Python fallback (always maintain for compatibility and debugging)
        query_info = QueryInfo(sql=sql, time=time, params=params, alias=alias)
        self.queries.append(query_info)
        self.query_count += 1
        self.total_time += time

    # -- Query Analysis Methods --

    def get_duplicate_queries(self) -> Dict[str, List[QueryInfo]]:
        """
        Finds and groups identical queries to detect potential N+1 problems.

        Returns:
            Dict[str, List[QueryInfo]]: A dictionary where keys are normalized
                                        SQL queries and values are lists of
                                        QueryInfo objects for each execution.
        """
        query_groups = defaultdict(list)
        for query in self.queries:
            normalized = self._normalize_query(query.sql)
            query_groups[normalized].append(query)
        return {k: v for k, v in query_groups.items() if len(v) > 1}

    def _normalize_query(self, sql: str) -> str:
        """
        Normalizes an SQL query by replacing literal values with placeholders.

        Args:
            sql (str): The SQL query string.

        Returns:
            str: The normalized SQL query.
        """
        sql = re.sub(r"\b\d+\.?\d*\b", "?", sql)  # Handle decimal numbers
        sql = re.sub(r"'[^']*'", "?", sql)
        sql = re.sub(r'"[^"]*"', "?", sql)
        return sql.strip()

    def detect_n_plus_one(self) -> List[str]:
        """
        Detects potential N+1 query patterns from the tracked queries.

        Returns:
            List[str]: A list of strings describing potential N+1 patterns found.
        """
        # Use C extension for enhanced N+1 detection if available
        if C_EXTENSIONS_AVAILABLE:
            try:
                # Check if N+1 patterns detected by C extension
                has_n_plus_one = c_extensions.query_analyzer.detect_n_plus_one_patterns()
                if has_n_plus_one:
                    severity = c_extensions.query_analyzer.get_n_plus_one_severity()
                    cause = c_extensions.query_analyzer.get_n_plus_one_cause()
                    suggestion = c_extensions.query_analyzer.get_optimization_suggestion().decode(
                        "utf-8"
                    )

                    severity_levels = ["NONE", "MILD", "MODERATE", "HIGH", "SEVERE", "CRITICAL"]
                    severity_text = severity_levels[min(severity, 5)]

                    return [f"N+1 Pattern Detected: {severity_text} severity - {suggestion}"]
            except Exception as e:
                import logging

                logging.getLogger(__name__).debug(f"C extension N+1 detection failed: {e}")

        # Python fallback
        duplicates = self.get_duplicate_queries()
        n_plus_one_patterns = []
        for normalized_sql, query_list in duplicates.items():
            if len(query_list) > 3:
                n_plus_one_patterns.append(
                    f"Potential N+1: {len(query_list)} similar queries - {normalized_sql[:100]}..."
                )
        return n_plus_one_patterns

    def get_slow_queries(self, threshold_ms: float = 100.0) -> List[QueryInfo]:
        """
        Identifies queries that exceed a given execution time threshold.

        Args:
            threshold_ms (float): The time threshold in milliseconds.

        Returns:
            List[QueryInfo]: A list of queries that are slower than the threshold.
        """
        threshold_seconds = threshold_ms / 1000.0
        return [q for q in self.queries if q.time > threshold_seconds]

    def get_query_summary(self) -> Dict[str, Any]:
        """
        Generates a summary of query performance statistics.

        Returns:
            Dict[str, Any]: A dictionary containing performance metrics.
        """
        if not self.queries:
            return {
                "total_queries": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "slow_queries": 0,
                "duplicate_groups": 0,
                "n_plus_one_patterns": [],
            }

        query_times = [q.time for q in self.queries]
        duplicates = self.get_duplicate_queries()
        slow_queries = self.get_slow_queries()
        n_plus_one = self.detect_n_plus_one()

        return {
            "total_queries": len(self.queries),
            "total_time": sum(query_times),
            "avg_time": sum(query_times) / len(query_times),
            "max_time": max(query_times),
            "min_time": min(query_times),
            "slow_queries": len(slow_queries),
            "duplicate_groups": len(duplicates),
            "n_plus_one_patterns": n_plus_one,
        }


# --- Cache Tracking ---


class DjangoCacheTracker:
    """
    Tracks and analyzes Django cache operations.
    """

    def __init__(self) -> None:
        """Initializes the DjangoCacheTracker."""
        self.operations: List[Dict[str, Any]] = []
        self.hits: int = 0
        self.misses: int = 0
        self.sets: int = 0
        self.deletes: int = 0
        self.is_active: bool = False

    def start(self) -> None:
        """Starts tracking cache operations."""
        if not DJANGO_AVAILABLE:
            return
        self.is_active = True
        self.operations.clear()
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0

    def stop(self) -> None:
        """Stops tracking cache operations."""
        if not DJANGO_AVAILABLE or not self.is_active:
            return
        self.is_active = False

    def record_cache_operation(self, operation: str, key: str, time: float) -> None:
        """
        Records a single cache operation and updates counters.

        Args:
            operation (str): The type of cache operation (e.g., 'hit', 'miss').
            key (str): The cache key being accessed.
            time (float): The time taken for the operation.
        """
        if not self.is_active:
            return

        self.operations.append({"operation": operation, "key": key, "time": time})

        if operation == "hit":
            self.hits += 1
            self._update_c_counter("increment_cache_hits")
        elif operation == "miss":
            self.misses += 1
            self._update_c_counter("increment_cache_misses")
        elif operation == "set":
            self.sets += 1
        elif operation == "delete":
            self.deletes += 1

    def _update_c_counter(self, function_name: str) -> None:
        """Updates a performance counter in the C library."""
        try:
            current_dir = Path(__file__).parent
            lib_path = current_dir.parent / "c_core" / "libperformance.so"
            if lib_path.exists():
                lib = ctypes.CDLL(str(lib_path))
                getattr(lib, function_name)()
        except Exception:
            pass

    def get_cache_summary(self) -> Dict[str, Any]:
        """
        Generates a summary of cache performance statistics.

        Returns:
            Dict[str, Any]: A dictionary containing cache metrics.
        """
        total_gets = self.hits + self.misses
        hit_ratio = (self.hits / total_gets) if total_gets > 0 else 0.0

        return {
            "total_operations": len(self.operations),
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_ratio": hit_ratio,
            "total_gets": total_gets,
        }


# --- Performance Context Manager ---


class PerformanceContextManager:
    """
    A context manager to monitor performance of a block of code.

    Usage:
        with PerformanceContextManager("my_operation") as perf:
            # Code to be monitored
        print(perf.get_optimization_report())
    """

    def __init__(self, operation_name: str):
        """
        Initializes the context manager.

        Args:
            operation_name (str): A name for the operation being monitored.
        """
        self.operation_name = operation_name
        self.query_tracker = DjangoQueryTracker()
        self.cache_tracker = DjangoCacheTracker()
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def __enter__(self) -> "PerformanceContextManager":
        """Starts the performance trackers."""
        self._start_time = time.time()
        self.query_tracker.start()
        self.cache_tracker.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stops the performance trackers."""
        self._end_time = time.time()
        self.query_tracker.stop()
        self.cache_tracker.stop()

    def get_optimization_report(self) -> str:
        """
        Generates a human-readable report with optimization suggestions.

        Returns:
            str: A summary report of performance issues and suggestions.
        """
        query_summary = self.query_tracker.get_query_summary()
        cache_summary = self.cache_tracker.get_cache_summary()
        lines = []

        if query_summary["total_queries"] == 0:
            lines.append("ℹ️ No database queries detected (possible caching or static response).")
        elif query_summary["n_plus_one_patterns"]:
            lines.append("🚨 N+1 Query Patterns Detected:")
            for pattern in query_summary["n_plus_one_patterns"]:
                lines.append(f"   - {pattern}")
        else:
            lines.append(f"✅ {query_summary['total_queries']} queries executed efficiently.")

        if cache_summary["total_gets"] > 0:
            hit_ratio = cache_summary["hit_ratio"]
            if hit_ratio < 0.7:
                lines.append(
                    f"⚠️ Low cache hit ratio: {hit_ratio:.1%} - consider optimizing cache usage."
                )
            else:
                lines.append(f"✅ Good cache hit ratio: {hit_ratio:.1%}.")

        if query_summary["slow_queries"] > 0:
            lines.append(f"⚠️ {query_summary['slow_queries']} slow queries detected ( > 100ms).")

        return "\n".join(lines) if lines else "✅ No performance issues detected!"
