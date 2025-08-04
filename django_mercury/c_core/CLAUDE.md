# C Security Standards & Best Practices for Django Mercury

*Comprehensive guidelines for writing safe, documented, and maintainable C code*

## CRITICAL: C Code is Dangerous

**C gives you complete control and complete responsibility.** There is no safety net. Every line of C code can corrupt memory, crash the program, or create security vulnerabilities. This document contains hard-learned lessons from real security bugs.

**For AI/Agents generating C code:** Follow these standards exactly. C is unforgiving of mistakes.

## Section 1: MANDATORY Documentation Requirements

### EVERY Function MUST Have Doxygen Documentation

**This is non-negotiable. No exceptions. Every single function, structure, macro, and file MUST have complete Doxygen documentation.**

```c
/**
 * @file test_orchestrator.c
 * @brief High-Performance Test Orchestration Engine
 * 
 * @details This library implements a high-performance test orchestration engine
 * replacing Python-based orchestration with optimized C implementations.
 * 
 * @author Django Mercury Team
 * @date 2024
 * @version 2.0.0
 */

/**
 * @brief Initialize the test orchestrator
 * 
 * @details Sets up memory-mapped history file and allocates context pool.
 * Must be called before any other orchestrator functions.
 * 
 * @param history_file_path Path to history file (NULL for default)
 * @return 0 on success, negative error code on failure
 * 
 * @pre history_file_path must be valid path or NULL
 * @post Orchestrator is initialized and ready for use
 * 
 * @warning Not thread-safe - call only once at startup
 * @note Automatically creates history file if it doesn't exist
 */
int initialize_test_orchestrator(const char* history_file_path);

/**
 * @struct TestContext
 * @brief Test execution context for performance monitoring
 * 
 * @details Maintains all metrics and configuration for a single test run.
 * Memory layout is critical - do not modify without updating all users.
 */
typedef struct TestContext {
    /** @brief Unique identifier for this context */
    int context_id;
    
    /** @brief Test class name (max 127 chars + null) */
    char test_class[128];
    
    /** @brief Test method name (max 127 chars + null) */
    char test_method[128];
    
    /** @brief Start timestamp in nanoseconds since epoch */
    uint64_t start_time;
    
    /** @brief Performance configuration thresholds */
    struct {
        double response_time_threshold;  /**< Max acceptable response time (ms) */
        double memory_threshold_mb;       /**< Max memory usage (MB) */
        uint32_t max_queries;            /**< Max database queries allowed */
        double min_cache_hit_ratio;      /**< Minimum cache hit ratio (0.0-1.0) */
    } config;
} TestContext;
```

### Documentation Checklist

- [ ] **EVERY .c and .h file has @file header**
- [ ] **EVERY function has @brief and @param**
- [ ] **EVERY function documents @return values**
- [ ] **EVERY struct has @brief for the struct and EACH field**
- [ ] **EVERY macro has documentation**
- [ ] **EVERY typedef has documentation**
- [ ] **Complex functions have @details sections**
- [ ] **Error conditions documented with @warning**
- [ ] **Thread safety documented with @warning**
- [ ] **Memory ownership documented with @note**

## Section 2: Critical Security Requirements

### The #1 Security Bug: Struct Definition Mismatch

**This single issue caused 4 security vulnerabilities in our code.**

```c
// NEVER DO THIS - Duplicate struct definitions
// file: implementation.c
typedef struct {
    int64_t id;           // 8 bytes
    char name[128];       
    MercuryTimestamp time; // Custom type
} MyStruct;

// file: header.h  
typedef struct {
    int id;               // 4 bytes - DIFFERENT SIZE!
    char name[128];       
    uint64_t time;        // Different type!
} MyStruct;
```

**Why this destroys your program:**
- Tests cast `void*` to `MyStruct*` using header definition
- Implementation uses different memory layout
- Fields get corrupted silently
- Security checks fail
- Memory corruption spreads

### RULE: Single Definition Only

