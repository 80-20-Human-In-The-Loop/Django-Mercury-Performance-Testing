# Django Mercury Performance Testing - Complete API Reference

This comprehensive API reference covers the Django Mercury Performance Testing framework's two main test case classes and their complete feature set.

## Table of Contents

1. [Overview](#overview)
2. [Class Hierarchy](#class-hierarchy)
3. [DjangoPerformanceAPITestCase](#djangoperformanceapitestcase)
4. [DjangoMercuryAPITestCase](#djangomercuryapitestcase)
5. [Helper Classes](#helper-classes)
6. [Usage Examples](#usage-examples)
7. [Best Practices](#best-practices)

---

## Overview

The Django Mercury Performance Testing framework provides two powerful test case classes for comprehensive performance monitoring of Django REST Framework applications:

- **`DjangoPerformanceAPITestCase`**: A foundational performance testing class with rich assertions and manual monitoring capabilities
- **`DjangoMercuryAPITestCase`**: An intelligent, self-managing performance test case with automatic monitoring, scoring, and educational guidance

Both classes extend Django REST Framework's `APITestCase` and provide seamless integration with Django applications.

---

## Class Hierarchy

```python
rest_framework.test.APITestCase
    ↓
DjangoPerformanceAPITestCase
    ↓
DjangoMercuryAPITestCase
```

---

## DjangoPerformanceAPITestCase

**Module**: `django_mercury.python_bindings.django_integration`  
**Inheritance**: `rest_framework.test.APITestCase`

The foundational performance testing class that provides comprehensive performance monitoring capabilities with explicit control over the monitoring process.

### Core Assertion Methods

#### `assertPerformance(monitor, max_response_time=None, max_memory_mb=None, max_queries=None, min_cache_hit_ratio=None, msg=None)`

Asserts that a full suite of performance metrics meets the specified thresholds.

**Parameters:**
- `monitor` (`EnhancedPerformanceMonitor`): The monitor instance after its context has exited
- `max_response_time` (`Optional[float]`): Maximum acceptable response time in milliseconds
- `max_memory_mb` (`Optional[float]`): Maximum acceptable memory usage in megabytes
- `max_queries` (`Optional[int]`): Maximum acceptable number of database queries
- `min_cache_hit_ratio` (`Optional[float]`): Minimum acceptable cache hit ratio (0.0-1.0)
- `msg` (`Optional[str]`): Custom message for assertion failure

**Example:**
```python
with self.monitor_django_view("user_list") as monitor:
    response = self.client.get('/api/users/')

self.assertPerformance(
    monitor,
    max_response_time=200.0,
    max_memory_mb=50.0,
    max_queries=10,
    min_cache_hit_ratio=0.7
)
```

### Threshold-Based Assertions

#### `assertResponseTimeLess(metrics_or_monitor, milliseconds, msg=None)`

Asserts that the response time is less than a given threshold.

**Parameters:**
- `metrics_or_monitor` (`Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python]`): The metrics object or monitor
- `milliseconds` (`float`): Response time threshold in milliseconds
- `msg` (`Optional[str]`): Custom message for assertion failure

#### `assertMemoryLess(metrics_or_monitor, megabytes, msg=None)`

Asserts that memory usage is less than a given threshold.

**Parameters:**
- `metrics_or_monitor` (`Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python]`): The metrics object or monitor
- `megabytes` (`float`): Memory usage threshold in megabytes
- `msg` (`Optional[str]`): Custom message for assertion failure

#### `assertQueriesLess(metrics_or_monitor, count, msg=None)`

Asserts that the number of database queries is less than a given threshold.

**Parameters:**
- `metrics_or_monitor` (`Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python]`): The metrics object or monitor
- `count` (`int`): Database query count threshold
- `msg` (`Optional[str]`): Custom message for assertion failure

### Status-Based Assertions

#### `assertPerformanceFast(metrics_or_monitor, msg=None)`

Asserts that performance is rated as 'fast' (typically < 100ms response time).

#### `assertPerformanceNotSlow(metrics_or_monitor, msg=None)`

Asserts that performance is not rated as 'slow' (typically >= 500ms response time).

#### `assertMemoryEfficient(metrics_or_monitor, msg=None)`

Asserts that memory usage is not considered intensive.

### Django-Specific Assertions

#### `assertNoNPlusOne(metrics_or_monitor, msg=None)`

Asserts that no N+1 query patterns were detected.

#### `assertGoodCachePerformance(metrics_or_monitor, min_hit_ratio=0.7, msg=None)`

Asserts that the cache hit ratio meets a minimum threshold.

### Monitor Creation Methods

#### `monitor_django_view(operation_name)`

Creates a monitor with full hooks for a Django view operation.

**Parameters:**
- `operation_name` (`str`): Descriptive name for the operation

**Returns:** `EnhancedPerformanceMonitor`

#### `monitor_django_model(operation_name)`

Creates a monitor specialized for Django model operations.

#### `monitor_serializer(operation_name)`

Creates a monitor specialized for serializer operations.

### Measurement and Analysis

#### `measure_django_view(url, method='GET', data=None, format=None, operation_name=None, **kwargs)`

Measures the performance of a Django view with comprehensive, automated monitoring.

**Parameters:**
- `url` (`str`): The URL of the view to measure
- `method` (`str`): HTTP method ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')
- `data` (`Optional[Dict[str, Any]]`): Request data for POST, PUT, or PATCH methods
- `format` (`Optional[str]`): Request format (e.g., 'json')
- `operation_name` (`Optional[str]`): Custom operation name (auto-generated if None)
- `**kwargs`: Additional arguments passed to the client request

**Returns:** `EnhancedPerformanceMetrics_Python`

#### `run_comprehensive_analysis(operation_name, test_function, operation_type='general', **options)`

Runs comprehensive, Django-aware performance analysis with built-in scoring system.

**Parameters:**
- `operation_name` (`str`): Descriptive name for the operation
- `test_function` (`Callable`): Function to execute and monitor
- `operation_type` (`str`): Type of operation (default: 'general')
- `expect_response_under` (`Optional[float]`): Expected maximum response time in ms
- `expect_memory_under` (`Optional[float]`): Expected maximum memory usage in MB
- `expect_queries_under` (`Optional[int]`): Expected maximum query count
- `expect_cache_hit_ratio_above` (`Optional[float]`): Expected minimum cache hit ratio
- `print_analysis` (`bool`): Whether to print analysis report (default: True)
- `auto_detect_n_plus_one` (`bool`): Whether to detect N+1 patterns (default: True)
- `show_scoring` (`bool`): Whether to show performance scoring (default: True)
- `enable_educational_guidance` (`bool`): Whether to show educational guidance (default: False)
- `operation_context` (`Optional[Dict[str, Any]]`): Additional context for analysis

**Returns:** `EnhancedPerformanceMetrics_Python`

### Dashboard and Reporting

#### `create_enhanced_performance_dashboard_with_scoring(metrics, title='Enhanced Performance Dashboard')`

Creates a performance dashboard that includes a comprehensive performance score.

#### `create_enhanced_dashboard(metrics, title='Enhanced Performance Dashboard')`

Creates a comprehensive dashboard with Django-specific insights.

---

## DjangoMercuryAPITestCase

**Module**: `django_mercury.python_bindings.django_integration_mercury`  
**Inheritance**: `DjangoPerformanceAPITestCase`

An intelligent, self-managing performance test case that automatically monitors all test methods and provides comprehensive analysis with minimal configuration.

### Class-Level Configuration

#### Class Attributes

```python
_mercury_enabled: bool = True                    # Enable/disable Mercury features
_auto_scoring: bool = True                       # Enable automatic performance scoring
_auto_threshold_adjustment: bool = True          # Enable intelligent threshold adjustment
_generate_summaries: bool = True                 # Generate executive summaries
_verbose_reporting: bool = False                 # Enable verbose output for each test
_educational_guidance: bool = True               # Enable educational guidance on failures

_custom_thresholds: Optional[Dict[str, Any]] = None      # Class-level thresholds
_per_test_thresholds: Optional[Dict[str, Any]] = None    # Per-test threshold overrides

_test_executions: List[EnhancedPerformanceMetrics_Python] = []  # Test execution history
_test_failures: List[str] = []                                  # Failed test names
_optimization_recommendations: List[str] = []                  # Optimization suggestions
```

### Class Configuration Methods

#### `configure_mercury(enabled=True, auto_scoring=True, auto_threshold_adjustment=True, generate_summaries=True, verbose_reporting=False, educational_guidance=True)`
Configures Mercury's behavior for the entire test class.

**Parameters:**
- `enabled` (`bool`): Enable/disable Mercury features (default: True)
- `auto_scoring` (`bool`): Enable automatic performance scoring (default: True)
- `auto_threshold_adjustment` (`bool`): Enable smart threshold adjustments (default: True)
- `generate_summaries` (`bool`): Generate executive summaries (default: True)
- `verbose_reporting` (`bool`): Enable verbose reporting for each test (default: False)
- `educational_guidance` (`bool`): Enable educational guidance on failures (default: True)

**Example:**
```python
@classmethod
def setUpClass(cls):
    super().setUpClass()
    cls.configure_mercury(
        auto_scoring=True,
        verbose_reporting=True,
        educational_guidance=True
    )
```

#### `set_performance_thresholds(thresholds)`
Sets custom performance thresholds for all tests in the class.

**Parameters:**
- `thresholds` (`Dict[str, Union[int, float]]`): Performance threshold dictionary

**Supported Threshold Keys:**
- `response_time_ms`: Maximum response time in milliseconds
- `query_count_max`: Maximum database query count
- `memory_overhead_mb`: Maximum memory overhead in megabytes
- `cache_hit_ratio_min`: Minimum cache hit ratio (0.0-1.0)

**Example:**
```python
@classmethod
def setUpClass(cls):
    super().setUpClass()
    cls.set_performance_thresholds({
        'response_time_ms': 200,
        'query_count_max': 10,
        'memory_overhead_mb': 50
    })
```

#### `tearDownClass()`

Generates comprehensive executive summary after all tests complete.

### Instance Configuration Methods

#### `set_test_performance_thresholds(thresholds)`

Sets custom performance thresholds for a single test method, overriding class-level settings.

**Parameters:**
- `thresholds` (`Dict[str, Union[int, float]]`): Performance threshold dictionary

**Example:**
```python
def test_complex_operation(self):
    self.set_test_performance_thresholds({
        'response_time_ms': 500,  # Allow more time for complex operation
        'query_count_max': 20
    })
    response = self.client.get('/api/complex-data/')
    self.assertEqual(response.status_code, 200)
```

### Property Accessors

#### `mercury_override_thresholds`

Context manager for temporarily overriding performance thresholds within a specific code block.

**Returns:** `MercuryThresholdOverride` context manager

**Example:**
```python
def test_bulk_operation(self):
    with self.mercury_override_thresholds({
        'query_count_max': 50,
        'response_time_ms': 1000
    }):
        response = self.client.post('/api/bulk-create/', data)
        self.assertEqual(response.status_code, 201)
```

### Mercury-Specific Assertions

#### `assert_mercury_performance_excellent(metrics)`

Asserts that performance meets excellence standards (typically A+ or S grade).

**Parameters:**
- `metrics` (`EnhancedPerformanceMetrics_Python`): Performance metrics to evaluate

#### `assert_mercury_performance_production_ready(metrics)`

Asserts that performance meets production readiness standards (typically B grade or better).

**Parameters:**
- `metrics` (`EnhancedPerformanceMetrics_Python`): Performance metrics to evaluate

### Special Methods

#### `__init__(*args, **kwargs)`

Enhanced initialization that sets up Mercury's intelligent monitoring system.

#### `setUp()`

Enhanced setup method that initializes Mercury's monitoring context for each test.

### Automatic Features

#### Automatic Test Method Wrapping

Mercury automatically wraps all `test_*` methods with performance monitoring. No manual setup required.

```python
def test_user_list(self):
    # This method is automatically monitored by Mercury
    response = self.client.get('/api/users/')
    self.assertEqual(response.status_code, 200)
    # Mercury automatically analyzes performance and provides scoring
```

#### Intelligent Operation Detection

Mercury automatically detects operation types based on:
- Method name patterns (`test_list_*`, `test_create_*`, etc.)
- URL patterns
- HTTP methods used
- Response analysis

**Detected Operation Types:**
- `list_view`: List/index operations
- `detail_view`: Detail/show operations  
- `create_view`: Create/POST operations
- `update_view`: Update/PUT/PATCH operations
- `delete_view`: Delete operations
- `search_view`: Search/filter operations
- `authentication`: Login/auth operations

#### Intelligent Threshold Calculation

Mercury calculates context-aware thresholds based on:
- Operation type complexity
- Historical performance data
- Application context
- Custom overrides

---

## Helper Classes

### MercuryThresholdOverride

Context manager for temporarily overriding performance thresholds.

```python
class MercuryThresholdOverride:
    def __init__(self, test_instance)
    def __call__(self, thresholds: Dict[str, Union[int, float]])
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
```

**Usage:**
```python
with self.mercury_override_thresholds({'response_time_ms': 500}):
    # Code with temporary threshold override
    pass
```

### Data Classes

#### PerformanceBaseline

Tracks performance baselines for operations.

```python
@dataclass
class PerformanceBaseline:
    operation_type: str
    avg_response_time: float
    avg_memory_usage: float
    avg_query_count: float
    sample_count: int
    last_updated: str
    
    def update_with_new_measurement(self, metrics)
```

#### OperationProfile

Defines expected performance characteristics for operation types.

```python
@dataclass
class OperationProfile:
    operation_name: str
    expected_query_range: Tuple[int, int]
    response_time_baseline: float
    memory_overhead_tolerance: float
    complexity_factors: Dict[str, Any]
    
    def calculate_dynamic_thresholds(self, context: Dict[str, Any]) -> Dict[str, float]
```

#### TestExecutionSummary

Summary of test execution performance across a test suite.

```python
@dataclass
class TestExecutionSummary:
    total_tests: int
    passed_tests: int
    failed_tests: int
    average_score: float
    grade_distribution: Dict[str, int]
    critical_issues: List[str]
    optimization_opportunities: List[str]
    performance_trends: Dict[str, str]
    execution_time: float
    recommendations: List[str]
```

---

## Usage Examples

### Basic Mercury Usage

```python
from django_mercury import DjangoMercuryAPITestCase

class UserAPITestCase(DjangoMercuryAPITestCase):
    def test_user_list(self):
        # Mercury automatically monitors this test
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        # Output: 🎯 test_user_list - Grade A (42ms, 3Q, 8.2MB)
```

### Custom Thresholds

```python
class StrictPerformanceTestCase(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_performance_thresholds({
            'response_time_ms': 100,
            'query_count_max': 5,
            'memory_overhead_mb': 20
        })
        
    def test_with_stricter_thresholds(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
```

### Manual Monitoring with DjangoPerformanceAPITestCase

```python
class DetailedMonitoringTestCase(DjangoPerformanceAPITestCase):
    def test_with_detailed_monitoring(self):
        with self.monitor_django_view("user_detail") as monitor:
            response = self.client.get('/api/users/1/')
        
        self.assertPerformance(
            monitor,
            max_response_time=150,
            max_queries=5
        )
        self.assertNoNPlusOne(monitor)
```

### Comprehensive Analysis

```python
def test_with_comprehensive_analysis(self):
    metrics = self.run_comprehensive_analysis(
        operation_name="UserSearch",
        test_function=lambda: self.client.get('/api/users/search/?q=john'),
        operation_type="search_view",
        expect_response_under=300,
        print_analysis=True,
        auto_detect_n_plus_one=True
    )
    
    self.assert_mercury_performance_production_ready(metrics)
```

---

## Best Practices

### 1. Choose the Right Test Case Class

- **Use `DjangoMercuryAPITestCase`** for:
  - Rapid development and testing
  - Automatic performance monitoring
  - Educational/learning environments
  - General API testing with performance awareness

- **Use `DjangoPerformanceAPITestCase`** for:
  - Fine-grained control over monitoring
  - Custom performance analysis workflows
  - Integration with existing test frameworks
  - Advanced performance debugging

### 2. Threshold Configuration

```python
# Good: Set realistic, context-aware thresholds
cls.set_performance_thresholds({
    'response_time_ms': 200,     # Based on your app's needs
    'query_count_max': 10,       # Consider your data relationships
    'memory_overhead_mb': 50     # Based on your server capacity
})

# Avoid: Overly strict or overly lenient thresholds
cls.set_performance_thresholds({
    'response_time_ms': 10,      # Too strict for most real apps
    'query_count_max': 1000      # Too lenient, won't catch issues
})
```

### 3. Test Organization

```python
class APIPerformanceTestCase(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_mercury(
            verbose_reporting=False,     # Set True only during debugging
            educational_guidance=True    # Helpful for learning
        )
    
    def test_list_operations(self):
        """Test list operations with appropriate expectations."""
        pass
    
    def test_detail_operations(self):
        """Test detail operations with different thresholds."""
        pass
    
    def test_complex_operations(self):
        """Test complex operations with relaxed thresholds."""
        self.set_test_performance_thresholds({
            'response_time_ms': 500,
            'query_count_max': 20
        })
        pass
```

### 4. Debugging Performance Issues

```python
# Enable verbose reporting for debugging
cls.configure_mercury(verbose_reporting=True, educational_guidance=True)

# Use comprehensive analysis for detailed insights
metrics = self.run_comprehensive_analysis(
    "ProblemOperation",
    test_function,
    print_analysis=True,
    show_scoring=True
)
```

### 5. Production Readiness Testing

```python
class ProductionReadinessTestCase(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Production-grade thresholds
        cls.set_performance_thresholds({
            'response_time_ms': 200,
            'query_count_max': 10,
            'memory_overhead_mb': 30
        })
    
    def test_critical_endpoints(self):
        # Test critical paths with strict requirements
        metrics = self.measure_django_view('/api/critical/')
        self.assert_mercury_performance_production_ready(metrics)
```

---

This API reference provides comprehensive documentation for effectively using the Django Mercury Performance Testing framework. For additional examples and guidance, see the existing documentation files and example test cases in the project repository.