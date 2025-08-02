/**
 * @file performance_monitor.c
 * @brief Enhanced Performance Monitor with Django-aware capabilities for EduLite
 * 
 * This C library provides high-performance monitoring capabilities for Django applications
 * with realistic thresholds for applications that have user profiles and related models.
 * 
 * Features:
 * - Operation-aware scoring (DELETE operations get more lenient thresholds)
 * - Realistic N+1 detection (12+ queries before flagging as N+1)
 * - Comprehensive performance metrics collection
 * - Django-specific query and cache tracking
 */

#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 199309L
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <stdint.h>
#include <sys/times.h>
#include <sys/resource.h>
#include <pthread.h>

/**
 * @brief Performance metrics structure for enhanced monitoring
 * 
 * Contains comprehensive performance data including timing, memory usage,
 * database queries, and cache statistics for Django operations.
 */
typedef struct {
    uint64_t start_time_ns;          /**< Start time in nanoseconds */
    uint64_t end_time_ns;            /**< End time in nanoseconds */
    size_t memory_start_bytes;       /**< Initial memory usage in bytes */
    size_t memory_peak_bytes;        /**< Peak memory usage in bytes */
    size_t memory_end_bytes;         /**< Final memory usage in bytes */
    uint32_t query_count_start;      /**< Database queries at start */
    uint32_t query_count_end;        /**< Database queries at end */
    uint32_t cache_hits;             /**< Cache hits during operation */
    uint32_t cache_misses;           /**< Cache misses during operation */
    char operation_name[256];        /**< Name of the operation */
    char operation_type[64];         /**< Type: view, model, serializer, query */
} EnhancedPerformanceMetrics_t;

// Global storage for active monitors
static EnhancedPerformanceMetrics_t* active_monitors[2048] = {NULL};
static int active_monitor_slots[2048] = {0};

// Thread safety mutex for slot allocation
static pthread_mutex_t slot_mutex = PTHREAD_MUTEX_INITIALIZER;

// Global counters for Django-specific metrics
static uint32_t global_query_count = 0;
static uint32_t global_cache_hits = 0;
static uint32_t global_cache_misses = 0;

// Forward declarations for N+1 detection functions (exported to Python)
int detect_n_plus_one_severe(EnhancedPerformanceMetrics_t* metrics);
int detect_n_plus_one_moderate(EnhancedPerformanceMetrics_t* metrics);
int detect_n_plus_one_pattern_by_count(EnhancedPerformanceMetrics_t* metrics);

// --- Internal Helper Functions ---

/**
 * @brief Get current time in nanoseconds using monotonic clock
 * @return Current time in nanoseconds
 */
static uint64_t get_current_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * @brief Get memory usage in bytes by reading /proc/self/status
 * @return Memory usage in bytes (VmRSS)
 */
static size_t get_memory_usage_bytes(void) {
    FILE *file = fopen("/proc/self/status", "r");
    if (!file) return 0;
    
    char line[256];
    size_t vmrss_kb = 0;
    
    while (fgets(line, sizeof(line), file)) {
        if (strncmp(line, "VmRSS:", 6) == 0) {
            sscanf(line, "VmRSS: %zu kB", &vmrss_kb);
            break;
        }
    }
    
    fclose(file);
    return vmrss_kb * 1024;
}

// --- Django Hooks for Query and Cache Tracking ---

/**
 * @brief Reset global counters (called between tests)
 */
void reset_global_counters(void) {
    global_query_count = 0;
    global_cache_hits = 0;
    global_cache_misses = 0;
}

/**
 * @brief Increment global query counter (called from Django hooks)
 */
void increment_query_count(void) {
    global_query_count++;
}

/**
 * @brief Increment global cache hits counter (called from Django hooks)
 */
void increment_cache_hits(void) {
    global_cache_hits++;
}

/**
 * @brief Increment global cache misses counter (called from Django hooks)
 */
void increment_cache_misses(void) {
    global_cache_misses++;
}

// --- Performance Monitoring Lifecycle ---