```c
// header.h - THE ONLY DEFINITION
typedef struct {
    int id;
    char name[128];
    uint64_t time;
} MyStruct;

// implementation.c
#include "header.h"  // Use the SAME definition
// NO redefinition allowed
```

### String Handling Security

```c
// BANNED FUNCTIONS - Never use these
strcpy(dest, src);        // Buffer overflow
strcat(dest, src);        // Buffer overflow
sprintf(buffer, format);  // Format string attack
gets(buffer);            // Removed from C11

// REQUIRED: Safe string operations
// Method 1: Explicit bounds checking
size_t len = strlen(src);
if (len >= dest_size) {
    len = dest_size - 1;
}
memcpy(dest, src, len);
dest[len] = '\0';

// Method 2: Bounded string functions
strncpy(dest, src, dest_size - 1);
dest[dest_size - 1] = '\0';  // ALWAYS null-terminate

// Method 3: Safe formatting
snprintf(buffer, sizeof(buffer), "%s", user_input);
```

### Input Validation Requirements

```c
/**
 * @brief Process user data safely
 * 
 * @param data User-provided data (may be NULL)
 * @param size Size of data
 * @return 0 on success, negative on error
 */
int process_user_data(const void* data, size_t size) {
    // MANDATORY: Validate ALL inputs
    if (!data) return ERROR_NULL_INPUT;
    if (size == 0) return ERROR_INVALID_SIZE;
    if (size > MAX_ALLOWED_SIZE) return ERROR_TOO_LARGE;
    
    // MANDATORY: Validate numeric ranges
    if (size > SIZE_MAX / 2) return ERROR_OVERFLOW_RISK;
    
    // MANDATORY: Check for integer overflow
    size_t buffer_size;
    if (__builtin_mul_overflow(size, 2, &buffer_size)) {
        return ERROR_OVERFLOW;
    }
    
    // Now safe to proceed
    void* buffer = malloc(buffer_size);
    if (!buffer) return ERROR_NO_MEMORY;
    
    // ... process data ...
    
    free(buffer);
    return 0;
}
```

## Section 3: Architecture Standards

### Project Structure

```
django_mercury/c_core/
├── common.h                # Shared structures and utilities
├── common.c                # Cross-platform implementations
├── performance_monitor.c   # Performance monitoring
├── query_analyzer.c        # SQL analysis engine
├── metrics_engine.c        # Metrics calculation
├── test_orchestrator.c     # Test coordination
├── *_wrapper.c            # Python C API wrappers
├── Makefile               # Cross-platform build
└── tests/
    ├── simple_test_*.c    # Unit tests
    ├── comprehensive_*.c  # Integration tests
    ├── edge_test_*.c     # Edge cases
    └── security/         # Security tests
        ├── test_*.c      # Vulnerability tests
        └── *.c          # Attack scenarios
```

### Naming Conventions

```c
// Types: PascalCase with descriptive names
typedef struct {
    uint64_t start_time_ns;
    uint32_t query_count;
    double response_time_ms;
} PerformanceMetrics;

// Functions: module_action pattern
MercuryError mercury_init(void);
TestContext* test_context_create(const char* name);
void performance_monitor_start(Monitor* m);

// Constants: SCREAMING_SNAKE_CASE
#define MERCURY_MAX_BUFFER_SIZE 4096
#define MERCURY_CACHE_LINE_SIZE 64
#define DEFAULT_TIMEOUT_MS 5000

// Enums: PascalCase for type, SCREAMING_SNAKE for values
typedef enum {
    MERCURY_SUCCESS = 0,
    MERCURY_ERROR_NULL_PTR = -1,
    MERCURY_ERROR_NO_MEMORY = -2
} MercuryError;
```

## Section 4: Memory Management

### RAII Pattern (Resource Acquisition Is Initialization)

