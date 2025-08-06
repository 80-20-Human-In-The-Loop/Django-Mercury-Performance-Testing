/**
 * @file common.h
 * @brief Shared structures and utilities for Mercury Performance Testing Framework
 * 
 * This header contains common data structures, utility functions, and cross-platform
 * compatibility macros used across all three high-performance C libraries:
 * - libquery_analyzer.so
 * - libmetrics_engine.so  
 * - libtest_orchestrator.so
 *
 * Features:
 * - Cross-platform compatibility (Linux, macOS, Windows)
 * - Memory-safe data structures with explicit cleanup
 * - High-performance timing and hashing utilities
 * - SIMD-aware data alignment for optimal performance
 * - Thread-safe atomic operations
 */

#ifndef MERCURY_COMMON_H
#define MERCURY_COMMON_H

/* GLIBC compatibility note: manylinux2014 compatibility is handled
 * via linker wrapping in setup.py when CIBUILDWHEEL=1 */

/* Define feature test macros BEFORE any includes */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif

/* Include Windows compatibility layer */
#include "windows_compat.h"

#include <stdint.h>
#include <stddef.h>
#ifndef _MSC_VER
    #include <stdbool.h>
#else
    // MSVC doesn't have stdbool.h in C mode
    #ifndef __cplusplus
        typedef int bool;
        #define true 1
        #define false 0
    #endif
#endif
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

// Platform detection
#ifdef __linux__
    #define MERCURY_LINUX 1
    #include <unistd.h>
    #include <sys/mman.h>
    #include <fcntl.h>
    #include <time.h>
    #include <pthread.h>
#elif __APPLE__
    #define MERCURY_MACOS 1
    #include <mach/mach_time.h>
    #include <sys/mman.h>
    #include <fcntl.h>
    #include <unistd.h>
    #include <pthread.h>
#elif _WIN32
    #define MERCURY_WINDOWS 1
    #include <windows.h>
#endif

// Architecture detection for SIMD
#ifdef __x86_64__
    #define MERCURY_X86_64 1
    #ifdef USE_SIMD
        #include <immintrin.h>  // SSE2, AVX
    #endif
#elif __aarch64__
    #define MERCURY_ARM64 1
    #ifdef USE_NEON
        #include <arm_neon.h>
    #endif
#endif

// Thread safety and atomic types
#if defined(__STDC_NO_ATOMICS__) || defined(_MSC_VER)
    // For MSVC and systems without atomics, define atomic types directly
    #define MERCURY_ATOMIC(type) type
    #define _Atomic
    
    // Define memory order constants for MSVC
    #ifndef memory_order_relaxed
        #define memory_order_relaxed 0
        #define memory_order_consume 1
        #define memory_order_acquire 2
        #define memory_order_release 3
        #define memory_order_acq_rel 4
        #define memory_order_seq_cst 5
    #endif
    
    // Define atomic operations as regular operations (non-thread-safe fallback)
    #define atomic_load(ptr) (*(ptr))
    #define atomic_store(ptr, val) ((*(ptr)) = (val))
    #define atomic_fetch_add(ptr, val) ((*(ptr)) += (val), (*(ptr)) - (val))
    #define atomic_fetch_sub(ptr, val) ((*(ptr)) -= (val), (*(ptr)) + (val))
    
    // Define explicit atomic operations (ignore memory order for fallback)
    #define atomic_load_explicit(ptr, order) atomic_load(ptr)
    #define atomic_store_explicit(ptr, val, order) atomic_store(ptr, val)
    #define atomic_fetch_add_explicit(ptr, val, order) atomic_fetch_add(ptr, val)
    #define atomic_fetch_sub_explicit(ptr, val, order) atomic_fetch_sub(ptr, val)
    
    // Compare and exchange - simple non-atomic fallback
    #define atomic_compare_exchange_weak_explicit(ptr, expected, desired, succ, fail) \
        ((*(ptr) == *(expected)) ? (*(ptr) = (desired), 1) : (*(expected) = *(ptr), 0))
    
    #ifdef _MSC_VER
        #pragma message("WARNING: Atomic operations not available, thread safety not guaranteed")
    #else
        #warning "Atomic operations not available, thread safety not guaranteed"
    #endif
