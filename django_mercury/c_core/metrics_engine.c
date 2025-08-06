/**
 * @file metrics_engine.c
 * @brief High-Performance Metrics Collection Engine
 * 
 * This library implements a high-performance metrics collection engine for the
 * Mercury Performance Testing Framework. It replaces the Python-based metrics
 * collection in monitor.py with optimized C implementations.
 *
 * Key Features:
 * - RDTSC high-resolution timing with nanosecond precision
 * - SIMD-accelerated threshold checking using SSE2/AVX
 * - Native stack frame walking with libunwind
 * - Cache-aligned data structures for optimal performance
 * - Memory-efficient metrics storage and aggregation
 *
 * Performance Target: 67% reduction in metrics collection overhead
 * Memory Usage: Cache-aligned structures for SIMD operations
 */

/* Suppress deprecation warnings on Windows */
#ifdef _MSC_VER
    #define _CRT_SECURE_NO_WARNINGS
#endif

#include "common.h"
#include <stdlib.h>  /* For malloc, free */
#include <string.h>  /* For strcpy, strncpy, strlen */
#include <math.h>    /* For sqrt, fabs */

// Platform-specific includes
#ifdef MERCURY_MACOS
#include <mach/task.h>
#include <mach/mach_init.h>
#endif

#ifdef MERCURY_WINDOWS
#include <windows.h>
#include <psapi.h>  // For PROCESS_MEMORY_COUNTERS and GetProcessMemoryInfo
#endif

// Conditional includes for stack unwinding
// Check if MERCURY_HAS_LIBUNWIND was set by the build system
#ifndef MERCURY_HAS_LIBUNWIND
    // If not set by build system, auto-detect
    #ifdef MERCURY_LINUX
        // Check if libunwind is available
        #ifdef __has_include
            #if __has_include(<libunwind.h>)
                #define MERCURY_HAS_LIBUNWIND 1
            #else
                #define MERCURY_HAS_LIBUNWIND 0
            #endif
        #else
            // Assume libunwind is available on Linux (fallback)
            #define MERCURY_HAS_LIBUNWIND 1
        #endif
    #else
        #define MERCURY_HAS_LIBUNWIND 0
    #endif
#endif

// Include libunwind headers if available
#if MERCURY_HAS_LIBUNWIND
    #define UNW_LOCAL_ONLY
    #include <libunwind.h>
    #include <dlfcn.h>
#endif

// === CONSTANTS ===

#define MAX_ACTIVE_MONITORS 64
#define MAX_METRICS_HISTORY 1000
#define THRESHOLD_CACHE_SIZE 32
#define STACK_TRACE_MAX_DEPTH 16

// Violation flags (bit field)
#define VIOLATION_RESPONSE_TIME  (1ULL << 0)
#define VIOLATION_MEMORY_USAGE   (1ULL << 1)
#define VIOLATION_QUERY_COUNT    (1ULL << 2)
#define VIOLATION_CACHE_RATIO    (1ULL << 3)
#define VIOLATION_N_PLUS_ONE     (1ULL << 4)

// === DATA STRUCTURES ===

/**
 * @struct StackFrame
 * @brief Stack frame information for debugging and profiling
 * 
 * @var StackFrame::address
 * Memory address of the stack frame
 * 
 * @var StackFrame::function_name
 * Name of the function (demangled if C++)
 * 
 * @var StackFrame::file_name
 * Source file containing the function
 * 
 * @var StackFrame::line_number
 * Line number in the source file
 */
typedef struct {
    void* address;
    char function_name[128];
    char file_name[256];
    int line_number;
} StackFrame;

/**
 * @struct ThresholdConfig
 * @brief Performance threshold configuration
 * 
 * SIMD-aligned structure for efficient threshold checking.
 * 
 * @var ThresholdConfig::response_time_ms
 * Maximum allowed response time in milliseconds
 * 
 * @var ThresholdConfig::memory_usage_mb
 * Maximum allowed memory usage in megabytes
 * 
 * @var ThresholdConfig::query_count_max
 * Maximum number of database queries allowed
 * 
 * @var ThresholdConfig::cache_hit_ratio_min
 * Minimum required cache hit ratio (0.0-1.0)
 * 
 * @var ThresholdConfig::flags
 * Configuration flags for enabling/disabling checks
 */