```c
/**
 * @brief Create a new buffer
 * @param size Initial size in bytes
 * @return Buffer pointer or NULL on failure
 * @note Caller must call buffer_destroy() to free
 */
Buffer* buffer_create(size_t size) {
    Buffer* buf = malloc(sizeof(Buffer));
    if (!buf) return NULL;
    
    buf->data = malloc(size);
    if (!buf->data) {
        free(buf);  // Clean up on failure
        return NULL;
    }
    
    buf->size = size;
    buf->used = 0;
    return buf;
}

/**
 * @brief Destroy buffer and free all resources
 * @param buf Buffer to destroy (may be NULL)
 */
void buffer_destroy(Buffer* buf) {
    if (buf) {
        free(buf->data);  // Free internal resources first
        free(buf);        // Then free container
    }
}
```

### Memory Error Prevention

```c
// ALWAYS check allocations
void* ptr = malloc(size);
if (!ptr) {
    // Log error but don't crash
    log_error("Allocation failed: %zu bytes", size);
    return ERROR_NO_MEMORY;
}

// ALWAYS clear sensitive memory
typedef struct {
    char password[256];
    uint8_t key[32];
} Sensitive;

void sensitive_clear(Sensitive* s) {
    // Use explicit_bzero or SecureZeroMemory
    explicit_bzero(s->password, sizeof(s->password));
    explicit_bzero(s->key, sizeof(s->key));
}

// ALWAYS use calloc for structs with pointers
Context* ctx = calloc(1, sizeof(Context));
// All pointers in ctx are now NULL
```

## Section 5: Error Handling

### Error Code Standards

```c
// Error codes: negative for errors, 0 for success
typedef enum {
    MERCURY_SUCCESS         =  0,
    MERCURY_ERROR_NULL_PTR  = -1,
    MERCURY_ERROR_NO_MEMORY = -2,
    MERCURY_ERROR_INVALID   = -3,
    MERCURY_ERROR_OVERFLOW  = -4,
    MERCURY_ERROR_IO        = -5
} MercuryError;

// Consistent error handling pattern
MercuryError function_that_can_fail(void) {
    void* resource = acquire_resource();
    if (!resource) {
        return MERCURY_ERROR_NO_MEMORY;
    }
    
    MercuryError err = do_operation(resource);
    if (err != MERCURY_SUCCESS) {
        release_resource(resource);  // Clean up on error
        return err;
    }
    
    release_resource(resource);
    return MERCURY_SUCCESS;
}
```

## Section 6: Python Integration

### Python C API Patterns

```c
/**
 * @brief Python wrapper for C functionality
 */
typedef struct {
    PyObject_HEAD
    Monitor* monitor;  // C struct being wrapped
} PyMonitor;

/**
 * @brief Create new Python monitor object
 */
static PyObject* PyMonitor_new(PyTypeObject* type, 
                               PyObject* args, 
                               PyObject* kwds) {
    PyMonitor* self = (PyMonitor*)type->tp_alloc(type, 0);
    if (self) {
        self->monitor = monitor_create();
        if (!self->monitor) {
            Py_DECREF(self);
            PyErr_SetString(PyExc_MemoryError, 
                          "Failed to create monitor");
            return NULL;
        }
    }
    return (PyObject*)self;
}

/**
 * @brief Clean up Python monitor object
 */
static void PyMonitor_dealloc(PyMonitor* self) {
    if (self->monitor) {
        monitor_destroy(self->monitor);
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}
```

## Section 7: Performance Standards

### Optimization Guidelines

```c
// Use branch prediction hints for hot paths
#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)

int process_data(Data* data) {
    // Common case - optimize for this
    if (likely(data && data->valid)) {
        return process_fast_path(data);
    }
    
    // Error case - rare
    if (unlikely(!data)) {
        return ERROR_NULL;
    }
    
    return ERROR_INVALID;
}

// Cache-line alignment for performance
typedef struct MERCURY_ALIGNED(64) {
    // Hot data - accessed frequently
    uint32_t count;
    uint32_t flags;
    double metrics[4];
    
    // Padding to cache line
    uint8_t padding[16];
    
    // Cold data - accessed rarely
    char name[256];
    uint64_t created_at;
} PerfStruct;
```

## Section 8: Testing Requirements

### Django Mercury C Test Runner

**The primary testing tool is `c_test_runner.sh` from the project root:**