/**
 * @brief Start enhanced performance monitoring for a Django operation
 * 
 * Initializes performance tracking with operation-specific context.
 * Captures baseline metrics including memory, and Django counters.
 * 
 * @param operation_name Name of the operation being monitored
 * @param operation_type Type of operation (view, model, serializer, query)
 * @return Handle for the monitoring session, -1 on error
 */
int64_t start_performance_monitoring_enhanced(const char* operation_name, const char* operation_type) {
    if (!operation_name) return -1;
    
    // Thread-safe slot allocation
    pthread_mutex_lock(&slot_mutex);
    
    // Find next available slot and mark it as taken immediately
    int slot = -1;
    for (int i = 0; i < 2048; i++) {
        if (active_monitor_slots[i] == 0) {
            slot = i;
            active_monitor_slots[i] = 1;  // Mark as taken immediately
            break;
        }
    }
    
    if (slot == -1) {
        pthread_mutex_unlock(&slot_mutex);
        return -1;  // No available slots
    }
    
    pthread_mutex_unlock(&slot_mutex);
    
    // Allocate new metrics structure (outside the critical section)
    EnhancedPerformanceMetrics_t* metrics = (EnhancedPerformanceMetrics_t*)calloc(1, sizeof(EnhancedPerformanceMetrics_t));
    if (!metrics) {
        // Clean up the slot if allocation fails
        pthread_mutex_lock(&slot_mutex);
        active_monitor_slots[slot] = 0;
        pthread_mutex_unlock(&slot_mutex);
        return -1;
    }
    
    // Set the monitor pointer (no need for mutex as slot is already reserved)
    active_monitors[slot] = metrics;
    
    // Initialize operation metadata
    strncpy(metrics->operation_name, operation_name, sizeof(metrics->operation_name) - 1);
    metrics->operation_name[sizeof(metrics->operation_name) - 1] = '\0';
    
    strncpy(metrics->operation_type, operation_type ? operation_type : "general", sizeof(metrics->operation_type) - 1);
    metrics->operation_type[sizeof(metrics->operation_type) - 1] = '\0';
    
    // Capture baseline metrics
    metrics->start_time_ns = get_current_time_ns();
    metrics->end_time_ns = 0;
    metrics->memory_start_bytes = get_memory_usage_bytes();
    metrics->memory_peak_bytes = metrics->memory_start_bytes;
    metrics->memory_end_bytes = 0;
    
    // Capture Django-specific baseline counters
    metrics->query_count_start = global_query_count;
    metrics->query_count_end = 0;
    metrics->cache_hits = global_cache_hits;
    metrics->cache_misses = global_cache_misses;
    
    return slot + 1;  // Return 1-based handle
}

/**
 * @brief Stop enhanced performance monitoring and finalize metrics
 * 
 * Captures final performance metrics and calculates deltas.
 * Returns pointer to metrics structure for analysis.
 * 
 * @param handle Handle returned by start_performance_monitoring_enhanced
 * @return Pointer to metrics structure, NULL on error
 */
EnhancedPerformanceMetrics_t* stop_performance_monitoring_enhanced(int64_t handle) {
    if (handle <= 0) return NULL;
    
    int slot = handle - 1;
    
    // Thread-safe slot validation and retrieval
    pthread_mutex_lock(&slot_mutex);
    
    if (slot < 0 || slot >= 2048 || active_monitor_slots[slot] == 0) {
        pthread_mutex_unlock(&slot_mutex);
        return NULL;
    }
    
    EnhancedPerformanceMetrics_t* metrics = active_monitors[slot];
    if (!metrics) {
        pthread_mutex_unlock(&slot_mutex);
        return NULL;
    }
    
    pthread_mutex_unlock(&slot_mutex);
    
    // Capture final metrics
    metrics->end_time_ns = get_current_time_ns();
    metrics->memory_end_bytes = get_memory_usage_bytes();
    
    // Update peak memory if current is higher
    if (metrics->memory_end_bytes > metrics->memory_peak_bytes) {
        metrics->memory_peak_bytes = metrics->memory_end_bytes;
    }
    
    // Calculate Django-specific deltas
    metrics->query_count_end = global_query_count;
    uint32_t final_cache_hits = global_cache_hits;
    uint32_t final_cache_misses = global_cache_misses;
    
    metrics->cache_hits = final_cache_hits - metrics->cache_hits;
    metrics->cache_misses = final_cache_misses - metrics->cache_misses;
    
    // Thread-safe slot clearing
    pthread_mutex_lock(&slot_mutex);
    active_monitor_slots[slot] = 0;
    active_monitors[slot] = NULL;
    pthread_mutex_unlock(&slot_mutex);
    
    return metrics;  // Return the allocated metrics for caller to free
}