typedef struct MERCURY_ALIGNED(32) {
    double response_time_ms;
    double memory_usage_mb;
    uint32_t query_count_max;
    double cache_hit_ratio_min;
    uint32_t flags;  // Configuration flags
} ThresholdConfig;

// Performance monitor session
typedef struct MERCURY_ALIGNED(64) {
    int64_t session_id;
    MercuryTimestamp start_time;
    MercuryTimestamp end_time;
    
    // Metrics
    uint32_t query_count_start;
    uint32_t query_count_end;
    uint32_t cache_hits;
    uint32_t cache_misses;
    size_t memory_start_bytes;
    size_t memory_peak_bytes;
    size_t memory_end_bytes;
    
    // Configuration
    ThresholdConfig thresholds;
    
    // Context information
    char operation_name[128];
    char operation_type[64];
    
    // Stack trace for error reporting
    StackFrame stack_trace[STACK_TRACE_MAX_DEPTH];
    int stack_depth;
    
    // Status
    uint64_t violation_flags;
    bool is_active;
    
} PerformanceMonitor;

// Global metrics engine state
typedef struct {
    PerformanceMonitor* monitors;
    size_t monitor_count;
    size_t max_monitors;
    
    // Thread synchronization for monitor allocation
    mercury_mutex_t monitor_lock;
    
    // SIMD-aligned threshold cache for fast checking
    ThresholdConfig* threshold_cache;  /* Alignment handled at allocation */
    size_t cache_size;
    
    // Statistics
    MERCURY_ATOMIC(uint64_t) total_sessions;
    MERCURY_ATOMIC(uint64_t) violations_detected;
    MERCURY_ATOMIC(uint64_t) timing_overhead_ns;  // Self-monitoring
    
    // Django hook counters
    MERCURY_ATOMIC(uint64_t) global_query_count;
    MERCURY_ATOMIC(uint64_t) global_cache_hits;
    MERCURY_ATOMIC(uint64_t) global_cache_misses;
    
    // RDTSC calibration
    uint64_t rdtsc_frequency;
    bool rdtsc_available;
    
} MetricsEngine;

// Global engine instance
static MetricsEngine* g_engine = NULL;

// === TIMING UTILITIES ===

// Get current memory usage (RSS) in bytes
static size_t get_memory_usage(void) {
#ifdef MERCURY_LINUX
    FILE* file = fopen("/proc/self/status", "r");
    if (!file) return 0;
    
    char line[256];
    size_t memory_kb = 0;
    
    while (fgets(line, sizeof(line), file)) {
        if (strncmp(line, "VmRSS:", 6) == 0) {
            sscanf(line, "VmRSS: %zu kB", &memory_kb);
            break;
        }
    }
    
    fclose(file);
    return memory_kb * 1024;  // Convert to bytes
    
#elif defined(MERCURY_MACOS)
    // macOS implementation using task_info
    struct task_basic_info info;
    mach_msg_type_number_t info_count = TASK_BASIC_INFO_COUNT;
    
    if (task_info(mach_task_self(), TASK_BASIC_INFO, (task_info_t)&info, &info_count) == KERN_SUCCESS) {
        return info.resident_size;
    }
    return 0;
    
#elif defined(MERCURY_WINDOWS)
    PROCESS_MEMORY_COUNTERS pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))) {
        return pmc.WorkingSetSize;
    }
    return 0;
    
#else
    return 0;  // Fallback for unsupported platforms
#endif
}

