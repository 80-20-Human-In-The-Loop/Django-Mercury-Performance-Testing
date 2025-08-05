# Development Testing C

Learn how to create, fix, and run tests with the Django Mercury C testing system.

## Understanding the C Test System

Django Mercury uses a comprehensive C testing framework built around the `c_test_runner.sh` script. The system emphasizes memory safety, performance monitoring, and educational feedback.

### **What Makes Our C Testing Special**

**Quiet Mode by Default**: Tests show consolidated output ("X assertions passed") instead of individual assertions  
**Auto-Build System**: Missing test executables are automatically built - no more silent failures  
**Security Focus**: Comprehensive security vulnerability testing suite included  
**Educational Features**: Enhanced debugging mode with detailed explanations  
**Cross-Platform Support**: Works on Linux, macOS, and Windows environments

## Quick Start

### **Run All C Tests**
```bash
./c_test_runner.sh
# or
./c_test_runner.sh test
```

### **Run Tests Verbosely**
```bash
./c_test_runner.sh test --verbose
# or set environment variable
TEST_VERBOSE=1 ./c_test_runner.sh
```

### **Run Tests with Coverage Analysis**
```bash
./c_test_runner.sh coverage
```

### **Run Security Tests**
```bash
./c_test_runner.sh security
```

## Available Commands

The `c_test_runner.sh` script provides these commands:

- **test** - Run simple C tests with quiet mode (default)
- **coverage** - Run tests with gcov coverage analysis
- **enhanced** - Run tests with enhanced debugging features
- **security** - Run security vulnerability tests 🔒
- **all** - Run all tests and coverage
- **clean** - Clean test artifacts
- **build** - Build C libraries only
- **benchmark** - Run performance benchmarks
- **memcheck** - Run memory safety checks (Linux only)
- **help** - Show help message

## Command Options

- **--verbose** - Show all test assertions (overrides quiet mode)
- **--debug** - Enable debug output with verbose information
- **--explain** - Enable educational mode with failure explanations
- **--warnings** - Show compilation warnings and info messages
- **--single TEST** - Run a specific test file
- **--fix-only** - Only compile with fixes, don't run

## Test Framework Features

### **Quiet Mode (Default Behavior)**

By default, tests run in quiet mode, showing only summaries:

```bash
Running test_memory_alignment...
✓ test_memory_alignment: 12 assertions passed

Running test_ring_buffer...
✓ test_ring_buffer: 20 assertions passed
```

To see all assertions, use `--verbose`:

```bash
./c_test_runner.sh test --verbose
```

### **Auto-Build Feature**

The test runner automatically detects missing executables and builds them:

```
[INFO] Test executables not found, building first...
🔨 Building C extensions and test executables...
[PASS] Libraries built successfully!
```

### **Test Framework Macros**

The framework provides these macros in `simple_tests.h`:

- `ASSERT(condition, message)` - Main assertion macro with quiet mode support
- `ASSERT_QUIET(condition, message)` - Always quiet assertion
- `TEST_SUITE_START(name)` - Initialize test suite
- `TEST_SUITE_END()` - Print test summary  
- `TEST_FUNCTION_START()` - Initialize test function counters
- `RUN_TEST(test_func)` - Run test with automatic quiet mode handling
- `QUIET_MODE_INIT()` - Initialize quiet mode from environment

## Test Structure

Django Mercury organizes C tests by functionality and complexity:

```
django_mercury/c_core/tests/
├── simple_test_*.c          # Unit tests for individual functions
├── comprehensive_test_*.c   # Integration tests for components
├── edge_test_*.c           # Edge cases and error conditions
├── consolidation/          # Migration safety tests
│   ├── test_api_compatibility.c
│   ├── test_feature_parity.c
│   └── test_migration_safety.c
├── security/               # Security vulnerability tests
│   ├── test_buffer_overflow.c
│   ├── test_command_injection.c
│   ├── test_format_and_bounds.c
│   ├── test_input_validation.c
│   └── test_memory_security.c
├── simple_tests.h          # Main test framework
├── enhanced_tests.h        # Enhanced debugging framework
└── coverage/              # Coverage analysis output
```

