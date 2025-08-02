/*
 * common.c - Implementation of shared utilities for Mercury Performance Testing Framework
 * 
 * This file implements the common data structures and utility functions declared in common.h.
 * It provides cross-platform compatibility and high-performance implementations for:
 * - Memory management and ring buffers
 * - String operations and Boyer-Moore pattern matching
 * - Timing utilities and RDTSC calibration
 * - SIMD-accelerated operations
 * - Error handling and logging
 *
 * Author: EduLite Performance Team
 * Version: 2.0.0
 */

/* Define feature test macros BEFORE any includes */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif

#include "common.h"
#include <assert.h>
#include <stdarg.h>

#ifdef MERCURY_LINUX
#include <time.h>
#endif

// === GLOBAL VARIABLES ===

// RDTSC frequency for timing calibration
#ifdef MERCURY_X86_64
uint64_t mercury_rdtsc_frequency = 0;
#endif

// Thread-local error context
#ifdef __STDC_NO_THREADS__
    MercuryErrorContext mercury_last_error = {MERCURY_SUCCESS, {0}, NULL, NULL, 0};
#else
    _Thread_local MercuryErrorContext mercury_last_error = {MERCURY_SUCCESS, {0}, NULL, NULL, 0};
#endif

// Default logger function pointer
void (*mercury_log_function)(MercuryLogLevel level, const char* format, ...) = mercury_default_logger;

// === TIMING UTILITIES ===

#ifdef MERCURY_X86_64
void mercury_calibrate_rdtsc(void) {
    if (mercury_rdtsc_frequency != 0) {
        return;  // Already calibrated
    }
    
    // Calibrate RDTSC against system clock
    MercuryTimestamp start_sys = mercury_get_timestamp();
    uint64_t start_rdtsc = mercury_rdtsc();
    
    // Wait approximately 100ms
    #ifdef MERCURY_LINUX
        struct timespec sleep_time = {0, 100000000};  // 100ms
        nanosleep(&sleep_time, NULL);
    #elif defined(MERCURY_MACOS)
        usleep(100000);  // 100ms
    #elif defined(MERCURY_WINDOWS)
        Sleep(100);  // 100ms
    #endif
    
    MercuryTimestamp end_sys = mercury_get_timestamp();
    uint64_t end_rdtsc = mercury_rdtsc();
    
    uint64_t sys_elapsed = end_sys.nanoseconds - start_sys.nanoseconds;
    uint64_t rdtsc_elapsed = end_rdtsc - start_rdtsc;
    
    if (sys_elapsed > 0 && rdtsc_elapsed > 0) {
        mercury_rdtsc_frequency = (rdtsc_elapsed * 1000000000ULL) / sys_elapsed;
        MERCURY_INFO("RDTSC calibrated: %llu Hz", mercury_rdtsc_frequency);
    } else {
        MERCURY_WARN("RDTSC calibration failed, using fallback timing");
        mercury_rdtsc_frequency = 1;  // Fallback to prevent division by zero
    }
}
#endif

// === MEMORY UTILITIES ===

void* mercury_aligned_alloc(size_t size, size_t alignment) {
    if (size == 0 || alignment == 0 || (alignment & (alignment - 1)) != 0) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Invalid size or alignment");
        return NULL;
    }
    
    void* ptr = NULL;
    
#ifdef MERCURY_LINUX
    if (posix_memalign(&ptr, alignment, size) != 0) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "posix_memalign failed");
        return NULL;
    }
#elif defined(MERCURY_MACOS)
    if (posix_memalign(&ptr, alignment, size) != 0) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "posix_memalign failed");
        return NULL;
    }
#elif defined(MERCURY_WINDOWS)
    ptr = _aligned_malloc(size, alignment);
    if (!ptr) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "_aligned_malloc failed");
        return NULL;
    }
#else
    // Fallback: allocate extra space and align manually
    void* raw_ptr = malloc(size + alignment - 1 + sizeof(void*));
    if (!raw_ptr) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "malloc failed");
        return NULL;
    }
    
    char* aligned_ptr = (char*)raw_ptr + sizeof(void*);
    aligned_ptr += alignment - ((uintptr_t)aligned_ptr % alignment);
    ((void**)aligned_ptr)[-1] = raw_ptr;  // Store original pointer
    ptr = aligned_ptr;
#endif
    
    return ptr;
}

void mercury_aligned_free(void* ptr) {
    if (!ptr) return;
    
#ifdef MERCURY_LINUX
    free(ptr);
#elif defined(MERCURY_MACOS)
    free(ptr);
#elif defined(MERCURY_WINDOWS)
    _aligned_free(ptr);
#else
    // Fallback: retrieve original pointer and free
    void* raw_ptr = ((void**)ptr)[-1];
    free(raw_ptr);
#endif
}

// === RING BUFFER IMPLEMENTATION ===