#else
    // For systems with C11 atomics
    #include <stdatomic.h>
    #define MERCURY_ATOMIC(type) _Atomic(type)
#endif

// Thread synchronization primitives
#ifdef _WIN32
    #include <windows.h>
    typedef CRITICAL_SECTION mercury_mutex_t;
    #define MERCURY_MUTEX_INIT(mutex) InitializeCriticalSection(&(mutex))
    #define MERCURY_MUTEX_LOCK(mutex) EnterCriticalSection(&(mutex))
    #define MERCURY_MUTEX_UNLOCK(mutex) LeaveCriticalSection(&(mutex))
    #define MERCURY_MUTEX_DESTROY(mutex) DeleteCriticalSection(&(mutex))
#else
    #include <pthread.h>
    typedef pthread_mutex_t mercury_mutex_t;
    #define MERCURY_MUTEX_INIT(mutex) pthread_mutex_init(&(mutex), NULL)
    #define MERCURY_MUTEX_LOCK(mutex) pthread_mutex_lock(&(mutex))
    #define MERCURY_MUTEX_UNLOCK(mutex) pthread_mutex_unlock(&(mutex))
    #define MERCURY_MUTEX_DESTROY(mutex) pthread_mutex_destroy(&(mutex))
#endif

// Compiler attributes for optimization
#ifdef __GNUC__
    #define MERCURY_INLINE __attribute__((always_inline)) inline
    #define MERCURY_NOINLINE __attribute__((noinline))
    #define MERCURY_ALIGNED(x) __attribute__((aligned(x)))
    #define MERCURY_PACKED __attribute__((packed))
    #define MERCURY_LIKELY(x) __builtin_expect(!!(x), 1)
    #define MERCURY_UNLIKELY(x) __builtin_expect(!!(x), 0)
    
    // Cache prefetching macros
    #define MERCURY_PREFETCH_READ(addr) __builtin_prefetch((addr), 0, 3)   // Read, high temporal locality
    #define MERCURY_PREFETCH_WRITE(addr) __builtin_prefetch((addr), 1, 3)  // Write, high temporal locality
    #define MERCURY_PREFETCH_READ_LOW(addr) __builtin_prefetch((addr), 0, 1) // Read, low temporal locality
    #define MERCURY_PREFETCH_WRITE_LOW(addr) __builtin_prefetch((addr), 1, 1) // Write, low temporal locality
#elif defined(_MSC_VER)
    // MSVC-specific attributes
    #define MERCURY_INLINE __forceinline
    #define MERCURY_NOINLINE __declspec(noinline)
    #define MERCURY_ALIGNED(x) __declspec(align(x))
    #define MERCURY_PACKED
    #define MERCURY_LIKELY(x) (x)
    #define MERCURY_UNLIKELY(x) (x)
    
    // No-op prefetch for MSVC
    #define MERCURY_PREFETCH_READ(addr) do {} while(0)
    #define MERCURY_PREFETCH_WRITE(addr) do {} while(0)
    #define MERCURY_PREFETCH_READ_LOW(addr) do {} while(0)
    #define MERCURY_PREFETCH_WRITE_LOW(addr) do {} while(0)
#else
    #define MERCURY_INLINE inline
    #define MERCURY_NOINLINE
    #define MERCURY_ALIGNED(x)
    #define MERCURY_PACKED
    #define MERCURY_LIKELY(x) (x)
    #define MERCURY_UNLIKELY(x) (x)
    
    // No-op prefetch for other compilers
    #define MERCURY_PREFETCH_READ(addr) do {} while(0)
    #define MERCURY_PREFETCH_WRITE(addr) do {} while(0)
    #define MERCURY_PREFETCH_READ_LOW(addr) do {} while(0)
    #define MERCURY_PREFETCH_WRITE_LOW(addr) do {} while(0)
#endif

// Constants
#define MERCURY_MAX_STRING_LENGTH 4096
#define MERCURY_MAX_QUERY_LENGTH 8192
#define MERCURY_MAX_STACK_DEPTH 32
#define MERCURY_CACHE_LINE_SIZE 64
#define MERCURY_PAGE_SIZE 4096

