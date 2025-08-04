/**
 * @file test_feature_parity.c
 * @brief Test feature parity between libperformance.so and libmetrics_engine.so
 * 
 * This test ensures that libmetrics_engine.so has complete feature parity
 * with libperformance.so by testing all 6 previously missing functions.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <dlfcn.h>
#include "../../common.h"
#include "../simple_tests.h"

// Global test counters
int total_tests = 0;
int passed_tests = 0;
int failed_tests = 0;

// Function pointers for the new functions
typedef void (*set_current_session_id_fn)(int64_t);
typedef int64_t (*get_current_session_id_fn)(void);
typedef int (*calculate_n_plus_one_severity_fn)(const MercuryMetrics*);
typedef int (*detect_n_plus_one_pattern_by_count_fn)(const MercuryMetrics*);
typedef int (*estimate_n_plus_one_cause_fn)(const MercuryMetrics*);
typedef const char* (*get_n_plus_one_fix_suggestion_fn)(const MercuryMetrics*);

// Other required function pointers
typedef int64_t (*start_performance_monitoring_enhanced_fn)(const char*, const char*);
typedef MercuryMetrics* (*stop_performance_monitoring_enhanced_fn)(int64_t);
typedef double (*get_elapsed_time_ms_fn)(const MercuryMetrics*);
typedef uint32_t (*get_query_count_fn)(const MercuryMetrics*);
typedef void (*free_metrics_fn)(MercuryMetrics*);

// Library handle and function pointers
static void* lib_handle = NULL;
static set_current_session_id_fn set_current_session_id_func = NULL;
static get_current_session_id_fn get_current_session_id_func = NULL;
static calculate_n_plus_one_severity_fn calculate_n_plus_one_severity_func = NULL;
static detect_n_plus_one_pattern_by_count_fn detect_n_plus_one_pattern_by_count_func = NULL;
static estimate_n_plus_one_cause_fn estimate_n_plus_one_cause_func = NULL;
static get_n_plus_one_fix_suggestion_fn get_n_plus_one_fix_suggestion_func = NULL;

// Helper functions
static start_performance_monitoring_enhanced_fn start_monitoring = NULL;
static stop_performance_monitoring_enhanced_fn stop_monitoring = NULL;
static get_elapsed_time_ms_fn get_elapsed_time = NULL;
static get_query_count_fn get_query_count = NULL;
static free_metrics_fn free_metrics = NULL;

/**
 * @brief Load libmetrics_engine.so and get function pointers
 */
int load_library(void) {
    // Try to load the library
    lib_handle = dlopen("./libmetrics_engine.so", RTLD_LAZY);
    if (!lib_handle) {
        lib_handle = dlopen("../libmetrics_engine.so", RTLD_LAZY);
    }
    if (!lib_handle) {
        lib_handle = dlopen("../../libmetrics_engine.so", RTLD_LAZY);
    }
    
    if (!lib_handle) {
        fprintf(stderr, "Failed to load libmetrics_engine.so: %s\n", dlerror());
        return -1;
    }
    
    // Load the 6 new functions
    set_current_session_id_func = (set_current_session_id_fn)dlsym(lib_handle, "set_current_session_id");
    get_current_session_id_func = (get_current_session_id_fn)dlsym(lib_handle, "get_current_session_id");
    calculate_n_plus_one_severity_func = (calculate_n_plus_one_severity_fn)dlsym(lib_handle, "calculate_n_plus_one_severity");
    detect_n_plus_one_pattern_by_count_func = (detect_n_plus_one_pattern_by_count_fn)dlsym(lib_handle, "detect_n_plus_one_pattern_by_count");
    estimate_n_plus_one_cause_func = (estimate_n_plus_one_cause_fn)dlsym(lib_handle, "estimate_n_plus_one_cause");
    get_n_plus_one_fix_suggestion_func = (get_n_plus_one_fix_suggestion_fn)dlsym(lib_handle, "get_n_plus_one_fix_suggestion");
    
    // Load helper functions
    start_monitoring = (start_performance_monitoring_enhanced_fn)dlsym(lib_handle, "start_performance_monitoring_enhanced");
    stop_monitoring = (stop_performance_monitoring_enhanced_fn)dlsym(lib_handle, "stop_performance_monitoring_enhanced");
    get_elapsed_time = (get_elapsed_time_ms_fn)dlsym(lib_handle, "get_elapsed_time_ms");
    get_query_count = (get_query_count_fn)dlsym(lib_handle, "get_query_count");
    free_metrics = (free_metrics_fn)dlsym(lib_handle, "free_metrics");
    
    // Check all functions loaded
    if (!set_current_session_id_func || !get_current_session_id_func ||
        !calculate_n_plus_one_severity_func || !detect_n_plus_one_pattern_by_count_func ||
        !estimate_n_plus_one_cause_func || !get_n_plus_one_fix_suggestion_func) {
        fprintf(stderr, "Failed to load one or more new functions\n");
        return -1;
    }
    
    if (!start_monitoring || !stop_monitoring || !get_elapsed_time || 
        !get_query_count || !free_metrics) {
        fprintf(stderr, "Failed to load helper functions\n");
        return -1;
    }
    
    return 0;
}