MercuryRingBuffer* mercury_ring_buffer_create(size_t element_size, size_t capacity) {
    if (element_size == 0 || capacity == 0) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Invalid element size or capacity");
        return NULL;
    }
    
    // Check for overflow in size calculation
    size_t total_size;
    if (!mercury_safe_mul_size(element_size, capacity, &total_size)) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, 
                         "Buffer size would overflow");
        return NULL;
    }
    
    // Sanity check: limit to 1GB to prevent accidental huge allocations
    if (total_size > (1ULL << 30)) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, 
                         "Buffer size too large (max 1GB)");
        return NULL;
    }
    
    MercuryRingBuffer* buffer = mercury_aligned_alloc(sizeof(MercuryRingBuffer), 64);
    if (!buffer) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, 
                         "Failed to allocate ring buffer structure");
        return NULL;
    }
    
    buffer->data = mercury_aligned_alloc(total_size, 64);
    if (!buffer->data) {
        mercury_aligned_free(buffer);
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, 
                         "Failed to allocate ring buffer data");
        return NULL;
    }
    
    buffer->element_size = element_size;
    buffer->capacity = capacity;
    atomic_store(&buffer->head, 0);
    atomic_store(&buffer->tail, 0);
    atomic_store(&buffer->count, 0);
    
    return buffer;
}

void mercury_ring_buffer_destroy(MercuryRingBuffer* buffer) {
    if (!buffer) return;
    
    mercury_aligned_free(buffer->data);
    mercury_aligned_free(buffer);
}

bool mercury_ring_buffer_push(MercuryRingBuffer* buffer, const void* element) {
    if (MERCURY_UNLIKELY(!buffer || !element)) {
        return false;
    }
    
    // Debug: verify buffer integrity
    MERCURY_VERIFY_BUFFER(buffer);
    
    // Atomic CAS loop to ensure we don't exceed capacity
    size_t current_count, new_count;
    do {
        current_count = atomic_load_explicit(&buffer->count, memory_order_acquire);
        if (MERCURY_UNLIKELY(current_count >= buffer->capacity)) {
            return false;  // Buffer is full
        }
        new_count = current_count + 1;
    } while (!atomic_compare_exchange_weak_explicit(&buffer->count, &current_count, new_count,
                                                    memory_order_acq_rel, memory_order_acquire));
    
    // Now we have successfully reserved a slot, get our position
    size_t head = atomic_fetch_add_explicit(&buffer->head, 1, memory_order_acq_rel);
    head = head % buffer->capacity;  // Wrap around
    
    // Copy data to reserved slot
    char* dest = (char*)buffer->data + (head * buffer->element_size);
    
    // Prefetch destination for write
    MERCURY_PREFETCH_WRITE(dest);
    
    // Prefetch next few slots for sequential writes (cache warming)
    if (MERCURY_LIKELY(head + 1 < buffer->capacity)) {
        MERCURY_PREFETCH_WRITE_LOW((char*)buffer->data + ((head + 1) * buffer->element_size));
    }
    if (MERCURY_LIKELY(head + 2 < buffer->capacity)) {
        MERCURY_PREFETCH_WRITE_LOW((char*)buffer->data + ((head + 2) * buffer->element_size));
    }
    
    // Optimized copy based on element size
    if (buffer->element_size <= 8) {
        // Fast path for small elements (like ints, pointers)
        memcpy(dest, element, buffer->element_size);
    } else if (buffer->element_size >= 32) {
        // SIMD path for larger elements
        mercury_memcpy_simd(dest, element, buffer->element_size);
    } else {
        // Regular memcpy for medium elements
        memcpy(dest, element, buffer->element_size);
    }
    
    // Count was already updated atomically in the CAS loop above
    
    return true;
}

bool mercury_ring_buffer_pop(MercuryRingBuffer* buffer, void* element) {
    if (MERCURY_UNLIKELY(!buffer || !element)) {
        return false;
    }
    
    // Debug: verify buffer integrity
    MERCURY_VERIFY_BUFFER(buffer);
    
    // Atomic CAS loop to ensure we don't pop from empty buffer
    size_t current_count, new_count;
    do {
        current_count = atomic_load_explicit(&buffer->count, memory_order_acquire);
        if (MERCURY_UNLIKELY(current_count == 0)) {
            return false;  // Buffer is empty
        }
        new_count = current_count - 1;
    } while (!atomic_compare_exchange_weak_explicit(&buffer->count, &current_count, new_count,
                                                    memory_order_acq_rel, memory_order_acquire));
    
    // Now we have successfully reserved a slot, get our position
    size_t tail = atomic_fetch_add_explicit(&buffer->tail, 1, memory_order_acq_rel);
    tail = tail % buffer->capacity;  // Wrap around
    
    // Copy data from reserved slot
    const char* src = (const char*)buffer->data + (tail * buffer->element_size);
    
    // Prefetch source for read
    MERCURY_PREFETCH_READ(src);
    
    // Prefetch next few slots for sequential reads (cache warming)
    if (MERCURY_LIKELY(tail + 1 < buffer->capacity)) {
        MERCURY_PREFETCH_READ_LOW((const char*)buffer->data + ((tail + 1) * buffer->element_size));
    }
    if (MERCURY_LIKELY(tail + 2 < buffer->capacity)) {
        MERCURY_PREFETCH_READ_LOW((const char*)buffer->data + ((tail + 2) * buffer->element_size));
    }
    
    // Optimized copy based on element size
    if (buffer->element_size <= 8) {
        // Fast path for small elements (like ints, pointers)
        memcpy(element, src, buffer->element_size);
    } else if (buffer->element_size >= 32) {
        // SIMD path for larger elements
        mercury_memcpy_simd(element, src, buffer->element_size);
    } else {
        // Regular memcpy for medium elements
        memcpy(element, src, buffer->element_size);
    }
    
    // Count was already updated atomically in the CAS loop above
    
    return true;
}

