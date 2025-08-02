# DjangoPerformanceAPITestCase Documentation

`DjangoPerformanceAPITestCase` is an enhanced test case class designed for comprehensive, Django-aware performance monitoring. It inherits from `rest_framework.test.APITestCase` and provides a powerful suite of tools for detailed performance analysis, including custom assertions, monitoring contexts, and reporting dashboards.

This class is central to the performance testing framework, enabling developers to write tests that not only verify correctness but also ensure that code meets performance standards for response time, memory usage, and database efficiency.

---

## Core Features

- **Seamless Integration**: Extends `APITestCase` for a familiar testing experience.
- **Rich Assertions**: A comprehensive set of assertions for performance metrics.
- **Django-Aware Monitoring**: Specialized monitors for views, models, and serializers.
- **Automated Analysis**: Methods for running comprehensive, automated performance analyses.
- **Beautiful Reporting**: Tools for generating insightful and visually appealing performance dashboards.

---

## Assertion Methods

These methods provide a way to verify that performance metrics meet specific expectations within your tests.

### `assertPerformance(...)`

Asserts that a full suite of performance metrics meets the specified thresholds.

- **Args**:
  - `monitor` (EnhancedPerformanceMonitor): The monitor instance after its context has exited.
  - `max_response_time` (Optional[float]): The maximum acceptable response time in milliseconds.
  - `max_memory_mb` (Optional[float]): The maximum acceptable memory usage in megabytes.
  - `max_queries` (Optional[int]): The maximum acceptable number of database queries.
  - `min_cache_hit_ratio` (Optional[float]): The minimum acceptable cache hit ratio.
  - `msg` (Optional[str]): A custom message for the assertion failure.

### `assertResponseTimeLess(...)`

Asserts that the response time is less than a given threshold.

- **Args**:
  - `metrics_or_monitor` (Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python]): The metrics object or monitor.
  - `milliseconds` (float): The response time threshold in milliseconds.

### `assertMemoryLess(...)`

Asserts that memory usage is less than a given threshold.

- **Args**:
  - `metrics_or_monitor` (Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python]): The metrics object or monitor.
  - `megabytes` (float): The memory usage threshold in megabytes.

### `assertQueriesLess(...)`

Asserts that the number of database queries is less than a given threshold.

- **Args**:
  - `metrics_or_monitor` (Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python]): The metrics object or monitor.
  - `count` (int): The database query count threshold.

---

## Status-Based Assertions

These assertions check the performance status, which is a qualitative assessment of the metrics.

- `assertPerformanceFast(...)`: Asserts that performance is rated as 'fast' (typically < 100ms).
- `assertPerformanceNotSlow(...)`: Asserts that performance is not rated as 'slow' (typically >= 500ms).
- `assertMemoryEfficient(...)`: Asserts that memory usage is not considered intensive.

---

## Django-Specific Assertions

These assertions are tailored for common Django performance issues.

- `assertNoNPlusOne(...)`: Asserts that no N+1 query patterns were detected.
- `assertGoodCachePerformance(...)`: Asserts that the cache hit ratio meets a minimum threshold (default is 70%).

---

## Monitor Creation

These methods provide convenient shortcuts for creating specialized performance monitors.

- `monitor_django_view(operation_name)`: Creates a monitor with full hooks for a Django view.
- `monitor_django_model(operation_name)`: Creates a monitor for a Django model operation.
- `monitor_serializer(operation_name)`: Creates a monitor for a serializer.

---

## Measurement and Analysis

These high-level methods automate the process of measuring and analyzing performance.

### `measure_django_view(...)`

Measures the performance of a Django view with comprehensive, automated monitoring.

- **Args**:
  - `url` (str): The URL of the view to measure.
  - `method` (str): The HTTP method to use (e.g., 'GET', 'POST').
  - `data` (Optional[Dict[str, Any]]): Request data for POST, PUT, or PATCH methods.

- **Returns**: `EnhancedPerformanceMetrics_Python` - The captured performance metrics.

### `run_comprehensive_analysis(...)`

Runs an ultimate, Django-aware performance analysis with a built-in scoring system.

- **Args**:
  - `operation_name` (str): A descriptive name for the operation being tested.
  - `test_function` (Callable): The function to execute and monitor.
  - `expect_response_under` (Optional[float]): The expected maximum response time in ms.
  - `print_analysis` (bool): Whether to print the analysis report to the console.
  - `auto_detect_n_plus_one` (bool): Whether to automatically detect N+1 issues.

- **Returns**: `EnhancedPerformanceMetrics_Python` - The captured performance metrics.

---

## Dashboard and Reporting

These methods generate and print performance reports to the console.

- `create_enhanced_performance_dashboard_with_scoring(...)`: Creates a dashboard that includes a performance score.
- `create_enhanced_dashboard(...)`: Creates a comprehensive dashboard with Django-specific insights.
