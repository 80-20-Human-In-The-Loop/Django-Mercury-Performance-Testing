/**
 * Representative workload for Profile-Guided Optimization (PGO)
 * 
 * This program exercises the most common code paths in the Mercury
 * Performance Testing Framework to collect representative profile data.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>
#include "common.h"

#define WORKLOAD_TEXT_SIZE (256 * 1024)  // 256KB
#define WORKLOAD_ITERATIONS 100

// Generate realistic workload text
static void generate_workload_text(char* text, size_t size) {
    const char* common_patterns[] = {
        "SELECT * FROM users WHERE id = ",
        "INSERT INTO products VALUES (",
        "UPDATE inventory SET quantity = ",
        "DELETE FROM logs WHERE created_at < ",
        "CREATE INDEX ON users(email)",
        "ALTER TABLE orders ADD COLUMN ",
        "UNION ALL SELECT * FROM ",
        "JOIN orders ON users.id = orders.user_id",
        "GROUP BY category ORDER BY count DESC",
        "LIMIT 100 OFFSET 0"
    };
    const int num_patterns = sizeof(common_patterns) / sizeof(common_patterns[0]);
    
    size_t pos = 0;
    srand(42);  // Fixed seed for reproducible profiles
    
    while (pos < size - 200) {
        int idx = rand() % num_patterns;
        const char* pattern = common_patterns[idx];
        size_t len = strlen(pattern);
        
        if (pos + len < size - 100) {
            memcpy(text + pos, pattern, len);
            pos += len;
            
            // Add some random data
            int num = rand() % 10000;
            pos += snprintf(text + pos, size - pos, "%d; ", num);
        }
    }
    
    text[size - 1] = '\0';
}

// Exercise ring buffer operations (common hot path)
static void profile_ring_buffer_operations(void) {
    MercuryRingBuffer* buffer = mercury_ring_buffer_create(64, 512);
    if (!buffer) return;
    
    char test_data[64];
    char output_data[64];
    
    // Fill test data
    for (int i = 0; i < 64; i++) {
        test_data[i] = (char)(i & 0xFF);
    }
    
    // Exercise push/pop patterns
    for (int iter = 0; iter < WORKLOAD_ITERATIONS * 10; iter++) {
        // Batch push
        for (int i = 0; i < 100; i++) {
            test_data[0] = (char)(iter + i);
            mercury_ring_buffer_push(buffer, test_data);
        }
        
        // Batch pop
        for (int i = 0; i < 100; i++) {
            mercury_ring_buffer_pop(buffer, output_data);
        }
    }
    
    mercury_ring_buffer_destroy(buffer);
}

// Exercise memory pool operations (common hot path)
static void profile_memory_pool_operations(void) {
    memory_pool_t pool;
    memory_pool_init(&pool, 1024, 128);
    
    void* ptrs[64];
    
    // Exercise allocation/deallocation patterns
    for (int iter = 0; iter < WORKLOAD_ITERATIONS; iter++) {
        // Allocate in batches
        for (int i = 0; i < 64; i++) {
            ptrs[i] = memory_pool_alloc(&pool);
        }
        
        // Free in different patterns
        for (int i = 0; i < 64; i += 2) {
            if (ptrs[i]) memory_pool_free(&pool, ptrs[i]);
        }
        for (int i = 1; i < 64; i += 2) {
            if (ptrs[i]) memory_pool_free(&pool, ptrs[i]);
        }
    }
    
    memory_pool_destroy(&pool);
}

// Exercise string operations (common hot path)
static void profile_string_operations(void) {
    MercuryString* str = mercury_string_create(1024);
    if (!str) return;
    
    const char* test_strings[] = {
        "SELECT * FROM users",
        " WHERE status = 'active'",
        " AND created_at > '2023-01-01'",
        " ORDER BY id DESC",
        " LIMIT 100"
    };
    const int num_strings = sizeof(test_strings) / sizeof(test_strings[0]);
    
    // Exercise string building patterns
    for (int iter = 0; iter < WORKLOAD_ITERATIONS; iter++) {
        mercury_string_clear(str);
        
        for (int i = 0; i < num_strings; i++) {
            mercury_string_append(str, test_strings[i]);
        }
    }
    
    mercury_string_destroy(str);
}

// Exercise multi-pattern search (key optimization target)
static void profile_multi_pattern_search(const char* text, size_t text_len) {
    const char* search_patterns[] = {
        "SELECT",
        "INSERT", 
        "UPDATE",
        "DELETE",
        "CREATE",
        "ALTER",
        "UNION",
        "JOIN"
    };
    const size_t num_patterns = sizeof(search_patterns) / sizeof(search_patterns[0]);
    
    MercuryMultiPatternSearch* mps = mercury_multi_pattern_create(search_patterns, num_patterns);
    if (!mps) return;
    
    // Exercise search patterns
    for (int iter = 0; iter < WORKLOAD_ITERATIONS; iter++) {
        int pattern_id;
        int pos = mercury_multi_pattern_search_simd(mps, text, text_len, &pattern_id);
        
        // If found, search from next position
        if (pos >= 0 && pos + 10 < text_len) {
            mercury_multi_pattern_search_simd(mps, text + pos + 10, 
                                            text_len - pos - 10, &pattern_id);
        }
    }
    
    mercury_multi_pattern_destroy(mps);
}

// Exercise Boyer-Moore search
static void profile_boyer_moore_search(const char* text, size_t text_len) {
    const char* patterns[] = {
        "SELECT * FROM",
        "INSERT INTO",
        "UPDATE SET",
        "DELETE FROM"
    };
    const int num_patterns = sizeof(patterns) / sizeof(patterns[0]);
    
    for (int p = 0; p < num_patterns; p++) {
        MercuryBoyerMoore* bm = mercury_boyer_moore_create(patterns[p]);
        if (!bm) continue;
        
        // Exercise search
        for (int iter = 0; iter < WORKLOAD_ITERATIONS / 4; iter++) {
            mercury_boyer_moore_search(bm, text, text_len, patterns[p]);
        }
        
        mercury_boyer_moore_destroy(bm);
    }
}

int main() {
    printf("🎯 Running PGO Representative Workload\n");
    printf("=====================================\n");
    
    // Initialize Mercury
    mercury_init();
    
    // Generate workload text
    printf("📝 Generating workload text...\n");
    char* text = malloc(WORKLOAD_TEXT_SIZE);
    if (!text) {
        printf("❌ Failed to allocate workload text\n");
        mercury_cleanup();
        return 1;
    }
    generate_workload_text(text, WORKLOAD_TEXT_SIZE);
    
    // Exercise common operations to collect profile data
    printf("🔄 Exercising ring buffer operations...\n");
    profile_ring_buffer_operations();
    
    printf("🗃️  Exercising memory pool operations...\n");
    profile_memory_pool_operations();
    
    printf("📝 Exercising string operations...\n");
    profile_string_operations();
    
    printf("🔍 Exercising multi-pattern search...\n");
    profile_multi_pattern_search(text, strlen(text));
    
    printf("🎯 Exercising Boyer-Moore search...\n");
    profile_boyer_moore_search(text, strlen(text));
    
    printf("✅ PGO workload completed - profile data collected\n");
    
    // Cleanup
    free(text);
    mercury_cleanup();
    
    return 0;
}