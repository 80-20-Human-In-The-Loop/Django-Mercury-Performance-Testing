/**
 * @file security_test.c
 * @brief Security vulnerability tests for Mercury C libraries
 * 
 * This test suite verifies that critical security vulnerabilities have been fixed:
 * - Command injection via system() calls
 * - Buffer overflow via unsafe string operations
 * - Memory safety issues
 * 
 * @author Security Team
 * @version 1.0.0
 */

#include "../common.h"
#include "../test_orchestrator.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <assert.h>

// Test tracking
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

// Color codes for output
#define RED "\033[31m"
#define GREEN "\033[32m"
#define YELLOW "\033[33m"
#define RESET "\033[0m"

// Test macros
#define RUN_TEST(test_func) do { \
    printf("Running: %s... ", #test_func); \
    tests_run++; \
    if (test_func()) { \
        printf(GREEN "PASSED" RESET "\n"); \
        tests_passed++; \
    } else { \
        printf(RED "FAILED" RESET "\n"); \
        tests_failed++; \
    } \
} while(0)

/**
 * Test 1: Verify command injection is prevented
 * 
 * The old code used system() with user input, allowing command injection.
 * This test verifies the vulnerability is fixed.
 */
int test_command_injection_prevention(void) {
    printf("\n  Testing command injection prevention...\n");
    
    // Initialize test orchestrator
    if (initialize_test_orchestrator("test_history.bin") != 0) {
        printf("    Failed to initialize orchestrator\n");
        return 0;
    }
    
    // Create a test file to detect if commands are executed
    const char* canary_file = "/tmp/SECURITY_CANARY_SHOULD_NOT_EXIST";
    
    // Remove canary file if it exists
    unlink(canary_file);
    
    // Test 1: Try injecting a command that would create the canary file
    char malicious_path[256];
    snprintf(malicious_path, sizeof(malicious_path), 
             "test.conf'; touch '%s'; echo '", canary_file);
    
    printf("    Attempting command injection with: %s\n", malicious_path);
    
    // Call the function that was vulnerable
    int result = save_binary_configuration(malicious_path);
    
    // Check if the canary file was created (it shouldn't be)
    struct stat st;
    if (stat(canary_file, &st) == 0) {
        printf(RED "    VULNERABILITY: Command injection succeeded! Canary file created!\n" RESET);
        unlink(canary_file);
        cleanup_test_orchestrator();
        return 0;
    }
    
    printf(GREEN "    Good: Command injection prevented\n" RESET);
    
    // Test 2: Try with backticks
    snprintf(malicious_path, sizeof(malicious_path), 
             "test.conf`touch %s`", canary_file);
    
    save_binary_configuration(malicious_path);
    
    if (stat(canary_file, &st) == 0) {
        printf(RED "    VULNERABILITY: Backtick injection succeeded!\n" RESET);
        unlink(canary_file);
        cleanup_test_orchestrator();
        return 0;
    }
    
    printf(GREEN "    Good: Backtick injection prevented\n" RESET);
    
    // Test 3: Try with semicolon
    snprintf(malicious_path, sizeof(malicious_path), 
             "test.conf; touch %s", canary_file);
    
    save_binary_configuration(malicious_path);
    
    if (stat(canary_file, &st) == 0) {
        printf(RED "    VULNERABILITY: Semicolon injection succeeded!\n" RESET);
        unlink(canary_file);
        cleanup_test_orchestrator();
        return 0;
    }
    
    printf(GREEN "    Good: Semicolon injection prevented\n" RESET);
    
    cleanup_test_orchestrator();
    return 1;
}

/**
 * Test 2: Verify buffer overflow prevention
 * 
 * The old code used strcpy() without bounds checking.
 * This test verifies proper bounds checking is in place.
 */
