/**
 * @file test_command_injection.c
 * @brief Command injection vulnerability tests
 * 
 * Tests to verify that command injection vulnerabilities are prevented
 * in all modules that handle external input.
 */

#include "../../common.h"
#include "../../test_orchestrator.h"
#include "../test_security.h"
#include <sys/stat.h>
#include <unistd.h>

static void test_save_config_command_injection(void) {
    TEST_START("Command injection in save_binary_configuration");
    
    // Initialize test orchestrator
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Create a canary file to detect command execution
    const char* canary = "/tmp/CANARY_CMD_INJECT";
    unlink(canary);  // Ensure it doesn't exist
    
    // Test various injection attempts
    const char* injection_attempts[] = {
        "test.conf'; touch '/tmp/CANARY_CMD_INJECT'; echo '",
        "test.conf`touch /tmp/CANARY_CMD_INJECT`",
        "test.conf; touch /tmp/CANARY_CMD_INJECT",
        "test.conf && touch /tmp/CANARY_CMD_INJECT",
        "test.conf | touch /tmp/CANARY_CMD_INJECT",
        "test.conf$(touch /tmp/CANARY_CMD_INJECT)",
        NULL
    };
    
    for (int i = 0; injection_attempts[i]; i++) {
        // Attempt injection
        save_binary_configuration(injection_attempts[i]);
        
        // Check if canary was created (it shouldn't be)
        struct stat st;
        ASSERT_NEQ(stat(canary, &st), 0, 
                   "CRITICAL: Command injection succeeded with: %s", 
                   injection_attempts[i]);
    }
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_path_traversal_prevention(void) {
    TEST_START("Path traversal prevention");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test path traversal attempts
    const char* traversal_attempts[] = {
        "../../../etc/passwd",
        "..\\..\\..\\sensitive\\system\\file",
        "test/../../../etc/shadow",
        "/etc/passwd",
        NULL
    };
    
    for (int i = 0; traversal_attempts[i]; i++) {
        int result = save_binary_configuration(traversal_attempts[i]);
        
        // Should either fail or create in safe location
        if (result == 0) {
            // Verify it didn't actually write to system files
            if (strcmp(traversal_attempts[i], "/etc/passwd") == 0) {
                // This might exist but shouldn't be writable
                FILE* fp = fopen("/etc/passwd", "a");
                ASSERT_EQ(fp, NULL, 
                         "CRITICAL: Able to write to system file!");
            }
        }
    }
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_shell_metacharacter_handling(void) {
    TEST_START("Shell metacharacter handling");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test files with shell metacharacters
    const char* metachar_files[] = {
        "/tmp/test$USER.conf",
        "/tmp/test${HOME}.conf",
        "/tmp/test*.conf",
        "/tmp/test?.conf",
        "/tmp/test[abc].conf",
        "/tmp/test~.conf",
        NULL
    };
    
    for (int i = 0; metachar_files[i]; i++) {
        int result = save_binary_configuration(metachar_files[i]);
        
        if (result == 0) {
            // File should be created literally, not expanded
            struct stat st;
            if (stat(metachar_files[i], &st) == 0) {
                // Good - file created with literal name
                unlink(metachar_files[i]);
            }
        }
    }
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

void run_command_injection_tests(void) {
    TEST_SUITE_START("Command Injection Security Tests");
    
    test_save_config_command_injection();
    test_path_traversal_prevention();
    test_shell_metacharacter_handling();
    
    TEST_SUITE_END();
}