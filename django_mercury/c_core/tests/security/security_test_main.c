/**
 * @file security_test_main.c
 * @brief Main security test runner
 * 
 * Runs all security vulnerability tests and reports results.
 * Exit code 0 = all tests passed, 1 = vulnerabilities detected
 */

#include <stdio.h>
#include <stdlib.h>

// Declare test suite functions
void run_command_injection_tests(void);
void run_buffer_overflow_tests(void);
void run_input_validation_tests(void);
void run_memory_security_tests(void);
void run_format_and_bounds_tests(void);

// Import test statistics from test_framework
extern int total_tests;
extern int passed_tests;
extern int failed_tests;

int main(int argc, char* argv[]) {
    // Suppress unused parameter warnings
    (void)argc;
    (void)argv;
    
    printf("\n");
    printf("╔════════════════════════════════════════════════════════════╗\n");
    printf("║           🔒 MERCURY SECURITY TEST SUITE 🔒               ║\n");
    printf("║                                                            ║\n");
    printf("║  Testing for critical security vulnerabilities:           ║\n");
    printf("║  • Command injection                                      ║\n");
    printf("║  • Buffer overflows                                       ║\n");
    printf("║  • Input validation                                       ║\n");
    printf("║  • Memory safety                                          ║\n");
    printf("║  • Format string vulnerabilities                          ║\n");
    printf("║  • Integer overflow/underflow                             ║\n");
    printf("║  • Race conditions                                        ║\n");
    printf("╚════════════════════════════════════════════════════════════╝\n");
    printf("\n");
    
    // Reset test counters
    total_tests = 0;
    passed_tests = 0;
    failed_tests = 0;
    
    // Run all security test suites
    run_command_injection_tests();
    run_buffer_overflow_tests();
    run_input_validation_tests();
    run_memory_security_tests();
    run_format_and_bounds_tests();
    
    // Print summary
    printf("\n");
    printf("════════════════════════════════════════════════════════════\n");
    printf("                    SECURITY TEST SUMMARY                   \n");
    printf("════════════════════════════════════════════════════════════\n");
    printf("Total tests:  %d\n", total_tests);
    printf("Passed:       \033[32m%d\033[0m\n", passed_tests);
    printf("Failed:       %s%d\033[0m\n", 
           failed_tests > 0 ? "\033[31m" : "\033[32m", failed_tests);
    printf("\n");
    
    if (failed_tests > 0) {
        printf("\033[31m");
        printf("╔════════════════════════════════════════════════════════════╗\n");
        printf("║                    ⚠️  CRITICAL WARNING ⚠️                  ║\n");
        printf("║                                                            ║\n");
        printf("║     SECURITY VULNERABILITIES DETECTED!                    ║\n");
        printf("║     DO NOT DEPLOY THIS CODE TO PRODUCTION!                ║\n");
        printf("║                                                            ║\n");
        printf("║     Review failed tests and fix all vulnerabilities       ║\n");
        printf("║     before proceeding with deployment.                    ║\n");
        printf("╚════════════════════════════════════════════════════════════╝\n");
        printf("\033[0m\n");
        return 1;
    } else {
        printf("\033[32m");
        printf("╔════════════════════════════════════════════════════════════╗\n");
        printf("║                   ✅ ALL TESTS PASSED ✅                   ║\n");
        printf("║                                                            ║\n");
        printf("║     No security vulnerabilities detected!                 ║\n");
        printf("║                                                            ║\n");
        printf("║     Comprehensive security validation complete:           ║\n");
        printf("║     • Command injection prevention                        ║\n");
        printf("║     • Buffer overflow protection                          ║\n");
        printf("║     • Input validation and sanitization                   ║\n");
        printf("║     • Memory safety (NULL ptr, use-after-free)            ║\n");
        printf("║     • Format string vulnerability prevention              ║\n");
        printf("║     • Integer overflow/underflow protection               ║\n");
        printf("║     • Race condition and bounds checking                  ║\n");
        printf("╚════════════════════════════════════════════════════════════╝\n");
        printf("\033[0m\n");
        return 0;
    }
}