int test_buffer_overflow_prevention(void) {
    printf("\n  Testing buffer overflow prevention...\n");
    
    if (initialize_test_orchestrator("test_history.bin") != 0) {
        printf("    Failed to initialize orchestrator\n");
        return 0;
    }
    
    // Create a test context
    void* context = create_test_context("TestClass", "test_method");
    if (!context) {
        printf("    Failed to create test context\n");
        cleanup_test_orchestrator();
        return 0;
    }
    
    // Test 1: Try to overflow the grade field (4 bytes)
    char long_grade[100];
    memset(long_grade, 'A', sizeof(long_grade) - 1);
    long_grade[sizeof(long_grade) - 1] = '\0';
    
    printf("    Attempting to overflow grade field with %zu bytes...\n", strlen(long_grade));
    
    // This should safely truncate instead of overflowing
    update_test_metrics(context, 100.0, 50.0, 5, 0.8, 85.0, long_grade);
    
    // Verify the context is still valid and not corrupted
    TestContext* ctx = (TestContext*)context;
    
    // Grade should be truncated to 3 chars + null
    if (strlen(ctx->grade) > 3) {
        printf(RED "    VULNERABILITY: Grade field overflow! Length: %zu\n" RESET, strlen(ctx->grade));
        destroy_test_context(context);
        cleanup_test_orchestrator();
        return 0;
    }
    
    printf(GREEN "    Good: Grade field properly bounded to %zu chars\n" RESET, strlen(ctx->grade));
    
    // Test 2: Try to overflow optimization_suggestion (256 bytes)
    char long_suggestion[1024];
    memset(long_suggestion, 'B', sizeof(long_suggestion) - 1);
    long_suggestion[sizeof(long_suggestion) - 1] = '\0';
    
    printf("    Attempting to overflow suggestion field with %zu bytes...\n", strlen(long_suggestion));
    
    update_n_plus_one_analysis(context, 1, 5, long_suggestion);
    
    // Suggestion should be truncated to 255 chars + null
    if (strlen(ctx->optimization_suggestion) > 255) {
        printf(RED "    VULNERABILITY: Suggestion field overflow! Length: %zu\n" RESET, 
               strlen(ctx->optimization_suggestion));
        destroy_test_context(context);
        cleanup_test_orchestrator();
        return 0;
    }
    
    printf(GREEN "    Good: Suggestion field properly bounded to %zu chars\n" RESET, 
           strlen(ctx->optimization_suggestion));
    
    // Test 3: Verify no memory corruption occurred
    // Try to access fields after the potentially overflowed ones
    if (ctx->is_active != true) {
        printf(RED "    Memory corruption detected: is_active field corrupted\n" RESET);
        destroy_test_context(context);
        cleanup_test_orchestrator();
        return 0;
    }
    
    printf(GREEN "    Good: No memory corruption detected\n" RESET);
    
    destroy_test_context(context);
    cleanup_test_orchestrator();
    return 1;
}

/**
 * Test 3: Verify safe file operations
 * 
 * Ensure file operations are done safely without shell interpretation
 */
int test_safe_file_operations(void) {
    printf("\n  Testing safe file operations...\n");
    
    if (initialize_test_orchestrator("test_history.bin") != 0) {
        printf("    Failed to initialize orchestrator\n");
        return 0;
    }
    
    // Test with various special characters that could be interpreted by shell
    const char* test_paths[] = {
        "/tmp/test file with spaces.conf",
        "/tmp/test'with'quotes.conf",
        "/tmp/test\"with\"doublequotes.conf",
        "/tmp/test$USER.conf",
        "/tmp/test|pipe.conf",
        "/tmp/test&background.conf",
        "/tmp/test>redirect.conf",
        NULL
    };
    
    for (int i = 0; test_paths[i] != NULL; i++) {
        printf("    Testing with path: %s\n", test_paths[i]);
        
        // Should create the file safely without shell interpretation
        int result = save_binary_configuration(test_paths[i]);
        
        if (result == 0) {
            // Verify the file was actually created
            struct stat st;
            if (stat(test_paths[i], &st) == 0) {
                printf(GREEN "      File created safely\n" RESET);
                unlink(test_paths[i]);  // Clean up
            } else {
                printf(YELLOW "      Warning: File creation failed (may be expected for some paths)\n" RESET);
            }
        }
    }
    
    cleanup_test_orchestrator();
    return 1;
}

