# 🔧 Multi-Platform C Extension Deployment: The Hard-Won Lessons

> **A technical guide for deploying Python libraries with C extensions across Windows, macOS, and Linux**

## Table of Contents

- [The Architecture: Why It's Complex](#the-architecture-why-its-complex)
- [Platform-Specific Loading Strategies](#platform-specific-loading-strategies)
- [The Build System Duality](#the-build-system-duality)
- [Critical Lessons Learned](#critical-lessons-learned)
- [CI/CD Pipeline Architecture](#cicd-pipeline-architecture)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Reusable Patterns](#reusable-patterns-for-future-projects)

---

## The Architecture: Why It's Complex

Building Python libraries with C extensions that work across all platforms is surprisingly difficult. Here's what we're dealing with:

### The File Extension Matrix

| Platform | C Library | Python Extension | ctypes loads | importlib loads |
|----------|-----------|------------------|--------------|-----------------|
| Linux    | `.so`     | `.so`            | ✅ Yes       | ✅ Yes          |
| macOS    | `.so`*    | `.so`            | ✅ Yes       | ✅ Yes          |
| Windows  | `.dll`    | `.pyd`           | ✅ `.dll` only | ✅ `.pyd` only |

*Note: macOS traditionally uses `.dylib` but `.so` works fine and simplifies cross-platform builds

### The Dual Loading Problem

```python
# On Unix (Linux/macOS):
lib = ctypes.CDLL('./libquery_analyzer.so')  # Works for standalone libraries

# On Windows:
lib = ctypes.CDLL('./query_analyzer.dll')    # Works for DLLs
# BUT .pyd files are Python extensions, NOT raw DLLs
import _c_analyzer  # Must import .pyd files as modules
```

**Key Insight**: Windows `.pyd` files are Python extension modules that happen to be DLLs internally, but they MUST be imported as Python modules, not loaded with ctypes.

---

## Platform-Specific Loading Strategies

### The Solution: Dual Loading Strategy

```python
# c_bindings.py - The working solution
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    # Windows: Import Python extensions
    try:
        import django_mercury._c_analyzer as module
        # Extract the raw function pointers from the module
        self.query_analyzer = module
    except ImportError:
        self.query_analyzer = None
else:
    # Unix: Load shared libraries with ctypes
    try:
        lib_path = find_library('libquery_analyzer')
        self.query_analyzer = ctypes.CDLL(lib_path)
    except OSError:
        self.query_analyzer = None
```

### Platform Detection Pitfalls

```python
# WRONG - Don't check file extensions:
if library_path.suffix == '.pyd':
    # This breaks because .pyd might not exist yet

# RIGHT - Check platform:
if platform.system() == 'Windows':
    # Windows-specific logic
```

---

## The Build System Duality

We need TWO different build systems because:

1. **Makefile**: Builds standalone `.so` libraries for ctypes on Unix
2. **setup.py**: Builds Python extensions for all platforms

### Why Both?

```bash
# Unix developers want simple libraries:
cd django_mercury/c_core && make
# Produces: libquery_analyzer.so (standalone, ctypes-loadable)

# pip/wheel installation needs Python extensions:
python setup.py build_ext
# Produces: _c_analyzer.cpython-310-x86_64-linux-gnu.so (Python module)
```

### The setup.py Pitfalls

#### ❌ Absolute Path Error
```python
# WRONG - Causes "absolute path" error
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sources=[os.path.join(BASE_DIR, 'django_mercury/c_core/common.c')]
```

#### ✅ Relative Path Solution
```python
# RIGHT - Use relative paths
sources=['django_mercury/c_core/common.c']
```

#### ❌ Missing Package Info
```python
# WRONG - Too minimal, cibuildwheel fails
setup(
    ext_modules=get_c_extensions(),
)
```

#### ✅ Include Package Discovery
```python
# RIGHT - Include packages for backward compatibility
setup(
    packages=find_packages(exclude=['tests*']),
    package_data={...},
    ext_modules=get_c_extensions(),
)
```

---

## Critical Lessons Learned

### Lesson 1: The CIBUILDWHEEL Environment Variable

**The Problem**: Your setup.py checks for `CIBUILDWHEEL` to avoid linking libunwind, but pyproject.toml doesn't set it!

```python
# setup.py
if os.environ.get('CIBUILDWHEEL', '0') != '1':
    libraries.append('unwind')  # Not manylinux compliant!
```

**The Fix**:
```toml
# pyproject.toml
[tool.cibuildwheel]
environment = {CIBUILDWHEEL="1", ...}  # MUST set this!
```

### Lesson 2: macOS .dylib vs .so

**The Problem**: Code expects `.dylib` on macOS but Makefile builds `.so`

```python
# WRONG
PLATFORM_EXTENSIONS = {
    "Darwin": ".dylib",  # macOS doesn't actually need .dylib
}
```

**The Fix**:
```python
# RIGHT - Use .so everywhere for simplicity
PLATFORM_EXTENSIONS = {
    "Darwin": ".so",  # Works fine on macOS
}
```

### Lesson 3: Windows Mock Testing

**The Problem**: Can't mock ctypes.CDLL on Windows when using importlib

```python
# Unix tests mock ctypes.CDLL
@patch('django_mercury.python_bindings.c_bindings.ctypes.CDLL')
def test_something(mock_cdll):
    # This doesn't work on Windows!
```

**The Solution**:
```python
IS_WINDOWS = platform.system() == "Windows"

@unittest.skipIf(IS_WINDOWS, "Unix-specific test")
class TestUnixLoading(TestCase):
    # Unix-only tests

class TestWindowsLoading(TestCase):
    @unittest.skipUnless(IS_WINDOWS, "Windows-specific test")
    def test_pyd_loading(self):
        # Windows-only tests
```

### Lesson 4: CI vs User Machine Fallbacks

**Design Decision**: C extensions MUST work in CI but CAN fallback for users

```yaml
# CI script - FAIL if C extensions don't build
if ! make ci; then
    echo "❌ ERROR: C library build failed!"
    exit 1  # FAIL the CI
fi

# User installation - graceful fallback
try:
    import _c_analyzer
except ImportError:
    logger.warning("C extensions not available, using pure Python")
    # Continue with fallback
```

---

## CI/CD Pipeline Architecture

### The Multi-Stage Pipeline

```
┌──────────────────────────────────────────────────────────┐
│                    Trigger Events                         │
│  • Push to main                                          │
│  • Version tags (v*)                                     │
│  • Manual workflow_dispatch                              │
└────────────────────────┬─────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────┐                ┌──────────────┐
│    Tests     │                │ Build Wheels │
│ (3 OS × 3 Py)│                │   (9 jobs)   │
│              │                │              │
│ continue-on- │                │  - Linux x64 │
│   error ✓    │                │  - macOS x64 │
└──────────────┘                │  - macOS ARM │
        │                       │  - Windows   │
        │                       └──────┬───────┘
        │                              │
        │                              ▼
        │                     ┌──────────────┐
        │                     │ Build Source │
        │                     │    (sdist)   │
        │                     └──────┬───────┘
        │                             │
        └─────────┬───────────────────┘
                  │ (Tests don't block!)
                  ▼
          ┌──────────────┐
          │ Check Builds │
          │  (Validate)  │
          └──────┬───────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────┐          ┌──────────┐
│Test PyPI │          │   PyPI   │
│ (manual) │          │  (tags)  │
└──────────┘          └──────────┘
```

### Key Design Decisions

1. **Tests Don't Block Deployment**
   ```yaml
   test:
     continue-on-error: true  # Can deploy even if tests fail
   ```
   Why: Sometimes you need to ship a critical fix even if unrelated tests fail

2. **Parallel Wheel Building**
   ```yaml
   strategy:
     matrix:
       include:
         - os: ubuntu-latest
           archs: x86_64
         - os: macos-13  # Intel
           archs: x86_64
         - os: macos-14  # Apple Silicon
           archs: arm64
   ```

3. **Source Distribution + Wheels**
   - Always build both sdist and wheels
   - sdist allows users to build from source if no wheel matches
   - Wheels provide pre-built binaries for common platforms

---

## Troubleshooting Guide

### Error: "Failed to load _c_analyzer: Library file not found"

**Cause**: Wrong file extension or search path

**Fix**: Check platform-specific extensions:
```python
# c_bindings.py
PLATFORM_EXTENSIONS = {
    "Linux": ".so",
    "Darwin": ".so",  # NOT .dylib!
    "Windows": ".dll",
}
```

### Error: "auditwheel repair failed"

**Cause**: Linking against non-manylinux libraries (e.g., libunwind)

**Fix**: Set CIBUILDWHEEL=1 in environment:
```toml
[tool.cibuildwheel]
environment = {CIBUILDWHEEL="1"}
```

### Error: "setup() arguments must be /-separated paths"

**Cause**: Using absolute paths in setup.py

**Fix**: Use relative paths:
```python
# WRONG
os.path.join(BASE_DIR, 'django_mercury/c_core/common.c')
# RIGHT
'django_mercury/c_core/common.c'
```

### Error: "No module named 'django_mercury.python_bindings.c_bindings.importlib'"

**Cause**: Invalid mock patch path on Windows

**Fix**: Patch at the right level:
```python
# WRONG
@patch('django_mercury.python_bindings.c_bindings.importlib.import_module')
# RIGHT
@patch('importlib.import_module')
```

### Error: Windows CI Can't Find .pyd Files

**Cause**: Looking for wrong extension or in wrong location

**Fix**: Windows builds create .pyd files, not .dll:
```python
if IS_WINDOWS:
    # Look for .pyd files
    extensions_to_try = [".pyd"]
```

---

## Reusable Patterns for Future Projects

### Pattern 1: Platform-Aware Extension Loading

```python
class CExtensionLoader:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.extensions = {}
    
    def load(self, name, library_name):
        if self.is_windows:
            # Windows: Import as Python module
            try:
                module = importlib.import_module(f"mypackage.{library_name}")
                self.extensions[name] = module
            except ImportError:
                self.extensions[name] = None
        else:
            # Unix: Load with ctypes
            try:
                lib_path = self._find_library(library_name)
                self.extensions[name] = ctypes.CDLL(lib_path)
            except OSError:
                self.extensions[name] = None
```

### Pattern 2: Minimal setup.py for Modern Python

```python
#!/usr/bin/env python
"""Minimal setup.py - all metadata in pyproject.toml"""

from setuptools import setup, Extension, find_packages
import platform

def get_extensions():
    """Build C extensions with platform-specific settings"""
    compile_args = ['-O2', '-fPIC', '-std=c99']
    
    if platform.system() == 'Windows':
        compile_args = ['/O2']
    
    return [
        Extension(
            'mypackage._c_module',
            sources=['mypackage/c_src/module.c'],
            extra_compile_args=compile_args,
        )
    ]

setup(
    packages=find_packages(),
    ext_modules=get_extensions(),
)
```

### Pattern 3: CI Configuration for C Extensions

```yaml
# .github/workflows/build.yml
env:
  CIBUILDWHEEL: "1"  # Always set this!

jobs:
  build_wheels:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    
    steps:
      - uses: pypa/cibuildwheel@v2.22.0
        env:
          CIBW_ENVIRONMENT: CIBUILDWHEEL=1
          CIBW_BUILD: "cp38-* cp39-* cp310-* cp311-* cp312-*"
          CIBW_SKIP: "*-win32 *-musllinux_*"
```

### Pattern 4: Testing Strategy

```python
# tests/test_c_extensions.py
import unittest
import platform

IS_WINDOWS = platform.system() == "Windows"

class TestCExtensions(unittest.TestCase):
    def test_loading(self):
        """Test appropriate loading mechanism for platform"""
        from mypackage import c_extensions
        
        if IS_WINDOWS:
            # Windows should import modules
            self.assertIsNotNone(c_extensions.module)
        else:
            # Unix should load libraries
            self.assertIsNotNone(c_extensions.library)
    
    @unittest.skipIf(IS_WINDOWS, "Unix-specific test")
    def test_ctypes_loading(self):
        """Test ctypes.CDLL loading on Unix"""
        # Unix-only test
    
    @unittest.skipUnless(IS_WINDOWS, "Windows-specific test")
    def test_pyd_import(self):
        """Test .pyd import on Windows"""
        # Windows-only test
```

---

## Summary: The Key Takeaways

1. **Windows .pyd files are special** - They're Python extensions, not raw DLLs
2. **Use platform detection, not file extension checking** - More reliable
3. **Set CIBUILDWHEEL=1 in your environment** - Avoid linking non-standard libraries
4. **Use relative paths in setup.py** - Absolute paths break wheel building
5. **Keep setup.py minimal but complete** - Include packages= for cibuildwheel
6. **Test loading mechanisms separately per platform** - Don't mock what doesn't exist
7. **C extensions mandatory in CI, optional for users** - Different requirements
8. **Build both .so libraries AND Python extensions** - Different use cases

---

## The 80-20 Philosophy Applied

- **80% Automated**: Building, testing, packaging across 9+ configurations
- **20% Human Control**: When to release, version numbers, quality gates
- **Result**: Reliable multi-platform deployment with C extension performance

This architecture ensures that:
- Performance-critical code runs at native speed
- Fallbacks exist for unsupported platforms
- Testing covers all platform combinations
- Deployment is reliable and repeatable

---

*Built through trial, error, and a lot of CI runs. May your builds be green and your wheels be round.*