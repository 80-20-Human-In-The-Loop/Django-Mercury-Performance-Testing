/**
 * @file test_debug_helpers.h
 * @brief Debug helper functions for test inspection and analysis
 * 
 * Provides utilities for dumping state, analyzing failures, and
 * understanding test behavior during debugging sessions.
 */

#ifndef TEST_DEBUG_HELPERS_H
#define TEST_DEBUG_HELPERS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>
#include "../common.h"

// Forward declarations for analyzer types
typedef struct QueryCluster QueryCluster;
typedef struct QueryAnalyzer QueryAnalyzer;

/**
 * Hex dump a buffer for inspection
 */
static void debug_hex_dump(const char* label, const void* data, size_t size) {
    printf("\n=== HEX DUMP: %s (%zu bytes) ===\n", label, size);
    
    const unsigned char* bytes = (const unsigned char*)data;
    char ascii[17];
    size_t i, j;
    
    ascii[16] = '\0';
    
    for (i = 0; i < size; i++) {
        // Print offset at beginning of line
        if (i % 16 == 0) {
            printf("%06zx: ", i);
        }
        
        // Print hex byte
        printf("%02x ", bytes[i]);
        
        // Store ASCII representation
        if (isprint(bytes[i])) {
            ascii[i % 16] = bytes[i];
        } else {
            ascii[i % 16] = '.';
        }
        
        // Print ASCII at end of line
        if ((i + 1) % 16 == 0) {
            printf(" |%s|\n", ascii);
        } else if (i + 1 == size) {
            // Last line padding
            ascii[(i % 16) + 1] = '\0';
            for (j = (i % 16) + 1; j < 16; j++) {
                printf("   ");
            }
            printf(" |%s|\n", ascii);
        }
    }
    
    printf("=== END HEX DUMP ===\n\n");
}

/**
 * Dump query analyzer state for debugging
 */
static void debug_dump_query_analyzer_state(void) {
    printf("\n=== QUERY ANALYZER STATE ===\n");
    
    // Get statistics
    uint64_t total_queries, n_plus_one_detected, similar_queries;
    int active_clusters;
    
    extern void get_query_statistics(uint64_t*, uint64_t*, uint64_t*, int*);
    get_query_statistics(&total_queries, &n_plus_one_detected, 
                        &similar_queries, &active_clusters);
    
    printf("Total Queries:     %lu\n", total_queries);
    printf("N+1 Detected:      %lu\n", n_plus_one_detected);
    printf("Similar Queries:   %lu\n", similar_queries);
    printf("Active Clusters:   %d\n", active_clusters);
    
    // Get severity information
    extern int get_n_plus_one_severity(void);
    extern int get_n_plus_one_cause(void);
    extern const char* get_optimization_suggestion(void);
    
    int severity = get_n_plus_one_severity();
    int cause = get_n_plus_one_cause();
    const char* suggestion = get_optimization_suggestion();
    
    printf("\nN+1 Analysis:\n");
    printf("  Severity: %d ", severity);
    switch(severity) {
        case 0: printf("(NONE)\n"); break;
        case 1: printf("(MILD)\n"); break;
        case 2: printf("(MODERATE)\n"); break;
        case 3: printf("(HIGH)\n"); break;
        case 4: printf("(SEVERE)\n"); break;
        case 5: printf("(CRITICAL)\n"); break;
        default: printf("(UNKNOWN)\n"); break;
    }
    
    printf("  Cause: %d ", cause);
    switch(cause) {
        case 0: printf("(No issue)\n"); break;
        case 1: printf("(Serializer methods)\n"); break;
        case 2: printf("(Missing select_related)\n"); break;
        case 3: printf("(Missing prefetch_related)\n"); break;
        case 4: printf("(Loop queries)\n"); break;
        default: printf("(Unknown)\n"); break;
    }
    
    printf("  Suggestion: %s\n", suggestion ? suggestion : "(none)");
    
    // Get duplicate queries report
    char report[2048];
    extern int get_duplicate_queries(char*, size_t);
    int dup_count = get_duplicate_queries(report, sizeof(report));
    
    if (dup_count > 0) {
        printf("\nDuplicate Query Clusters (%d):\n", dup_count);
        printf("%s", report);
    } else {
        printf("\nNo duplicate queries found.\n");
    }
    
    printf("=== END ANALYZER STATE ===\n\n");
}

/**
 * Compare two values and show difference
 */
