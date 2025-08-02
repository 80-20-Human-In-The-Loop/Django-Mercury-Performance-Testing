# Changelog

All notable changes to Django Mercury Performance Testing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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