size_t mercury_ring_buffer_size(const MercuryRingBuffer* buffer) {
    if (!buffer) return 0;
    return atomic_load(&buffer->count);
}

bool mercury_ring_buffer_is_full(const MercuryRingBuffer* buffer) {
    if (!buffer) return true;
    return atomic_load(&buffer->count) >= buffer->capacity;
}

bool mercury_ring_buffer_is_empty(const MercuryRingBuffer* buffer) {
    if (!buffer) return true;
    return atomic_load(&buffer->count) == 0;
}

// === STRING UTILITIES ===

MercuryString* mercury_string_create(size_t initial_capacity) {
    if (initial_capacity == 0) {
        initial_capacity = 256;  // Default capacity
    }
    
    MercuryString* str = malloc(sizeof(MercuryString));
    if (!str) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate string structure");
        return NULL;
    }
    
    str->data = malloc(initial_capacity);
    if (!str->data) {
        free(str);
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate string buffer");
        return NULL;
    }
    
    str->data[0] = '\0';
    str->length = 0;
    str->capacity = initial_capacity;
    
    return str;
}

void mercury_string_destroy(MercuryString* str) {
    if (!str) return;
    
    free(str->data);
    free(str);
}

MercuryError mercury_string_append(MercuryString* str, const char* text) {
    if (MERCURY_UNLIKELY(!str || !text)) {
        return MERCURY_ERROR_INVALID_ARGUMENT;
    }
    
    size_t text_len = strlen(text);
    if (MERCURY_UNLIKELY(text_len == 0)) {
        return MERCURY_SUCCESS;  // Nothing to append
    }
    
    size_t new_length = str->length + text_len;
    
    // Resize buffer if necessary with better growth strategy
    if (MERCURY_UNLIKELY(new_length + 1 > str->capacity)) {
        // Growth strategy: for small strings double, for large strings add 50%
        size_t new_capacity;
        if (str->capacity < 4096) {
            new_capacity = str->capacity * 2;
        } else {
            new_capacity = str->capacity + (str->capacity >> 1);  // +50%
        }
        
        // Ensure we have enough space
        if (new_capacity <= new_length) {
            new_capacity = new_length + 256;  // Add some padding
        }
        
        char* new_data = realloc(str->data, new_capacity);
        if (MERCURY_UNLIKELY(!new_data)) {
            MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to resize string buffer");
            return MERCURY_ERROR_OUT_OF_MEMORY;
        }
        
        str->data = new_data;
        str->capacity = new_capacity;
    }
    
    // Use optimized copy based on text length
    char* dest = str->data + str->length;
    
    // Prefetch destination for write operations
    MERCURY_PREFETCH_WRITE(dest);
    
    // For larger strings, prefetch additional cache lines
    if (text_len >= 64) {
        MERCURY_PREFETCH_WRITE_LOW(dest + 64);
    }
    if (text_len >= 128) {
        MERCURY_PREFETCH_WRITE_LOW(dest + 128);
    }
    
    if (text_len >= 32) {
        // SIMD path for large appends
        mercury_memcpy_simd(dest, text, text_len);
    } else if (text_len >= 8) {
        // Use 64-bit copies for medium strings
        const uint64_t* src64 = (const uint64_t*)text;
        uint64_t* dest64 = (uint64_t*)dest;
        size_t chunks = text_len / 8;
        size_t remainder = text_len % 8;
        
        for (size_t i = 0; i < chunks; i++) {
            dest64[i] = src64[i];
        }
        
        // Handle remainder
        if (remainder > 0) {
            memcpy(dest + chunks * 8, text + chunks * 8, remainder);
        }
    } else {
        // Fast path for small strings
        memcpy(dest, text, text_len);
    }
    
    str->length = new_length;
    str->data[str->length] = '\0';
    
    return MERCURY_SUCCESS;
}

MercuryError mercury_string_append_char(MercuryString* str, char c) {
    char temp[2] = {c, '\0'};
    return mercury_string_append(str, temp);
}

void mercury_string_clear(MercuryString* str) {
    if (!str) return;
    
    str->length = 0;
    if (str->data) {
        str->data[0] = '\0';
    }
}

const char* mercury_string_cstr(const MercuryString* str) {
    if (!str || !str->data) {
        return "";
    }
    return str->data;
}

// === BOYER-MOORE IMPLEMENTATION ===