static void debug_compare_values(const char* label, int expected, int actual) {
    printf("\n=== VALUE COMPARISON: %s ===\n", label);
    printf("Expected: %d (0x%08x) [binary: ", expected, expected);
    for (int i = 31; i >= 0; i--) {
        printf("%d", (expected >> i) & 1);
        if (i % 8 == 0 && i > 0) printf(" ");
    }
    printf("]\n");
    
    printf("Actual:   %d (0x%08x) [binary: ", actual, actual);
    for (int i = 31; i >= 0; i--) {
        printf("%d", (actual >> i) & 1);
        if (i % 8 == 0 && i > 0) printf(" ");
    }
    printf("]\n");
    
    printf("Diff:     %d (", actual - expected);
    if (actual > expected) {
        printf("+%d", actual - expected);
    } else {
        printf("%d", actual - expected);
    }
    printf(")\n");
    
    // Show boundary analysis
    printf("\nBoundary Analysis:\n");
    if (expected >= 0 && expected <= 5) {
        const char* boundaries[] = {
            "0: No queries (NONE)",
            "1-4: Few queries (MILD starts at 5)",
            "5-7: MILD severity",
            "8-11: MODERATE severity",
            "12-24: HIGH severity",
            "25-49: SEVERE severity",
            "50+: CRITICAL severity"
        };
        
        printf("  Expected falls in: ");
        if (expected == 0) printf("%s\n", boundaries[0]);
        else if (expected < 5) printf("%s\n", boundaries[1]);
        else if (expected < 8) printf("%s\n", boundaries[2]);
        else if (expected < 12) printf("%s\n", boundaries[3]);
        else if (expected < 25) printf("%s\n", boundaries[4]);
        else if (expected < 50) printf("%s\n", boundaries[5]);
        else printf("%s\n", boundaries[6]);
        
        printf("  Actual falls in: ");
        if (actual == 0) printf("%s\n", boundaries[0]);
        else if (actual < 5) printf("%s\n", boundaries[1]);
        else if (actual < 8) printf("%s\n", boundaries[2]);
        else if (actual < 12) printf("%s\n", boundaries[3]);
        else if (actual < 25) printf("%s\n", boundaries[4]);
        else if (actual < 50) printf("%s\n", boundaries[5]);
        else printf("%s\n", boundaries[6]);
    }
    
    printf("=== END COMPARISON ===\n\n");
}

/**
 * Memory usage tracker
 */
typedef struct {
    size_t allocated;
    size_t freed;
    size_t peak;
    int allocations;
    int deallocations;
} MemoryStats;

static MemoryStats test_memory_stats = {0};

static void debug_reset_memory_stats(void) {
    memset(&test_memory_stats, 0, sizeof(test_memory_stats));
}

static void debug_track_allocation(size_t size) {
    test_memory_stats.allocated += size;
    test_memory_stats.allocations++;
    if (test_memory_stats.allocated - test_memory_stats.freed > test_memory_stats.peak) {
        test_memory_stats.peak = test_memory_stats.allocated - test_memory_stats.freed;
    }
}

static void debug_track_deallocation(size_t size) {
    test_memory_stats.freed += size;
    test_memory_stats.deallocations++;
}

static void debug_print_memory_stats(void) {
    printf("\n=== MEMORY STATISTICS ===\n");
    printf("Total Allocated:  %zu bytes\n", test_memory_stats.allocated);
    printf("Total Freed:      %zu bytes\n", test_memory_stats.freed);
    printf("Peak Usage:       %zu bytes\n", test_memory_stats.peak);
    printf("Current Usage:    %zu bytes\n", 
           test_memory_stats.allocated - test_memory_stats.freed);
    printf("Allocations:      %d\n", test_memory_stats.allocations);
    printf("Deallocations:    %d\n", test_memory_stats.deallocations);
    
    if (test_memory_stats.allocated != test_memory_stats.freed) {
        printf("\n⚠️  WARNING: Memory leak detected! ");
        printf("%zu bytes not freed\n", 
               test_memory_stats.allocated - test_memory_stats.freed);
    } else {
        printf("\n✓ All memory properly freed\n");
    }
    
    printf("=== END MEMORY STATS ===\n\n");
}

/**
 * String diff utility for better error messages
 */
