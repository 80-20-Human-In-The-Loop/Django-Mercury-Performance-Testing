# DjangoMercuryAPITestCase Documentation

`DjangoMercuryAPITestCase` is an intelligent, self-managing performance test case for Django APIs. It is designed to automate performance monitoring, smart threshold management, N+1 detection, scoring, trend analysis, and reporting with minimal boilerplate code.

This class inherits from `DjangoPerformanceAPITestCase` and provides a fully automated testing experience, making it easy to integrate performance testing into your development workflow.

---

## Core Features

- **Automated Monitoring**: Automatically wraps all test methods with performance monitoring.
- **Intelligent Thresholds**: Smart threshold management based on operation complexity and historical data.
- **N+1 Detection**: Automatic detection of N+1 query patterns with actionable guidance.
- **Performance Scoring**: A comprehensive scoring system to evaluate performance.
- **Historical Analysis**: Tracks performance history to detect regressions and trends.
- **Executive Summaries**: Generates comprehensive summaries with actionable insights.

---

## Configuration

Mercury's behavior can be configured at the class level to tailor the testing process to your needs.

### `configure_mercury(...)`

Configures the behavior of the Mercury test case for the entire class.

- **Args**:
  - `enabled` (bool): Enables or disables Mercury's features.
  - `auto_scoring` (bool): Enables or disables automatic performance scoring.
  - `auto_threshold_adjustment` (bool): Enables or disables smart threshold adjustments.
  - `store_history` (bool): Enables or disables storing performance history.
  - `verbose_reporting` (bool): Enables or disables verbose reporting for each test.

### `set_performance_thresholds(...)`

Sets custom performance thresholds for all tests in the class.

- **Args**:
  - `thresholds` (Dict[str, Union[int, float]]): A dictionary of performance thresholds.

### `set_test_performance_thresholds(...)`

Sets custom performance thresholds for a single test method, overriding class-level settings.

- **Args**:
  - `thresholds` (Dict[str, Union[int, float]]): A dictionary of performance thresholds for the current test.

---

## Automated Workflow

`DjangoMercuryAPITestCase` automates the following steps for each test method:

1. **Operation Detection**: Intelligently determines the type of operation being tested (e.g., list view, detail view).
2. **Threshold Calculation**: Calculates smart performance thresholds based on the operation type, historical data, and any custom overrides.
3. **Execution and Monitoring**: Runs the test while monitoring performance metrics.
4. **Scoring and Analysis**: Scores the performance and analyzes the results for issues like N+1 queries.
5. **History Tracking**: Stores the results in a performance history database to track trends and detect regressions.
6. **Reporting**: Generates a final executive summary with actionable insights and optimization recommendations.

---

## Educational Guidance

When a test fails due to a performance issue, Mercury provides educational guidance in the console, explaining the likely cause of the failure and offering concrete suggestions for how to fix it. This feature is designed to help developers learn about performance best practices and improve their code.

---

## Executive Summary

After all tests in the class have been executed, Mercury generates a comprehensive executive summary that includes:

- **Overall Performance Grade**: A letter grade (S, A, B, C, D, F) summarizing the performance of the test suite.
- **Grade Distribution**: A breakdown of how many tests achieved each grade.
- **Critical Issues**: A list of the most critical performance issues found.
- **Performance Trends**: An analysis of how performance has changed over time.
