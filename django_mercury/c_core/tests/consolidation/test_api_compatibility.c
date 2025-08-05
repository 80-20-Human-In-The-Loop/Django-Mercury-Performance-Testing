/**
 * @file test_api_compatibility.c
 * @brief Test API/ABI compatibility between libperformance.so and libmetrics_engine.so
 * 
 * This test verifies that libmetrics_engine.so exports all the same symbols
 * as libperformance.so and that function signatures are compatible.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include "../../common.h"
#include "../simple_tests.h"

// Global test counters
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

// List of all functions that must be exported by both libraries
const char* required_functions[] = {
    // Core monitoring functions
    "start_performance_monitoring_enhanced",
    "stop_performance_monitoring_enhanced",
    "free_metrics",
    
    // Metric accessor functions
    "get_elapsed_time_ms",
    "get_memory_usage_mb",
    "get_memory_delta_mb",
    "get_query_count",
    "get_cache_hit_count",
    "get_cache_miss_count",
    "get_cache_hit_ratio",
    
    // N+1 detection functions
    "has_n_plus_one_pattern",
    "detect_n_plus_one_severe",
    "detect_n_plus_one_moderate",
    "detect_n_plus_one_pattern_by_count",
    "calculate_n_plus_one_severity",
    "estimate_n_plus_one_cause",
    "get_n_plus_one_fix_suggestion",
    
    // Memory analysis functions
    "is_memory_intensive",
    "has_poor_cache_performance",
    
    // Counter management functions
    "increment_query_count",
    "increment_cache_hits",
    "increment_cache_misses",
    "reset_global_counters",
    
    // Session management functions
    "set_current_session_id",
    "get_current_session_id",
    
    // Common utility functions from common.c
    "mercury_init",
    "mercury_cleanup",
    "mercury_aligned_alloc",
    "mercury_aligned_free",
    "mercury_get_last_error",
    "mercury_clear_error",
    
    NULL  // Sentinel
};

/**
 * @brief Check if a symbol exists in a library
 */
int check_symbol_exists(void* handle, const char* symbol_name) {
    // Clear any existing error
    dlerror();
    
    // Try to get the symbol
    void* symbol = dlsym(handle, symbol_name);
    
    // Check for error
    const char* error = dlerror();
    if (error != NULL) {
        return 0;  // Symbol not found
    }
    
    return symbol != NULL ? 1 : 0;
}

/**
 * @brief Test that all required symbols exist in libmetrics_engine.so
 */
int test_all_symbols_exist(void) {
    // Load libmetrics_engine.so
    void* metrics_handle = dlopen("./libmetrics_engine.so", RTLD_LAZY);
    if (!metrics_handle) {
        metrics_handle = dlopen("../libmetrics_engine.so", RTLD_LAZY);
    }
    if (!metrics_handle) {
        metrics_handle = dlopen("../../libmetrics_engine.so", RTLD_LAZY);
    }
    
    if (!metrics_handle) {
        fprintf(stderr, "Failed to load libmetrics_engine.so: %s\n", dlerror());
        return 0;
    }
    
    // Check each required function
    int all_found = 1;
    for (int i = 0; required_functions[i] != NULL; i++) {
        if (!check_symbol_exists(metrics_handle, required_functions[i])) {
            fprintf(stderr, "Missing symbol in libmetrics_engine.so: %s\n", required_functions[i]);
            all_found = 0;
        }
    }
    
    dlclose(metrics_handle);
    
    ASSERT(all_found == 1, "All required symbols should exist in libmetrics_engine.so");
    return 1;
}

/**
 * @brief Compare symbols between libperformance.so and libmetrics_engine.so
 */
