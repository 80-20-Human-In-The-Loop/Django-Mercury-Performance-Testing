/**
 * @file test_enhanced.h
 * @brief Enhanced test framework with detailed debugging features
 * 
 * This header provides rich assertion macros with value printing,
 * educational explanations, and detailed failure messages.
 * It builds on top of test_base.h for common definitions.
 */

#ifndef TEST_ENHANCED_H
#define TEST_ENHANCED_H

#include "test_base.h"

// ============================================================================
// ENHANCED TEST CONTEXT
// ============================================================================

// TestContext is already defined in test_base.h
// Just define the instance macro

/**
 * @brief Global test context variable
 * @note This must be defined in your test file if using enhanced context features
 */
#define DEFINE_TEST_CONTEXT() TestContext current_test_context = {0}

// ============================================================================
// ENHANCED CONTEXT MACROS
// ============================================================================

/**
 * @brief Set test context for better error messages
 */
#define SET_TEST_CONTEXT(name, ...) do { \
    current_test_context.test_name = name; \
    current_test_context.test_file = __FILE__; \
    current_test_context.test_line = __LINE__; \
    snprintf(current_test_context.context_message, \
             sizeof(current_test_context.context_message), \
             ##__VA_ARGS__); \
} while(0)

/**
 * @brief Debug print macro (only prints in debug mode)
 */
#define DEBUG_PRINT(fmt, ...) do { \
    if (is_debug_mode()) { \
        printf(DIM "  [DEBUG] " fmt RESET "\n", ##__VA_ARGS__); \
    } \
} while(0)

/**
 * @brief Educational explanation for failures
 */
#define EXPLAIN_FAILURE(explanation) do { \
    if (is_explain_mode()) { \
        printf(YELLOW "  💡 Explanation: " RESET "%s\n", explanation); \
    } \
} while(0)

// ============================================================================
// ENHANCED ASSERTION MACROS - INTEGERS
// ============================================================================

/**
 * @brief Enhanced assertion for integer equality
 */
#define ASSERT_EQ_INT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (_actual != _expected) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " %d (0x%x)\n", _expected, _expected); \
        printf("  " BOLD "Got:     " RESET " %d (0x%x)\n", _actual, _actual); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        if (strlen(current_test_context.context_message) > 0) { \
            printf("  " BLUE "Context: %s" RESET "\n", \
                   current_test_context.context_message); \
        } \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET, message); \
            if (is_debug_mode()) { \
                printf(" (value: %d)", _actual); \
            } \
            printf("\n"); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Enhanced assertion for unsigned integer equality
 */
#define ASSERT_EQ_UINT(actual, expected, message) do { \
    total_tests++; \
    unsigned int _actual = (actual); \
    unsigned int _expected = (expected); \
    if (_actual != _expected) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " %u (0x%x)\n", _expected, _expected); \
        printf("  " BOLD "Got:     " RESET " %u (0x%x)\n", _actual, _actual); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// ENHANCED ASSERTION MACROS - POINTERS
// ============================================================================

/**
 * @brief Enhanced assertion for non-null pointers
 */
#define ASSERT_NOT_NULL(ptr, message) do { \
    total_tests++; \
    void* _ptr = (void*)(ptr); \
    if (_ptr == NULL) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " non-NULL pointer\n"); \
        printf("  " BOLD "Got:     " RESET " NULL\n"); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET, message); \
            if (is_debug_mode()) { \
                printf(" (ptr: %p)", _ptr); \
            } \
            printf("\n"); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Enhanced assertion for null pointers
 */
#define ASSERT_NULL(ptr, message) do { \
    total_tests++; \
    void* _ptr = (void*)(ptr); \
    if (_ptr != NULL) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " NULL\n"); \
        printf("  " BOLD "Got:     " RESET " %p\n", _ptr); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// ENHANCED ASSERTION MACROS - STRINGS
// ============================================================================

/**
 * @brief String equality assertion with diff display
 */
#define ASSERT_STR_EQ(actual, expected, message) do { \
    total_tests++; \
    const char* _actual = (actual); \
    const char* _expected = (expected); \
    if (_actual == NULL || _expected == NULL || strcmp(_actual, _expected) != 0) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " \"%s\"\n", \
               _expected ? _expected : "(NULL)"); \
        printf("  " BOLD "Got:     " RESET " \"%s\"\n", \
               _actual ? _actual : "(NULL)"); \
        if (_actual && _expected) { \
            /* Show first difference */ \
            size_t i = 0; \
            while (_actual[i] && _expected[i] && _actual[i] == _expected[i]) i++; \
            printf("  " YELLOW "First diff at position %zu" RESET "\n", i); \
        } \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief String contains assertion
 */