/**
 * @brief Test session ID management functions
 */
int test_session_id_management(void) {
    // Test setting and getting session ID
    int64_t test_id = 12345;
    set_current_session_id_func(test_id);
    int64_t retrieved_id = get_current_session_id_func();
    
    ASSERT(retrieved_id == test_id, "Session ID should match what was set");
    
    // Test with different value
    test_id = 67890;
    set_current_session_id_func(test_id);
    retrieved_id = get_current_session_id_func();
    
    ASSERT(retrieved_id == test_id, "Session ID should update correctly");
    
    return 1;
}

/**
 * @brief Test thread-specific session IDs
 */
void* thread_test_func(void* arg) {
    int64_t thread_id = (int64_t)arg;
    set_current_session_id_func(thread_id);
    usleep(10000); // 10ms
    int64_t retrieved = get_current_session_id_func();
    return (void*)(retrieved == thread_id ? 1 : 0);
}

int test_thread_specific_sessions(void) {
    pthread_t threads[4];
    void* results[4];
    
    // Start threads with different session IDs
    for (int i = 0; i < 4; i++) {
        pthread_create(&threads[i], NULL, thread_test_func, (void*)(int64_t)(1000 + i));
    }
    
    // Wait for threads
    for (int i = 0; i < 4; i++) {
        pthread_join(threads[i], &results[i]);
    }
    
    // Check all threads succeeded
    for (int i = 0; i < 4; i++) {
        ASSERT((int64_t)results[i] == 1, "Thread-specific session ID should be isolated");
    }
    
    return 1;
}

/**
 * @brief Create mock metrics with specified query count!
 */
MercuryMetrics* create_mock_metrics(uint32_t query_count, double response_time) {
    MercuryMetrics* metrics = (MercuryMetrics*)calloc(1, sizeof(MercuryMetrics));
    if (!metrics) return NULL;
    
    // Set up basic fields
    metrics->query_count = query_count;
    // Set start and end time to simulate response time
    metrics->start_time.nanoseconds = 0;
    metrics->end_time.nanoseconds = (uint64_t)(response_time * 1000000);  // Convert ms to ns
    metrics->memory_bytes = 50 * 1024 * 1024;  // 50 MB in bytes
    metrics->cache_hits = 10;
    metrics->cache_misses = 5;
    
    return metrics;
}

/**
 * @brief Test N+1 severity calculation
 */
int test_n_plus_one_severity(void) {
    // Test with no queries
    MercuryMetrics* metrics = create_mock_metrics(0, 100.0);
    int severity = calculate_n_plus_one_severity_func(metrics);
    ASSERT(severity == 0, "No queries should have severity 0");
    free(metrics);
    
    // Test mild N+1 (12 queries)
    metrics = create_mock_metrics(12, 150.0);
    severity = calculate_n_plus_one_severity_func(metrics);
    ASSERT(severity == 1, "12 queries should be mild (severity 1)");
    free(metrics);
    
    // Test moderate N+1 (18 queries)
    metrics = create_mock_metrics(18, 200.0);
    severity = calculate_n_plus_one_severity_func(metrics);
    ASSERT(severity == 2, "18 queries should be moderate (severity 2)");
    free(metrics);
    
    // Test high N+1 (25 queries)
    metrics = create_mock_metrics(25, 300.0);
    severity = calculate_n_plus_one_severity_func(metrics);
    ASSERT(severity == 3, "25 queries should be high (severity 3)");
    free(metrics);
    
    // Test severe N+1 (35 queries)
    metrics = create_mock_metrics(35, 400.0);
    severity = calculate_n_plus_one_severity_func(metrics);
    ASSERT(severity == 4, "35 queries should be severe (severity 4)");
    free(metrics);
    
    // Test critical N+1 (50+ queries)
    metrics = create_mock_metrics(50, 500.0);
    severity = calculate_n_plus_one_severity_func(metrics);
    ASSERT(severity == 5, "50+ queries should be critical (severity 5)");
    free(metrics);
    
    // Test NULL metrics
    severity = calculate_n_plus_one_severity_func(NULL);
    ASSERT(severity == 0, "NULL metrics should return 0");
    
    return 1;
}

