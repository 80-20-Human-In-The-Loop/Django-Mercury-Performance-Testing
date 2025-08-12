/**
 * @file enhanced_tests.h
 * @brief Enhanced test framework with educational debugging features
 * 
 * This framework provides comprehensive test macros with detailed failure
 * messages, value printing, and educational explanations to help developers
 * understand and fix test failures quickly.
 */

#ifndef ENHANCED_TESTS_H
#define ENHANCED_TESTS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>

// ANSI color codes for test output
#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_MAGENTA "\x1b[35m"
#define ANSI_COLOR_CYAN    "\x1b[36m"
#define ANSI_COLOR_DIM     "\x1b[2m"
#define ANSI_COLOR_RESET   "\x1b[0m"
#define ANSI_BOLD          "\x1b[1m"

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

// Debug mode flag (can be set via environment variable)
static int debug_mode = 0;

// Test context for better error messages
typedef struct {
    const char* test_name;
    const char* test_file;
    int test_line;
    char context_message[512];
} TestContext;

static TestContext current_test_context = {0};

// Initialize debug mode from environment
#define INIT_TEST_FRAMEWORK() do { \
    const char* debug_env = getenv("TEST_DEBUG"); \
    debug_mode = (debug_env && strcmp(debug_env, "1") == 0); \
    if (debug_mode) { \
        printf(ANSI_COLOR_CYAN "🔍 Debug mode enabled" ANSI_COLOR_RESET "\n"); \
    } \
    const char* verbose = getenv("TEST_VERBOSE"); \
    quiet_mode = (verbose == NULL || strcmp(verbose, "0") == 0); \
} while(0)

// Initialize quiet mode test function
#define TEST_FUNCTION_START() do { \
    test_assertions = 0; \
    test_passed = 0; \
    test_failed = 0; \
    test_failure_buffer_used = 0; \
    test_failure_buffer[0] = '\0'; \
} while(0)

// Set test context for better error messages
#define SET_TEST_CONTEXT(name, ...) do { \
    current_test_context.test_name = name; \
    current_test_context.test_file = __FILE__; \
    current_test_context.test_line = __LINE__; \
    snprintf(current_test_context.context_message, sizeof(current_test_context.context_message), \
             ##__VA_ARGS__); \
} while(0)

// Debug print macro (only prints in debug mode)
#define DEBUG_PRINT(fmt, ...) do { \
    if (debug_mode) { \
        printf(ANSI_COLOR_DIM "  [DEBUG] " fmt ANSI_COLOR_RESET "\n", ##__VA_ARGS__); \
    } \
} while(0)

// Educational explanation for failures
#define EXPLAIN_FAILURE(explanation) do { \
    printf(ANSI_COLOR_YELLOW "  💡 Explanation: " ANSI_COLOR_RESET "%s\n", explanation); \
} while(0)

// Enhanced assertion with value printing for integers
#define ASSERT_EQ_INT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (_actual != _expected) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " %d (0x%x)\n", _expected, _expected); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " %d (0x%x)\n", _actual, _actual); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        if (strlen(current_test_context.context_message) > 0) { \
            printf("  " ANSI_COLOR_BLUE "Context: %s" ANSI_COLOR_RESET "\n", \
                   current_test_context.context_message); \
        } \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET, message); \
        if (debug_mode) { \
            printf(" (value: %d)", _actual); \
        } \
        printf("\n"); \
        passed_tests++; \
    } \
} while(0)

// Enhanced assertion for unsigned integers
#define ASSERT_EQ_UINT(actual, expected, message) do { \
    total_tests++; \
    unsigned int _actual = (actual); \
    unsigned int _expected = (expected); \
    if (_actual != _expected) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " %u (0x%x)\n", _expected, _expected); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " %u (0x%x)\n", _actual, _actual); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET "\n", message); \
        passed_tests++; \
    } \
} while(0)

// Enhanced assertion for pointers
#define ASSERT_NOT_NULL(ptr, message) do { \
    total_tests++; \
    void* _ptr = (void*)(ptr); \
    if (_ptr == NULL) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " non-NULL pointer\n"); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " NULL\n"); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET, message); \
        if (debug_mode) { \
            printf(" (ptr: %p)", _ptr); \
        } \
        printf("\n"); \
        passed_tests++; \
    } \
} while(0)

