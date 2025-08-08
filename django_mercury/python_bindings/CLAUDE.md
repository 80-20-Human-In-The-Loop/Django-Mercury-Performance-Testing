# Django Mercury Python Standards

> **Clear code removes barriers to education. When we write clearly, we make learning accessible to everyone.**

## Core Philosophy

Django Mercury follows the **80/20 Human-in-the-Loop** principle:
- **80% Automation**: The framework handles monitoring, detection, and analysis
- **20% Human Control**: You make decisions and optimizations
- **100% Human Responsibility**

Other core principals include:
- **Educational First**: Tools teach optimization, not just find problems
- **Global Access**: Simple English that translates well to Arabic, French, Spanish
- **Graceful Degradation**: Python fallbacks when C extensions unavailable
- **Performance Conscious**: Fast tests, efficient code, minimal overhead

## Project Configuration

### Build System (pyproject.toml)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
python_requires = ">=3.10"
dependencies = [
    "Django>=3.2",
    "djangorestframework>=3.12.0",
    "psutil>=5.9.0",
    "jsonschema>=4.0.0",
]
```

### Code Quality Tools

**Black Configuration:**
```toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
```

**isort Configuration:**
```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
```

**Ruff Configuration:**
```toml
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "W", "C90", "I", "N"]
```

**MyPy Configuration:**

*Current State (Reality):*
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Currently false
ignore_missing_imports = true
```

*Target State (Goal - ALL new code MUST follow):*
```toml
[tool.mypy]
strict = true  # Goal for all new modules
python_version = "3.10"
warn_unused_ignores = true
disallow_untyped_defs = true  # Required for new code
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
show_error_codes = true
```

## Type Hints Standards (REQUIRED for New Code)

### Why Type Hints Matter
- **AI Agents**: Type hints help AI understand your code
- **Global Teams**: Clear types reduce confusion across languages
- **Fewer Bugs**: MyPy catches errors before runtime
- **Better Documentation**: Types explain what functions expect

### Current Implementation Patterns
```python
from typing import Optional, Dict, List, Tuple, Union, Any, TYPE_CHECKING

def validate_mercury_config(
    config: Dict[str, Any]
) -> Tuple[bool, Optional[List[str]]]:
    """Returns (is_valid, error_messages)."""
    pass
```

**Complex Return Types:**
```python
def get_metrics(
    self
) -> Tuple[float, float, int, Optional[Dict[str, Any]]]:
    """Returns (response_time, memory, queries, metadata)."""
    pass
```

**TYPE_CHECKING for Circular Imports:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_mercury.monitor import PerformanceMonitor
```

### Dataclass Patterns (9 files using dataclasses)

**Performance Metrics:**
```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class PerformanceMetrics:
    """Core performance metrics with defaults."""
    response_time: float = 0.0
    memory_overhead: float = 0.0
    query_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    n_plus_one_detected: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Configuration Dataclasses:**
```python
@dataclass
class ThresholdConfig:
    """Threshold configuration with validation."""
    response_time_ms: float = 200.0
    memory_overhead_mb: float = 50.0
    query_count_max: int = 20
    cache_hit_ratio_min: float = 0.7
    
    def __post_init__(self):
        """Validate thresholds on initialization."""
        if self.response_time_ms < 0:
            raise ValueError("Response time cannot be negative")
```

## Import Organization

### Standard Import Order
```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Dict, Optional, List

# Third-party imports
import django
from django.test import TestCase
from rest_framework.test import APITestCase

# Local imports - relative for internal modules
from .monitor import PerformanceMonitor
from .constants import MAX_VALUES, THRESHOLDS
from ..utils import format_time
```

### Lazy Loading Pattern (__init__.py)
```python
"""Django Mercury - Performance Testing Framework

Lazy loading for optimal import performance.
"""

__version__ = "0.5.10"

# Core exports - always available
from .python_bindings.django_integration_mercury import (
    DjangoMercuryAPITestCase,
    DjangoPerformanceAPITestCase,
)

# Lazy imports for optional components
def __getattr__(name):
    """Lazy load heavy components only when needed."""
    if name == "PerformanceMonitor":
        from .monitor import PerformanceMonitor
        return PerformanceMonitor
    elif name == "monitor_django_view":
        from .monitor import monitor_django_view
        return monitor_django_view
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "DjangoMercuryAPITestCase",
    "DjangoPerformanceAPITestCase",
    "PerformanceMonitor",
    "monitor_django_view",
]
```

