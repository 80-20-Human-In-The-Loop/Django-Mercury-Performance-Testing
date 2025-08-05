# Windows C Extension Support for Django Mercury

Eventually this will be moved to the wiki to be maintained by the community, but for now I am working on it.

## Overview

Django Mercury now supports C extensions on Windows, eliminating the 900x performance penalty of pure Python mode. This document explains how Windows support was implemented following the 80-20 Human in the Loop philosophy.

## The Problem

Without C extensions on Windows:
- **900x slower performance** compared to Linux/macOS
- Pure Python fallback worked but was painfully slow
- Windows developers couldn't use the full performance capabilities

## The Solution

### 1. Windows Compatibility Layer (`windows_compat.h`)

Created a compatibility header that maps POSIX functions to Windows equivalents:

```c
// Thread compatibility
typedef HANDLE pthread_t;
typedef CRITICAL_SECTION pthread_mutex_t;
typedef DWORD pthread_key_t;

// Maps pthread_create to CreateThread
static inline int pthread_create(pthread_t *thread, void *attr, 
                                void *(*start_routine)(void*), void *arg) {
    *thread = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)start_routine, arg, 0, NULL);
    return (*thread == NULL) ? -1 : 0;
}
```

### 2. Export Macros for DLL Symbols

All public functions now use `MERCURY_API` macro:

```c
// On Windows: __declspec(dllexport)
// On Unix: (empty)
MERCURY_API void* mercury_aligned_alloc(size_t size, size_t alignment);
```

### 3. Build System Updates

#### Makefile Changes
- Detect Windows platforms (Windows_NT, MinGW, MSYS)
- Use `.dll` extension instead of `.so`
- Support MSVC compiler flags

#### setup.py Changes
- Windows-specific compile flags
- Link Windows system libraries (kernel32, user32, advapi32)
- Define `BUILDING_MERCURY_DLL` for proper exports

### 4. Python Loader Updates

The loader now handles Windows DLL loading:

```python
if sys.platform == 'win32':
    import os
    # Add package directory to DLL search path
    package_dir = os.path.dirname(os.path.dirname(__file__))
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(package_dir)
```

### 5. CI/CD Integration

#### cibuildwheel Configuration
```toml
[tool.cibuildwheel.windows]
archs = ["AMD64"]
environment = {DJANGO_MERCURY_SUPPRESS_WARNING="1", DJANGO_MERCURY_PURE_PYTHON="0"}
repair-wheel-command = "delvewheel repair -w {dest_dir} {wheel}"
```

#### GitHub Actions Updates
- Install Visual Studio Build Tools
- Test C extension loading before running tests
- Use delvewheel to bundle dependencies

## Testing Windows C Extensions

### Local Testing

```bash
# Build C extensions
cd django_mercury/c_core
make  # or use Visual Studio

# Test loading
python test_windows_dll.py
```

### CI Testing

The GitHub Actions workflow automatically:
1. Builds C extensions with cibuildwheel
2. Tests DLL loading with `test_windows_dll.py`
3. Falls back to pure Python if needed

## Performance Impact

With C extensions enabled on Windows:
- **900x faster** than pure Python mode
- Performance parity with Linux/macOS
- All optimizations available

## Troubleshooting

### Common Issues

1. **"DLL load failed"**
   - Ensure Visual C++ Redistributables are installed
   - Check that all dependencies are in PATH

2. **"Unresolved external symbol"**
   - Verify all functions use `MERCURY_API` macro
   - Check that setup.py links required libraries

3. **"C extensions not available"**
   - Install Visual Studio Build Tools
   - Set `DJANGO_MERCURY_PURE_PYTHON=0`

### Debug Commands

```powershell
# Check if DLLs are built
dir django_mercury\*.dll

# Test import
python -c "import django_mercury._c_metrics"

# Check dependencies
dumpbin /dependents django_mercury\_c_metrics.pyd
```

## 80-20 Philosophy Applied

### 80% Automated
- Automatic DLL building with cibuildwheel
- Automatic fallback to pure Python
- Automatic dependency bundling
- CI/CD handles all platforms

### 20% Human Control
- Developers choose when to use C extensions
- Control over Visual Studio version
- Debugging and optimization decisions
- Security review of native code

## Future Improvements

1. **ARM64 Windows Support**
   - Add ARM64 target to cibuildwheel
   - Test on Windows ARM devices

2. **Better Error Messages**
   - Clearer messages when DLLs fail to load
   - Diagnostic tool for dependency issues

3. **Performance Profiling**
   - Windows-specific performance tools
   - Integration with Windows Performance Toolkit

## Conclusion

Windows C extension support brings Django Mercury to performance parity across all platforms. The implementation follows Windows best practices while maintaining the simplicity of the 80-20 philosophy.

**Key Achievement**: Windows users now get the same 900x performance boost as Linux/macOS users, making Django Mercury truly cross-platform.

---

*Built with the 80-20 Human in the Loop philosophy - high performance for everyone, regardless of operating system.*