// Magic numbers for format validation
#define MERCURY_MAGIC_QUERY 0x51455259   // 'QERY'
#define MERCURY_MAGIC_METRICS 0x4D455452 // 'METR'
#define MERCURY_MAGIC_CONFIG 0x434F4E46  // 'CONF'

// Debug assertions
#ifdef DEBUG
    #define MERCURY_ASSERT(cond, msg) do { \
        if (!(cond)) { \
            fprintf(stderr, "ASSERTION FAILED: %s\n  at %s:%d in %s()\n  condition: %s\n", \
                    (msg), __FILE__, __LINE__, __func__, #cond); \
            abort(); \
        } \
    } while(0)
    
    #define MERCURY_VERIFY_BUFFER(buffer) do { \
        MERCURY_ASSERT((buffer) != NULL, "Buffer is NULL"); \
        MERCURY_ASSERT((buffer)->data != NULL, "Buffer data is NULL"); \
        MERCURY_ASSERT((buffer)->capacity > 0, "Buffer capacity is 0"); \
        MERCURY_ASSERT((buffer)->element_size > 0, "Buffer element size is 0"); \
        size_t count = atomic_load(&(buffer)->count); \
        MERCURY_ASSERT(count <= (buffer)->capacity, "Buffer count exceeds capacity"); \
    } while(0)
#else
    #define MERCURY_ASSERT(cond, msg) ((void)0)
    #define MERCURY_VERIFY_BUFFER(buffer) ((void)0)
#endif

// Error codes
typedef enum {
    MERCURY_SUCCESS = 0,
    MERCURY_ERROR_INVALID_ARGUMENT = -1,
    MERCURY_ERROR_OUT_OF_MEMORY = -2,
    MERCURY_ERROR_BUFFER_OVERFLOW = -3,
    MERCURY_ERROR_INVALID_FORMAT = -4,
    MERCURY_ERROR_IO_ERROR = -5,
    MERCURY_ERROR_NOT_IMPLEMENTED = -6
} MercuryError;

// Performance levels for operation complexity
typedef enum {
    MERCURY_PERF_SIMPLE = 0,    // Single table queries
    MERCURY_PERF_MODERATE = 1,  // Joins, basic relations
    MERCURY_PERF_COMPLEX = 2,   // Multiple joins, subqueries
    MERCURY_PERF_CRITICAL = 3   // Bulk operations, migrations
} MercuryPerfLevel;

// === TIMING UTILITIES ===

/**
 * @struct MercuryTimestamp
 * @brief High-resolution timestamp structure for precise timing
 * 
 * @var MercuryTimestamp::nanoseconds
 * Absolute time in nanoseconds since epoch
 * 
 * @var MercuryTimestamp::sequence
 * Sequence number for ordering events that occur at the same nanosecond
 */
typedef struct MERCURY_ALIGNED(8) {
    uint64_t nanoseconds;
    uint32_t sequence;  // For ordering events
} MercuryTimestamp;

/**
 * @brief Get high-resolution timestamp
 * 
 * Retrieves a high-precision timestamp using the best available
 * platform-specific timing mechanism.
 * 
 * @return MercuryTimestamp containing current time in nanoseconds
 */
static inline MercuryTimestamp mercury_get_timestamp(void) {
    MercuryTimestamp ts = {0};
    
#ifdef MERCURY_LINUX
    struct timespec spec;
    if (clock_gettime(CLOCK_MONOTONIC, &spec) == 0) {
        ts.nanoseconds = (uint64_t)spec.tv_sec * 1000000000ULL + spec.tv_nsec;
    }
#elif defined(MERCURY_MACOS)
    static mach_timebase_info_data_t timebase = {0};
    if (timebase.denom == 0) {
        mach_timebase_info(&timebase);
    }
    uint64_t mach_time = mach_absolute_time();
    ts.nanoseconds = mach_time * timebase.numer / timebase.denom;
#elif defined(MERCURY_WINDOWS)
    LARGE_INTEGER frequency, counter;
    if (QueryPerformanceFrequency(&frequency) && QueryPerformanceCounter(&counter)) {
        ts.nanoseconds = (counter.QuadPart * 1000000000ULL) / frequency.QuadPart;
    }
#endif
    
    return ts;
}

