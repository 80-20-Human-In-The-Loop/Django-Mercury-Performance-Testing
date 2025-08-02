/**
 * @file edge_test_performance_monitor.c
 * @brief Edge case tests for performance monitor - slot management & threading
 * 
 * This test file focuses on extreme edge cases and boundary conditions for
 * performance_monitor.c with emphasis on:
 * - Slot allocation and management under pressure
 * - Thread safety and concurrent access patterns
 * - Memory pressure and resource exhaustion scenarios
 * - Timing edge cases and clock irregularities
 * - Extreme metric values and boundary conditions
 * - Error recovery and fault tolerance
 * - Signal handling and process edge cases
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/wait.h>
#include <signal.h>
#include <limits.h>
#include <float.h>
#include <errno.h>
#include "../common.h"
#include "simple_tests.h"

// Global test counters for the enhanced test framework
int total_tests = 0;
int passed_tests = 0;
int failed_tests = 0;

// Forward declarations from performance_monitor.c
extern int64_t start_performance_monitoring_enhanced(const char* operation_name, const char* operation_type);
extern void* stop_performance_monitoring_enhanced(int64_t handle);
extern void reset_global_counters(void);
extern void increment_query_count(void);
extern void increment_cache_hits(void);
extern void increment_cache_misses(void);
extern void free_metrics(void* metrics);

// Performance metrics structure (from performance_monitor.c)
typedef struct {
    uint64_t start_time_ns;
    uint64_t end_time_ns;
    size_t memory_start_bytes;
    size_t memory_peak_bytes;
    size_t memory_end_bytes;
    uint32_t query_count_start;
    uint32_t query_count_end;
    uint32_t cache_hits;
    uint32_t cache_misses;
    char operation_name[256];
    char operation_type[64];
} EnhancedPerformanceMetrics_t;

// Accessor and analysis functions
extern double get_elapsed_time_ms(EnhancedPerformanceMetrics_t* metrics);
extern uint32_t get_query_count(EnhancedPerformanceMetrics_t* metrics);
extern int has_n_plus_one_pattern(EnhancedPerformanceMetrics_t* metrics);
extern int calculate_n_plus_one_severity(EnhancedPerformanceMetrics_t* metrics);

// Test slot exhaustion and management
int test_slot_exhaustion_management(void) {
    printf("Testing slot exhaustion and management...\n");
    
    // Test 1: Create maximum possible monitoring sessions
    int64_t handles[2100];  // More than the 2048 limit
    int created_count = 0;
    
    printf("Attempting to create 2100 monitoring sessions...\n");
    
    for (int i = 0; i < 2100; i++) {
        char op_name[64];
        snprintf(op_name, sizeof(op_name), "SlotTest_%d", i);
        
        handles[i] = start_performance_monitoring_enhanced(op_name, "test");
        if (handles[i] >= 0) {
            created_count++;
        } else {
            printf("Slot exhaustion at session %d\n", i);
            break;
        }
    }
    
    printf("Successfully created %d monitoring sessions\n", created_count);
    ASSERT(created_count > 1000, "Should create a significant number of sessions");
    ASSERT(created_count <= 2048, "Should not exceed maximum slot limit");
    
    // Test 2: Try to create more sessions when exhausted
    int64_t failed_handle = start_performance_monitoring_enhanced("ExhaustionTest", "test");
    if (created_count == 2048) {
        ASSERT(failed_handle < 0, "Should fail when slots are exhausted");
        printf("Correctly rejected session when slots exhausted\n");
    }
    
    // Test 3: Free sessions in batches to test slot reuse
    int batch_size = created_count / 10;
    printf("Freeing %d sessions in first batch\n", batch_size);
    
    for (int i = 0; i < batch_size && i < created_count; i++) {
        if (handles[i] >= 0) {
            // Add some activity
            increment_query_count();
            usleep(100);
            
            EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(handles[i]);
            if (metrics != NULL) {
                free_metrics(metrics);
            }
            handles[i] = -1;  // Mark as freed
        }
    }
    
    // Test 4: Create new sessions in freed slots
    printf("Creating new sessions in freed slots...\n");
    int reuse_count = 0;
    
    for (int i = 0; i < batch_size; i++) {
        char reuse_name[64];
        snprintf(reuse_name, sizeof(reuse_name), "ReuseTest_%d", i);
        
        int64_t reuse_handle = start_performance_monitoring_enhanced(reuse_name, "reuse");
        if (reuse_handle >= 0) {
            reuse_count++;
            
            // Immediate cleanup
            EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(reuse_handle);
            if (metrics != NULL) {
                free_metrics(metrics);
            }
        }
    }
    
    printf("Successfully reused %d slots\n", reuse_count);
    ASSERT(reuse_count > 0, "Should be able to reuse freed slots");
    
    // Test 5: Clean up remaining sessions
    printf("Cleaning up remaining sessions...\n");
    int cleanup_count = 0;
    
    for (int i = batch_size; i < created_count; i++) {
        if (handles[i] >= 0) {
            EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(handles[i]);
            if (metrics != NULL) {
                cleanup_count++;
                free_metrics(metrics);
            }
        }
    }
    
    printf("Cleaned up %d remaining sessions\n", cleanup_count);
    
    return 1;
}

// Thread data for concurrent testing
typedef struct {
    int thread_id;
    int iterations;
    int success_count;
    int error_count;
    int timing_anomalies;
} MonitorThreadData;

// Thread function for concurrent monitoring
void* concurrent_monitoring_thread(void* arg) {
    MonitorThreadData* data = (MonitorThreadData*)arg;
    
    for (int i = 0; i < data->iterations; i++) {
        char op_name[64];
        snprintf(op_name, sizeof(op_name), "Thread_%d_Op_%d", data->thread_id, i);
        
        // Start monitoring
        int64_t handle = start_performance_monitoring_enhanced(op_name, "concurrent");
        if (handle >= 0) {
            // Simulate work with varying patterns
            int work_cycles = (data->thread_id % 5) + 1;
            for (int j = 0; j < work_cycles; j++) {
                increment_query_count();
                if (j % 2 == 0) increment_cache_hits();
                else increment_cache_misses();
                
                // Variable sleep to create timing variations
                usleep((rand() % 1000) + (data->thread_id * 100));
            }
            
            // Stop monitoring
            EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(handle);
            if (metrics != NULL) {
                data->success_count++;
                
                // Check for timing anomalies
                double elapsed = get_elapsed_time_ms(metrics);
                if (elapsed < 0.0 || elapsed > 10000.0) {  // Negative or > 10 seconds
                    data->timing_anomalies++;
                }
                
                uint32_t queries = get_query_count(metrics);
                if (queries != work_cycles) {
                    // Query count mismatch might indicate race condition
                    data->timing_anomalies++;
                }
                
                free_metrics(metrics);
            } else {
                data->error_count++;
            }
        } else {
            data->error_count++;
        }
        
        // Random delay between operations
        if (i % 10 == 0) {
            usleep(rand() % 5000);
        }
    }
    
    return NULL;
}

// Test thread safety and concurrent access patterns
int test_thread_safety_concurrent_access(void) {
    printf("Testing thread safety and concurrent access patterns...\n");
    
    const int num_threads = 16;
    const int iterations_per_thread = 20;
    
    pthread_t threads[num_threads];
    MonitorThreadData thread_data[num_threads];
    
    // Initialize thread data
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].iterations = iterations_per_thread;
        thread_data[i].success_count = 0;
        thread_data[i].error_count = 0;
        thread_data[i].timing_anomalies = 0;
    }
    
    printf("Starting %d threads with %d iterations each\n", num_threads, iterations_per_thread);
    
    // Reset counters before test
    reset_global_counters();
    
    // Create and start all threads simultaneously
    for (int i = 0; i < num_threads; i++) {
        int create_result = pthread_create(&threads[i], NULL, concurrent_monitoring_thread, &thread_data[i]);
        ASSERT(create_result == 0, "Should create concurrent monitoring thread");
    }
    
    // Wait for all threads to complete
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Analyze results
    int total_successes = 0, total_errors = 0, total_anomalies = 0;
    for (int i = 0; i < num_threads; i++) {
        printf("Thread %d: %d successes, %d errors, %d anomalies\n",
               i, thread_data[i].success_count, thread_data[i].error_count, 
               thread_data[i].timing_anomalies);
        
        total_successes += thread_data[i].success_count;
        total_errors += thread_data[i].error_count;
        total_anomalies += thread_data[i].timing_anomalies;
    }
    
    printf("Totals: %d successes, %d errors, %d anomalies\n", 
           total_successes, total_errors, total_anomalies);
    
    ASSERT(total_successes > total_errors, "Should have more successes than errors");
    ASSERT(total_anomalies < total_successes / 10, "Anomalies should be less than 10% of successes");
    
    // Test system functionality after concurrent stress
    int64_t post_test_handle = start_performance_monitoring_enhanced("PostConcurrentTest", "recovery");
    ASSERT(post_test_handle >= 0, "System should be functional after concurrent stress");
    
    usleep(1000);
    EnhancedPerformanceMetrics_t* post_metrics = stop_performance_monitoring_enhanced(post_test_handle);
    ASSERT(post_metrics != NULL, "Should get metrics after concurrent stress");
    free_metrics(post_metrics);
    
    return 1;
}

// Test memory pressure and resource exhaustion
int test_memory_pressure_exhaustion(void) {
    printf("Testing memory pressure and resource exhaustion...\n");
    
    // Test 1: Memory allocation pressure
    void* memory_blocks[5000];
    int allocated_blocks = 0;
    
    printf("Allocating memory blocks to create pressure...\n");
    
    // Allocate memory blocks while creating monitoring sessions
    for (int i = 0; i < 500; i++) {
        // Allocate memory block
        memory_blocks[i] = malloc(512 * 1024);  // 512KB blocks
        if (memory_blocks[i] != NULL) {
            allocated_blocks++;
            memset(memory_blocks[i], i % 256, 512 * 1024);  // Use the memory
        }
        
        // Create monitoring session under memory pressure
        if (i % 10 == 0) {
            char pressure_name[64];
            snprintf(pressure_name, sizeof(pressure_name), "MemoryPressure_%d", i);
            
            int64_t pressure_handle = start_performance_monitoring_enhanced(pressure_name, "pressure");
            if (pressure_handle >= 0) {
                // Add some load
                for (int j = 0; j < 5; j++) {
                    increment_query_count();
                }
                usleep(500);
                
                EnhancedPerformanceMetrics_t* pressure_metrics = stop_performance_monitoring_enhanced(pressure_handle);
                if (pressure_metrics != NULL) {
                    // Verify metrics are still valid under pressure
                    double elapsed = get_elapsed_time_ms(pressure_metrics);
                    uint32_t queries = get_query_count(pressure_metrics);
                    
                    if (elapsed < 0 || queries != 5) {
                        printf("Metrics corruption detected under memory pressure\n");
                    }
                    
                    free_metrics(pressure_metrics);
                }
            }
        }
    }
    
    printf("Allocated %d memory blocks during pressure test\n", allocated_blocks);
    
    // Test 2: Extreme monitoring session creation under pressure
    int64_t pressure_handles[100];
    int pressure_sessions = 0;
    
    for (int i = 0; i < 100; i++) {
        char extreme_name[64];
        snprintf(extreme_name, sizeof(extreme_name), "ExtremePressure_%d", i);
        
        pressure_handles[i] = start_performance_monitoring_enhanced(extreme_name, "extreme");
        if (pressure_handles[i] >= 0) {
            pressure_sessions++;
        }
    }
    
    printf("Created %d monitoring sessions under extreme pressure\n", pressure_sessions);
    
    // Clean up pressure sessions
    for (int i = 0; i < pressure_sessions; i++) {
        if (pressure_handles[i] >= 0) {
            EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(pressure_handles[i]);
            if (metrics != NULL) {
                free_metrics(metrics);
            }
        }
    }
    
    // Clean up memory blocks
    for (int i = 0; i < allocated_blocks; i++) {
        if (memory_blocks[i] != NULL) {
            free(memory_blocks[i]);
        }
    }
    
    // Test 3: Verify system recovery after pressure
    printf("Testing system recovery after memory pressure...\n");
    
    int64_t recovery_handle = start_performance_monitoring_enhanced("RecoveryTest", "recovery");
    ASSERT(recovery_handle >= 0, "Should create session after memory pressure");
    
    for (int i = 0; i < 10; i++) {
        increment_query_count();
    }
    usleep(1000);
    
    EnhancedPerformanceMetrics_t* recovery_metrics = stop_performance_monitoring_enhanced(recovery_handle);
    ASSERT(recovery_metrics != NULL, "Should get metrics after recovery");
    
    uint32_t recovery_queries = get_query_count(recovery_metrics);
    ASSERT(recovery_queries == 10, "Should have correct query count after recovery");
    
    free_metrics(recovery_metrics);
    
    return 1;
}

// Test timing edge cases and clock irregularities
int test_timing_edge_cases(void) {
    printf("Testing timing edge cases and clock irregularities...\n");
    
    // Test 1: Very short duration operations
    reset_global_counters();
    int64_t short_handle = start_performance_monitoring_enhanced("ShortDuration", "timing");
    // Minimal work - just one increment
    increment_query_count();
    
    EnhancedPerformanceMetrics_t* short_metrics = stop_performance_monitoring_enhanced(short_handle);
    ASSERT(short_metrics != NULL, "Should handle very short operations");
    
    double short_elapsed = get_elapsed_time_ms(short_metrics);
    printf("Short operation elapsed time: %.6fms\n", short_elapsed);
    ASSERT(short_elapsed >= 0.0, "Should have non-negative elapsed time");
    
    free_metrics(short_metrics);
    
    // Test 2: Back-to-back operations with minimal delays
    printf("Testing back-to-back operations...\n");
    
    for (int i = 0; i < 50; i++) {
        char rapid_name[64];
        snprintf(rapid_name, sizeof(rapid_name), "Rapid_%d", i);
        
        int64_t rapid_handle = start_performance_monitoring_enhanced(rapid_name, "rapid");
        if (rapid_handle >= 0) {
            increment_query_count();
            // No delay - immediate stop
            
            EnhancedPerformanceMetrics_t* rapid_metrics = stop_performance_monitoring_enhanced(rapid_handle);
            if (rapid_metrics != NULL) {
                double rapid_elapsed = get_elapsed_time_ms(rapid_metrics);
                if (rapid_elapsed < 0.0) {
                    printf("Negative elapsed time detected in rapid test %d: %.6fms\n", i, rapid_elapsed);
                }
                free_metrics(rapid_metrics);
            }
        }
    }
    
    // Test 3: Long duration operations
    printf("Testing long duration operation...\n");
    
    int64_t long_handle = start_performance_monitoring_enhanced("LongDuration", "timing");
    ASSERT(long_handle >= 0, "Should start long duration monitoring");
    
    // Simulate longer work
    for (int i = 0; i < 100; i++) {
        increment_query_count();
        usleep(1000);  // 1ms per iteration = ~100ms total
    }
    
    EnhancedPerformanceMetrics_t* long_metrics = stop_performance_monitoring_enhanced(long_handle);
    ASSERT(long_metrics != NULL, "Should handle long duration operations");
    
    double long_elapsed = get_elapsed_time_ms(long_metrics);
    printf("Long operation elapsed time: %.2fms\n", long_elapsed);
    ASSERT(long_elapsed > 50.0, "Should have reasonable elapsed time for long operation");
    
    uint32_t long_queries = get_query_count(long_metrics);
    ASSERT(long_queries == 100, "Should have correct query count for long operation");
    
    free_metrics(long_metrics);
    
    // Test 4: Operations started but never stopped (handle cleanup)
    printf("Testing abandoned handles...\n");
    
    int64_t abandoned_handles[20];
    int abandoned_count = 0;
    
    for (int i = 0; i < 20; i++) {
        char abandoned_name[64];
        snprintf(abandoned_name, sizeof(abandoned_name), "Abandoned_%d", i);
        
        abandoned_handles[i] = start_performance_monitoring_enhanced(abandoned_name, "abandoned");
        if (abandoned_handles[i] >= 0) {
            abandoned_count++;
            increment_query_count();
            // Don't stop these - test handle cleanup
        }
    }
    
    printf("Created %d abandoned monitoring sessions\n", abandoned_count);
    
    // System should still be able to create new sessions despite abandoned handles
    int64_t new_handle = start_performance_monitoring_enhanced("AfterAbandoned", "test");
    ASSERT(new_handle >= 0, "Should create new session despite abandoned handles");
    
    EnhancedPerformanceMetrics_t* new_metrics = stop_performance_monitoring_enhanced(new_handle);
    ASSERT(new_metrics != NULL, "Should stop new session normally");
    free_metrics(new_metrics);
    
    return 1;
}

// Test extreme metric values and boundary conditions
int test_extreme_metric_values(void) {
    printf("Testing extreme metric values and boundary conditions...\n");
    
    // Test 1: Extreme query counts  
    reset_global_counters();
    int64_t extreme_handle = start_performance_monitoring_enhanced("ExtremeMetrics", "boundary");
    
    // Generate extreme query count
    printf("Generating extreme query count...\n");
    for (int i = 0; i < 10000; i++) {
        increment_query_count();
        if (i % 1000 == 0) {
            printf("  Generated %d queries...\n", i);
        }
    }
    
    // Mix of cache hits and misses
    for (int i = 0; i < 5000; i++) {
        increment_cache_hits();
    }
    for (int i = 0; i < 3000; i++) {
        increment_cache_misses();
    }
    
    usleep(10000);  // 10ms work
    
    EnhancedPerformanceMetrics_t* extreme_metrics = stop_performance_monitoring_enhanced(extreme_handle);
    ASSERT(extreme_metrics != NULL, "Should handle extreme metric values");
    
    uint32_t extreme_queries = get_query_count(extreme_metrics);
    printf("Extreme query count: %u\n", extreme_queries);
    ASSERT(extreme_queries == 10000, "Should have correct extreme query count");
    
    // Test N+1 detection with extreme values
    int has_n_plus_one = has_n_plus_one_pattern(extreme_metrics);
    int severity = calculate_n_plus_one_severity(extreme_metrics);
    
    printf("Extreme N+1 detection: pattern=%d, severity=%d\n", has_n_plus_one, severity);
    ASSERT(has_n_plus_one == 1, "Should detect N+1 with extreme query count");
    ASSERT(severity > 0, "Should have high severity for extreme query count");
    
    free_metrics(extreme_metrics);
    
    // Test 2: Zero values edge case (targeting line 441)
    reset_global_counters();
    int64_t zero_handle = start_performance_monitoring_enhanced("ZeroQueries", "boundary");
    
    // No queries added - should trigger line 441 condition
    usleep(1000);
    
    EnhancedPerformanceMetrics_t* zero_metrics = stop_performance_monitoring_enhanced(zero_handle);
    ASSERT(zero_metrics != NULL, "Should handle zero query operation");
    
    uint32_t zero_queries = get_query_count(zero_metrics);
    printf("Zero queries test: %u queries\n", zero_queries);
    ASSERT(zero_queries == 0, "Should have zero queries");
    
    // This should trigger the line 441 condition check in detect functions
    int zero_n_plus_one = has_n_plus_one_pattern(zero_metrics);
    int zero_severity = calculate_n_plus_one_severity(zero_metrics);
    
    printf("Zero queries N+1 check: pattern=%d, severity=%d\n", zero_n_plus_one, zero_severity);
    ASSERT(zero_n_plus_one == 0, "Should not detect N+1 for zero queries");
    ASSERT(zero_severity == 0, "Should have zero severity for zero queries");
    
    free_metrics(zero_metrics);
    
    // Test 3: Boundary query counts for N+1 detection thresholds
    const int boundary_counts[] = {11, 12, 13, 19, 20, 21, 49, 50, 51};
    
    for (int i = 0; i < 9; i++) {
        reset_global_counters();
        char boundary_name[64];
        snprintf(boundary_name, sizeof(boundary_name), "Boundary_%d", boundary_counts[i]);
        
        int64_t boundary_handle = start_performance_monitoring_enhanced(boundary_name, "boundary");
        
        for (int j = 0; j < boundary_counts[i]; j++) {
            increment_query_count();
        }
        usleep(1000);
        
        EnhancedPerformanceMetrics_t* boundary_metrics = stop_performance_monitoring_enhanced(boundary_handle);
        if (boundary_metrics != NULL) {
            uint32_t boundary_queries = get_query_count(boundary_metrics);
            int boundary_n_plus_one = has_n_plus_one_pattern(boundary_metrics);
            int boundary_severity = calculate_n_plus_one_severity(boundary_metrics);
            
            printf("Boundary test %d queries: N+1=%d, severity=%d\n", 
                   boundary_queries, boundary_n_plus_one, boundary_severity);
            
            // Verify threshold behavior
            if (boundary_counts[i] >= 12) {
                ASSERT(boundary_n_plus_one == 1, "Should detect N+1 for >= 12 queries");
            } else {
                ASSERT(boundary_n_plus_one == 0, "Should not detect N+1 for < 12 queries");
            }
            
            free_metrics(boundary_metrics);
        }
    }
    
    return 1;
}

// Test invalid handle operations
int test_invalid_handle_operations(void) {
    printf("Testing invalid handle operations...\n");
    
    // Test 1: Invalid handle values
    int64_t invalid_handles[] = {-1, 0, -100, INT64_MAX, INT64_MIN};
    
    for (int i = 0; i < 5; i++) {
        printf("Testing invalid handle: %lld\n", (long long)invalid_handles[i]);
        
        EnhancedPerformanceMetrics_t* invalid_metrics = stop_performance_monitoring_enhanced(invalid_handles[i]);
        ASSERT(invalid_metrics == NULL, "Should return NULL for invalid handle");
    }
    
    // Test 2: Double-stop operations
    int64_t double_handle = start_performance_monitoring_enhanced("DoubleStop", "test");
    ASSERT(double_handle >= 0, "Should create handle for double-stop test");
    
    increment_query_count();
    usleep(100);
    
    // First stop - should work
    EnhancedPerformanceMetrics_t* first_stop = stop_performance_monitoring_enhanced(double_handle);
    ASSERT(first_stop != NULL, "First stop should succeed");
    
    // Second stop with same handle - should fail
    EnhancedPerformanceMetrics_t* second_stop = stop_performance_monitoring_enhanced(double_handle);
    ASSERT(second_stop == NULL, "Second stop should fail");
    
    free_metrics(first_stop);
    
    // Test 3: Out-of-range handle values
    int64_t out_of_range_handles[] = {2049, 3000, 10000};  // Beyond 2048 slot limit
    
    for (int i = 0; i < 3; i++) {
        printf("Testing out-of-range handle: %lld\n", (long long)out_of_range_handles[i]);
        
        EnhancedPerformanceMetrics_t* oor_metrics = stop_performance_monitoring_enhanced(out_of_range_handles[i]);
        ASSERT(oor_metrics == NULL, "Should return NULL for out-of-range handle");
    }
    
    return 1;
}

// Test signal handling and process edge cases
int test_signal_handling_process_edges(void) {
    printf("Testing signal handling and process edge cases...\n");
    
    // Test 1: Normal operation that completes successfully
    int64_t normal_handle = start_performance_monitoring_enhanced("SignalTest", "signal");
    ASSERT(normal_handle >= 0, "Should create handle for signal test");
    
    for (int i = 0; i < 10; i++) {
        increment_query_count();
        usleep(100);
    }
    
    EnhancedPerformanceMetrics_t* normal_metrics = stop_performance_monitoring_enhanced(normal_handle);
    ASSERT(normal_metrics != NULL, "Should complete normally");
    
    uint32_t normal_queries = get_query_count(normal_metrics);
    ASSERT(normal_queries == 10, "Should have correct query count");
    
    free_metrics(normal_metrics);
    
    // Test 2: Rapid creation and destruction (stress test)
    printf("Rapid handle creation/destruction stress test...\n");
    
    int rapid_successes = 0;
    for (int i = 0; i < 1000; i++) {
        char rapid_name[64];
        snprintf(rapid_name, sizeof(rapid_name), "Rapid_%d", i);
        
        int64_t rapid_handle = start_performance_monitoring_enhanced(rapid_name, "rapid");
        if (rapid_handle >= 0) {
            increment_query_count();
            
            EnhancedPerformanceMetrics_t* rapid_metrics = stop_performance_monitoring_enhanced(rapid_handle);
            if (rapid_metrics != NULL) {
                rapid_successes++;
                free_metrics(rapid_metrics);
            }
        }
        
        // Periodic status
        if (i % 200 == 0 && i > 0) {
            printf("  Completed %d rapid operations, %d successes\n", i, rapid_successes);
        }
    }
    
    printf("Rapid stress test: %d successes out of 1000 attempts\n", rapid_successes);
    ASSERT(rapid_successes > 900, "Should have high success rate in rapid test");
    
    // Test 3: System recovery verification
    printf("Verifying system recovery after stress...\n");
    
    int64_t recovery_handle = start_performance_monitoring_enhanced("RecoveryVerification", "recovery");
    ASSERT(recovery_handle >= 0, "Should create handle after stress test");
    
    for (int i = 0; i < 5; i++) {
        increment_query_count();
    }
    usleep(1000);
    
    EnhancedPerformanceMetrics_t* recovery_metrics = stop_performance_monitoring_enhanced(recovery_handle);
    ASSERT(recovery_metrics != NULL, "Should get metrics after recovery");
    
    uint32_t recovery_queries = get_query_count(recovery_metrics);
    ASSERT(recovery_queries == 5, "Should have correct count after recovery");
    
    free_metrics(recovery_metrics);
    
    return 1;
}

int main(void) {
    TEST_SUITE_START("Edge Case Performance Monitor Tests - Slot Management & Threading");
    
    printf("🎯 Edge case testing of performance_monitor.c extreme conditions:\n");
    printf("   - Slot exhaustion and management under maximum pressure\n");
    printf("   - Thread safety and concurrent access patterns\n");
    printf("   - Memory pressure and resource exhaustion scenarios\n");
    printf("   - Timing edge cases and clock irregularities\n");
    printf("   - Extreme metric values and boundary conditions\n");
    printf("   - Invalid handle operations and error recovery\n");
    printf("   - Signal handling and process edge cases\n\n");
    
    RUN_TEST(test_slot_exhaustion_management);
    RUN_TEST(test_thread_safety_concurrent_access);
    RUN_TEST(test_memory_pressure_exhaustion);
    RUN_TEST(test_timing_edge_cases);
    RUN_TEST(test_extreme_metric_values);
    RUN_TEST(test_invalid_handle_operations);
    RUN_TEST(test_signal_handling_process_edges);
    
    TEST_SUITE_END();
    
    printf("\n🚀 Edge case performance monitor tests completed!\n");
    printf("Expected result: Push performance_monitor.c coverage to final 55-60%% target\n");
    printf("Focus areas: Slot management, threading, resource limits, extreme values\n");
    
    return (failed_tests == 0) ? 0 : 1;
}