// Capture stack trace for error reporting
static int capture_stack_trace(StackFrame* frames, int max_frames) {
    int frame_count = 0;
    
#if defined(MERCURY_LINUX) && MERCURY_HAS_LIBUNWIND
    unw_cursor_t cursor;
    unw_context_t context;
    
    if (unw_getcontext(&context) != 0) {
        return 0;
    }
    
    if (unw_init_local(&cursor, &context) != 0) {
        return 0;
    }
    
    while (frame_count < max_frames && unw_step(&cursor) > 0) {
        StackFrame* frame = &frames[frame_count];
        
        // Get instruction pointer
        unw_word_t ip;
        if (unw_get_reg(&cursor, UNW_REG_IP, &ip) != 0) {
            break;
        }
        frame->address = (void*)ip;
        
        // Get function name
        char func_name[128];
        unw_word_t offset;
        if (unw_get_proc_name(&cursor, func_name, sizeof(func_name), &offset) == 0) {
            strncpy(frame->function_name, func_name, sizeof(frame->function_name) - 1);
            frame->function_name[sizeof(frame->function_name) - 1] = '\0';
        } else {
            strcpy(frame->function_name, "<unknown>");
        }
        
        // Get file and line info using dladdr
        Dl_info dl_info;
        if (dladdr(frame->address, &dl_info) && dl_info.dli_fname) {
            strncpy(frame->file_name, dl_info.dli_fname, sizeof(frame->file_name) - 1);
            frame->file_name[sizeof(frame->file_name) - 1] = '\0';
        } else {
            strcpy(frame->file_name, "<unknown>");
        }
        
        frame->line_number = 0;  // Line numbers require debug info
        frame_count++;
    }
#else
    // Fallback: Use backtrace if available, or create minimal stack info
    if (max_frames > 0 && frames) {
        // Create a minimal stack frame entry
        StackFrame* frame = &frames[0];
        strcpy(frame->function_name, "<capture_stack_trace>");
        strcpy(frame->file_name, "metrics_engine.c");
        frame->address = (void*)capture_stack_trace;
        frame->line_number = __LINE__;
        frame_count = 1;
    }
#endif
    
    return frame_count;
}

// === SIMD THRESHOLD CHECKING ===

#ifdef USE_SIMD
static void check_thresholds_simd_impl(const PerformanceMonitor* monitors, size_t count,
                                       uint64_t* violations) {
    #ifdef MERCURY_X86_64
        // Process 4 monitors at a time using AVX
        size_t simd_count = count & ~3UL;  // Round down to multiple of 4
        
        for (size_t i = 0; i < simd_count; i += 4) {
            // Load response time thresholds
            __m256d response_thresholds = _mm256_set_pd(
                monitors[i+3].thresholds.response_time_ms,
                monitors[i+2].thresholds.response_time_ms,
                monitors[i+1].thresholds.response_time_ms,
                monitors[i+0].thresholds.response_time_ms
            );
            
            // Calculate actual response times
            __m256d response_times = _mm256_set_pd(
                mercury_ns_to_ms(monitors[i+3].end_time.nanoseconds - monitors[i+3].start_time.nanoseconds),
                mercury_ns_to_ms(monitors[i+2].end_time.nanoseconds - monitors[i+2].start_time.nanoseconds),
                mercury_ns_to_ms(monitors[i+1].end_time.nanoseconds - monitors[i+1].start_time.nanoseconds),
                mercury_ns_to_ms(monitors[i+0].end_time.nanoseconds - monitors[i+0].start_time.nanoseconds)
            );
            
            // Compare response times
            __m256d response_violations = _mm256_cmp_pd(response_times, response_thresholds, _CMP_GT_OQ);
            int response_mask = _mm256_movemask_pd(response_violations);
            
            // Load memory thresholds
            __m256d memory_thresholds = _mm256_set_pd(
                monitors[i+3].thresholds.memory_usage_mb,
                monitors[i+2].thresholds.memory_usage_mb,
                monitors[i+1].thresholds.memory_usage_mb,
                monitors[i+0].thresholds.memory_usage_mb
            );
            
            // Calculate actual memory usage
            __m256d memory_usage = _mm256_set_pd(
                (double)monitors[i+3].memory_peak_bytes / (1024.0 * 1024.0),
                (double)monitors[i+2].memory_peak_bytes / (1024.0 * 1024.0),
                (double)monitors[i+1].memory_peak_bytes / (1024.0 * 1024.0),
                (double)monitors[i+0].memory_peak_bytes / (1024.0 * 1024.0)
            );
            
            // Compare memory usage
            __m256d memory_violations = _mm256_cmp_pd(memory_usage, memory_thresholds, _CMP_GT_OQ);
            int memory_mask = _mm256_movemask_pd(memory_violations);
            
            // Set violation flags
            for (int j = 0; j < 4; j++) {
                if (response_mask & (1 << j)) {
                    violations[i + j] |= VIOLATION_RESPONSE_TIME;
                }
                if (memory_mask & (1 << j)) {
                    violations[i + j] |= VIOLATION_MEMORY_USAGE;
                }
            }
        }
        
        // Handle remaining monitors with scalar operations
        for (size_t i = simd_count; i < count; i++) {
            const PerformanceMonitor* monitor = &monitors[i];
            double response_time = mercury_ns_to_ms(monitor->end_time.nanoseconds - monitor->start_time.nanoseconds);
            double memory_mb = (double)monitor->memory_peak_bytes / (1024.0 * 1024.0);
            
            if (response_time > monitor->thresholds.response_time_ms) {
                violations[i] |= VIOLATION_RESPONSE_TIME;
            }
            if (memory_mb > monitor->thresholds.memory_usage_mb) {
                violations[i] |= VIOLATION_MEMORY_USAGE;
            }
        }
    #endif
}
#endif

