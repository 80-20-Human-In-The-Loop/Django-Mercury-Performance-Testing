/**
 * @file test_base.h
 * @brief Base definitions for Mercury C test framework
 * 
 * This header contains common definitions used by all test frameworks.
 * It should be included by test_simple.h, test_enhanced.h, test_security.h, etc.
 * 
 * DO NOT include test macros here - only common definitions.
 */

#ifndef TEST_BASE_H
#define TEST_BASE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>

// ============================================================================
// ANSI COLOR CODES
// ============================================================================

#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_MAGENTA "\x1b[35m"
#define ANSI_COLOR_CYAN    "\x1b[36m"
#define ANSI_COLOR_DIM     "\x1b[2m"
#define ANSI_COLOR_RESET   "\x1b[0m"
#define ANSI_BOLD          "\x1b[1m"

// Shorter aliases for common use
#define RED     ANSI_COLOR_RED
#define GREEN   ANSI_COLOR_GREEN
#define YELLOW  ANSI_COLOR_YELLOW
#define BLUE    ANSI_COLOR_BLUE
#define MAGENTA ANSI_COLOR_MAGENTA
#define CYAN    ANSI_COLOR_CYAN
#define DIM     ANSI_COLOR_DIM
#define RESET   ANSI_COLOR_RESET
#define BOLD    ANSI_BOLD

// ============================================================================
// GLOBAL TEST STATISTICS
// ============================================================================

// These globals track overall test results
// They should be defined in each test file's main() function
#ifndef TEST_GLOBALS_DEFINED
#define TEST_GLOBALS_DEFINED

// Overall test counters
extern int total_tests;
extern int passed_tests;
extern int failed_tests;

// Quiet mode support (only show failures)
extern int quiet_mode;

// Per-function test tracking
extern int test_assertions;
extern int test_passed;
extern int test_failed;

// Buffer for collecting failure messages in quiet mode
extern char test_failure_buffer[4096];
extern int test_failure_buffer_used;

#endif // TEST_GLOBALS_DEFINED

// ============================================================================
// TEST CONTEXT
// ============================================================================

// Only define TestContext if not already defined elsewhere
// (test_orchestrator.h defines a different TestContext for security tests)
#ifndef TEST_ORCHESTRATOR_H
// Context for better error messages
typedef struct {
    const char* test_name;
    const char* test_file;
    int test_line;
    char context_message[512];
} TestContext;

// Global test context (can be used by any test framework)
extern TestContext current_test_context;
#endif

// ============================================================================
// INITIALIZATION
// ============================================================================

// Initialize test framework from environment variables
#define INIT_TEST_BASE() do { \
    const char* verbose_env = getenv("TEST_VERBOSE"); \
    const char* quiet_env = getenv("TEST_QUIET"); \
    \
    /* Default to quiet mode unless explicitly verbose */ \
    if (quiet_env && strcmp(quiet_env, "1") == 0) { \
        quiet_mode = 1; \
    } else if (verbose_env && strcmp(verbose_env, "1") == 0) { \
        quiet_mode = 0; \
    } else { \
        quiet_mode = 1; /* Default to quiet */ \
    } \
} while(0)

// Initialize per-function test tracking
#define INIT_TEST_FUNCTION() do { \
    test_assertions = 0; \
    test_passed = 0; \
    test_failed = 0; \
    test_failure_buffer_used = 0; \
    test_failure_buffer[0] = '\0'; \
} while(0)

// ============================================================================
// TIMING UTILITIES
// ============================================================================

// Timer structure for performance testing
typedef struct {
    struct timespec start;
    struct timespec end;
} TestTimer;

// Start timing
static inline void test_timer_start(TestTimer* timer) {
    clock_gettime(CLOCK_MONOTONIC, &timer->start);
}

// End timing and return milliseconds elapsed
static inline double test_timer_end(TestTimer* timer) {
    clock_gettime(CLOCK_MONOTONIC, &timer->end);
    return (timer->end.tv_sec - timer->start.tv_sec) * 1000.0 +
           (timer->end.tv_nsec - timer->start.tv_nsec) / 1000000.0;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Get debug mode from environment
static inline int is_debug_mode(void) {
    const char* debug_env = getenv("TEST_DEBUG");
    return (debug_env && strcmp(debug_env, "1") == 0);
}

// Get explain mode from environment
static inline int is_explain_mode(void) {
    const char* explain_env = getenv("TEST_EXPLAIN");
    return (explain_env && strcmp(explain_env, "1") == 0);
}

// Print a separator line
static inline void print_separator(void) {
    printf(CYAN "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" RESET "\n");
}

// Print a thin separator line
static inline void print_thin_separator(void) {
    printf(CYAN "────────────────────────────────────────────────────────" RESET "\n");
}

// ============================================================================
// MEMORY UTILITIES
// ============================================================================

// Safe string copy with null termination
static inline void safe_strcpy(char* dest, const char* src, size_t dest_size) {
    if (dest_size == 0) return;
    
    size_t src_len = strlen(src);
    size_t copy_len = (src_len < dest_size - 1) ? src_len : dest_size - 1;
    
    memcpy(dest, src, copy_len);
    dest[copy_len] = '\0';
}

// Hex dump for debugging
static inline void hex_dump(const void* data, size_t size) {
    const unsigned char* bytes = (const unsigned char*)data;
    size_t i, j;
    
    for (i = 0; i < size; i += 16) {
        printf("%04zx: ", i);
        
        // Print hex bytes
        for (j = 0; j < 16; j++) {
            if (i + j < size) {
                printf("%02x ", bytes[i + j]);
            } else {
                printf("   ");
            }
            if (j == 7) printf(" ");
        }
        
        printf(" |");
        
        // Print ASCII representation
        for (j = 0; j < 16 && i + j < size; j++) {
            unsigned char c = bytes[i + j];
            printf("%c", (c >= 32 && c < 127) ? c : '.');
        }
        
        printf("|\n");
    }
}

// ============================================================================
// COMMON DEFINITIONS FOR TEST FILES
// ============================================================================

// Standard definitions for test files to implement these globals
#ifndef TEST_ORCHESTRATOR_H
#define DEFINE_TEST_GLOBALS() \
    int total_tests = 0; \
    int passed_tests = 0; \
    int failed_tests = 0; \
    int quiet_mode = 0; \
    int test_assertions = 0; \
    int test_passed = 0; \
    int test_failed = 0; \
    char test_failure_buffer[4096] = {0}; \
    int test_failure_buffer_used = 0; \
    TestContext current_test_context = {0};
#else
// When test_orchestrator.h is included, don't define TestContext
#define DEFINE_TEST_GLOBALS() \
    int total_tests = 0; \
    int passed_tests = 0; \
    int failed_tests = 0; \
    int quiet_mode = 0; \
    int test_assertions = 0; \
    int test_passed = 0; \
    int test_failed = 0; \
    char test_failure_buffer[4096] = {0}; \
    int test_failure_buffer_used = 0;
#endif

// Main function helper for test files
#define TEST_MAIN_HEADER() \
    DEFINE_TEST_GLOBALS() \
    int main(void) { \
        INIT_TEST_BASE();

#define TEST_MAIN_FOOTER() \
        return (failed_tests > 0) ? 1 : 0; \
    }

#endif // TEST_BASE_H