// String comparison assertion
#define ASSERT_STR_EQ(actual, expected, message) do { \
    total_tests++; \
    const char* _actual = (actual); \
    const char* _expected = (expected); \
    if (_actual == NULL || _expected == NULL || strcmp(_actual, _expected) != 0) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " \"%s\"\n", \
               _expected ? _expected : "(NULL)"); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " \"%s\"\n", \
               _actual ? _actual : "(NULL)"); \
        if (_actual && _expected) { \
            /* Show first difference */ \
            size_t i = 0; \
            while (_actual[i] && _expected[i] && _actual[i] == _expected[i]) i++; \
            printf("  " ANSI_COLOR_YELLOW "First diff at position %zu" ANSI_COLOR_RESET "\n", i); \
        } \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET "\n", message); \
        passed_tests++; \
    } \
} while(0)

// String contains assertion
#define ASSERT_STR_CONTAINS(haystack, needle, message) do { \
    total_tests++; \
    const char* _haystack = (haystack); \
    const char* _needle = (needle); \
    if (_haystack == NULL || _needle == NULL || strstr(_haystack, _needle) == NULL) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Looking for:" ANSI_COLOR_RESET " \"%s\"\n", \
               _needle ? _needle : "(NULL)"); \
        printf("  " ANSI_BOLD "In string:  " ANSI_COLOR_RESET " \"%s\"\n", \
               _haystack ? (_haystack[0] ? _haystack : "(empty)") : "(NULL)"); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET "\n", message); \
        passed_tests++; \
    } \
} while(0)

// Comparison assertions
#define ASSERT_GT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual > _expected)) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " > %d\n", _expected); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " %d\n", _actual); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET " (%d > %d)\n", \
               message, _actual, _expected); \
        passed_tests++; \
    } \
} while(0)

#define ASSERT_GE(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual >= _expected)) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " >= %d\n", _expected); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " %d\n", _actual); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET " (%d >= %d)\n", \
               message, _actual, _expected); \
        passed_tests++; \
    } \
} while(0)

#define ASSERT_LT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual < _expected)) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " < %d\n", _expected); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " %d\n", _actual); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET " (%d < %d)\n", \
               message, _actual, _expected); \
        passed_tests++; \
    } \
} while(0)

#define ASSERT_LE(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual <= _expected)) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " <= %d\n", _expected); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " %d\n", _actual); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET " (%d <= %d)\n", \
               message, _actual, _expected); \
        passed_tests++; \
    } \
} while(0)

// Boolean assertion with clear true/false display
#define ASSERT_TRUE(condition, message) do { \
    if (quiet_mode) { \
        test_assertions++; \
        total_tests++; \
        bool _result = (bool)(condition); \
        if (!_result) { \
            test_failed++; \
            failed_tests++; \
            if (test_failure_buffer_used < (int)(sizeof(test_failure_buffer) - 256)) { \
                test_failure_buffer_used += snprintf(test_failure_buffer + test_failure_buffer_used, \
                    sizeof(test_failure_buffer) - test_failure_buffer_used, \
                    "  " ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n" \
                    "    Expected: true, Got: false\n" \
                    "    Expression: %s\n" \
                    "    at %s:%d in %s()\n", \
                    message, #condition, __FILE__, __LINE__, __func__); \
            } \
            return 0; \
        } else { \
            test_passed++; \
            passed_tests++; \
        } \
    } else { \
        total_tests++; \
        bool _result = (bool)(condition); \
        if (!_result) { \
            printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
            printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " true\n"); \
            printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " false\n"); \
            printf("  " ANSI_BOLD "Expression:" ANSI_COLOR_RESET " %s\n", #condition); \
            printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
                   __FILE__, __LINE__, __func__); \
            failed_tests++; \
            return 0; \
        } else { \
            printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET "\n", message); \
            passed_tests++; \
        } \
    } \
} while(0)

