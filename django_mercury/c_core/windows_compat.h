/**
 * @file windows_compat.h
 * @brief Windows compatibility layer for POSIX functions
 * 
 * This header provides Windows equivalents for POSIX functions used
 * throughout the Mercury Performance Testing Framework.
 */

#ifndef MERCURY_WINDOWS_COMPAT_H
#define MERCURY_WINDOWS_COMPAT_H

#ifdef _WIN32

#include <winsock2.h>  // For struct timeval
#include <windows.h>
#include <process.h>
#include <stdint.h>
#include <time.h>

// Thread compatibility
typedef HANDLE pthread_t;
typedef CRITICAL_SECTION pthread_mutex_t;
typedef DWORD pthread_key_t;
typedef INIT_ONCE pthread_once_t;

#define PTHREAD_ONCE_INIT INIT_ONCE_STATIC_INIT
#define PTHREAD_MUTEX_INITIALIZER {0}

// Thread function prototypes
static inline int pthread_create(pthread_t *thread, void *attr, 
                                void *(*start_routine)(void*), void *arg) {
    (void)attr; // Unused
    *thread = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)start_routine, arg, 0, NULL);
    return (*thread == NULL) ? -1 : 0;
}

static inline int pthread_join(pthread_t thread, void **retval) {
    (void)retval; // Unused
    WaitForSingleObject(thread, INFINITE);
    CloseHandle(thread);
    return 0;
}

// Mutex functions
static inline int pthread_mutex_init(pthread_mutex_t *mutex, void *attr) {
    (void)attr; // Unused
    InitializeCriticalSection(mutex);
    return 0;
}

static inline int pthread_mutex_destroy(pthread_mutex_t *mutex) {
    DeleteCriticalSection(mutex);
    return 0;
}

static inline int pthread_mutex_lock(pthread_mutex_t *mutex) {
    EnterCriticalSection(mutex);
    return 0;
}

static inline int pthread_mutex_unlock(pthread_mutex_t *mutex) {
    LeaveCriticalSection(mutex);
    return 0;
}

// Thread-local storage
static inline int pthread_key_create(pthread_key_t *key, void (*destructor)(void*)) {
    (void)destructor; // Not supported on Windows TLS
    *key = TlsAlloc();
    return (*key == TLS_OUT_OF_INDEXES) ? -1 : 0;
}

static inline int pthread_key_delete(pthread_key_t key) {
    return TlsFree(key) ? 0 : -1;
}

static inline void *pthread_getspecific(pthread_key_t key) {
    return TlsGetValue(key);
}

static inline int pthread_setspecific(pthread_key_t key, const void *value) {
    return TlsSetValue(key, (LPVOID)value) ? 0 : -1;
}

// Once initialization
typedef struct {
    void (*func)(void);
} pthread_once_func_wrapper;

static BOOL CALLBACK pthread_once_callback(PINIT_ONCE InitOnce, PVOID Parameter, PVOID *lpContext) {
    (void)InitOnce;
    (void)lpContext;
    pthread_once_func_wrapper *wrapper = (pthread_once_func_wrapper*)Parameter;
    wrapper->func();
    return TRUE;
}

static inline int pthread_once(pthread_once_t *once_control, void (*init_routine)(void)) {
    pthread_once_func_wrapper wrapper = {init_routine};
    InitOnceExecuteOnce(once_control, pthread_once_callback, &wrapper, NULL);
    return 0;
}

// Time functions
static inline void clock_gettime_monotonic(struct timespec *ts) {
    LARGE_INTEGER frequency, counter;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&counter);
    
    ts->tv_sec = (time_t)(counter.QuadPart / frequency.QuadPart);
    ts->tv_nsec = (long)(((counter.QuadPart % frequency.QuadPart) * 1000000000) / frequency.QuadPart);
}

#define CLOCK_MONOTONIC 1
static inline int clock_gettime(int clk_id, struct timespec *ts) {
    (void)clk_id; // Always use monotonic on Windows
    clock_gettime_monotonic(ts);
    return 0;
}

// Memory functions
static inline void explicit_bzero(void *s, size_t n) {
    SecureZeroMemory(s, n);
}

// Sleep function
static inline unsigned int sleep(unsigned int seconds) {
    Sleep(seconds * 1000);
    return 0;
}

static inline int usleep(unsigned int microseconds) {
    Sleep(microseconds / 1000);
    return 0;
}

// Time structures and functions

// Windows implementation of gettimeofday
static inline int gettimeofday(struct timeval *tv, void *tz) {
    FILETIME ft;
    ULARGE_INTEGER epoch;
    
    (void)tz; /* Unused parameter */
    
    GetSystemTimeAsFileTime(&ft);
    epoch.LowPart = ft.dwLowDateTime;
    epoch.HighPart = ft.dwHighDateTime;
    
    /* Convert to microseconds since Unix epoch (1970-01-01) */
    epoch.QuadPart = epoch.QuadPart / 10 - 11644473600000000LL;
    
    tv->tv_sec = (long)(epoch.QuadPart / 1000000);
    tv->tv_usec = (long)(epoch.QuadPart % 1000000);
    
    return 0;
}

// Export macros
#define MERCURY_API __declspec(dllexport)

#else
// Non-Windows platforms
#define MERCURY_API

#endif // _WIN32

#endif // MERCURY_WINDOWS_COMPAT_H