static void compute_bad_char_table(const char* pattern, size_t pattern_len, int* bad_char_table) {
    // Initialize all entries to -1
    for (int i = 0; i < 256; i++) {
        bad_char_table[i] = -1;
    }
    
    // Fill the actual positions of characters in pattern
    for (size_t i = 0; i < pattern_len; i++) {
        bad_char_table[(unsigned char)pattern[i]] = (int)i;
    }
}

static void compute_good_suffix_table(const char* pattern, size_t pattern_len, int* good_suffix_table) {
    int* suffix = malloc(pattern_len * sizeof(int));
    if (!suffix) return;
    
    // Compute suffix array
    suffix[pattern_len - 1] = pattern_len;
    int g = pattern_len - 1;
    int f = 0;
    
    for (int i = pattern_len - 2; i >= 0; i--) {
        if (i > g && suffix[i + pattern_len - 1 - f] < i - g) {
            suffix[i] = suffix[i + pattern_len - 1 - f];
        } else {
            if (i < g) g = i;
            f = i;
            while (g >= 0 && pattern[g] == pattern[g + pattern_len - 1 - f]) {
                g--;
            }
            suffix[i] = f - g;
        }
    }
    
    // Compute good suffix table
    for (size_t i = 0; i < pattern_len; i++) {
        good_suffix_table[i] = pattern_len;
    }
    
    int j = 0;
    for (int i = pattern_len - 1; i >= 0; i--) {
        if (suffix[i] == i + 1) {
            for (; j < (int)(pattern_len - 1 - i); j++) {
                if (good_suffix_table[j] == (int)pattern_len) {
                    good_suffix_table[j] = pattern_len - 1 - i;
                }
            }
        }
    }
    
    for (size_t i = 0; i <= pattern_len - 2; i++) {
        good_suffix_table[pattern_len - 1 - suffix[i]] = pattern_len - 1 - i;
    }
    
    free(suffix);
}

MercuryBoyerMoore* mercury_boyer_moore_create(const char* pattern) {
    if (!pattern) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Pattern cannot be NULL");
        return NULL;
    }
    
    size_t pattern_len = strlen(pattern);
    if (pattern_len == 0) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Pattern cannot be empty");
        return NULL;
    }
    
    MercuryBoyerMoore* bm = malloc(sizeof(MercuryBoyerMoore));
    if (!bm) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate Boyer-Moore structure");
        return NULL;
    }
    
    bm->good_suffix_table = malloc(pattern_len * sizeof(int));
    if (!bm->good_suffix_table) {
        free(bm);
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate good suffix table");
        return NULL;
    }
    
    bm->pattern_length = pattern_len;
    
    compute_bad_char_table(pattern, pattern_len, bm->bad_char_table);
    compute_good_suffix_table(pattern, pattern_len, bm->good_suffix_table);
    
    return bm;
}

void mercury_boyer_moore_destroy(MercuryBoyerMoore* bm) {
    if (!bm) return;
    
    free(bm->good_suffix_table);
    free(bm);
}

int mercury_boyer_moore_search(const MercuryBoyerMoore* bm, const char* text, 
                              size_t text_length, const char* pattern) {
    if (!bm || !text || !pattern) {
        return -1;
    }
    
    size_t pattern_len = bm->pattern_length;
    
    // Defensive check to prevent integer underflow
    if (text_length < pattern_len || pattern_len == 0) {
        return -1;
    }
    
    size_t shift = 0;
    size_t max_shift = text_length - pattern_len;
    
    while (shift <= max_shift) {
        // Prefetch ahead for better cache performance
        if (shift + pattern_len + 64 <= text_length) {
            MERCURY_PREFETCH_READ_LOW(text + shift + pattern_len + 64);
        }
        
        // SIMD-accelerated pattern comparison for longer patterns
        if (pattern_len >= 16) {
            // For patterns >= 16 bytes, use SIMD for initial comparison
            const char* text_pos = text + shift;
            
            // Compare in 16-byte chunks from the end (Boyer-Moore style)
            size_t chunks = pattern_len / 16;
            size_t remainder = pattern_len % 16;
            bool match = true;
            
            // Check from right to left in 16-byte chunks
            for (size_t chunk = chunks; chunk > 0 && match; chunk--) {
                size_t offset = (chunk - 1) * 16 + remainder;
                
                #ifdef USE_SIMD
                __m128i pattern_chunk = _mm_loadu_si128((const __m128i*)(pattern + offset));
                __m128i text_chunk = _mm_loadu_si128((const __m128i*)(text_pos + offset));
                __m128i cmp = _mm_cmpeq_epi8(pattern_chunk, text_chunk);
                
                if (_mm_movemask_epi8(cmp) != 0xFFFF) {
                    match = false;
                }
                #else
                if (memcmp(pattern + offset, text_pos + offset, 16) != 0) {
                    match = false;
                }
                #endif
            }
            
            // Check remainder bytes
            if (match && remainder > 0) {
                if (memcmp(pattern, text_pos, remainder) != 0) {
                    match = false;
                }
            }
            
            if (match) {
                return (int)shift;  // Match found
            }
            
            // Calculate shift using bad character heuristic
            // Use the rightmost character that didn't match
            unsigned char bad_char = (unsigned char)text[shift + pattern_len - 1];
            int bad_char_shift = (int)pattern_len - 1 - bm->bad_char_table[bad_char];
            
            // Use good suffix table for better shift
            int good_suffix_shift = bm->good_suffix_table[pattern_len - 1];
            
            shift += (bad_char_shift > good_suffix_shift) ? bad_char_shift : good_suffix_shift;
            if (shift == 0) shift = 1;  // Ensure progress
            
        } else {
            // Original Boyer-Moore for shorter patterns
            int j = (int)pattern_len - 1;
            
            // Compare from right to left
            while (j >= 0 && pattern[j] == text[shift + j]) {
                j--;
            }
            
            if (j < 0) {
                return (int)shift;  // Match found
            } else {
                // Calculate shift using bad character and good suffix heuristics
                int bad_char_shift = j - bm->bad_char_table[(unsigned char)text[shift + j]];
                int good_suffix_shift = bm->good_suffix_table[j];
                
                shift += (bad_char_shift > good_suffix_shift) ? bad_char_shift : good_suffix_shift;
                if (shift == 0) shift = 1;  // Ensure progress
            }
        }
    }
    
    return -1;  // No match found
}