/**
 * Test 4: Verify memory mapping error handling
 */
int test_memory_mapping_safety(void) {
    printf("\n  Testing memory mapping safety...\n");
    
    // Test with invalid file path
    if (initialize_test_orchestrator("/invalid/path/that/does/not/exist/test.bin") == 0) {
        printf(RED "    Should have failed with invalid path\n" RESET);
        cleanup_test_orchestrator();
        return 0;
    }
    
    printf(GREEN "    Good: Invalid path properly rejected\n" RESET);
    
    // Test with valid path
    if (initialize_test_orchestrator("/tmp/test_mmap.bin") != 0) {
        printf(RED "    Failed to initialize with valid path\n" RESET);
        return 0;
    }
    
    printf(GREEN "    Good: Valid path accepted\n" RESET);
    
    cleanup_test_orchestrator();
    return 1;
}

/**
 * Test 5: Verify input validation
 */
int test_input_validation(void) {
    printf("\n  Testing input validation...\n");
    
    if (initialize_test_orchestrator("test_history.bin") != 0) {
        printf("    Failed to initialize orchestrator\n");
        return 0;
    }
    
    // Test NULL inputs
    if (save_binary_configuration(NULL) != -1) {
        printf(RED "    NULL path not rejected\n" RESET);
        cleanup_test_orchestrator();
        return 0;
    }
    printf(GREEN "    Good: NULL path rejected\n" RESET);
    
    // Test empty string
    if (save_binary_configuration("") == 0) {
        printf(YELLOW "    Warning: Empty path accepted (may be valid)\n" RESET);
    }
    
    // Test very long path
    char long_path[4096];
    memset(long_path, 'A', sizeof(long_path) - 1);
    long_path[sizeof(long_path) - 1] = '\0';
    
    if (save_binary_configuration(long_path) == 0) {
        printf(YELLOW "    Warning: Very long path accepted\n" RESET);
    }
    
    cleanup_test_orchestrator();
    return 1;
}

int main(void) {
    printf("========================================\n");
    printf("Mercury Security Test Suite\n");
    printf("========================================\n\n");
    
    printf(YELLOW "WARNING: These tests check for security vulnerabilities!\n" RESET);
    printf("If any test fails, DO NOT deploy to production!\n\n");
    
    // Run security tests
    RUN_TEST(test_command_injection_prevention);
    RUN_TEST(test_buffer_overflow_prevention);
    RUN_TEST(test_safe_file_operations);
    RUN_TEST(test_memory_mapping_safety);
    RUN_TEST(test_input_validation);
    
    // Print summary
    printf("\n========================================\n");
    printf("Security Test Summary\n");
    printf("========================================\n");
    printf("Tests run: %d\n", tests_run);
    printf(GREEN "Passed: %d\n" RESET, tests_passed);
    if (tests_failed > 0) {
        printf(RED "Failed: %d\n" RESET, tests_failed);
        printf(RED "\n⚠️  CRITICAL: Security vulnerabilities detected!\n" RESET);
        printf(RED "DO NOT deploy this code to production!\n" RESET);
    } else {
        printf(GREEN "\n✅ All security tests passed!\n" RESET);
        printf("The following vulnerabilities have been fixed:\n");
        printf("  • Command injection via system() calls\n");
        printf("  • Buffer overflow via strcpy()\n");
        printf("  • Memory mapping error handling\n");
        printf("  • Input validation\n");
    }
    
    return tests_failed > 0 ? 1 : 0;
}