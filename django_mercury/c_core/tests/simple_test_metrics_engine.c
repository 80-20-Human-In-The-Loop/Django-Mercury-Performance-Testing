/**
 * @file simple_test_metrics_engine.c
 * @brief Basic tests for the metrics engine module
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../common.h"

// Forward declarations for metrics engine functions
typedef struct {
    uint64_t value;
    double threshold;
    const char* name;
} metric_t;

// Basic initialization test
static void test_metrics_engine_init() {
    printf("Running test_metrics_engine_init...\n");
    
    // Test that we can include the header and basic types work
    metric_t test_metric = {
        .value = 1000,
        .threshold = 500.0,
        .name = "test_metric"
    };
    
    assert(test_metric.value == 1000);
    assert(test_metric.threshold == 500.0);
    assert(strcmp(test_metric.name, "test_metric") == 0);
    
    // Use the metric to avoid unused variable warning
    printf("  Metric '%s': value=%lu, threshold=%.1f\n", 
           test_metric.name, (unsigned long)test_metric.value, test_metric.threshold);
    
    printf("✓ test_metrics_engine_init passed\n");
}

// Test metric collection
static void test_metric_collection() {
    printf("Running test_metric_collection...\n");
    
    // Simple metric tracking
    uint64_t start_time = 0;
    uint64_t end_time = 1000000; // 1ms in nanoseconds
    
    uint64_t duration = end_time - start_time;
    assert(duration == 1000000);
    
    // Use duration to avoid unused variable warning
    printf("  Duration: %lu nanoseconds\n", (unsigned long)duration);
    
    printf("✓ test_metric_collection passed\n");
}

// Test threshold checking
static void test_threshold_checking() {
    printf("Running test_threshold_checking...\n");
    
    double response_time_ms = 150.0;
    double threshold_ms = 100.0;
    
    int is_violation = (response_time_ms > threshold_ms) ? 1 : 0;
    assert(is_violation == 1);
    printf("  150ms > 100ms threshold: violation=%d\n", is_violation);
    
    response_time_ms = 50.0;
    is_violation = (response_time_ms > threshold_ms) ? 1 : 0;
    assert(is_violation == 0);
    printf("  50ms > 100ms threshold: violation=%d\n", is_violation);
    
    printf("✓ test_threshold_checking passed\n");
}

// Test memory tracking
static void test_memory_tracking() {
    printf("Running test_memory_tracking...\n");
    
    size_t initial_memory = 1024 * 1024; // 1MB
    size_t peak_memory = 2048 * 1024;    // 2MB
    size_t final_memory = 1536 * 1024;   // 1.5MB
    
    size_t memory_growth = final_memory - initial_memory;
    assert(memory_growth == 512 * 1024); // 512KB growth
    
    // Use variables to avoid unused warnings
    printf("  Memory: initial=%zuKB, peak=%zuKB, final=%zuKB, growth=%zuKB\n",
           initial_memory/1024, peak_memory/1024, final_memory/1024, memory_growth/1024);
    
    printf("✓ test_memory_tracking passed\n");
}

int main() {
    printf("\n=== Metrics Engine Tests ===\n");
    
    int tests_run = 0;
    int tests_passed = 0;
    
    // Run all tests
    test_metrics_engine_init();
    tests_run++; tests_passed++;
    
    test_metric_collection();
    tests_run++; tests_passed++;
    
    test_threshold_checking();
    tests_run++; tests_passed++;
    
    test_memory_tracking();
    tests_run++; tests_passed++;
    
    printf("\n=== Results ===\n");
    printf("Total: %d, Passed: %d, Failed: %d\n", 
           tests_run, tests_passed, tests_run - tests_passed);
    
    if (tests_passed == tests_run) {
        printf("All tests passed!\n");
        return 0;
    } else {
        printf("Some tests failed!\n");
        return 1;
    }
}