// === SIMD UTILITIES ===

#ifdef USE_SIMD
void mercury_check_thresholds_simd(const MercuryMetrics* metrics, size_t count,
                                  const double* thresholds, uint64_t* violations) {
    // SIMD implementation for x86_64
    #ifdef MERCURY_X86_64
        // Process 4 metrics at a time using AVX
        size_t simd_count = count & ~3;  // Round down to multiple of 4
        
        for (size_t i = 0; i < simd_count; i += 4) {
            // Load thresholds
            __m256d threshold_vec = _mm256_load_pd(&thresholds[i]);
            
            // Compare with metrics (example for one field)
            // This would be expanded for all threshold types
            __m256d response_times = _mm256_set_pd(
                mercury_ns_to_ms(metrics[i+3].end_time.nanoseconds - metrics[i+3].start_time.nanoseconds),
                mercury_ns_to_ms(metrics[i+2].end_time.nanoseconds - metrics[i+2].start_time.nanoseconds),
                mercury_ns_to_ms(metrics[i+1].end_time.nanoseconds - metrics[i+1].start_time.nanoseconds),
                mercury_ns_to_ms(metrics[i].end_time.nanoseconds - metrics[i].start_time.nanoseconds)
            );
            
            __m256d comparison = _mm256_cmp_pd(response_times, threshold_vec, _CMP_GT_OQ);
            int mask = _mm256_movemask_pd(comparison);
            
            // Set violation flags based on comparison
            for (int j = 0; j < 4; j++) {
                if (mask & (1 << j)) {
                    violations[i + j] |= 1;  // Response time violation
                }
            }
        }
        
        // Handle remaining metrics
        for (size_t i = simd_count; i < count; i++) {
            double response_time = mercury_ns_to_ms(metrics[i].end_time.nanoseconds - metrics[i].start_time.nanoseconds);
            if (response_time > thresholds[i]) {
                violations[i] |= 1;
            }
        }
    #else
        // Fallback to scalar implementation
        for (size_t i = 0; i < count; i++) {
            double response_time = mercury_ns_to_ms(metrics[i].end_time.nanoseconds - metrics[i].start_time.nanoseconds);
            if (response_time > thresholds[i]) {
                violations[i] |= 1;
            }
        }
    #endif
}
#endif

// === ERROR HANDLING ===

const MercuryErrorContext* mercury_get_last_error(void) {
    return &mercury_last_error;
}

void mercury_clear_error(void) {
    mercury_last_error.code = MERCURY_SUCCESS;
    mercury_last_error.message[0] = '\0';
    mercury_last_error.function = NULL;
    mercury_last_error.file = NULL;
    mercury_last_error.line = 0;
}

// === LOGGING ===

void mercury_default_logger(MercuryLogLevel level, const char* format, ...) {
    const char* level_strings[] = {"DEBUG", "INFO", "WARN", "ERROR"};
    
    FILE* output = (level >= MERCURY_LOG_WARN) ? stderr : stdout;
    
    fprintf(output, "[MERCURY %s] ", level_strings[level]);
    
    va_list args;
    va_start(args, format);
    vfprintf(output, format, args);
    va_end(args);
    
    fprintf(output, "\n");
    fflush(output);
}

// === INITIALIZATION ===

MercuryError mercury_init(void) {
    MERCURY_INFO("Initializing Mercury Performance Testing Framework");
    
    // Initialize RDTSC calibration
    #ifdef MERCURY_X86_64
    mercury_calibrate_rdtsc();
    #endif
    
    // Clear error state
    mercury_clear_error();
    
    MERCURY_INFO("Mercury initialization complete");
    return MERCURY_SUCCESS;
}

