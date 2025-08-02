/**
 * @file simple_tests.h
 * @brief Simple test framework macros for Mercury Performance Testing Framework
 */

#ifndef SIMPLE_TESTS_H
#define SIMPLE_TESTS_H

#include <stdio.h>
#include <stdlib.h>

// ANSI color codes for test output
#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_CYAN    "\x1b[36m"
#define ANSI_COLOR_RESET   "\x1b[0m"

// Global test counters (defined in each test file's main())
extern int total_tests;
extern int passed_tests;
extern int failed_tests;

// Test assertion macro
#define ASSERT(condition, message) do { \
    total_tests++; \
    if (!(condition)) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  at %s:%d in %s()\n", __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET "\n", message); \
        passed_tests++; \
    } \
} while(0)

// Test suite macros
#define TEST_SUITE_START(name) do { \
    printf(ANSI_COLOR_CYAN "\n=== %s ===" ANSI_COLOR_RESET "\n", name); \
    total_tests = 0; \
    passed_tests = 0; \
    failed_tests = 0; \
} while(0)

#define RUN_TEST(test_func) do { \
    printf(ANSI_COLOR_YELLOW "\nRunning %s..." ANSI_COLOR_RESET "\n", #test_func); \
    if (test_func()) { \
        printf(ANSI_COLOR_GREEN "✓ %s passed" ANSI_COLOR_RESET "\n", #test_func); \
    } else { \
        printf(ANSI_COLOR_RED "✗ %s failed" ANSI_COLOR_RESET "\n", #test_func); \
    } \
} while(0)

#define TEST_SUITE_END() do { \
    printf(ANSI_COLOR_CYAN "\n=== Results ===" ANSI_COLOR_RESET "\n"); \
    printf("Total: %d, Passed: " ANSI_COLOR_GREEN "%d" ANSI_COLOR_RESET ", Failed: " ANSI_COLOR_RED "%d" ANSI_COLOR_RESET "\n", \
           total_tests, passed_tests, failed_tests); \
    if (failed_tests > 0) { \
        printf(ANSI_COLOR_RED "%d test(s) failed!" ANSI_COLOR_RESET "\n", failed_tests); \
    } else { \
        printf(ANSI_COLOR_GREEN "All tests passed!" ANSI_COLOR_RESET "\n"); \
    } \
} while(0)

#endif // SIMPLE_TESTS_H