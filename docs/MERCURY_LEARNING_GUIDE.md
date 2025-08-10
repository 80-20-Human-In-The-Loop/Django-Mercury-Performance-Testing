# Django Mercury Learning & Investigation Guide

## 🎓 Philosophy: Learn First, Optimize Second

Django Mercury provides two test case classes with distinct purposes:

1. **`DjangoMercuryAPITestCase`** - For **learning and investigation**
2. **`DjangoPerformanceAPITestCase`** - For **production testing with assertions**

This guide focuses on using Mercury as a learning tool to understand your Django app's performance.

## 📚 The Learning Workflow

### Step 1: Start with Investigation

When you suspect performance issues or want to understand your app better, start with `DjangoMercuryAPITestCase`:

```python
from django_mercury import DjangoMercuryAPITestCase

class UserAPIInvestigation(DjangoMercuryAPITestCase):
    """Investigate user API performance patterns."""
    
    def test_user_list_endpoint(self):
        """What happens when we list users?"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        # Mercury automatically analyzes this
    
    def test_user_detail_endpoint(self):
        """What happens when we fetch a single user?"""
        user = User.objects.create(username='testuser')
        response = self.client.get(f'/api/users/{user.id}/')
        self.assertEqual(response.status_code, 200)
        # Mercury watches for N+1 queries
```

### Step 2: Run and Learn

```bash
python manage.py test users.tests.investigation
```

**What you'll see (clean, focused output):**

```
💡 test_user_list_endpoint: N+1 Query Pattern Detected (156 queries)
   → Fix: Use select_related() or prefetch_related()

============================================================
🎓 MERCURY LEARNING SUMMARY
============================================================

📍 PRIMARY ISSUE: N+1 Query Pattern
   Found in 1/2 tests
   → Next Step: Add select_related() and prefetch_related()
   → Learn more: https://docs.djangoproject.com/en/stable/topics/db/optimization/

📊 Quick Stats:
   Tests run: 2
   Avg response time: 125ms
   Avg query count: 79.5

💡 Ready to optimize?
   Switch to DjangoPerformanceAPITestCase for production tests
   Add specific assertions: assertResponseTimeLess(), assertQueriesLess()
============================================================
```

### Step 3: Fix the Issue

Based on Mercury's guidance, fix your view:

```python
# views.py - BEFORE
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    
# views.py - AFTER (Mercury's suggestion)
class UserViewSet(ModelViewSet):
    queryset = User.objects.select_related('profile').prefetch_related('groups')
```

### Step 4: Switch to Production Testing

Once you understand the issue and have fixed it, switch to `DjangoPerformanceAPITestCase`:

```python
from django_mercury import DjangoPerformanceAPITestCase
from django_mercury import monitor_django_view

class UserAPIPerformanceTest(DjangoPerformanceAPITestCase):
    """Production performance tests with specific assertions."""
    
    def test_user_list_performance(self):
        """User list should be fast and efficient."""
        with monitor_django_view("user_list") as monitor:
            response = self.client.get('/api/users/')
        
        self.assertEqual(response.status_code, 200)
        
        # Specific performance assertions
        self.assertResponseTimeLess(monitor.metrics, 100, "Should respond quickly")
        self.assertQueriesLess(monitor.metrics, 3, "Should use optimized queries")
        # These will FAIL if performance regresses!
```

## 🔍 When to Use Each Test Case

### Use `DjangoMercuryAPITestCase` When:

- 🔍 **Investigating** unknown performance issues
- 📚 **Learning** about your app's behavior
- 🎯 **Discovering** optimization opportunities
- 🧪 **Experimenting** with different approaches
- 📊 **Profiling** before optimization

**Example scenarios:**
- "Why is this endpoint slow?"
- "How many queries does this view make?"
- "Is there an N+1 problem here?"
- "What's using so much memory?"

### Use `DjangoPerformanceAPITestCase` When:

- ✅ **Asserting** specific performance requirements
- 🚨 **Preventing** performance regressions
- 📈 **Tracking** performance over time
- 🏭 **Production** test suites
- 🎯 **CI/CD** pipeline checks

**Example scenarios:**
- "This endpoint must respond in under 100ms"
- "This view should make no more than 5 queries"
- "Memory usage must stay under 150MB"
- "Ensure N+1 queries never come back"

## 📖 Understanding Mercury's Output

### Learning Mode Output (DjangoMercuryAPITestCase)

Mercury focuses on **one primary issue** at a time:

```
💡 test_name: N+1 Query Pattern Detected (156 queries)
   → Fix: Use select_related() or prefetch_related()
```

**Icons and their meanings:**
- 💡 = Learning opportunity found
- ⏱️ = Slow response time issue
- 🗃️ = High query count issue
- 📍 = Primary issue to focus on
- ✅ = Performance looks good

### The Learning Summary

At the end of test runs, Mercury provides:

1. **Primary Issue** - The #1 thing to investigate
2. **Quick Stats** - Basic performance metrics
3. **Next Steps** - Actionable guidance