void mercury_cleanup(void) {
    MERCURY_INFO("Cleaning up Mercury Performance Testing Framework");
    mercury_clear_error();
}

// === MEMORY POOL IMPLEMENTATION ===

// Memory pool types now in common.h

void memory_pool_init(memory_pool_t* pool, size_t block_size, size_t num_blocks) {
    if (MERCURY_UNLIKELY(!pool)) return;
    
    pool->block_size = block_size;
    pool->num_blocks = num_blocks;
    
    // Initialize atomic variables
    atomic_store_explicit(&pool->free_stack, NULL, memory_order_relaxed);
    atomic_store_explicit(&pool->free_count, 0, memory_order_relaxed);
    
    // Pre-allocate all blocks in a contiguous array for better cache locality
    pool->all_blocks = mercury_aligned_alloc(sizeof(memory_block_t) * num_blocks, 64);
    if (!pool->all_blocks) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate block array");
        return;
    }
    
    // Initialize all blocks and build the lock-free stack
    memory_block_t* stack_head = NULL;
    for (size_t i = 0; i < num_blocks; i++) {
        memory_block_t* block = &pool->all_blocks[i];
        
        block->size = block_size;
        block->data = mercury_aligned_alloc(block_size, 64);  // 64-byte aligned
        if (!block->data) {
            // Skip this block on allocation failure
            continue;
        }
        
        block->in_use = false;
        // Build stack in reverse order for better locality
        block->next = stack_head;
        stack_head = block;
    }
    
    // Set the initial stack head atomically
    atomic_store_explicit(&pool->free_stack, stack_head, memory_order_release);
    
    // Count actual allocated blocks
    size_t count = 0;
    memory_block_t* current = stack_head;
    while (current) {
        count++;
        current = current->next;
    }
    atomic_store_explicit(&pool->free_count, count, memory_order_relaxed);
}

void* memory_pool_alloc(memory_pool_t* pool) {
    if (MERCURY_UNLIKELY(!pool)) return NULL;
    
    // Lock-free atomic stack pop operation
    memory_block_t* head;
    memory_block_t* next;
    
    do {
        // Load current head with acquire ordering
        head = atomic_load_explicit(&pool->free_stack, memory_order_acquire);
        
        // Check if stack is empty
        if (MERCURY_UNLIKELY(head == NULL)) {
            return NULL;  // Pool exhausted
        }
        
        // Prefetch the head block for reading its fields
        MERCURY_PREFETCH_READ(head);
        
        // Get the next block in the stack  
        next = head->next;
        
        // Prefetch the next block in case CAS fails and we need to retry
        if (MERCURY_LIKELY(next != NULL)) {
            MERCURY_PREFETCH_READ_LOW(next);
        }
        
        // Try to update the head atomically (CAS operation)
        // This will fail if another thread modified the head
    } while (!atomic_compare_exchange_weak_explicit(
        &pool->free_stack, &head, next,
        memory_order_acq_rel, memory_order_acquire));
    
    // Successfully popped a block from the stack
    head->in_use = true;
    head->next = NULL;  // Clear the next pointer for safety
    
    // Prefetch the actual data block for the caller
    MERCURY_PREFETCH_WRITE(head->data);
    
    // Update statistics (relaxed ordering for performance)
    atomic_fetch_sub_explicit(&pool->free_count, 1, memory_order_relaxed);
    
    return head->data;
}

void memory_pool_free(memory_pool_t* pool, void* ptr) {
    if (MERCURY_UNLIKELY(!pool || !ptr)) return;
    
    // Find the block that contains this pointer
    // Since we allocated all blocks contiguously, we can search through them
    memory_block_t* target_block = NULL;
    for (size_t i = 0; i < pool->num_blocks; i++) {
        if (pool->all_blocks[i].data == ptr && pool->all_blocks[i].in_use) {
            target_block = &pool->all_blocks[i];
            break;
        }
    }
    
    if (MERCURY_UNLIKELY(!target_block)) {
        // Invalid pointer or already freed
        return;
    }
    
    // Mark as not in use
    target_block->in_use = false;
    
    // Lock-free atomic stack push operation
    memory_block_t* current_head;
    do {
        // Load current head with acquire ordering
        current_head = atomic_load_explicit(&pool->free_stack, memory_order_acquire);
        
        // Set this block's next to point to current head
        target_block->next = current_head;
        
        // Try to update the head atomically (CAS operation)
        // This will fail if another thread modified the head
    } while (!atomic_compare_exchange_weak_explicit(
        &pool->free_stack, &current_head, target_block,
        memory_order_acq_rel, memory_order_acquire));
    
    // Successfully pushed the block back onto the free stack
    // Update statistics (relaxed ordering for performance)
    atomic_fetch_add_explicit(&pool->free_count, 1, memory_order_relaxed);
}