int test_symbol_parity(void) {
    // Try to load both libraries
    void* perf_handle = dlopen("./libperformance.so", RTLD_LAZY);
    if (!perf_handle) {
        perf_handle = dlopen("../libperformance.so", RTLD_LAZY);
    }
    if (!perf_handle) {
        perf_handle = dlopen("../../libperformance.so", RTLD_LAZY);
    }
    
    void* metrics_handle = dlopen("./libmetrics_engine.so", RTLD_LAZY);
    if (!metrics_handle) {
        metrics_handle = dlopen("../libmetrics_engine.so", RTLD_LAZY);
    }
    if (!metrics_handle) {
        metrics_handle = dlopen("../../libmetrics_engine.so", RTLD_LAZY);
    }
    
    if (!metrics_handle) {
        fprintf(stderr, "Failed to load libmetrics_engine.so: %s\n", dlerror());
        return 0;
    }
    
    // If we can't load libperformance.so, that's okay (it might be removed already)
    // Just check that metrics_engine has all required functions
    if (!perf_handle) {
        printf("Note: libperformance.so not found (may be already removed)\n");
        printf("Checking libmetrics_engine.so has all required functions...\n");
        
        int all_found = 1;
        for (int i = 0; required_functions[i] != NULL; i++) {
            if (!check_symbol_exists(metrics_handle, required_functions[i])) {
                fprintf(stderr, "Missing required symbol: %s\n", required_functions[i]);
                all_found = 0;
            }
        }
        
        dlclose(metrics_handle);
        ASSERT(all_found == 1, "libmetrics_engine.so should have all required functions");
        return 1;
    }
    
    // Both libraries loaded - compare symbols
    int parity_ok = 1;
    for (int i = 0; required_functions[i] != NULL; i++) {
        int in_perf = check_symbol_exists(perf_handle, required_functions[i]);
        int in_metrics = check_symbol_exists(metrics_handle, required_functions[i]);
        
        if (in_perf && !in_metrics) {
            fprintf(stderr, "Symbol missing in libmetrics_engine.so: %s\n", required_functions[i]);
            parity_ok = 0;
        }
    }
    
    dlclose(perf_handle);
    dlclose(metrics_handle);
    
    ASSERT(parity_ok == 1, "libmetrics_engine.so should have all symbols from libperformance.so");
    return 1;
}

/**
 * @brief Test function signatures by calling them
 */
int test_function_signatures(void) {
    void* handle = dlopen("./libmetrics_engine.so", RTLD_LAZY);
    if (!handle) {
        handle = dlopen("../libmetrics_engine.so", RTLD_LAZY);
    }
    if (!handle) {
        handle = dlopen("../../libmetrics_engine.so", RTLD_LAZY);
    }
    
    if (!handle) {
        fprintf(stderr, "Failed to load libmetrics_engine.so\n");
        return 0;
    }
    
    // Test core monitoring functions
    typedef int64_t (*start_fn)(const char*, const char*);
    typedef MercuryMetrics* (*stop_fn)(int64_t);
    typedef void (*free_fn)(MercuryMetrics*);
    
    start_fn start_func = (start_fn)dlsym(handle, "start_performance_monitoring_enhanced");
    stop_fn stop_func = (stop_fn)dlsym(handle, "stop_performance_monitoring_enhanced");
    free_fn free_func = (free_fn)dlsym(handle, "free_metrics");
    
    ASSERT(start_func != NULL, "start_performance_monitoring_enhanced should exist");
    ASSERT(stop_func != NULL, "stop_performance_monitoring_enhanced should exist");
    ASSERT(free_func != NULL, "free_metrics should exist");
    
    // Test calling the functions
    int64_t session = start_func("test", "test");
    ASSERT(session >= 0, "Should start monitoring session (session_id can be 0)");
    
    MercuryMetrics* metrics = stop_func(session);
    ASSERT(metrics != NULL, "Should return metrics");
    
    free_func(metrics);
    
    // Test session management functions
    typedef void (*set_session_fn)(int64_t);
    typedef int64_t (*get_session_fn)(void);
    
    set_session_fn set_session = (set_session_fn)dlsym(handle, "set_current_session_id");
    get_session_fn get_session = (get_session_fn)dlsym(handle, "get_current_session_id");
    
    ASSERT(set_session != NULL, "set_current_session_id should exist");
    ASSERT(get_session != NULL, "get_current_session_id should exist");
    
    // Test calling session functions
    set_session(42);
    int64_t retrieved = get_session();
    ASSERT(retrieved == 42, "Session functions should work correctly");
    
    dlclose(handle);
    return 1;
}

/**
 * @brief Test that N+1 detection functions work identically
 */