```bash
# From anywhere in the project:
./c_test_runner.sh [COMMAND] [OPTIONS]
```

### Available Test Commands

#### Basic Testing
```bash
./c_test_runner.sh test        # Run simple C tests (default)
./c_test_runner.sh coverage    # Run tests with gcov coverage analysis
./c_test_runner.sh all         # Run all tests and coverage
./c_test_runner.sh clean       # Clean test artifacts
```

#### Advanced Testing
```bash
./c_test_runner.sh security    # Run security vulnerability tests 🔒
./c_test_runner.sh enhanced    # Run tests with educational debugging
./c_test_runner.sh benchmark   # Run performance benchmarks
./c_test_runner.sh memcheck    # Run memory safety checks (Linux only)
```

#### Test Options
```bash
--debug         # Enable verbose debug output
--explain       # Enable educational mode with failure explanations
--single TEST   # Run a specific test file
--fix-only      # Only compile with fixes, don't run

# Examples:
./c_test_runner.sh enhanced --debug      # Debug mode
./c_test_runner.sh enhanced --explain    # Educational explanations
./c_test_runner.sh coverage              # Code coverage analysis
```

### Security Testing (`--security`)

**Comprehensive vulnerability testing for:**
- Command injection vulnerabilities
- Buffer overflow protections
- Input validation
- Memory safety
- Format string attacks
- Integer overflow detection

```bash
# Run security tests
./c_test_runner.sh security

# Output includes:
# ✅ All security tests passed!
# ⚠️  SECURITY VULNERABILITIES DETECTED! (if issues found)
```

The security tests exercise the `sec_test` Makefile target which runs all tests in `tests/security/`.

### Coverage Analysis (`coverage`)

**Code coverage with gcov:**
```bash
./c_test_runner.sh coverage

# Generates:
# - Coverage reports per source file
# - Coverage summary with percentages
# - Colorized output showing uncovered lines
# - HTML reports in tests/coverage/
```

Coverage tools included:
- `colorize_gcov.py` - Highlights uncovered code
- `show_coverage_summary.py` - Displays coverage percentages
- `show_uncovered_lines.py` - Lists uncovered lines

### Enhanced Testing Mode (`enhanced`)

**Educational debugging features:**
```bash
./c_test_runner.sh enhanced --explain

# Provides:
# • Detailed failure messages with expected vs actual values
# • Hex dumps for buffer comparisons
# • Query analyzer state inspection
# • Memory leak detection
# • Performance timing information
# • Educational explanations for common issues
```

### Environment Variables

```bash
TEST_DEBUG=1   # Enable debug output in tests
TEST_TRACE=1   # Enable function tracing
FORCE_COLOR=1  # Force colored output (CI environments)
```

### Mandatory Security Test Patterns

Every C module MUST implement these security tests:

```c
// Test null pointer handling
void test_null_inputs(void) {
    assert(create_thing(NULL) == ERROR_NULL);
    assert(process(NULL, NULL) == ERROR_NULL);
}

// Test buffer overflow protection
void test_buffer_overflows(void) {
    char huge[10000];
    memset(huge, 'A', sizeof(huge) - 1);
    huge[sizeof(huge) - 1] = '\0';
    
    void* ctx = create_context();
    int err = process_string(ctx, huge);
    assert(err == ERROR_TOO_LARGE || err == SUCCESS);
    assert(validate_context(ctx) == true);
    destroy_context(ctx);
}

// Test integer overflow detection
void test_integer_overflow(void) {
    assert(allocate_array(SIZE_MAX, SIZE_MAX) == ERROR_OVERFLOW);
}

// Test format string vulnerability protection
void test_format_strings(void) {
    const char* attacks[] = {
        "%s%s%s%s", "%n%n%n", "%.999999s", NULL
    };
    
    for (int i = 0; attacks[i]; i++) {
        assert(process_input(attacks[i]) != ERROR_CRASH);
    }
}
```

### Additional Memory Safety Tools

For deep memory analysis beyond the test runner:

