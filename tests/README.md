# Django Mercury Performance Testing - Test Suite Documentation

## Overview

This test suite has been reorganized into a modular architecture for better maintainability and organization. The tests are now grouped by functionality rather than having duplicate files.

## Test Structure

```
tests/
├── monitor/                    # Performance monitoring tests
├── django_integration/          # Django-specific integration tests
│   ├── mercury_api/            # DjangoMercuryAPITestCase tests
│   └── performance_api/        # DjangoPerformanceAPITestCase tests
├── hooks/                      # Hook system tests
├── bindings/                   # C extension and Python binding tests
├── core/                       # Core functionality tests
├── config/                     # Configuration and settings tests
└── integration/                # Full integration tests
```

## Test Categories

### Monitor Tests (`tests/monitor/`)
- `test_monitor_core.py` - Core monitoring functionality
- `test_basic_monitoring.py` - Basic monitoring operations
- `test_performance_metrics.py` - Performance metrics calculations
- `test_scoring_boundaries.py` - Scoring algorithm boundary tests

### Django Integration Tests (`tests/django_integration/`)

#### Mercury API (`mercury_api/`)
- `test_django_analyzer.py` - Django query analyzer
- `test_django_hooks.py` - Django hooks implementation
- `test_django_hooks_edge_cases.py` - Edge cases for hooks
- `test_django_integration.py` - Basic Django integration
- `test_django_integration_mercury.py` - Mercury-specific integration
- `test_django_integration_mercury_comprehensive.py` - Comprehensive scenarios
- `test_django_integration_mercury_exceptions.py` - Exception handling
- `test_django_integration_mercury_guidance.py` - Educational guidance features
- `test_django_integration_mercury_reporting.py` - Reporting functionality
- `test_mercury_config.py` - Mercury configuration

#### Performance API (`performance_api/`)
Currently empty - reserved for future DjangoPerformanceAPITestCase tests

### Bindings Tests (`tests/bindings/`)
- `test_c_extensions.py` - C extension loading and fallback
- `test_c_integration_simple.py` - Simple C library integration
- `test_c_bindings_failures.py` - Error handling in C bindings
- `test_new_c_integrations.py` - Enhanced C integration tests

### Core Tests (`tests/core/`)
- `test_validation.py` - Input validation
- `test_colors.py` - Color output functionality
- `test_constants.py` - Constants and configuration
- `test_metrics.py` - Metrics calculations
- `test_error_reporting.py` - Error reporting
- `test_thread_safety.py` - Thread safety tests

### Config Tests (`tests/config/`)
- `test_logging_config.py` - Logging configuration
- `test_settings.py` - Settings management

### Integration Tests (`tests/integration/`)
- `test_complete_integration.py` - End-to-end integration tests

### Hooks Tests (`tests/hooks/`)
Currently empty - reserved for hook-specific tests

## Running Tests

### Run All Tests
```bash
./test_runner.py
```

### Run with Coverage
```bash
./test_runner.py --coverage
```

### Run Specific Category
```bash
# Run only monitor tests
python -m pytest tests/monitor/

# Run only Django integration tests
python -m pytest tests/django_integration/

# Run only binding tests
python -m pytest tests/bindings/
```

### Run Individual Test File
```bash
python -m pytest tests/monitor/test_scoring_boundaries.py -v
```

### Using the Test Runner
```bash
# List all available test modules
./test_runner.py --list-modules

# Run with verbose output
./test_runner.py --verbose

# Run C integration tests
./test_runner.py --c-tests

# Run all tests including C tests
./test_runner.py --all

# Disable timing analysis
./test_runner.py --no-timing
```

## Test Statistics

- **Total Test Files**: 22
- **Total Test Cases**: ~708
- **Categories**: 7
- **Removed Duplicates**: 13 redundant monitor test files

## Test Performance Targets

Tests are categorized by execution time:
- 🟢 **Fast**: < 0.1s
- 🟡 **Medium**: 0.1-0.5s  
- 🔴 **Slow**: 0.5-2s
- 💀 **Critical**: > 2s

Goal: Keep all tests in the green zone (< 0.1s)

## Common Test Patterns

### Performance Monitoring Test
```python
class TestMonitoringFeature(unittest.TestCase):
    def test_basic_monitoring(self):
        monitor = EnhancedPerformanceMonitor("test_op")
        with monitor:
            # Simulate work
            time.sleep(0.01)
        metrics = monitor.get_metrics()
        self.assertIsNotNone(metrics)
```

### Django Integration Test
```python
class TestDjangoIntegration(DjangoMercuryAPITestCase):
    def test_view_monitoring(self):
        with self.monitor_performance():
            response = self.client.get('/api/test/')
        self.assert_performance_within_limits()
```

## Maintenance Notes

1. **No Duplicate Tests**: Each test should exist in only one file
2. **Clear Organization**: Tests should be in the appropriate category folder
3. **Fast Execution**: Aim for sub-100ms test execution times
4. **Comprehensive Coverage**: Maintain >90% code coverage

## Troubleshooting

### C Extension Tests Failing
If C extension tests fail with "cannot open shared object file":
```bash
cd c_core
make clean
make all
```

### Memory Threshold Failures
Tests may fail due to memory thresholds. These are typically set at 130MB but can be adjusted in individual test classes:
```python
cls.set_performance_thresholds({'memory_overhead_mb': 200})
```

### Import Errors
Ensure all test directories have `__init__.py` files and the parent directory is in the Python path.

## Contributing

When adding new tests:
1. Place them in the appropriate category folder
2. Follow existing naming conventions (`test_*.py`)
3. Ensure tests are fast (< 0.1s ideally)
4. Update this README if adding new categories
5. Run the full test suite before committing