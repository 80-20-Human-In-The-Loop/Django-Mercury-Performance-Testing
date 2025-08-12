/**
 * @file simple_tests.h
 * @brief Simple test framework macros for Mercury Performance Testing Framework
 */

#ifndef SIMPLE_TESTS_H
#define SIMPLE_TESTS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

// Quiet mode support
extern int quiet_mode;
extern int test_assertions;
extern int test_passed;
extern int test_failed;
extern char test_failure_buffer[4096];
extern int test_failure_buffer_used;

// Test assertion macro - respects quiet mode
#define ASSERT(condition, message) do { \
    if (quiet_mode) { \
        /* In quiet mode, use ASSERT_QUIET behavior */ \
        test_assertions++; \
        total_tests++; \
        if (!(condition)) { \
            test_failed++; \
            failed_tests++; \
            if (test_failure_buffer_used < (int)(sizeof(test_failure_buffer) - 256)) { \
                test_failure_buffer_used += snprintf(test_failure_buffer + test_failure_buffer_used, \
                    sizeof(test_failure_buffer) - test_failure_buffer_used, \
                    "  " ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n    at %s:%d in %s()\n", \
                    message, __FILE__, __LINE__, __func__); \
            } \
            return 0; \
        } else { \
            test_passed++; \
            passed_tests++; \
        } \
    } else { \
        /* Verbose mode - show all assertions */ \
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
    } \
} while(0)

// Test suite macros
#define TEST_SUITE_START(name) do { \
    printf(ANSI_COLOR_CYAN "\n=== %s ===" ANSI_COLOR_RESET "\n", name); \
    total_tests = 0; \
    passed_tests = 0; \
    failed_tests = 0; \
} while(0)

// Initialize quiet mode based on environment variable
#define QUIET_MODE_INIT() do { \
    const char* verbose = getenv("TEST_VERBOSE"); \
    /* Default to quiet mode (1) unless TEST_VERBOSE is explicitly set to "1" */ \
    quiet_mode = (verbose == NULL || strcmp(verbose, "1") != 0); \
} while(0)

// Test function with quiet mode support
#define TEST_FUNCTION_START() do { \
    test_assertions = 0; \
    test_passed = 0; \
    test_failed = 0; \
    test_failure_buffer_used = 0; \
    test_failure_buffer[0] = '\0'; \
} while(0)

// Quiet assertion macro - only shows failures
#define ASSERT_QUIET(condition, message) do { \
    test_assertions++; \
    total_tests++; \
    if (!(condition)) { \
        test_failed++; \
        failed_tests++; \
        if (test_failure_buffer_used < sizeof(test_failure_buffer) - 256) { \
            test_failure_buffer_used += snprintf(test_failure_buffer + test_failure_buffer_used, \
                sizeof(test_failure_buffer) - test_failure_buffer_used, \
                "  " ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n    at %s:%d in %s()\n", \
                message, __FILE__, __LINE__, __func__); \
        } \
    } else { \
        test_passed++; \
        passed_tests++; \
    } \
} while(0)

// Run test with quiet mode support
#define RUN_TEST(test_func) do { \
    printf(ANSI_COLOR_YELLOW "\nRunning %s..." ANSI_COLOR_RESET "\n", #test_func); \
    if (quiet_mode) { \
        TEST_FUNCTION_START(); \
        int result = test_func(); \
        (void)result; /* Suppress unused variable warning */ \
        if (test_failed == 0) { \
            printf(ANSI_COLOR_GREEN "✓ %s: %d assertions passed" ANSI_COLOR_RESET "\n", #test_func, test_passed); \
        } else { \
            printf(ANSI_COLOR_RED "✗ %s: %d/%d assertions passed" ANSI_COLOR_RESET "\n", #test_func, test_passed, test_assertions); \
            printf("%s", test_failure_buffer); \
        } \
    } else { \
        if (test_func()) { \
            printf(ANSI_COLOR_GREEN "✓ %s passed" ANSI_COLOR_RESET "\n", #test_func); \
        } else { \
            printf(ANSI_COLOR_RED "✗ %s failed" ANSI_COLOR_RESET "\n", #test_func); \
        } \
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