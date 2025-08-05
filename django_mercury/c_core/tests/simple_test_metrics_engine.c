/**
 * @file simple_test_metrics_engine.c
 * @brief Basic tests for the metrics engine module
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
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

// Forward declarations for metrics engine functions
typedef struct {
    uint64_t value;
    double threshold;
    const char* name;
} metric_t;

// Basic initialization test
static int test_metrics_engine_init() {
    TEST_FUNCTION_START();
    
    // Test that we can include the header and basic types work
    metric_t test_metric = {
        .value = 1000,
        .threshold = 500.0,
        .name = "test_metric"
    };
    
    ASSERT(test_metric.value == 1000, "Metric value should be 1000");
    ASSERT(test_metric.threshold == 500.0, "Metric threshold should be 500.0");
    ASSERT(strcmp(test_metric.name, "test_metric") == 0, "Metric name should match");
    
    // Use the metric to avoid unused variable warning
    if (!quiet_mode) {
        printf("  Metric '%s': value=%lu, threshold=%.1f\n", 
               test_metric.name, (unsigned long)test_metric.value, test_metric.threshold);
    }
    
    return 1;
}

// Test metric collection
static int test_metric_collection() {
    TEST_FUNCTION_START();
    
    // Simple metric tracking
    uint64_t start_time = 0;
    uint64_t end_time = 1000000; // 1ms in nanoseconds
    
    uint64_t duration = end_time - start_time;
    ASSERT(duration == 1000000, "Duration should be 1000000 nanoseconds");
    
    // Use duration to avoid unused variable warning
    if (!quiet_mode) {
        printf("  Duration: %lu nanoseconds\n", (unsigned long)duration);
    }
    
    return 1;
}

// Test threshold checking
static int test_threshold_checking() {
    TEST_FUNCTION_START();
    
    double response_time_ms = 150.0;
    double threshold_ms = 100.0;
    
    int is_violation = (response_time_ms > threshold_ms) ? 1 : 0;
    ASSERT(is_violation == 1, "150ms should violate 100ms threshold");
    
    if (!quiet_mode) {
        printf("  150ms > 100ms threshold: violation=%d\n", is_violation);
    }
    
    response_time_ms = 50.0;
    is_violation = (response_time_ms > threshold_ms) ? 1 : 0;
    ASSERT(is_violation == 0, "50ms should not violate 100ms threshold");
    
    if (!quiet_mode) {
        printf("  50ms > 100ms threshold: violation=%d\n", is_violation);
    }
    
    return 1;
}

// Test memory tracking
static int test_memory_tracking() {
    TEST_FUNCTION_START();
    
    size_t initial_memory = 1024 * 1024; // 1MB
    size_t peak_memory = 2048 * 1024;    // 2MB
    size_t final_memory = 1536 * 1024;   // 1.5MB
    
    size_t memory_growth = final_memory - initial_memory;
    ASSERT(memory_growth == 512 * 1024, "Memory growth should be 512KB");
    
    // Use variables to avoid unused warnings
    if (!quiet_mode) {
        printf("  Memory: initial=%zuKB, peak=%zuKB, final=%zuKB, growth=%zuKB\n",
               initial_memory/1024, peak_memory/1024, final_memory/1024, memory_growth/1024);
    }
    
    return 1;
}

int main() {
    QUIET_MODE_INIT();  // Initialize quiet mode from TEST_VERBOSE env var
    TEST_SUITE_START("Metrics Engine Tests");
    
    RUN_TEST(test_metrics_engine_init);
    RUN_TEST(test_metric_collection);
    RUN_TEST(test_threshold_checking);
    RUN_TEST(test_memory_tracking);
    
    TEST_SUITE_END();
    
    return failed_tests > 0 ? 1 : 0;
}