// Scalar threshold checking (fallback)
#ifndef USE_SIMD
static void check_thresholds_scalar(const PerformanceMonitor* monitors, size_t count,
                                   uint64_t* violations) {
    for (size_t i = 0; i < count; i++) {
        const PerformanceMonitor* monitor = &monitors[i];
        
        // Check response time
        double response_time = mercury_ns_to_ms(monitor->end_time.nanoseconds - monitor->start_time.nanoseconds);
        if (response_time > monitor->thresholds.response_time_ms) {
            violations[i] |= VIOLATION_RESPONSE_TIME;
        }
        
        // Check memory usage
        double memory_mb = (double)monitor->memory_peak_bytes / (1024.0 * 1024.0);
        if (memory_mb > monitor->thresholds.memory_usage_mb) {
            violations[i] |= VIOLATION_MEMORY_USAGE;
        }
        
        // Check query count
        uint32_t query_count = monitor->query_count_end - monitor->query_count_start;
        if (query_count > monitor->thresholds.query_count_max) {
            violations[i] |= VIOLATION_QUERY_COUNT;
        }
        
        // Check cache hit ratio
        uint32_t total_cache_ops = monitor->cache_hits + monitor->cache_misses;
        if (total_cache_ops > 0) {
            double hit_ratio = (double)monitor->cache_hits / (double)total_cache_ops;
            if (hit_ratio < monitor->thresholds.cache_hit_ratio_min) {
                violations[i] |= VIOLATION_CACHE_RATIO;
            }
        }
    }
}
#endif

// === ENGINE INITIALIZATION ===

static MercuryError init_metrics_engine(void) {
    if (g_engine) {
        return MERCURY_SUCCESS;  // Already initialized
    }
    
    g_engine = mercury_aligned_alloc(sizeof(MetricsEngine), 64);
    if (!g_engine) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate metrics engine");
        return MERCURY_ERROR_OUT_OF_MEMORY;
    }
    
    // Initialize monitor pool
    g_engine->max_monitors = MAX_ACTIVE_MONITORS;
    g_engine->monitors = mercury_aligned_alloc(g_engine->max_monitors * sizeof(PerformanceMonitor), 64);
    if (!g_engine->monitors) {
        mercury_aligned_free(g_engine);
        g_engine = NULL;
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate monitor pool");
        return MERCURY_ERROR_OUT_OF_MEMORY;
    }
    
    g_engine->monitor_count = 0;
    
    // Initialize mutex for thread-safe monitor allocation
    MERCURY_MUTEX_INIT(g_engine->monitor_lock);
    
    // Initialize SIMD-aligned threshold cache
    g_engine->cache_size = THRESHOLD_CACHE_SIZE;
    g_engine->threshold_cache = mercury_aligned_alloc(g_engine->cache_size * sizeof(ThresholdConfig), 32);
    if (!g_engine->threshold_cache) {
        mercury_aligned_free(g_engine->monitors);
        mercury_aligned_free(g_engine);
        g_engine = NULL;
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate threshold cache");
        return MERCURY_ERROR_OUT_OF_MEMORY;
    }
    
    // Initialize statistics
    atomic_store(&g_engine->total_sessions, 0);
    atomic_store(&g_engine->violations_detected, 0);
    atomic_store(&g_engine->timing_overhead_ns, 0);
    
    // Initialize Django hook counters
    atomic_store(&g_engine->global_query_count, 0);
    atomic_store(&g_engine->global_cache_hits, 0);
    atomic_store(&g_engine->global_cache_misses, 0);
    
    // Initialize timing
    #ifdef MERCURY_X86_64
    mercury_calibrate_rdtsc();
    g_engine->rdtsc_frequency = mercury_rdtsc_frequency;
    g_engine->rdtsc_available = (g_engine->rdtsc_frequency > 0);
    #else
    g_engine->rdtsc_available = false;
    #endif
    
    // Initialize all monitors as inactive
    for (size_t i = 0; i < g_engine->max_monitors; i++) {
        g_engine->monitors[i].is_active = false;
        g_engine->monitors[i].session_id = -1;
    }
    
    MERCURY_INFO("Metrics engine initialized with %zu monitor slots", g_engine->max_monitors);
    return MERCURY_SUCCESS;
}