```bash
# AddressSanitizer (compile-time)
gcc -fsanitize=address -g test.c -o test
./test

# Valgrind (runtime analysis)
valgrind --leak-check=full --show-leak-kinds=all ./test

# Undefined Behavior Sanitizer
gcc -fsanitize=undefined test.c -o test
```

### Test Organization

```
django_mercury/c_core/tests/
├── simple_test_*.c        # Unit tests (run with 'test')
├── comprehensive_*.c      # Integration tests
├── edge_test_*.c         # Edge case tests
├── security/             # Security vulnerability tests
│   ├── test_*.c         # Individual security tests
│   └── security_test    # Main security test runner
└── coverage/            # Coverage reports and tools
    ├── colorize_gcov.py
    ├── show_coverage_summary.py
    └── show_uncovered_lines.py
```

### Continuous Integration

```bash
# CI-friendly minimal output
./c_test_runner.sh test 2>&1 | grep -E "PASS|FAIL"

# Full CI validation
./c_test_runner.sh all && ./c_test_runner.sh security
```

## Section 9: Build System

### Makefile Requirements

```makefile
# Platform detection
UNAME_S := $(shell uname -s)

# Base flags - ALWAYS include these
CFLAGS := -std=c11 -fPIC
CFLAGS += -Wall -Wextra -Werror
CFLAGS += -Wstrict-prototypes
CFLAGS += -Wmissing-prototypes
CFLAGS += -Wwrite-strings
CFLAGS += -Wno-unused-parameter

# Security flags - MANDATORY
CFLAGS += -fstack-protector-strong
CFLAGS += -D_FORTIFY_SOURCE=2
CFLAGS += -Wformat -Wformat-security

# Debug build
debug: CFLAGS += -g -O0 -DDEBUG
debug: CFLAGS += -fsanitize=address
debug: CFLAGS += -fsanitize=undefined

# Release build
release: CFLAGS += -O3 -DNDEBUG
release: CFLAGS += -flto -march=native
```

## Section 10: Common Pitfalls

### The "It Compiles" Fallacy

```c
// This compiles but has multiple vulnerabilities
void bad_function(void* data, const char* input) {
    MyStruct* s = (MyStruct*)data;  // Unsafe cast - no validation
    strcpy(s->name, input);          // Buffer overflow
    printf(s->format);               // Format string vulnerability
    free(data);                      // Use after free if used again
}
```

### The "I Checked NULL" False Security

```c
// BAD: Incomplete validation
int process(Context* ctx) {
    if (!ctx) return -1;
    // But ctx->internal could be NULL
    // ctx could be wrong type
    // ctx could be corrupted
}

// GOOD: Complete validation
int process(Context* ctx) {
    if (!ctx) return ERROR_NULL;
    if (ctx->magic != CTX_MAGIC) return ERROR_CORRUPT;
    if (!ctx->initialized) return ERROR_UNINIT;
    if (!ctx->internal) return ERROR_INVALID;
    // Now safe to use
}
```

## Security Checklist

Before committing ANY C code:

- [ ] NO duplicate struct definitions
- [ ] NO strcpy, strcat, sprintf, gets
- [ ] ALL inputs validated for NULL
- [ ] ALL array bounds checked
- [ ] ALL integer operations checked for overflow
- [ ] ALL allocations checked for failure
- [ ] ALL resources freed in error paths
- [ ] ALL functions have Doxygen comments
- [ ] ALL structs have Doxygen comments
- [ ] Security tests pass
- [ ] Valgrind shows no leaks
- [ ] AddressSanitizer shows no errors

## Final Warning

**C is not Python. C is not JavaScript. C is not forgiving.**

Every pointer can be NULL. Every buffer can overflow. Every cast can be wrong. Every allocation can fail. Every integer can overflow.

**Validate everything. Document everything. Test everything.**

The most dangerous bug in our codebase was a simple struct definition mismatch. It looked correct. It compiled. It passed basic tests. It corrupted memory in production.

**In C, paranoia is professionalism.**

---

*Based on real security vulnerabilities found and fixed in Django Mercury Performance Testing Framework*