### **Test Categories**

**Simple Tests** (`simple_test_*.c`)
- `simple_test_common.c` - Common utility functions
- `simple_test_advanced.c` - Advanced feature tests
- `simple_test_query_analyzer.c` - SQL query analysis
- `simple_test_metrics_engine.c` - Metrics calculation
- `simple_test_test_orchestrator.c` - Test coordination

**Comprehensive Tests** (`comprehensive_test_*.c`)
- Full integration testing of multiple components
- Complex workflows and real-world scenarios

**Edge Tests** (`edge_test_*.c`)
- Boundary conditions and extreme cases
- Error handling and recovery scenarios

**Security Tests** (`security/test_*.c`)
- Buffer overflow protection
- Command injection prevention
- Input validation
- Memory safety

## Writing Tests Using Django Mercury Framework

### **Basic Test Structure**

```c
/**
 * @file simple_test_my_feature.c
 * @brief Test suite for my new feature
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../common.h"
#include "simple_tests.h"

// Global test counters required by framework
int total_tests = 0;
int passed_tests = 0;
int failed_tests = 0;

// Quiet mode variables
int quiet_mode = 0;
int test_assertions = 0;
int test_passed = 0;
int test_failed = 0;
char test_failure_buffer[4096];
int test_failure_buffer_used = 0;

/**
 * @brief Test basic functionality
 * @return 1 on success, 0 on failure
 */
static int test_basic_functionality(void) {
    TEST_FUNCTION_START();
    
    // Your test code here
    int result = my_function(42);
    ASSERT(result == 84, "my_function should double the input");
    
    char* buffer = malloc(100);
    ASSERT(buffer != NULL, "Should allocate memory successfully");
    
    // Use buffer...
    strcpy(buffer, "test");
    ASSERT(strcmp(buffer, "test") == 0, "Buffer should contain 'test'");
    
    free(buffer);
    return 1;
}

/**
 * @brief Test error handling
 * @return 1 on success, 0 on failure
 */
static int test_error_handling(void) {
    TEST_FUNCTION_START();
    
    // Test NULL input
    int result = my_function_safe(NULL);
    ASSERT(result == ERROR_NULL_INPUT, "Should handle NULL input");
    
    // Test invalid parameters
    result = my_function_with_size("test", 0);
    ASSERT(result == ERROR_INVALID_SIZE, "Should reject zero size");
    
    return 1;
}

int main(void) {
    QUIET_MODE_INIT();  // Initialize quiet mode from TEST_VERBOSE env var
    TEST_SUITE_START("My Feature Test Suite");
    
    if (!quiet_mode) {
        printf("Testing my_feature functionality...\n\n");
    }
    
    RUN_TEST(test_basic_functionality);
    RUN_TEST(test_error_handling);
    
    TEST_SUITE_END();
    
    return (failed_tests == 0) ? 0 : 1;
}
```

### **Using Enhanced Tests for Debugging**

The `enhanced_tests.h` framework provides more detailed debugging:

```c
#include "enhanced_tests.h"

// Enhanced tests show detailed failure information
ASSERT_EQ_INT(actual, expected, "Values should match");
// Output on failure:
// ✗ FAIL: Values should match
//   Expected: 42 (0x2a)
//   Got:      41 (0x29)
//   at test_file.c:123 in test_function()

ASSERT_STR_EQ(str1, str2, "Strings should match");
// Shows first character difference on failure

ASSERT_TRUE(condition, "Condition should be true");
// Shows the actual expression that failed
```

## Running Tests

### **Basic Test Execution**

```bash
# Run all tests (quiet mode by default)
./c_test_runner.sh

# Run with verbose output
./c_test_runner.sh test --verbose

# Clean and rebuild
./c_test_runner.sh clean
./c_test_runner.sh test  # Will auto-build
```