static void cleanup_metrics_engine(void) {
    if (!g_engine) return;
    
    // Destroy the mutex before freeing memory
    MERCURY_MUTEX_DESTROY(g_engine->monitor_lock);
    
    mercury_aligned_free(g_engine->threshold_cache);
    mercury_aligned_free(g_engine->monitors);
    mercury_aligned_free(g_engine);
    g_engine = NULL;
    
    MERCURY_INFO("Metrics engine cleaned up");
}

// === PUBLIC API FUNCTIONS ===

// Start performance monitoring session
int64_t start_performance_monitoring_enhanced(const char* operation_name, const char* operation_type) {
    if (!operation_name || !operation_type) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Operation name and type cannot be NULL");
        return -1;
    }
    
    // Initialize engine if needed
    if (!g_engine) {
        if (init_metrics_engine() != MERCURY_SUCCESS) {
            return -1;
        }
    }
    
    // Find available monitor slot - PROTECTED SECTION
    PerformanceMonitor* monitor = NULL;
    int64_t session_id = -1;
    
    MERCURY_MUTEX_LOCK(g_engine->monitor_lock);
    
    for (size_t i = 0; i < g_engine->max_monitors; i++) {
        if (!g_engine->monitors[i].is_active) {
            monitor = &g_engine->monitors[i];
            session_id = (int64_t)i;
            break;
        }
    }
    
    if (!monitor) {
        MERCURY_MUTEX_UNLOCK(g_engine->monitor_lock);
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "No available monitor slots");
        return -1;
    }
    
    // Initialize monitor
    monitor->session_id = session_id;
    monitor->start_time = mercury_get_timestamp();
    monitor->end_time = monitor->start_time;  // Will be updated on stop
    
    // Initialize metrics - capture baseline counters
    monitor->query_count_start = (uint32_t)atomic_load(&g_engine->global_query_count);
    monitor->query_count_end = 0;
    monitor->cache_hits = 0;
    monitor->cache_misses = 0;
    monitor->memory_start_bytes = get_memory_usage();
    monitor->memory_peak_bytes = monitor->memory_start_bytes;
    monitor->memory_end_bytes = 0;
    
    // Set default thresholds
    monitor->thresholds.response_time_ms = 1000.0;  // 1 second default
    monitor->thresholds.memory_usage_mb = 200.0;    // 200MB default
    monitor->thresholds.query_count_max = 50;       // 50 queries default
    monitor->thresholds.cache_hit_ratio_min = 0.7;  // 70% cache hit ratio
    monitor->thresholds.flags = 0;
    
    // Copy operation info
    strncpy(monitor->operation_name, operation_name, sizeof(monitor->operation_name) - 1);
    monitor->operation_name[sizeof(monitor->operation_name) - 1] = '\0';
    strncpy(monitor->operation_type, operation_type, sizeof(monitor->operation_type) - 1);
    monitor->operation_type[sizeof(monitor->operation_type) - 1] = '\0';
    
    // Capture stack trace for context
    monitor->stack_depth = capture_stack_trace(monitor->stack_trace, STACK_TRACE_MAX_DEPTH);
    
    // Initialize status
    monitor->violation_flags = 0;
    monitor->is_active = true;  // Mark active before releasing lock
    
    atomic_fetch_add(&g_engine->total_sessions, 1);
    g_engine->monitor_count++;
    
    MERCURY_MUTEX_UNLOCK(g_engine->monitor_lock);
    
    return session_id;
}

