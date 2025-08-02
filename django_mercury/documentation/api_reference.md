# API Reference

## DjangoMercuryAPITestCase

The main test case class that provides automatic performance monitoring for Django REST Framework tests.

### Class Methods

#### `setUpClass(cls)`
Called once before all tests in the class. Used to configure Mercury settings.

```python
@classmethod
def setUpClass(cls):
    super().setUpClass()
    cls.configure_mercury(enabled=True)
    cls.set_performance_thresholds({...})
```

#### `configure_mercury(**kwargs)`
Configure Mercury behavior for the test class.

**Parameters:**
- `enabled` (bool): Enable/disable Mercury monitoring. Default: `True`
- `auto_scoring` (bool): Enable automatic performance scoring. Default: `True`
- `auto_threshold_adjustment` (bool): Adjust thresholds based on operation type. Default: `True`
- `store_history` (bool): Store performance history in SQLite. Default: `True`
- `verbose_reporting` (bool): Print detailed reports for each test. Default: `False`
- `generate_summaries` (bool): Generate executive summary after tests. Default: `True`
- `educational_guidance` (bool): Show educational messages for failures. Default: `True`

```python
cls.configure_mercury(
    enabled=True,
    verbose_reporting=False,
    educational_guidance=True
)
```

#### `set_performance_thresholds(thresholds)`
Set custom performance thresholds for all tests in the class.

**Parameters:**
- `thresholds` (dict): Dictionary with threshold values
  - `response_time_ms` (float): Maximum response time in milliseconds
  - `query_count_max` (int): Maximum number of database queries
  - `memory_overhead_mb` (float): Maximum memory overhead in MB

```python
cls.set_performance_thresholds({
    'response_time_ms': 300,
    'query_count_max': 15,
    'memory_overhead_mb': 50
})
```

### Instance Methods

#### `set_test_performance_thresholds(thresholds)`
Set performance thresholds for the current test only.

**Parameters:**
Same as `set_performance_thresholds`, but applies only to the current test method.

```python
def test_expensive_operation(self):
    self.set_test_performance_thresholds({
        'response_time_ms': 1000,
        'query_count_max': 50
    })
    # Test code...
```

#### `run_comprehensive_analysis(**kwargs)`
Run a comprehensive performance analysis on a test function.

**Parameters:**
- `operation_name` (str): Name of the operation being tested
- `test_function` (callable): Function to execute and monitor
- `operation_type` (str): Type of operation ('list_view', 'detail_view', etc.)
- `expect_response_under` (float): Expected max response time in ms
- `expect_memory_under` (float): Expected max memory usage in MB
- `expect_queries_under` (int): Expected max query count
- `expect_cache_hit_ratio_above` (float): Expected min cache hit ratio
- `print_analysis` (bool): Whether to print analysis report
- `auto_detect_n_plus_one` (bool): Automatically detect N+1 patterns
- `show_scoring` (bool): Include scoring in report

**Returns:**
`EnhancedPerformanceMetrics_Python` object with all metrics

```python
metrics = self.run_comprehensive_analysis(
    operation_name="UserListView",
    test_function=lambda: self.client.get('/api/users/'),
    operation_type="list_view",
    expect_response_under=200,
    expect_queries_under=10,
    show_scoring=True
)
```

### Assertion Methods

#### `assertPerformance(monitor, **kwargs)`
Assert that performance metrics meet specified expectations.

**Parameters:**
- `monitor` (EnhancedPerformanceMonitor): The monitor instance
- `max_response_time` (float): Max response time in ms
- `max_memory_mb` (float): Max memory usage in MB
- `max_queries` (int): Max number of queries
- `min_cache_hit_ratio` (float): Min cache hit ratio

```python
self.assertPerformance(
    monitor,
    max_response_time=200,
    max_queries=10
)
```

#### `assertResponseTimeLess(metrics, milliseconds, msg=None)`
Assert response time is less than threshold.

#### `assertMemoryLess(metrics, megabytes, msg=None)`
Assert memory usage is less than threshold.

#### `assertQueriesLess(metrics, count, msg=None)`
Assert query count is less than threshold.

#### `assertPerformanceFast(metrics, msg=None)`
Assert performance is rated as 'fast' (< 100ms).

#### `assertPerformanceNotSlow(metrics, msg=None)`
Assert performance is not rated as 'slow' (< 500ms).

#### `assertNoNPlusOne(metrics, msg=None)`
Assert no N+1 query patterns were detected.

#### `assert_mercury_performance_excellent(metrics)`
Assert performance meets excellent standards (Grade A or above).

#### `assert_mercury_performance_production_ready(metrics)`
Assert performance is ready for production deployment.

## EnhancedPerformanceMonitor

Context manager for manual performance monitoring.

### Factory Functions

#### `monitor_django_view(operation_name, operation_type="view")`
Create a monitor for Django views.

```python
with monitor_django_view("UserDetailView") as monitor:
    response = view(request)

metrics = monitor.metrics
```

#### `monitor_django_model(operation_name)`
Create a monitor for Django model operations.

#### `monitor_serializer(operation_name)`
Create a monitor for serializer operations.

### Monitor Methods

#### `expect_response_under(milliseconds)`
Set response time expectation (chainable).

#### `expect_memory_under(megabytes)`
Set memory usage expectation (chainable).