### **Coverage Analysis**

```bash
# Run tests with coverage
./c_test_runner.sh coverage

# Generates:
# - Console coverage report with percentages
# - Detailed line-by-line coverage
# - HTML reports in c_core/tests/coverage/
```

### **Security Testing**

```bash
# Run comprehensive security tests
./c_test_runner.sh security

# Tests for:
# ✓ Buffer overflow protection
# ✓ Command injection prevention
# ✓ Format string vulnerabilities
# ✓ Input validation
# ✓ Memory safety
```

### **Enhanced Debugging Mode**

```bash
# Run with enhanced debugging
./c_test_runner.sh enhanced

# With educational explanations
./c_test_runner.sh enhanced --explain

# Features:
# - Detailed failure messages
# - Hex dumps for buffer comparisons
# - Query analyzer state inspection
# - Performance timing information
```

## Understanding Test Output

### **Quiet Mode Output (Default)**

```
╔════════════════════════════════════════════════════════════╗
║          Django Mercury C Core Test Runner                ║
╚════════════════════════════════════════════════════════════╝

[INFO] Running simple C tests...
🔧 Running all tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Running test_memory_alignment...
✓ test_memory_alignment: 12 assertions passed

Running test_ring_buffer...
✓ test_ring_buffer: 20 assertions passed

=== Results ===
Total: 32, Passed: 32, Failed: 0
All tests passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Test Summary:
   Total tests: 695
   Passed: 698
   Failed: 0
[PASS] All tests passed!
```

### **Verbose Mode Output**

```
Running test_memory_alignment...
Testing memory alignment functions...
✓ PASS: Should align to 8 bytes
✓ PASS: Should align to 16 bytes
✓ PASS: Should align to cache line
✓ test_memory_alignment passed
```

### **Failure Output**

```
Running test_boundary_conditions...
✗ test_boundary_conditions: 3/5 assertions passed
  ✗ FAIL: Buffer size should be exactly 1024
    at simple_test_common.c:156 in test_boundary_conditions()
  ✗ FAIL: Should handle maximum size
    at simple_test_common.c:162 in test_boundary_conditions()
```

### **Coverage Output**

```
📊 Coverage Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File                          Lines    Exec  Cover
------------------------------------------------------------
common.c                       280     245   87.5%
query_analyzer.c               450     423   94.0%
metrics_engine.c               320     298   93.1%
test_orchestrator.c            560     504   90.0%
------------------------------------------------------------
TOTAL                         1610    1470   91.3%

Uncovered Lines:
  common.c:156-162 - Error handling path
  query_analyzer.c:89-92 - Complex query parsing
```

### **Security Test Output**

```
╔════════════════════════════════════════════════════════════╗
║           🔒 SECURITY VULNERABILITY TESTING 🔒            ║
║                                                            ║
║  Testing for:                                              ║
║  • Command injection vulnerabilities                      ║
║  • Buffer overflow protections                            ║
║  • Input validation                                       ║
║  • Memory safety                                          ║
╚════════════════════════════════════════════════════════════╝

Testing buffer overflow protection...
✓ Stack buffer overflow protection working
✓ Heap buffer overflow protection working

Testing command injection...
✓ System commands properly escaped
✓ SQL injection prevented

✅ All security tests passed!
No critical vulnerabilities detected.
```

## Debugging Test Failures

### **Build Failures**

If the auto-build fails:

```bash
[INFO] Test executables not found, building first...
🔨 Building C extensions and test executables...
[FAIL] Failed to build C extensions

Build output above. Common issues:
  - Missing dependencies (check error messages)
  - Compilation errors in C code
  - Permission issues
```

Solutions:
```bash
# Check for missing tools
./c_test_runner.sh help

# Install build tools (Ubuntu/Debian)
sudo apt-get install build-essential

# Install build tools (macOS)
xcode-select --install
```