// RDTSC timing for x86_64 (nanosecond precision)
#ifdef MERCURY_X86_64
#ifndef _WIN32
MERCURY_INLINE uint64_t mercury_rdtsc(void) {
    uint32_t lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((uint64_t)hi << 32) | lo;
}
#else
// Windows version using intrinsics
#include <intrin.h>
MERCURY_INLINE uint64_t mercury_rdtsc(void) {
    return __rdtsc();
}
#endif

// Calibrate RDTSC frequency (call once at startup)
extern uint64_t mercury_rdtsc_frequency;
void mercury_calibrate_rdtsc(void);
#endif

// Convert between nanoseconds and milliseconds
MERCURY_INLINE double mercury_ns_to_ms(uint64_t nanoseconds) {
    return (double)nanoseconds / 1000000.0;
}

MERCURY_INLINE uint64_t mercury_ms_to_ns(double milliseconds) {
    return (uint64_t)(milliseconds * 1000000.0);
}

// === HASHING UTILITIES ===

/**
 * @brief FNV-1a hash function for fast string hashing
 * 
 * Implements the FNV-1a (Fowler-Noll-Vo) hash algorithm which provides
 * fast computation with good distribution properties.
 * 
 * @param data Pointer to data to hash
 * @param len Length of data in bytes
 * @return 64-bit hash value
 */
MERCURY_INLINE uint64_t mercury_fnv1a_hash(const char* data, size_t len) {
    const uint64_t FNV_OFFSET_BASIS = 14695981039346656037ULL;
    const uint64_t FNV_PRIME = 1099511628211ULL;
    
    // Defensive programming: handle NULL data gracefully
    if (MERCURY_UNLIKELY(!data)) {
        return FNV_OFFSET_BASIS;  // Return default hash for NULL input
    }
    
    uint64_t hash = FNV_OFFSET_BASIS;
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint8_t)data[i];
        hash *= FNV_PRIME;
    }
    return hash;
}

/**
 * @brief Hash a null-terminated string
 * 
 * Convenience wrapper around mercury_fnv1a_hash for C strings.
 * 
 * @param str Null-terminated string to hash
 * @return 64-bit hash value
 */
MERCURY_INLINE uint64_t mercury_hash_string(const char* str) {
    // Defensive programming: handle NULL string gracefully
    if (MERCURY_UNLIKELY(!str)) {
        return 14695981039346656037ULL;  // Return FNV_OFFSET_BASIS for NULL input
    }
    return mercury_fnv1a_hash(str, strlen(str));
}

// === MEMORY UTILITIES ===

/**
 * @brief Allocate cache-aligned memory
 * 
 * @param size Size in bytes to allocate
 * @param alignment Required alignment (must be power of 2)
 * @return Pointer to aligned memory or NULL on failure
 */
MERCURY_API void* mercury_aligned_alloc(size_t size, size_t alignment);

/**
 * @brief Free memory allocated with mercury_aligned_alloc
 * 
 * @param ptr Pointer returned by mercury_aligned_alloc
 */
MERCURY_API void mercury_aligned_free(void* ptr);

/**
 * @struct MercuryRingBuffer
 * @brief Thread-safe ring buffer for fixed-size circular buffers
 * 
 * @var MercuryRingBuffer::data
 * Pointer to the buffer data
 * 
 * @var MercuryRingBuffer::element_size
 * Size of each element in bytes
 * 
 * @var MercuryRingBuffer::capacity
 * Maximum number of elements
 * 
 * @var MercuryRingBuffer::head
 * Atomic index of the head (write position)
 * 
 * @var MercuryRingBuffer::tail
 * Atomic index of the tail (read position)
 * 
 * @var MercuryRingBuffer::count
 * Atomic count of elements in buffer
 */
