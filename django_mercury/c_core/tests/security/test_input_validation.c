/**
 * @file test_input_validation.c
 * @brief Input validation security tests
 * 
 * Tests to verify proper validation of all external inputs
 * to prevent various injection and corruption attacks.
 */

#include "../../common.h"
#include "../../test_orchestrator.h"
#include "../test_framework.h"
#include <limits.h>
#include <float.h>

static void test_null_input_handling(void) {
    TEST_START("NULL input validation");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test NULL configuration path
    ASSERT_EQ(save_binary_configuration(NULL), -1, 
              "NULL path should be rejected");
    
    ASSERT_EQ(load_binary_configuration(NULL), -1, 
              "NULL path should be rejected");
    
    // Test NULL context creation
    void* context = create_test_context(NULL, "method");
    ASSERT_NEQ(context, NULL, "Should handle NULL class name");
    destroy_test_context(context);
    
    context = create_test_context("class", NULL);
    ASSERT_NEQ(context, NULL, "Should handle NULL method name");
    destroy_test_context(context);
    
    // Test NULL in update functions
    context = create_test_context("class", "method");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    ASSERT_EQ(update_test_metrics(NULL, 1, 1, 1, 1, 1, "A"), -1,
              "NULL context should be rejected");
    
    ASSERT_EQ(update_n_plus_one_analysis(NULL, 1, 1, "test"), -1,
              "NULL context should be rejected");
    
    // NULL grade and suggestion should be handled
    update_test_metrics(context, 1, 1, 1, 1, 1, NULL);
    update_n_plus_one_analysis(context, 1, 1, NULL);
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_boundary_values(void) {
    TEST_START("Boundary value validation");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("class", "method");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Test extreme metric values
    update_test_metrics(context, -1.0, -1.0, -1, -1.0, -1.0, "F");
    update_test_metrics(context, 0.0, 0.0, 0, 0.0, 0.0, "F");
    update_test_metrics(context, DBL_MAX, DBL_MAX, INT_MAX, 1.0, 100.0, "A");
    
    // Test extreme severity levels
    update_n_plus_one_analysis(context, 0, INT_MIN, "test");
    update_n_plus_one_analysis(context, 1, INT_MAX, "test");
    
    // Verify context is still valid
    TestContext* ctx = (TestContext*)context;
    ASSERT_EQ(ctx->is_active, true, "Context corrupted by boundary values");
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_empty_string_handling(void) {
    TEST_START("Empty string validation");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test empty string paths
    int result = save_binary_configuration("");
    // Empty path might be valid (current directory)
    
    // Test empty class/method names
    void* context = create_test_context("", "");
    ASSERT_NEQ(context, NULL, "Should handle empty strings");
    
    TestContext* ctx = (TestContext*)context;
    
    // Update with empty strings
    update_test_metrics(context, 1, 1, 1, 1, 1, "");
    update_n_plus_one_analysis(context, 1, 1, "");
    
    // Verify empty strings are handled
    ASSERT_EQ(strlen(ctx->grade), 0, "Empty grade not handled");
    ASSERT_EQ(strlen(ctx->optimization_suggestion), 0, 
              "Empty suggestion not handled");
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_special_characters(void) {
    TEST_START("Special character handling");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test various special characters in paths
    const char* special_paths[] = {
        "/tmp/test\nwith\nnewlines.conf",
        "/tmp/test\twith\ttabs.conf",
        "/tmp/test\rwith\rcarriage.conf",
        "/tmp/test\x00with\x00nulls.conf",  // Note: will be truncated at first null
        "/tmp/test\x1b[31mwith\x1b[0mansi.conf",
        "/tmp/test™with©unicode®.conf",
        NULL
    };
    
    for (int i = 0; special_paths[i]; i++) {
        save_binary_configuration(special_paths[i]);
        // Should handle gracefully without crashes
    }
    
    // Test special characters in context fields
    void* context = create_test_context("Class\nWith\nNewlines", 
                                        "method\twith\ttabs");
    ASSERT_NEQ(context, NULL, "Failed with special chars");
    
    update_n_plus_one_analysis(context, 1, 1, 
                               "Suggestion\nwith\x1b[31mspecial\x1b[0mchars");
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_integer_overflow(void) {
    TEST_START("Integer overflow prevention");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("class", "method");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Test with values that could cause integer overflow
    update_test_metrics(context, 
                        1e308,  // Near double max
                        1e308,
                        INT_MAX,
                        1.0,
                        100.0,
                        "A");
    
    // Test query count that could overflow
    for (int i = 0; i < 100; i++) {
        update_test_metrics(context, 1, 1, INT_MAX / 2, 1, 1, "A");
    }
    
    // Context should still be valid
    TestContext* ctx = (TestContext*)context;
    ASSERT_EQ(ctx->is_active, true, "Integer overflow corrupted context");
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

void run_input_validation_tests(void) {
    TEST_SUITE_START("Input Validation Security Tests");
    
    test_null_input_handling();
    test_boundary_values();
    test_empty_string_handling();
    test_special_characters();
    test_integer_overflow();
    
    TEST_SUITE_END();
}