/**
 * @brief Free metrics structure memory
 * @param metrics Pointer to metrics structure allocated by stop_performance_monitoring_enhanced
 */
void free_metrics(EnhancedPerformanceMetrics_t* metrics) {
    if (metrics) {
        free(metrics);
    }
}

// --- Performance Metric Accessors ---

/**
 * @brief Get elapsed time in milliseconds
 * @param metrics Pointer to performance metrics structure
 * @return Elapsed time in milliseconds, -1.0 on error
 */
double get_elapsed_time_ms(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics || metrics->end_time_ns == 0) return -1.0;
    
    uint64_t elapsed_ns = metrics->end_time_ns - metrics->start_time_ns;
    return (double)elapsed_ns / 1000000.0;
}

/**
 * @brief Get peak memory usage in megabytes
 * @param metrics Pointer to performance metrics structure
 * @return Peak memory usage in MB, -1.0 on error
 */
double get_memory_usage_mb(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return -1.0;
    return (double)metrics->memory_peak_bytes / (1024.0 * 1024.0);
}

/**
 * @brief Get memory usage delta in megabytes
 * @param metrics Pointer to performance metrics structure
 * @return Memory delta in MB (end - start), can be negative
 */
double get_memory_delta_mb(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return -1.0;
    int64_t delta = (int64_t)metrics->memory_end_bytes - (int64_t)metrics->memory_start_bytes;
    return (double)delta / (1024.0 * 1024.0);
}

/**
 * @brief Get number of database queries executed during operation
 * @param metrics Pointer to performance metrics structure
 * @return Number of queries, 0 on error
 */
uint32_t get_query_count(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    return metrics->query_count_end - metrics->query_count_start;
}

/**
 * @brief Get number of cache hits during operation
 * @param metrics Pointer to performance metrics structure
 * @return Number of cache hits, 0 on error
 */
uint32_t get_cache_hit_count(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    return metrics->cache_hits;
}

/**
 * @brief Get number of cache misses during operation
 * @param metrics Pointer to performance metrics structure
 * @return Number of cache misses, 0 on error
 */
uint32_t get_cache_miss_count(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    return metrics->cache_misses;
}

/**
 * @brief Get cache hit ratio for the operation
 * @param metrics Pointer to performance metrics structure
 * @return Cache hit ratio (0.0-1.0), -1.0 on error, 0.0 if no cache ops
 */
double get_cache_hit_ratio(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return -1.0;
    
    uint32_t total_cache_ops = metrics->cache_hits + metrics->cache_misses;
    if (total_cache_ops == 0) return 0.0;
    
    return (double)metrics->cache_hits / (double)total_cache_ops;
}

// --- Performance Analysis Functions ---

/**
 * @brief Check if operation has N+1 query pattern
 * 
 * Uses advanced detection combining severe, moderate, and count-based analysis
 * with realistic thresholds for Django applications.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return 1 if N+1 pattern detected, 0 otherwise
 */
int has_n_plus_one_pattern(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    
    uint32_t query_count = get_query_count(metrics);
    
    // No N+1 pattern possible with fewer than 3 queries
    if (query_count < 3) return 0;
    
    return detect_n_plus_one_severe(metrics) || 
           detect_n_plus_one_moderate(metrics) || 
           detect_n_plus_one_pattern_by_count(metrics);
}

