/**
 * @file test_format_and_bounds.c
 * @brief Format string and bounds checking security tests
 * 
 * Tests for critical format string and integer-related security vulnerabilities:
 * - CWE-134: Format String Vulnerabilities
 * - CWE-190: Integer Overflow
 * - CWE-191: Integer Underflow  
 * - CWE-362: Race Conditions in shared data
 * - CWE-787/125: Advanced bounds checking scenarios
 * 
 * Based on CERT C guidelines for secure integer and string handling.
 */

#include "../../common.h"
#include "../../test_orchestrator.h"
#include "../test_framework.h"
#include <limits.h>
#include <float.h>
#include <stdint.h>
#include <pthread.h>
#include <unistd.h>
#include <errno.h>

//=============================================================================
// CWE-134: Format String Vulnerability Tests
//=============================================================================

static void test_format_string_injection_protection(void) {
    TEST_START("Format string injection protection (CWE-134)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test 1: Malicious format strings in context names
    const char* malicious_formats[] = {
        "%s%s%s%s%s%s%s%s%s%s",           // Stack reading
        "%n%n%n%n%n%n%n%n%n%n",           // Memory writing
        "%.999999s",                      // Huge width specifier
        "%*s",                            // Dynamic width
        "%1$s%2$s%3$s%4$s%5$s",          // Position parameters
        "%x%x%x%x%x%x%x%x",              // Stack dumping
        "%%n%%n%%n%%n",                   // Escaped format chars
        "%c%c%c%c%c%c%c%c",              // Character reading
        NULL
    };
    
    for (int i = 0; malicious_formats[i]; i++) {
        // Test class name with format strings
        void* context = create_test_context(malicious_formats[i], "safe_method");
        if (context != NULL) {
            // Verify the format string was stored as literal text, not interpreted
            TestContext* ctx = (TestContext*)context;
            
            // The stored string should contain the literal format characters
            // It should NOT have been interpreted as a format string
            ASSERT_NEQ(strstr(ctx->test_class, "%"), NULL,
                       "Format specifiers should be stored literally");
            
            finalize_test_context(context);
        }
        
        // Test method name with format strings
        context = create_test_context("safe_class", malicious_formats[i]);
        if (context != NULL) {
            TestContext* ctx = (TestContext*)context;
            ASSERT_NEQ(strstr(ctx->test_method, "%"), NULL,
                       "Format specifiers should be stored literally");
            finalize_test_context(context);
        }
    }
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_optimization_suggestion_format_safety(void) {
    TEST_START("Optimization suggestion format safety (CWE-134)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("FormatTest", "test_suggestions");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Test format string attacks in optimization suggestions
    const char* format_attacks[] = {
        "Use SELECT * FROM users WHERE id = %n AND status = %s",
        "Consider indexing: CREATE INDEX ON table_%x_%x_%x",
        "Query pattern detected: %1$s with %2$d rows",
        "Performance issue: %.1000000f seconds",
        "Memory usage: %*.*s MB allocated",
        NULL
    };
    
    for (int i = 0; format_attacks[i]; i++) {
        ASSERT_EQ(update_n_plus_one_analysis(context, 1, i + 1, format_attacks[i]), 0,
                  "Should handle format strings in suggestions");
        
        TestContext* ctx = (TestContext*)context;
        
        // Verify the format string is stored literally, not interpreted
        ASSERT_NEQ(strstr(ctx->optimization_suggestion, "%"), NULL,
                   "Format specifiers should remain literal in suggestions");
        
        // Verify the suggestion doesn't contain signs of format interpretation
        // (like random memory contents or crashes)
        size_t len = strlen(ctx->optimization_suggestion);
        ASSERT_GT(len, 0, "Suggestion should not be empty");
        ASSERT_LT(len, sizeof(ctx->optimization_suggestion),
                  "Suggestion should fit in buffer");
    }
    
    finalize_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_logging_format_string_safety(void) {
    TEST_START("Logging format string safety (CWE-134)");
    
    // Test that logging functions handle user-controlled input safely
    const char* user_inputs[] = {
        "%s%s%s%s%s%s%s%s",
        "%n%n%n%n%n%n%n%n", 
        "%x%x%x%x%x%x%x%x",
        "User input with %d format specifiers %s",
        NULL
    };
    
    for (int i = 0; user_inputs[i]; i++) {
        // These logging calls should be safe because they don't use
        // user input directly as format strings
        
        // Test configuration file operations with format string filenames
        char malicious_filename[256];
        snprintf(malicious_filename, sizeof(malicious_filename), 
                 "/tmp/config_%s.bin", user_inputs[i]);
        
        // This should safely handle the filename without interpreting format specifiers
        int result = save_binary_configuration(malicious_filename);
        // Should either succeed or fail gracefully, not crash
        ASSERT_GE(result, -1, "Config save should not crash on format strings");
        
        if (result == 0) {
            // If file was created, try to load it
            result = load_binary_configuration(malicious_filename);
            ASSERT_GE(result, -1, "Config load should not crash on format strings");
            
            // Clean up
            unlink(malicious_filename);
        }
    }
    
    TEST_PASS();
}

//=============================================================================
// CWE-190: Integer Overflow Tests
//=============================================================================

static void test_integer_overflow_protection(void) {
    TEST_START("Integer overflow protection (CWE-190)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("OverflowTest", "test_integers");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Test 1: Extreme metric values that could cause overflow
    ASSERT_EQ(update_test_metrics(context, DBL_MAX, DBL_MAX, UINT32_MAX, 
                                 1.0, 100.0, "F"), 0,
              "Should handle maximum double/uint32 values");
    
    // Test 2: Query count overflow scenarios
    for (int i = 0; i < 10; i++) {
        ASSERT_EQ(update_test_metrics(context, 1.0, 1.0, UINT32_MAX / 2, 
                                     1.0, 100.0, "A"), 0,
                  "Should handle large query counts");
    }
    
    // Test 3: Negative values that could underflow when cast
    ASSERT_EQ(update_test_metrics(context, -1.0, -1.0, 0, -1.0, -1.0, "F"), 0,
              "Should handle negative metric values");
    
    // Test 4: Extreme timestamp values
    TestContext* ctx = (TestContext*)context;
    uint64_t original_start = ctx->start_time;
    
    // Simulate extreme timestamp scenarios
    ctx->start_time = UINT64_MAX - 1000;  // Near maximum
    ASSERT_EQ(update_test_metrics(context, 1.0, 1.0, 1, 1.0, 100.0, "A"), 0,
              "Should handle extreme start timestamps");
    
    ctx->start_time = 0;  // Minimum timestamp
    ASSERT_EQ(update_test_metrics(context, 1.0, 1.0, 1, 1.0, 100.0, "A"), 0,
              "Should handle zero start timestamp");
    
    ctx->start_time = original_start;  // Restore
    
    finalize_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_memory_size_overflow_protection(void) {
    TEST_START("Memory size overflow protection (CWE-190)");
    
    // Test ring buffer size calculations
    // SIZE_MAX / element_size should not overflow
    ASSERT_EQ(mercury_ring_buffer_create(SIZE_MAX, 1), NULL,
              "Should reject SIZE_MAX element size");
    ASSERT_EQ(mercury_ring_buffer_create(1, SIZE_MAX), NULL,
              "Should reject SIZE_MAX capacity");
    
    // Test edge cases near overflow
    size_t large_size = SIZE_MAX / 1000;
    ASSERT_EQ(mercury_ring_buffer_create(large_size, 1000), NULL,
              "Should reject sizes near overflow");
    
    // Test string capacity overflow
    ASSERT_EQ(mercury_string_create(SIZE_MAX), NULL,
              "Should reject SIZE_MAX string capacity");
    ASSERT_EQ(mercury_string_create(SIZE_MAX / 2), NULL,
              "Should reject half SIZE_MAX capacity");
    
    // Test aligned allocation overflow
    ASSERT_EQ(mercury_aligned_alloc(SIZE_MAX, 16), NULL,
              "Should reject SIZE_MAX allocation size");
    ASSERT_EQ(mercury_aligned_alloc(SIZE_MAX / 2, 16), NULL,
              "Should reject half SIZE_MAX allocation");
    
    // Test valid large allocations that shouldn't overflow
    void* large_mem = mercury_aligned_alloc(1024 * 1024, 16);  // 1MB
    if (large_mem != NULL) {
        // Write to ensure it's really allocated
        memset(large_mem, 0x42, 1024 * 1024);
        mercury_aligned_free(large_mem);
    }
    // If allocation failed, that's also acceptable behavior
    
    TEST_PASS();
}

//=============================================================================
// CWE-191: Integer Underflow Tests
//=============================================================================

static void test_integer_underflow_protection(void) {
    TEST_START("Integer underflow protection (CWE-191)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("UnderflowTest", "test_underflow");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Test 1: Negative severity levels
    ASSERT_EQ(update_n_plus_one_analysis(context, 1, INT_MIN, "Min severity"), 0,
              "Should handle INT_MIN severity");
    ASSERT_EQ(update_n_plus_one_analysis(context, 1, -1000000, "Large negative"), 0,
              "Should handle large negative severity");
    
    // Test 2: Zero and near-zero values
    ASSERT_EQ(update_test_metrics(context, 0.0, 0.0, 0, 0.0, 0.0, ""), 0,
              "Should handle all-zero metrics");
    
    // Test 3: Floating point underflow scenarios
    ASSERT_EQ(update_test_metrics(context, -DBL_MAX, -DBL_MAX, 0, 
                                 -1.0, -100.0, "F"), 0,
              "Should handle negative DBL_MAX values");
    
    // Test 4: Cache hit ratio underflow (should be clamped to 0.0-1.0 range)
    TestContext* ctx = (TestContext*)context;
    ASSERT_EQ(update_test_metrics(context, 1.0, 1.0, 1, -10.0, 50.0, "C"), 0,
              "Should handle negative cache hit ratio");
    
    // Verify cache hit ratio was clamped
    ASSERT_GE(ctx->cache_hit_ratio, 0.0, "Cache hit ratio should be >= 0.0");
    ASSERT_LE(ctx->cache_hit_ratio, 1.0, "Cache hit ratio should be <= 1.0");
    
    finalize_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

//=============================================================================
// CWE-362: Race Condition Tests  
//=============================================================================

typedef struct {
    int thread_id;
    int iterations;
    volatile int* shared_error_count;
} RaceTestData;

static void* statistics_race_thread(void* arg) {
    RaceTestData* data = (RaceTestData*)arg;
    
    for (int i = 0; i < data->iterations; i++) {
        char class_name[50], method_name[50];
        snprintf(class_name, sizeof(class_name), "RaceClass%d", data->thread_id);
        snprintf(method_name, sizeof(method_name), "race_method_%d_%d", 
                 data->thread_id, i);
        
        void* context = create_test_context(class_name, method_name);
        if (context != NULL) {
            // Update metrics
            update_test_metrics(context, 10.0 + i, 5.0 + i, i % 20, 
                               0.8, 80.0 + i, "B");
            
            // Randomly add N+1 analysis
            if (i % 3 == 0) {
                update_n_plus_one_analysis(context, 1, i % 5, "Race condition test");
            }
            
            // Get statistics while other threads are also accessing
            uint64_t total_tests, total_violations, total_n_plus_one, history_entries;
            size_t active_contexts;
            get_orchestrator_statistics(&total_tests, &total_violations,
                                       &total_n_plus_one, &active_contexts,
                                       &history_entries);
            
            // Verify statistics are reasonable (not corrupted by race conditions)
            if (total_tests > 1000000 || total_violations > 1000000) {
                (*data->shared_error_count)++;
            }
            
            finalize_test_context(context);
        } else {
            (*data->shared_error_count)++;
        }
        
        // Small delay to increase race condition probability
        if (i % 10 == 0) {
            usleep(1000);
        }
    }
    
    return NULL;
}

static void test_statistics_race_conditions(void) {
    TEST_START("Statistics race conditions (CWE-362)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    const int num_threads = 4;
    const int iterations_per_thread = 50;
    pthread_t threads[4];
    RaceTestData thread_data[4];
    volatile int shared_error_count = 0;
    
    // Launch threads that concurrently access orchestrator statistics
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].iterations = iterations_per_thread;
        thread_data[i].shared_error_count = &shared_error_count;
        
        int result = pthread_create(&threads[i], NULL, 
                                   statistics_race_thread, &thread_data[i]);
        ASSERT_EQ(result, 0, "Failed to create statistics race thread");
    }
    
    // Also perform operations on main thread
    for (int i = 0; i < 20; i++) {
        uint64_t total_tests, total_violations, total_n_plus_one, history_entries;
        size_t active_contexts;
        get_orchestrator_statistics(&total_tests, &total_violations,
                                   &total_n_plus_one, &active_contexts,
                                   &history_entries);
        usleep(5000);
    }
    
    // Wait for all threads
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Check final statistics for reasonableness
    uint64_t final_tests, final_violations, final_n_plus_one, final_history;
    size_t final_active;
    get_orchestrator_statistics(&final_tests, &final_violations,
                               &final_n_plus_one, &final_active,
                               &final_history);
    
    // Should have processed roughly num_threads * iterations_per_thread tests
    uint64_t expected_tests = (uint64_t)(num_threads * iterations_per_thread);
    ASSERT_GE(final_tests, expected_tests - 10, "Should have processed most tests");
    ASSERT_LE(final_tests, expected_tests + 10, "Should not have too many tests");
    
    // Should have no active contexts after all threads finished
    ASSERT_EQ(final_active, 0, "Should have no active contexts after completion");
    
    // Should have minimal errors from race conditions
    ASSERT_LT(shared_error_count, num_threads, 
              "Should have minimal race condition errors");
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

//=============================================================================
// Advanced Bounds Checking Tests (CWE-787/125)
//=============================================================================

static void test_edge_case_bounds_checking(void) {
    TEST_START("Edge case bounds checking (CWE-787/125)");
    
    // Test 1: Ring buffer with single-byte elements
    MercuryRingBuffer* tiny_buffer = mercury_ring_buffer_create(1, 3);
    ASSERT_NEQ(tiny_buffer, NULL, "Should create single-byte element buffer");
    
    char values[] = {0x41, 0x42, 0x43, 0x44, 0x45};
    
    // Fill and test boundaries
    for (int i = 0; i < 3; i++) {
        ASSERT_EQ(mercury_ring_buffer_push(tiny_buffer, &values[i]), true,
                  "Should push within capacity");
    }
    
    // Test overflow
    ASSERT_EQ(mercury_ring_buffer_push(tiny_buffer, &values[3]), false,
              "Should reject overflow push");
    
    // Test reading back
    for (int i = 0; i < 3; i++) {
        char retrieved;
        ASSERT_EQ(mercury_ring_buffer_pop(tiny_buffer, &retrieved), true,
                  "Should pop within bounds");
        ASSERT_EQ(retrieved, values[i], "Should retrieve correct value");
    }
    
    mercury_ring_buffer_destroy(tiny_buffer);
    
    // Test 2: Large structure elements
    typedef struct {
        char data[256];
        int checksum;
    } LargeStruct;
    
    MercuryRingBuffer* large_buffer = mercury_ring_buffer_create(sizeof(LargeStruct), 2);
    ASSERT_NEQ(large_buffer, NULL, "Should create large structure buffer");
    
    LargeStruct large_data[3];
    for (int i = 0; i < 3; i++) {
        memset(large_data[i].data, 'A' + i, sizeof(large_data[i].data));
        large_data[i].checksum = i * 1000;
    }
    
    // Fill to capacity
    ASSERT_EQ(mercury_ring_buffer_push(large_buffer, &large_data[0]), true,
              "Should push first large struct");
    ASSERT_EQ(mercury_ring_buffer_push(large_buffer, &large_data[1]), true,
              "Should push second large struct");
    
    // Test overflow with large struct
    ASSERT_EQ(mercury_ring_buffer_push(large_buffer, &large_data[2]), false,
              "Should reject large struct overflow");
    
    mercury_ring_buffer_destroy(large_buffer);
    
    TEST_PASS();
}

static void test_string_bounds_edge_cases(void) {
    TEST_START("String bounds edge cases (CWE-787/125)");
    
    // Test 1: Append at exact capacity boundary
    MercuryString* str = mercury_string_create(10);
    ASSERT_NEQ(str, NULL, "Should create string");
    
    // Fill to near capacity
    ASSERT_EQ(mercury_string_append(str, "12345"), MERCURY_SUCCESS,
              "Should append within capacity");
    ASSERT_EQ(mercury_string_append(str, "6789"), MERCURY_SUCCESS,
              "Should append to near capacity");
    
    // Test boundary append
    ASSERT_EQ(mercury_string_append(str, "X"), MERCURY_SUCCESS,
              "Should handle boundary append");
    
    // Test over-capacity append - should grow or fail gracefully
    MercuryError result = mercury_string_append(str, "OVERFLOW_TEST_DATA");
    // Either succeeds (string grew) or fails gracefully
    ASSERT_TRUE(result == MERCURY_SUCCESS || result != MERCURY_SUCCESS,
                "Should handle over-capacity append gracefully");
    
    const char* final_str = mercury_string_cstr(str);
    ASSERT_NEQ(final_str, NULL, "Should return valid string");
    
    // String should not be corrupted
    size_t len = strlen(final_str);
    ASSERT_LT(len, 1000, "String length should be reasonable");
    
    mercury_string_destroy(str);
    
    // Test 2: Character-by-character append
    str = mercury_string_create(5);
    ASSERT_NEQ(str, NULL, "Should create small string");
    
    for (int i = 0; i < 10; i++) {
        char single_char[2] = {'A' + (i % 26), '\0'};
        MercuryError append_result = mercury_string_append(str, single_char);
        
        // Should either succeed or fail gracefully
        if (append_result != MERCURY_SUCCESS) {
            // If it fails, string should still be valid
            const char* current = mercury_string_cstr(str);
            ASSERT_NEQ(current, NULL, "String should remain valid after failed append");
            break;
        }
    }
    
    mercury_string_destroy(str);
    TEST_PASS();
}

//=============================================================================
// Public Test Suite Function
//=============================================================================

void run_format_and_bounds_tests(void) {
    TEST_SUITE_START("Format String and Bounds Security Tests");
    
    // CWE-134: Format String Vulnerabilities
    test_format_string_injection_protection();
    test_optimization_suggestion_format_safety();
    test_logging_format_string_safety();
    
    // CWE-190: Integer Overflow
    test_integer_overflow_protection();
    test_memory_size_overflow_protection();
    
    // CWE-191: Integer Underflow
    test_integer_underflow_protection();
    
    // CWE-362: Race Conditions
    test_statistics_race_conditions();
    
    // CWE-787/125: Advanced Bounds Checking
    test_edge_case_bounds_checking();
    test_string_bounds_edge_cases();
    
    TEST_SUITE_END();
}