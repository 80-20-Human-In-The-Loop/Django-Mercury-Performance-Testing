
# Django Mercury

[![PyPI version](https://badge.fury.io/py/django-mercury-performance.svg)](https://badge.fury.io/py/django-mercury-performance)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 3.2-5.1](https://img.shields.io/badge/django-3.2--5.1-green.svg)](https://docs.djangoproject.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-red.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Built for: EduLite](https://img.shields.io/badge/Built%20for-EduLite-orange)](https://github.com/ibrahim-sisar/EduLite)
[![Values: Open](https://img.shields.io/badge/Values-Open%20%7C%20Free%20%7C%20Fair-purple)](https://github.com/80-20-Human-In-The-Loop)

**Part of the [80-20 Human in the Loop](https://github.com/80-20-Human-In-The-Loop) ecosystem**

> Test Django app speed. Learn why it's slow. Fix it.

## Quick Install

```bash
pip install django-mercury-performance
```

**Then in your test files:**

For quick investigation/learning about the performance of your current tests:

```python
from django_mercury import DjangoMercuryAPITestCase

class MyPerformanceTest(DjangoMercuryAPITestCase):
    def test_api_performance(self):
        response = self.client.get('/api/endpoint/')
        # Performance is automatically monitored and reported!
```

`DjangoMercuryAPITestCase` is meant to be used as a temporary investigation tool.
Once you find a suspicious looking response, switch to `DjangoPerformanceAPITestCase` and utilize  


**How to use:**
```python
from django_mercury import DjangoPerformanceAPITestCase
from django_mercury import monitor_django_view

with monitor_django_view("admin_search") as monitor:
    response = self.admin_client.get('/api/users/search/?q=perf_user')
    
# Performance assertions
self.assertResponseTimeLess(monitor.metrics, 50, "Admin search should be fast")
self.assertQueriesLess(monitor.metrics, 5, "Admin search should be optimized")
self.assertMemoryLess(monitor.metrics, 150, "Should use reasonable memory")
```


## 🌟 Origin Story

Mercury started at [EduLite](https://github.com/ibrahim-sisar/EduLite). EduLite helps students learn with slow internet. We found our UserSearchView made **325 database queries** to show one page!

We built Mercury to find these problems and teach you how to fix them. Mercury follows EduLite's values: **Fair**, **Free**, and **Open**. Everyone can use it and learn. 

Beginners or Students contributing to an open source project that has Mercury in their test pipeline should learn and grow as a developer.

## 📦 Installation

### Install from PyPI (Recommended)

```bash
pip install django-mercury-performance
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing.git
cd Django-Mercury-Performance-Testing

# Install in development mode
pip install -e .
```

## Choose Your Mode

According to [The 80-20 Three Audiences Pattern](https://github.com/80-20-Human-In-The-Loop/Community/wiki/Tutorial-How-To-Write-80-20-Tools#three-audiences-pattern) Django Mercury adapts to your needs.

This library features a plugin system, use `mercury-test --list-plugins` to view what comes pre-installed:

```sh
❯ mercury-test --list-plugins
Available Mercury-Test Plugins:


✅ discovery (priority: 10)
   Intelligent manage.py discovery with caching

✅ wizard (priority: 20)
   Interactive test selection wizard

✅ learn (priority: 60)
   Interactive learning with explanations and quizzes

✅ hints (priority: 90)
   Show performance tips for slow tests
```

### 💼 Professional Mode (Default) - For Experts
Fast, efficient, no hand-holding. You know what you're doing.

**What it does:**
- ✅ Automatic performance monitoring
- 📊 Detailed reports and grades (S, A+, A, B, C, D, F)
- ⚡ Fast execution without interruptions
- 🎯 Precise performance metrics
- 🔍 N+1 query detection

#### Plugins for Professionals 


### 🎓 Educational Mode - For Learning & Understanding
Learn while you test! Mercury becomes your performance tutor.

**What it does:**
- ⏸️ Pauses when it finds problems to teach you
- 📚 Explains issues in simple language  
- 🎮 Interactive quizzes test your understanding
- 📈 Tracks your learning progress
- 🔧 Shows step-by-step fixes

--wizard plugin, --tip

### 🤖 Agent Mode (`--agent`) - Coming Soon!
Let AI help optimize your code while you keep control.

**What will it do:**
- 🔄 Auto-fix level 1-2 complexity issues
- 📝 Generate optimization suggestions
- 🚨 Flag critical issues for human review  
- 📊 Structured JSON output for tool integration
- 🧠 Preserve human decision points

**Future usage:**
```bash
python manage.py test --agent
```

```json
{
  "auto_fix_immediately": ["missing_select_related", "unused_imports"],
  "requires_human_review": ["architecture_change", "security_update"],
  "complexity_breakdown": {
    "1/5_trivial": 12,
    "2/5_routine": 8,
    "3/5_moderate": 3,
    "4/5_complex": 2,
    "5/5_critical": 1
  }
}
```

## 🚀 Quick Start

### Step 1: Choose Your Experience

1. **🎓 Student/Beginner?** Use `--edu` for interactive learning
2. **💼 Expert?** Use default mode for fast results  
3. **🤖 AI Agent?** `--agent` mode coming soon!

### Step 2: Run Your Tests

#### 🎓 Educational Mode - Learn While Testing

```bash
# Enable in settings.py
import sys
if '--edu' in sys.argv:
    TEST_RUNNER = 'django_mercury.test_runner.EducationalTestRunner'

# Run with learning
python manage.py test --edu
```

Mercury will pause at performance issues to teach you!

#### 💼 Professional Mode - Automatic Monitoring (Default)

```python
from django_mercury import DjangoMercuryAPITestCase

class UserSearchPerformanceTest(DjangoMercuryAPITestCase):
    """Mercury monitors every test automatically."""
    
    def test_user_search(self):
        # Write your normal test
        response = self.client.get('/api/users/search/?q=test')
        self.assertEqual(response.status_code, 200)
        # Mercury checks performance automatically
```

**What Mercury does:**
- Counts database queries
- Measures response time  
- Tracks memory usage
- Finds N+1 problems
- Shows clear reports

#### 💼 Advanced: Manual Control

You control when to monitor. Good for specific performance checks.

```python
from django_mercury import DjangoPerformanceAPITestCase
from django_mercury import monitor_django_view

class AdvancedPerformanceTest(DjangoPerformanceAPITestCase):
    """Control exactly what you test."""
    
    def test_with_assertions(self):
        with monitor_django_view("search") as monitor:
            response = self.client.get('/api/users/search/')
        
        # Check specific limits
        self.assertResponseTimeLess(monitor, 100)  # Under 100ms
        self.assertQueriesLess(monitor, 10)         # Under 10 queries
        self.assertNoNPlusOne(monitor)              # No N+1 problems
```

**You control:**
- When monitoring starts
- What to check
- Your performance limits

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

## 📈 Your Learning Journey

### Start Here → Master Performance → Help Others

```
🎓 Educational Mode          💼 Professional Mode         🤖 Agent Mode
Learn the basics      →      Apply your skills      →     Automate wisely
Interactive lessons          Fast, efficient testing      AI-assisted optimization
Quizzes & progress          Expert-level control         (Coming soon!)
```

**Your Path:**
1. **Begin** with `--edu` mode to understand concepts
2. **Practice** with real projects in professional mode
3. **Master** performance optimization patterns
4. **Contribute** improvements back to the community
5. **Future**: Use AI agents to scale your expertise

## 🎓 How Mercury Works

Mercury follows the [Human in the Loop](https://github.com/80-20-Human-In-The-Loop/Community) philosophy:

**80% Computer Help:**
- Watches performance automatically
- Finds N+1 problems
- Grades your code speed
- Manages limits

**20% Human Control:**
- You understand WHY speed matters
- You choose how to fix problems
- You learn from the guides
- You make design choices

**Example: How Mercury Teaches**

When a test fails, Mercury helps you learn:

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

## 🛠️ Performance Checks

### Test Methods You Can Use

```python
# Check response time
self.assertResponseTimeLess(monitor, 100)    # Must be under 100ms
self.assertPerformanceFast(monitor)          # Must be fast
self.assertPerformanceNotSlow(monitor)       # Must not be slow

# Check database queries  
self.assertQueriesLess(monitor, 10)          # Must use less than 10 queries
self.assertNoNPlusOne(monitor)               # Must not have N+1 problems

# Check memory use
self.assertMemoryLess(monitor, 50)           # Must use less than 50MB
self.assertMemoryEfficient(monitor)          # Must use memory well

# Check cache use
self.assertGoodCachePerformance(monitor, 0.8) # Must hit cache 80% of time
```

## 🔧 Setup Options

```python
class MyTest(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Turn Mercury features on or off
        cls.configure_mercury(
            enabled=True,               # Turn on Mercury
            auto_scoring=True,          # Grade tests automatically
            verbose_reporting=False,    # Show less detail
            educational_guidance=True   # Show help messages
        )
        
        # Set your speed limits
        cls.set_performance_thresholds({
            'response_time_ms': 100,    # Max time: 100ms
            'query_count_max': 10,      # Max queries: 10
            'memory_overhead_mb': 20,   # Max extra memory: 20MB
        })
```

### Getting Help

- **Test failures?** Check the error message first
- **Slow tests?** Look for `time.sleep()` or database queries
- **Still stuck?** Open an issue with your test output

## 🚧 Future Plans

### Phase 1: Foundation ✅
- ✅ Performance monitoring
- ✅ N+1 query detection
- ✅ Educational guidance
- ✅ PyPI availability
- ✅ Educational Mode (`--edu`)

### Phase 2: Enhancement (In Progress)
- 🔨 Improve test stability
- 🔨 Support all Django view types
- 🔨 Track performance trends
- 🔨 Better learning materials

### Phase 3: AI Agent Mode (Coming Soon)
- 🤖 Agent Mode (`--agent`) with structured output
- 🤖 Auto-fix level 1-2 complexity issues
- 🤖 Generate optimization suggestions
- 🤖 Preserve human decision points for level 4-5 issues
- 🤖 Integration with AI development tools

## 🤝 Contributing

Mercury is part of [EduLite](https://github.com/ibrahim-sisar/EduLite) and [Human in the Loop](https://github.com/80-20-Human-In-The-Loop). We welcome everyone.

### Our Values

- **Education First**: Tools should teach, not just find problems
- **Human Understanding**: You control your code
- **Open Source**: Built together, shared with everyone

### How You Can Help

1. **Test Mercury** - Try it on your Django project
2. **Report Problems** - Tell us what doesn't work
3. **Share Ideas** - Suggest improvements
4. **Write Code** - Fix bugs or add features
5. **Improve Docs** - Make them clearer
6. **Help Others** - Answer questions

### Getting Started

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**New to open source?** Start here:
- Look for "good first issue" labels
- Ask questions - we're here to help
- Small fixes matter too

## 🏫 Made for Learning

Mercury was made for [EduLite](https://github.com/ibrahim-sisar/EduLite). EduLite helps students learn even with slow internet. Mercury helps by:

- Working on slow computers
- Teaching as it tests
- Helping developers learn
- Making apps work for everyone

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

### Why GPL-3.0?

We use GPL-3.0 because it matches our values:

- **🌍 Open**: Code stays open for everyone
- **🆓 Free**: You can use, study, share, and improve it
- **⚖️ Fair**: Improvements must be shared
- **🤝 Copyleft**: Stays free forever

If you share a changed version, you must:
- Share your code
- Use GPL-3.0 license
- Keep all notices
- List your changes

This keeps knowledge open for all.

For the full license text, see [LICENSE.txt](LICENSE.txt) or visit [GNU GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html).

## 🙏 Thanks To

- [EduLite Team](https://github.com/ibrahim-sisar/EduLite) - For showing us the need
- [Human in the Loop](https://github.com/80-20-Human-In-The-Loop) - For the ideas
- Django/DRF Community - For the tools

---

**Mercury**: Making performance testing simple for everyone.

*Built with ❤️ by developers who believe people should understand their code.*
