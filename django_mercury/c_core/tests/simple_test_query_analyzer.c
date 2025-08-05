/**
 * @file simple_test_query_analyzer.c
 * @brief Clean tests for query analyzer functionality
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include "../common.h"
#include "simple_tests.h"

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

// Function declarations for query analyzer API
extern int analyze_query(const char* query_text, double execution_time);
extern int get_duplicate_queries(char* result_buffer, size_t buffer_size);
extern int detect_n_plus_one_patterns(void);
extern void reset_query_analyzer(void);
extern void get_query_statistics(uint64_t* total_queries, uint64_t* n_plus_one_detected,
                               uint64_t* similar_queries, int* active_clusters);
extern int get_n_plus_one_severity(void);
extern int get_n_plus_one_cause(void);
extern const char* get_optimization_suggestion(void);
extern void analyzer_clear_cache(void);

int test_query_analyzer_initialization(void) {
    // Reset analyzer to ensure clean state
    reset_query_analyzer();
    
    // Test initial statistics
    uint64_t total_queries, n_plus_one_detected, similar_queries;
    int active_clusters;
    
    get_query_statistics(&total_queries, &n_plus_one_detected, &similar_queries, &active_clusters);
    
    ASSERT(total_queries == 0, "Initial total queries should be 0");
    ASSERT(n_plus_one_detected == 0, "Initial N+1 detections should be 0");
    ASSERT(similar_queries == 0, "Initial similar queries should be 0");
    ASSERT(active_clusters == 0, "Initial active clusters should be 0");
    
    // Test initial N+1 state
    ASSERT(detect_n_plus_one_patterns() == 0, "No N+1 patterns should be detected initially");
    ASSERT(get_n_plus_one_severity() == 0, "Initial N+1 severity should be 0");
    ASSERT(get_n_plus_one_cause() == 0, "Initial N+1 cause should be 0");
    
    const char* suggestion = get_optimization_suggestion();
    ASSERT(suggestion != NULL, "Optimization suggestion should not be NULL");
    ASSERT(strlen(suggestion) > 0, "Optimization suggestion should not be empty");
    
    return 1;
}

int test_single_query_analysis(void) {
    // Reset analyzer for clean test
    reset_query_analyzer();
    
    // Test analyzing a simple SELECT query
    const char* select_query = "SELECT * FROM users WHERE id = 1";
    int result = analyze_query(select_query, 2.5);
    ASSERT(result == 0, "Simple SELECT query analysis should succeed");
    
    // Check statistics after one query
    uint64_t total_queries, n_plus_one_detected, similar_queries;
    int active_clusters;
    
    get_query_statistics(&total_queries, &n_plus_one_detected, &similar_queries, &active_clusters);
    ASSERT(total_queries == 1, "Should have analyzed 1 query");
    
    // Test different query types
    ASSERT(analyze_query("INSERT INTO users (name) VALUES ('test')", 1.0) == 0, 
           "INSERT query analysis should succeed");
    ASSERT(analyze_query("UPDATE users SET name = 'test' WHERE id = 1", 1.5) == 0,
           "UPDATE query analysis should succeed");
    ASSERT(analyze_query("DELETE FROM users WHERE id = 1", 0.5) == 0,
           "DELETE query analysis should succeed");
    
    get_query_statistics(&total_queries, &n_plus_one_detected, &similar_queries, &active_clusters);
    ASSERT(total_queries == 4, "Should have analyzed 4 queries total");
    
    return 1;
}

int test_duplicate_query_detection(void) {
    reset_query_analyzer();
    
    // Execute same query multiple times
    const char* query = "SELECT * FROM products WHERE category_id = 5";
    for (int i = 0; i < 5; i++) {
        ASSERT(analyze_query(query, 1.0 + i * 0.1) == 0, "Query analysis should succeed");
    }
    
    // Check for duplicates
    char duplicate_buffer[1024];
    int dup_result = get_duplicate_queries(duplicate_buffer, sizeof(duplicate_buffer));
    ASSERT(dup_result >= 0, "Get duplicate queries should succeed");
    ASSERT(strstr(duplicate_buffer, "products") != NULL, "Should find duplicate product queries");
    
    return 1;
}

int test_n_plus_one_detection(void) {
    reset_query_analyzer();
    
    // Simulate N+1 pattern
    ASSERT(analyze_query("SELECT * FROM posts", 5.0) == 0, "Posts query should succeed");
    
    // Execute many similar queries (N+1 pattern)
    for (int i = 1; i <= 20; i++) {
        char query[256];
        snprintf(query, sizeof(query), "SELECT * FROM comments WHERE post_id = %d", i);
        ASSERT(analyze_query(query, 0.5) == 0, "Comment query should succeed");
    }
    
    // Check N+1 detection
    int n_plus_one = detect_n_plus_one_patterns();
    ASSERT(n_plus_one > 0, "Should detect N+1 pattern");
    
    int severity = get_n_plus_one_severity();
    ASSERT(severity > 0, "N+1 severity should be greater than 0");
    
    const char* suggestion = get_optimization_suggestion();
    ASSERT(suggestion != NULL && strlen(suggestion) > 0, "Should provide optimization suggestion");
    
    return 1;
}

int test_query_statistics(void) {
    reset_query_analyzer();
    
    // Mix of queries
    ASSERT(analyze_query("SELECT * FROM users", 2.0) == 0, "Users query should succeed");
    ASSERT(analyze_query("SELECT * FROM users WHERE active = 1", 1.8) == 0, "Active users query should succeed");
    ASSERT(analyze_query("SELECT * FROM posts WHERE user_id = 1", 1.0) == 0, "Posts query should succeed");
    
    uint64_t total_queries, n_plus_one_detected, similar_queries;
    int active_clusters;
    
    get_query_statistics(&total_queries, &n_plus_one_detected, &similar_queries, &active_clusters);
    
    ASSERT(total_queries == 3, "Should have 3 total queries");
    ASSERT(active_clusters > 0, "Should have active query clusters");
    
    // Test that we have some statistics
    ASSERT(total_queries > 0, "Should have tracked queries");
    ASSERT(active_clusters >= 0, "Cluster count should be non-negative");
    
    return 1;
}

int test_concurrent_analyzer_access(void) {
    reset_query_analyzer();
    
    // Simple concurrent test - just verify no crashes
    const int num_threads = 4;
    const int queries_per_thread = 10;
    
    // Thread function
    void* analyzer_thread(void* arg) {
        int thread_id = *(int*)arg;
        for (int i = 0; i < queries_per_thread; i++) {
            char query[256];
            snprintf(query, sizeof(query), "SELECT * FROM table_%d WHERE id = %d", thread_id, i);
            analyze_query(query, 0.1 * i);
        }
        return NULL;
    }
    
    pthread_t threads[4];
    int thread_ids[4];
    
    // Start threads
    for (int i = 0; i < num_threads; i++) {
        thread_ids[i] = i;
        pthread_create(&threads[i], NULL, analyzer_thread, &thread_ids[i]);
    }
    
    // Wait for threads
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    uint64_t total_queries, n_plus_one_detected, similar_queries;
    int active_clusters;
    
    get_query_statistics(&total_queries, &n_plus_one_detected, &similar_queries, &active_clusters);
    ASSERT(total_queries == num_threads * queries_per_thread, "Should have analyzed all queries");
    
    return 1;
}

int main(void) {
    QUIET_MODE_INIT();  // Initialize quiet mode from TEST_VERBOSE env var
    TEST_SUITE_START("Query Analyzer Tests");
    
    RUN_TEST(test_query_analyzer_initialization);
    RUN_TEST(test_single_query_analysis);
    RUN_TEST(test_duplicate_query_detection);
    RUN_TEST(test_n_plus_one_detection);
    RUN_TEST(test_query_statistics);
    RUN_TEST(test_concurrent_analyzer_access);
    
    TEST_SUITE_END();
    
    return (failed_tests == 0) ? 0 : 1;
}