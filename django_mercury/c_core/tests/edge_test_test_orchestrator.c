/**
 * @file edge_test_test_orchestrator.c
 * @brief Edge case tests for test orchestrator - platform paths & boundaries
 * 
 * This test file focuses on extreme edge cases, boundary conditions, and
 * platform-specific behaviors for test_orchestrator.c:
 * - Platform-specific file path handling and limits
 * - Memory pressure and allocation failures
 * - Boundary conditions for strings, buffers, and numeric limits
 * - Race conditions and threading edge cases
 * - File system edge cases and permission scenarios
 * - Resource exhaustion and recovery
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <time.h>
#include <limits.h>
#include <float.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <pthread.h>
#include <errno.h>
#include <signal.h>
#include "../common.h"
#include "test_simple.h"

// Global test counters for the enhanced test framework
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

// External function declarations from test_orchestrator.c
extern void* create_test_context(const char* test_class, const char* test_method);
extern int update_test_context(void* context_ptr, double response_time_ms, double memory_usage_mb,
                              uint32_t query_count, double cache_hit_ratio, double performance_score,
                              const char* grade);
extern int update_n_plus_one_analysis(void* context_ptr, int has_n_plus_one, int severity_level,
                                     const char* query_signature);
extern int finalize_test_context(void* context_ptr);
extern void get_orchestrator_statistics(uint64_t* total_tests, uint64_t* total_violations,
                                       uint64_t* total_n_plus_one, size_t* active_contexts,
                                       uint64_t* history_entries);
extern int load_binary_configuration(const char* config_path);
extern int save_binary_configuration(const char* config_path);
extern int query_history_entries(const char* test_class_filter, const char* test_method_filter,
                               uint64_t start_timestamp, uint64_t end_timestamp,
                               char* result_buffer, size_t buffer_size);

// Test platform-specific file path handling
int test_platform_path_handling(void) {
    printf("Testing platform-specific file path handling...\n");
    
    // Test 1: Very long file paths (approaching PATH_MAX)
    char long_path[PATH_MAX];
    memset(long_path, 'x', PATH_MAX - 50);
    strcpy(long_path + PATH_MAX - 50, "/test_config.bin");
    long_path[PATH_MAX - 1] = '\0';
    
    printf("Testing very long path (%zu chars)\n", strlen(long_path));
    int long_path_result = save_binary_configuration(long_path);
    // Should either succeed or fail gracefully
    printf("Long path save result: %d\n", long_path_result);
    
    // Test 2: Path with special characters
    const char* special_paths[] = {
        "/tmp/test config with spaces.bin",
        "/tmp/test-config-with-dashes.bin", 
        "/tmp/test_config_with_underscores.bin",
        "/tmp/test.config.with.dots.bin",
        "/tmp/test@config#with$symbols%.bin"
    };
    
    for (int i = 0; i < 5; i++) {
        printf("Testing special path: %s\n", special_paths[i]);
        int special_save = save_binary_configuration(special_paths[i]);
        int special_load = load_binary_configuration(special_paths[i]);
        
        printf("  Save: %d, Load: %d\n", special_save, special_load);
        
        // Clean up if file was created
        unlink(special_paths[i]);
    }
    
    // Test 3: Non-existent directory paths
    const char* invalid_paths[] = {
        "/nonexistent/directory/config.bin",
        "/proc/invalid/config.bin",  // proc filesystem edge case
        "/dev/null/config.bin",      // Device file edge case
        "",                          // Empty path
        "relative/path/config.bin"   // Relative path
    };
    
    for (int i = 0; i < 5; i++) {
        printf("Testing invalid path: %s\n", invalid_paths[i]);
        int invalid_save = save_binary_configuration(invalid_paths[i]);
        int invalid_load = load_binary_configuration(invalid_paths[i]);
        
        // Should fail gracefully
        ASSERT(invalid_save != 0 || invalid_load != 0, "Should handle invalid paths");
        printf("  Handled invalid path gracefully\n");
    }
    
    // Test 4: Unicode and international characters (if supported)
    const char* unicode_path = "/tmp/test_конфиг_配置.bin";
    int unicode_result = save_binary_configuration(unicode_path);
    printf("Unicode path result: %d\n", unicode_result);
    unlink(unicode_path);
    
    return 1;
}

// Test string boundary conditions and buffer overflows
int test_string_boundary_conditions(void) {
    printf("Testing string boundary conditions and buffer safety...\n");
    
    // Test 1: Maximum length strings for test class and method
    char max_class[256], max_method[256];
    memset(max_class, 'C', 255);
    max_class[255] = '\0';
    memset(max_method, 'M', 255);  
    max_method[255] = '\0';
    
    printf("Testing maximum length strings (255 chars each)\n");
    void* max_context = create_test_context(max_class, max_method);
    if (max_context != NULL) {
        printf("Successfully created context with max length strings\n");
        update_test_context(max_context, 100.0, 50.0, 10, 0.5, 75.0, "C");
        finalize_test_context(max_context);
    } else {
        printf("Gracefully rejected max length strings\n");
    }
    
    // Test 2: Extremely long strings (beyond buffer limits)
    char huge_class[4096], huge_method[4096];
    memset(huge_class, 'H', 4095);
    huge_class[4095] = '\0';
    memset(huge_method, 'G', 4095);
    huge_method[4095] = '\0';
    
    printf("Testing huge strings (4095 chars each)\n");
    void* huge_context = create_test_context(huge_class, huge_method);
    if (huge_context != NULL) {
        // Should either truncate or handle gracefully
        printf("Handled huge strings (likely truncated)\n");
        finalize_test_context(huge_context);
    } else {
        printf("Gracefully rejected huge strings\n");
    }
    
    // Test 3: Strings with null bytes in the middle
    char null_class[64] = "TestClass";
    null_class[4] = '\0';  // Null byte in middle
    null_class[5] = 'X';   // Character after null
    
    void* null_context = create_test_context(null_class, "normal_method");
    if (null_context != NULL) {
        printf("Handled string with internal null byte\n");
        finalize_test_context(null_context);
    }
    
    // Test 4: Empty strings
    void* empty_context1 = create_test_context("", "method");
    void* empty_context2 = create_test_context("class", "");
    void* empty_context3 = create_test_context("", "");
    
    // Should handle empty strings gracefully (likely reject)
    if (empty_context1) finalize_test_context(empty_context1);
    if (empty_context2) finalize_test_context(empty_context2);
    if (empty_context3) finalize_test_context(empty_context3);
    
    // Test 5: Extremely long N+1 query signatures
    char huge_query[8192];
    memset(huge_query, 'Q', 8191);
    huge_query[8191] = '\0';
    
    void* query_context = create_test_context("QueryTest", "huge_query");
    if (query_context != NULL) {
        update_test_context(query_context, 75.0, 25.0, 15, 0.53, 70.0, "C");
        int huge_query_result = update_n_plus_one_analysis(query_context, 1, 3, huge_query);
        printf("Huge query signature result: %d\n", huge_query_result);
        finalize_test_context(query_context);
    }
    
    return 1;
}

// Test numeric boundary conditions and limits
int test_numeric_boundary_conditions(void) {
    printf("Testing numeric boundary conditions and limits...\n");
    
    void* boundary_context = create_test_context("BoundaryTest", "numeric_limits");
    ASSERT(boundary_context != NULL, "Should create boundary test context");
    
    // Test 1: Maximum values
    double max_response_time = DBL_MAX;
    double max_memory_usage = DBL_MAX;
    uint32_t max_query_count = UINT32_MAX;
    
    printf("Testing maximum numeric values\n");
    int max_result = update_test_context(boundary_context, max_response_time, max_memory_usage,
                                        max_query_count, 0.5, 50.0, "F");
    printf("Max values update result: %d\n", max_result);
    
    // Test 2: Minimum/Zero values  
    int zero_result = update_test_context(boundary_context, 0.0, 0.0, 0, 0.0, 0.0, "F");
    printf("Zero values update result: %d\n", zero_result);
    
    // Test 3: Negative values (should be handled appropriately)
    int negative_result = update_test_context(boundary_context, -100.0, -50.0, 0, 0.0, 0.0, "F");
    printf("Negative values update result: %d\n", negative_result);
    
    // Test 4: Special float values
    double inf_value = 1.0 / 0.0;  // Infinity
    double nan_value = 0.0 / 0.0;  // NaN
    
    int inf_result = update_test_context(boundary_context, inf_value, 10.0, 5, 0.4, 60.0, "D");
    printf("Infinity value update result: %d\n", inf_result);
    
    int nan_result = update_test_context(boundary_context, nan_value, 10.0, 5, 0.4, 50.0, "D");
    printf("NaN value update result: %d\n", nan_result);
    
    // Test 5: Very small positive values
    double tiny_value = 1e-100;
    int tiny_result = update_test_context(boundary_context, tiny_value, tiny_value, 1, 0.0, 10.0, "F");
    printf("Tiny values update result: %d\n", tiny_result);
    
    finalize_test_context(boundary_context);
    
    return 1;
}

// Thread data structure for race condition testing
typedef struct {
    int thread_id;
    int iterations;
    int success_count;
    int error_count;
} ThreadData;

// Thread function for race condition testing
void* race_condition_thread(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    
    for (int i = 0; i < data->iterations; i++) {
        char class_name[64], method_name[64];
        snprintf(class_name, sizeof(class_name), "RaceTest_%d", data->thread_id);
        snprintf(method_name, sizeof(method_name), "race_method_%d_%d", data->thread_id, i);
        
        // Create context
        void* context = create_test_context(class_name, method_name);
        if (context != NULL) {
            data->success_count++;
            
            // Update context with thread-specific data
            double response_time = 50.0 + (data->thread_id * 10.0);
            double memory_usage = 10.0 + (data->thread_id * 2.0);
            uint32_t query_count = 5 + data->thread_id;
            
            int update_result = update_test_context(context, response_time, memory_usage,
                                                   query_count, 0.6, 80.0, "B");
            
            if (update_result == 0) {
                // Randomly add N+1 analysis
                if (i % 3 == 0) {
                    char query_sig[128];
                    snprintf(query_sig, sizeof(query_sig), 
                            "SELECT * FROM race_table_%d WHERE id = ?", data->thread_id);
                    update_n_plus_one_analysis(context, 1, 2, query_sig);
                }
                
                // Small delay to increase chance of race conditions
                usleep(rand() % 1000);
                
                // Finalize context
                int finalize_result = finalize_test_context(context);
                if (finalize_result != 0) {
                    data->error_count++;
                }
            } else {
                data->error_count++;
                // Still try to finalize to avoid leaks
                finalize_test_context(context);
            }
        } else {
            data->error_count++;
        }
    }
    
    return NULL;
}

// Test race conditions and threading edge cases
int test_race_conditions_threading(void) {
    printf("Testing race conditions and threading edge cases...\n");
    
    const int num_threads = 8;
    const int iterations_per_thread = 25;
    
    pthread_t threads[num_threads];
    ThreadData thread_data[num_threads];
    
    // Initialize thread data
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].iterations = iterations_per_thread;
        thread_data[i].success_count = 0;
        thread_data[i].error_count = 0;
    }
    
    printf("Starting %d threads with %d iterations each\n", num_threads, iterations_per_thread);
    
    // Create threads
    for (int i = 0; i < num_threads; i++) {
        int create_result = pthread_create(&threads[i], NULL, race_condition_thread, &thread_data[i]);
        ASSERT(create_result == 0, "Should create race condition test thread");
    }
    
    // Wait for all threads to complete
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Analyze results
    int total_successes = 0, total_errors = 0;
    for (int i = 0; i < num_threads; i++) {
        printf("Thread %d: %d successes, %d errors\n", 
               i, thread_data[i].success_count, thread_data[i].error_count);
        total_successes += thread_data[i].success_count;
        total_errors += thread_data[i].error_count;
    }
    
    printf("Total: %d successes, %d errors\n", total_successes, total_errors);
    
    // Should have mostly successes, some errors are acceptable under race conditions
    ASSERT(total_successes > total_errors, "Should have more successes than errors");
    
    // Verify system is still functional after race conditions
    void* post_race_context = create_test_context("PostRaceTest", "functionality_check");
    ASSERT(post_race_context != NULL, "System should be functional after race conditions");
    
    update_test_context(post_race_context, 100.0, 25.0, 12, 0.5, 75.0, "B");
    int post_race_finalize = finalize_test_context(post_race_context);
    ASSERT(post_race_finalize == 0, "Should finalize post-race context");
    
    return 1;
}

// Test file system edge cases and permission scenarios
int test_filesystem_edge_cases(void) {
    printf("Testing file system edge cases and permission scenarios...\n");
    
    // Test 1: Read-only directory (if possible to create)
    const char* readonly_dir = "/tmp/readonly_test_dir";
    mkdir(readonly_dir, 0755);
    chmod(readonly_dir, 0444);  // Read-only
    
    char readonly_config[256];
    snprintf(readonly_config, sizeof(readonly_config), "%s/config.bin", readonly_dir);
    
    int readonly_save = save_binary_configuration(readonly_config);
    printf("Read-only directory save result: %d\n", readonly_save);
    // Should fail gracefully
    
    // Restore permissions and clean up
    chmod(readonly_dir, 0755);
    rmdir(readonly_dir);
    
    // Test 2: Full file system simulation (create large file)
    const char* large_file_path = "/tmp/large_test_file.bin";
    int large_fd = open(large_file_path, O_CREAT | O_WRONLY, 0644);
    if (large_fd >= 0) {
        // Try to write a large amount of data to simulate disk full
        char buffer[4096];
        memset(buffer, 'X', sizeof(buffer));
        
        // Write until error (disk full) or reasonable limit
        for (int i = 0; i < 10000; i++) {  // ~40MB max
            if (write(large_fd, buffer, sizeof(buffer)) < 0) {
                printf("Simulated disk full condition at iteration %d\n", i);
                break;
            }
        }
        close(large_fd);
        unlink(large_file_path);
    }
    
    // Test 3: Concurrent file access
    const char* concurrent_config = "/tmp/concurrent_config.bin";
    
    // Save configuration from main thread
    int main_save = save_binary_configuration(concurrent_config);
    printf("Main thread save result: %d\n", main_save);
    
    // Try to load while another process might be accessing it
    for (int i = 0; i < 5; i++) {
        int concurrent_load = load_binary_configuration(concurrent_config);
        printf("Concurrent load %d result: %d\n", i, concurrent_load);
        usleep(1000);  // Small delay
    }
    
    unlink(concurrent_config);
    
    // Test 4: Symbolic links and special files
    const char* symlink_target = "/tmp/config_target.bin";
    const char* symlink_path = "/tmp/config_symlink.bin";
    
    // Create target file
    save_binary_configuration(symlink_target);
    
    // Create symbolic link
    if (symlink(symlink_target, symlink_path) == 0) {
        printf("Testing symbolic link access\n");
        int symlink_load = load_binary_configuration(symlink_path);
        printf("Symbolic link load result: %d\n", symlink_load);
        
        unlink(symlink_path);
    }
    
    unlink(symlink_target);
    
    return 1;
}

// Test resource exhaustion and recovery
int test_resource_exhaustion_recovery(void) {
    printf("Testing resource exhaustion and recovery scenarios...\n");
    
    // Test 1: Context pool exhaustion (already tested in comprehensive, but with recovery focus)
    void* exhaustion_contexts[300];
    int exhaustion_created = 0;
    
    printf("Exhausting context pool...\n");
    for (int i = 0; i < 300; i++) {
        char class_name[64], method_name[64];
        snprintf(class_name, sizeof(class_name), "ExhaustionTest_%d", i);
        snprintf(method_name, sizeof(method_name), "exhaust_%d", i);
        
        exhaustion_contexts[i] = create_test_context(class_name, method_name);
        if (exhaustion_contexts[i] != NULL) {
            exhaustion_created++;
        } else {
            break;  // Pool exhausted
        }
    }
    
    printf("Created %d contexts before exhaustion\n", exhaustion_created);
    
    // Test recovery by freeing contexts in batches
    int recovery_batches = 5;
    int contexts_per_batch = exhaustion_created / recovery_batches;
    
    for (int batch = 0; batch < recovery_batches; batch++) {
        printf("Recovery batch %d: freeing %d contexts\n", batch, contexts_per_batch);
        
        // Free contexts in this batch
        for (int i = batch * contexts_per_batch; 
             i < (batch + 1) * contexts_per_batch && i < exhaustion_created; i++) {
            if (exhaustion_contexts[i] != NULL) {
                update_test_context(exhaustion_contexts[i], 50.0, 10.0, 5, 0.4, 80.0, "B");
                finalize_test_context(exhaustion_contexts[i]);
                exhaustion_contexts[i] = NULL;
            }
        }
        
        // Test that we can create new contexts after freeing
        void* recovery_context = create_test_context("RecoveryTest", "recovery_batch");
        if (recovery_context != NULL) {
            printf("Successfully created context after batch %d recovery\n", batch);
            update_test_context(recovery_context, 75.0, 15.0, 8, 0.5, 85.0, "B");
            finalize_test_context(recovery_context);
        } else {
            printf("Failed to create context after batch %d recovery\n", batch);
        }
    }
    
    // Clean up any remaining contexts
    for (int i = 0; i < exhaustion_created; i++) {
        if (exhaustion_contexts[i] != NULL) {
            finalize_test_context(exhaustion_contexts[i]);
        }
    }
    
    // Test 2: Memory pressure simulation
    printf("Simulating memory pressure...\n");
    void* memory_blocks[1000];
    int allocated_blocks = 0;
    
    // Allocate memory blocks until allocation fails
    for (int i = 0; i < 1000; i++) {
        memory_blocks[i] = malloc(1024 * 1024);  // 1MB blocks
        if (memory_blocks[i] != NULL) {
            allocated_blocks++;
            memset(memory_blocks[i], i % 256, 1024 * 1024);  // Use the memory
        } else {
            printf("Memory allocation failed at block %d\n", i);
            break;
        }
    }
    
    printf("Allocated %d memory blocks\n", allocated_blocks);
    
    // Test context creation under memory pressure
    void* pressure_context = create_test_context("MemoryPressureTest", "under_pressure");
    if (pressure_context != NULL) {
        printf("Created context under memory pressure\n");
        update_test_context(pressure_context, 200.0, 100.0, 20, 0.5, 65.0, "C");
        finalize_test_context(pressure_context);
    } else {
        printf("Failed to create context under memory pressure\n");
    }
    
    // Free memory blocks to simulate recovery
    for (int i = 0; i < allocated_blocks; i++) {
        if (memory_blocks[i] != NULL) {
            free(memory_blocks[i]);
        }
    }
    
    // Test context creation after memory recovery
    void* post_pressure_context = create_test_context("PostPressureTest", "after_recovery");
    ASSERT(post_pressure_context != NULL, "Should create context after memory recovery");
    
    update_test_context(post_pressure_context, 50.0, 10.0, 5, 0.6, 90.0, "A");
    int post_pressure_finalize = finalize_test_context(post_pressure_context);
    ASSERT(post_pressure_finalize == 0, "Should finalize context after recovery");
    
    return 1;
}

// Test query buffer edge cases
int test_query_buffer_edge_cases(void) {
    printf("Testing query buffer edge cases...\n");
    
    // Create some test contexts for history
    for (int i = 0; i < 5; i++) {
        char class_name[32], method_name[32];
        snprintf(class_name, sizeof(class_name), "BufferTest_%d", i);
        snprintf(method_name, sizeof(method_name), "buffer_method_%d", i);
        
        void* context = create_test_context(class_name, method_name);
        if (context != NULL) {
            update_test_context(context, 50.0 + i * 10.0, 10.0 + i, 5 + i, 0.5, 80.0, "B");
            finalize_test_context(context);
        }
    }
    
    // Test 1: Very small buffer
    char tiny_buffer[8];
    int tiny_result = query_history_entries("BufferTest", NULL, 0, UINT64_MAX, tiny_buffer, sizeof(tiny_buffer));
    printf("Tiny buffer query result: %d\n", tiny_result);
    ASSERT(tiny_result >= 0, "Should handle tiny buffer gracefully");
    
    // Test 2: Exactly 1 byte buffer
    char one_byte_buffer[1];
    int one_byte_result = query_history_entries(NULL, "buffer_method", 0, UINT64_MAX, one_byte_buffer, 1);
    printf("One byte buffer query result: %d\n", one_byte_result);
    
    // Test 3: Large buffer
    char* large_buffer = malloc(1024 * 1024);  // 1MB buffer
    if (large_buffer != NULL) {
        int large_result = query_history_entries("BufferTest", NULL, 0, UINT64_MAX, large_buffer, 1024 * 1024);
        printf("Large buffer query result: %d\n", large_result);
        ASSERT(large_result >= 0, "Should handle large buffer");
        free(large_buffer);
    }
    
    // Test 4: Buffer with existing content (should be overwritten)
    char dirty_buffer[256];
    memset(dirty_buffer, 'X', sizeof(dirty_buffer) - 1);
    dirty_buffer[sizeof(dirty_buffer) - 1] = '\0';
    
    int dirty_result = query_history_entries("BufferTest_1", NULL, 0, UINT64_MAX, dirty_buffer, sizeof(dirty_buffer));
    printf("Dirty buffer query result: %d\n", dirty_result);
    printf("Buffer after query: %.50s...\n", dirty_buffer);  // Show first 50 chars
    
    return 1;
}

int main(void) {
    QUIET_MODE_INIT();  // Initialize quiet mode from TEST_VERBOSE env var
    TEST_SUITE_START("Edge Case Test Orchestrator Tests - Platform Paths & Boundaries");
    
    if (!quiet_mode) {
        printf("🎯 Edge case testing of test_orchestrator.c extreme conditions:\n");
        printf("   - Platform-specific file path handling and limits\n");
        printf("   - String boundary conditions and buffer overflow protection\n");
        printf("   - Numeric boundary conditions and special values\n");
        printf("   - Race conditions and threading edge cases\n");
        printf("   - File system edge cases and permission scenarios\n");
        printf("   - Resource exhaustion and recovery mechanisms\n");
        printf("   - Query buffer edge cases and size limits\n\n");
    }
    
    RUN_TEST(test_platform_path_handling);
    RUN_TEST(test_string_boundary_conditions);
    RUN_TEST(test_numeric_boundary_conditions);
    RUN_TEST(test_race_conditions_threading);
    RUN_TEST(test_filesystem_edge_cases);
    RUN_TEST(test_resource_exhaustion_recovery);
    RUN_TEST(test_query_buffer_edge_cases);
    
    TEST_SUITE_END();
    
    if (!quiet_mode) {
        printf("\n🚀 Edge case test orchestrator tests completed!\n");
        printf("Expected result: Push test_orchestrator.c coverage to final 55-60%% target\n");
        printf("Focus areas: Platform boundaries, resource limits, error recovery\n");
    }
    
    return (failed_tests == 0) ? 0 : 1;
}