/**
 * @file test_framework.h
 * @brief Common test framework for Mercury C tests
 */

#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>

// Test statistics (global)
extern int total_tests;
extern int passed_tests;
extern int failed_tests;

// Color codes
#define RED "\033[31m"
#define GREEN "\033[32m"
#define YELLOW "\033[33m"
#define CYAN "\033[36m"
#define RESET "\033[0m"

// Test suite macros
#define TEST_SUITE_START(name) do { \
    printf("\n" CYAN "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" RESET "\n"); \
    printf(CYAN "  %s" RESET "\n", name); \
    printf(CYAN "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" RESET "\n"); \
} while(0)

#define TEST_SUITE_END() do { \
    printf(CYAN "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" RESET "\n"); \
} while(0)

// Test case macros
#define TEST_START(name) do { \
    printf("  Testing: %s... ", name); \
    fflush(stdout); \
    total_tests++; \
} while(0)

#define TEST_PASS() do { \
    printf(GREEN "✓ PASSED" RESET "\n"); \
    passed_tests++; \
} while(0)

#define TEST_FAIL(msg, ...) do { \
    printf(RED "✗ FAILED" RESET "\n"); \
    printf("    " RED "Error: " msg RESET "\n", ##__VA_ARGS__); \
    failed_tests++; \
    return; \
} while(0)

// Assertion macros
#define ASSERT_TRUE(condition, msg, ...) do { \
    if (!(condition)) { \
        TEST_FAIL(msg, ##__VA_ARGS__); \
    } \
} while(0)

#define ASSERT_FALSE(condition, msg, ...) do { \
    if (condition) { \
        TEST_FAIL(msg, ##__VA_ARGS__); \
    } \
} while(0)

#define ASSERT_EQ(actual, expected, msg, ...) do { \
    if ((actual) != (expected)) { \
        printf(RED "✗ FAILED" RESET "\n"); \
        printf("    Expected: %ld, Got: %ld\n", (long)(expected), (long)(actual)); \
        printf("    " RED "Error: " msg RESET "\n", ##__VA_ARGS__); \
        failed_tests++; \
        return; \
    } \
} while(0)

#define ASSERT_NEQ(actual, expected, msg, ...) do { \
    if ((actual) == (expected)) { \
        TEST_FAIL(msg, ##__VA_ARGS__); \
    } \
} while(0)

#define ASSERT_GT(actual, expected, msg, ...) do { \
    if ((actual) <= (expected)) { \
        TEST_FAIL(msg, ##__VA_ARGS__); \
    } \
} while(0)

#define ASSERT_LT(actual, expected, msg, ...) do { \
    if ((actual) >= (expected)) { \
        TEST_FAIL(msg, ##__VA_ARGS__); \
    } \
} while(0)

#define ASSERT_GE(actual, expected, msg, ...) do { \
    if ((actual) < (expected)) { \
        TEST_FAIL(msg, ##__VA_ARGS__); \
    } \
} while(0)

#define ASSERT_LE(actual, expected, msg, ...) do { \
    if ((actual) > (expected)) { \
        TEST_FAIL(msg, ##__VA_ARGS__); \
    } \
} while(0)

#define ASSERT_STR_EQ(actual, expected, msg, ...) do { \
    if (strcmp((actual), (expected)) != 0) { \
        printf(RED "✗ FAILED" RESET "\n"); \
        printf("    Expected: '%s', Got: '%s'\n", (expected), (actual)); \
        printf("    " RED "Error: " msg RESET "\n", ##__VA_ARGS__); \
        failed_tests++; \
        return; \
    } \
} while(0)

#define ASSERT_STR_CONTAINS(haystack, needle, msg, ...) do { \
    if (strstr((haystack), (needle)) == NULL) { \
        printf(RED "✗ FAILED" RESET "\n"); \
        printf("    String '%s' does not contain '%s'\n", (haystack), (needle)); \
        printf("    " RED "Error: " msg RESET "\n", ##__VA_ARGS__); \
        failed_tests++; \
        return; \
    } \
} while(0)

#define ASSERT_FLOAT_EQ(actual, expected, tolerance, msg, ...) do { \
    if (fabs((actual) - (expected)) > (tolerance)) { \
        printf(RED "✗ FAILED" RESET "\n"); \
        printf("    Expected: %f, Got: %f (tolerance: %f)\n", \
               (expected), (actual), (tolerance)); \
        printf("    " RED "Error: " msg RESET "\n", ##__VA_ARGS__); \
        failed_tests++; \
        return; \
    } \
} while(0)

#endif // TEST_FRAMEWORK_H