/**
 * @brief Test N+1 pattern detection by count
 */
int test_n_plus_one_pattern_detection(void) {
    // Test no N+1 with low query count
    MercuryMetrics* metrics = create_mock_metrics(5, 50.0);
    int has_n_plus_one = detect_n_plus_one_pattern_by_count_func(metrics);
    ASSERT(has_n_plus_one == 0, "5 queries should not trigger N+1 detection");
    free(metrics);
    
    // Test N+1 detection at threshold (12 queries)
    metrics = create_mock_metrics(12, 120.0);
    has_n_plus_one = detect_n_plus_one_pattern_by_count_func(metrics);
    ASSERT(has_n_plus_one == 1, "12 queries should trigger N+1 detection");
    free(metrics);
    
    // Test paginated pattern detection (1 + 20)
    metrics = create_mock_metrics(21, 210.0);
    has_n_plus_one = detect_n_plus_one_pattern_by_count_func(metrics);
    ASSERT(has_n_plus_one == 1, "21 queries (1+20) should be detected as N+1 pattern");
    free(metrics);
    
    // Test paginated pattern detection (1 + 50)
    metrics = create_mock_metrics(51, 510.0);
    has_n_plus_one = detect_n_plus_one_pattern_by_count_func(metrics);
    ASSERT(has_n_plus_one == 1, "51 queries (1+50) should be detected as N+1 pattern");
    free(metrics);
    
    // Test NULL metrics
    has_n_plus_one = detect_n_plus_one_pattern_by_count_func(NULL);
    ASSERT(has_n_plus_one == 0, "NULL metrics should return 0");
    
    return 1;
}

/**
 * @brief Test N+1 cause estimation
 */
int test_n_plus_one_cause_estimation(void) {
    // Test no N+1 cause with low queries
    MercuryMetrics* metrics = create_mock_metrics(5, 50.0);
    int cause = estimate_n_plus_one_cause_func(metrics);
    ASSERT(cause == 0, "Low query count should have no N+1 cause");
    free(metrics);
    
    // Test related model N+1 (12-19 queries)
    metrics = create_mock_metrics(15, 150.0);
    cause = estimate_n_plus_one_cause_func(metrics);
    ASSERT(cause == 2, "15 queries should indicate related model N+1");
    free(metrics);
    
    // Test serializer N+1 (20+ queries, fast)
    metrics = create_mock_metrics(25, 30.0);  // Fast queries
    cause = estimate_n_plus_one_cause_func(metrics);
    ASSERT(cause == 1, "Many fast queries should indicate serializer N+1");
    free(metrics);
    
    // Test foreign key N+1 (30+ queries, slow)
    metrics = create_mock_metrics(35, 150.0);  // Slower queries
    cause = estimate_n_plus_one_cause_func(metrics);
    ASSERT(cause == 3, "Many slow queries should indicate foreign key N+1");
    free(metrics);
    
    // Test complex N+1 (50+ queries)
    metrics = create_mock_metrics(60, 600.0);
    cause = estimate_n_plus_one_cause_func(metrics);
    ASSERT(cause == 4, "Very many queries should indicate complex N+1");
    free(metrics);
    
    // Test NULL metrics
    cause = estimate_n_plus_one_cause_func(NULL);
    ASSERT(cause == 0, "NULL metrics should return 0");
    
    return 1;
}

/**
 * @brief Test N+1 fix suggestions
 */