### **Test Failures**

For detailed debugging:

```bash
# Run specific test with verbose output
TEST_VERBOSE=1 ./c_test_runner.sh test

# Use gdb for crashes
cd django_mercury/c_core
gdb ./simple_test_common
(gdb) run
(gdb) bt  # Show backtrace on crash
```

### **Memory Issues**

```bash
# Run memory checks (Linux with valgrind)
./c_test_runner.sh memcheck

# Use AddressSanitizer
cd django_mercury/c_core
make clean
CFLAGS="-fsanitize=address -g" make test
```

## Writing Effective C Tests

### **Follow the Framework Patterns**

```c
// ✅ Good: Use framework macros
static int test_example(void) {
    TEST_FUNCTION_START();
    
    void* ptr = malloc(100);
    ASSERT(ptr != NULL, "Allocation should succeed");
    
    int result = process_data(ptr);
    ASSERT(result == 0, "Processing should succeed");
    
    free(ptr);
    return 1;
}

// ❌ Bad: Don't use raw asserts
static int test_bad_example(void) {
    void* ptr = malloc(100);
    assert(ptr != NULL);  // Won't respect quiet mode
    // Missing TEST_FUNCTION_START()
    return 1;
}
```

### **Test Naming Conventions**

```c
// ✅ Good: Descriptive test names
static int test_handles_null_input_gracefully(void)
static int test_validates_buffer_size_limits(void)
static int test_recovers_from_allocation_failure(void)

// ❌ Bad: Vague names
static int test1(void)
static int test_stuff(void)
```

### **Memory Management**

```c
// ✅ Good: Always clean up
static int test_with_cleanup(void) {
    TEST_FUNCTION_START();
    
    char* buffer1 = malloc(100);
    ASSERT(buffer1 != NULL, "First allocation should succeed");
    
    char* buffer2 = malloc(200);
    if (buffer2 == NULL) {
        free(buffer1);  // Clean up before return
        ASSERT(0, "Second allocation failed");
        return 0;
    }
    
    // Use buffers...
    
    free(buffer2);
    free(buffer1);
    return 1;
}
```

### **Performance Testing**

```c
static int test_performance_requirements(void) {
    TEST_FUNCTION_START();
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    // Run operation 1000 times
    for (int i = 0; i < 1000; i++) {
        fast_function();
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double elapsed_ms = (end.tv_sec - start.tv_sec) * 1000.0 +
                       (end.tv_nsec - start.tv_nsec) / 1000000.0;
    
    if (!quiet_mode) {
        printf("  Performance: %.2f ms for 1000 operations\n", elapsed_ms);
    }
    
    ASSERT(elapsed_ms < 100.0, "Should complete 1000 ops in < 100ms");
    
    return 1;
}
```

## Adding New Test Files

### **1. Create Test File**

Create your test file following the naming convention:

```bash
# For unit tests
touch django_mercury/c_core/tests/simple_test_my_feature.c

# For integration tests
touch django_mercury/c_core/tests/comprehensive_test_my_feature.c

# For edge cases
touch django_mercury/c_core/tests/edge_test_my_feature.c
```

### **2. Include Required Headers**

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include "../common.h"
#include "simple_tests.h"

// Add all required global variables
int total_tests = 0;
int passed_tests = 0;
int failed_tests = 0;
int quiet_mode = 0;
int test_assertions = 0;
int test_passed = 0;
int test_failed = 0;
char test_failure_buffer[4096];
int test_failure_buffer_used = 0;
```

### **3. Update Makefile**

Add your test to the appropriate section in `django_mercury/c_core/Makefile`:

```makefile
# For simple tests, add to the test target
test: simple_test
	@echo "\n=== My Feature Tests ==="
	@./simple_test_my_feature
