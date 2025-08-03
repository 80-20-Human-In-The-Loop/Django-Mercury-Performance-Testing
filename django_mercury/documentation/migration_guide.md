# Migration Guide

This guide helps you migrate from other performance testing solutions to the EduLite Performance Testing Framework.

## Migrating from Django Test Client

### Before (Standard Django)
```python
from django.test import TestCase
import time

class UserAPITestCase(TestCase):
    def test_user_list(self):
        start_time = time.time()
        response = self.client.get('/api/users/')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 0.5)  # Manual timing
        
        # No query counting
        # No memory tracking
        # No N+1 detection
```

### After (Mercury)
```python
from django_mercury import DjangoMercuryAPITestCase

class UserAPITestCase(DjangoMercuryAPITestCase):
    def test_user_list(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        
        # Automatic:
        # ✓ Response time tracking
        # ✓ Query counting and N+1 detection
        # ✓ Memory usage monitoring
        # ✓ Performance scoring
        # ✓ Historical tracking
```

## Migrating from Django Debug Toolbar

### Complementary Usage
Django Debug Toolbar and Mercury serve different purposes:
- **Debug Toolbar**: Interactive debugging during development
- **Mercury**: Automated testing and CI/CD integration

### Using Both Together
```python
class UserAPITestCase(DjangoMercuryAPITestCase):
    def test_with_debug_info(self):
        # Mercury provides automated analysis
        response = self.client.get('/api/users/')
        
        # Debug toolbar accessible at /__debug__/
        # Mercury captures same metrics programmatically
```

## Migrating from django-silk

### Before (Silk)
```python
# Requires middleware configuration
# Manual inspection via web UI
# No test integration

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    # ...
]
```

### After (Mercury)
```python
# No middleware required
# Integrated with tests
# Programmatic assertions

class APITestCase(DjangoMercuryAPITestCase):
    def test_performance(self):
        response = self.client.get('/api/endpoint/')
        
        # Automatic profiling
        # Test assertions on performance
        self.assertPerformanceFast(self.metrics)
```

## Migrating from pytest-benchmark

### Before (pytest-benchmark)
```python
def test_api_performance(benchmark, client):
    result = benchmark(client.get, '/api/users/')
    assert result.status_code == 200
    
    # Limited to timing
    # No Django-specific metrics
```

### After (Mercury)
```python
class UserAPITestCase(DjangoMercuryAPITestCase):
    def test_api_performance(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        
        # Comprehensive metrics beyond timing
        # Django-aware analysis
        # N+1 detection
```

## Migrating from locust

### Different Use Cases
- **Locust**: Load testing, multiple users
- **Mercury**: Single-user performance testing, code quality

### Complementary Approach
```python
# Use Mercury for functional performance tests
class APITestCase(DjangoMercuryAPITestCase):
    def test_single_user_performance(self):
        response = self.client.get('/api/users/')
        # Ensures code quality and optimization

# Use Locust for load testing
class UserBehavior(TaskSet):
    @task
    def list_users(self):
        self.client.get('/api/users/')
        # Tests scalability
```

## Migrating Custom Solutions

### Before (Custom Timer)
```python
class PerformanceTestCase(TestCase):
    def setUp(self):
        self.start_time = time.time()
        self.query_count = len(connection.queries)
    
    def tearDown(self):
        duration = time.time() - self.start_time
        queries = len(connection.queries) - self.query_count
        
        print(f"Time: {duration}s, Queries: {queries}")
        
        if queries > 10:
            self.fail("Too many queries!")
```

### After (Mercury)
```python
class PerformanceTestCase(DjangoMercuryAPITestCase):
    # All the custom logic is built-in
    # Plus: scoring, N+1 detection, memory tracking
    pass
```

## Feature Comparison

| Feature | Django Test | Debug Toolbar | Silk | pytest-benchmark | Mercury |
|---------|------------|---------------|------|------------------|---------|
| Test Integration | ✓ | ✗ | ✗ | ✓ | ✓ |
| Automatic Monitoring | ✗ | ✗ | ✓ | ✗ | ✓ |
| Query Analysis | ✗ | ✓ | ✓ | ✗ | ✓ |
| N+1 Detection | ✗ | ✓ | ✗ | ✗ | ✓ |
| Memory Tracking | ✗ | ✗ | ✓ | ✗ | ✓ |
| Performance Scoring | ✗ | ✗ | ✗ | ✗ | ✓ |
| Historical Tracking | ✗ | ✗ | ✗ | ✓ | ✓ |
| CI/CD Friendly | ✓ | ✗ | ✗ | ✓ | ✓ |
| Optimization Hints | ✗ | ✗ | ✗ | ✗ | ✓ |

## Migration Checklist

1. **Install Mercury**
   ```bash
   cd django_mercury/c_core
   make
   ```

2. **Update Base Test Class**
   ```python
   # Replace
   from django.test import TestCase
   
   # With
   from django_mercury import DjangoMercuryAPITestCase
   ```

3. **Remove Manual Timing Code**
   - Delete custom timer decorators
   - Remove manual query counting
   - Remove custom assertion helpers

4. **Configure Thresholds (Optional)**
   ```python
   @classmethod
   def setUpClass(cls):
       super().setUpClass()
       cls.set_performance_thresholds({
           'response_time_ms': 300,
           'query_count_max': 15,
       })
   ```

5. **Run Tests**
   ```bash
   python manage.py test
   ```

6. **Review Performance Reports**
   - Check the grades and scores
   - Follow optimization suggestions
   - Monitor trends over time

## Common Migration Patterns

### Pattern 1: Assertion Migration
```python
# Old
self.assertLess(response_time, 0.5)
self.assertLess(query_count, 10)

# New (automatic with Mercury)
# Thresholds enforced automatically
# Or explicit:
self.assertPerformance(
    monitor,
    max_response_time=500,
    max_queries=10
)
```

### Pattern 2: Custom Metrics
```python
# Old
custom_metric = measure_something()
self.record_metric('custom', custom_metric)

# New
with monitor_django_view("operation") as mon:
    # Your code
    custom_metric = measure_something()

# Access all metrics
metrics = mon.metrics
```

### Pattern 3: Conditional Testing
```python
# Old
if settings.PERFORMANCE_TESTING:
    # Performance assertions

# New
# Always active, configurable
cls.configure_mercury(enabled=settings.PERFORMANCE_TESTING)
```

## Getting Help

1. **Documentation**: See README.md
2. **Examples**: Check test files in the codebase
3. **Issues**: GitHub issues for bugs/features
4. **Debugging**: Enable verbose mode
   ```python
   cls.configure_mercury(verbose_reporting=True)
   ```