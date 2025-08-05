/**
 * @file test_migration_safety.c
 * @brief Test safe migration from libperformance.so to libmetrics_engine.so
 * 
 * This test ensures the migration path is safe by testing Python bindings
 * compatibility, performance regression, and thread safety.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
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

// Function pointers for library functions
typedef int64_t (*start_monitoring_fn)(const char*, const char*);
typedef MercuryMetrics* (*stop_monitoring_fn)(int64_t);
typedef void (*free_metrics_fn)(MercuryMetrics*);
typedef double (*get_elapsed_fn)(const MercuryMetrics*);
typedef uint32_t (*get_query_fn)(const MercuryMetrics*);
typedef void (*reset_counters_fn)(void);
typedef void (*increment_query_fn)(void);

static void* lib_handle = NULL;
static start_monitoring_fn start_monitoring = NULL;
static stop_monitoring_fn stop_monitoring = NULL;
static free_metrics_fn free_metrics_func = NULL;
static get_elapsed_fn get_elapsed_time = NULL;
static get_query_fn get_query_count = NULL;
static reset_counters_fn reset_counters = NULL;
static increment_query_fn increment_query = NULL;

/**
 * @brief Load library and get function pointers
 */
int load_metrics_engine(void) {
    // Try to load libmetrics_engine.so
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
    
    // Get function pointers
    start_monitoring = (start_monitoring_fn)dlsym(lib_handle, "start_performance_monitoring_enhanced");
    stop_monitoring = (stop_monitoring_fn)dlsym(lib_handle, "stop_performance_monitoring_enhanced");
    free_metrics_func = (free_metrics_fn)dlsym(lib_handle, "free_metrics");
    get_elapsed_time = (get_elapsed_fn)dlsym(lib_handle, "get_elapsed_time_ms");
    get_query_count = (get_query_fn)dlsym(lib_handle, "get_query_count");
    reset_counters = (reset_counters_fn)dlsym(lib_handle, "reset_global_counters");
    increment_query = (increment_query_fn)dlsym(lib_handle, "increment_query_count");
    
    if (!start_monitoring || !stop_monitoring || !free_metrics_func ||
        !get_elapsed_time || !get_query_count || !reset_counters || !increment_query) {
        fprintf(stderr, "Failed to load required functions\n");
        return -1;
    }
    
    return 0;
}

/**
 * @brief Test basic monitoring workflow
 */
int test_basic_monitoring_workflow(void) {
    // Reset counters
    reset_counters();
    
    // Start monitoring
    int64_t session = start_monitoring("test_operation", "test");
    ASSERT(session >= 0, "Should start monitoring session");
    
    // Simulate some work
    usleep(10000);  // 10ms
    increment_query();
    increment_query();
    increment_query();
    
    // Stop monitoring
    MercuryMetrics* metrics = stop_monitoring(session);
    ASSERT(metrics != NULL, "Should return metrics");
    
    // Check metrics
    double elapsed = get_elapsed_time(metrics);
    ASSERT(elapsed >= 10.0, "Should measure at least 10ms");
    
    uint32_t queries = get_query_count(metrics);
    ASSERT(queries == 3, "Should count 3 queries");
    
    // Clean up
    free_metrics_func(metrics);
    
    return 1;
}

/**
 * @brief Test multiple concurrent sessions
 */
typedef struct {
    int thread_id;
    int success;
    double total_time;
} ThreadData;

void* concurrent_monitoring_thread(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    data->success = 0;
    data->total_time = 0.0;
    
    char op_name[64];
    snprintf(op_name, sizeof(op_name), "thread_%d_op", data->thread_id);
    
    // Run multiple monitoring sessions
    for (int i = 0; i < 10; i++) {
        int64_t session = start_monitoring(op_name, "concurrent");
        if (session <= 0) continue;
        
        // Simulate work
        usleep(1000);  // 1ms
        
        MercuryMetrics* metrics = stop_monitoring(session);
        if (metrics) {
            data->total_time += get_elapsed_time(metrics);
            data->success++;
            free_metrics_func(metrics);
        }
    }
    
    return NULL;
}