// Stop performance monitoring and return metrics
MercuryMetrics* stop_performance_monitoring_enhanced(int64_t session_id) {
    if (!g_engine || session_id < 0 || session_id >= (int64_t)g_engine->max_monitors) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Invalid session ID");
        return NULL;
    }
    
    PerformanceMonitor* monitor = &g_engine->monitors[session_id];
    
    MERCURY_MUTEX_LOCK(g_engine->monitor_lock);
    
    if (!monitor->is_active || monitor->session_id != session_id) {
        MERCURY_MUTEX_UNLOCK(g_engine->monitor_lock);
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Session not active");
        return NULL;
    }
    
    // Record end time and final metrics
    monitor->end_time = mercury_get_timestamp();
    monitor->memory_end_bytes = get_memory_usage();
    
    // Update peak memory if current is higher
    if (monitor->memory_end_bytes > monitor->memory_peak_bytes) {
        monitor->memory_peak_bytes = monitor->memory_end_bytes;
    }
    
    // Capture final Django hook counters
    monitor->query_count_end = (uint32_t)atomic_load(&g_engine->global_query_count);
    
    // Check thresholds
    uint64_t violations = 0;
    
    #ifdef USE_SIMD
        check_thresholds_simd_impl(monitor, 1, &violations);
    #else
        check_thresholds_scalar(monitor, 1, &violations);
    #endif
    
    monitor->violation_flags = violations;
    if (violations > 0) {
        atomic_fetch_add(&g_engine->violations_detected, 1);
    }
    
    // Create result metrics
    MercuryMetrics* metrics = mercury_aligned_alloc(sizeof(MercuryMetrics), 64);
    if (!metrics) {
        MERCURY_MUTEX_UNLOCK(g_engine->monitor_lock);
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate result metrics");
        return NULL;
    }
    
    // Copy data to result
    metrics->start_time = monitor->start_time;
    metrics->end_time = monitor->end_time;
    metrics->query_count = monitor->query_count_end - monitor->query_count_start;
    metrics->cache_hits = monitor->cache_hits;
    metrics->cache_misses = monitor->cache_misses;
    metrics->memory_bytes = monitor->memory_peak_bytes;
    metrics->violation_flags = monitor->violation_flags;
    
    strncpy(metrics->operation_name, monitor->operation_name, sizeof(metrics->operation_name) - 1);
    metrics->operation_name[sizeof(metrics->operation_name) - 1] = '\0';
    strncpy(metrics->operation_type, monitor->operation_type, sizeof(metrics->operation_type) - 1);
    metrics->operation_type[sizeof(metrics->operation_type) - 1] = '\0';
    
    // Deactivate monitor - PROTECTED SECTION
    monitor->is_active = false;
    monitor->session_id = -1;
    g_engine->monitor_count--;
    
    MERCURY_MUTEX_UNLOCK(g_engine->monitor_lock);
    
    return metrics;
}

// Helper functions for Python integration
double get_elapsed_time_ms(const MercuryMetrics* metrics) {
    if (!metrics) return 0.0;
    return mercury_ns_to_ms(metrics->end_time.nanoseconds - metrics->start_time.nanoseconds);
}

double get_memory_usage_mb(const MercuryMetrics* metrics) {
    if (!metrics) return 0.0;
    return (double)metrics->memory_bytes / (1024.0 * 1024.0);
}

uint32_t get_query_count(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    return metrics->query_count;
}

uint32_t get_cache_hit_count(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    return metrics->cache_hits;
}

uint32_t get_cache_miss_count(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    return metrics->cache_misses;
}

double get_cache_hit_ratio(const MercuryMetrics* metrics) {
    if (!metrics) return 0.0;
    uint32_t total = metrics->cache_hits + metrics->cache_misses;
    return (total > 0) ? (double)metrics->cache_hits / (double)total : 0.0;
}

// N+1 detection functions (would integrate with query analyzer)
int has_n_plus_one_pattern(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    return (metrics->violation_flags & VIOLATION_N_PLUS_ONE) ? 1 : 0;
}

int detect_n_plus_one_severe(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    return (metrics->query_count > 50) ? 1 : 0;
}

int detect_n_plus_one_moderate(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    return (metrics->query_count > 20 && metrics->query_count <= 50) ? 1 : 0;
}

// Get memory delta in megabytes
double get_memory_delta_mb(const MercuryMetrics* metrics) {
    // MercuryMetrics only stores peak memory, not start/end
    // So we can't calculate a true delta - return 0 for compatibility
    return 0.0;
}

// Check if operation is memory intensive
int is_memory_intensive(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    
    // Check if peak memory usage exceeds 100MB
    double memory_mb = (double)metrics->memory_bytes / (1024.0 * 1024.0);
    
    // Consider memory intensive if:
    // - Peak memory > 100MB
    return (memory_mb > 100.0) ? 1 : 0;
}