#define ASSERT_STR_CONTAINS(haystack, needle, message) do { \
    total_tests++; \
    const char* _haystack = (haystack); \
    const char* _needle = (needle); \
    if (_haystack == NULL || _needle == NULL || strstr(_haystack, _needle) == NULL) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Looking for:" RESET " \"%s\"\n", \
               _needle ? _needle : "(NULL)"); \
        printf("  " BOLD "In string:  " RESET " \"%s\"\n", \
               _haystack ? (_haystack[0] ? _haystack : "(empty)") : "(NULL)"); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// ENHANCED ASSERTION MACROS - COMPARISONS
// ============================================================================

/**
 * @brief Greater than assertion
 */
#define ASSERT_GT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual > _expected)) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " > %d\n", _expected); \
        printf("  " BOLD "Got:     " RESET " %d\n", _actual); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (%d > %d)\n", \
                   message, _actual, _expected); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Greater than or equal assertion
 */
#define ASSERT_GE(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual >= _expected)) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " >= %d\n", _expected); \
        printf("  " BOLD "Got:     " RESET " %d\n", _actual); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (%d >= %d)\n", \
                   message, _actual, _expected); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Less than assertion
 */
#define ASSERT_LT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual < _expected)) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " < %d\n", _expected); \
        printf("  " BOLD "Got:     " RESET " %d\n", _actual); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (%d < %d)\n", \
                   message, _actual, _expected); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Less than or equal assertion
 */
#define ASSERT_LE(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual <= _expected)) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " <= %d\n", _expected); \
        printf("  " BOLD "Got:     " RESET " %d\n", _actual); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (%d <= %d)\n", \
                   message, _actual, _expected); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// ENHANCED ASSERTION MACROS - BOOLEAN
// ============================================================================

/**
 * @brief Boolean true assertion
 */
#define ASSERT_TRUE(condition, message) do { \
    total_tests++; \
    bool _result = (bool)(condition); \
    if (!_result) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " true\n"); \
        printf("  " BOLD "Got:     " RESET " false\n"); \
        printf("  " BOLD "Expression:" RESET " %s\n", #condition); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Boolean false assertion
 */
#define ASSERT_FALSE(condition, message) do { \
    total_tests++; \
    bool _result = (bool)(condition); \
    if (_result) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " false\n"); \
        printf("  " BOLD "Got:     " RESET " true\n"); \
        printf("  " BOLD "Expression:" RESET " %s\n", #condition); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// EXPECT VARIANTS (NON-FATAL)
// ============================================================================

/**
 * @brief EXPECT variant - doesn't stop test execution
 */
#define EXPECT_EQ_INT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (_actual != _expected) { \
        printf(YELLOW "⚠ EXPECT FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " %d\n", _expected); \
        printf("  " BOLD "Got:     " RESET " %d\n", _actual); \
        printf("  " DIM "at %s:%d" RESET "\n", __FILE__, __LINE__); \
        failed_tests++; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// TIMING MACROS
// ============================================================================

/**
 * @brief Time a code block
 */
#define TIME_TEST(code, description) do { \
    TestTimer _timer; \
    test_timer_start(&_timer); \
    code; \
    double _elapsed = test_timer_end(&_timer); \
    printf(MAGENTA "  ⏱ %s took %.2f ms" RESET "\n", \
           description, _elapsed); \
} while(0)

// ============================================================================
// BACKWARD COMPATIBILITY
// ============================================================================

/**
 * @brief Basic ASSERT for compatibility with test_simple.h
 */
#define ASSERT(condition, message) ASSERT_TRUE(condition, message)

/**
 * @brief Quiet assertion for compatibility
 */
#define ASSERT_QUIET(condition, message) do { \
    test_assertions++; \
    total_tests++; \
    if (!(condition)) { \
        test_failed++; \
        failed_tests++; \
        if (test_failure_buffer_used < sizeof(test_failure_buffer) - 512) { \
            test_failure_buffer_used += snprintf( \
                test_failure_buffer + test_failure_buffer_used, \
                sizeof(test_failure_buffer) - test_failure_buffer_used, \
                "  " RED "✗ FAIL: %s" RESET "\n" \
                "    Expression: %s\n" \
                "    at %s:%d in %s()\n", \
                message, #condition, __FILE__, __LINE__, __func__); \
        } \
    } else { \
        test_passed++; \
        passed_tests++; \
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
    quiet_mode = (verbose == NULL || strcmp(verbose, "1") != 0); \
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
    INIT_TEST_BASE(); \
} while(0)

/**
 * @brief End a test suite
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

/**
 * @brief Run a test function
 */
#define RUN_TEST(test_func) do { \
    printf(YELLOW "\nRunning %s..." RESET "\n", #test_func); \
    memset(&current_test_context, 0, sizeof(current_test_context)); \
    current_test_context.test_name = #test_func; \
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

#endif // TEST_ENHANCED_H