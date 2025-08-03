#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <pthread.h>

typedef struct {
    uint64_t start_time_ns;
    uint64_t end_time_ns;
    size_t memory_start_bytes;
    size_t memory_peak_bytes;
    size_t memory_end_bytes;
    uint32_t session_query_count;
    uint32_t session_cache_hits;
    uint32_t session_cache_misses;
    char operation_name[256];
    char operation_type[64];
    pthread_mutex_t session_mutex;
    int64_t session_id;
} EnhancedPerformanceMetrics_t;

int main() {
    printf("Structure layout:\n");
    printf("start_time_ns offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, start_time_ns));
    printf("end_time_ns offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, end_time_ns));
    printf("memory_start_bytes offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, memory_start_bytes));
    printf("memory_peak_bytes offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, memory_peak_bytes));
    printf("memory_end_bytes offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, memory_end_bytes));
    printf("session_query_count offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, session_query_count));
    printf("session_cache_hits offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, session_cache_hits));
    printf("session_cache_misses offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, session_cache_misses));
    printf("operation_name offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, operation_name));
    printf("operation_type offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, operation_type));
    printf("session_mutex offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, session_mutex));
    printf("session_id offset: %zu\n", offsetof(EnhancedPerformanceMetrics_t, session_id));
    printf("\nTotal structure size: %zu\n", sizeof(EnhancedPerformanceMetrics_t));
    printf("pthread_mutex_t size: %zu\n", sizeof(pthread_mutex_t));
    return 0;
}