typedef struct MERCURY_ALIGNED(MERCURY_CACHE_LINE_SIZE) {
    void* data;
    size_t element_size;
    size_t capacity;
    char padding1[MERCURY_CACHE_LINE_SIZE - (sizeof(void*) + 2*sizeof(size_t))];
    
    // Separate cache lines for atomic variables to prevent false sharing
    MERCURY_ATOMIC(size_t) head;
    char padding2[MERCURY_CACHE_LINE_SIZE - sizeof(size_t)];
    
    MERCURY_ATOMIC(size_t) tail;
    char padding3[MERCURY_CACHE_LINE_SIZE - sizeof(size_t)];
    
    MERCURY_ATOMIC(size_t) count;
    char padding4[MERCURY_CACHE_LINE_SIZE - sizeof(size_t)];
} MercuryRingBuffer;

// Ring buffer operations
MERCURY_API MercuryRingBuffer* mercury_ring_buffer_create(size_t element_size, size_t capacity);
MERCURY_API void mercury_ring_buffer_destroy(MercuryRingBuffer* buffer);
MERCURY_API bool mercury_ring_buffer_push(MercuryRingBuffer* buffer, const void* element);
MERCURY_API bool mercury_ring_buffer_pop(MercuryRingBuffer* buffer, void* element);
MERCURY_API size_t mercury_ring_buffer_size(const MercuryRingBuffer* buffer);
MERCURY_API bool mercury_ring_buffer_is_full(const MercuryRingBuffer* buffer);
MERCURY_API bool mercury_ring_buffer_is_empty(const MercuryRingBuffer* buffer);

// === STRING UTILITIES ===

// Safe string operations
typedef struct {
    char* data;
    size_t length;
    size_t capacity;
} MercuryString;

MERCURY_API MercuryString* mercury_string_create(size_t initial_capacity);
MERCURY_API void mercury_string_destroy(MercuryString* str);
MERCURY_API MercuryError mercury_string_append(MercuryString* str, const char* text);
MERCURY_API MercuryError mercury_string_append_char(MercuryString* str, char c);
MERCURY_API void mercury_string_clear(MercuryString* str);
MERCURY_API const char* mercury_string_cstr(const MercuryString* str);

// Boyer-Moore string matching utilities
typedef struct {
    int bad_char_table[256];
    int* good_suffix_table;
    size_t pattern_length;
} MercuryBoyerMoore;

MERCURY_API MercuryBoyerMoore* mercury_boyer_moore_create(const char* pattern);
MERCURY_API void mercury_boyer_moore_destroy(MercuryBoyerMoore* bm);
MERCURY_API int mercury_boyer_moore_search(const MercuryBoyerMoore* bm, const char* text, 
                              size_t text_length, const char* pattern);

// === SAFE ARITHMETIC ===

// Safe size_t addition with overflow check
static inline bool mercury_safe_add_size(size_t a, size_t b, size_t* result) {
    if (a > SIZE_MAX - b) {
        return false;  // Would overflow
    }
    *result = a + b;
    return true;
}

// Safe size_t multiplication with overflow check
static inline bool mercury_safe_mul_size(size_t a, size_t b, size_t* result) {
    if (a > 0 && b > SIZE_MAX / a) {
        return false;  // Would overflow
    }
    *result = a * b;
    return true;
}

// === ERROR HANDLING ===

// Error context for debugging
typedef struct {
    MercuryError code;
    char message[256];
    const char* function;
    const char* file;
    int line;
} MercuryErrorContext;

// Thread-local error context
// Global error context (removed thread-local for PIC compatibility)
// Note: Thread-local storage is incompatible with Position Independent Code
extern MercuryErrorContext mercury_last_error;

// Set error with context information
#define MERCURY_SET_ERROR(error_code, msg) do { \
    mercury_last_error.code = (error_code); \
    snprintf(mercury_last_error.message, sizeof(mercury_last_error.message), "%s", (msg)); \
    mercury_last_error.function = __func__; \
    mercury_last_error.file = __FILE__; \
    mercury_last_error.line = __LINE__; \
} while(0)

// Get last error
MERCURY_API const MercuryErrorContext* mercury_get_last_error(void);
MERCURY_API void mercury_clear_error(void);

// === PERFORMANCE MONITORING STRUCTURES ===