#define ASSERT_FALSE(condition, message) do { \
    total_tests++; \
    bool _result = (bool)(condition); \
    if (_result) { \
        printf(ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " false\n"); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " true\n"); \
        printf("  " ANSI_BOLD "Expression:" ANSI_COLOR_RESET " %s\n", #condition); \
        printf("  " ANSI_COLOR_DIM "at %s:%d in %s()" ANSI_COLOR_RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET "\n", message); \
        passed_tests++; \
    } \
} while(0)

// Quiet assertion macro - only shows failures
#define ASSERT_QUIET(condition, message) do { \
    test_assertions++; \
    total_tests++; \
    if (!(condition)) { \
        test_failed++; \
        failed_tests++; \
        if (test_failure_buffer_used < sizeof(test_failure_buffer) - 512) { \
            test_failure_buffer_used += snprintf(test_failure_buffer + test_failure_buffer_used, \
                sizeof(test_failure_buffer) - test_failure_buffer_used, \
                "  " ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n    Expression: %s\n    at %s:%d in %s()\n", \
                message, #condition, __FILE__, __LINE__, __func__); \
        } \
    } else { \
        test_passed++; \
        passed_tests++; \
    } \
} while(0)

// Enhanced quiet assertion for integers
#define ASSERT_EQ_INT_QUIET(actual, expected, message) do { \
    test_assertions++; \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (_actual != _expected) { \
        test_failed++; \
        failed_tests++; \
        if (test_failure_buffer_used < sizeof(test_failure_buffer) - 512) { \
            test_failure_buffer_used += snprintf(test_failure_buffer + test_failure_buffer_used, \
                sizeof(test_failure_buffer) - test_failure_buffer_used, \
                "  " ANSI_COLOR_RED "✗ FAIL: %s" ANSI_COLOR_RESET "\n    Expected: %d, Got: %d\n    at %s:%d in %s()\n", \
                message, _expected, _actual, __FILE__, __LINE__, __func__); \
        } \
    } else { \
        test_passed++; \
        passed_tests++; \
    } \
} while(0)

// Backward compatibility with simple_tests.h
#define ASSERT(condition, message) ASSERT_TRUE(condition, message)

// EXPECT variants that don't stop test execution
#define EXPECT_EQ_INT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (_actual != _expected) { \
        printf(ANSI_COLOR_YELLOW "⚠ EXPECT FAIL: %s" ANSI_COLOR_RESET "\n", message); \
        printf("  " ANSI_BOLD "Expected:" ANSI_COLOR_RESET " %d\n", _expected); \
        printf("  " ANSI_BOLD "Got:     " ANSI_COLOR_RESET " %d\n", _actual); \
        printf("  " ANSI_COLOR_DIM "at %s:%d" ANSI_COLOR_RESET "\n", __FILE__, __LINE__); \
        failed_tests++; \
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
    INIT_TEST_FRAMEWORK(); \
} while(0)

#define RUN_TEST(test_func) do { \
    printf(ANSI_COLOR_YELLOW "\nRunning %s..." ANSI_COLOR_RESET "\n", #test_func); \
    memset(&current_test_context, 0, sizeof(current_test_context)); \
    current_test_context.test_name = #test_func; \
    if (quiet_mode) { \
        TEST_FUNCTION_START(); \
        int result = test_func(); \
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

// Time measurement utilities
typedef struct {
    struct timespec start;
    struct timespec end;
} TestTimer;

static inline void test_timer_start(TestTimer* timer) {
    clock_gettime(CLOCK_MONOTONIC, &timer->start);
}

static inline double test_timer_end(TestTimer* timer) {
    clock_gettime(CLOCK_MONOTONIC, &timer->end);
    return (timer->end.tv_sec - timer->start.tv_sec) * 1000.0 +
           (timer->end.tv_nsec - timer->start.tv_nsec) / 1000000.0;
}

#define TIME_TEST(code, description) do { \
    TestTimer _timer; \
    test_timer_start(&_timer); \
    code; \
    double _elapsed = test_timer_end(&_timer); \
    printf(ANSI_COLOR_MAGENTA "  ⏱ %s took %.2f ms" ANSI_COLOR_RESET "\n", \
           description, _elapsed); \
} while(0)

#endif // ENHANCED_TESTS_H