## Error Handling Patterns

### Graceful C Extension Fallback
```python
try:
    # Try C extension first
    from django_mercury.c_core import performance_monitor
    HAS_C_EXTENSIONS = True
except ImportError:
    # Fall back to pure Python
    HAS_C_EXTENSIONS = False
    from django_mercury.python_bindings.fallback import performance_monitor

class PerformanceMonitor:
    def __init__(self):
        if HAS_C_EXTENSIONS:
            self._impl = performance_monitor.CMonitor()
        else:
            self._impl = performance_monitor.PythonMonitor()
            if not self._warning_shown:
                logger.warning("C extensions not available, using Python fallback")
```

### Validation with Detailed Errors
```python
def validate_thresholds(
    thresholds: Dict[str, Union[int, float]]
) -> Tuple[bool, Optional[List[str]]]:
    """Validate with detailed error messages."""
    errors = []
    
    if "response_time_ms" in thresholds:
        if thresholds["response_time_ms"] < 0:
            errors.append("Response time cannot be negative")
        elif thresholds["response_time_ms"] > MAX_VALUES["RESPONSE_TIME_MS"]:
            errors.append(f"Response time exceeds maximum {MAX_VALUES['RESPONSE_TIME_MS']}ms")
    
    if errors:
        logger.warning(f"Validation failed: {errors}")
        return False, errors
    
    return True, None
```

## Django Integration Patterns

### Test Case Architecture
```python
class DjangoMercuryAPITestCase(APITestCase):
    """Enhanced test case with automatic performance monitoring."""
    
    # Class-level configuration
    _mercury_enabled: bool = True
    _auto_scoring: bool = True
    _thresholds: Dict[str, Any] = {}
    
    @classmethod
    def setUpClass(cls):
        """Initialize Mercury at class level."""
        super().setUpClass()
        cls._load_configuration()
        cls._setup_monitoring()
    
    def setUp(self):
        """Per-test setup with monitoring."""
        super().setUp()
        if self._mercury_enabled:
            self._start_test_monitoring()
    
    def tearDown(self):
        """Cleanup and report."""
        if self._mercury_enabled:
            self._finalize_test_monitoring()
        super().tearDown()
```

### Context Manager Pattern
```python
from contextlib import contextmanager

@contextmanager
def monitor_django_view(operation_name: str, **kwargs):
    """Context manager for manual monitoring."""
    monitor = PerformanceMonitor(operation_name, **kwargs)
    try:
        monitor.start()
        yield monitor
    finally:
        monitor.stop()
        if monitor.auto_report:
            monitor.print_report()
```

## Logging Standards

### Logger Configuration
```python
import logging
from typing import Optional

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with consistent configuration."""
    logger = logging.getLogger(f"django_mercury.{name}")
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)  # Default level
    
    return logger
```

### Logging Patterns
```python
logger = get_logger(__name__)

class PerformanceMonitor:
    def start(self):
        logger.debug(f"Starting monitoring for {self.operation_name}")
        try:
            self._do_start()
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}", exc_info=True)
            raise
```

## Documentation Standards (Write for the World)

### Writing Principles
1. **Simple English**: Use words that translate well
2. **Active Voice**: "The function returns data" not "Data is returned"
3. **One Idea Per Line**: Short sentences. Clear meaning.
4. **Explain Why**: Help developers understand the purpose

### Module Docstrings
```python
"""Performance monitoring module for Django Mercury.

This module provides the core monitoring functionality including:
- Real-time performance tracking
- Memory profiling
- Query analysis
- N+1 detection

Example:
    >>> from django_mercury import monitor_django_view
    >>> with monitor_django_view("UserListView") as monitor:
    ...     response = client.get("/api/users/")
    >>> print(monitor.metrics)
"""
```