// Basic performance metrics (cache-aligned for SIMD)
typedef struct MERCURY_ALIGNED(MERCURY_CACHE_LINE_SIZE) {
    MercuryTimestamp start_time;
    MercuryTimestamp end_time;
    uint32_t query_count;
    uint32_t cache_hits;
    uint32_t cache_misses;
    uint64_t memory_bytes;
    uint64_t violation_flags;  // Bit field for threshold violations
    char operation_name[64];
    char operation_type[32];
} MercuryMetrics;

// Query record for analysis
typedef struct MERCURY_ALIGNED(32) {
    char* query_text;
    uint64_t hash;
    double execution_time;
    MercuryTimestamp timestamp;
    int similarity_score;
    uint16_t query_type;  // SELECT, INSERT, UPDATE, DELETE, etc.
    uint16_t flags;       // Various query flags
} MercuryQueryRecord;

// === SIMD UTILITIES ===

#ifdef USE_SIMD
// SIMD-accelerated threshold checking
void mercury_check_thresholds_simd(const MercuryMetrics* metrics, size_t count,
                                  const double* thresholds, uint64_t* violations);

// SIMD-accelerated memory operations
void mercury_memcpy_simd(void* dest, const void* src, size_t size);
int mercury_memcmp_simd(const void* a, const void* b, size_t size);

// SIMD-accelerated string operations
int mercury_string_search_simd(const char* text, size_t text_len, const char* pattern, size_t pattern_len);
#else
// Fallback declarations when SIMD is not available
void mercury_memcpy_simd(void* dest, const void* src, size_t size);
int mercury_string_search_simd(const char* text, size_t text_len, const char* pattern, size_t pattern_len);
#endif

// === MULTI-PATTERN SEARCH ===
// (Available regardless of SIMD support)

#define MERCURY_MAX_PATTERNS 32
#define MERCURY_MAX_PATTERN_LENGTH 64

typedef struct {
    char patterns[MERCURY_MAX_PATTERNS][MERCURY_MAX_PATTERN_LENGTH];
    size_t pattern_lengths[MERCURY_MAX_PATTERNS];
    size_t pattern_count;
    // First character vectors for SIMD comparison
    uint8_t first_chars[MERCURY_MAX_PATTERNS];
    // Bitmasks for quick pattern identification
    uint32_t pattern_masks[256];  // Maps first char to pattern bitmask
} MercuryMultiPatternSearch;

MERCURY_API MercuryMultiPatternSearch* mercury_multi_pattern_create(const char* patterns[], size_t count);
MERCURY_API void mercury_multi_pattern_destroy(MercuryMultiPatternSearch* mps);
MERCURY_API int mercury_multi_pattern_search_simd(const MercuryMultiPatternSearch* mps, const char* text, 
                                     size_t text_len, int* pattern_id);

// === LOGGING AND DEBUGGING ===

typedef enum {
    MERCURY_LOG_DEBUG = 0,
    MERCURY_LOG_INFO = 1,
    MERCURY_LOG_WARN = 2,
    MERCURY_LOG_ERROR = 3
} MercuryLogLevel;

// Logging function (can be overridden)
extern void (*mercury_log_function)(MercuryLogLevel level, const char* format, ...);

// Default console logger
MERCURY_API void mercury_default_logger(MercuryLogLevel level, const char* format, ...);

// Logging macros
#define MERCURY_LOG(level, ...) do { \
    if (mercury_log_function) { \
        mercury_log_function(level, __VA_ARGS__); \
    } \
} while(0)

#ifdef DEBUG
    #define MERCURY_DEBUG(...) MERCURY_LOG(MERCURY_LOG_DEBUG, __VA_ARGS__)
#else
    #define MERCURY_DEBUG(...) do {} while(0)
#endif

#define MERCURY_INFO(...) MERCURY_LOG(MERCURY_LOG_INFO, __VA_ARGS__)
#define MERCURY_WARN(...) MERCURY_LOG(MERCURY_LOG_WARN, __VA_ARGS__)
#define MERCURY_ERROR(...) MERCURY_LOG(MERCURY_LOG_ERROR, __VA_ARGS__)

// === MEMORY POOL TYPES ===

typedef struct memory_block {
    void* data;
    size_t size;
    bool in_use;
    struct memory_block* next;
} memory_block_t;