void memory_pool_destroy(memory_pool_t* pool) {
    if (!pool || !pool->all_blocks) return;
    
    // Free all allocated block data
    for (size_t i = 0; i < pool->num_blocks; i++) {
        if (pool->all_blocks[i].data) {
            mercury_aligned_free(pool->all_blocks[i].data);
            pool->all_blocks[i].data = NULL;
        }
    }
    
    // Free the block array
    mercury_aligned_free(pool->all_blocks);
    pool->all_blocks = NULL;
    
    // Reset atomic variables
    atomic_store_explicit(&pool->free_stack, NULL, memory_order_relaxed);
    atomic_store_explicit(&pool->free_count, 0, memory_order_relaxed);
    
    pool->block_size = 0;
    pool->num_blocks = 0;
}

// === ERROR CHAIN IMPLEMENTATION ===

// Error chain types now in common.h

void error_chain_init(error_chain_t* chain) {
    if (!chain) return;
    
    chain->head = NULL;
    chain->count = 0;
}

void error_chain_add(error_chain_t* chain, int code, const char* format, ...) {
    if (!chain || !format) return;
    
    error_node_t* node = malloc(sizeof(error_node_t));
    if (!node) return;
    
    node->code = code;
    
    va_list args;
    va_start(args, format);
    vsnprintf(node->message, sizeof(node->message), format, args);
    va_end(args);
    
    // Add to head (LIFO)
    node->next = chain->head;
    chain->head = node;
    chain->count++;
}

void error_chain_destroy(error_chain_t* chain) {
    if (!chain) return;
    
    error_node_t* node = chain->head;
    while (node) {
        error_node_t* next = node->next;
        free(node);
        node = next;
    }
    
    chain->head = NULL;
    chain->count = 0;
}

// === SIMD OPTIMIZED OPERATIONS ===

#ifdef USE_SIMD
void mercury_memcpy_simd(void* dest, const void* src, size_t size) {
    if (MERCURY_UNLIKELY(!dest || !src || size == 0)) {
        return;
    }
    
    char* d = (char*)dest;
    const char* s = (const char*)src;
    
    // For small sizes, use regular memcpy
    if (MERCURY_UNLIKELY(size < 32)) {
        memcpy(dest, src, size);
        return;
    }
    
    // AVX2 implementation for 256-bit (32-byte) chunks
    size_t avx_chunks = size / 32;
    size_t remainder = size % 32;
    
    for (size_t i = 0; i < avx_chunks; i++) {
        __m256i data = _mm256_loadu_si256((const __m256i*)(s + i * 32));
        _mm256_storeu_si256((__m256i*)(d + i * 32), data);
    }
    
    // Handle remainder with regular memcpy
    if (remainder > 0) {
        memcpy(d + avx_chunks * 32, s + avx_chunks * 32, remainder);
    }
}

// SIMD-accelerated string search (Boyer-Moore style)
int mercury_string_search_simd(const char* text, size_t text_len, const char* pattern, size_t pattern_len) {
    if (!text || !pattern || pattern_len == 0 || text_len < pattern_len) {
        return -1;
    }
    
    // For small patterns, use regular strstr
    if (pattern_len < 4) {
        const char* found = strstr(text, pattern);
        return found ? (int)(found - text) : -1;
    }
    
    // Use SIMD for searching the first character of pattern
    const char first_char = pattern[0];
    const __m256i first_chars = _mm256_set1_epi8(first_char);
    
    size_t max_pos = text_len - pattern_len;
    size_t pos = 0;
    
    // SIMD scan for potential matches
    while (pos <= max_pos) {
        if (pos + 32 <= text_len) {
            // Prefetch next chunk for sequential scanning
            if (pos + 64 <= text_len) {
                MERCURY_PREFETCH_READ_LOW(text + pos + 64);
            }
            
            // Load 32 characters from text
            __m256i text_chunk = _mm256_loadu_si256((const __m256i*)(text + pos));
            
            // Compare with first character
            __m256i matches = _mm256_cmpeq_epi8(text_chunk, first_chars);
            uint32_t match_mask = _mm256_movemask_epi8(matches);
            
            // Check each potential match
            while (match_mask != 0) {
                int bit_pos = __builtin_ctz(match_mask);  // Count trailing zeros
                size_t match_pos = pos + bit_pos;
                
                if (match_pos <= max_pos) {
                    // Prefetch the potential match location
                    MERCURY_PREFETCH_READ(text + match_pos);
                    
                    // Verify full pattern match
                    if (memcmp(text + match_pos, pattern, pattern_len) == 0) {
                        return (int)match_pos;
                    }
                }
                
                match_mask &= (match_mask - 1);  // Clear lowest set bit
            }
            
            pos += 32;
        } else {
            // Handle remainder with regular search
            const char* found = strstr(text + pos, pattern);
            return found ? (int)(found - text) : -1;
        }
    }
    
    return -1;  // Not found
}

// === MULTI-PATTERN SIMD SEARCH IMPLEMENTATION ===

