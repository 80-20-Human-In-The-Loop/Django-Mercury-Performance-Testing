"""
Formatting utilities for Mercury Visual Display.

This module contains functions for formatting test names, calculating grades,
and other display formatting operations.
"""


def format_test_name_for_display(test_name: str) -> str:
    """
    Format test name for better display in UI.

    Args:
        test_name: Full test name (e.g., 'app.tests.TestClass.test_method')

    Returns:
        Formatted name showing class.method for better context
    """
    parts = test_name.split(".")
    if len(parts) >= 2:
        # Show class.method for better context
        return f"{parts[-2]}.{parts[-1]}"
    return test_name


def guess_test_module_path(test_name: str) -> str:
    """
    Guess the full module path from a test name.

    This is a heuristic to help users navigate to failing tests.

    Args:
        test_name: Test name like 'TestClass.test_method'

    Returns:
        Guessed module path
    """
    # If it's already a full path, return it
    if "." in test_name and not test_name.startswith("Test"):
        return test_name

    # Otherwise, try to build a reasonable path
    parts = test_name.split(".")
    if len(parts) == 2 and parts[0].startswith("Test"):
        # Likely TestClass.test_method
        # Guess it might be in tests module
        return f"tests.{test_name}"

    return test_name


def calculate_simple_mercury_grade(
    query_count: int, response_time_ms: float
) -> str:
    """
    Calculate a grade using simplified Mercury scoring logic.

    This mimics Mercury's grading system when we only have minimal stats.
    Based on Mercury's scoring:
    - Response time: 30 points max
    - Query efficiency: 40 points max
    - We assume baseline memory (20 points) and no cache data (5 points)

    Args:
        query_count: Number of database queries
        response_time_ms: Response time in milliseconds

    Returns:
        Letter grade (S, A+, A, B, C, D, F)
    """
    # Score response time (0-30 points)
    if response_time_ms <= 10:
        response_score = 30.0
    elif response_time_ms <= 25:
        response_score = 27.0
    elif response_time_ms <= 50:
        response_score = 24.0
    elif response_time_ms <= 100:
        response_score = 20.0
    elif response_time_ms <= 200:
        response_score = 15.0
    elif response_time_ms <= 500:
        response_score = 10.0
    elif response_time_ms <= 1000:
        response_score = 5.0
    else:
        response_score = 0.0

    # Score query efficiency (0-40 points)
    if query_count <= 1:
        query_score = 40.0
    elif query_count <= 3:
        query_score = 36.0
    elif query_count <= 5:
        query_score = 32.0
    elif query_count <= 10:
        query_score = 25.0
    elif query_count <= 20:
        query_score = 15.0
    elif query_count <= 50:
        query_score = 8.0
    else:
        query_score = 0.0

    # Assume decent memory usage (15/20 points)
    memory_score = 15.0

    # Assume some caching (5/10 points)
    cache_score = 5.0

    # Calculate total score
    total_score = response_score + query_score + memory_score + cache_score

    # Apply Mercury's grade thresholds
    if total_score >= 95:
        return "S"
    if total_score >= 90:
        return "A+"
    if total_score >= 80:
        return "A"
    if total_score >= 70:
        return "B"
    if total_score >= 60:
        return "C"
    if total_score >= 50:
        return "D"
    else:
        return "F"


def format_query_info(query_count: int, n_plus_one: bool = False) -> str:
    """
    Format query information for display.

    Args:
        query_count: Number of queries
        n_plus_one: Whether N+1 was detected

    Returns:
        Formatted string with query info
    """
    if n_plus_one:
        return f"{query_count}Q ⚠️ N+1"
    elif query_count > 20:
        return f"{query_count}Q ⚠️"
    else:
        return f"{query_count}Q"


def format_response_time(time_ms: float) -> str:
    """
    Format response time for display.

    Args:
        time_ms: Time in milliseconds

    Returns:
        Formatted time string
    """
    if time_ms < 1000:
        return f"{time_ms:.0f}ms"
    else:
        return f"{time_ms/1000:.1f}s"


def truncate_test_name(test_name: str, max_length: int = 30) -> str:
    """
    Truncate test name for display if too long.

    Args:
        test_name: Full test name
        max_length: Maximum display length

    Returns:
        Truncated name with ellipsis if needed
    """
    if len(test_name) <= max_length:
        return test_name

    # Try to truncate at a sensible boundary
    if "." in test_name:
        parts = test_name.split(".")
        # Keep the test method name if possible
        if len(parts[-1]) < max_length - 3:
            remaining = max_length - len(parts[-1]) - 3
            prefix = ".".join(parts[:-1])[:remaining]
            return f"{prefix}...{parts[-1]}"

    # Simple truncation
    return test_name[: max_length - 3] + "..."
