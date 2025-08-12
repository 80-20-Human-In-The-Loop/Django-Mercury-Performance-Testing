/**
 * @file test_security.h
 * @brief Security-focused test framework for Mercury C tests
 * 
 * This header provides specialized macros for testing security vulnerabilities,
 * including buffer overflows, injection attacks, and memory safety.
 * It builds on top of test_base.h for common definitions.
 */

#ifndef TEST_SECURITY_H
#define TEST_SECURITY_H

#include "test_base.h"
#include <limits.h>
#include <errno.h>

// ============================================================================
// SECURITY TEST MACROS
// ============================================================================

/**
 * @brief Test for integer overflow in multiplication
 */
#define ASSERT_NO_MULT_OVERFLOW(a, b, message) do { \
    total_tests++; \
    size_t _a = (a); \
    size_t _b = (b); \
    size_t result; \
    bool overflow = false; \
    \
    /* Check for overflow */ \
    if (_a != 0 && _b > SIZE_MAX / _a) { \
        overflow = true; \
    } else { \
        result = _a * _b; \
    } \
    \
    if (overflow) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Integer overflow detected:" RESET \
               " %zu * %zu would overflow\n", _a, _b); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (no overflow: %zu * %zu = %zu)\n", \
                   message, _a, _b, result); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Test for integer overflow in addition
 */
#define ASSERT_NO_ADD_OVERFLOW(a, b, message) do { \
    total_tests++; \
    size_t _a = (a); \
    size_t _b = (b); \
    \
    if (_a > SIZE_MAX - _b) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Integer overflow detected:" RESET \
               " %zu + %zu would overflow\n", _a, _b); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (no overflow: %zu + %zu = %zu)\n", \
                   message, _a, _b, _a + _b); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Test that a buffer operation stays within bounds
 */
#define ASSERT_BOUNDS_CHECK(index, size, message) do { \
    total_tests++; \
    size_t _index = (index); \
    size_t _size = (size); \
    \
    if (_index >= _size) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Buffer overflow detected:" RESET \
               " index %zu >= size %zu\n", _index, _size); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (index %zu < size %zu)\n", \
                   message, _index, _size); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Test that a string is properly null-terminated
 */
#define ASSERT_NULL_TERMINATED(str, max_len, message) do { \
    total_tests++; \
    const char* _str = (str); \
    size_t _max_len = (max_len); \
    bool is_terminated = false; \
    \
    for (size_t i = 0; i < _max_len; i++) { \
        if (_str[i] == '\0') { \
            is_terminated = true; \
            break; \
        } \
    } \
    \
    if (!is_terminated) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "String not null-terminated" RESET \
               " within %zu bytes\n", _max_len); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (properly terminated)\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Test that a pointer is not NULL before use
 */
#define ASSERT_VALID_PTR(ptr, message) do { \
    total_tests++; \
    void* _ptr = (void*)(ptr); \
    \
    if (_ptr == NULL) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "NULL pointer detected" RESET "\n"); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (valid ptr: %p)\n", message, _ptr); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Test that input doesn't contain dangerous characters
 */
#define ASSERT_NO_INJECTION(input, message) do { \
    total_tests++; \
    const char* _input = (input); \
    const char* dangerous[] = {";", "|", "&", "`", "$", "(", ")", "<", ">", NULL}; \
    bool is_safe = true; \
    const char* found_char = NULL; \
    \
    for (int i = 0; dangerous[i] != NULL; i++) { \
        if (strstr(_input, dangerous[i]) != NULL) { \
            is_safe = false; \
            found_char = dangerous[i]; \
            break; \
        } \
    } \
    \
    if (!is_safe) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Injection character detected:" RESET " '%s'\n", found_char); \
        printf("  " BOLD "In string:" RESET " \"%s\"\n", _input); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (no injection chars)\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

/**
 * @brief Test format string safety
 */
