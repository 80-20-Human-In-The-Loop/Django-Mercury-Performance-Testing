# Django Mercury 🚀

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://docs.djangoproject.com/en/5.1/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-red.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Built for: EduLite](https://img.shields.io/badge/Built%20for-EduLite-orange)](https://github.com/ibrahim-sisar/EduLite)
[![Values: Open](https://img.shields.io/badge/Values-Open%20%7C%20Free%20%7C%20Fair-purple)](https://github.com/80-20-Human-In-The-Loop)

**Part of the [Human in the Loop](https://github.com/80-20-Human-In-The-Loop) ecosystem**

> A performance testing framework for Django that helps you understand and fix performance issues, not just detect them.

## 🌟 Origin Story

Mercury was born from a real need at [EduLite](https://github.com/ibrahim-sisar/EduLite) - an open-source education platform designed for students in areas with poor internet connectivity. When we discovered our UserSearchView was making **825 queries for paginated results**, we knew we needed better tools.

Instead of just fixing the issue, we built Mercury - a framework that not only catches performance problems but teaches developers how to fix them. This aligns with the **Fair**, **Free**, and **Open** values of [EduLite](https://github.com/ibrahim-sisar/EduLite) - as we wanted people of all skill levels to be able to contribute and learn!

## 🎯 Current Status: Initial Release

**What's Working NOW:**
- ✅ N+1 query detection with severity analysis
- ✅ Performance grading (F to A+) 
- ✅ Two test case classes: `DjangoMercuryAPITestCase` and `DjangoPerformanceAPITestCase`
- ✅ Smart operation type detection
- ✅ Educational guidance when tests fail
- ✅ C-powered monitoring for minimal overhead
- ✅ Comprehensive metrics: response time, queries, memory

**What We Actually Found:**
```text
🚨 POTENTIAL N+1 QUERY PROBLEM! 🚨
Severity: CRITICAL (825 queries)
```

**Coming Soon:**
- 🔜 MCP (Model Context Protocol) integration for AI-assisted optimization
- 🔜 Historical performance tracking
- 🔜 Standard TestCase for non-API views
- 🔜 PyPI package release
- 🔜 Performance regression detection

## 📦 Installation (Current)

Mercury is currently part of the EduLite project. To use it in your Django project:

```bash
# Clone and build
git clone https://github.com/ibrahim-sisar/EduLite.git
cd EduLite/backend/performance_testing/c_core
make clean && make

# Add to your Python path in test files
import sys
from pathlib import Path
performance_testing_path = Path(__file__).parent.parent / "performance_testing"
sys.path.insert(0, str(performance_testing_path))
```

## 🚀 Quick Start

### Two Classes, Two Approaches

#### 1. DjangoMercuryAPITestCase - Automatic Monitoring

```python
from python_bindings.django_integration_mercury import DjangoMercuryAPITestCase

class UserSearchPerformanceTest(DjangoMercuryAPITestCase):
    """Mercury automatically monitors every test method."""
    
    def test_user_search(self):
        # Just write your test - Mercury handles the rest
        response = self.client.get('/api/users/search/?q=test')
        self.assertEqual(response.status_code, 200)
        # Mercury automatically analyzes and reports performance
```

#### 2. DjangoPerformanceAPITestCase - Modular Control

```python
from python_bindings.django_integration import DjangoPerformanceAPITestCase
from python_bindings.monitor import monitor_django_view

class AdvancedPerformanceTest(DjangoPerformanceAPITestCase):
    """For when you need specific assertions and control."""
    
    def test_with_assertions(self):
        with monitor_django_view("search") as monitor:
            response = self.client.get('/api/users/search/')
        
        # Use specific assertions
        self.assertResponseTimeLess(monitor, 100)
        self.assertQueriesLess(monitor, 10)
        self.assertNoNPlusOne(monitor)
```

## 📊 Real Output from Mercury

This is actual output from testing EduLite:

```text
🎨 MERCURY PERFORMANCE DASHBOARD - UserSearchPerformanceTest
╭─────────────────────────────────────────────────────────────╮
│ 🚀 Overall Status: NEEDS IMPROVEMENT                          │
│ 🎓 Overall Grade: F (20.5/100)                               │
│ 📊 Tests Executed: 12                                        │
│ ⏱️  Avg Response Time: 105.6ms                                │
│ 🧠 Avg Memory Usage: 91.7MB                                  │
│ 🗃️  Total Queries: 2761 (230.1 avg)                          │
│ 🚨 N+1 Issues: 10/12 tests affected                          │
╰─────────────────────────────────────────────────────────────╯
```

## 🎓 The  Philosophy in Action

Mercury embodies the [Human in the Loop](https://github.com/80-20-Human-In-The-Loop/Community) philosophy:

**80% Automation:**
- Automatic performance monitoring
- N+1 detection and analysis
- Performance grading
- Threshold management

**20% Human Wisdom:**
- Understanding WHY performance matters
- Choosing the right optimization strategy
- Learning from the guidance
- Making architectural decisions

**Example: Educational Guidance**

When a test fails, Mercury doesn't just say "failed" - it teaches:

```text
📚 MERCURY EDUCATIONAL GUIDANCE
============================================================
🎯 Test: test_user_list_view
⚠️  Default thresholds exceeded

🗃️  Query Count: 230 (limit: 10)
   → 220 extra queries (2200% exceeded)

💡 SOLUTION: N+1 Query Pattern Detected
   Your code is likely missing select_related() or prefetch_related()
   
   Try: User.objects.select_related('profile').prefetch_related('groups')

🛠️  Quick Fix for Testing:
   cls.set_performance_thresholds({'query_count_max': 250})
   
   But the REAL fix is optimizing your queries!
============================================================
```

## 🛠️ Available Assertions

### DjangoPerformanceAPITestCase Methods

```python
# Time assertions
self.assertResponseTimeLess(monitor, 100)    # < 100ms
self.assertPerformanceFast(monitor)          # Predefined "fast"
self.assertPerformanceNotSlow(monitor)       # Not "slow"

# Query assertions  
self.assertQueriesLess(monitor, 10)          # < 10 queries
self.assertNoNPlusOne(monitor)               # No N+1 detected

# Memory assertions
self.assertMemoryLess(monitor, 50)           # < 50MB
self.assertMemoryEfficient(monitor)          # Reasonable memory use

# Cache assertions
self.assertGoodCachePerformance(monitor, 0.8) # 80% hit ratio
```

## 🔧 Configuration

```python
class MyTest(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Configure Mercury
        cls.configure_mercury(
            enabled=True,
            auto_scoring=True,
            verbose_reporting=False,
            educational_guidance=True  # Learn while you test!
        )
        
        # Set thresholds
        cls.set_performance_thresholds({
            'response_time_ms': 100,
            'query_count_max': 10,
            'memory_overhead_mb': 20,
        })
```

## 🎯 Real Impact on EduLite

Before Mercury:
- UserSearchView: **825 queries** for pagination
- No visibility into performance issues
- Users in poor connectivity areas suffered

After Mercury:
- Identified the exact problem
- Reduced to **12 queries**
- Performance monitoring on every PR

## 🚧 Roadmap

### Phase 1: Current Release ✅
- Basic performance monitoring
- N+1 detection
- Educational guidance

### Phase 2: MCP Integration (Q1 2025)
- AI-assisted optimization suggestions
- Automated fix generation with human review
- Learning mode for junior developers

### Phase 3: Standalone Package (Q2 2025)
- PyPI release as `django-mercury`
- Comprehensive documentation
- Plugin system for custom analyzers

## 🤝 Contributing

Mercury is part of both [EduLite](https://github.com/ibrahim-sisar/EduLite) and the [Human in the Loop](https://github.com/80-20-Human-In-The-Loop) ecosystem. We believe in:

- **Education First**: Tools should teach, not just detect
- **Human Understanding**: Keep humans in control of their code
- **Open Source**: Built by the community, for the community

### How to Contribute

1. Try Mercury on your Django project
2. Report issues and suggestions
3. Help us build MCP integration
4. Share your performance optimization stories

## 🏫 Built for Education

Mercury was created for [EduLite](https://github.com/ibrahim-sisar/EduLite), an education platform serving students in challenging conditions. Every feature is designed to:

- Work with limited resources
- Teach while testing
- Build developer skills
- Ensure quality for end users

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

### Why GPL-3.0?

We chose GPL-3.0 because it enforces the same standards and values we believe in:

- **🌍 Open**: The source code must remain open and accessible to everyone
- **🆓 Free**: Free as in freedom - you can use, study, share, and improve the software
- **⚖️ Fair**: Any improvements or derivatives must be shared back with the community
- **🤝 Copyleft**: Ensures the software and its derivatives remain free forever

This means if you create and distribute a modified version, you must:
- Make your source code available
- License it under GPL-3.0
- Preserve all copyright and license notices
- Document your changes

This aligns perfectly with the Human in the Loop philosophy of keeping knowledge open and accessible.

For the full license text, see [LICENSE](LICENSE) or visit [GNU GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html).

## 🙏 Acknowledgments

- [EduLite Team](https://github.com/ibrahim-sisar/EduLite) - For the real-world use case
- [Human in the Loop](https://github.com/80-20-Human-In-The-Loop) - For the philosophy
- Django/DRF Community - For the foundation

---

**Mercury**: Because finding N+1 queries shouldn't require a PhD in database optimization.

*Built with ❤️ by developers who believe in human understanding, not just automation.*
