# Django Mercury C Test Framework

## Overview

The Django Mercury C test framework provides a hierarchical, modular testing infrastructure for C code. The framework is designed without backward compatibility concerns, focusing on clean architecture and appropriate tool selection for each testing scenario.

## Hierarchical Structure

```
test_base.h
    ├── test_simple.h     (Basic testing)
    ├── test_enhanced.h   (Rich assertions & debugging)
    └── test_security.h   (Security vulnerability testing)
```

### 1. test_base.h - Foundation Layer

**Purpose**: Core definitions shared by all test frameworks

**Contents**:
- ANSI color code definitions (RED, GREEN, YELLOW, etc.)
- Global test counter declarations
- Quiet mode support variables
- Common utility macros (DEFINE_TEST_GLOBALS, INIT_TEST_BASE, etc.)
- TestContext structure definition
- Timer utilities for performance measurement

**When to use**: Never include directly - it's automatically included by other headers

### 2. test_simple.h - Simple Testing

**Purpose**: Basic pass/fail testing with minimal overhead

**Key Features**:
- Simple ASSERT macro for condition checking
- ASSERT_QUIET for collecting failures without output
- TEST_SUITE_START/END for test organization
- RUN_TEST macro for executing test functions
- Quiet mode support (controlled by TEST_VERBOSE env var)

**When to use**:
- Unit tests with simple pass/fail requirements
- Tests that don't need detailed failure information
- Performance-critical tests where overhead matters

**Example**:
```c
#include "test_simple.h"

DEFINE_TEST_GLOBALS();

int test_basic_functionality() {
    ASSERT(1 + 1 == 2, "Basic math should work");
    ASSERT(strlen("test") == 4, "String length check");
    return 1;
}

int main() {
    QUIET_MODE_INIT();
    TEST_SUITE_START("Basic Tests");
    RUN_TEST(test_basic_functionality);
    TEST_SUITE_END();
    return failed_tests > 0 ? 1 : 0;
}
```

### 3. test_enhanced.h - Enhanced Testing

**Purpose**: Rich assertions with detailed debugging and educational features

**Key Features**:
- Value-printing assertions (ASSERT_EQ_INT, ASSERT_STR_EQ, etc.)
- Comparison assertions (ASSERT_GT, ASSERT_LT, etc.)
- Boolean assertions (ASSERT_TRUE, ASSERT_FALSE)
- String testing (ASSERT_STR_CONTAINS)
- Pointer validation (ASSERT_NOT_NULL, ASSERT_NULL)
- EXPECT variants (non-fatal failures)
- Test context for better error messages
- Debug mode support (TEST_DEBUG env var)
- Performance timing macros

**When to use**:
- Integration tests requiring detailed failure analysis
- Comprehensive test suites
- Tests where understanding failures is critical
- Educational scenarios where detailed output helps learning

**Example**:
```c
#include "test_enhanced.h"

DEFINE_TEST_GLOBALS();
DEFINE_TEST_CONTEXT();

int test_detailed_checks() {
    SET_TEST_CONTEXT("Database Test", "Checking query performance");
    
    int result = 42;
    ASSERT_EQ_INT(result, 42, "Result should be 42");
    
    const char* query = "SELECT * FROM users";
    ASSERT_STR_CONTAINS(query, "SELECT", "Should be a SELECT query");
    
    double elapsed = 105.3;
    ASSERT_LT(elapsed, 200, "Query should complete in < 200ms");
    
    return 1;
}

int main() {
    QUIET_MODE_INIT();
    TEST_SUITE_START("Enhanced Tests");
    RUN_TEST(test_detailed_checks);
    TEST_SUITE_END();
    return failed_tests > 0 ? 1 : 0;
}
```

### 4. test_security.h - Security Testing

**Purpose**: Specialized testing for security vulnerabilities

**Key Features**:
- Integer overflow detection (ASSERT_NO_MULT_OVERFLOW, ASSERT_NO_ADD_OVERFLOW)
- Buffer bounds checking (ASSERT_BOUNDS_CHECK)
- String safety (ASSERT_NULL_TERMINATED)
- Pointer validation (ASSERT_VALID_PTR)
- Injection detection (ASSERT_NO_INJECTION)
- Format string safety (ASSERT_SAFE_FORMAT)
- Fuzzing support (FUZZ_TEST)
- Use-after-free testing
- Security-specific test suite macros

**When to use**:
- Security vulnerability testing
- Input validation testing
- Memory safety verification
- Fuzzing and stress testing
- Compliance testing

