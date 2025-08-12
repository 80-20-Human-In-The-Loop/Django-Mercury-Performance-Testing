/**
 * @file test_buffer_overflow.c
 * @brief Buffer overflow vulnerability tests
 * 
 * Tests to verify that buffer overflow vulnerabilities are prevented
 * through proper bounds checking and safe string operations.
 */

#include "../../common.h"
#include "../../test_orchestrator.h"
#include "../test_security.h"
#include <string.h>

static void test_grade_field_overflow(void) {
    TEST_START("Grade field buffer overflow prevention");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("TestClass", "test_method");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Create an oversized grade string (grade field is 4 bytes)
    char overflow_grade[1024];
    memset(overflow_grade, 'A', sizeof(overflow_grade) - 1);
    overflow_grade[sizeof(overflow_grade) - 1] = '\0';
    
    // Update with oversized grade
    update_test_metrics(context, 100.0, 50.0, 5, 0.8, 85.0, overflow_grade);
    
    TestContext* ctx = (TestContext*)context;
    
    // Verify grade is properly bounded
    ASSERT_LE(strlen(ctx->grade), 3, 
              "Grade field overflow! Length: %zu", strlen(ctx->grade));
    
    // Verify no memory corruption by checking adjacent fields
    ASSERT_EQ(ctx->is_active, true, "Memory corruption detected!");
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_suggestion_field_overflow(void) {
    TEST_START("Optimization suggestion buffer overflow prevention");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("TestClass", "test_method");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Create an oversized suggestion string (field is 256 bytes)
    char overflow_suggestion[4096];
    memset(overflow_suggestion, 'B', sizeof(overflow_suggestion) - 1);
    overflow_suggestion[sizeof(overflow_suggestion) - 1] = '\0';
    
    // Update with oversized suggestion
    update_n_plus_one_analysis(context, 1, 5, overflow_suggestion);
    
    TestContext* ctx = (TestContext*)context;
    
    // Verify suggestion is properly bounded
    ASSERT_LE(strlen(ctx->optimization_suggestion), 255, 
              "Suggestion field overflow! Length: %zu", 
              strlen(ctx->optimization_suggestion));
    
    // Verify termination
    ASSERT_EQ(ctx->optimization_suggestion[255], '\0', 
              "String not properly terminated!");
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_operation_name_overflow(void) {
    TEST_START("Operation name buffer overflow prevention");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Create context with very long class and method names
    char long_class[512];
    char long_method[512];
    memset(long_class, 'C', sizeof(long_class) - 1);
    memset(long_method, 'M', sizeof(long_method) - 1);
    long_class[sizeof(long_class) - 1] = '\0';
    long_method[sizeof(long_method) - 1] = '\0';
    
    void* context = create_test_context(long_class, long_method);
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    TestContext* ctx = (TestContext*)context;
    
    // Verify class and method names are bounded
    ASSERT_LE(strlen(ctx->test_class), 127, 
              "Class name overflow! Length: %zu", strlen(ctx->test_class));
    ASSERT_LE(strlen(ctx->test_method), 127, 
              "Method name overflow! Length: %zu", strlen(ctx->test_method));
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_format_string_vulnerability(void) {
    TEST_START("Format string vulnerability prevention");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    void* context = create_test_context("TestClass", "test_method");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Try format string attacks
    const char* format_attacks[] = {
        "%s%s%s%s%s",
        "%x%x%x%x",
        "%n%n%n%n",
        "%.1000000s",
        NULL
    };
    
    for (int i = 0; format_attacks[i]; i++) {
        // These should be treated as literal strings, not format strings
        update_n_plus_one_analysis(context, 1, 5, format_attacks[i]);
        
        TestContext* ctx = (TestContext*)context;
        
        // Verify the string was copied literally
        ASSERT_STR_CONTAINS(ctx->optimization_suggestion, "%", 
                           "Format string not handled safely");
    }
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    TEST_PASS();
}

void run_buffer_overflow_tests(void) {
    TEST_SUITE_START("Buffer Overflow Security Tests");
    
    test_grade_field_overflow();
    test_suggestion_field_overflow();
    test_operation_name_overflow();
    test_format_string_vulnerability();
    
    TEST_SUITE_END();
}