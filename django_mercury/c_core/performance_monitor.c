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
 * 
 * ## Thread Safety Guarantees
 * 
 * **Thread-Safe Functions:**
 * - start_performance_monitoring_enhanced() - Protected by slot_mutex
 * - stop_performance_monitoring_enhanced() - Protected by slot_mutex  
 * - increment_*() functions - Per-session mutex protection
 * - All get_*() accessor functions - Read-only after stop_performance_monitoring_enhanced()
 * 
 * **Not Thread-Safe Functions:**
 * - reset_global_counters() - Call only when no other threads are active
 * - free_metrics() - Do not call concurrently with same metrics pointer
 * 
 * **Global Counter Limitations:**
 * Global counters (global_query_count, global_cache_hits, global_cache_misses) 
 * are updated without atomic operations for performance. Use session-specific 
 * counters for accurate concurrent tracking.
 * 
 * **Session Isolation:**
 * Each monitoring session maintains isolated per-session counters protected by
 * individual mutexes, ensuring accurate metrics even under concurrent access.
 * 
 * @author Django Mercury Team
 * @date 2024
 * @version 2.0.0
 */

#include "common.h"

/**
 * @brief Performance metrics structure for enhanced monitoring
 * 
 * Contains comprehensive performance data including timing, memory usage,
 * database queries, and cache statistics for Django operations.
 * Uses per-session counters for proper concurrent session isolation.
 */