```

## Security Testing Best Practices

### **Always Include Security Tests**

```c
static int test_buffer_overflow_protection(void) {
    TEST_FUNCTION_START();
    
    char buffer[16];
    
    // Try to overflow - should be caught
    int result = safe_copy(buffer, sizeof(buffer), 
                          "This string is way too long for the buffer");
    
    ASSERT(result == ERROR_BUFFER_TOO_SMALL, 
           "Should prevent buffer overflow");
    
    return 1;
}

static int test_null_pointer_handling(void) {
    TEST_FUNCTION_START();
    
    // All functions should handle NULL gracefully
    ASSERT(my_function(NULL) == ERROR_NULL_INPUT,
           "Should handle NULL input");
    
    ASSERT(my_function_with_output(NULL, NULL) == ERROR_NULL_INPUT,
           "Should handle NULL output");
    
    return 1;
}
```

### **Test Format String Safety**

```c
static int test_format_string_safety(void) {
    TEST_FUNCTION_START();
    
    char output[256];
    const char* malicious = "%s%s%s%s%n";
    
    // Should not crash or corrupt memory
    int result = safe_format(output, sizeof(output), malicious);
    ASSERT(result == 0 || result == ERROR_INVALID_FORMAT,
           "Should handle format string attack safely");
    
    return 1;
}
```

## Environment Variables

- `TEST_VERBOSE=1` - Enable verbose output (same as --verbose)
- `TEST_DEBUG=1` - Enable debug output
- `FORCE_COLOR=1` - Force colored output in CI environments

## Continuous Integration

For CI/CD pipelines:

```bash
# Basic CI test run
./c_test_runner.sh test

# Full CI validation
./c_test_runner.sh all && ./c_test_runner.sh security

# With coverage reporting
./c_test_runner.sh coverage
# Coverage reports are in django_mercury/c_core/tests/coverage/
```

## Common Patterns

### **Testing with Mock Data**

```c
static int test_with_mock_data(void) {
    TEST_FUNCTION_START();
    
    // Create mock data
    MockDatabase* db = mock_database_create();
    ASSERT(db != NULL, "Should create mock database");
    
    // Add test data
    mock_database_add_user(db, "testuser", "test@example.com");
    
    // Test function with mock
    User* user = find_user_by_email(db, "test@example.com");
    ASSERT(user != NULL, "Should find user by email");
    ASSERT(strcmp(user->username, "testuser") == 0, 
           "Username should match");
    
    // Clean up
    mock_database_destroy(db);
    
    return 1;
}
```

### **Testing Thread Safety**

```c
static void* thread_worker(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    
    for (int i = 0; i < 1000; i++) {
        increment_counter(data->counter);
    }
    
    return NULL;
}

static int test_thread_safety(void) {
    TEST_FUNCTION_START();
    
    SharedCounter* counter = counter_create();
    ASSERT(counter != NULL, "Should create counter");
    
    pthread_t threads[4];
    ThreadData data = { .counter = counter };
    
    // Start threads
    for (int i = 0; i < 4; i++) {
        ASSERT(pthread_create(&threads[i], NULL, 
                            thread_worker, &data) == 0,
               "Should create thread");
    }
    
    // Wait for completion
    for (int i = 0; i < 4; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Verify result
    ASSERT(counter_get_value(counter) == 4000,
           "Counter should be thread-safe");
    
    counter_destroy(counter);
    return 1;
}
```

## Troubleshooting

### **"Test executables not found"**

This is now automatically handled - the script will build missing executables.

### **Silent Failures**

No longer an issue! The improved script shows clear error messages.

### **Compilation Warnings**

Use `--warnings` flag to see compilation warnings:

```bash
./c_test_runner.sh test --warnings
```

### **Test Timeout**

For long-running tests, increase timeout in test code:

```c
// For tests that need more time
alarm(60);  // 60 second timeout
```

---

**Remember**: Django Mercury's C testing framework emphasizes safety, clarity, and education. Write tests that not only verify functionality but also help other developers understand your code!