MercuryMultiPatternSearch* mercury_multi_pattern_create(const char* patterns[], size_t count) {
    if (!patterns || count == 0 || count > MERCURY_MAX_PATTERNS) {
        MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Invalid patterns or count");
        return NULL;
    }
    
    MercuryMultiPatternSearch* mps = mercury_aligned_alloc(sizeof(MercuryMultiPatternSearch), 64);
    if (!mps) {
        MERCURY_SET_ERROR(MERCURY_ERROR_OUT_OF_MEMORY, "Failed to allocate multi-pattern search");
        return NULL;
    }
    
    // Initialize structure
    memset(mps, 0, sizeof(MercuryMultiPatternSearch));
    mps->pattern_count = count;
    
    // Copy patterns and build lookup tables
    for (size_t i = 0; i < count; i++) {
        if (!patterns[i]) {
            mercury_aligned_free(mps);
            MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "NULL pattern in array");
            return NULL;
        }
        
        size_t len = strlen(patterns[i]);
        if (len == 0 || len >= MERCURY_MAX_PATTERN_LENGTH) {
            mercury_aligned_free(mps);
            MERCURY_SET_ERROR(MERCURY_ERROR_INVALID_ARGUMENT, "Pattern length out of range");
            return NULL;
        }
        
        // Copy pattern
        strcpy(mps->patterns[i], patterns[i]);
        mps->pattern_lengths[i] = len;
        mps->first_chars[i] = (uint8_t)patterns[i][0];
        
        // Update first character lookup table
        uint8_t first_char = (uint8_t)patterns[i][0];
        mps->pattern_masks[first_char] |= (1U << i);
    }
    
    return mps;
}

void mercury_multi_pattern_destroy(MercuryMultiPatternSearch* mps) {
    if (mps) {
        mercury_aligned_free(mps);
    }
}

int mercury_multi_pattern_search_simd(const MercuryMultiPatternSearch* mps, const char* text, 
                                     size_t text_len, int* pattern_id) {
    if (!mps || !text || !pattern_id || text_len == 0) {
        return -1;
    }
    
    *pattern_id = -1;
    
    // Smart multi-pattern search using optimized strstr
    // Find the leftmost match across all patterns
    int best_position = -1;
    int best_pattern = -1;
    
    // Use highly optimized strstr for each pattern
    for (size_t p = 0; p < mps->pattern_count; p++) {
        const char* found = strstr(text, mps->patterns[p]);
        
        if (found) {
            int pos = (int)(found - text);
            if (best_position == -1 || pos < best_position) {
                best_position = pos;
                best_pattern = (int)p;
            }
        }
    }
    
    if (best_position >= 0) {
        *pattern_id = best_pattern;
        return best_position;
    }
    
    return -1;  // No patterns found
}

#else
// Fallback implementations when SIMD is not available
void mercury_memcpy_simd(void* dest, const void* src, size_t size) {
    memcpy(dest, src, size);
}

int mercury_string_search_simd(const char* text, size_t text_len, const char* pattern, size_t pattern_len) {
    const char* found = strstr(text, pattern);
    return found ? (int)(found - text) : -1;
}

// Multi-pattern search fallback implementation
MercuryMultiPatternSearch* mercury_multi_pattern_create(const char* patterns[], size_t count) {
    if (!patterns || count == 0 || count > MERCURY_MAX_PATTERNS) {
        return NULL;
    }
    
    MercuryMultiPatternSearch* mps = malloc(sizeof(MercuryMultiPatternSearch));
    if (!mps) return NULL;
    
    memset(mps, 0, sizeof(MercuryMultiPatternSearch));
    mps->pattern_count = count;
    
    for (size_t i = 0; i < count; i++) {
        if (!patterns[i]) {
            free(mps);
            return NULL;
        }
        
        size_t len = strlen(patterns[i]);
        if (len == 0 || len >= MERCURY_MAX_PATTERN_LENGTH) {
            free(mps);
            return NULL;
        }
        
        strcpy(mps->patterns[i], patterns[i]);
        mps->pattern_lengths[i] = len;
        mps->first_chars[i] = (uint8_t)patterns[i][0];
        
        uint8_t first_char = (uint8_t)patterns[i][0];
        mps->pattern_masks[first_char] |= (1U << i);
    }
    
    return mps;
}

void mercury_multi_pattern_destroy(MercuryMultiPatternSearch* mps) {
    if (mps) {
        free(mps);
    }
}

int mercury_multi_pattern_search_simd(const MercuryMultiPatternSearch* mps, const char* text, 
                                     size_t text_len, int* pattern_id) {
    if (!mps || !text || !pattern_id || text_len == 0) {
        return -1;
    }
    
    *pattern_id = -1;
    
    // Fallback using optimized strstr
    int best_position = -1;
    int best_pattern = -1;
    
    for (size_t p = 0; p < mps->pattern_count; p++) {
        const char* found = strstr(text, mps->patterns[p]);
        
        if (found) {
            int pos = (int)(found - text);
            if (best_position == -1 || pos < best_position) {
                best_position = pos;
                best_pattern = (int)p;
            }
        }
    }
    
    if (best_position >= 0) {
        *pattern_id = best_pattern;
        return best_position;
    }
    
    return -1;  // No patterns found
}
#endif