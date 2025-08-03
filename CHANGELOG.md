# Changelog

All notable changes to Django Mercury Performance Testing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-08-03

### Fixed
- Python 3.8 compatibility issues with type hints (List[Path] instead of list[Path])
- Windows build failures for C11 atomics support (added /std:c11 flag for MSVC)
- Unicode encoding errors on Windows (replaced emoji characters with ASCII equivalents)
- CI/CD build order ensuring C libraries are compiled before tests run
- Cross-platform compilation issues (POSIX compatibility, platform-specific flags)

### Added
- Pure Python fallback mode when C extensions are unavailable
- Enhanced test runner script (c_test_runner.sh) with coverage and debugging capabilities
- Comprehensive C test suite including edge cases and boundary testing
- Multi-OS CI/CD support via GitHub Actions (Linux, macOS, Windows)
- DJANGO_MERCURY_PURE_PYTHON environment variable for forcing fallback mode

### Changed
- Improved CI/CD architecture using cibuildwheel for multi-platform wheel building
- Refactored test structure with better organization and separation
- Enhanced error handling and recovery in C extension loading
- Better distinction between Python C extensions and standalone C libraries

### Internal
- Extensive test suite improvements with higher coverage
- Added simple_test targets in Makefile for easier testing
- Improved build system robustness with better error messages
- Reorganized test files for clarity and maintainability
- Added comprehensive performance monitoring tests

## [0.0.1] - 2025-08-02

### Added
- Initial release of Django Mercury Performance Testing framework
- Two main test case classes: `DjangoMercuryAPITestCase` and `DjangoPerformanceAPITestCase`
- N+1 query detection with severity analysis
- Performance grading system (F to A+)
- Smart operation type detection
- Educational guidance when tests fail
- C-powered monitoring for minimal overhead
- Comprehensive metrics: response time, queries, memory
- Support for Django 3.2+ and Django REST Framework
- Colorful terminal output and performance dashboards
- Configurable performance thresholds
- Memory profiling and cache performance analysis

### Known Issues
- Tests require Django to be installed
- C extensions need to be compiled with `make` before use
- Limited to API test cases (standard TestCase support coming soon)

### Coming Soon
- MCP (Model Context Protocol) integration for AI-assisted optimization
- Historical performance tracking
- Standard TestCase for non-API views
- Performance regression detection

[0.0.1]: https://github.com/Django-Mercury/Performance-Testing/releases/tag/v0.0.1