### Function Documentation (Google Style + Educational Context)
```python
def run_comprehensive_analysis(
    self,
    operation_name: str,
    test_function: callable,
    operation_type: str = "general",
    **kwargs
) -> Optional[PerformanceMetrics]:
    """Run performance analysis on a test function.
    
    This function helps you find performance problems in your Django views.
    It measures response time, counts database queries, and tracks memory.
    
    Args:
        operation_name: Name for the operation (example: "UserListView").
        test_function: Function that runs the test (no parameters).
        operation_type: Type of view being tested. Options:
            - 'list_view': Shows multiple items
            - 'detail_view': Shows one item
            - 'search_view': Searches for items
            - 'create_view': Creates new items
        **kwargs: Extra settings (see documentation for full list).
    
    Returns:
        PerformanceMetrics with test results, or None if Mercury is disabled.
        The metrics include response time, query count, and memory usage.
    
    Raises:
        PerformanceThresholdExceeded: Test was too slow or used too many queries.
        ValidationError: Settings are invalid.
    
    Example:
        >>> # Test a user search endpoint
        >>> metrics = self.run_comprehensive_analysis(
        ...     "UserSearch",
        ...     lambda: self.client.get("/api/users/search?q=test"),
        ...     operation_type="search_view"
        ... )
        >>> print(f"Took {metrics.response_time}ms")
    
    Note:
        This function teaches you about performance. It shows which
        operations are slow and suggests improvements.
    """
    pass
```

## Testing Standards (Tests Must Be Fast!)

### Test Organization
```
tests/
├── monitor/                      # Performance monitor tests
├── django_integration/
│   ├── mercury_api/             # Mercury API tests
│   └── performance_api/         # Performance API tests  
├── hooks/                       # Hook system tests
├── bindings/                    # C binding tests
├── core/                        # Core functionality tests
├── config/                      # Configuration tests
└── integration/                 # Full integration tests
```

### Running Tests
```bash
# Run all tests with timing analysis
python test_runner.py

# Run with coverage reporting
python test_runner.py --coverage

# Run specific module tests
python test_runner.py --module monitor

# Run C extension tests
./c_test_runner.sh

# CI mode (minimal output)
python test_runner.py --ci
```

### Test Performance Requirements

Our test runner uses color coding for test speed:
- **GREEN (<0.1s)**: Excellent! This is the target.
- **YELLOW (0.1-0.5s)**: Acceptable but could be faster.
- **RED (0.5-2s)**: Too slow! Needs optimization.
- **CRITICAL (>2s)**: Unacceptable! Must fix immediately.

**Rules for Fast Tests:**
1. **No sleep() calls**: Use mocks instead of waiting
2. **Mock external services**: Don't make real HTTP requests
3. **Use in-memory databases**: SQLite :memory: for tests
4. **Minimal fixtures**: Create only needed test data
5. **Batch database operations**: Reduce query count

### Test Patterns
```python
import unittest
from unittest.mock import Mock, patch, MagicMock

class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up expensive resources once."""
        cls.shared_resource = create_expensive_resource()
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
        self.mock_client = Mock()
    
    @patch('django_mercury.monitor.time.perf_counter')
    def test_timing_accuracy(self, mock_time):
        """Test accurate time measurement."""
        mock_time.side_effect = [0, 0.1, 0.2]  # Simulate time passing
        
        with monitor_django_view("test") as mon:
            pass
        
        self.assertAlmostEqual(mon.metrics.response_time, 200.0, places=1)
```

## Constants and Configuration

### Constants Module Pattern
```python
# constants.py
from typing import Dict, Any

# Maximum values for validation
MAX_VALUES: Dict[str, Any] = {
    "RESPONSE_TIME_MS": 60000,  # 1 minute
    "MEMORY_MB": 1024,          # 1 GB
    "QUERY_COUNT": 1000,
    "OPERATION_NAME_LENGTH": 255,
}

# Threshold categories
RESPONSE_TIME_THRESHOLDS = {
    "EXCELLENT": 50,
    "GOOD": 100,
    "ACCEPTABLE": 200,
    "SLOW": 500,
    "CRITICAL": 1000,
}

# Environment variables
ENV_VARS = {
    "MERCURY_ENABLED": "DJANGO_MERCURY_ENABLED",
    "MERCURY_CONFIG": "DJANGO_MERCURY_CONFIG_PATH",
    "FORCE_COLOR": "FORCE_COLOR",
}
```

## Color and Formatting

### Color System (colors.py pattern)
```python
from enum import Enum
from typing import Optional

class ColorScheme:
    """Centralized color definitions."""
    EXCELLENT = "#73bed3"
    GOOD = "#4f8fba"
    WARNING = "#de9e41"
    CRITICAL = "#a53030"
    SUCCESS = "#75a743"

class PerformanceColors:
    """Handle colored output with environment awareness."""
    
    def __init__(self, mode: ColorMode = ColorMode.AUTO):
        self.mode = mode
        self._supports_color = self._detect_color_support()
    
    def colorize(self, text: str, color: str, bold: bool = False) -> str:
        """Apply color if supported."""
        if not self._supports_color:
            return text
        # Apply ANSI color codes
        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"
```

