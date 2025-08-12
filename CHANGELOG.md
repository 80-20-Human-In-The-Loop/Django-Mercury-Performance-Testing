# Changelog

All notable changes to Django Mercury Performance Testing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.7] - 2025-08-12

### Added
- **Extension Verification Command**: New `mercury-test --ext` command to verify C extensions are loaded and working
- **Performance Benchmarking**: New `mercury-test --benchmark` command to compare C extension vs pure Python performance
- **Memory Safety Testing**: Added comprehensive Valgrind memcheck tests for C extensions
- **Microsecond Precision Display**: Benchmark results now show microseconds (µs) for very fast operations

### Fixed
- **C Extension Build Issues**: Fixed Makefile TEST_DIR variable ordering that caused build failures
- **Memory Leak Detection**: Added Valgrind suppressions for false positives from libunwind
- **Benchmark Accuracy**: Fixed query analyzer benchmark to prevent cache hits and show real performance
- **macOS Compatibility**: Fixed build issues on macOS systems
- **Windows CI Build Failure**: Fixed metrics_engine.c compilation on Windows by adding conditional includes for Unix-specific headers (unistd.h)

### Changed
- **Test Framework Organization**: Reorganized C test headers into modular components (test_base.h, test_simple.h, test_enhanced.h, test_security.h)
- **Benchmark Display**: Added explanations of what each implementation does (e.g., C does basic tracking, Python does full monitoring)
- **Query Generation**: Benchmark now uses deterministic seeds for consistent performance comparisons

### Developer Notes
- Test Orchestrator benchmark shows 787-1186x speedup because implementations have different features (C: basic tracking, Python: full performance monitoring with GC)
- This will be addressed in v0.0.8 with feature parity improvements

## [0.0.6] - 2025-08-10

### Fixed
- **Query Counting**: Fixed issue where Django Mercury reported 0 queries even when database operations were performed
  - Updated `DjangoQueryTracker` to use Django's built-in `connection.queries` as primary source when DEBUG=True
  - Modified query tracker to sync with Django's query log in the `stop()` method
  - Fixed fallback metrics to prioritize custom tracker count over Django's total queries
  - Ensured proper handling of query counts in both C extension and Python fallback paths

### Changed
- **Query Tracking Priority**: Changed order to use session-specific query counts from custom tracker before falling back to Django's total

## [0.0.5] - 2025-08-10

### Added
- **3-Tier Educational Mode Access**: Implemented three user-friendly ways to enable educational mode:
  - `mercury-test` console command for immediate use
  - `MERCURY_EDU=1` environment variable for CI/CD integration
  - `enable_educational_testing()` function for programmatic control
- **Enhanced Quiz System**: Added 5 new beginner-level N+1 quiz questions for variety
- **Contextual Educational Content**: Educational explanations now include test-specific metrics and tailored advice

### Fixed
- **Educational Mode Interactivity**: Fixed EOF errors in educational mode by detecting non-interactive environments (CI, piped input) and gracefully falling back to non-interactive output
- **C Extension Loading**: Fixed issue where C extensions failed to load when installed from PyPI by using Python extension modules instead of standalone libraries
- **Key Mismatches**: Fixed concept key mismatches between `n+1_queries` and `n_plus_one_queries`

## [0.0.4] - 2025-08-08

### Fixed
- **Python 3.11/3.12 Compatibility**: Fixed unittest.mock AttributeError issues by using patch.object instead of string-based patching
- **Platform-Specific Testing**: Simplified test architecture to only run platform-specific tests on their actual platforms (no cross-platform mocking)
- **Windows Test Failures**: Fixed Windows-specific test failures with proper error messages and exception handling
- **Variable Name Collisions**: Fixed variable name collisions in platform mocks
- **Library Configuration**: Fixed LIBRARY_CONFIG patching for Windows tests

### Changed
- **Test Architecture**: Platform tests now use `@unittest.skipUnless` instead of complex mocking decorators
- **Error Handling**: Windows error tests now use platform-appropriate error messages (PE format instead of ELF)
- **Exception Wrapping**: Windows code path now properly wraps non-ImportError exceptions as ImportError

### Removed
- **mercury_test Command**: Removed abandoned Django management command - educational mode now properly uses TEST_RUNNER approach only

### Enhanced  
- **Educational Mode**: Expanded quiz system with more comprehensive questions and improved interactive UI
- **Educational Guidance**: Enhanced performance issue explanations and learning content
- **Learning Paths**: Added progressive learning paths for different skill levels

### Documentation
- **Issue Template**: Updated to reflect correct usage (`python manage.py test --edu` instead of `mercury_test --edu`)

## [0.0.3] - 2025-08-06

### Fixed
- **GLIBC Compatibility**: Fixed Linux wheel compatibility issues by using manylinux_2_28 containers and proper GLIBC symbol versioning
- **Windows Build**: Improved Windows C extension building with better MSVC detection and .pyd file handling
- **macOS Library Extensions**: Fixed library extension mismatch issues on macOS (.so vs .dylib)
- **Thread Safety**: Enhanced thread safety in monitor module with proper lock acquisition

### Changed
- **CI/CD Pipeline**: Refactored GitHub Actions workflow to build wheels independently of test results
- **Build System**: Switched to manylinux_2_28 for better Linux distribution compatibility
- **Wheel Building**: Updated cibuildwheel configuration for more reliable cross-platform builds
- **Test Organization**: Reorganized test structure into logical subdirectories (bindings/, config/, core/, django_integration/, monitor/)

### Added
- **Build Scripts**: Added comprehensive CI test runner script (scripts/ci_test_runner.sh) for all platforms
- **Diagnostics**: New diagnostic scripts for verifying C extension builds (scripts/diagnose_c_extensions.py, scripts/verify_build.py)
- **Pure Python Tests**: Comprehensive pure Python fallback tests for all C modules
- **Security Tests**: Added security test suite for C extensions including buffer overflow and memory safety checks

### Internal
- **Test Coverage**: Improved test organization with separated test modules by functionality
- **Build Verification**: Added scripts to verify C extension loading across platforms
- **Documentation**: Added CLAUDE.md files for architecture documentation
- **Git Configuration**: Added .gitattributes for better cross-platform compatibility
- **PyPI Deployment**: Fixed twine validation error by upgrading setuptools to handle metadata correctly

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

[0.0.4]: https://github.com/Django-Mercury/Performance-Testing/releases/tag/v0.0.4
[0.0.3]: https://github.com/Django-Mercury/Performance-Testing/releases/tag/v0.0.3
[0.0.2]: https://github.com/Django-Mercury/Performance-Testing/releases/tag/v0.0.2
[0.0.1]: https://github.com/Django-Mercury/Performance-Testing/releases/tag/v0.0.1