// Check for poor cache performance
int has_poor_cache_performance(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    
    uint32_t total = metrics->cache_hits + metrics->cache_misses;
    if (total == 0) return 0;  // No cache operations, not poor performance
    
    double hit_ratio = (double)metrics->cache_hits / (double)total;
    
    // Poor cache performance if hit ratio < 70%
    return (hit_ratio < 0.7) ? 1 : 0;
}

// Free metrics memory
void free_metrics(MercuryMetrics* metrics) {
    if (metrics) {
        mercury_aligned_free(metrics);
    }
}

// Increment counters (called by Django hooks)
void increment_query_count(void) {
    if (g_engine) {
        atomic_fetch_add(&g_engine->global_query_count, 1);
    }
}

void increment_cache_hits(void) {
    if (g_engine) {
        atomic_fetch_add(&g_engine->global_cache_hits, 1);
    }
}

void increment_cache_misses(void) {
    if (g_engine) {
        atomic_fetch_add(&g_engine->global_cache_misses, 1);
    }
}

// Reset global counters (called before test execution)
void reset_global_counters(void) {
    if (g_engine) {
        atomic_store(&g_engine->global_query_count, 0);
        atomic_store(&g_engine->global_cache_hits, 0);
        atomic_store(&g_engine->global_cache_misses, 0);
    }
}

// Get engine statistics
void get_engine_statistics(uint64_t* total_sessions, uint64_t* violations_detected,
                          uint64_t* timing_overhead_ns, size_t* active_monitors) {
    if (!g_engine) {
        if (total_sessions) *total_sessions = 0;
        if (violations_detected) *violations_detected = 0;
        if (timing_overhead_ns) *timing_overhead_ns = 0;
        if (active_monitors) *active_monitors = 0;
        return;
    }
    
    if (total_sessions) *total_sessions = atomic_load(&g_engine->total_sessions);
    if (violations_detected) *violations_detected = atomic_load(&g_engine->violations_detected);
    if (timing_overhead_ns) *timing_overhead_ns = atomic_load(&g_engine->timing_overhead_ns);
    if (active_monitors) *active_monitors = g_engine->monitor_count;
}

// === MISSING FUNCTIONS FROM PERFORMANCE_MONITOR.C ===

// Thread-specific storage for current session ID (for compatibility)
static pthread_key_t session_id_key;
static pthread_once_t session_key_once = PTHREAD_ONCE_INIT;

/**
 * @brief Cleanup function for thread-specific session ID storage
 */
static void cleanup_session_id(void* ptr) {
    if (ptr) {
        free(ptr);
    }
}

/**
 * @brief Initialize thread-specific storage key (called once)
 */
static void init_session_key(void) {
    pthread_key_create(&session_id_key, cleanup_session_id);
}

/**
 * @brief Set the current session ID for this thread
 * @param session_id The session ID to set as current for this thread
 * @warning Not thread-safe during initialization - call pthread_once first
 */
void set_current_session_id(int64_t session_id) {
    pthread_once(&session_key_once, init_session_key);
    int64_t* stored_id = malloc(sizeof(int64_t));
    if (stored_id) {
        *stored_id = session_id;
        pthread_setspecific(session_id_key, stored_id);
    }
}

/**
 * @brief Get the current session ID for this thread
 * @return Current session ID, 0 if none set
 * @warning Returns 0 if thread-specific storage not initialized
 */
int64_t get_current_session_id(void) {
    pthread_once(&session_key_once, init_session_key);
    int64_t* stored_id = (int64_t*)pthread_getspecific(session_id_key);
    return stored_id ? *stored_id : 0;
}

/**
 * @brief Calculate N+1 severity level with realistic thresholds
 * 
 * Returns severity level from 0-5 based on query count, adjusted for
 * Django applications with complex user models and relationships.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return Severity level (0=none, 1=mild, 2=moderate, 3=high, 4=severe, 5=critical)
 * @warning Returns 0 if metrics is NULL
 */
int calculate_n_plus_one_severity(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    
    uint32_t query_count = get_query_count(metrics);
    
    // No N+1 issues for 0 queries (static/cached responses)
    if (query_count == 0) return 0;
    
    // Adjusted thresholds to align with realistic Django app needs
    if (query_count >= 50) return 5;  // CRITICAL - extreme N+1 
    if (query_count >= 35) return 4;  // SEVERE - very high query count
    if (query_count >= 25) return 3;  // HIGH - high query count 
    if (query_count >= 18) return 2;  // MODERATE - moderate N+1 issue
    if (query_count >= 12) return 1;  // MILD - potential N+1, investigate
    
    return 0;  // NONE - acceptable for Django apps with profiles/permissions
}

