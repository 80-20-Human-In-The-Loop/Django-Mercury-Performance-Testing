The Community Wiki is Living Documentation:

[Contributing - Python Standards](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Contributing-Python-Standards)

[Contributing - C Standards](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Contributing-C-Standards)

# Contributing to Django Mercury Performance Testing

Thank you for your interest in contributing to Django Mercury! We believe in the power of community and welcome contributions that align with our mission of making performance testing accessible and educational.

## Our Philosophy

Django Mercury is part of the [Human in the Loop](https://github.com/80-20-Human-In-The-Loop) ecosystem, which means we value:
- **Open**: Knowledge should be accessible to everyone
- **Free**: Freedom to use, study, share, and improve
- **Fair**: Contributions benefit the entire community
- **Educational**: Tools should teach, not just detect

## How to Contribute

### 1. Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/Django-Mercury-Performance-Testing.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`
6. Build C extensions: `cd django_mercury/c_core && make clean && make`

### 2. Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes following our coding standards
3. Write or update tests as needed
4. Update documentation if applicable
5. Commit with clear, descriptive messages

### 3. Testing Your Changes

Django Mercury has comprehensive testing for both Python and C components. We provide helper scripts to make testing easy.

#### Test Structure
```
tests/                      # Python tests
├── test_complete_integration.py
├── test_c_extensions.py
├── monitor/               # Monitor-specific tests
└── ...

django_mercury/c_core/tests/  # C tests
├── simple_test_*.c        # Basic unit tests
├── comprehensive_test_*.c # Full feature tests
├── edge_test_*.c         # Edge case tests
└── coverage_boost_test.c  # Coverage improvement tests
```

#### Quick Test Commands

```bash
# Run ALL Python tests with coverage
pytest tests/ -v --cov=django_mercury --cov-report=term-missing

# Run specific Python test file
pytest tests/test_complete_integration.py -v

# Run C tests using helper script (from project root)
./c_run_tests.sh          # Run simple C tests
./c_run_tests.sh coverage # Run C tests with coverage analysis
./c_run_tests.sh all      # Run all C tests and coverage

# Check Python code quality
black django_mercury/
isort django_mercury/
ruff check django_mercury/

# Quick build check
python setup.py build_ext --inplace
```

#### Test Helpers

**c_run_tests.sh** - C test runner script (in project root)
- `./c_run_tests.sh test` - Run unit tests
- `./c_run_tests.sh coverage` - Generate coverage report
- `./c_run_tests.sh clean` - Clean test artifacts
- `./c_run_tests.sh build` - Build C libraries
- `./c_run_tests.sh benchmark` - Run performance benchmarks
- `./c_run_tests.sh memcheck` - Memory leak detection (Linux)

#### Adding New Tests

**Python Tests:**
1. Create test file in `tests/` directory
2. Inherit from `unittest.TestCase` or `DjangoMercuryAPITestCase`
3. Follow naming convention: `test_*.py`
4. Example:
```python
# tests/test_my_feature.py
import unittest
from django_mercury import DjangoMercuryAPITestCase

class TestMyFeature(DjangoMercuryAPITestCase):
    def test_feature_works(self):
        # Your test here
        self.assertTrue(True)
```

**C Tests:**
1. Create test file in `django_mercury/c_core/tests/`
2. Follow naming convention: `simple_test_*.c` or `comprehensive_test_*.c`
3. Include test framework: `#include "test_framework.h"`
4. Register tests in the Makefile
5. Example:
```c
// django_mercury/c_core/tests/simple_test_myfeature.c
#include <stdio.h>
#include <assert.h>
#include "../myfeature.h"

int main() {
    printf("Testing my feature...\n");
    assert(my_function() == expected_value);
    printf("✓ All tests passed!\n");
    return 0;
}
```

### 4. Submitting Changes

1. Push to your fork: `git push origin feature/your-feature-name`
2. Create a Pull Request with:
   - Clear description of changes
   - Link to related issue (if applicable)
   - Screenshots/examples for UI changes
   - Performance impact analysis for core changes

## Types of Contributions We're Looking For

### High Priority
- Performance optimization algorithms
- N+1 query detection improvements
- Educational guidance enhancements
- Django 5.1+ compatibility updates
- Documentation improvements

### Feature Ideas
- MCP (Model Context Protocol) integration
- Historical performance tracking
- Standard TestCase support (non-API)
- Performance regression detection
- Additional database backend support

### Always Welcome
- Bug fixes with test coverage
- Documentation improvements
- Example code and tutorials
- Performance optimization stories
- Translations

## Code Standards

### Python Code
- Follow PEP 8 with 100-character line limit
- Use type hints where possible
- Add docstrings to all public functions
- Maintain test coverage above 75%

### C Code
- Follow existing code style in c_core/
- Include comprehensive tests
- Document memory management carefully
- Ensure thread safety

### Commit Messages
Format: `type: brief description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `perf`: Performance improvements
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Maintenance tasks

Example: `feat: add PostgreSQL-specific query analyzer`

## Reporting Issues

### Bug Reports Should Include:
1. Django and Python versions
2. Complete error traceback
3. Minimal reproducible example
4. Expected vs actual behavior
5. Performance metrics if relevant

### Feature Requests Should Include:
1. Use case description
2. Proposed solution
3. Alternative approaches considered
4. Impact on existing functionality
5. Performance implications

## Community Guidelines

We follow the Contributor Covenant Code of Conduct. Key points:
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what's best for the community
- Show empathy towards others
- Accept constructive criticism gracefully

## Development Setup Tips

### Quick Setup
```bash
# Clone and setup
git clone https://github.com/your-username/Django-Mercury-Performance-Testing.git
cd Django-Mercury-Performance-Testing
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Build C extensions
./c_run_tests.sh build

# Verify everything works
pytest tests/ -v
./c_run_tests.sh test
```

### Building C Extensions
```bash
# Using helper script (recommended)
./c_run_tests.sh build

# Or manually
cd django_mercury/c_core
make clean
make
make test
```

### Running Specific Tests
```bash
# Python tests
pytest tests/test_specific.py::TestClass::test_method -v

# Run tests matching a pattern
pytest tests/ -k "test_performance" -v

# C tests - run individual test binary
cd django_mercury/c_core
./simple_test_performance_monitor

# Or use helper for all tests
./c_run_tests.sh test
```

### Performance Testing Your Changes
```bash
# Test the performance impact of your changes
python test_performance_comparison.py

# Use Mercury to test itself!
python -c "
from django_mercury import DjangoMercuryAPITestCase
# Your performance test here
"
```

### Debugging Tips
```bash
# Run Python tests with verbose output
pytest tests/ -vvs

# Debug C tests with gdb (Linux/Mac)
cd django_mercury/c_core
gdb ./simple_test_performance_monitor

# Check for memory leaks (Linux)
./c_run_tests.sh memcheck

# Generate coverage reports
pytest tests/ --cov=django_mercury --cov-report=html
./c_run_tests.sh coverage
```

## Getting Help

- **Discord**: Join our community server (coming soon)
- **Issues**: Check existing issues or create new ones
- **Discussions**: Use GitHub Discussions for questions
- **Email**: mercury@djangoperformance.dev

## Recognition

All contributors will be:
- Listed in our CONTRIBUTORS file
- Mentioned in release notes
- Given credit in documentation

## License

By contributing, you agree that your contributions will be licensed under GPL-3.0, maintaining the project's commitment to open source principles.

## First-Time Contributors

New to open source? We're here to help!

1. Look for issues labeled `good first issue`
2. Read our documentation thoroughly
3. Ask questions - we're happy to guide you
4. Start small - even typo fixes are valuable
5. Join our community discussions

Remember: Every expert was once a beginner. Your perspective as a newcomer is valuable for making our tools more accessible!

---

Thank you for helping make Django Mercury better for everyone! Your contributions help developers worldwide write more performant Django applications.