typedef struct MERCURY_ALIGNED(MERCURY_CACHE_LINE_SIZE) {
    size_t block_size;
    size_t num_blocks;
    char padding1[MERCURY_CACHE_LINE_SIZE - 2*sizeof(size_t)];
    
    // Lock-free atomic stack for available blocks
    MERCURY_ATOMIC(memory_block_t*) free_stack;
    char padding2[MERCURY_CACHE_LINE_SIZE - sizeof(memory_block_t*)];
    
    // Atomic counter for statistics  
    MERCURY_ATOMIC(size_t) free_count;
    char padding3[MERCURY_CACHE_LINE_SIZE - sizeof(size_t)];
    
    // Array of all blocks for cleanup (not used in hot path)
    memory_block_t* all_blocks;
    char padding4[MERCURY_CACHE_LINE_SIZE - sizeof(memory_block_t*)];
} memory_pool_t;

// Memory pool functions
MERCURY_API void memory_pool_init(memory_pool_t* pool, size_t block_size, size_t num_blocks);
MERCURY_API void* memory_pool_alloc(memory_pool_t* pool);
MERCURY_API void memory_pool_free(memory_pool_t* pool, void* ptr);
MERCURY_API void memory_pool_destroy(memory_pool_t* pool);

// === ERROR CHAIN TYPES ===

typedef struct error_node {
    int code;
    char message[256];
    struct error_node* next;
} error_node_t;

typedef struct {
    error_node_t* head;
    int count;
} error_chain_t;

// Error chain functions
MERCURY_API void error_chain_init(error_chain_t* chain);
MERCURY_API void error_chain_add(error_chain_t* chain, int code, const char* format, ...);
MERCURY_API void error_chain_destroy(error_chain_t* chain);

// === INITIALIZATION AND CLEANUP ===

/**
 * @brief Initialize Mercury common utilities
 * 
 * Must be called once per process before using any Mercury functions.
 * Initializes platform-specific resources and calibrates timing.
 * 
 * @return MERCURY_SUCCESS on success, error code otherwise
 */
MERCURY_API MercuryError mercury_init(void);

/**
 * @brief Cleanup Mercury common utilities
 * 
 * Should be called once per process when done using Mercury.
 * Releases any allocated resources.
 */
MERCURY_API void mercury_cleanup(void);

// === PORTABLE CONSTRUCTOR/DESTRUCTOR MACROS ===

/**
 * @brief Portable constructor/destructor attributes
 * 
 * These macros provide cross-platform support for library initialization
 * and cleanup functions that run automatically when a shared library is
 * loaded or unloaded.
 */
#if defined(_MSC_VER)
    // MSVC doesn't support __attribute__((constructor/destructor))
    // Use pragma section and linker directives instead
    #define MERCURY_CONSTRUCTOR(func) \
        static void func(void); \
        static int func##_wrapper(void) { func(); return 0; } \
        __pragma(section(".CRT$XCU",read)) \
        __declspec(allocate(".CRT$XCU")) static int (*func##_)(void) = func##_wrapper; \
        static void func(void)

    #define MERCURY_DESTRUCTOR(func) \
        static void func(void); \
        static int func##_destructor_wrapper(void) { func(); return 0; } \
        __pragma(section(".CRT$XPU",read)) \
        __declspec(allocate(".CRT$XPU")) static int (*func##_)(void) = func##_destructor_wrapper; \
        static void func(void)

#elif defined(__GNUC__) || defined(__clang__)
    // GCC and Clang support __attribute__((constructor/destructor))
    #define MERCURY_CONSTRUCTOR(func) \
        __attribute__((constructor)) static void func(void)
    
    #define MERCURY_DESTRUCTOR(func) \
        __attribute__((destructor)) static void func(void)

#else
    // Fallback: No automatic initialization/cleanup
    #warning "Constructor/destructor attributes not supported on this compiler"
    #define MERCURY_CONSTRUCTOR(func) \
        static void func(void)
    
    #define MERCURY_DESTRUCTOR(func) \
        static void func(void)
#endif

#endif // MERCURY_COMMON_H