typedef struct {
    uint64_t start_time_ns;          /**< Start time in nanoseconds */
    uint64_t end_time_ns;            /**< End time in nanoseconds */
    size_t memory_start_bytes;       /**< Initial memory usage in bytes */
    size_t memory_peak_bytes;        /**< Peak memory usage in bytes */
    size_t memory_end_bytes;         /**< Final memory usage in bytes */
    uint32_t session_query_count;    /**< Per-session database query count */
    uint32_t session_cache_hits;     /**< Per-session cache hits */
    uint32_t session_cache_misses;   /**< Per-session cache misses */
    char operation_name[256];        /**< Name of the operation */
    char operation_type[64];         /**< Type: view, model, serializer, query */
    pthread_mutex_t session_mutex;   /**< Mutex for thread-safe session updates */
    int64_t session_id;              /**< Unique session identifier */
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
 * @warning Not thread-safe - call only when no other threads are active
 */
void reset_global_counters(void) {
    global_query_count = 0;
    global_cache_hits = 0;
    global_cache_misses = 0;
}

// Thread-specific storage for current session ID (PIC-compatible)
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
 * @brief Find active session by session ID
 * @param session_id The session ID to find
 * @return Pointer to session metrics, NULL if not found
 */
static EnhancedPerformanceMetrics_t* find_session_by_id(int64_t session_id) {
    if (session_id <= 0) return NULL;
    
    pthread_mutex_lock(&slot_mutex);
    
    int slot = session_id - 1;  // Convert back to 0-based slot
    EnhancedPerformanceMetrics_t* session = NULL;
    
    if (slot >= 0 && slot < 2048 && active_monitor_slots[slot] == 1 && active_monitors[slot] != NULL) {
        session = active_monitors[slot];
    }
    
    pthread_mutex_unlock(&slot_mutex);
    return session;
}

/**
 * @brief Find active session for current thread using thread-specific session ID
 * @return Pointer to active session metrics, NULL if none found
 */
static EnhancedPerformanceMetrics_t* find_current_session(void) {
    return find_session_by_id(get_current_session_id());
}

/**
 * @brief Increment query counter for current active session (called from Django hooks)
 * @warning Thread-safe for session counters, but global counter updates are not atomic
 */
void increment_query_count(void) {
    // Update global counter for backward compatibility
    global_query_count++;
    
    // Update current session counter for accurate per-session tracking
    EnhancedPerformanceMetrics_t* session = find_current_session();
    if (session != NULL) {
        pthread_mutex_lock(&session->session_mutex);
        session->session_query_count++;
        pthread_mutex_unlock(&session->session_mutex);
    }
}

/**
 * @brief Increment cache hits counter for current active session (called from Django hooks)
 * @warning Thread-safe for session counters, but global counter updates are not atomic
 */
void increment_cache_hits(void) {
    // Update global counter for backward compatibility
    global_cache_hits++;
    
    // Update current session counter for accurate per-session tracking
    EnhancedPerformanceMetrics_t* session = find_current_session();
    if (session != NULL) {
        pthread_mutex_lock(&session->session_mutex);
        session->session_cache_hits++;
        pthread_mutex_unlock(&session->session_mutex);
    }
}

/**
 * @brief Increment cache misses counter for current active session (called from Django hooks)
 * @warning Thread-safe for session counters, but global counter updates are not atomic
 */
void increment_cache_misses(void) {
    // Update global counter for backward compatibility  
    global_cache_misses++;
    
    // Update current session counter for accurate per-session tracking
    EnhancedPerformanceMetrics_t* session = find_current_session();
    if (session != NULL) {
        pthread_mutex_lock(&session->session_mutex);
        session->session_cache_misses++;
        pthread_mutex_unlock(&session->session_mutex);
    }
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
 * 
 * @warning Thread-safe but limited to 2048 concurrent sessions
 * @warning Returns -1 if no slots available or memory allocation fails
 * @warning Caller must call stop_performance_monitoring_enhanced() to free resources
 */
int64_t start_performance_monitoring_enhanced(const char* operation_name, const char* operation_type) {
    if (!operation_name) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Operation name cannot be NULL");
        return -1;
    }
    
    
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
    
    // Use default type if not provided
    const char* type_to_use = operation_type ? operation_type : "unknown";
    strncpy(metrics->operation_type, type_to_use, sizeof(metrics->operation_type) - 1);
    metrics->operation_type[sizeof(metrics->operation_type) - 1] = '\0';
    
    // Initialize session-specific data
    metrics->session_id = slot + 1;  // Use slot+1 as session ID
    
    // Initialize per-session mutex
    if (pthread_mutex_init(&metrics->session_mutex, NULL) != 0) {
        // Clean up on mutex initialization failure
        pthread_mutex_lock(&slot_mutex);
        active_monitor_slots[slot] = 0;
        pthread_mutex_unlock(&slot_mutex);
        free(metrics);
        return -1;
    }
    
    // Capture baseline metrics
    metrics->start_time_ns = get_current_time_ns();
    metrics->end_time_ns = 0;
    metrics->memory_start_bytes = get_memory_usage_bytes();
    metrics->memory_peak_bytes = metrics->memory_start_bytes;
    metrics->memory_end_bytes = 0;
    
    // Initialize per-session counters (start at 0 for isolated tracking)
    metrics->session_query_count = 0;
    metrics->session_cache_hits = 0;
    metrics->session_cache_misses = 0;
    
    // Set this session as the current session for this thread
    int64_t session_id = slot + 1;
    set_current_session_id(session_id);
    
    return session_id;  // Return 1-based handle
}

/**
 * @brief Stop enhanced performance monitoring and finalize metrics
 * 
 * Captures final performance metrics and calculates deltas.
 * Returns pointer to metrics structure for analysis.
 * 
 * @param handle Handle returned by start_performance_monitoring_enhanced
 * @return Pointer to metrics structure, NULL on error
 * 
 * @warning Thread-safe but caller must free returned metrics with free_metrics()
 * @warning Returns NULL for invalid handles or already-stopped sessions
 * @warning Metrics pointer becomes invalid after free_metrics() call
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
    
    // Session counters are already accurate (no delta calculation needed)
    // The session-specific counters already contain the correct isolated values
    
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
 * @warning Not thread-safe - do not call concurrently with same metrics pointer
 * @warning Pointer becomes invalid after this call - do not use after freeing
 */
void free_metrics(EnhancedPerformanceMetrics_t* metrics) {
    if (metrics) {
        // Clean up the session mutex before freeing
        pthread_mutex_destroy(&metrics->session_mutex);
        free(metrics);
    }
}

// --- Performance Metric Accessors ---

/**
 * @brief Get elapsed time in milliseconds  
 * @param metrics Pointer to performance metrics structure
 * @return Elapsed time in milliseconds, -1.0 on error
 * @warning Returns -1.0 if metrics is NULL or monitoring not yet stopped
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
 * @warning Returns -1.0 if metrics is NULL
 */
double get_memory_usage_mb(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return -1.0;
    return (double)metrics->memory_peak_bytes / (1024.0 * 1024.0);
}

/**
 * @brief Get memory usage delta in megabytes
 * @param metrics Pointer to performance metrics structure
 * @return Memory delta in MB (end - start), can be negative
 * @warning Returns -1.0 if metrics is NULL
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
 * @warning Returns 0 if metrics is NULL (cannot distinguish from legitimate 0 queries)
 */
uint32_t get_query_count(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    // Return the session-specific query count (no delta calculation needed)
    return metrics->session_query_count;
}

/**
 * @brief Get number of cache hits during operation
 * @param metrics Pointer to performance metrics structure
 * @return Number of cache hits, 0 on error
 * @warning Returns 0 if metrics is NULL (cannot distinguish from legitimate 0 hits)
 */
uint32_t get_cache_hit_count(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    // Return the session-specific cache hits
    return metrics->session_cache_hits;
}

/**
 * @brief Get number of cache misses during operation
 * @param metrics Pointer to performance metrics structure
 * @return Number of cache misses, 0 on error
 * @warning Returns 0 if metrics is NULL (cannot distinguish from legitimate 0 misses)
 */
uint32_t get_cache_miss_count(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    // Return the session-specific cache misses
    return metrics->session_cache_misses;
}

/**
 * @brief Get cache hit ratio for the operation
 * @param metrics Pointer to performance metrics structure
 * @return Cache hit ratio (0.0-1.0), -1.0 on error, 0.0 if no cache ops
 * @warning Returns -1.0 if metrics is NULL, 0.0 if no cache operations occurred
 */
double get_cache_hit_ratio(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return -1.0;
    
    uint32_t total_cache_ops = metrics->session_cache_hits + metrics->session_cache_misses;
    if (total_cache_ops == 0) return 0.0;
    
    return (double)metrics->session_cache_hits / (double)total_cache_ops;
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
 * @warning Returns 0 if metrics is NULL or query count < 3
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
 * @warning Returns 0 if metrics is NULL or query count is 0
 */
int detect_n_plus_one_severe(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    
    uint32_t query_count = get_query_count(metrics);
    double response_time = get_elapsed_time_ms(metrics);
    
    // Debug logging for false positives
    if (query_count == 0) {
        fprintf(stderr, "DEBUG: detect_n_plus_one_severe called with 0 queries\n");
        fprintf(stderr, "  session_query_count=%u\n", 
                metrics->session_query_count);
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
 * @warning Returns 0 if metrics is NULL
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
 * @warning Returns 0 if metrics is NULL or query count is 0
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
 * @warning Returns 0 if metrics is NULL
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
 * @warning Returns 0 if metrics is NULL
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
 * @warning Returns "No metrics available" if metrics is NULL - pointer remains valid
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
 * @warning Returns 0 if metrics is NULL
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
 * @warning Returns 0 if metrics is NULL
 */
int has_poor_cache_performance(EnhancedPerformanceMetrics_t* metrics) {
    if (!metrics) return 0;
    
    double hit_ratio = get_cache_hit_ratio(metrics);
    uint32_t total_ops = metrics->session_cache_hits + metrics->session_cache_misses;
    
    // Poor cache performance if hit ratio < 70% and significant cache usage
    return (hit_ratio >= 0 && hit_ratio < 0.7 && total_ops > 5);
}