**Example**:
```c
#include "test_security.h"

DEFINE_TEST_GLOBALS();

int test_buffer_safety() {
    size_t size = 100;
    size_t index = 50;
    ASSERT_BOUNDS_CHECK(index, size, "Index should be within bounds");
    
    size_t a = SIZE_MAX / 2;
    size_t b = 3;
    ASSERT_NO_MULT_OVERFLOW(a, b, "Multiplication should not overflow");
    
    const char* user_input = "safe_input";
    ASSERT_NO_INJECTION(user_input, "Input should not contain injection chars");
    
    const char* fmt = "%s %d";
    ASSERT_SAFE_FORMAT(fmt, "Format string should be safe");
    
    return 1;
}

int process_fuzzed_input(const char* input) {
    // Your function to test
    return (input && strlen(input) < 1000) ? 0 : -1;
}

int test_fuzzing() {
    FUZZ_TEST(process_fuzzed_input, 1000, "Function should handle random input");
    return 1;
}

int main() {
    SECURITY_TEST_START("Buffer Security");
    RUN_TEST(test_buffer_safety);
    RUN_TEST(test_fuzzing);
    SECURITY_TEST_END();
    return failed_tests > 0 ? 1 : 0;
}
```

## Migration Guide

### From old headers to new:

1. **simple_tests.h → test_simple.h**
   - Direct replacement, same functionality
   - Add `DEFINE_TEST_GLOBALS();` at file scope

2. **enhanced_tests.h → test_enhanced.h**
   - Direct replacement with more features
   - Add `DEFINE_TEST_GLOBALS();` and `DEFINE_TEST_CONTEXT();`

3. **test_framework.h → test_security.h**
   - Replace for security-specific tests
   - Add `DEFINE_TEST_GLOBALS();`

## File Organization

```
tests/
├── test_base.h           # Foundation (don't include directly)
├── test_simple.h         # Simple testing framework
├── test_enhanced.h       # Enhanced testing with debugging
├── test_security.h       # Security testing framework
├── simple_test_*.c       # Unit tests using test_simple.h
├── comprehensive_*.c     # Integration tests using test_enhanced.h
├── edge_test_*.c        # Edge cases using test_simple.h
└── security/            # Security tests using test_security.h
    └── test_*.c
```

## Environment Variables

- `TEST_VERBOSE=1` - Enable verbose output (default is quiet mode)
- `TEST_DEBUG=1` - Enable debug output in enhanced tests
- `TEST_EXPLAIN=1` - Enable educational explanations

## Best Practices

1. **Choose the right framework**:
   - Use `test_simple.h` for unit tests
   - Use `test_enhanced.h` for integration/comprehensive tests
   - Use `test_security.h` for security testing

2. **Always define globals**:
   ```c
   DEFINE_TEST_GLOBALS();  // Required in all test files
   ```

3. **Initialize properly**:
   ```c
   QUIET_MODE_INIT();      // For quiet/verbose mode control
   TEST_SUITE_START(name); // At the beginning of tests
   ```

4. **Return proper exit codes**:
   ```c
   return failed_tests > 0 ? 1 : 0;  // In main()
   ```

5. **Use appropriate assertions**:
   - Simple: `ASSERT(condition, message)`
   - Enhanced: `ASSERT_EQ_INT(actual, expected, message)`
   - Security: `ASSERT_BOUNDS_CHECK(index, size, message)`

## Running Tests

Use the Django Mercury C test runner:

```bash
# Run all tests
./c_test_runner.sh test

# Run with verbose output
TEST_VERBOSE=1 ./c_test_runner.sh test

# Run security tests
./c_test_runner.sh security

# Run with debug output
TEST_DEBUG=1 ./c_test_runner.sh enhanced
```

## Benefits of the New Structure

1. **Clear Separation of Concerns**: Each header serves a specific purpose
2. **No Backward Compatibility Baggage**: Clean, modern design
3. **Hierarchical Design**: Build on common foundation
4. **Appropriate Tools**: Use the right level of testing for each scenario
5. **Consistent Interface**: All frameworks share similar macros and patterns
6. **Educational Value**: Enhanced framework helps developers learn from failures
7. **Security Focus**: Dedicated framework for vulnerability testing
8. **Performance**: Simple framework has minimal overhead for unit tests

## Future Enhancements

Potential additions while maintaining the hierarchical structure:

- `test_performance.h` - Specialized performance benchmarking
- `test_concurrent.h` - Multi-threaded testing support
- `test_mock.h` - Mocking and stubbing framework
- `test_coverage.h` - Coverage tracking integration

The framework is designed to grow while maintaining its clean, hierarchical architecture.