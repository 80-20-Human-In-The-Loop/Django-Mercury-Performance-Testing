# Django Mercury Educational Testing Mode

Transform your performance testing into an interactive learning journey! Educational Mode teaches you optimization techniques while you test your Django application.

## 🎓 What is Educational Mode?

Educational Mode is an interactive testing experience that:
- **Pauses tests** when performance issues are detected
- **Explains problems** in simple, clear language
- **Teaches solutions** with code examples
- **Tracks progress** across testing sessions
- **Adapts difficulty** based on your expertise level

Following the **80-20 Human-in-the-Loop philosophy**:
- 80% automated detection and monitoring
- 20% human learning and decision-making

## 🚀 Quick Start

### Method 1: Custom Test Runner (Recommended)

Add to your Django settings:

```python
# settings.py or test_settings.py
import sys

# Enable educational mode with --edu flag
if '--edu' in sys.argv:
    TEST_RUNNER = 'django_mercury.test_runner.EducationalTestRunner'
```

Run tests with educational mode:

```bash
python manage.py test --edu
```

### Method 2: Environment Variables

Set up environment variables:

```bash
# Enable educational mode
export MERCURY_EDUCATIONAL_MODE=true

# Set difficulty level (beginner/intermediate/advanced)
export MERCURY_EDU_LEVEL=intermediate

# Run your tests normally
python manage.py test
```

### Method 3: Programmatic Usage

```python
from django_mercury.test_runner import run_tests_with_education

# Run specific tests with education
run_tests_with_education(
    test_labels=['myapp.tests'],
    verbosity=2,
    interactive=True
)
```

## 📚 Difficulty Levels

### Beginner
- Simple explanations with analogies
- Basic optimization techniques
- Foundational concepts (N+1 queries, caching basics)
- Gentle learning curve

### Intermediate (Default)
- Detailed technical explanations
- Advanced optimization patterns
- Performance profiling techniques
- Best practices and trade-offs

### Advanced
- Expert-level optimizations
- Complex query analysis
- Architecture decisions
- Production-scale considerations

Set your level:
```bash
export MERCURY_EDU_LEVEL=advanced
```

## 🎯 Features

### 1. Interactive Performance Analysis

When a test exceeds performance thresholds:

```
╭───────────────── 🚨 Learning Opportunity ─────────────────╮
│                                                            │
│  ⚠️  Performance Issue Detected!                           │
│                                                            │
│  Test: test_user_list_api                                 │
│  Issue Type: N+1 Queries                                  │
│  Details: Queries executed: 230 | Response time: 450ms    │
│                                                            │
╰────────────────────────────────────────────────────────────╯

╭───────────── 📚 What's Happening? ─────────────────╮
│                                                      │
│  ## The N+1 Query Problem                           │
│                                                      │
│  When you fetch a list of objects and then access   │
│  their related data, Django makes:                  │
│  - 1 query to get the list                          │
│  - N additional queries (one for each item)         │
│                                                      │
│  This creates N+1 total queries!                    │
│                                                      │
╰──────────────────────────────────────────────────────╯
```

### 2. Interactive Quizzes

Test your understanding with contextual quizzes:

```
╭────────── 🤔 Quick Learning Check ──────────╮
│                                              │
│  Your test executed 230 queries.            │
│  What's the most likely cause?              │
│                                              │
│  [1] Database connection issues             │
│  [2] Missing select_related()               │
│  [3] Too much test data                     │
│  [4] Slow database server                   │
│                                              │
│  Your answer: _                             │
│                                              │
╰──────────────────────────────────────────────╯
```

### 3. Code Examples and Fixes

Get specific solutions for your code:

```python
╭───────────── ✅ How to Fix ─────────────────╮
│                                              │
│  # Bad: Creates N+1 queries                 │
│  users = User.objects.all()                 │
│  for user in users:                         │
│      print(user.profile.bio)                │
│                                              │
│  # Good: Only 2 queries total               │
│  users = User.objects.select_related(       │
│      'profile'                              │
│  ).all()                                     │
│  for user in users:                         │
│      print(user.profile.bio)                │
│                                              │
╰──────────────────────────────────────────────╯
```

### 4. Progress Tracking

Track your learning journey:

```
╭──────── 📊 Educational Testing Summary ────────╮
│                                                │
│  Metric                  Value                 │
│  ─────────────────────────────────────────    │
│  Total Tests Run         25                   │
│  Tests Passed            22                   │
│  Performance Issues      3                    │
│    - N+1 Queries         2                    │
│    - Slow Response       1                    │
│  Concepts Covered        5                    │
│  Quiz Accuracy           85%                  │
│                                                │
│  📚 Found 3 learning opportunities.           │
│  Review the guidance above to improve!        │
│                                                │
╰────────────────────────────────────────────────╯
```

### 5. Adaptive Learning

The system adapts to your skill level:
- Tracks which concepts you've mastered
- Adjusts quiz difficulty based on performance
- Suggests next learning topics
- Provides personalized optimization tips

## 🛠️ Configuration

### Test-Level Configuration

```python
class MyAPITestCase(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Enable educational features for this test class
        cls.configure_mercury(
            educational_mode=True,
            edu_level='intermediate',
            interactive_quizzes=True,
            show_optimization_tips=True
        )
```

### Global Configuration