static void debug_string_diff(const char* label, const char* expected, const char* actual) {
    printf("\n=== STRING DIFF: %s ===\n", label);
    
    if (!expected) {
        printf("Expected: (NULL)\n");
    } else {
        printf("Expected: \"%s\"\n", expected);
    }
    
    if (!actual) {
        printf("Actual:   (NULL)\n");
    } else {
        printf("Actual:   \"%s\"\n", actual);
    }
    
    if (expected && actual) {
        size_t exp_len = strlen(expected);
        size_t act_len = strlen(actual);
        
        printf("\nLength: Expected=%zu, Actual=%zu\n", exp_len, act_len);
        
        // Find first difference
        size_t first_diff = 0;
        while (expected[first_diff] && actual[first_diff] && 
               expected[first_diff] == actual[first_diff]) {
            first_diff++;
        }
        
        if (first_diff < exp_len || first_diff < act_len) {
            printf("\nFirst difference at position %zu:\n", first_diff);
            printf("  Expected[%zu]: '%c' (0x%02x)\n", 
                   first_diff, 
                   first_diff < exp_len ? expected[first_diff] : '\0',
                   first_diff < exp_len ? (unsigned char)expected[first_diff] : 0);
            printf("  Actual[%zu]:   '%c' (0x%02x)\n", 
                   first_diff,
                   first_diff < act_len ? actual[first_diff] : '\0',
                   first_diff < act_len ? (unsigned char)actual[first_diff] : 0);
            
            // Show context around difference
            size_t context_start = first_diff > 10 ? first_diff - 10 : 0;
            size_t context_end = first_diff + 10;
            
            printf("\nContext (10 chars before/after):\n");
            printf("  Expected: \"");
            for (size_t i = context_start; i < context_end && i < exp_len; i++) {
                if (i == first_diff) printf("[");
                printf("%c", expected[i]);
                if (i == first_diff) printf("]");
            }
            printf("\"\n");
            
            printf("  Actual:   \"");
            for (size_t i = context_start; i < context_end && i < act_len; i++) {
                if (i == first_diff) printf("[");
                printf("%c", actual[i]);
                if (i == first_diff) printf("]");
            }
            printf("\"\n");
        } else {
            printf("\nStrings are identical.\n");
        }
    }
    
    printf("=== END STRING DIFF ===\n\n");
}

/**
 * Query pattern generator for testing
 */
static void debug_generate_n_plus_one_pattern(int parent_count, int children_per_parent) {
    printf("\n=== GENERATING N+1 PATTERN ===\n");
    printf("Pattern: %d parent(s), %d children each\n", parent_count, children_per_parent);
    printf("Total queries: %d\n", parent_count + (parent_count * children_per_parent));
    printf("\nGenerated queries:\n");
    
    // Generate parent queries
    for (int p = 0; p < parent_count; p++) {
        printf("  [PARENT %d] SELECT * FROM posts WHERE id = %d\n", p, p);
        
        // Generate child queries
        for (int c = 0; c < children_per_parent; c++) {
            printf("    [CHILD %d.%d] SELECT * FROM comments WHERE post_id = %d\n", 
                   p, c, p);
        }
    }
    
    printf("\nExpected severity based on total queries:\n");
    int total = parent_count + (parent_count * children_per_parent);
    if (total < 5) printf("  NONE (0) - Less than 5 queries\n");
    else if (total < 8) printf("  MILD (1) - 5-7 queries\n");
    else if (total < 12) printf("  MODERATE (2) - 8-11 queries\n");
    else if (total < 25) printf("  HIGH (3) - 12-24 queries\n");
    else if (total < 50) printf("  SEVERE (4) - 25-49 queries\n");
    else printf("  CRITICAL (5) - 50+ queries\n");
    
    printf("=== END PATTERN GENERATION ===\n\n");
}

/**
 * Test execution tracer
 */
#define TRACE_FUNCTION_ENTRY() do { \
    if (getenv("TEST_TRACE")) { \
        printf("[TRACE] Entering %s at %s:%d\n", __func__, __FILE__, __LINE__); \
    } \
} while(0)

#define TRACE_FUNCTION_EXIT() do { \
    if (getenv("TEST_TRACE")) { \
        printf("[TRACE] Exiting %s\n", __func__); \
    } \
} while(0)

#define TRACE_VALUE(name, value, format) do { \
    if (getenv("TEST_TRACE")) { \
        printf("[TRACE] %s = " format "\n", name, value); \
    } \
} while(0)

#endif // TEST_DEBUG_HELPERS_H