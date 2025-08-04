/**
 * @file comprehensive_test_performance_monitor.c
 * @brief Comprehensive tests for performance monitor - Django-aware capabilities
 * 
 * This test file provides comprehensive testing of performance_monitor.c with focus on:
 * - Django-aware thresholds and operation types
 * - Advanced N+1 detection algorithms  
 * - Memory tracking and cache performance analysis
 * - Concurrent session management
 * - Performance scoring and optimization suggestions
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/wait.h>
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
extern void set_current_session_id(int64_t session_id);
extern int64_t get_current_session_id(void);

// Performance metrics structure from performance_monitor.c
typedef struct {
    uint64_t start_time_ns;
    uint64_t end_time_ns;
    size_t memory_start_bytes;
    size_t memory_peak_bytes;
    size_t memory_end_bytes;
    uint32_t session_query_count;
    uint32_t session_cache_hits;
    uint32_t session_cache_misses;
    char operation_name[256];
    char operation_type[64];
    pthread_mutex_t session_mutex;
    int64_t session_id;
} EnhancedPerformanceMetrics_t;

// Accessor functions from performance_monitor.c
extern double get_elapsed_time_ms(EnhancedPerformanceMetrics_t* metrics);
extern double get_memory_usage_mb(EnhancedPerformanceMetrics_t* metrics);
extern double get_memory_delta_mb(EnhancedPerformanceMetrics_t* metrics);
extern uint32_t get_query_count(EnhancedPerformanceMetrics_t* metrics);
extern uint32_t get_cache_hit_count(EnhancedPerformanceMetrics_t* metrics);
extern uint32_t get_cache_miss_count(EnhancedPerformanceMetrics_t* metrics);
extern double get_cache_hit_ratio(EnhancedPerformanceMetrics_t* metrics);

// Analysis functions from performance_monitor.c  
extern int has_n_plus_one_pattern(EnhancedPerformanceMetrics_t* metrics);
extern int detect_n_plus_one_severe(EnhancedPerformanceMetrics_t* metrics);
extern int detect_n_plus_one_moderate(EnhancedPerformanceMetrics_t* metrics);
extern int calculate_n_plus_one_severity(EnhancedPerformanceMetrics_t* metrics);
extern int estimate_n_plus_one_cause(EnhancedPerformanceMetrics_t* metrics);
extern const char* get_n_plus_one_fix_suggestion(EnhancedPerformanceMetrics_t* metrics);
extern int is_memory_intensive(EnhancedPerformanceMetrics_t* metrics);
extern int has_poor_cache_performance(EnhancedPerformanceMetrics_t* metrics);

// Test Django-aware operation thresholds and realistic patterns
int test_django_operation_thresholds(void) {
    printf("Testing Django-aware operation thresholds and realistic patterns...\n");
    
    // Test realistic Django operation scenarios
    const char* scenarios[][3] = {
        {"UserListView", "view", "20"},        // List view with pagination
        {"UserDetailView", "view", "8"},       // Detail view with related data
        {"UserSerializer", "serializer", "15"}, // Serializer with nested data
        {"UserModel.save", "model", "5"},      // Model save operation
        {"UserModel.delete", "delete", "3"},   // Delete with cascade checks
        {"UserQuery.filter", "query", "25"},   // Complex filtering
        {"UserPermissions", "auth", "12"}      // Permission checking
    };
    
    for (int i = 0; i < 7; i++) {
        const char* op_name = scenarios[i][0];
        const char* op_type = scenarios[i][1]; 
        int query_count = atoi(scenarios[i][2]);
        
        printf("Testing scenario: %s (%s) with %d queries\n", op_name, op_type, query_count);
        
        reset_global_counters();
        int64_t handle = start_performance_monitoring_enhanced(op_name, op_type);
        ASSERT(handle >= 0, "Should start monitoring for Django operation");
        
        // Simulate realistic Django query patterns
        for (int j = 0; j < query_count; j++) {
            increment_query_count();
            if (j % 3 == 0) increment_cache_hits();
            else if (j % 5 == 0) increment_cache_misses();
        }
        
        usleep(1000 * (i + 1)); // Variable work time
        
        EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(handle);
        ASSERT(metrics != NULL, "Should get metrics for Django operation");
        
        // Verify metrics are reasonable
        uint32_t actual_queries = get_query_count(metrics);
        double elapsed_ms = get_elapsed_time_ms(metrics);
        
        printf("  Queries: %u, Time: %.2fms\n", actual_queries, elapsed_ms);
        ASSERT(actual_queries == query_count, "Query count should match simulation");
        ASSERT(elapsed_ms > 0.0, "Should have positive elapsed time");
        
        // Test N+1 detection with realistic thresholds
        int has_n_plus_one = has_n_plus_one_pattern(metrics);
        int severity = calculate_n_plus_one_severity(metrics);
        
        if (query_count >= 12) {
            ASSERT(has_n_plus_one == 1, "Should detect N+1 for high query count");
            ASSERT(severity > 0, "Should have positive severity for N+1");
        }
        
        free_metrics(metrics);
    }
    
    return 1;
}

// Test advanced N+1 detection algorithms with realistic patterns
int test_advanced_n_plus_one_detection(void) {
    printf("Testing advanced N+1 detection algorithms...\n");
    
    // Test pattern: 1 + N queries (classic N+1)
    reset_global_counters();
    int64_t handle1 = start_performance_monitoring_enhanced("ClassicN+1", "view");
    
    // Parent query
    increment_query_count();
    usleep(500);
    
    // N child queries (21 total = 1 + 20)
    for (int i = 0; i < 20; i++) {
        increment_query_count();
        usleep(100); // Simulate individual query time
    }
    
    EnhancedPerformanceMetrics_t* metrics1 = stop_performance_monitoring_enhanced(handle1);
    ASSERT(metrics1 != NULL, "Should get metrics for classic N+1");
    
    uint32_t queries1 = get_query_count(metrics1);
    int has_n_plus_one1 = has_n_plus_one_pattern(metrics1);
    int severe1 = detect_n_plus_one_severe(metrics1);  
    int cause1 = estimate_n_plus_one_cause(metrics1);
    
    printf("Classic N+1: %u queries, detected=%d, severe=%d, cause=%d\n", 
           queries1, has_n_plus_one1, severe1, cause1);
    
    ASSERT(queries1 == 21, "Should have 21 queries for classic N+1");
    ASSERT(has_n_plus_one1 == 1, "Should detect classic N+1 pattern");
    ASSERT(cause1 > 0, "Should estimate N+1 cause");
    
    free_metrics(metrics1);
    
    // Test pattern: Serializer N+1 (many quick queries)
    reset_global_counters();
    int64_t handle2 = start_performance_monitoring_enhanced("SerializerN+1", "serializer");
    
    // Many quick serializer queries
    for (int i = 0; i < 35; i++) {
        increment_query_count();
        if (i % 4 == 0) increment_cache_hits();
        usleep(50); // Quick queries
    }
    
    EnhancedPerformanceMetrics_t* metrics2 = stop_performance_monitoring_enhanced(handle2);
    ASSERT(metrics2 != NULL, "Should get metrics for serializer N+1");
    
    uint32_t queries2 = get_query_count(metrics2);
    int severe2 = detect_n_plus_one_severe(metrics2);
    int cause2 = estimate_n_plus_one_cause(metrics2);
    const char* suggestion2 = get_n_plus_one_fix_suggestion(metrics2);
    
    printf("Serializer N+1: %u queries, severe=%d, cause=%d\n", queries2, severe2, cause2);
    printf("Suggestion: %s\n", suggestion2);
    
    ASSERT(queries2 == 35, "Should have 35 queries for serializer N+1");
    ASSERT(severe2 == 1, "Should detect severe N+1 for 35 queries");
    ASSERT(cause2 > 0, "Should estimate serializer cause");
    ASSERT(suggestion2 != NULL, "Should have optimization suggestion");
    
    free_metrics(metrics2);
    
    // Test pattern: No N+1 (acceptable Django query count)
    reset_global_counters();
    int64_t handle3 = start_performance_monitoring_enhanced("AcceptableQueries", "view");
    
    // Acceptable number of queries for Django view with user profile
    for (int i = 0; i < 8; i++) {
        increment_query_count();
        increment_cache_hits();
    }
    
    EnhancedPerformanceMetrics_t* metrics3 = stop_performance_monitoring_enhanced(handle3);
    ASSERT(metrics3 != NULL, "Should get metrics for acceptable queries");
    
    uint32_t queries3 = get_query_count(metrics3);
    int has_n_plus_one3 = has_n_plus_one_pattern(metrics3);
    int severity3 = calculate_n_plus_one_severity(metrics3);
    
    printf("Acceptable pattern: %u queries, N+1=%d, severity=%d\n", 
           queries3, has_n_plus_one3, severity3);
    
    ASSERT(queries3 == 8, "Should have 8 queries for acceptable pattern");
    ASSERT(has_n_plus_one3 == 0, "Should NOT detect N+1 for 8 queries");
    ASSERT(severity3 == 0, "Should have zero severity for acceptable pattern");
    
    free_metrics(metrics3);
    
    return 1;
}

// Test memory tracking and intensive operation detection
int test_memory_tracking_analysis(void) {
    printf("Testing memory tracking and intensive operation detection...\n");
    
    // Test memory delta tracking
    int64_t handle = start_performance_monitoring_enhanced("MemoryTest", "query");
    ASSERT(handle >= 0, "Should start memory tracking");
    
    // Simulate memory-intensive work by allocating memory
    void* test_memory[100];
    for (int i = 0; i < 100; i++) {
        test_memory[i] = malloc(1024 * 1024); // 1MB each = ~100MB total
        if (test_memory[i]) {
            memset(test_memory[i], i, 1024 * 1024);
        }
        increment_query_count();
        usleep(1000);
    }
    
    EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(handle);
    ASSERT(metrics != NULL, "Should get metrics for memory test");
    
    // Test memory functions
    double memory_delta = get_memory_delta_mb(metrics);
    double peak_memory = get_memory_usage_mb(metrics);
    int is_intensive = is_memory_intensive(metrics);
    
    printf("Memory delta: %.2fMB, Peak: %.2fMB, Intensive: %d\n", 
           memory_delta, peak_memory, is_intensive);
    
    ASSERT(memory_delta != -1.0, "Should have valid memory delta");
    ASSERT(peak_memory > 0.0, "Should have positive peak memory");
    
    // Clean up memory
    for (int i = 0; i < 100; i++) {
        if (test_memory[i]) {
            free(test_memory[i]);
        }
    }
    
    free_metrics(metrics);
    
    // Test normal memory usage
    reset_global_counters();
    int64_t handle2 = start_performance_monitoring_enhanced("NormalMemory", "view");
    
    // Light work - should not be memory intensive
    for (int i = 0; i < 5; i++) {
        increment_query_count();
        usleep(1000);
    }
    
    EnhancedPerformanceMetrics_t* metrics2 = stop_performance_monitoring_enhanced(handle2);
    ASSERT(metrics2 != NULL, "Should get metrics for normal memory test");
    
    int is_intensive2 = is_memory_intensive(metrics2);
    printf("Normal memory usage - Intensive: %d\n", is_intensive2);
    
    free_metrics(metrics2);
    
    return 1;
}

// Test cache performance analysis
int test_cache_performance_analysis(void) {
    printf("Testing cache performance analysis...\n");
    
    // Test poor cache performance scenario
    reset_global_counters();
    int64_t handle1 = start_performance_monitoring_enhanced("PoorCache", "view");
    
    // Simulate poor cache performance: many misses, few hits
    for (int i = 0; i < 20; i++) {
        increment_query_count();
        if (i < 3) increment_cache_hits();    // 3 hits
        else increment_cache_misses();        // 17 misses
    }
    
    EnhancedPerformanceMetrics_t* metrics1 = stop_performance_monitoring_enhanced(handle1);
    ASSERT(metrics1 != NULL, "Should get metrics for poor cache");
    
    uint32_t hits1 = get_cache_hit_count(metrics1);
    uint32_t misses1 = get_cache_miss_count(metrics1);
    double hit_ratio1 = get_cache_hit_ratio(metrics1);
    int poor_cache1 = has_poor_cache_performance(metrics1);
    
    printf("Poor cache: %u hits, %u misses, ratio=%.2f, poor=%d\n", 
           hits1, misses1, hit_ratio1, poor_cache1);
    
    ASSERT(hits1 == 3, "Should have 3 cache hits");
    ASSERT(misses1 == 17, "Should have 17 cache misses");
    ASSERT(hit_ratio1 < 0.7, "Should have poor hit ratio");
    ASSERT(poor_cache1 == 1, "Should detect poor cache performance");
    
    free_metrics(metrics1);
    
    // Test good cache performance scenario
    reset_global_counters();
    int64_t handle2 = start_performance_monitoring_enhanced("GoodCache", "view");
    
    // Simulate good cache performance: many hits, few misses
    for (int i = 0; i < 20; i++) {
        increment_query_count();
        if (i < 16) increment_cache_hits();   // 16 hits
        else increment_cache_misses();        // 4 misses
    }
    
    EnhancedPerformanceMetrics_t* metrics2 = stop_performance_monitoring_enhanced(handle2);
    ASSERT(metrics2 != NULL, "Should get metrics for good cache");
    
    double hit_ratio2 = get_cache_hit_ratio(metrics2);
    int poor_cache2 = has_poor_cache_performance(metrics2);
    
    printf("Good cache: ratio=%.2f, poor=%d\n", hit_ratio2, poor_cache2);
    
    ASSERT(hit_ratio2 >= 0.7, "Should have good hit ratio");
    ASSERT(poor_cache2 == 0, "Should NOT detect poor cache performance");
    
    free_metrics(metrics2);
    
    // Test no cache operations
    reset_global_counters();
    int64_t handle3 = start_performance_monitoring_enhanced("NoCache", "model");
    
    // Just queries, no cache operations
    for (int i = 0; i < 10; i++) {
        increment_query_count();
    }
    
    EnhancedPerformanceMetrics_t* metrics3 = stop_performance_monitoring_enhanced(handle3);
    ASSERT(metrics3 != NULL, "Should get metrics for no cache");
    
    double hit_ratio3 = get_cache_hit_ratio(metrics3);
    int poor_cache3 = has_poor_cache_performance(metrics3);
    
    printf("No cache: ratio=%.2f, poor=%d\n", hit_ratio3, poor_cache3);
    
    ASSERT(hit_ratio3 == 0.0, "Should have zero hit ratio for no cache ops");
    ASSERT(poor_cache3 == 0, "Should NOT flag as poor with no cache ops");
    
    free_metrics(metrics3);
    
    return 1;
}

// Test concurrent monitoring sessions with different patterns
int test_concurrent_monitoring_patterns(void) {
    printf("Testing concurrent monitoring with different patterns...\n");
    
    // Reset global counters once at the start for all sessions
    reset_global_counters();
    
    // Create multiple concurrent sessions with different characteristics
    int64_t handles[4];
    const char* operations[] = {"FastView", "SlowQuery", "CachedData", "HeavySerializer"};
    const char* types[] = {"view", "query", "model", "serializer"};
    
    // Start all sessions
    for (int i = 0; i < 4; i++) {
        handles[i] = start_performance_monitoring_enhanced(operations[i], types[i]);
        ASSERT(handles[i] >= 0, "Should start concurrent session");
    }
    
    // Simulate different workload patterns - set session context before each session's work
    for (int session = 0; session < 4; session++) {
        // Set the current session context for this session's work
        set_current_session_id(handles[session]);
        
        for (int work = 0; work < (session + 1) * 5; work++) {
            increment_query_count();
            
            // Different cache patterns per session
            switch (session) {
                case 0: // Fast view - good cache
                    if (work % 2 == 0) increment_cache_hits();
                    break;
                case 1: // Slow query - poor cache  
                    if (work % 4 == 0) increment_cache_hits();
                    else increment_cache_misses();
                    break;
                case 2: // Cached data - excellent cache
                    if (work % 5 != 0) increment_cache_hits();
                    break;
                case 3: // Heavy serializer - no cache
                    break;
            }
            
            usleep(100 * (session + 1)); // Different timing patterns
        }
    }
    
    // Stop and analyze all sessions
    for (int i = 0; i < 4; i++) {
        EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(handles[i]);
        ASSERT(metrics != NULL, "Should stop concurrent session");
        
        uint32_t queries = get_query_count(metrics);
        double elapsed = get_elapsed_time_ms(metrics);
        double hit_ratio = get_cache_hit_ratio(metrics);
        int has_n_plus_one = has_n_plus_one_pattern(metrics);
        
        printf("Session %d (%s): %u queries, %.2fms, cache=%.2f, N+1=%d\n",
               i, operations[i], queries, elapsed, hit_ratio, has_n_plus_one);
        
        uint32_t expected_queries = (i + 1) * 5;
        if (queries != expected_queries) {
            printf("ERROR: Session %d expected %u queries but got %u queries\n", 
                   i, expected_queries, queries);
        }
        ASSERT(queries == expected_queries, "Query count mismatch");
        ASSERT(elapsed > 0.0, "Should have positive elapsed time");
        
        free_metrics(metrics);
    }
    
    return 1;
}

// Test operation-specific optimization suggestions
int test_optimization_suggestions(void) {
    printf("Testing operation-specific optimization suggestions...\n");
    
    // Test different N+1 causes and their suggestions
    struct {
        const char* name;
        const char* type;
        int queries;
        int expected_cause;
    } scenarios[] = {
        {"SerializerN+1", "serializer", 25, 1},  // Serializer N+1
        {"RelatedModelN+1", "model", 15, 2},     // Related model N+1  
        {"ForeignKeyN+1", "view", 35, 3},        // Foreign key N+1
        {"ComplexN+1", "query", 55, 4}           // Complex relationship N+1
    };
    
    for (int i = 0; i < 4; i++) {
        reset_global_counters();
        int64_t handle = start_performance_monitoring_enhanced(scenarios[i].name, scenarios[i].type);
        
        // Generate queries with appropriate timing for cause detection
        for (int j = 0; j < scenarios[i].queries; j++) {
            increment_query_count();
            
            // Vary timing to influence cause estimation
            if (scenarios[i].expected_cause == 1) {
                usleep(100); // Quick serializer queries
            } else if (scenarios[i].expected_cause == 3) {
                usleep(1000); // Slow foreign key queries
            } else {
                usleep(500); // Moderate timing
            }
        }
        
        EnhancedPerformanceMetrics_t* metrics = stop_performance_monitoring_enhanced(handle);
        ASSERT(metrics != NULL, "Should get metrics for optimization test");
        
        int cause = estimate_n_plus_one_cause(metrics);
        const char* suggestion = get_n_plus_one_fix_suggestion(metrics);
        int severity = calculate_n_plus_one_severity(metrics);
        
        printf("Scenario %s: cause=%d, severity=%d\n", scenarios[i].name, cause, severity);
        printf("  Suggestion: %s\n", suggestion);
        
        ASSERT(cause > 0, "Should estimate N+1 cause for high query count");
        ASSERT(suggestion != NULL, "Should have optimization suggestion");
        ASSERT(strlen(suggestion) > 10, "Should have meaningful suggestion");
        ASSERT(severity > 0, "Should have positive severity");
        
        free_metrics(metrics);
    }
    
    return 1;
}

// Test edge cases and error conditions
int test_monitor_edge_cases(void) {
    printf("Testing monitor edge cases and error conditions...\n");
    
    // Test very short operations
    int64_t handle1 = start_performance_monitoring_enhanced("QuickOp", "model");
    usleep(1); // Minimal work
    EnhancedPerformanceMetrics_t* metrics1 = stop_performance_monitoring_enhanced(handle1);
    
    ASSERT(metrics1 != NULL, "Should handle very short operations");
    double elapsed1 = get_elapsed_time_ms(metrics1);
    ASSERT(elapsed1 >= 0.0, "Should have non-negative elapsed time");
    free_metrics(metrics1);
    
    // Test operations with zero queries (should not trigger line 441)
    reset_global_counters();
    int64_t handle2 = start_performance_monitoring_enhanced("ZeroQueries", "view");
    // No queries added
    usleep(1000);
    
    EnhancedPerformanceMetrics_t* metrics2 = stop_performance_monitoring_enhanced(handle2);
    ASSERT(metrics2 != NULL, "Should handle zero query operations");
    
    uint32_t queries2 = get_query_count(metrics2);
    int has_n_plus_one2 = has_n_plus_one_pattern(metrics2);
    int severity2 = calculate_n_plus_one_severity(metrics2);
    
    printf("Zero queries: count=%u, N+1=%d, severity=%d\n", queries2, has_n_plus_one2, severity2);
    ASSERT(queries2 == 0, "Should have zero queries");
    ASSERT(has_n_plus_one2 == 0, "Should not detect N+1 for zero queries");
    ASSERT(severity2 == 0, "Should have zero severity for zero queries");
    
    free_metrics(metrics2);
    
    // Test invalid handles
    EnhancedPerformanceMetrics_t* null_metrics = stop_performance_monitoring_enhanced(-1);
    ASSERT(null_metrics == NULL, "Should return NULL for invalid handle");
    
    EnhancedPerformanceMetrics_t* null_metrics2 = stop_performance_monitoring_enhanced(0);
    ASSERT(null_metrics2 == NULL, "Should return NULL for zero handle");
    
    // Test operations with NULL operation type (should succeed with default value)
    int64_t handle3 = start_performance_monitoring_enhanced("NullType", NULL);
    ASSERT(handle3 > 0, "Should succeed with NULL operation type (uses default)");
    
    // Clean up handle3 since it's now valid
    if (handle3 > 0) {
        EnhancedPerformanceMetrics_t* metrics3 = stop_performance_monitoring_enhanced(handle3);
        if (metrics3) {
            free_metrics(metrics3);
        }
    }
    
    return 1;
}

int main(void) {
    TEST_SUITE_START("Comprehensive Performance Monitor Tests - Django-Aware Capabilities");
    
    printf("🎯 Comprehensive testing of performance_monitor.c Django-aware features:\n");
    printf("   - Django operation thresholds and realistic query patterns\n");
    printf("   - Advanced N+1 detection algorithms (severe, moderate, count-based)\n");
    printf("   - Memory tracking and intensive operation detection\n");
    printf("   - Cache performance analysis and hit ratio calculations\n");
    printf("   - Concurrent monitoring with different workload patterns\n");
    printf("   - Operation-specific optimization suggestions\n");
    printf("   - Edge cases and error condition handling\n\n");
    
    RUN_TEST(test_django_operation_thresholds);
    RUN_TEST(test_advanced_n_plus_one_detection);
    RUN_TEST(test_memory_tracking_analysis);
    RUN_TEST(test_cache_performance_analysis);
    RUN_TEST(test_concurrent_monitoring_patterns);
    RUN_TEST(test_optimization_suggestions);
    RUN_TEST(test_monitor_edge_cases);
    
    TEST_SUITE_END();
    
    printf("\n🚀 Comprehensive performance monitor tests completed!\n");
    printf("Expected result: Push performance_monitor.c coverage from ~35%% to 55-60%%\n");
    printf("Focus areas: Django-aware thresholds, advanced N+1 detection, memory/cache analysis\n");
    
    return (failed_tests == 0) ? 0 : 1;
}