/**
 * @brief Detect N+1 pattern by analyzing query count patterns
 * 
 * @param metrics Pointer to performance metrics structure
 * @return 1 if N+1 pattern detected, 0 otherwise
 * @warning Returns 0 if metrics is NULL
 */
int detect_n_plus_one_pattern_by_count(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    
    uint32_t query_count = get_query_count(metrics);
    
    // Debug logging for false positives
    if (query_count == 0) {
        fprintf(stderr, "DEBUG: detect_n_plus_one_pattern_by_count called with 0 queries\n");
        return 0;  // No N+1 possible with 0 queries
    }
    
    // Pattern detection for list views with individual queries
    if (query_count >= 21 && query_count <= 101) {
        // Likely pattern: 1 query for list + N queries for related data
        // Common in paginated views: 1 + 10, 1 + 20, 1 + 50, etc.
        if ((query_count - 1) % 10 == 0 || 
            (query_count - 1) % 20 == 0 ||
            (query_count - 1) % 25 == 0) {
            return 1;
        }
    }
    
    // Realistic N+1 detection: Django user apps with profiles/permissions typically need 4-8 queries
    // Only flag as N+1 if significantly above normal Django patterns
    if (query_count >= 12) return 1;  // Raised from 3 to 12 for realistic Django apps
    
    return 0;
}

/**
 * @brief Estimate the likely cause of N+1 queries
 * 
 * Analyzes query patterns to determine the most probable cause of N+1 issues.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return Cause code (0=none, 1=serializer, 2=related_model, 3=foreign_key, 4=complex)
 * @warning Returns 0 if metrics is NULL
 */
int estimate_n_plus_one_cause(const MercuryMetrics* metrics) {
    if (!metrics) return 0;
    
    uint32_t query_count = get_query_count(metrics);
    double response_time = get_elapsed_time_ms(metrics);
    
    // Cause classification:
    // 0 = No N+1
    // 1 = Serializer N+1 (many quick queries)
    // 2 = Related model N+1 (moderate queries)
    // 3 = Foreign key N+1 (many queries, slow)
    // 4 = Complex relationship N+1 (very many queries)
    
    // No N+1 issues for 0 queries (static/cached responses) or low query counts
    if (query_count == 0 || query_count < 12) return 0;
    
    double avg_query_time = response_time / query_count;
    
    if (query_count >= 50) return 4;  // Complex relationship N+1
    if (query_count >= 30 && avg_query_time > 2.0) return 3;  // Foreign key N+1
    if (query_count >= 20 && avg_query_time < 2.0) return 1;  // Serializer N+1
    if (query_count >= 12) return 2;   // Related model N+1
    
    return 0;
}

/**
 * @brief Get suggested fix for detected N+1 pattern
 * 
 * Returns human-readable suggestion based on estimated cause of N+1 queries.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return String with optimization suggestion
 * @warning Returns "No metrics available" if metrics is NULL - pointer remains valid
 */
const char* get_n_plus_one_fix_suggestion(const MercuryMetrics* metrics) {
    if (!metrics) return "No metrics available";
    
    int cause = estimate_n_plus_one_cause(metrics);
    
    switch (cause) {
        case 0:
            return "No N+1 detected";
        case 1:
            return "Serializer N+1: Check SerializerMethodField usage, use prefetch_related()";
        case 2:
            return "Related model N+1: Add select_related() for ForeignKey fields";
        case 3:
            return "Foreign key N+1: Use select_related() and check for nested relationship access";
        case 4:
            return "Complex N+1: Review QuerySet optimization, consider using raw SQL or database views";
        default:
            return "Add select_related() and prefetch_related() to your QuerySet";
    }
}

// === LIBRARY INITIALIZATION ===

// Library constructor
MERCURY_CONSTRUCTOR(metrics_engine_init) {
    // MERCURY_INFO("libmetrics_engine.so loaded");  // Too verbose
}

// Library destructor
MERCURY_DESTRUCTOR(metrics_engine_cleanup) {
    cleanup_metrics_engine();
    // MERCURY_INFO("libmetrics_engine.so unloaded");  // Too verbose
}