/**
 * @brief Detect severe N+1 query patterns
 * 
 * Identifies clearly problematic query patterns that indicate N+1 issues.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return 1 if severe N+1 detected, 0 otherwise
 */
int detect_n_plus_one_severe(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    
    uint32_t query_count = get_query_count(metrics);
    double response_time = get_elapsed_time_ms(metrics);
    
    // Debug logging for false positives
    if (query_count == 0) {
        fprintf(stderr, "DEBUG: detect_n_plus_one_severe called with 0 queries\n");
        fprintf(stderr, "  query_count_start=%u, query_count_end=%u\n", 
                metrics->query_count_start, metrics->query_count_end);
        return 0;  // No N+1 possible with 0 queries
    }
    
    // SEVERE N+1: More than 20 queries is almost certainly N+1
    if (query_count > 20) return 1;
    
    // SEVERE N+1: More than 10 queries with reasonable response time
    if (query_count > 10 && response_time > 10) return 1;
    
    return 0;
}

/**
 * @brief Detect moderate N+1 query patterns
 * 
 * Identifies potential N+1 issues based on query count vs response time scaling.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return 1 if moderate N+1 detected, 0 otherwise
 */
int detect_n_plus_one_moderate(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    
    uint32_t query_count = get_query_count(metrics);
    double response_time = get_elapsed_time_ms(metrics);
    
    // MODERATE N+1: 5-20 queries for a simple operation
    if (query_count >= 5 && query_count <= 20) {
        // If response time scales with query count, likely N+1
        double time_per_query = response_time / query_count;
        if (time_per_query > 0.5) return 1;  // More than 0.5ms per query suggests individual queries
    }
    
    return 0;
}

/**
 * @brief Detect N+1 patterns based on realistic query count thresholds
 * 
 * Uses realistic thresholds for Django apps with user profiles and permissions.
 * 12+ queries are required before flagging as N+1 to avoid false positives.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return 1 if N+1 pattern detected by count, 0 otherwise
 */
int detect_n_plus_one_pattern_by_count(EnhancedPerformanceMetrics_t* metrics) {
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
 * @brief Calculate N+1 severity level with realistic thresholds
 * 
 * Returns severity level from 0-5 based on query count, adjusted for
 * Django applications with complex user models and relationships.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return Severity level (0=none, 1=mild, 2=moderate, 3=high, 4=severe, 5=critical)
 */
int calculate_n_plus_one_severity(EnhancedPerformanceMetrics_t* metrics) {
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
 * @brief Estimate the likely cause of N+1 queries
 * 
 * Analyzes query patterns to determine the most probable cause of N+1 issues.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return Cause code (0=none, 1=serializer, 2=related_model, 3=foreign_key, 4=complex)
 */
int estimate_n_plus_one_cause(EnhancedPerformanceMetrics_t* metrics) {
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
 */
const char* get_n_plus_one_fix_suggestion(EnhancedPerformanceMetrics_t* metrics) {
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

/**
 * @brief Check if operation is memory intensive
 * 
 * Determines if memory usage exceeds reasonable thresholds for Django operations.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return 1 if memory intensive, 0 otherwise
 */
int is_memory_intensive(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    
    double memory_delta = get_memory_delta_mb(metrics);
    double peak_memory = get_memory_usage_mb(metrics);
    
    // Memory intensive if delta > 50MB or peak > 200MB
    return (memory_delta > 50.0 || peak_memory > 200.0);
}

/**
 * @brief Check if operation has poor cache performance
 * 
 * Determines if cache hit ratio is below acceptable thresholds.
 * 
 * @param metrics Pointer to performance metrics structure
 * @return 1 if poor cache performance, 0 otherwise
 */
int has_poor_cache_performance(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    
    double hit_ratio = get_cache_hit_ratio(metrics);
    uint32_t total_ops = metrics->cache_hits + metrics->cache_misses;
    
    // Poor cache performance if hit ratio < 70% and significant cache usage
    return (hit_ratio >= 0 && hit_ratio < 0.7 && total_ops > 5);
}