Create `mercury_config.json`:

```json
{
  "educational": {
    "enabled": true,
    "level": "intermediate",
    "interactive": true,
    "quiz_frequency": "on_failure",
    "show_fixes": true,
    "track_progress": true
  }
}
```

## 📖 Learning Paths

### Path 1: Query Optimization Journey
1. **N+1 Query Detection** → Learn about select_related()
2. **Prefetch Optimization** → Master prefetch_related()
3. **Query Reduction** → Understand only() and defer()
4. **Advanced Patterns** → Prefetch objects and custom lookups

### Path 2: Performance Profiling
1. **Response Time Analysis** → Identify bottlenecks
2. **Database Indexing** → Speed up queries
3. **Caching Strategies** → Reduce database load
4. **Memory Management** → Handle large datasets

### Path 3: Scalability Practices
1. **Pagination** → Handle large result sets
2. **Async Processing** → Background tasks with Celery
3. **Database Pooling** → Connection management
4. **Load Testing** → Prepare for production

## 🎮 Interactive Commands

During educational testing, you can:

- **`s` or `skip`**: Skip current learning moment
- **`d` or `details`**: Show more detailed explanation
- **`e` or `example`**: Show code examples
- **`q` or `quiz`**: Take a quiz on current topic
- **`h` or `help`**: Show available commands

## 📊 Progress Files

Your learning progress is saved to:
```
~/.django_mercury/
├── learning_progress.json    # Overall progress
├── quiz_history.json         # Quiz performance
└── concepts_mastered.json    # Completed topics
```

View your progress:
```python
from django_mercury.cli.educational.progress_tracker import ProgressTracker

tracker = ProgressTracker()
summary = tracker.get_progress_summary()
print(f"Concepts mastered: {summary['concepts_mastered']}")
print(f"Quiz accuracy: {summary['quiz_accuracy']}%")
print(f"Next suggestion: {summary['next_suggestion']}")
```

## 🚫 Disabling Educational Mode

To run tests without educational features:

### Temporarily
```bash
# Skip educational mode for one run
python manage.py test --no-edu
```

### For Specific Tests
```python
@override_settings(MERCURY_EDUCATIONAL_MODE=False)
def test_performance_critical():
    # This test runs without educational interruptions
    pass
```

### In CI/CD
```yaml
# .github/workflows/test.yml
- name: Run Tests
  env:
    MERCURY_EDUCATIONAL_MODE: false
  run: python manage.py test
```

## 🎯 Best Practices

1. **Start with Beginner Mode**: Even experts can learn from the basics
2. **Complete the Quizzes**: They reinforce important concepts
3. **Review Fix Suggestions**: Apply them to your actual code
4. **Track Your Progress**: Celebrate improvements over time
5. **Share Knowledge**: Discuss learnings with your team

## 🌟 Example Session

```bash
$ python manage.py test --edu

╭─────────────────────────────────────────────────────────╮
│  🎓 Django Mercury Educational Testing Mode             │
│                                                          │
│  Interactive Learning Experience Active                  │
│  📚 Difficulty Level: Intermediate                       │
│  🎯 Performance Monitoring: Active                       │
│  🧠 Interactive Quizzes: Enabled                         │
│                                                          │
│  Tests will pause at learning moments...                 │
╰──────────────────────────────────────────────────────────╯

Running tests...

test_user_list_api ... 
⚠️  Performance Issue - Learning Opportunity!

Your test made 150 queries to load 50 users.
This is called an 'N+1 Query Problem'.

🤔 Quick Check: Which Django ORM method would fix this?
  [1] filter()
  [2] select_related()
  [3] prefetch_related()
  [4] annotate()

Your answer: 2

✅ Correct! 

💡 Explanation: select_related() performs a SQL join 
and includes related objects in a single query, perfect 
for ForeignKey and OneToOne relationships.

Ready to continue testing? [Y/n]: y

test_user_list_api ... ok

Ran 1 test in 2.341s

╭──────── 📊 Educational Testing Summary ────────╮
│                                                │
│  Tests Run: 1                                  │
│  Performance Issues Found: 1                  │
│  Concepts Covered: N+1 Queries                │
│  Quiz Accuracy: 100%                          │
│                                                │
│  🎉 Great job! You're learning fast!          │
│                                                │
│  Progress saved to ~/.django_mercury/         │
╰────────────────────────────────────────────────╯
```

## 🤝 Contributing

Help us improve educational content:

1. **Add Quiz Questions**: Contribute to `django_mercury/cli/educational/data/quizzes.json`
2. **Improve Explanations**: Make complex concepts clearer
3. **Share Learning Paths**: Document your optimization journey
4. **Report Issues**: Help us fix confusing content

## 📚 Additional Resources

- [Django Performance Optimization Guide](https://docs.djangoproject.com/en/stable/topics/performance/)
- [Database Optimization Best Practices](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [Django Debug Toolbar Documentation](https://django-debug-toolbar.readthedocs.io/)
- [Django Mercury Main Documentation](../README.md)

## 🎓 Philosophy

> "The best way to learn performance optimization is by doing it. Educational Mode ensures you learn while you test, turning every performance issue into a teaching moment."

Remember: **80% automation, 20% human learning, 100% better code!**

---

*Educational Mode: Because every developer deserves to understand why their code is slow and how to fix it.*