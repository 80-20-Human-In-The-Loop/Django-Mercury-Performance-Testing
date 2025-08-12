# Building a Professional C Test Framework: Complete Implementation Guide

*Based on Django Mercury's battle-tested C testing architecture*

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Header Files](#core-header-files)
4. [Assertion Macros](#assertion-macros)
5. [Test Organization](#test-organization)
6. [Build System Integration](#build-system-integration)
7. [Test Runner Script](#test-runner-script)
8. [Coverage Analysis](#coverage-analysis)
9. [Example Test Implementation](#example-test-implementation)
10. [Best Practices](#best-practices)

## Overview

This guide provides everything needed to implement a professional C test framework similar to Django Mercury's. The framework features:

- **Modular header architecture** (base, simple, enhanced, security)
- **Rich assertion macros** with value printing
- **Quiet and verbose modes** for CI/development
- **Coverage analysis** with gcov
- **Security testing** capabilities
- **Colored output** with ANSI codes
- **Test runner script** for convenience
- **Educational debugging** features

## Architecture

### Directory Structure
```
project/
├── src/                      # Source code
│   ├── module1.c
│   └── module1.h
├── tests/                    # Test files
│   ├── test_base.h          # Base definitions
│   ├── test_simple.h        # Simple assertions
│   ├── test_enhanced.h      # Enhanced debugging
│   ├── test_security.h      # Security testing
│   ├── simple_test_*.c      # Unit tests
│   ├── comprehensive_*.c    # Integration tests
│   ├── edge_test_*.c        # Edge case tests
│   ├── security/            # Security tests
│   └── coverage/            # Coverage reports
├── Makefile                 # Build configuration
└── test_runner.sh           # Test runner script
```

### Layered Header Design
```
test_base.h       (Foundation - colors, globals, utilities)
    ↑
test_simple.h     (Basic assertions, quiet mode)
    ↑
test_enhanced.h   (Rich debugging, value printing)
    ↑
test_security.h   (Security-specific testing)
```

## Core Header Files

### test_base.h - Foundation Layer
```c
/**
 * @file test_base.h
 * @brief Base definitions for C test framework
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

#define RED     "\x1b[31m"
#define GREEN   "\x1b[32m"
#define YELLOW  "\x1b[33m"
#define BLUE    "\x1b[34m"
#define MAGENTA "\x1b[35m"
#define CYAN    "\x1b[36m"
#define DIM     "\x1b[2m"
#define RESET   "\x1b[0m"
#define BOLD    "\x1b[1m"

// ============================================================================
// GLOBAL TEST STATISTICS
// ============================================================================

// These must be defined in each test file
extern int total_tests;
extern int passed_tests;
extern int failed_tests;

// Quiet mode support
extern int quiet_mode;

// Per-function test tracking
extern int test_assertions;
extern int test_passed;
extern int test_failed;

// Buffer for collecting failure messages in quiet mode
extern char test_failure_buffer[4096];
extern int test_failure_buffer_used;

// ============================================================================
// TEST CONTEXT
// ============================================================================

typedef struct {
    const char* test_name;
    const char* test_file;
    int test_line;
    char context_message[512];
} TestContext;

extern TestContext current_test_context;

// ============================================================================
// INITIALIZATION
// ============================================================================

#define INIT_TEST_BASE() do { \
    const char* verbose_env = getenv("TEST_VERBOSE"); \
    const char* quiet_env = getenv("TEST_QUIET"); \
    if (quiet_env && strcmp(quiet_env, "1") == 0) { \
        quiet_mode = 1; \
    } else if (verbose_env && strcmp(verbose_env, "1") == 0) { \
        quiet_mode = 0; \
    } else { \
        quiet_mode = 1; /* Default to quiet */ \
    } \
} while(0)

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

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

static inline int is_debug_mode(void) {
    const char* debug_env = getenv("TEST_DEBUG");
    return (debug_env && strcmp(debug_env, "1") == 0);
}

static inline int is_explain_mode(void) {
    const char* explain_env = getenv("TEST_EXPLAIN");
    return (explain_env && strcmp(explain_env, "1") == 0);
}

// Hex dump for debugging
static inline void hex_dump(const void* data, size_t size) {
    const unsigned char* bytes = (const unsigned char*)data;
    for (size_t i = 0; i < size; i += 16) {
        printf("%04zx: ", i);
        for (size_t j = 0; j < 16; j++) {
            if (i + j < size) {
                printf("%02x ", bytes[i + j]);
            } else {
                printf("   ");
            }
            if (j == 7) printf(" ");
        }
        printf(" |");
        for (size_t j = 0; j < 16 && i + j < size; j++) {
            unsigned char c = bytes[i + j];
            printf("%c", (c >= 32 && c < 127) ? c : '.');
        }
        printf("|\n");
    }
}

// ============================================================================
// STANDARD DEFINITIONS FOR TEST FILES
// ============================================================================

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

#endif // TEST_BASE_H
```

### test_simple.h - Basic Assertions
```c
/**
 * @file test_simple.h
 * @brief Simple test framework with basic assertions
 */

#ifndef TEST_SIMPLE_H
#define TEST_SIMPLE_H

#include "test_base.h"

// ============================================================================
// BASIC ASSERTION MACRO
// ============================================================================

#define ASSERT(condition, message) do { \
    if (quiet_mode) { \
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

// ============================================================================
// TEST SUITE MACROS
// ============================================================================

#define TEST_SUITE_START(name) do { \
    printf(CYAN "\n=== %s ===" RESET "\n", name); \
    total_tests = 0; \
    passed_tests = 0; \
    failed_tests = 0; \
} while(0)

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
// TEST FUNCTION RUNNER
// ============================================================================

#define RUN_TEST(test_func) do { \
    printf(YELLOW "\nRunning %s..." RESET "\n", #test_func); \
    if (quiet_mode) { \
        INIT_TEST_FUNCTION(); \
        int result = test_func(); \
        (void)result; \
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
// INITIALIZATION
// ============================================================================

#define QUIET_MODE_INIT() do { \
    const char* verbose = getenv("TEST_VERBOSE"); \
    quiet_mode = (verbose == NULL || strcmp(verbose, "1") != 0); \
} while(0)

#endif // TEST_SIMPLE_H
```

### test_enhanced.h - Rich Debugging Features
```c
/**
 * @file test_enhanced.h
 * @brief Enhanced test framework with detailed debugging
 */

#ifndef TEST_ENHANCED_H
#define TEST_ENHANCED_H

#include "test_base.h"

// ============================================================================
// ENHANCED ASSERTIONS - INTEGERS
// ============================================================================

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
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (value: %d)\n", message, _actual); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// ENHANCED ASSERTIONS - STRINGS
// ============================================================================

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

// ============================================================================
// ENHANCED ASSERTIONS - POINTERS
// ============================================================================

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
            printf(GREEN "✓ PASS: %s" RESET " (ptr: %p)\n", message, _ptr); \
        } \
        passed_tests++; \
    } \
} while(0)

// ============================================================================
// ENHANCED ASSERTIONS - COMPARISONS
// ============================================================================

#define ASSERT_GT(actual, expected, message) do { \
    total_tests++; \
    int _actual = (actual); \
    int _expected = (expected); \
    if (!(_actual > _expected)) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  " BOLD "Expected:" RESET " > %d\n", _expected); \
        printf("  " BOLD "Got:     " RESET " %d\n", _actual); \
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

// ============================================================================
// CONTEXT AND DEBUGGING
// ============================================================================

#define SET_TEST_CONTEXT(name, ...) do { \
    current_test_context.test_name = name; \
    current_test_context.test_file = __FILE__; \
    current_test_context.test_line = __LINE__; \
    snprintf(current_test_context.context_message, \
             sizeof(current_test_context.context_message), \
             ##__VA_ARGS__); \
} while(0)

#define DEBUG_PRINT(fmt, ...) do { \
    if (is_debug_mode()) { \
        printf(DIM "  [DEBUG] " fmt RESET "\n", ##__VA_ARGS__); \
    } \
} while(0)

#define EXPLAIN_FAILURE(explanation) do { \
    if (is_explain_mode()) { \
        printf(YELLOW "  💡 Explanation: " RESET "%s\n", explanation); \
    } \
} while(0)

// ============================================================================
// TIMING MACROS
// ============================================================================

#define TIME_TEST(code, description) do { \
    TestTimer _timer; \
    test_timer_start(&_timer); \
    code; \
    double _elapsed = test_timer_end(&_timer); \
    printf(MAGENTA "  ⏱ %s took %.2f ms" RESET "\n", \
           description, _elapsed); \
} while(0)

#endif // TEST_ENHANCED_H
```

### test_security.h - Security Testing
```c
/**
 * @file test_security.h
 * @brief Security-focused test framework
 */

#ifndef TEST_SECURITY_H
#define TEST_SECURITY_H

#include "test_base.h"
#include <limits.h>

// ============================================================================
// SECURITY TEST MACROS
// ============================================================================

#define ASSERT_NO_MULT_OVERFLOW(a, b, message) do { \
    total_tests++; \
    size_t _a = (a); \
    size_t _b = (b); \
    if (_a != 0 && _b > SIZE_MAX / _a) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  Integer overflow: %zu * %zu\n", _a, _b); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (no overflow)\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

#define ASSERT_BOUNDS_CHECK(index, size, message) do { \
    total_tests++; \
    size_t _index = (index); \
    size_t _size = (size); \
    if (_index >= _size) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  Buffer overflow: index %zu >= size %zu\n", _index, _size); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (in bounds)\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

#define ASSERT_NULL_TERMINATED(str, max_len, message) do { \
    total_tests++; \
    const char* _str = (str); \
    size_t _max_len = (max_len); \
    bool is_terminated = false; \
    for (size_t i = 0; i < _max_len; i++) { \
        if (_str[i] == '\0') { \
            is_terminated = true; \
            break; \
        } \
    } \
    if (!is_terminated) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  String not null-terminated within %zu bytes\n", _max_len); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (terminated)\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

#define ASSERT_NO_INJECTION(input, message) do { \
    total_tests++; \
    const char* _input = (input); \
    const char* dangerous[] = {";", "|", "&", "`", "$", "(", ")", "<", ">", NULL}; \
    bool is_safe = true; \
    const char* found_char = NULL; \
    for (int i = 0; dangerous[i] != NULL; i++) { \
        if (strstr(_input, dangerous[i]) != NULL) { \
            is_safe = false; \
            found_char = dangerous[i]; \
            break; \
        } \
    } \
    if (!is_safe) { \
        printf(RED "✗ FAIL: %s" RESET "\n", message); \
        printf("  Injection character detected: '%s'\n", found_char); \
        failed_tests++; \
        return 0; \
    } else { \
        if (!quiet_mode) { \
            printf(GREEN "✓ PASS: %s" RESET " (no injection)\n", message); \
        } \
        passed_tests++; \
    } \
} while(0)

#endif // TEST_SECURITY_H
```

## Example Test Implementation

### simple_test_example.c
```c
/**
 * @file simple_test_example.c
 * @brief Example test file using the framework
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "test_simple.h"
#include "../src/my_module.h"

// Define global test variables
DEFINE_TEST_GLOBALS();

// Test basic functionality
int test_basic_operations(void) {
    int result = add(2, 3);
    ASSERT(result == 5, "2 + 3 should equal 5");
    
    result = multiply(4, 5);
    ASSERT(result == 20, "4 * 5 should equal 20");
    
    return 1;
}

// Test error handling
int test_error_handling(void) {
    int result = divide(10, 0);
    ASSERT(result == -1, "Division by zero should return -1");
    
    char* str = process_string(NULL);
    ASSERT(str == NULL, "NULL input should return NULL");
    
    return 1;
}

// Test edge cases
int test_edge_cases(void) {
    int result = add(INT_MAX, 1);
    ASSERT(result == INT_MIN, "Integer overflow should wrap");
    
    char buffer[10];
    bool success = copy_string(buffer, sizeof(buffer), "very long string");
    ASSERT(!success, "Should fail when string too long");
    
    return 1;
}

int main(void) {
    QUIET_MODE_INIT();
    TEST_SUITE_START("Example Module Tests");
    
    RUN_TEST(test_basic_operations);
    RUN_TEST(test_error_handling);
    RUN_TEST(test_edge_cases);
    
    TEST_SUITE_END();
    
    return (failed_tests == 0) ? 0 : 1;
}
```

## Build System Integration

### Makefile Targets
```makefile
# Test configuration
TEST_DIR = tests
TEST_CFLAGS = -Wall -Wextra -g -I$(TEST_DIR)
TEST_LIBS = -lm -lpthread

# Test source files
TEST_SRCS = $(wildcard $(TEST_DIR)/simple_test_*.c)
TEST_BINS = $(TEST_SRCS:.c=)

# Default test target
test: build-tests run-tests

# Build all test executables
build-tests: $(TEST_BINS)

# Pattern rule for building tests
$(TEST_DIR)/simple_test_%: $(TEST_DIR)/simple_test_%.c
	$(CC) $(TEST_CFLAGS) -o $@ $< src/%.c $(TEST_LIBS)

# Run all tests
run-tests:
	@echo "Running tests..."
	@for test in $(TEST_BINS); do \
		echo "Running $$test..."; \
		./$$test || exit 1; \
	done
	@echo "All tests passed!"

# Coverage analysis
coverage: clean-coverage
	@echo "Building with coverage..."
	@mkdir -p $(TEST_DIR)/coverage
	$(CC) $(TEST_CFLAGS) -fprofile-arcs -ftest-coverage \
		-o $(TEST_DIR)/coverage/test_all \
		$(TEST_DIR)/simple_test_*.c src/*.c $(TEST_LIBS)
	@echo "Running tests for coverage..."
	@cd $(TEST_DIR)/coverage && ./test_all
	@echo "Generating coverage report..."
	@gcov -b $(TEST_DIR)/coverage/*.gcda | grep -A 2 "File"
	@echo "Coverage report complete"

clean-coverage:
	rm -rf $(TEST_DIR)/coverage
	rm -f *.gcda *.gcno *.gcov

clean-tests:
	rm -f $(TEST_BINS)
	rm -f $(TEST_DIR)/*.o

clean: clean-tests clean-coverage
```

## Test Runner Script

### test_runner.sh
```bash
#!/bin/bash
# Test runner script for C tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEST_DIR="$SCRIPT_DIR/tests"

# Command line parsing
COMMAND="${1:-test}"
DEBUG=0
VERBOSE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG=1
            export TEST_DEBUG=1
            shift
            ;;
        --verbose)
            VERBOSE=1
            export TEST_VERBOSE=1
            shift
            ;;
        --explain)
            export TEST_EXPLAIN=1
            shift
            ;;
        test|coverage|clean|help)
            COMMAND="$1"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Functions
print_header() {
    echo -e "${CYAN}════════════════════════════════════════${NC}"
    echo -e "${CYAN}         C Test Runner                  ${NC}"
    echo -e "${CYAN}════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}[PASS] $1${NC}"
}

print_error() {
    echo -e "${RED}[FAIL] $1${NC}"
}

print_info() {
    echo -e "${CYAN}[INFO] $1${NC}"
}

# Main execution
print_header

case "$COMMAND" in
    test)
        print_info "Running tests..."
        make test
        print_success "All tests passed!"
        ;;
        
    coverage)
        print_info "Running coverage analysis..."
        make coverage
        print_success "Coverage analysis complete!"
        ;;
        
    clean)
        print_info "Cleaning test artifacts..."
        make clean-tests clean-coverage
        print_success "Clean complete!"
        ;;
        
    help)
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  test       Run all tests (default)"
        echo "  coverage   Run tests with coverage analysis"
        echo "  clean      Clean test artifacts"
        echo "  help       Show this help message"
        echo ""
        echo "Options:"
        echo "  --debug    Enable debug output"
        echo "  --verbose  Show all assertions"
        echo "  --explain  Enable educational explanations"
        echo ""
        echo "Environment Variables:"
        echo "  TEST_DEBUG=1    Enable debug output"
        echo "  TEST_VERBOSE=1  Show all assertions"
        echo "  TEST_EXPLAIN=1  Enable explanations"
        ;;
        
    *)
        print_error "Unknown command: $COMMAND"
        exit 1
        ;;
esac

echo ""
print_success "Test runner completed!"
```

## Coverage Analysis

### Python Coverage Formatter (colorize_gcov.py)
```python
#!/usr/bin/env python3
"""Colorize gcov output based on coverage percentages."""

import sys
import re

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

def get_color(percentage):
    """Get color based on coverage percentage."""
    if percentage < 50:
        return RED
    elif percentage < 80:
        return YELLOW
    else:
        return GREEN

def colorize_line(line):
    """Add color to lines containing coverage percentages."""
    match = re.search(r"Lines executed:(\d+\.\d+)%", line)
    if match:
        percentage = float(match.group(1))
        color = get_color(percentage)
        colored = f"{color}{match.group(1)}%{RESET}"
        return line.replace(f"{match.group(1)}%", colored)
    return line

def main():
    for line in sys.stdin:
        print(colorize_line(line.rstrip()))

if __name__ == "__main__":
    main()
```

### Coverage Summary Script (show_coverage_summary.py)
```python
#!/usr/bin/env python3
"""Display coverage summary from gcov files."""

import os
import glob
import re

def parse_gcov_file(filepath):
    """Parse a gcov file and extract coverage stats."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract source file name
    source_match = re.search(r"File '(.+)'", content)
    if not source_match:
        return None
    
    source_file = source_match.group(1)
    
    # Extract coverage percentage
    coverage_match = re.search(r"Lines executed:(\d+\.\d+)%", content)
    if not coverage_match:
        return None
    
    coverage = float(coverage_match.group(1))
    
    return {
        'file': os.path.basename(source_file),
        'coverage': coverage
    }

def main():
    gcov_files = glob.glob("*.gcov")
    
    if not gcov_files:
        print("No coverage data found")
        return
    
    results = []
    for gcov_file in gcov_files:
        stats = parse_gcov_file(gcov_file)
        if stats and stats['file'].endswith('.c'):
            results.append(stats)
    
    # Sort by coverage percentage
    results.sort(key=lambda x: x['coverage'], reverse=True)
    
    # Display results
    print("\nCoverage Summary:")
    print("=" * 50)
    
    total_coverage = 0
    for result in results:
        coverage = result['coverage']
        color = ""
        if coverage >= 80:
            color = "\033[92m"  # Green
        elif coverage >= 50:
            color = "\033[93m"  # Yellow
        else:
            color = "\033[91m"  # Red
        
        print(f"{result['file']:30s} {color}{coverage:5.1f}%\033[0m")
        total_coverage += coverage
    
    if results:
        avg_coverage = total_coverage / len(results)
        print("=" * 50)
        print(f"Average Coverage: {avg_coverage:.1f}%")

if __name__ == "__main__":
    main()
```

## Best Practices

### 1. Test Organization
- **Naming Convention**: `test_<module>_<functionality>.c`
- **One test function per feature**: Keep tests focused
- **Clear test names**: `test_error_handling_null_input()`
- **Group related tests**: Use test suites

### 2. Assertion Messages
- **Be specific**: "Should return -1 for NULL input"
- **Include expected values**: "Expected 5, got 3"
- **Context matters**: Add file:line information

### 3. Test Coverage
- **Aim for 80%+ coverage**: Focus on critical paths
- **Test edge cases**: NULL, empty, overflow, boundaries
- **Test error paths**: Invalid inputs, allocation failures
- **Security tests**: Buffer overflows, injections

### 4. CI Integration
```yaml
# .github/workflows/test.yml
name: C Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y build-essential gcov
    
    - name: Run tests
      run: ./test_runner.sh test
    
    - name: Run coverage
      run: ./test_runner.sh coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./tests/coverage/*.gcov
```

### 5. Test Execution Modes

#### Quiet Mode (Default for CI)
```bash
# Only shows failures
./test_runner.sh test
```

#### Verbose Mode (Development)
```bash
# Shows all assertions
TEST_VERBOSE=1 ./test_runner.sh test
```

#### Debug Mode
```bash
# Shows debug output
TEST_DEBUG=1 ./test_runner.sh test
```

#### Educational Mode
```bash
# Shows explanations for failures
TEST_EXPLAIN=1 ./test_runner.sh test
```

### 6. Common Patterns

#### Setup and Teardown
```c
int test_with_setup(void) {
    // Setup
    void* resource = allocate_resource();
    ASSERT(resource != NULL, "Setup should succeed");
    
    // Test
    int result = use_resource(resource);
    ASSERT(result == 0, "Operation should succeed");
    
    // Teardown
    free_resource(resource);
    
    return 1;
}
```

#### Testing Error Conditions
```c
int test_error_conditions(void) {
    // Test NULL handling
    int result = process(NULL);
    ASSERT(result == ERROR_NULL, "Should handle NULL");
    
    // Test overflow
    result = add(INT_MAX, 1);
    ASSERT(result == ERROR_OVERFLOW, "Should detect overflow");
    
    return 1;
}
```

#### Performance Testing
```c
int test_performance(void) {
    TIME_TEST({
        for (int i = 0; i < 1000000; i++) {
            process_data(i);
        }
    }, "Processing 1M items");
    
    return 1;
}
```

## Summary

This framework provides:

1. **Modular Architecture**: Separate headers for different testing needs
2. **Rich Assertions**: Value printing, comparisons, security checks
3. **Flexible Output**: Quiet mode for CI, verbose for development
4. **Coverage Analysis**: Integrated gcov support with formatting
5. **Educational Features**: Debug output and failure explanations
6. **Security Testing**: Specialized macros for vulnerability testing
7. **Convenience Scripts**: Test runner and coverage tools
8. **Best Practices**: Proven patterns from production use

The framework has been battle-tested in Django Mercury with:
- 70%+ code coverage across multiple modules
- Thousands of assertions
- Cross-platform compatibility (Linux, macOS, Windows)
- CI/CD integration
- Security vulnerability detection

Start with `test_simple.h` for basic testing, add `test_enhanced.h` for debugging, and include `test_security.h` for security-critical code. The modular design allows you to use only what you need while maintaining a consistent testing approach across your C project.