## Performance Considerations

### Memory Management
```python
class PerformanceMonitor:
    """Monitor with automatic cleanup."""
    
    def __init__(self):
        self._data = []
        self._max_samples = 10000  # Prevent unbounded growth
    
    def add_sample(self, sample):
        """Add sample with automatic pruning."""
        self._data.append(sample)
        if len(self._data) > self._max_samples:
            # Keep most recent samples
            self._data = self._data[-self._max_samples:]
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()
```

### Lazy Evaluation
```python
class PerformanceReport:
    """Report with lazy calculation."""
    
    def __init__(self, metrics):
        self._metrics = metrics
        self._score = None  # Calculate on demand
    
    @property
    def score(self):
        """Calculate score only when accessed."""
        if self._score is None:
            self._score = self._calculate_score()
        return self._score
```

## Strict Typing Migration (REQUIRED for New Code)

### Current vs Target
- **Current**: `disallow_untyped_defs = false` (legacy code)
- **Required for NEW code**: Full strict typing
- **Goal**: 100% type coverage by 2025

### Rules for New Code
**ALL new Python files MUST:**
1. Start with `# mypy: strict` comment
2. Type ALL function parameters and returns
3. Type ALL class attributes
4. Pass `mypy --strict` with zero errors

### Migration Strategy
1. Enable strict typing per module:
   ```python
   # mypy: strict
   ```

2. Gradual conversion pattern:
   ```python
   # Before
   def process_data(data):
       return data.get("value")
   
   # After
   def process_data(data: Dict[str, Any]) -> Optional[Any]:
       return data.get("value")
   ```

3. Use Protocol for duck typing:
   ```python
   from typing import Protocol
   
   class Monitorable(Protocol):
       def get_metrics(self) -> Dict[str, float]: ...
   ```

## Educational Comments

### Write Comments That Teach
```python
def detect_n_plus_one_queries(queries: List[QueryDict]) -> bool:
    """Detect N+1 query problems in Django views.
    
    N+1 problem explained:
    - You load a list of users (1 query)
    - For each user, you load their profile (N queries)
    - Total: N+1 queries instead of 1-2 optimized queries
    
    This causes slow page loads, especially with many items.
    """
    # Group similar queries to find repeated patterns
    # Example: 'SELECT * FROM profile WHERE user_id = ?' repeated 100 times
    similar_groups = self._group_similar_queries(queries)
    
    for group in similar_groups:
        if len(group) > 10:  # More than 10 similar queries = problem
            # Django solutions:
            # 1. Use select_related() for foreign keys
            # 2. Use prefetch_related() for many-to-many
            # 3. Use only() to load specific fields
            return True
    
    return False
```

### Avoid Complex Language
```python
# Bad: Uses idioms and complex terms
def kick_off_perf_monitoring():  # "kick off" doesn't translate
    """Fire up the monitoring engine and get the ball rolling."""
    
# Good: Simple and clear
def start_performance_monitoring():
    """Start monitoring application performance."""
```

## Common Patterns

### Singleton Pattern for Configuration
```python
class MercuryConfig:
    """Singleton configuration manager."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._initialized = True
```

### Factory Pattern for Monitors
```python
def create_monitor(monitor_type: str, **kwargs) -> PerformanceMonitor:
    """Factory for creating appropriate monitor type."""
    monitors = {
        "django": DjangoPerformanceMonitor,
        "api": APIPerformanceMonitor,
        "celery": CeleryPerformanceMonitor,
    }
    
    monitor_class = monitors.get(monitor_type, PerformanceMonitor)
    return monitor_class(**kwargs)
```

## Security Considerations

### Input Sanitization
```python
def sanitize_operation_name(operation_name: str) -> str:
    """Sanitize user input for safety."""
    # Remove dangerous characters
    dangerous_chars = ["<", ">", "&", '"', "'", "\n", "\r", "\0"]
    sanitized = operation_name
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    # Truncate to safe length
    max_length = MAX_VALUES["OPERATION_NAME_LENGTH"]
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized
```

---

*These standards help Django Mercury stay accessible to developers worldwide. Follow them to make performance testing available to everyone.*

**Remember**: We write code for students learning in Gaza, developers building in Nigeria, and engineers optimizing in Silicon Valley. Clear code changes the world.