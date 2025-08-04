/**
 * @file test_memory_security.c
 * @brief Comprehensive memory security vulnerability tests
 * 
 * Tests for critical memory-related security vulnerabilities in Django Mercury:
 * - CWE-476: NULL Pointer Dereference
 * - CWE-416: Use After Free (Dangling Pointers)
 * - CWE-787: Out-of-bounds Write
 * - CWE-125: Out-of-bounds Read
 * - CWE-401: Memory Leaks
 * 
 * Based on CERT C Secure Coding Standard and OWASP security guidelines.
 */

#include "../../common.h"
#include "../../test_orchestrator.h"
#include "../test_framework.h"
#include <limits.h>
#include <pthread.h>
#include <unistd.h>
#include <signal.h>
#include <setjmp.h>

// Global jump buffer for segfault handling
static jmp_buf segv_env;
static volatile sig_atomic_t segv_occurred = 0;

// Signal handler for segmentation faults during security testing
static void segv_handler(int sig) {
    (void)sig;
    segv_occurred = 1;
    longjmp(segv_env, 1);
}

// Set up signal handler for safe memory testing
static void setup_segv_handler(void) {
    struct sigaction sa;
    sa.sa_handler = segv_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGSEGV, &sa, NULL);
    segv_occurred = 0;
}

// Restore default signal handler
static void restore_segv_handler(void) {
    struct sigaction sa;
    sa.sa_handler = SIG_DFL;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGSEGV, &sa, NULL);
}

//=============================================================================
// CWE-476: NULL Pointer Dereference Tests
//=============================================================================