#### `expect_queries_under(count)`
Set query count expectation (chainable).

#### `expect_cache_hit_ratio_above(ratio)`
Set cache hit ratio expectation (chainable).

```python
monitor = monitor_django_view("UserList")
    .expect_response_under(200)
    .expect_queries_under(10)
```

## EnhancedPerformanceMetrics_Python

Performance metrics object with analysis results.

### Properties

- `response_time` (float): Response time in milliseconds
- `memory_usage` (float): Total memory usage in MB
- `memory_overhead` (float): Memory overhead above Django baseline
- `query_count` (int): Number of database queries
- `cache_hits` (int): Number of cache hits
- `cache_misses` (int): Number of cache misses
- `cache_hit_ratio` (float): Cache hit ratio (0.0-1.0)
- `operation_name` (str): Name of the operation
- `operation_type` (str): Type of operation
- `performance_status` (PerformanceStatus): Overall performance rating
- `performance_score` (PerformanceScore): Detailed scoring breakdown
- `django_issues` (DjangoPerformanceIssues): Detected Django-specific issues

### Methods

#### `detailed_report()`
Get a detailed performance report as a string.

#### `get_performance_report_with_scoring()`
Get a performance report with scoring breakdown.

#### `get_memory_analysis_report()`
Get detailed memory usage analysis.

## DjangoPerformanceIssues

Container for Django-specific performance issues.

### Properties

- `has_n_plus_one` (bool): N+1 queries detected
- `excessive_queries` (bool): Too many queries for operation type
- `memory_intensive` (bool): High memory usage
- `poor_cache_performance` (bool): Low cache hit ratio
- `slow_serialization` (bool): Serialization bottleneck detected
- `inefficient_pagination` (bool): Pagination issues detected
- `missing_db_indexes` (bool): Potential missing indexes
- `n_plus_one_analysis` (NPlusOneAnalysis): Detailed N+1 analysis

### Methods

#### `get_issue_summary()`
Get list of detected issues as human-readable strings.

## NPlusOneAnalysis

Detailed N+1 query pattern analysis.

### Properties

- `severity_level` (int): Severity from 0-5
- `severity_text` (str): Human-readable severity
- `estimated_cause` (int): Cause code
- `cause_text` (str): Human-readable cause
- `fix_suggestion` (str): Specific fix recommendation
- `query_count` (int): Number of queries in pattern

## PerformanceScore

Performance scoring with detailed breakdown.

### Properties

- `total_score` (float): Total score (0-100)
- `grade` (str): Letter grade (S, A+, A, B, C, D, F)
- `response_time_score` (float): Response time component
- `query_efficiency_score` (float): Query efficiency component
- `memory_efficiency_score` (float): Memory efficiency component
- `n_plus_one_penalty` (float): Points deducted for N+1
- `cache_performance_score` (float): Cache performance component
- `points_lost` (List[str]): List of point deductions
- `points_gained` (List[str]): List of point gains
- `optimization_impact` (Dict[str, float]): Potential score improvements

## Configuration Classes

### MercuryConfiguration

Configuration object for Mercury settings.

```python
from performance_testing.python_bindings.mercury_config import (
    get_mercury_config,
    update_mercury_config,
    configure_for_environment
)

# Get current config
config = get_mercury_config()

# Get environment-specific config
prod_config = configure_for_environment('production')
```

### PerformanceThresholds

Performance threshold configuration.

```python
from performance_testing.python_bindings.mercury_config import PerformanceThresholds

thresholds = PerformanceThresholds(
    response_time_ms=200.0,
    memory_overhead_mb=30.0,
    query_count_max=10,
    cache_hit_ratio_min=0.7
)
```

## Utility Functions

### Color Output

```python
from performance_testing.python_bindings.colors import colors, ColorMode

# Configure color output
colors = PerformanceColors(ColorMode.AUTO)

# Colorize text
colored_text = colors.colorize("Success", "#75a743", bold=True)

# Format performance status
status_text = colors.format_performance_status("excellent")
```

### Validation

```python
from performance_testing.python_bindings.validation import (
    validate_mercury_config,
    validate_thresholds,
    sanitize_operation_name
)

# Validate configuration
is_valid, errors = validate_mercury_config(config_dict)

# Sanitize operation names
safe_name = sanitize_operation_name(user_input)
```

### Thread Safety

```python
from performance_testing.python_bindings.thread_safety import (
    ThreadSafeCounter,
    ThreadSafeDict,
    synchronized
)

# Thread-safe counter
counter = ThreadSafeCounter()
counter.increment()

# Thread-safe dictionary
cache = ThreadSafeDict()
cache.set("key", "value")

# Synchronized method
class MyClass:
    def __init__(self):
        self._lock = threading.Lock()
    
    @synchronized()
    def thread_safe_method(self):
        # Method is automatically synchronized
        pass
```

## Constants

```python
from performance_testing.python_bindings.constants import (
    RESPONSE_TIME_THRESHOLDS,
    MEMORY_THRESHOLDS,
    QUERY_COUNT_THRESHOLDS,
    N_PLUS_ONE_THRESHOLDS,
    DJANGO_BASELINE_MEMORY_MB
)

# Use predefined thresholds
if response_time > RESPONSE_TIME_THRESHOLDS['ACCEPTABLE']:
    # Handle slow response
    pass
```