This is intentionally minimal to focus your learning.

## 🎯 Common Performance Patterns

### Pattern 1: N+1 Queries

**Investigation reveals:**
```
💡 test_user_list: N+1 Query Pattern Detected (201 queries)
```

**Common causes:**
- Accessing related models in loops
- Serializers accessing foreign keys
- Template loops accessing related data

**Fix approach:**
```python
# Add to your queryset
.select_related('foreign_key_field')  # For ForeignKey/OneToOne
.prefetch_related('many_to_many_field')  # For ManyToMany
```

### Pattern 2: Slow Response Times

**Investigation reveals:**
```
⏱️ test_search: Slow Response (450ms)
```

**Common causes:**
- Missing database indexes
- Complex unoptimized queries
- Loading too much data

**Fix approach:**
1. Add database indexes
2. Use `.only()` to limit fields
3. Implement pagination
4. Add caching

### Pattern 3: High Query Count

**Investigation reveals:**
```
🗃️ test_dashboard: High Query Count (47 queries)
```

**Common causes:**
- Multiple separate queries that could be combined
- Repeated queries for the same data
- Missing query optimization

**Fix approach:**
1. Combine queries using `select_related()`
2. Cache repeated queries
3. Use aggregation instead of multiple queries

## 💡 Best Practices

### 1. Start Simple

Begin with `DjangoMercuryAPITestCase` and no custom configuration:

```python
class SimpleInvestigation(DjangoMercuryAPITestCase):
    def test_my_view(self):
        response = self.client.get('/my-endpoint/')
        # Let Mercury analyze it
```

### 2. Focus on One Issue at a Time

Mercury highlights the PRIMARY issue. Fix that first before moving to others.

### 3. Iterate and Learn

1. Run investigation test
2. See what Mercury finds
3. Fix the issue
4. Run again to verify
5. Switch to production test

### 4. Document Your Findings

```python
class UserAPIInvestigation(DjangoMercuryAPITestCase):
    """
    Investigation Results:
    - Found N+1 in user list (fixed with select_related)
    - Search was slow (added db index)
    - Detail view over-fetching (added .only())
    """
```

### 5. Graduate to Production Tests

Once you understand and fix issues, create permanent guards:

```python
class UserAPIPerformanceTest(DjangoPerformanceAPITestCase):
    """Guards against performance regressions."""
    
    def test_user_list_stays_fast(self):
        """Ensure our N+1 fix stays in place."""
        with monitor_django_view("user_list") as monitor:
            response = self.client.get('/api/users/')
        
        self.assertQueriesLess(monitor.metrics, 3, "N+1 queries must not return")
```

## 🚀 Advanced Investigation Techniques

### Custom Thresholds for Investigation

```python
class DetailedInvestigation(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set investigation thresholds
        cls.set_performance_thresholds({
            'response_time_ms': 50,  # Flag anything over 50ms
            'query_count_max': 5,    # Flag more than 5 queries
        })
```

### Comparing Approaches

```python
class OptimizationInvestigation(DjangoMercuryAPITestCase):
    def test_approach_without_select_related(self):
        """Baseline: How bad is it?"""
        users = User.objects.all()
        for user in users[:10]:
            _ = user.profile.bio  # Forces queries
    
    def test_approach_with_select_related(self):
        """Optimized: How much better?"""
        users = User.objects.select_related('profile').all()
        for user in users[:10]:
            _ = user.profile.bio  # No extra queries!
```

## 📊 Interpreting Grades

Mercury assigns grades to help you understand performance:

- **S** (95-100): Exceptional performance
- **A+** (90-94): Excellent 
- **A** (85-89): Very good
- **B** (75-84): Good
- **C** (60-74): Acceptable
- **D** (40-59): Needs improvement
- **F** (0-39): Critical issues

In learning mode, focus on understanding **why** you got a grade, not the grade itself.

## 🎓 Learning Resources

### Django Optimization Docs
- [Database Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [Performance and Optimization](https://docs.djangoproject.com/en/stable/topics/performance/)

### Common Solutions
- **N+1 Queries**: Use `select_related()` and `prefetch_related()`
- **Slow Queries**: Add database indexes with `db_index=True`
- **High Memory**: Implement pagination and use `iterator()`
- **Cache Misses**: Add Redis/Memcached caching

### Tools to Combine with Mercury
- Django Debug Toolbar (development)
- Django Silk (profiling)
- nplusone package (N+1 detection)

## 🎯 Summary

1. **Use DjangoMercuryAPITestCase to learn and investigate**
2. **Focus on one issue at a time**
3. **Fix issues based on Mercury's guidance**
4. **Switch to DjangoPerformanceAPITestCase for production tests**
5. **Keep tests as permanent guards against regressions**

Remember: Mercury is a learning tool first, testing framework second. Let it teach you about your Django app's performance patterns, then use that knowledge to build better, faster applications.