# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django Mercury is a performance testing framework for Django applications that helps developers understand and fix performance issues. It follows the 80-20 Human-in-the-Loop principle: 80% automation for detection and monitoring, 20% human control for decisions and optimizations.

Key features:
- Automatic performance monitoring in tests
- N+1 query detection
- Educational mode for learning
- Plugin system for extensibility
- Grade-based performance scoring (S, A+, A, B, C, D, F)

## Common Development Commands

### Running Tests

```bash
# Run all tests with timing analysis
python test_runner.py

# Run with coverage reporting
python test_runner.py --coverage

# Run specific module tests
python test_runner.py --module monitor

# Run with pytest (alternative)
pytest tests/ -v --tb=short

# CI test runner
./scripts/ci_test_runner.sh
```

### Code Quality Commands

```bash
# Format code with Black
black django_mercury/ tests/ --line-length 100

# Sort imports with isort
isort django_mercury/ tests/ --profile black --line-length 100

# Type checking with mypy
mypy django_mercury/

# Linting with ruff
ruff check django_mercury/ tests/

# Run all quality checks
black django_mercury/ tests/ --check && isort django_mercury/ tests/ --check && mypy django_mercury/ && ruff check django_mercury/ tests/
```

### Building and Installation

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Build wheel
python -m build

# Verify installation
python scripts/verify_build.py

# Deploy to PyPI (maintainers only)
./deploy.sh
```

### Mercury CLI Commands

```bash
# List available plugins
mercury-test --list-plugins

# Run with educational mode
mercury-test --edu

# Run with wizard plugin for interactive test selection
mercury-test --wizard

# Run with learning plugin
mercury-test --learn
```

## Architecture Overview

### Core Components

1. **django_mercury/python_bindings/** - Core monitoring functionality
   - `django_integration_mercury.py` - Main test case classes (DjangoMercuryAPITestCase, DjangoPerformanceAPITestCase)
   - `monitor.py` - Performance monitoring implementation
   - `metrics.py` - Performance metrics collection
   - `constants.py` - Configuration constants and thresholds
   - `django_hooks.py` - Django signal integration

2. **django_mercury/cli/** - Command-line interface
   - `mercury_test.py` - Main CLI entry point
   - `plugins/` - Plugin system implementation
     - `learn/` - Educational learning plugin
     - `plugin_manager.py` - Plugin loading and management
     - `plugin_wizard.py` - Interactive test selection

3. **django_mercury/cli/educational/** - Educational mode components
   - `interactive_ui.py` - Interactive learning interface
   - `quiz_system.py` - Quiz functionality for learning
   - `progress_tracker.py` - Learning progress tracking

### Test Case Hierarchy

```python
DjangoMercuryAPITestCase     # Automatic monitoring (investigation tool)
    └── APITestCase (Django REST Framework)

DjangoPerformanceAPITestCase # Manual control with assertions
    └── APITestCase (Django REST Framework)
```

### Plugin System

The framework uses a priority-based plugin system. Plugins are discovered automatically and can be enabled/disabled via CLI flags. Key plugins:
- **discovery** (priority: 10) - Intelligent manage.py discovery
- **wizard** (priority: 20) - Interactive test selection
- **learn** (priority: 60) - Educational content and quizzes
- **hints** (priority: 90) - Performance tips for slow tests

## Code Standards

### Type Hints (REQUIRED for new code)
- All new files must include type hints
- Use `from typing import Optional, Dict, List, Tuple, Union, Any`
- Dataclasses are preferred for configuration objects

### Import Organization
```python
# Standard library
import os
from typing import Dict, Optional

# Third-party
import django
from rest_framework.test import APITestCase

# Local (use relative imports)
from .monitor import PerformanceMonitor
from ..utils import format_time
```

### Error Handling
- Gracefully fall back from C extensions to pure Python
- Provide detailed validation errors
- Log warnings for degraded functionality

### Testing Requirements
- Tests must run in <0.1s (green), avoid >0.5s (red)
- No sleep() calls in tests
- Mock external services
- Use in-memory SQLite for test database

## Performance Thresholds

Default thresholds used by Mercury:
- Response time: 200ms (configurable)
- Query count: 20 max (configurable)
- Memory overhead: 50MB (configurable)
- Cache hit ratio: 70% minimum

Grade boundaries:
- S: Perfect performance (100 points)
- A+: Excellent (90-99 points)
- A: Very Good (80-89 points)
- B: Good (70-79 points)
- C: Acceptable (60-69 points)
- D: Poor (50-59 points)
- F: Failing (<50 points)

## Common Patterns

### Using Mercury in Tests
```python
# Automatic monitoring
class MyTest(DjangoMercuryAPITestCase):
    def test_api(self):
        response = self.client.get('/api/endpoint/')
        # Performance monitored automatically

# Manual control
from django_mercury import monitor_django_view

class MyTest(DjangoPerformanceAPITestCase):
    def test_with_assertions(self):
        with monitor_django_view("operation") as monitor:
            response = self.client.get('/api/endpoint/')
        
        self.assertResponseTimeLess(monitor, 100)
        self.assertQueriesLess(monitor, 10)
```

### Configuring Mercury
```python
class MyTest(DjangoMercuryAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_mercury(
            enabled=True,
            auto_scoring=True,
            educational_guidance=True
        )
        cls.set_performance_thresholds({
            'response_time_ms': 100,
            'query_count_max': 10,
        })
```

## Educational Philosophy

Mercury is designed to teach, not just detect problems. It:
- Explains performance issues in simple language
- Provides step-by-step fixes
- Tracks learning progress
- Uses quizzes to test understanding
- Follows the principle: "Clear code removes barriers to education"

## Important Notes

- Mercury is part of the 80-20 Human-In-The-Loop ecosystem
- Built for EduLite to help students learn with slow internet
- Licensed under GPL-3.0 to keep knowledge open for all
- Values: Fair, Free, and Open
- Designed for global accessibility (simple English that translates well)