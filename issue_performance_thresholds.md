---
name: General Issue Report
about: Add configurable performance thresholds via Django settings
title: "[FEATURE] Add Django settings for configurable performance thresholds ('fast', 'slow', etc.)"
labels: 'enhancement'
assignees: ''

---
## Claiming This Task:

Before you start working, please check the **Assignees** section on the right. If no one is assigned, leave a comment claiming the issue and assign it to yourself. This is required to prevent duplicate work.

## **Current Situation**

Currently, the Django Mercury performance testing framework has assertion methods like:
- `self.assertPerformanceFast(monitor)` - Checks if performance is "fast"
- `self.assertPerformanceNotSlow(monitor)` - Checks if performance is not "slow"  
- `self.assertMemoryEfficient(monitor)` - Checks if memory usage is "efficient"

However, there's no way to configure what counts as "fast", "slow", or "efficient". These thresholds are hardcoded, which means:
- Different projects with different requirements can't customize thresholds
- API endpoints vs. background tasks may need different definitions of "fast"
- No way to gradually tighten performance requirements over time

## **Proposed Solution(s)**

Add Django settings configuration for performance thresholds with sensible defaults:

```python
# In Django settings.py
MERCURY_PERFORMANCE_THRESHOLDS = {
    'response_time': {
        'fast': 100,        # <= 100ms is fast
        'normal': 500,      # <= 500ms is normal
        'slow': 1000,       # > 1000ms is slow
        'critical': 3000,   # > 3000ms is critical
    },
    'queries': {
        'efficient': 5,     # <= 5 queries is efficient
        'normal': 20,       # <= 20 queries is normal
        'excessive': 50,    # > 50 queries is excessive
    },
    'memory_mb': {
        'efficient': 10,    # <= 10MB is efficient
        'normal': 50,       # <= 50MB is normal
        'high': 100,        # > 100MB is high usage
    },
    'cache_hit_ratio': {
        'excellent': 0.9,   # >= 90% hit ratio
        'good': 0.7,        # >= 70% hit ratio
        'poor': 0.5,        # < 50% hit ratio
    }
}

# Or use defaults if not specified
MERCURY_PERFORMANCE_THRESHOLDS = getattr(
    settings, 
    'MERCURY_PERFORMANCE_THRESHOLDS',
    DEFAULT_THRESHOLDS
)
```

Additionally, allow per-test overrides:

```python
class MyTestCase(DjangoMercuryAPITestCase):
    # Class-level override
    performance_thresholds = {
        'response_time': {'fast': 50}  # Stricter for this test class
    }
    
    def test_critical_endpoint(self):
        # Method-level override
        self.set_threshold('response_time.fast', 25)  # Even stricter for this test
        
        response = self.client.get('/api/critical/')
        self.assertPerformanceFast(self.monitor)  # Now uses 25ms threshold
```

## **Benefits**

1. **Flexibility** - Different projects can define their own performance standards
2. **Gradual improvement** - Teams can progressively tighten thresholds as they optimize
3. **Context-aware** - Different test suites can have different thresholds (e.g., API vs admin)
4. **Clear expectations** - Performance requirements are explicitly documented in settings
5. **Better CI/CD** - Can fail builds when performance degrades below configured thresholds
6. **Industry standards** - Teams can align with their specific industry requirements (e.g., finance may need <50ms, while content sites may accept <500ms)

## **Files to be Altered or created (if known)**

- `django_mercury/python_bindings/constants.py` - Add DEFAULT_THRESHOLDS
- `django_mercury/python_bindings/django_integration.py` - Read settings and use thresholds in assertions
- `django_mercury/python_bindings/django_integration_mercury.py` - Update DjangoMercuryAPITestCase
- `django_mercury/documentation/api_reference.md` - Document new settings
- `tests/test_threshold_configuration.py` - New test file for threshold configuration
- `README.md` - Add configuration examples

## **Additional Context (Optional)**

Example use cases:

1. **E-commerce site**: 
   - Product pages: fast = 200ms
   - Checkout: fast = 100ms (more critical)
   - Admin: fast = 1000ms (less critical)

2. **Real-time dashboard**:
   - Data updates: fast = 50ms
   - Historical reports: fast = 500ms

3. **Progressive optimization**:
   - Month 1: slow > 2000ms
   - Month 2: slow > 1500ms  
   - Month 3: slow > 1000ms
   - Goal: slow > 500ms

Current workaround is using explicit threshold values:
```python
self.assertResponseTimeLess(monitor, 100)  # Have to specify 100 everywhere
```

But this doesn't scale well and makes it hard to maintain consistent standards across a large test suite.