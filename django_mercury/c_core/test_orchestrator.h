/**
 * @file test_orchestrator.h
 * @brief Public interface for the test orchestrator library
 */

#ifndef TEST_ORCHESTRATOR_H
#define TEST_ORCHESTRATOR_H

#include <stdint.h>
#include <stdbool.h>

// TestContext structure
// NOTE: This structure is exposed for testing purposes only
// Production code should treat it as opaque
typedef struct TestContext {
    // Test identification
    int context_id;
    char test_class[128];
    char test_method[128];
    uint64_t start_time;
    uint64_t end_time;
    
    // Configuration
    struct {
        double response_time_threshold;
        double memory_threshold_mb;
        uint32_t max_queries;
        double min_cache_hit_ratio;
    } config;
    
    // Metrics
    double response_time_ms;
    double memory_usage_mb;
    uint32_t query_count;
    double cache_hit_ratio;
    double performance_score;
    char grade[4];
    
    // Status
    bool is_active;
    bool has_violations;
    uint64_t violation_flags;
    
    // N+1 Detection
    bool has_n_plus_one;
    int severity_level;
    char optimization_suggestion[256];
    
} TestContext;

// === PUBLIC API ===

// Initialize the test orchestrator
int initialize_test_orchestrator(const char* history_file_path);

// Cleanup and shutdown
void cleanup_test_orchestrator(void);

// Create a new test context
void* create_test_context(const char* test_class, const char* test_method);

// Destroy a test context
void destroy_test_context(void* context);

// Update test metrics
int update_test_metrics(void* context_ptr, double response_time_ms, double memory_usage_mb,
                        uint32_t query_count, double cache_hit_ratio, double performance_score,
                        const char* grade);

// Update N+1 analysis
int update_n_plus_one_analysis(void* context_ptr, int has_n_plus_one, int severity_level,
                               const char* optimization_suggestion);

// Finalize test context
int finalize_test_context(void* context_ptr);

// Get orchestrator statistics
void get_orchestrator_statistics(uint64_t* total_tests, uint64_t* total_violations,
                                uint64_t* total_n_plus_one, size_t* active_contexts,
                                uint64_t* history_entries);

// Configuration management
int load_binary_configuration(const char* config_path);
int save_binary_configuration(const char* config_path);

// Query history
int query_history_entries(const char* test_class_filter, const char* test_method_filter,
                         uint64_t start_timestamp, uint64_t end_timestamp,
                         char* result_buffer, size_t buffer_size);

#endif // TEST_ORCHESTRATOR_H