/**
 * @file simple_test_advanced.c
 * @brief Clean advanced tests for common.c functionality
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
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

int test_multi_pattern_search(void) {
    const char* text = "The quick brown fox jumps over the lazy dog. "
                      "The brown dog was quick to jump over the lazy fox.";
    
    // Test 1: Find all occurrences of multiple patterns
    const char* patterns[] = {"quick", "brown", "fox", "dog", "lazy"};
    int pattern_count = 5;
    int total_matches = 0;
    
    for (int i = 0; i < pattern_count; i++) {
        const char* ptr = text;
        int matches = 0;
        
        while ((ptr = strstr(ptr, patterns[i])) != NULL) {
            matches++;
            ptr += strlen(patterns[i]);
        }
        
        ASSERT(matches > 0, "Pattern should be found");
        total_matches += matches;
    }
    
    ASSERT(total_matches == 10, "Should find 10 total pattern matches");
    return 1;
}

// Thread data for producer-consumer test
typedef struct {
    MercuryRingBuffer* buffer;
    int start_value;
    int count;
} thread_data_t;

void* producer_thread(void* arg) {
    thread_data_t* data = (thread_data_t*)arg;
    
    for (int i = 0; i < data->count; i++) {
        int value = data->start_value + i;
        while (!mercury_ring_buffer_push(data->buffer, &value)) {
            usleep(1000); // Wait 1ms if buffer is full
        }
    }
    
    return NULL;
}

void* consumer_thread(void* arg) {
    thread_data_t* data = (thread_data_t*)arg;
    int values_read = 0;
    
    while (values_read < data->count) {
        int value;
        if (mercury_ring_buffer_pop(data->buffer, &value)) {
            values_read++;
        } else {
            usleep(1000); // Wait 1ms if buffer is empty
        }
    }
    
    return NULL;
}

int test_producer_consumer_ring_buffer(void) {
    MercuryRingBuffer* buffer = mercury_ring_buffer_create(sizeof(int), 64);
    ASSERT(buffer != NULL, "Ring buffer creation should succeed");
    
    const int num_producers = 2;
    const int num_consumers = 2;
    const int items_per_thread = 100;
    
    pthread_t producers[2];
    pthread_t consumers[2];
    thread_data_t producer_data[2];
    thread_data_t consumer_data[2];
    
    // Start producers
    for (int i = 0; i < num_producers; i++) {
        producer_data[i].buffer = buffer;
        producer_data[i].start_value = i * items_per_thread;
        producer_data[i].count = items_per_thread;
        pthread_create(&producers[i], NULL, producer_thread, &producer_data[i]);
    }
    
    // Start consumers
    for (int i = 0; i < num_consumers; i++) {
        consumer_data[i].buffer = buffer;
        consumer_data[i].count = items_per_thread;
        pthread_create(&consumers[i], NULL, consumer_thread, &consumer_data[i]);
    }
    
    // Wait for all threads
    for (int i = 0; i < num_producers; i++) {
        pthread_join(producers[i], NULL);
    }
    for (int i = 0; i < num_consumers; i++) {
        pthread_join(consumers[i], NULL);
    }
    
    ASSERT(mercury_ring_buffer_is_empty(buffer), "Buffer should be empty after all operations");
    
    mercury_ring_buffer_destroy(buffer);
    return 1;
}

int test_memory_pool_stress(void) {
    // Test rapid allocation/deallocation patterns
    const int iterations = 1000;
    void* ptrs[100];
    int total_allocs = 0;
    int failed_allocs = 0;
    
    for (int iter = 0; iter < iterations; iter++) {
        // Allocate random sizes
        for (int i = 0; i < 100; i++) {
            size_t size = 16 + (rand() % 1024);
            size_t alignment = 1 << (4 + (rand() % 3)); // 16, 32, or 64
            ptrs[i] = mercury_aligned_alloc(size, alignment);
            total_allocs++;
            
            if (ptrs[i] == NULL) {
                failed_allocs++;
            } else if (((uintptr_t)ptrs[i] % alignment) != 0) {
                failed_allocs++;
            }
        }
        
        // Free in random order
        for (int i = 99; i >= 0; i--) {
            if (ptrs[i] != NULL) {
                mercury_aligned_free(ptrs[i]);
            }
        }
    }
    
    // Single summary assertion
    ASSERT(failed_allocs == 0, "All allocations should succeed and be aligned");
    printf("  Completed %d allocations successfully\n", total_allocs);
    
    return 1;
}

int test_string_builder_performance(void) {
    MercuryString* str = mercury_string_create(16);
    ASSERT(str != NULL, "String creation should succeed");
    
    // Test rapid appends
    const int append_count = 1000;
    clock_t start = clock();
    
    for (int i = 0; i < append_count; i++) {
        char buf[32];
        snprintf(buf, sizeof(buf), "Line %d\n", i);
        if (mercury_string_append(str, buf) != MERCURY_SUCCESS) {
            ASSERT(0, "String append failed");
            break;
        }
    }
    
    clock_t end = clock();
    double time_spent = ((double)(end - start)) / CLOCKS_PER_SEC;
    
    // Basic performance check - should complete quickly
    ASSERT(time_spent < 1.0, "String building should be fast");
    
    const char* result = mercury_string_cstr(str);
    ASSERT(strlen(result) > append_count * 5, "String should contain all appended data");
    
    mercury_string_destroy(str);
    return 1;
}

int test_boyer_moore_performance(void) {
    // Create a large text to search
    const int text_size = 10000;
    char* large_text = malloc(text_size);
    ASSERT(large_text != NULL, "Memory allocation should succeed");
    
    // Fill with repeating pattern
    const char* base = "The quick brown fox jumps over the lazy dog. ";
    int base_len = strlen(base);
    for (int i = 0; i < text_size - base_len; i += base_len) {
        memcpy(large_text + i, base, base_len);
    }
    large_text[text_size - 1] = '\0';
    
    // Search for pattern at end
    const char* pattern = "lazy dog";
    MercuryBoyerMoore* bm = mercury_boyer_moore_create(pattern);
    ASSERT(bm != NULL, "Boyer-Moore creation should succeed");
    
    clock_t start = clock();
    int matches = 0;
    int pos = 0;
    
    while ((size_t)pos < text_size - strlen(pattern)) {
        int found = mercury_boyer_moore_search(bm, large_text + pos, 
                                              text_size - pos, pattern);
        if (found >= 0) {
            matches++;
            pos += found + strlen(pattern);
        } else {
            break;
        }
    }
    
    clock_t end = clock();
    double time_spent = ((double)(end - start)) / CLOCKS_PER_SEC;
    
    ASSERT(matches > 100, "Should find many matches");
    ASSERT(time_spent < 0.1, "Boyer-Moore should be fast");
    
    mercury_boyer_moore_destroy(bm);
    free(large_text);
    return 1;
}

int main(void) {
    QUIET_MODE_INIT();  // Initialize quiet mode from TEST_VERBOSE env var
    TEST_SUITE_START("Advanced Common Tests");
    
    RUN_TEST(test_multi_pattern_search);
    RUN_TEST(test_producer_consumer_ring_buffer);
    RUN_TEST(test_memory_pool_stress);
    RUN_TEST(test_string_builder_performance);
    RUN_TEST(test_boyer_moore_performance);
    
    TEST_SUITE_END();
    
    return (failed_tests == 0) ? 0 : 1;
}