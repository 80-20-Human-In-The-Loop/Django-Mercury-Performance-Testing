/**
 * @file test_simple.h
 * @brief Simple test framework for Mercury C tests
 * 
 * This header provides basic assertion and test macros for simple pass/fail testing.
 * It builds on top of test_base.h for common definitions.
 */

#ifndef TEST_SIMPLE_H
#define TEST_SIMPLE_H

#include "test_base.h"

// ============================================================================
// SIMPLE ASSERTION MACROS
// ============================================================================

/**
 * @brief Basic assertion macro
 * 
 * Tests a condition and reports pass/fail.
 * In quiet mode, only failures are shown.
 * In verbose mode, all assertions are shown.
 */
#define ASSERT(condition, message) do { \
    if (quiet_mode) { \
        /* Quiet mode - collect failures in buffer */ \
        test_assertions++; \
        total_tests++; \
        if (!(condition)) { \
            test_failed++; \
            failed_tests++; \
            if (test_failure_buffer_used < (int)(sizeof(test_failure_buffer) - 256)) { \
                test_failure_buffer_used += snprintf( \
                    test_failure_buffer + test_failure_buffer_used, \
                    sizeof(test_failure_buffer) - test_failure_buffer_used, \
                    "  " RED "✗ FAIL: %s" RESET "\n" \
                    "    at %s:%d in %s()\n", \
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
            printf(RED "✗ FAIL: %s" RESET "\n", message); \
            printf("  at %s:%d in %s()\n", __FILE__, __LINE__, __func__); \
            failed_tests++; \
            return 0; \
        } else { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
            passed_tests++; \
        } \
    } \
} while(0)

/**
 * @brief Quiet assertion macro (always quiet regardless of mode)
 */
#define ASSERT_QUIET(condition, message) do { \
    test_assertions++; \
    total_tests++; \
    if (!(condition)) { \
        test_failed++; \
        failed_tests++; \
        if (test_failure_buffer_used < sizeof(test_failure_buffer) - 256) { \
            test_failure_buffer_used += snprintf( \
                test_failure_buffer + test_failure_buffer_used, \
                sizeof(test_failure_buffer) - test_failure_buffer_used, \
                "  " RED "✗ FAIL: %s" RESET "\n" \
                "    at %s:%d in %s()\n", \
                message, __FILE__, __LINE__, __func__); \
        } \
    } else { \
        test_passed++; \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// TEST SUITE MACROS
// ============================================================================

/**
 * @brief Start a test suite
 */
#define TEST_SUITE_START(name) do { \
    printf(CYAN "\n=== %s ===" RESET "\n", name); \
    total_tests = 0; \
    passed_tests = 0; \
    failed_tests = 0; \
} while(0)

/**
 * @brief End a test suite and print results
 */
#define TEST_SUITE_END() do { \
    printf(CYAN "\n=== Results ===" RESET "\n"); \
    printf("Total: %d, Passed: " GREEN "%d" RESET ", Failed: " RED "%d" RESET "\n", \
           total_tests, passed_tests, failed_tests); \
    if (failed_tests > 0) { \
        printf(RED "%d test(s) failed!" RESET "\n", failed_tests); \
    } else { \
        printf(GREEN "All tests passed!" RESET "\n"); \
    } \
} while(0)

// ============================================================================
// TEST FUNCTION MACROS
// ============================================================================

/**
 * @brief Run a test function
 * 
 * Executes a test function and reports results.
 * In quiet mode, shows only failures.
 * In verbose mode, shows all results.
 */
#define RUN_TEST(test_func) do { \
    printf(YELLOW "\nRunning %s..." RESET "\n", #test_func); \
    if (quiet_mode) { \
        INIT_TEST_FUNCTION(); \
        int result = test_func(); \
        (void)result; /* Suppress unused variable warning */ \
        if (test_failed == 0) { \
            printf(GREEN "✓ %s: %d assertions passed" RESET "\n", \
                   #test_func, test_passed); \
        } else { \
            printf(RED "✗ %s: %d/%d assertions passed" RESET "\n", \
                   #test_func, test_passed, test_assertions); \
            printf("%s", test_failure_buffer); \
        } \
    } else { \
        if (test_func()) { \
            printf(GREEN "✓ %s passed" RESET "\n", #test_func); \
        } else { \
            printf(RED "✗ %s failed" RESET "\n", #test_func); \
        } \
    } \
} while(0)

// ============================================================================
// INITIALIZATION MACROS
// ============================================================================

/**
 * @brief Initialize quiet mode based on environment
 */
#define QUIET_MODE_INIT() do { \
    const char* verbose = getenv("TEST_VERBOSE"); \
    /* Default to quiet mode (1) unless TEST_VERBOSE is explicitly set to "1" */ \
    quiet_mode = (verbose == NULL || strcmp(verbose, "1") != 0); \
} while(0)

/**
 * @brief Initialize test function (alias for base macro)
 */
#define TEST_FUNCTION_START() INIT_TEST_FUNCTION()

// ============================================================================
// BACKWARD COMPATIBILITY
// ============================================================================

// Keep the old header name working for existing code
#ifdef SIMPLE_TESTS_H
#warning "Please use test_simple.h instead of simple_tests.h"
#endif

#endif // TEST_SIMPLE_H