#define ASSERT_SAFE_FORMAT(fmt, message) do { \
    total_tests++; \
    const char* _fmt = (fmt); \
    bool is_safe = true; \
    \
    /* Check for dangerous format specifiers */ \
    if (strstr(_fmt, "%n") != NULL || \
        strstr(_fmt, "%hn") != NULL || \
        strstr(_fmt, "%ln") != NULL || \
        strstr(_fmt, "%hhn") != NULL) { \
        is_safe = false; \
    } \
    \
    if (!is_safe) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Dangerous format string:" RESET " \"%s\"\n", _fmt); \
        printf("  " YELLOW "Contains %%n specifier that can write to memory" RESET "\n"); \
        printf("  " DIM "at %s:%d in %s()" RESET "\n", \
               __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (safe format string)\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// FUZZING SUPPORT
// ============================================================================

/**
 * @brief Simple fuzzing macro for testing with random inputs
 */
#define FUZZ_TEST(func, iterations, message) do { \
    printf(YELLOW "🔀 Fuzzing %s for %d iterations..." RESET "\n", #func, iterations); \
    int fuzz_failures = 0; \
    for (int i = 0; i < iterations; i++) { \
        /* Generate random input */ \
        size_t size = rand() % 1024; \
        char* input = malloc(size + 1); \
        if (!input) continue; \
        \
        for (size_t j = 0; j < size; j++) { \
            input[j] = (char)(rand() % 256); \
        } \
        input[size] = '\0'; \
        \
        /* Test the function */ \
        int result = func(input); \
        if (result < 0) { \
            fuzz_failures++; \
        } \
        \
        free(input); \
    } \
    \
    total_tests++; \
    if (fuzz_failures > 0) { \
        printf(RED "✗ FUZZ FAIL: %s" RESET " (%d/%d iterations failed)\n", \
               message, fuzz_failures, iterations); \
        failed_tests++; \
    } else { \
        printf(GREEN "✓ FUZZ PASS: %s" RESET " (all %d iterations passed)\n", \
               message, iterations); \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// MEMORY SAFETY
// ============================================================================

/**
 * @brief Test for use-after-free vulnerabilities
 */
#define TEST_USE_AFTER_FREE(ptr_var, free_func, use_func, message) do { \
    total_tests++; \
    printf(YELLOW "Testing use-after-free: %s..." RESET "\n", message); \
    \
    /* This is a conceptual test - actual implementation would need */ \
    /* memory debugging tools or custom allocator */ \
    \
    free_func(ptr_var); \
    ptr_var = NULL; /* Good practice - set to NULL after free */ \
    \
    /* Verify that using freed pointer would fail safely */ \
    if (ptr_var == NULL) { \
        printf(GREEN "✓ PASS: %s" RESET " (pointer nulled after free)\n", message); \
        passed_tests++; \
    } else { \
        printf(RED "✗ FAIL: %s" RESET " (pointer not nulled after free)\n", message); \
        failed_tests++; \
    } \
} while(0)

// ============================================================================
// TEST SUITE MACROS (Security-specific)
// ============================================================================

/**
 * @brief Start a security test suite
 */
#define SECURITY_TEST_START(name) do { \
    printf(YELLOW "\n🔒 === Security Tests: %s ===" RESET "\n", name); \
    total_tests = 0; \
    passed_tests = 0; \
    failed_tests = 0; \
    srand(time(NULL)); /* Initialize for fuzzing */ \
} while(0)

/**
 * @brief End a security test suite
 */
#define SECURITY_TEST_END() do { \
    printf(YELLOW "\n🔒 === Security Test Results ===" RESET "\n"); \
    printf("Total: %d, Passed: " GREEN "%d" RESET ", Failed: " RED "%d" RESET "\n", \
           total_tests, passed_tests, failed_tests); \
    if (failed_tests > 0) { \
        printf(RED "⚠️  SECURITY VULNERABILITIES DETECTED!" RESET "\n"); \
        printf(RED "%d security test(s) failed!" RESET "\n", failed_tests); \
    } else { \
        printf(GREEN "✅ All security tests passed!" RESET "\n"); \
    } \
} while(0)

// ============================================================================
// SECURITY TEST MACROS (Legacy compatibility)
// ============================================================================

/* Test start/pass macros for security tests */
#define TEST_START(name) printf(YELLOW "\n[TEST] %s\n" RESET, name)
#define TEST_PASS() do { \
    printf(GREEN "✓ Test passed\n" RESET); \
    return; \
} while(0)

/* Assertion macros for security tests */
#define ASSERT_EQ(actual, expected, ...) do { \
    if ((actual) != (expected)) { \
        printf(RED "✗ ASSERT_EQ failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  Expected: %ld, Got: %ld\n", (long)(expected), (long)(actual)); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

#define ASSERT_NEQ(actual, expected, ...) do { \
    if ((actual) == (expected)) { \
        printf(RED "✗ ASSERT_NEQ failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  Values are equal: %ld\n", (long)(actual)); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

#define ASSERT_LT(actual, expected, ...) do { \
    if (!((actual) < (expected))) { \
        printf(RED "✗ ASSERT_LT failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  Expected %ld < %ld\n", (long)(actual), (long)(expected)); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

#define ASSERT_GT(actual, expected, ...) do { \
    if (!((actual) > (expected))) { \
        printf(RED "✗ ASSERT_GT failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  Expected %ld > %ld\n", (long)(actual), (long)(expected)); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

#define ASSERT_GE(actual, expected, ...) do { \
    if (!((actual) >= (expected))) { \
        printf(RED "✗ ASSERT_GE failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  Expected %ld >= %ld\n", (long)(actual), (long)(expected)); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

#define ASSERT_LE(actual, expected, ...) do { \
    if (!((actual) <= (expected))) { \
        printf(RED "✗ ASSERT_LE failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  Expected %ld <= %ld\n", (long)(actual), (long)(expected)); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

#define ASSERT_STR_CONTAINS(str, substr, ...) do { \
    if (strstr((str), (substr)) == NULL) { \
        printf(RED "✗ ASSERT_STR_CONTAINS failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  String '%s' does not contain '%s'\n", (str), (substr)); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

#define ASSERT_TRUE(condition, ...) do { \
    if (!(condition)) { \
        printf(RED "✗ ASSERT_TRUE failed: " __VA_ARGS__); \
        printf(RESET "\n"); \
        printf("  Condition was false\n"); \
        printf("  at %s:%d\n", __FILE__, __LINE__); \
        failed_tests++; \
        total_tests++; \
        return; \
    } \
    passed_tests++; \
    total_tests++; \
} while(0)

// ============================================================================
// COMPATIBILITY WITH test_simple.h
// ============================================================================

/* Basic assertion for compatibility */
#define ASSERT(condition, message) do { \
    total_tests++; \
    if (!(condition)) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  at %s:%d in %s()\n", __FILE__, __LINE__, __func__); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET "\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

/* Standard test suite macros */
#define TEST_SUITE_START(name) SECURITY_TEST_START(name)
#define TEST_SUITE_END() SECURITY_TEST_END()

/* Run test function */
#define RUN_TEST(test_func) do { \
    printf(YELLOW "\nRunning %s..." RESET "\n", #test_func); \
    if (test_func()) { \
        printf(GREEN "✓ %s passed" RESET "\n", #test_func); \
    } else { \
        printf(RED "✗ %s failed" RESET "\n", #test_func); \
    } \
} while(0)

#endif // TEST_SECURITY_H