# Cross-Platform C Compatibility Guide for Django Mercury

*Comprehensive techniques for writing portable C code across Windows, macOS, and Linux*

## Table of Contents
1. [Overview](#overview)
2. [Platform Detection](#platform-detection)
3. [Build System Architecture](#build-system-architecture)
4. [Windows POSIX Compatibility Layer](#windows-posix-compatibility-layer)
5. [Memory Management Across Platforms](#memory-management-across-platforms)
6. [Thread Synchronization](#thread-synchronization)
7. [Time and Performance Measurement](#time-and-performance-measurement)
8. [File System Operations](#file-system-operations)
9. [Python C Extensions](#python-c-extensions)
10. [CI/CD Multi-Platform Strategy](#cicd-multi-platform-strategy)
11. [Platform-Specific Optimizations](#platform-specific-optimizations)
12. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

## Overview

Django Mercury achieves cross-platform C compatibility through:
- **Abstraction layers** for platform-specific APIs
- **Conditional compilation** using preprocessor directives
- **POSIX compatibility shims** for Windows
- **Build system intelligence** adapting to each platform
- **CI/CD validation** across all target platforms

## Platform Detection

### Compile-Time Detection

```c
// common.h - Platform detection macros
#ifdef _WIN32
    #define MERCURY_WINDOWS 1
    #ifdef _WIN64
        #define MERCURY_WINDOWS64 1
    #endif
#elif __APPLE__
    #include <TargetConditionals.h>
    #if TARGET_OS_MAC
        #define MERCURY_MACOS 1
    #endif
#elif __linux__
    #define MERCURY_LINUX 1
#elif __unix__
    #define MERCURY_UNIX 1
#endif

// Architecture detection
#if defined(__x86_64__) || defined(_M_X64)
    #define MERCURY_X86_64 1
#elif defined(__aarch64__) || defined(_M_ARM64)
    #define MERCURY_ARM64 1
#endif
```

### Runtime Detection in Makefile

```makefile
# Makefile - Dynamic platform detection
UNAME_S := $(shell uname -s 2>/dev/null || echo "Unknown")
UNAME_M := $(shell uname -m 2>/dev/null || echo "Unknown")

# Normalize architecture names
ifeq ($(UNAME_M),x86_64)
    ARCH := x86_64
else ifeq ($(UNAME_M),arm64)
    ARCH := arm64
else ifeq ($(UNAME_M),aarch64)
    ARCH := arm64
endif

# Select compiler based on platform
ifeq ($(UNAME_S),Darwin)
    CC := clang
else ifeq ($(UNAME_S),Windows_NT)
    CC := cl
else
    CC := gcc
endif
```

## Build System Architecture

### Platform-Specific Compiler Flags

```makefile
# Base flags for all platforms
CFLAGS := -std=c11 -fPIC -Wall -Wextra

# Linux-specific
ifeq ($(UNAME_S),Linux)
    CFLAGS += -D_GNU_SOURCE -D_POSIX_C_SOURCE=200809L
    LDFLAGS += -ldl -lrt -pthread
    # Optional libunwind for stack traces
    ifneq ($(shell pkg-config --exists libunwind 2>/dev/null && echo "yes"),)
        LDFLAGS += -lunwind
        CFLAGS += -DMERCURY_HAS_LIBUNWIND=1
    endif
endif

# macOS-specific
ifeq ($(UNAME_S),Darwin)
    CFLAGS += -DMERCURY_MACOS=1
    LDFLAGS += -framework CoreFoundation -ldl -pthread
endif

# Windows MSVC
ifeq ($(UNAME_S),Windows_NT)
    CFLAGS := /std:c11 /D_CRT_SECURE_NO_WARNINGS /DMERCURY_WINDOWS=1
    LDFLAGS := /DLL kernel32.lib user32.lib
    OPT_FLAGS := /O2 /GL
    SO_EXT := .dll
else
    SO_EXT := .so
endif
```

### Shared Library Extensions

```makefile
# Platform-specific library extensions
ifeq ($(findstring Windows,$(UNAME_S)),Windows)
    SO_EXT := .dll
else ifeq ($(UNAME_S),Darwin)
    SO_EXT := .dylib
else
    SO_EXT := .so
endif
```

## Windows POSIX Compatibility Layer

### Complete windows_compat.h Implementation

```c
// windows_compat.h - POSIX compatibility for Windows
#ifdef _WIN32

#include <windows.h>
#include <time.h>
#include <stdint.h>

// POSIX thread types
typedef CRITICAL_SECTION pthread_mutex_t;
typedef HANDLE pthread_t;
typedef struct { int dummy; } pthread_attr_t;
typedef struct { int dummy; } pthread_mutexattr_t;

// Thread functions
#define pthread_mutex_init(m, a) (InitializeCriticalSection(m), 0)
#define pthread_mutex_destroy(m) (DeleteCriticalSection(m), 0)
#define pthread_mutex_lock(m) (EnterCriticalSection(m), 0)
#define pthread_mutex_unlock(m) (LeaveCriticalSection(m), 0)

// Time functions
struct timespec {
    time_t tv_sec;
    long tv_nsec;
};

static inline int clock_gettime(int clk_id, struct timespec* tp) {
    LARGE_INTEGER freq, counter;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&counter);
    
    tp->tv_sec = counter.QuadPart / freq.QuadPart;
    tp->tv_nsec = ((counter.QuadPart % freq.QuadPart) * 1000000000) / freq.QuadPart;
    return 0;
}

#define CLOCK_MONOTONIC 1
#define CLOCK_REALTIME 0

// Memory alignment
static inline int posix_memalign(void** memptr, size_t alignment, size_t size) {
    *memptr = _aligned_malloc(size, alignment);
    return (*memptr == NULL) ? ENOMEM : 0;
}

#define aligned_free _aligned_free

// String functions
#define strdup _strdup
#define strcasecmp _stricmp
#define strncasecmp _strnicmp
#define snprintf _snprintf_s

// File operations
#define access _access
#define F_OK 0
#define W_OK 2
#define R_OK 4

// Sleep functions
#define usleep(us) Sleep((us) / 1000)
#define sleep(s) Sleep((s) * 1000)

#endif // _WIN32
```

## Memory Management Across Platforms

### Aligned Memory Allocation

```c
// common.c - Cross-platform aligned allocation
void* mercury_aligned_alloc(size_t size, size_t alignment) {
    void* ptr = NULL;
    
#ifdef _WIN32
    ptr = _aligned_malloc(size, alignment);
#elif defined(__APPLE__)
    // macOS doesn't have aligned_alloc until macOS 10.15
    if (posix_memalign(&ptr, alignment, size) != 0) {
        ptr = NULL;
    }
#else
    // Linux and other POSIX systems
    ptr = aligned_alloc(alignment, size);
#endif
    
    if (!ptr && size > 0) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, 
                         "Failed to allocate %zu bytes with %zu alignment", 
                         size, alignment);
    }
    return ptr;
}

void mercury_aligned_free(void* ptr) {
    if (!ptr) return;
    
#ifdef _WIN32
    _aligned_free(ptr);
#else
    free(ptr);  // Standard free works for aligned_alloc/posix_memalign
#endif
}
```

### Memory Information

```c
// Get available memory across platforms
size_t mercury_get_available_memory(void) {
#ifdef _WIN32
    MEMORYSTATUSEX status;
    status.dwLength = sizeof(status);
    GlobalMemoryStatusEx(&status);
    return status.ullAvailPhys;
#elif defined(__APPLE__)
    int mib[2] = {CTL_HW, HW_MEMSIZE};
    uint64_t memory;
    size_t length = sizeof(memory);
    sysctl(mib, 2, &memory, &length, NULL, 0);
    return memory;
#else  // Linux
    struct sysinfo info;
    sysinfo(&info);
    return info.freeram * info.mem_unit;
#endif
}
```

## Thread Synchronization

### Cross-Platform Mutex Implementation

```c
// common.h - Thread synchronization abstraction
typedef struct {
#ifdef _WIN32
    CRITICAL_SECTION cs;
#else
    pthread_mutex_t mutex;
#endif
} mercury_mutex_t;

// common.c - Implementation
int mercury_mutex_init(mercury_mutex_t* mutex) {
#ifdef _WIN32
    InitializeCriticalSection(&mutex->cs);
    return 0;
#else
    return pthread_mutex_init(&mutex->mutex, NULL);
#endif
}

int mercury_mutex_lock(mercury_mutex_t* mutex) {
#ifdef _WIN32
    EnterCriticalSection(&mutex->cs);
    return 0;
#else
    return pthread_mutex_lock(&mutex->mutex);
#endif
}

int mercury_mutex_unlock(mercury_mutex_t* mutex) {
#ifdef _WIN32
    LeaveCriticalSection(&mutex->cs);
    return 0;
#else
    return pthread_mutex_unlock(&mutex->mutex);
#endif
}

void mercury_mutex_destroy(mercury_mutex_t* mutex) {
#ifdef _WIN32
    DeleteCriticalSection(&mutex->cs);
#else
    pthread_mutex_destroy(&mutex->mutex);
#endif
}
```

## Time and Performance Measurement

### High-Resolution Timing

```c
// Cross-platform high-resolution timer
typedef struct {
#ifdef _WIN32
    LARGE_INTEGER start;
    LARGE_INTEGER frequency;
#else
    struct timespec start;
#endif
} mercury_timer_t;

void mercury_timer_start(mercury_timer_t* timer) {
#ifdef _WIN32
    QueryPerformanceFrequency(&timer->frequency);
    QueryPerformanceCounter(&timer->start);
#else
    clock_gettime(CLOCK_MONOTONIC, &timer->start);
#endif
}

double mercury_timer_elapsed_ms(mercury_timer_t* timer) {
#ifdef _WIN32
    LARGE_INTEGER end;
    QueryPerformanceCounter(&end);
    return ((double)(end.QuadPart - timer->start.QuadPart) * 1000.0) / 
           timer->frequency.QuadPart;
#else
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC, &end);
    return (end.tv_sec - timer->start.tv_sec) * 1000.0 + 
           (end.tv_nsec - timer->start.tv_nsec) / 1000000.0;
#endif
}
```

### CPU Cycle Counting (x86_64)

```c
// RDTSC for precise CPU cycle counting
#ifdef MERCURY_X86_64
static inline uint64_t mercury_rdtsc(void) {
    #ifdef _WIN32
        return __rdtsc();
    #else
        uint32_t lo, hi;
        __asm__ volatile ("rdtsc" : "=a" (lo), "=d" (hi));
        return ((uint64_t)hi << 32) | lo;
    #endif
}
#endif
```

## File System Operations

### Path Handling

```c
// Cross-platform path separator
#ifdef _WIN32
    #define PATH_SEPARATOR "\\"
    #define PATH_SEPARATOR_CHAR '\\'
#else
    #define PATH_SEPARATOR "/"
    #define PATH_SEPARATOR_CHAR '/'
#endif

// Normalize paths for the current platform
void mercury_normalize_path(char* path) {
    if (!path) return;
    
    for (char* p = path; *p; p++) {
#ifdef _WIN32
        if (*p == '/') *p = '\\';
#else
        if (*p == '\\') *p = '/';
#endif
    }
}
```

### File Existence Check

```c
bool mercury_file_exists(const char* path) {
#ifdef _WIN32
    return _access(path, 0) == 0;
#else
    return access(path, F_OK) == 0;
#endif
}
```

## Python C Extensions

### Platform-Specific Module Initialization

```c
// Python module initialization across platforms
#ifdef _WIN32
    #define MERCURY_EXPORT __declspec(dllexport)
#else
    #define MERCURY_EXPORT __attribute__((visibility("default")))
#endif

// Module definition
static struct PyModuleDef mercury_module = {
    PyModuleDef_HEAD_INIT,
    "mercury_core",
    "High-performance C extensions for Django Mercury",
    -1,
    mercury_methods
};

// Module initialization
MERCURY_EXPORT PyObject* PyInit_mercury_core(void) {
    PyObject* module = PyModule_Create(&mercury_module);
    if (!module) return NULL;
    
    // Platform-specific initialization
#ifdef _WIN32
    // Windows-specific setup
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
#endif
    
    return module;
}
```

## CI/CD Multi-Platform Strategy

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Cross-Platform Tests

on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
        
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
    
    - name: Build C extensions
      run: |
        cd django_mercury/c_core
        make clean all
    
    - name: Run tests
      run: |
        ./c_test_runner.sh test
        python -m pytest tests/
```

### cibuildwheel Configuration

```toml
# pyproject.toml - Multi-platform wheel building
[tool.cibuildwheel]
build = "cp38-* cp39-* cp310-* cp311-*"

# Use manylinux_2_34 for modern GLIBC
manylinux-x86_64-image = "manylinux_2_34"
manylinux-aarch64-image = "manylinux_2_34"

# Test command
test-command = "python -c 'import django_mercury.c_core'"

# Windows configuration
[tool.cibuildwheel.windows]
before-build = "pip install delvewheel"
repair-wheel-command = "delvewheel repair -w {dest_dir} {wheel}"

# macOS configuration
[tool.cibuildwheel.macos]
archs = ["x86_64", "arm64", "universal2"]
```

## Platform-Specific Optimizations

### SIMD Support

```c
// Platform and architecture-specific SIMD
#ifdef MERCURY_X86_64
    #ifdef _WIN32
        #include <intrin.h>  // MSVC intrinsics
    #else
        #include <immintrin.h>  // GCC/Clang intrinsics
    #endif
    
    // SSE2/AVX operations
    void mercury_process_simd(float* data, size_t count) {
        #ifdef __AVX__
            // AVX implementation
            for (size_t i = 0; i < count; i += 8) {
                __m256 vec = _mm256_load_ps(&data[i]);
                vec = _mm256_sqrt_ps(vec);
                _mm256_store_ps(&data[i], vec);
            }
        #else
            // SSE2 fallback
            for (size_t i = 0; i < count; i += 4) {
                __m128 vec = _mm_load_ps(&data[i]);
                vec = _mm_sqrt_ps(vec);
                _mm_store_ps(&data[i], vec);
            }
        #endif
    }
#elif defined(MERCURY_ARM64)
    #include <arm_neon.h>
    
    // NEON implementation
    void mercury_process_simd(float* data, size_t count) {
        for (size_t i = 0; i < count; i += 4) {
            float32x4_t vec = vld1q_f32(&data[i]);
            vec = vsqrtq_f32(vec);
            vst1q_f32(&data[i], vec);
        }
    }
#endif
```

### Compiler-Specific Optimizations

```c
// Branch prediction hints
#ifdef __GNUC__
    #define likely(x)   __builtin_expect(!!(x), 1)
    #define unlikely(x) __builtin_expect(!!(x), 0)
#else
    #define likely(x)   (x)
    #define unlikely(x) (x)
#endif

// Function attributes
#ifdef __GNUC__
    #define MERCURY_INLINE __attribute__((always_inline)) inline
    #define MERCURY_NOINLINE __attribute__((noinline))
    #define MERCURY_HOT __attribute__((hot))
    #define MERCURY_COLD __attribute__((cold))
#elif defined(_MSC_VER)
    #define MERCURY_INLINE __forceinline
    #define MERCURY_NOINLINE __declspec(noinline)
    #define MERCURY_HOT
    #define MERCURY_COLD
#else
    #define MERCURY_INLINE inline
    #define MERCURY_NOINLINE
    #define MERCURY_HOT
    #define MERCURY_COLD
#endif
```

## Common Pitfalls and Solutions

### 1. Integer Size Differences

```c
// BAD: Assuming int is 32-bit
int file_size;  // May be 16-bit on embedded systems

// GOOD: Use fixed-width types
#include <stdint.h>
int32_t file_size;  // Always 32-bit
uint64_t large_value;  // Always 64-bit
```

### 2. Endianness Issues

```c
// Detect endianness at compile time
#define IS_BIG_ENDIAN (*(uint16_t*)"\0\1" == 0x0001)

// Portable byte swapping
uint32_t mercury_swap32(uint32_t value) {
#ifdef _MSC_VER
    return _byteswap_ulong(value);
#elif defined(__GNUC__)
    return __builtin_bswap32(value);
#else
    return ((value & 0xFF000000) >> 24) |
           ((value & 0x00FF0000) >> 8) |
           ((value & 0x0000FF00) << 8) |
           ((value & 0x000000FF) << 24);
#endif
}
```

### 3. Line Endings

```c
// Handle both Unix (LF) and Windows (CRLF) line endings
char* mercury_read_line(FILE* file, char* buffer, size_t size) {
    if (!fgets(buffer, size, file)) return NULL;
    
    // Remove any line ending
    size_t len = strlen(buffer);
    while (len > 0 && (buffer[len-1] == '\n' || buffer[len-1] == '\r')) {
        buffer[--len] = '\0';
    }
    return buffer;
}
```

### 4. Dynamic Library Loading

```c
// Cross-platform dynamic library loading
typedef void* mercury_dll_t;

mercury_dll_t mercury_dll_load(const char* path) {
#ifdef _WIN32
    return LoadLibrary(path);
#else
    return dlopen(path, RTLD_LAZY);
#endif
}

void* mercury_dll_symbol(mercury_dll_t dll, const char* name) {
#ifdef _WIN32
    return GetProcAddress((HMODULE)dll, name);
#else
    return dlsym(dll, name);
#endif
}

void mercury_dll_close(mercury_dll_t dll) {
#ifdef _WIN32
    FreeLibrary((HMODULE)dll);
#else
    dlclose(dll);
#endif
}
```

### 5. Stack Size Differences

```c
// Avoid large stack allocations
// BAD: May overflow on Windows (1MB default stack)
void process_data(void) {
    char huge_buffer[10 * 1024 * 1024];  // 10MB on stack!
}

// GOOD: Use heap allocation for large data
void process_data(void) {
    char* buffer = malloc(10 * 1024 * 1024);
    if (!buffer) return;
    // ... use buffer ...
    free(buffer);
}
```

## Testing Cross-Platform Compatibility

### Platform-Specific Test Compilation

```bash
# Test on Linux
gcc -std=c11 -D_GNU_SOURCE test.c -o test_linux

# Test on macOS
clang -std=c11 test.c -o test_macos

# Test on Windows (MSVC)
cl /std:c11 test.c /Fe:test_windows.exe

# Test on Windows (MinGW)
gcc -std=c11 -D__USE_MINGW_ANSI_STDIO test.c -o test_mingw.exe
```

### Automated Cross-Platform Testing Script

```bash
#!/bin/bash
# c_test_runner.sh - Cross-platform test runner

detect_platform() {
    case "$(uname -s)" in
        Linux*)     PLATFORM=Linux;;
        Darwin*)    PLATFORM=Mac;;
        CYGWIN*)    PLATFORM=Windows;;
        MINGW*)     PLATFORM=Windows;;
        MSYS*)      PLATFORM=Windows;;
        *)          PLATFORM=Unknown;;
    esac
    echo "Detected platform: $PLATFORM"
}

run_platform_tests() {
    case "$PLATFORM" in
        Linux)
            make -C django_mercury/c_core clean test
            ;;
        Mac)
            make -C django_mercury/c_core CC=clang clean test
            ;;
        Windows)
            cd django_mercury/c_core
            nmake /f Makefile.win clean test
            ;;
    esac
}

detect_platform
run_platform_tests
```

## Summary

Django Mercury achieves cross-platform compatibility through:

1. **Abstraction Layers**: Platform-specific code isolated in compatibility headers
2. **Conditional Compilation**: Using preprocessor directives for platform-specific code
3. **Build System Intelligence**: Makefile adapts to each platform automatically
4. **POSIX Shims**: Windows compatibility layer for POSIX functions
5. **Fixed-Width Types**: Using stdint.h for consistent integer sizes
6. **CI/CD Validation**: Automated testing on all platforms via GitHub Actions
7. **cibuildwheel**: Automated wheel building for all platforms and Python versions

Key principles:
- **Test on all platforms**: Don't assume portability
- **Use standard types**: Prefer stdint.h types over native types
- **Abstract platform APIs**: Hide platform differences behind common interfaces
- **Document platform requirements**: Be explicit about platform-specific behavior
- **Fail gracefully**: Detect missing features and provide fallbacks

This approach has enabled Django Mercury to run seamlessly on Linux, macOS, and Windows, supporting both x86_64 and ARM64 architectures, with optimized performance on each platform.