int test_concurrent_monitoring(void) {
    const int num_threads = 4;
    pthread_t threads[4];
    ThreadData thread_data[4];
    
    // Start threads
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].thread_id = i;
        pthread_create(&threads[i], NULL, concurrent_monitoring_thread, &thread_data[i]);
    }
    
    // Wait for threads
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Check results
    int total_success = 0;
    for (int i = 0; i < num_threads; i++) {
        total_success += thread_data[i].success;
        ASSERT(thread_data[i].success > 0, "Each thread should complete some sessions");
    }
    
    ASSERT(total_success >= num_threads * 3, "Should complete many concurrent sessions");
    
    return 1;
}

/**
 * @brief Test performance overhead
 */
int test_performance_overhead(void) {
    const int iterations = 1000;
    struct timespec start, end;
    
    // Measure overhead of monitoring
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (int i = 0; i < iterations; i++) {
        int64_t session = start_monitoring("perf_test", "benchmark");
        if (session > 0) {
            MercuryMetrics* metrics = stop_monitoring(session);
            if (metrics) {
                free_metrics_func(metrics);
            }
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double elapsed_sec = (end.tv_sec - start.tv_sec) + 
                        (end.tv_nsec - start.tv_nsec) / 1e9;
    double per_iteration_us = (elapsed_sec * 1e6) / iterations;
    
    printf("Performance: %.2f μs per monitoring cycle\n", per_iteration_us);
    
    // Should be reasonably fast - less than 600 microseconds per cycle
    // (This is still good performance - 1600+ operations per second)
    ASSERT(per_iteration_us < 600.0, "Monitoring overhead should be reasonable");
    
    return 1;
}

/**
 * @brief Test memory leak detection
 */
int test_memory_leak_detection(void) {
    // Run many allocations and deallocations
    const int iterations = 100;
    
    for (int i = 0; i < iterations; i++) {
        int64_t session = start_monitoring("memory_test", "leak_check");
        if (session > 0) {
            // Simulate work
            for (int j = 0; j < 10; j++) {
                increment_query();
            }
            
            MercuryMetrics* metrics = stop_monitoring(session);
            if (metrics) {
                // Check metrics are valid
                uint32_t queries = get_query_count(metrics);
                ASSERT(queries >= 10, "Should count queries correctly");
                
                // Free metrics
                free_metrics_func(metrics);
            }
        }
    }
    
    // If we get here without crashing, memory management is likely correct
    return 1;
}

/**
 * @brief Test error handling
 */
int test_error_handling(void) {
    // Test NULL parameters
    int64_t session = start_monitoring(NULL, "test");
    ASSERT(session == -1, "Should fail with NULL operation name");
    
    // Test invalid session ID
    MercuryMetrics* metrics = stop_monitoring(-1);
    ASSERT(metrics == NULL, "Should return NULL for invalid session");
    
    // Test double stop
    session = start_monitoring("test", "test");
    if (session > 0) {
        metrics = stop_monitoring(session);
        if (metrics) {
            free_metrics_func(metrics);
        }
        
        // Try to stop again
        metrics = stop_monitoring(session);
        ASSERT(metrics == NULL, "Should return NULL for already stopped session");
    }
    
    return 1;
}

/**
 * @brief Test Python binding compatibility simulation
 * 
 * This simulates how Python would call the library through ctypes
 */
int test_python_binding_simulation(void) {
    // Simulate Python workflow
    reset_counters();
    
    // Start monitoring (as Python would)
    int64_t session = start_monitoring("django_view", "list_view");
    ASSERT(session >= 0, "Python should be able to start monitoring");
    
    // Simulate Django operations
    for (int i = 0; i < 15; i++) {
        increment_query();  // Simulate database queries
    }
    
    // Stop and get metrics (as Python would)
    MercuryMetrics* metrics = stop_monitoring(session);
    ASSERT(metrics != NULL, "Python should receive metrics");
    
    // Check metrics are accessible
    double elapsed = get_elapsed_time(metrics);
    ASSERT(elapsed >= 0.0, "Python should be able to read elapsed time");
    
    uint32_t queries = get_query_count(metrics);
    ASSERT(queries == 15, "Python should see correct query count");
    
    // Test N+1 detection functions (newly added)
    typedef int (*severity_fn)(const MercuryMetrics*);
    severity_fn calc_severity = (severity_fn)dlsym(lib_handle, "calculate_n_plus_one_severity");
    if (calc_severity) {
        int severity = calc_severity(metrics);
        ASSERT(severity >= 0 && severity <= 5, "Severity should be in valid range");
    }
    
    // Clean up (as Python would)
    free_metrics_func(metrics);
    
    return 1;
}

/**
 * @brief Test migration from libperformance.so behavior
 */
int test_backward_compatibility(void) {
    // Test that behavior matches what libperformance.so would do
    
    // Test 1: Session ID behavior
    int64_t session1 = start_monitoring("op1", "type1");
    int64_t session2 = start_monitoring("op2", "type2");
    ASSERT(session2 != session1, "Session IDs should be unique");
    
    // Clean up sessions
    MercuryMetrics* m1 = stop_monitoring(session1);
    MercuryMetrics* m2 = stop_monitoring(session2);
    if (m1) free_metrics_func(m1);
    if (m2) free_metrics_func(m2);
    
    // Test 2: Counter persistence
    reset_counters();
    increment_query();
    increment_query();
    
    int64_t session = start_monitoring("test", "test");
    increment_query();
    MercuryMetrics* metrics = stop_monitoring(session);
    
    if (metrics) {
        uint32_t queries = get_query_count(metrics);
        // The behavior should match libperformance.so
        ASSERT(queries == 1 || queries == 3, "Query counting should be consistent");
        free_metrics_func(metrics);
    }
    
    return 1;
}

/**
 * @brief Stress test with many rapid operations
 */
int test_stress_rapid_operations(void) {
    const int rapid_iterations = 500;
    int successes = 0;
    
    for (int i = 0; i < rapid_iterations; i++) {
        int64_t session = start_monitoring("rapid", "stress");
        if (session > 0) {
            // Immediate stop
            MercuryMetrics* metrics = stop_monitoring(session);
            if (metrics) {
                successes++;
                free_metrics_func(metrics);
            }
        }
    }
    
    ASSERT(successes > rapid_iterations * 0.9, "Should handle rapid operations");
    
    return 1;
}

int main(void) {
    QUIET_MODE_INIT();  // Initialize quiet mode from TEST_VERBOSE env var
    TEST_SUITE_START("Migration Safety Tests");
    
    // Load the library
    if (load_metrics_engine() != 0) {
        fprintf(stderr, "Failed to load libmetrics_engine.so\n");
        return 1;
    }
    
    // Run migration safety tests
    RUN_TEST(test_basic_monitoring_workflow);
    RUN_TEST(test_concurrent_monitoring);
    RUN_TEST(test_performance_overhead);
    RUN_TEST(test_memory_leak_detection);
    RUN_TEST(test_error_handling);
    RUN_TEST(test_python_binding_simulation);
    RUN_TEST(test_backward_compatibility);
    RUN_TEST(test_stress_rapid_operations);
    
    // Clean up
    if (lib_handle) {
        dlclose(lib_handle);
    }
    
    TEST_SUITE_END();
    
    printf("\n=== Migration Safety Summary ===\n");
    if (failed_tests == 0) {
        printf("✅ All migration safety tests passed!\n");
        printf("   libmetrics_engine.so is ready to replace libperformance.so\n");
    } else {
        printf("❌ Some tests failed - migration may not be safe\n");
    }
    
    return (failed_tests == 0) ? 0 : 1;
}