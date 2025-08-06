/*
 * GLIBC Compatibility Wrappers for manylinux2014
 * 
 * This file provides wrapper functions that force the use of older GLIBC
 * symbol versions to ensure manylinux2014 compatibility.
 */

#ifdef __linux__

#include <string.h>
#include <stddef.h>

/* Force the use of GLIBC 2.2.5 symbols */
__asm__(".symver __memcpy_glibc_2_2_5, memcpy@GLIBC_2.2.5");
__asm__(".symver __memmove_glibc_2_2_5, memmove@GLIBC_2.2.5");
__asm__(".symver __memset_glibc_2_2_5, memset@GLIBC_2.2.5");
__asm__(".symver __memcmp_glibc_2_2_5, memcmp@GLIBC_2.2.5");

/* External declarations for the GLIBC 2.2.5 versions */
extern void *__memcpy_glibc_2_2_5(void *dest, const void *src, size_t n);
extern void *__memmove_glibc_2_2_5(void *dest, const void *src, size_t n);
extern void *__memset_glibc_2_2_5(void *s, int c, size_t n);
extern int __memcmp_glibc_2_2_5(const void *s1, const void *s2, size_t n);

/* Wrapper functions that will be used instead of the default ones */
void *__wrap_memcpy(void *dest, const void *src, size_t n) {
    return __memcpy_glibc_2_2_5(dest, src, n);
}

void *__wrap_memmove(void *dest, const void *src, size_t n) {
    return __memmove_glibc_2_2_5(dest, src, n);
}

void *__wrap_memset(void *s, int c, size_t n) {
    return __memset_glibc_2_2_5(s, c, n);
}

int __wrap_memcmp(const void *s1, const void *s2, size_t n) {
    return __memcmp_glibc_2_2_5(s1, s2, n);
}

#endif /* __linux__ */