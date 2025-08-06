/*
 * GLIBC Compatibility Layer for manylinux2014
 * 
 * This file forces the use of older GLIBC symbol versions to ensure
 * compatibility with manylinux2014 (GLIBC 2.17).
 * 
 * Background: GCC may optimize string operations (strlen, strcpy, etc.) 
 * by replacing them with memcpy calls. In newer GLIBC versions (2.33+),
 * these memcpy calls reference newer symbol versions that aren't available
 * on older systems, breaking manylinux2014 compatibility.
 * 
 * Solution: Use the .symver directive to force the linker to use
 * GLIBC_2.2.5 versions of these functions, which are available
 * in all GLIBC versions since 2.2.5.
 */

#ifdef __linux__
#ifdef __x86_64__
/* Force older GLIBC symbol versions for manylinux2014 compatibility */
__asm__(".symver memcpy,memcpy@GLIBC_2.2.5");
__asm__(".symver memmove,memmove@GLIBC_2.2.5");
__asm__(".symver memset,memset@GLIBC_2.2.5");
__asm__(".symver memcmp,memcmp@GLIBC_2.2.5");

/* Additional symbols that might be used */
__asm__(".symver strlen,strlen@GLIBC_2.2.5");
__asm__(".symver strcpy,strcpy@GLIBC_2.2.5");
__asm__(".symver strncpy,strncpy@GLIBC_2.2.5");
__asm__(".symver strcat,strcat@GLIBC_2.2.5");
__asm__(".symver strncat,strncat@GLIBC_2.2.5");
#endif /* __x86_64__ */
#endif /* __linux__ */

/* Empty function to ensure this file generates an object file */
void django_mercury_glibc_compat_dummy(void) {
    /* This function exists only to ensure the file is not empty */
}