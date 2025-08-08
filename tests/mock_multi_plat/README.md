# Cross-Platform Mock Testing Architecture

## Overview

This directory contains sophisticated cross-platform tests for Django Mercury's C bindings.
The tests can mock any platform behavior regardless of the host OS, enabling comprehensive
testing locally while still running native tests in CI/CD.

## Architecture

### Smart Platform Detection

Tests automatically detect the current platform and:
- Run natively if on the target platform
- Mock the target platform if on a different OS

### Files

- `platform_mocks.py` - Core mocking utilities and decorators
- `test_c_bindings_windows.py` - Windows-specific behavior tests
- `test_c_bindings_linux.py` - Linux-specific behavior tests
- `test_c_bindings_macos.py` - macOS-specific behavior tests
- `test_c_bindings_ci_paths.py` - CI/CD environment path tests
- `test_c_bindings_errors.py` - Error handling and recovery tests
- `test_c_bindings_context_manager.py` - Context manager tests

## Usage

### Running Tests Locally

```bash
# Run all cross-platform tests
python -m pytest tests/mock_multi_plat/

# Run only Windows tests (mocked on Linux/macOS)
python -m pytest tests/mock_multi_plat/test_c_bindings_windows.py

# Run with coverage
python -m pytest tests/mock_multi_plat/ --cov=django_mercury.python_bindings.c_bindings
```

### Writing New Tests

Use the `@mock_platform` decorator:

```python
from tests.mock_multi_plat.platform_mocks import mock_platform

class TestExample(unittest.TestCase):
    
    @mock_platform("Windows")
    def test_windows_specific_behavior(self):
        # This test will:
        # - Run with real Windows behavior on Windows
        # - Run with mocked Windows behavior on Linux/macOS
        pass
```

## CI/CD Integration

These tests run on GitHub Actions across:
- Ubuntu (latest)
- macOS (latest)
- Windows (latest)

Each platform runs its native tests without mocking, ensuring real-world validation.

## Coverage Goals

These tests specifically target low-coverage areas in c_bindings.py:
- Windows .pyd loading (lines 74-96, 414-449)
- CI environment detection (lines 174-201)
- Platform-specific paths (lines 206-214)
- Error handling (lines 400-406, 456-460)
- Context managers (lines 839-872)

Target: Increase c_bindings.py coverage from 66% to 85%+