int test_n_plus_one_fix_suggestions(void) {
    // Test no N+1 suggestion
    MercuryMetrics* metrics = create_mock_metrics(5, 50.0);
    const char* suggestion = get_n_plus_one_fix_suggestion_func(metrics);
    ASSERT(strstr(suggestion, "No N+1") != NULL, "Should suggest no N+1 detected");
    free(metrics);
    
    // Test serializer N+1 suggestion
    metrics = create_mock_metrics(25, 30.0);  // Fast queries
    suggestion = get_n_plus_one_fix_suggestion_func(metrics);
    ASSERT(strstr(suggestion, "Serializer") != NULL, "Should suggest serializer fix");
    ASSERT(strstr(suggestion, "prefetch_related") != NULL, "Should mention prefetch_related");
    free(metrics);
    
    // Test related model N+1 suggestion
    metrics = create_mock_metrics(15, 150.0);
    suggestion = get_n_plus_one_fix_suggestion_func(metrics);
    ASSERT(strstr(suggestion, "Related model") != NULL, "Should suggest related model fix");
    ASSERT(strstr(suggestion, "select_related") != NULL, "Should mention select_related");
    free(metrics);
    
    // Test foreign key N+1 suggestion
    metrics = create_mock_metrics(35, 150.0);
    suggestion = get_n_plus_one_fix_suggestion_func(metrics);
    ASSERT(strstr(suggestion, "Foreign key") != NULL, "Should suggest foreign key fix");
    free(metrics);
    
    // Test complex N+1 suggestion
    metrics = create_mock_metrics(60, 600.0);
    suggestion = get_n_plus_one_fix_suggestion_func(metrics);
    ASSERT(strstr(suggestion, "Complex") != NULL, "Should suggest complex N+1 fix");
    ASSERT(strstr(suggestion, "raw SQL") != NULL, "Should mention raw SQL option");
    free(metrics);
    
    // Test NULL metrics
    suggestion = get_n_plus_one_fix_suggestion_func(NULL);
    ASSERT(suggestion != NULL, "Should return valid string for NULL metrics");
    ASSERT(strstr(suggestion, "No metrics") != NULL, "Should indicate no metrics available");
    
    return 1;
}

/**
 * @brief Test integration with monitoring functions
 */
int test_integration_with_monitoring(void) {
    // Initialize Mercury first
    typedef MercuryError (*init_fn)(void);
    init_fn mercury_init_func = (init_fn)dlsym(lib_handle, "mercury_init");
    if (mercury_init_func) {
        mercury_init_func();
    }
    
    // Start monitoring
    int64_t session_id = start_monitoring("test_operation", "test_type");
    ASSERT(session_id >= 0, "Should start monitoring session (session_id can be 0)");
    
    // Set session ID for thread
    set_current_session_id_func(session_id);
    
    // Verify session ID is set
    int64_t retrieved_id = get_current_session_id_func();
    ASSERT(retrieved_id == session_id, "Session ID should be retrievable");
    
    // Simulate some work
    usleep(10000); // 10ms
    
    // Stop monitoring
    MercuryMetrics* metrics = stop_monitoring(session_id);
    ASSERT(metrics != NULL, "Should return metrics");
    
    // Test N+1 functions with real metrics
    int severity = calculate_n_plus_one_severity_func(metrics);
    ASSERT(severity >= 0 && severity <= 5, "Severity should be in valid range");
    
    const char* suggestion = get_n_plus_one_fix_suggestion_func(metrics);
    ASSERT(suggestion != NULL, "Should return valid suggestion");
    
    // Clean up
    free_metrics(metrics);
    
    return 1;
}

int main(void) {
    TEST_SUITE_START("Feature Parity Tests for libmetrics_engine.so");
    
    // Load the library
    if (load_library() != 0) {
        fprintf(stderr, "Failed to load library - cannot run tests\n");
        return 1;
    }
    
    // Run tests for all 6 missing functions
    RUN_TEST(test_session_id_management);
    RUN_TEST(test_thread_specific_sessions);
    RUN_TEST(test_n_plus_one_severity);
    RUN_TEST(test_n_plus_one_pattern_detection);
    RUN_TEST(test_n_plus_one_cause_estimation);
    RUN_TEST(test_n_plus_one_fix_suggestions);
    RUN_TEST(test_integration_with_monitoring);
    
    // Clean up
    if (lib_handle) {
        dlclose(lib_handle);
    }
    
    TEST_SUITE_END();
    
    return (failed_tests == 0) ? 0 : 1;
}