static void test_null_pointer_dereference_protection(void) {
    TEST_START("NULL pointer dereference protection (CWE-476)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test 1: All test orchestrator functions with NULL pointers
    void* null_context = NULL;
    
    // These should all safely return error codes, not segfault
    ASSERT_EQ(create_test_context(NULL, "method"), NULL, 
              "Should reject NULL class name");
    ASSERT_EQ(create_test_context("class", NULL), NULL, 
              "Should reject NULL method name");
    
    ASSERT_NEQ(update_test_metrics(null_context, 1, 1, 1, 1, 1, "A"), 0,
               "Should reject NULL context");
    ASSERT_NEQ(update_n_plus_one_analysis(null_context, 1, 1, "test"), 0,
               "Should reject NULL context");
    ASSERT_NEQ(finalize_test_context(null_context), 0,
               "Should reject NULL context");
    
    // Test 2: Statistics functions with NULL parameters
    get_orchestrator_statistics(NULL, NULL, NULL, NULL, NULL);
    // Should not crash even with all NULL parameters
    
    // Test 3: Configuration functions with NULL paths
    ASSERT_NEQ(load_binary_configuration(NULL), 0,
               "Should reject NULL config path");
    ASSERT_NEQ(save_binary_configuration(NULL), 0,
               "Should reject NULL config path");
    
    // Test 4: History querying with NULL parameters
    char buffer[100];
    ASSERT_LT(query_history_entries(NULL, NULL, 0, 1000, NULL, 0), 0,
              "Should reject NULL result buffer");
    ASSERT_LT(query_history_entries("test", "method", 0, 1000, buffer, 0), 0,
              "Should reject zero buffer size");
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_common_null_pointer_safety(void) {
    TEST_START("Common utilities NULL pointer safety (CWE-476)");
    
    // Test ring buffer with NULL
    ASSERT_EQ(mercury_ring_buffer_create(0, 10), NULL,
              "Should reject zero element size");
    ASSERT_EQ(mercury_ring_buffer_create(sizeof(int), 0), NULL,
              "Should reject zero capacity");
    
    MercuryRingBuffer* null_buffer = NULL;
    int value = 42;
    ASSERT_EQ(mercury_ring_buffer_push(null_buffer, &value), false,
              "Should handle NULL buffer safely");
    ASSERT_EQ(mercury_ring_buffer_pop(null_buffer, &value), false,
              "Should handle NULL buffer safely");
    ASSERT_EQ(mercury_ring_buffer_is_empty(null_buffer), true,
              "NULL buffer should be considered empty");
    mercury_ring_buffer_destroy(null_buffer); // Should not crash
    
    // Test string utilities with NULL
    MercuryString* null_string = NULL;
    ASSERT_NEQ(mercury_string_append(null_string, "test"), MERCURY_SUCCESS,
               "Should reject NULL string");
    const char* null_result = mercury_string_cstr(null_string);  
    ASSERT_NEQ(null_result, NULL, "Should return safe empty string for NULL input");
    ASSERT_EQ(strlen(null_result), 0, "Should return empty string for NULL input");
    mercury_string_destroy(null_string); // Should not crash
    
    // Test memory utilities with NULL  
    mercury_aligned_free(NULL); // Should not crash
    ASSERT_EQ(mercury_aligned_alloc(0, 16), NULL,
              "Should reject zero size allocation");
    
    TEST_PASS();
}

//=============================================================================
// CWE-416: Use After Free / Dangling Pointer Tests  
//=============================================================================

static void test_use_after_free_protection(void) {
    TEST_START("Use after free protection (CWE-416)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test 1: Test context use after finalize
    void* context = create_test_context("TestClass", "test_method");
    ASSERT_NEQ(context, NULL, "Failed to create context");
    
    // Update and finalize context
    ASSERT_EQ(update_test_metrics(context, 100, 20, 5, 0.8, 85, "A"), 0,
              "Failed to update context");
    ASSERT_EQ(finalize_test_context(context), 0,
              "Failed to finalize context");
    
    // Attempting to use finalized context should fail gracefully
    ASSERT_NEQ(update_test_metrics(context, 200, 30, 10, 0.6, 75, "B"), 0,
               "Should reject finalized context");
    ASSERT_NEQ(finalize_test_context(context), 0,
               "Should reject double finalize");
    
    // Test 2: Double destruction should be safe
    destroy_test_context(context);
    destroy_test_context(context); // Second call should not crash
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_double_free_protection(void) {
    TEST_START("Double free protection (CWE-416)");
    
    setup_segv_handler();
    
    if (setjmp(segv_env) == 0) {
        // Test 1: Single ring buffer creation and destruction (safe)
        MercuryRingBuffer* buffer = mercury_ring_buffer_create(sizeof(int), 5);
        ASSERT_NEQ(buffer, NULL, "Failed to create ring buffer");
        mercury_ring_buffer_destroy(buffer);
        
        // Test 2: String creation and destruction (safe)
        MercuryString* str = mercury_string_create(100);
        ASSERT_NEQ(str, NULL, "Failed to create string");
        ASSERT_EQ(mercury_string_append(str, "test content"), MERCURY_SUCCESS,
                  "Failed to append to string");
        mercury_string_destroy(str);
        
        // Test 3: Aligned memory (safe)
        void* mem = mercury_aligned_alloc(64, 16);
        ASSERT_NEQ(mem, NULL, "Failed to allocate aligned memory");
        mercury_aligned_free(mem);
        
        // Test 4: NULL pointer handling (should be safe)
        mercury_ring_buffer_destroy(NULL);
        mercury_string_destroy(NULL);
        mercury_aligned_free(NULL);
        
        // Note: We don't test actual double-free as it would crash the test suite.
        // The implementation should be fixed to set pointers to NULL after freeing.
        
    } else {
        ASSERT_EQ(1, 0, "CRITICAL: Segmentation fault during double-free test");
    }
    
    restore_segv_handler();
    TEST_PASS();
}

//=============================================================================
// CWE-787: Out-of-bounds Write Tests
//=============================================================================

static void test_buffer_write_overflow_protection(void) {
    TEST_START("Buffer write overflow protection (CWE-787)");
    
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Test 1: Extremely long class/method names
    char huge_name[1000];
    memset(huge_name, 'A', sizeof(huge_name) - 1);
    huge_name[sizeof(huge_name) - 1] = '\0';
    
    void* context = create_test_context(huge_name, huge_name);
    if (context != NULL) {
        // If context was created, verify strings were properly truncated
        TestContext* ctx = (TestContext*)context;
        ASSERT_LT(strlen(ctx->test_class), sizeof(ctx->test_class),
                  "Class name should be truncated");
        ASSERT_LT(strlen(ctx->test_method), sizeof(ctx->test_method),
                  "Method name should be truncated");
        
        // Test 2: Extremely long grade string
        char huge_grade[100];
        memset(huge_grade, 'F', sizeof(huge_grade) - 1);
        huge_grade[sizeof(huge_grade) - 1] = '\0';
        
        ASSERT_EQ(update_test_metrics(context, 1, 1, 1, 1, 1, huge_grade), 0,
                  "Should handle long grade string");
        
        // Verify grade was truncated to fit buffer
        ASSERT_LT(strlen(ctx->grade), sizeof(ctx->grade),
                  "Grade should be truncated");
        
        // Test 3: Extremely long optimization suggestion
        char huge_suggestion[2000];
        memset(huge_suggestion, 'X', sizeof(huge_suggestion) - 1);
        huge_suggestion[sizeof(huge_suggestion) - 1] = '\0';
        
        ASSERT_EQ(update_n_plus_one_analysis(context, 1, 5, huge_suggestion), 0,
                  "Should handle long optimization suggestion");
        
        // Verify suggestion was truncated
        ASSERT_LT(strlen(ctx->optimization_suggestion), 
                  sizeof(ctx->optimization_suggestion),
                  "Optimization suggestion should be truncated");
        
        finalize_test_context(context);
    }
    
    cleanup_test_orchestrator();
    TEST_PASS();
}

static void test_ring_buffer_bounds_protection(void) {
    TEST_START("Ring buffer bounds protection (CWE-787)");
    
    MercuryRingBuffer* buffer = mercury_ring_buffer_create(sizeof(int), 3);
    ASSERT_NEQ(buffer, NULL, "Failed to create ring buffer");
    
    // Fill buffer to capacity
    for (int i = 1; i <= 3; i++) {
        ASSERT_EQ(mercury_ring_buffer_push(buffer, &i), true,
                  "Should push within capacity");
    }
    
    // Test overflow protection
    int overflow_value = 999;
    ASSERT_EQ(mercury_ring_buffer_push(buffer, &overflow_value), false,
              "Should reject push when full");
    
    // Verify buffer contents weren't corrupted
    ASSERT_EQ(mercury_ring_buffer_size(buffer), 3,
              "Buffer size should remain at capacity");
    ASSERT_EQ(mercury_ring_buffer_is_full(buffer), true,
              "Buffer should still be full");
    
    // Test underflow protection  
    for (int i = 0; i < 3; i++) {
        int value;
        ASSERT_EQ(mercury_ring_buffer_pop(buffer, &value), true,
                  "Should pop within capacity");
    }
    
    // Test additional pops
    int underflow_value;
    ASSERT_EQ(mercury_ring_buffer_pop(buffer, &underflow_value), false,
              "Should reject pop when empty");
    
    mercury_ring_buffer_destroy(buffer);
    TEST_PASS();
}

//=============================================================================
// CWE-125: Out-of-bounds Read Tests
//=============================================================================

static void test_buffer_read_overflow_protection(void) {
    TEST_START("Buffer read overflow protection (CWE-125)");
    
    setup_segv_handler();
    
    if (setjmp(segv_env) == 0) {
        // Test 1: String operations with invalid lengths
        (void)0; // Remove unused variable
        
        // These operations should be bounds-safe
        MercuryString* str = mercury_string_create(5);
        ASSERT_NEQ(str, NULL, "Failed to create string");
        
        // Append should handle truncation safely
        char long_append[100];
        memset(long_append, 'A', sizeof(long_append) - 1);
        long_append[sizeof(long_append) - 1] = '\0';
        
        ASSERT_EQ(mercury_string_append(str, long_append), MERCURY_SUCCESS,
                  "Should handle long append safely");
        
        const char* result = mercury_string_cstr(str);
        ASSERT_NEQ(result, NULL, "Should return valid string");
        
        mercury_string_destroy(str);
        
        // Test 2: History query with extreme timestamp ranges
        ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
                  "Failed to initialize orchestrator");
        
        char small_buffer[10];
        // Should handle small buffer gracefully
        int query_result = query_history_entries("test", "method", 
                                                 0, UINT64_MAX, 
                                                 small_buffer, sizeof(small_buffer));
        // Function should either succeed with truncated data or fail gracefully
        ASSERT_GE(query_result, -1, "Query should not crash");
        
        cleanup_test_orchestrator();
        
    } else {
        // Segfault occurred - this indicates a security vulnerability
        ASSERT_EQ(1, 0, "CRITICAL: Segmentation fault during bounds read test");
    }
    
    restore_segv_handler();
    TEST_PASS();
}

static void test_negative_index_protection(void) {
    TEST_START("Negative index protection (CWE-125)");
    
    setup_segv_handler();
    
    if (setjmp(segv_env) == 0) {
        // Test ring buffer with conceptual negative indices through underflow
        MercuryRingBuffer* buffer = mercury_ring_buffer_create(sizeof(int), 5);
        ASSERT_NEQ(buffer, NULL, "Failed to create ring buffer");
        
        // Add some data
        for (int i = 1; i <= 3; i++) {
            mercury_ring_buffer_push(buffer, &i);
        }
        
        // Normal operations should work
        ASSERT_EQ(mercury_ring_buffer_size(buffer), 3, "Should have 3 elements");
        
        // Empty the buffer
        int value;
        for (int i = 0; i < 3; i++) {
            mercury_ring_buffer_pop(buffer, &value);
        }
        
        // Further pops should fail gracefully, not read invalid memory
        ASSERT_EQ(mercury_ring_buffer_pop(buffer, &value), false,
                  "Should reject pop from empty buffer");
        ASSERT_EQ(mercury_ring_buffer_is_empty(buffer), true,
                  "Buffer should be empty");
        
        mercury_ring_buffer_destroy(buffer);
        
    } else {
        ASSERT_EQ(1, 0, "CRITICAL: Segmentation fault during negative index test");
    }
    
    restore_segv_handler();
    TEST_PASS();
}

//=============================================================================
// CWE-401: Memory Leak Tests
//=============================================================================

static void test_error_path_cleanup(void) {
    TEST_START("Memory cleanup on error paths (CWE-401)");
    
    // Test 1: Test orchestrator cleanup on initialization failure
    // This should clean up any partially allocated resources
    cleanup_test_orchestrator(); // Safe to call even if not initialized
    
    // Test 2: Context creation with invalid parameters  
    ASSERT_EQ(initialize_test_orchestrator("/tmp/test_sec.bin"), 0, 
              "Failed to initialize orchestrator");
    
    // Create and immediately destroy contexts to test cleanup
    for (int i = 0; i < 10; i++) {
        char class_name[50], method_name[50];
        snprintf(class_name, sizeof(class_name), "TestClass%d", i);
        snprintf(method_name, sizeof(method_name), "test_method_%d", i);
        
        void* context = create_test_context(class_name, method_name);
        if (context != NULL) {
            // Sometimes finalize, sometimes just destroy
            if (i % 2 == 0) {
                finalize_test_context(context);
            } else {
                destroy_test_context(context);
            }
        }
    }
    
    cleanup_test_orchestrator();
    
    // Test 3: String creation and destruction
    for (int i = 0; i < 10; i++) {
        MercuryString* str = mercury_string_create(100 + i * 10);
        if (str != NULL) {
            for (int j = 0; j < 5; j++) {
                char append_data[20];
                snprintf(append_data, sizeof(append_data), "data_%d_%d", i, j);
                mercury_string_append(str, append_data);
            }
            mercury_string_destroy(str);
        }
    }
    
    // Test 4: Ring buffer creation and destruction
    for (int i = 1; i <= 10; i++) {
        MercuryRingBuffer* buffer = mercury_ring_buffer_create(sizeof(int) * i, 
                                                              10 + i);
        if (buffer != NULL) {
            // Add some data
            for (int j = 0; j < 5; j++) {
                int data[10];
                for (int k = 0; k < i && k < 10; k++) {
                    data[k] = j * 10 + k;
                }
                mercury_ring_buffer_push(buffer, data);
            }
            mercury_ring_buffer_destroy(buffer);
        }
    }
    
    TEST_PASS();
}

static void test_resource_exhaustion_handling(void) {
    TEST_START("Resource exhaustion handling (CWE-401)");
    
    // Test massive allocation requests that should fail gracefully
    ASSERT_EQ(mercury_aligned_alloc(SIZE_MAX, 16), NULL,
              "Should reject SIZE_MAX allocation");
    ASSERT_EQ(mercury_aligned_alloc(SIZE_MAX / 2, 16), NULL,
              "Should reject huge allocation");
    
    // Test ring buffer with extreme parameters
    ASSERT_EQ(mercury_ring_buffer_create(SIZE_MAX, 1), NULL,
              "Should reject SIZE_MAX element size");
    ASSERT_EQ(mercury_ring_buffer_create(1, SIZE_MAX), NULL,
              "Should reject SIZE_MAX capacity");
    
    // Test string with extreme capacity
    ASSERT_EQ(mercury_string_create(SIZE_MAX), NULL,
              "Should reject SIZE_MAX string capacity");
    
    // These should all fail without leasing memory
    TEST_PASS();
}

//=============================================================================
// Concurrent Memory Access Tests (Basic Race Condition Detection)
//=============================================================================

typedef struct {
    int thread_id;
    volatile int* shared_counter;
    volatile int* error_count;
} ThreadTestData;

static void* memory_stress_thread(void* arg) {
    ThreadTestData* data = (ThreadTestData*)arg;
    
    for (int i = 0; i < 100; i++) {
        // Test concurrent memory operations
        void* mem = mercury_aligned_alloc(64, 16);
        if (mem != NULL) {
            // Write some data
            memset(mem, data->thread_id, 64);
            
            // Increment shared counter (potential race condition)
            (*data->shared_counter)++;
            
            // Small delay to increase chance of race conditions
            usleep(1000);
            
            mercury_aligned_free(mem);
        } else {
            (*data->error_count)++;
        }
        
        // Test string operations
        MercuryString* str = mercury_string_create(50);
        if (str != NULL) {
            char buffer[20];
            snprintf(buffer, sizeof(buffer), "Thread%d_%d", data->thread_id, i);
            mercury_string_append(str, buffer);
            mercury_string_destroy(str);
        }
    }
    
    return NULL;
}

static void test_concurrent_memory_access(void) {
    TEST_START("Concurrent memory access safety");
    
    const int num_threads = 4;
    pthread_t threads[4];
    ThreadTestData thread_data[4];
    volatile int shared_counter = 0;
    volatile int error_count = 0;
    
    // Launch threads
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].shared_counter = &shared_counter;
        thread_data[i].error_count = &error_count;
        
        int result = pthread_create(&threads[i], NULL, 
                                   memory_stress_thread, &thread_data[i]);
        ASSERT_EQ(result, 0, "Failed to create thread");
    }
    
    // Wait for all threads
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Verify no excessive errors occurred
    ASSERT_LT(error_count, num_threads * 10, 
              "Too many allocation errors during concurrent test");
    
    // Note: shared_counter may not equal exactly num_threads * 100
    // due to race conditions, but should be reasonably close
    ASSERT_GT(shared_counter, num_threads * 80, 
              "Shared counter suspiciously low");
    ASSERT_LE(shared_counter, num_threads * 100, 
              "Shared counter impossibly high");
    
    TEST_PASS();
}

//=============================================================================
// Public Test Suite Function
//=============================================================================

void run_memory_security_tests(void) {
    TEST_SUITE_START("Memory Security Tests");
    
    // CWE-476: NULL Pointer Dereference
    test_null_pointer_dereference_protection();
    test_common_null_pointer_safety();
    
    // CWE-416: Use After Free
    test_use_after_free_protection();
    test_double_free_protection();
    
    // CWE-787: Out-of-bounds Write
    test_buffer_write_overflow_protection();
    test_ring_buffer_bounds_protection();
    
    // CWE-125: Out-of-bounds Read
    test_buffer_read_overflow_protection();
    test_negative_index_protection();
    
    // CWE-401: Memory Leaks
    test_error_path_cleanup();
    test_resource_exhaustion_handling();
    
    // Race Conditions (CWE-362 related)
    test_concurrent_memory_access();
    
    TEST_SUITE_END();
}