int test_n_plus_one_function_behavior(void) {
    void* handle = dlopen("./libmetrics_engine.so", RTLD_LAZY);
    if (!handle) {
        handle = dlopen("../libmetrics_engine.so", RTLD_LAZY);
    }
    if (!handle) {
        handle = dlopen("../../libmetrics_engine.so", RTLD_LAZY);
    }
    
    if (!handle) {
        fprintf(stderr, "Failed to load libmetrics_engine.so\n");
        return 0;
    }
    
    // Get function pointers
    typedef int (*severity_fn)(const MercuryMetrics*);
    typedef int (*detect_fn)(const MercuryMetrics*);
    typedef const char* (*suggestion_fn)(const MercuryMetrics*);
    
    severity_fn calc_severity = (severity_fn)dlsym(handle, "calculate_n_plus_one_severity");
    detect_fn detect_pattern = (detect_fn)dlsym(handle, "detect_n_plus_one_pattern_by_count");
    suggestion_fn get_suggestion = (suggestion_fn)dlsym(handle, "get_n_plus_one_fix_suggestion");
    
    ASSERT(calc_severity != NULL, "calculate_n_plus_one_severity should exist");
    ASSERT(detect_pattern != NULL, "detect_n_plus_one_pattern_by_count should exist");
    ASSERT(get_suggestion != NULL, "get_n_plus_one_fix_suggestion should exist");
    
    // Create mock metrics
    MercuryMetrics metrics = {0};
    metrics.query_count = 25;
    // Set elapsed time through start/end times
    metrics.start_time.nanoseconds = 0;
    metrics.end_time.nanoseconds = 250000000;  // 250ms in nanoseconds
    
    // Test functions work
    int severity = calc_severity(&metrics);
    ASSERT(severity == 3, "Should calculate correct severity for 25 queries");
    
    int has_pattern = detect_pattern(&metrics);
    ASSERT(has_pattern == 1, "Should detect N+1 pattern for 25 queries");
    
    const char* suggestion = get_suggestion(&metrics);
    ASSERT(suggestion != NULL, "Should return valid suggestion");
    ASSERT(strlen(suggestion) > 0, "Suggestion should not be empty");
    
    dlclose(handle);
    return 1;
}

/**
 * @brief Test memory management functions
 */
int test_memory_functions(void) {
    void* handle = dlopen("./libmetrics_engine.so", RTLD_LAZY);
    if (!handle) {
        handle = dlopen("../libmetrics_engine.so", RTLD_LAZY);
    }
    if (!handle) {
        handle = dlopen("../../libmetrics_engine.so", RTLD_LAZY);
    }
    
    if (!handle) {
        fprintf(stderr, "Failed to load libmetrics_engine.so\n");
        return 0;
    }
    
    // Test mercury_aligned_alloc and mercury_aligned_free
    typedef void* (*alloc_fn)(size_t, size_t);
    typedef void (*free_fn)(void*);
    
    alloc_fn aligned_alloc = (alloc_fn)dlsym(handle, "mercury_aligned_alloc");
    free_fn aligned_free = (free_fn)dlsym(handle, "mercury_aligned_free");
    
    ASSERT(aligned_alloc != NULL, "mercury_aligned_alloc should exist");
    ASSERT(aligned_free != NULL, "mercury_aligned_free should exist");
    
    // Test allocation
    void* ptr = aligned_alloc(1024, 64);
    ASSERT(ptr != NULL, "Should allocate aligned memory");
    ASSERT(((uintptr_t)ptr % 64) == 0, "Memory should be 64-byte aligned");
    
    // Test free
    aligned_free(ptr);  // Should not crash
    
    dlclose(handle);
    return 1;
}

/**
 * @brief Test counter increment functions
 */
int test_counter_functions(void) {
    void* handle = dlopen("./libmetrics_engine.so", RTLD_LAZY);
    if (!handle) {
        handle = dlopen("../libmetrics_engine.so", RTLD_LAZY);
    }
    if (!handle) {
        handle = dlopen("../../libmetrics_engine.so", RTLD_LAZY);
    }
    
    if (!handle) {
        fprintf(stderr, "Failed to load libmetrics_engine.so\n");
        return 0;
    }
    
    typedef void (*increment_fn)(void);
    typedef void (*reset_fn)(void);
    
    increment_fn inc_query = (increment_fn)dlsym(handle, "increment_query_count");
    increment_fn inc_hits = (increment_fn)dlsym(handle, "increment_cache_hits");
    increment_fn inc_misses = (increment_fn)dlsym(handle, "increment_cache_misses");
    reset_fn reset = (reset_fn)dlsym(handle, "reset_global_counters");
    
    ASSERT(inc_query != NULL, "increment_query_count should exist");
    ASSERT(inc_hits != NULL, "increment_cache_hits should exist");
    ASSERT(inc_misses != NULL, "increment_cache_misses should exist");
    ASSERT(reset != NULL, "reset_global_counters should exist");
    
    // Test calling functions (should not crash)
    reset();
    inc_query();
    inc_hits();
    inc_misses();
    
    dlclose(handle);
    return 1;
}

int main(void) {
    QUIET_MODE_INIT();  // Initialize quiet mode from TEST_VERBOSE env var
    TEST_SUITE_START("API/ABI Compatibility Tests");
    
    RUN_TEST(test_all_symbols_exist);
    RUN_TEST(test_symbol_parity);
    RUN_TEST(test_function_signatures);
    RUN_TEST(test_n_plus_one_function_behavior);
    RUN_TEST(test_memory_functions);
    RUN_TEST(test_counter_functions);
    
    TEST_SUITE_END();
    
    return (failed_tests == 0) ? 0 : 1;
}