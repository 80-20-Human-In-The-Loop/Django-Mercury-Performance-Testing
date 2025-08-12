/**
 * @file memcheck_test.c
 * @brief Dedicated memory leak detection test for Valgrind
 * 
 * Exercises all allocation/deallocation paths to detect:
 * - Memory leaks
 * - Use-after-free
 * - Buffer overflows
 * - Uninitialized memory access
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <stdint.h>
#include "../common.h"
#include "../test_orchestrator.h"

// Function declarations for test orchestrator
extern int initialize_test_orchestrator(const char* history_file_path);
extern void cleanup_test_orchestrator(void);
extern void* create_test_context(const char* test_class, const char* test_method);
extern int finalize_test_context(void* context_ptr);
extern int update_test_context(void* context_ptr, double response_time_ms, double memory_usage_mb,
                              uint32_t query_count, double cache_hit_ratio, double performance_score,
                              const char* grade);
// update_test_metrics is already declared in test_orchestrator.h with correct signature
extern int update_n_plus_one_analysis(void* context_ptr, int has_n_plus_one, int severity_level,
                                     const char* query_signature);

// Function declarations for query analyzer
extern void reset_query_analyzer(void);
extern int analyze_query(const char* query_text, double execution_time);
extern int get_duplicate_queries(char* result_buffer, size_t buffer_size);
extern int detect_n_plus_one_patterns(void);
extern void get_query_statistics(uint64_t* total_queries, uint64_t* n_plus_one_detected,
                                uint64_t* similar_queries, int* active_clusters);

// Function declarations for metrics engine
extern int64_t start_performance_monitoring_enhanced(const char* operation_name, const char* operation_type);
extern MercuryMetrics* stop_performance_monitoring_enhanced(int64_t session_id);
extern double get_elapsed_time_ms(const MercuryMetrics* metrics);
extern double get_memory_usage_mb(const MercuryMetrics* metrics);
extern uint32_t get_query_count(const MercuryMetrics* metrics);

// Function declarations for configuration
extern int load_binary_configuration(const char* config_path);
extern int save_binary_configuration(const char* config_path);
extern int query_history_entries(const char* test_class_filter, const char* test_method_filter,
                                uint64_t start_timestamp, uint64_t end_timestamp,
                                char* result_buffer, size_t buffer_size);

int main() {
    printf("=== Mercury Memory Check Test Suite ===\n");
    printf("Testing memory management in all C modules\n\n");
    
    // TEST 1: Test Orchestrator Memory Management
    printf("[1] Testing orchestrator memory management...\n");
    {
        // Initialize and cleanup multiple times to test repeated allocation/deallocation
        for (int i = 0; i < 3; i++) {
            printf("  Iteration %d/3\n", i + 1);
            
            // Initialize orchestrator
            if (initialize_test_orchestrator("/tmp/memcheck.bin") != 0) {
                printf("    Failed to initialize orchestrator\n");
                return 1;
            }
            
            // Create multiple contexts
            void* contexts[10];
            for (int j = 0; j < 10; j++) {
                char test_class[64];
                char test_method[64];
                snprintf(test_class, sizeof(test_class), "MemTest%d", j);
                snprintf(test_method, sizeof(test_method), "test_memory_%d", j);
                
                contexts[j] = create_test_context(test_class, test_method);
                assert(contexts[j] != NULL);
                
                // Update with various data
                if (update_test_context(contexts[j], 
                    100.0 + j, 50.0 + j, 10 + j, 0.9, 85.0 + j, "A") != 0) {
                    printf("    Failed to update context %d\n", j);
                }
                
                // Add N+1 analysis
                update_n_plus_one_analysis(contexts[j], j % 2, j % 3,
                    "SELECT * FROM test WHERE id = ?");
            }
            
            // Finalize all contexts
            for (int j = 0; j < 10; j++) {
                if (finalize_test_context(contexts[j]) != 0) {
                    printf("    Warning: Failed to finalize context %d\n", j);
                }
            }
            
            // Test configuration save/load
            save_binary_configuration("/tmp/memcheck_config.bin");
            load_binary_configuration("/tmp/memcheck_config.bin");
            
            // Query history
            char history_buffer[4096];
            query_history_entries("MemTest", NULL, 0, UINT64_MAX, 
                                history_buffer, sizeof(history_buffer));
            
            // Cleanup
            cleanup_test_orchestrator();
        }
        printf("  ✓ Orchestrator memory test passed\n");
    }
    
    // TEST 2: Query Analyzer Memory Management
    printf("\n[2] Testing query analyzer memory management...\n");
    {
        reset_query_analyzer();
        
        // Analyze many queries to test internal buffer management
        for (int i = 0; i < 100; i++) {
            char query[256];
            snprintf(query, sizeof(query), 
                    "SELECT * FROM table_%d WHERE id = %d", i % 10, i);
            
            int result = analyze_query(query, 1.5 + (i * 0.1));
            (void)result; // Suppress unused warning
        }
        
        // Test duplicate query detection
        char result_buffer[4096];
        int dup_result = get_duplicate_queries(result_buffer, sizeof(result_buffer));
        (void)dup_result;
        
        // Test N+1 pattern detection
        int n_plus_one = detect_n_plus_one_patterns();
        (void)n_plus_one;
        
        // Get statistics
        uint64_t total_queries, n_plus_one_detected, similar_queries;
        int active_clusters;
        get_query_statistics(&total_queries, &n_plus_one_detected, 
                           &similar_queries, &active_clusters);
        
        // Reset should free all internal memory
        reset_query_analyzer();
        printf("  ✓ Query analyzer memory test passed\n");
    }
    
    // TEST 3: Metrics Engine Memory Management
    printf("\n[3] Testing metrics engine memory management...\n");
    {
        // Start and stop many monitoring sessions
        for (int i = 0; i < 50; i++) {
            char op_name[64];
            snprintf(op_name, sizeof(op_name), "MemOp%d", i);
            
            int64_t session_id = start_performance_monitoring_enhanced(op_name, "test");
            if (session_id <= 0) {
                printf("  Warning: Failed to start monitoring session %d (id=%ld)\n", i, (long)session_id);
                continue;
            }
            
            // Simulate some work
            usleep(100);
            
            MercuryMetrics* metrics = stop_performance_monitoring_enhanced(session_id);
            if (metrics == NULL) {
                printf("  Warning: Failed to get metrics for session %ld\n", (long)session_id);
                continue;
            }
            
            // Use the metrics
            double elapsed = get_elapsed_time_ms(metrics);
            double memory = get_memory_usage_mb(metrics);
            uint32_t queries = get_query_count(metrics);
            (void)elapsed;
            (void)memory;
            (void)queries;
            
            // Free the metrics
            mercury_aligned_free(metrics);
        }
        printf("  ✓ Metrics engine memory test passed\n");
    }
    
    // TEST 4: Error Path Memory Management
    printf("\n[4] Testing error path memory management...\n");
    {
        // Initialize for error testing
        initialize_test_orchestrator("/tmp/memcheck_error.bin");
        
        // Test with NULL parameters
        void* ctx = create_test_context(NULL, NULL);
        if (ctx) {
            finalize_test_context(ctx);
        }
        
        // Test with empty strings
        ctx = create_test_context("", "");
        if (ctx) {
            finalize_test_context(ctx);
        }
        
        // Test with very long strings
        char long_string[1024];
        memset(long_string, 'A', sizeof(long_string) - 1);
        long_string[sizeof(long_string) - 1] = '\0';
        ctx = create_test_context(long_string, long_string);
        if (ctx) {
            finalize_test_context(ctx);
        }
        
        // Test with invalid session IDs
        MercuryMetrics* metrics = stop_performance_monitoring_enhanced(-1);
        if (metrics) {
            mercury_aligned_free(metrics);
        }
        
        metrics = stop_performance_monitoring_enhanced(999999);
        if (metrics) {
            mercury_aligned_free(metrics);
        }
        
        // Test with NULL query
        int result = analyze_query(NULL, 0.0);
        (void)result;
        
        // Test with empty query
        result = analyze_query("", 0.0);
        (void)result;
        
        cleanup_test_orchestrator();
        printf("  ✓ Error path memory test passed\n");
    }
    
    // TEST 5: Stress Test - Rapid Allocation/Deallocation
    printf("\n[5] Testing rapid allocation/deallocation...\n");
    {
        initialize_test_orchestrator("/tmp/memcheck_stress.bin");
        
        // Create and destroy contexts rapidly
        for (int i = 0; i < 500; i++) {
            void* ctx = create_test_context("StressTest", "rapid");
            assert(ctx != NULL);
            
            // Immediately finalize
            finalize_test_context(ctx);
            
            // Also test metrics engine rapid alloc/free
            if (i % 10 == 0) {
                int64_t sid = start_performance_monitoring_enhanced("Stress", "rapid");
                MercuryMetrics* m = stop_performance_monitoring_enhanced(sid);
                if (m) {
                    mercury_aligned_free(m);
                }
            }
        }
        
        cleanup_test_orchestrator();
        printf("  ✓ Stress test passed\n");
    }
    
    // TEST 6: Boundary Conditions
    printf("\n[6] Testing boundary conditions...\n");
    {
        initialize_test_orchestrator("/tmp/memcheck_boundary.bin");
        
        // Test with maximum contexts
        void* contexts[256];
        int max_contexts = 256;
        int created = 0;
        
        for (int i = 0; i < max_contexts; i++) {
            contexts[i] = create_test_context("Boundary", "max_test");
            if (contexts[i] == NULL) {
                break;
            }
            created++;
        }
        
        printf("  Created %d contexts\n", created);
        
        // Clean up all created contexts
        for (int i = 0; i < created; i++) {
            finalize_test_context(contexts[i]);
        }
        
        // Test with very large buffer requests
        char* large_buffer = malloc(1024 * 1024); // 1MB
        if (large_buffer) {
            int result = get_duplicate_queries(large_buffer, 1024 * 1024);
            (void)result;
            free(large_buffer);
        }
        
        cleanup_test_orchestrator();
        printf("  ✓ Boundary test passed\n");
    }
    
    // TEST 7: Deliberate Memory Leak Test (to verify Valgrind detection)
    printf("\n[7] Testing memory leak detection (deliberate leaks)...\n");
    {
        // This test only runs when ENABLE_LEAK_TEST is set
        // This allows us to verify Valgrind actually catches leaks
        if (getenv("ENABLE_LEAK_TEST")) {
            printf("  Creating deliberate memory leaks for testing...\n");
            
            // Leak 1: Malloc without free
            void* leak1 = malloc(1024);
            memset(leak1, 0xAA, 1024);
            (void)leak1; // Suppress unused warning
            
            // Leak 2: Lost pointer
            void* leak2 = malloc(2048);
            memset(leak2, 0xBB, 2048);
            leak2 = malloc(512); // Lost original allocation
            free(leak2); // Only frees the 512 byte block
            
            // Leak 3: Partial free in linked structure
            typedef struct Node {
                struct Node* next;
                char data[256];
            } Node;
            
            Node* head = malloc(sizeof(Node));
            head->next = malloc(sizeof(Node));
            head->next->next = malloc(sizeof(Node));
            head->next->next->next = NULL;
            
            // Only free head, leak the rest
            free(head);
            
            printf("  ✓ Deliberate leaks created (should be detected by Valgrind)\n");
        } else {
            printf("  Skipped (set ENABLE_LEAK_TEST=1 to test leak detection)\n");
        }
    }
    
    // TEST 8: Memory Corruption Tests
    printf("\n[8] Testing memory corruption detection...\n");
    {
        if (getenv("ENABLE_CORRUPTION_TEST")) {
            printf("  Testing buffer overflows and use-after-free...\n");
            
            // Test 1: Buffer overflow (write past end)
            char* buffer = malloc(16);
            strcpy(buffer, "This string is definitely too long for 16 bytes");
            free(buffer);
            
            // Test 2: Use after free
            char* ptr = malloc(32);
            strcpy(ptr, "Valid data");
            free(ptr);
            // This should be detected by Valgrind or AddressSanitizer
            ptr[0] = 'X'; // Use after free!
            
            // Test 3: Double free
            void* ptr2 = malloc(64);
            free(ptr2);
            free(ptr2); // Double free!
            
            printf("  ✓ Corruption tests executed (should trigger Valgrind errors)\n");
        } else {
            printf("  Skipped (set ENABLE_CORRUPTION_TEST=1 to test corruption detection)\n");
        }
    }
    
    // Note: Metrics engine cleanup is automatic
    
    printf("\n=== All memory tests completed successfully ===\n");
    printf("Run with valgrind to check for memory leaks:\n");
    printf("  valgrind --leak-check=full --show-leak-kinds=all ./memcheck_test\n");
    
    printf("\nTo test leak detection: ENABLE_LEAK_TEST=1 valgrind ./memcheck_test\n");
    printf("To test corruption detection: ENABLE_CORRUPTION_TEST=1 valgrind ./memcheck_test\n");
    
    return 0;
}