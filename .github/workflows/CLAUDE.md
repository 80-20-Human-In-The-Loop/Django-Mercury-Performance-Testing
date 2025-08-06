# Cross-Platform C Extension Deployment Guide

**How Django Mercury Ships High-Performance C Extensions That Work Everywhere**

## Introduction

This guide documents how Django Mercury successfully deploys C extensions across Windows, macOS, and Linux while maintaining a pure Python fallback. We started with a Django view making 825 database queries and ended with a framework that helps developers find and fix performance problems using C extensions that run 10-100x faster than pure Python.

## The Problem We Solved

Django Mercury needed to:
- Ship high-performance C extensions for speed-critical operations
- Work on any system, even without a compiler
- Install with a simple `pip install django-mercury-performance`
- Automatically use C when available, Python when not

## Architecture: The Three-Layer Strategy

Django Mercury implements three layers of functionality, each serving as a fallback for the previous:

### Layer 1: Direct C Libraries (Fastest)
On Unix systems, we build standalone shared libraries (.so files) that can be loaded via ctypes. This provides maximum performance with minimal Python overhead.

### Layer 2: Python C Extensions (Fast)
When direct libraries aren't available, we use Python C API extensions. These are .pyd files on Windows and .so files on Unix, imported as Python modules.

### Layer 3: Pure Python (Universal)
When no C implementation is available, we fall back to pure Python. Slower but guaranteed to work everywhere.

## Project Structure

Here's how Django Mercury organizes its C extension code:

```
django_mercury/
├── __init__.py                 # Lazy loading entry point
├── c_core/                     # C source code
│   ├── Makefile               # Unix build system
│   ├── common.c               # Shared utilities
│   ├── common.h               # Header definitions
│   ├── performance.c          # Performance monitoring
│   ├── metrics_engine.c       # Metrics calculations
│   ├── query_analyzer.c       # SQL analysis
│   ├── test_orchestrator.c    # Test coordination
│   └── *_wrapper.c           # Python C API wrappers
├── python_bindings/
│   ├── loader.py              # Smart loading logic
│   ├── c_bindings.py          # ctypes bindings
│   ├── c_wrappers.py          # Python wrappers
│   └── pure_python.py         # Fallback implementations
└── build/                      # Build artifacts (generated)
```

## Step 1: Writing the C Code

### The Header File (common.h)

Start with a single header file that defines all your structures. This prevents synchronization issues:

```c
// django_mercury/c_core/common.h
#ifndef MERCURY_COMMON_H
#define MERCURY_COMMON_H

#include <stdint.h>
#include <stdbool.h>

// Performance metrics structure
typedef struct {
    double response_time_ms;
    double memory_usage_mb;
    uint32_t query_count;
    uint32_t cache_hits;
    uint32_t cache_misses;
    bool n_plus_one_detected;
} PerformanceMetrics;

// Error codes
typedef enum {
    MERCURY_SUCCESS = 0,
    MERCURY_ERROR_INVALID_PARAM = -1,
    MERCURY_ERROR_OUT_OF_MEMORY = -2,
    MERCURY_ERROR_NOT_INITIALIZED = -3
} MercuryError;

// Export macro for Windows
#ifdef _WIN32
    #define MERCURY_EXPORT __declspec(dllexport)
#else
    #define MERCURY_EXPORT __attribute__((visibility("default")))
#endif

#endif // MERCURY_COMMON_H
```

### The Implementation (performance.c)

Write your C implementation with clear exports:

```c
// django_mercury/c_core/performance.c
#include "common.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    char operation_name[256];
    clock_t start_time;
    PerformanceMetrics metrics;
    bool is_active;
} MonitorContext;

static MonitorContext* g_context = NULL;

MERCURY_EXPORT int start_monitoring(const char* operation_name) {
    if (g_context && g_context->is_active) {
        return MERCURY_ERROR_INVALID_PARAM;
    }
    
    if (!g_context) {
        g_context = (MonitorContext*)calloc(1, sizeof(MonitorContext));
        if (!g_context) {
            return MERCURY_ERROR_OUT_OF_MEMORY;
        }
    }
    
    strncpy(g_context->operation_name, operation_name, 255);
    g_context->start_time = clock();
    g_context->is_active = true;
    memset(&g_context->metrics, 0, sizeof(PerformanceMetrics));
    
    return MERCURY_SUCCESS;
}

MERCURY_EXPORT PerformanceMetrics* stop_monitoring() {
    if (!g_context || !g_context->is_active) {
        return NULL;
    }
    
    clock_t end_time = clock();
    double elapsed_ms = ((double)(end_time - g_context->start_time) / CLOCKS_PER_SEC) * 1000;
    
    g_context->metrics.response_time_ms = elapsed_ms;
    g_context->is_active = false;
    
    return &g_context->metrics;
}
```

### The Python C API Wrapper

For Python extensions, create a wrapper:

```c
// django_mercury/c_core/performance_wrapper.c
#include <Python.h>
#include "common.h"

// External functions from performance.c
extern int start_monitoring(const char* operation_name);
extern PerformanceMetrics* stop_monitoring();

static PyObject* py_start_monitoring(PyObject* self, PyObject* args) {
    const char* operation_name;
    
    if (!PyArg_ParseTuple(args, "s", &operation_name)) {
        return NULL;
    }
    
    int result = start_monitoring(operation_name);
    return PyLong_FromLong(result);
}

static PyObject* py_stop_monitoring(PyObject* self, PyObject* args) {
    PerformanceMetrics* metrics = stop_monitoring();
    
    if (!metrics) {
        Py_RETURN_NONE;
    }
    
    // Convert to Python dict
    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "response_time_ms", 
                        PyFloat_FromDouble(metrics->response_time_ms));
    PyDict_SetItemString(dict, "query_count", 
                        PyLong_FromLong(metrics->query_count));
    
    return dict;
}

static PyMethodDef module_methods[] = {
    {"start_monitoring", py_start_monitoring, METH_VARARGS, 
     "Start performance monitoring"},
    {"stop_monitoring", py_stop_monitoring, METH_NOARGS, 
     "Stop monitoring and get metrics"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "_c_performance",
    "C performance monitoring extension",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit__c_performance(void) {
    return PyModule_Create(&module_def);
}
```

## Step 2: The Build System

### Makefile for Development

Create a Makefile for Unix development:

```makefile
# django_mercury/c_core/Makefile
CC = gcc
CFLAGS = -std=c99 -fPIC -O3 -Wall -Wextra
LDFLAGS = -shared

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    CC = clang
    LDFLAGS += -dynamiclib
endif

# Source files
SOURCES = common.c performance.c metrics_engine.c query_analyzer.c
OBJECTS = $(SOURCES:.c=.o)

# Targets
all: libperformance.so libmetrics.so libanalyzer.so

libperformance.so: common.o performance.o
	$(CC) $(LDFLAGS) -o $@ $^

libmetrics.so: common.o metrics_engine.o
	$(CC) $(LDFLAGS) -o $@ $^

libanalyzer.so: common.o query_analyzer.o
	$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.so

.PHONY: all clean
```

### setup.py for Distribution

The setup.py handles building Python extensions with graceful fallback:

```python
# setup.py
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import sys
import os

class OptionalBuildExt(build_ext):
    """Build extensions optionally - don't fail installation."""
    
    def build_extensions(self):
        # Check for environment override
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true'):
            print("Pure Python mode requested - skipping C extensions")
            return
        
        # Try to build each extension
        for ext in self.extensions:
            try:
                super().build_extension(ext)
                print(f"Successfully built {ext.name}")
            except Exception as e:
                print(f"WARNING: Failed to build {ext.name}: {e}")
                print("Will use pure Python fallback")

def get_extensions():
    """Get list of C extensions to build."""
    
    # Skip on PyPy
    if hasattr(sys, 'pypy_version_info'):
        return []
    
    compile_args = ['-O3', '-std=c99']
    libraries = []
    
    if sys.platform == 'win32':
        compile_args = ['/O2']
    elif sys.platform == 'darwin':
        compile_args.extend(['-mmacosx-version-min=10.9'])
    else:
        libraries = ['m', 'pthread']
    
    extensions = [
        Extension(
            'django_mercury._c_performance',
            sources=[
                'django_mercury/c_core/common.c',
                'django_mercury/c_core/performance.c',
                'django_mercury/c_core/performance_wrapper.c',
            ],
            extra_compile_args=compile_args,
            libraries=libraries,
        ),
        Extension(
            'django_mercury._c_metrics',
            sources=[
                'django_mercury/c_core/common.c',
                'django_mercury/c_core/metrics_engine.c',
                'django_mercury/c_core/metrics_wrapper.c',
            ],
            extra_compile_args=compile_args,
            libraries=libraries,
        ),
    ]
    
    return extensions

setup(
    packages=find_packages(),
    ext_modules=get_extensions(),
    cmdclass={'build_ext': OptionalBuildExt},
)
```

## Step 3: The Loading System

### The Smart Loader (loader.py)

This is the heart of Django Mercury's compatibility system:

```python
# django_mercury/python_bindings/loader.py
import os
import sys
import warnings
from typing import Type, Optional, Tuple

# Environment control
FORCE_PURE_PYTHON = os.environ.get("DJANGO_MERCURY_PURE_PYTHON", "").lower() in ("1", "true")

class ImplementationLoader:
    """Loads the best available implementation."""
    
    def __init__(self):
        self._performance_monitor_class = None
        self._loaded = False
        self._using_c = False
    
    def load(self):
        """Load appropriate implementation."""
        if self._loaded:
            return
        
        if FORCE_PURE_PYTHON:
            self._load_pure_python()
        else:
            # Try C extensions first
            if self._try_load_c_extensions():
                self._using_c = True
            else:
                self._load_pure_python()
                self._show_fallback_warning()
        
        self._loaded = True
    
    def _try_load_c_extensions(self) -> bool:
        """Try to load C extensions."""
        try:
            # Windows: Ensure DLLs can be loaded
            if sys.platform == 'win32':
                package_dir = os.path.dirname(os.path.dirname(__file__))
                if hasattr(os, 'add_dll_directory'):
                    os.add_dll_directory(package_dir)
            
            # Try importing C extensions
            import django_mercury._c_performance
            import django_mercury._c_metrics
            
            # Load wrapper classes
            from .c_wrappers import CPerformanceMonitor
            self._performance_monitor_class = CPerformanceMonitor
            
            return True
            
        except ImportError:
            return False
    
    def _load_pure_python(self):
        """Load pure Python implementation."""
        from .pure_python import PythonPerformanceMonitor
        self._performance_monitor_class = PythonPerformanceMonitor
    
    def _show_fallback_warning(self):
        """Show performance warning."""
        if os.environ.get("DJANGO_MERCURY_SUPPRESS_WARNING"):
            return
            
        msg = (
            "Django Mercury: C extensions not available, using pure Python.\n"
            "Performance will be reduced. For optimal performance:\n"
        )
        
        if sys.platform == "linux":
            msg += "  Ubuntu/Debian: sudo apt-get install python3-dev build-essential\n"
        elif sys.platform == "darwin":
            msg += "  macOS: xcode-select --install\n"
        elif sys.platform == "win32":
            msg += "  Windows: Install Visual Studio Build Tools\n"
        
        warnings.warn(msg, RuntimeWarning)
    
    @property
    def PerformanceMonitor(self):
        if not self._loaded:
            self.load()
        return self._performance_monitor_class

# Global loader instance
_loader = ImplementationLoader()

# Public API
def get_performance_monitor():
    return _loader.PerformanceMonitor
```

### The C Wrapper (c_wrappers.py)

Provides a clean Python interface over C extensions:

```python
# django_mercury/python_bindings/c_wrappers.py
from typing import Dict, Any

class CPerformanceMonitor:
    """Wrapper for C performance monitor."""
    
    def __init__(self):
        try:
            import django_mercury._c_performance as c_perf
            self._module = c_perf
            self._using_fallback = False
        except ImportError:
            # Fallback to pure Python
            from .pure_python import PythonPerformanceMonitor
            self._monitor = PythonPerformanceMonitor()
            self._using_fallback = True
    
    def start_monitoring(self, operation_name: str):
        if self._using_fallback:
            return self._monitor.start_monitoring(operation_name)
        
        result = self._module.start_monitoring(operation_name)
        if result != 0:
            raise RuntimeError(f"Failed to start monitoring: {result}")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        if self._using_fallback:
            return self._monitor.stop_monitoring()
        
        metrics = self._module.stop_monitoring()
        if metrics is None:
            raise RuntimeError("No monitoring in progress")
        
        return metrics
```

### Pure Python Fallback (pure_python.py)

The fallback that always works:

```python
# django_mercury/python_bindings/pure_python.py
import time
from typing import Dict, Any, Optional

class PythonPerformanceMonitor:
    """Pure Python performance monitoring."""
    
    def __init__(self):
        self._start_time: Optional[float] = None
        self._operation_name: Optional[str] = None
        self._metrics: Dict[str, Any] = {}
    
    def start_monitoring(self, operation_name: str):
        if self._start_time is not None:
            raise RuntimeError("Monitoring already in progress")
        
        self._operation_name = operation_name
        self._start_time = time.perf_counter()
        self._metrics = {
            'query_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
    
    def stop_monitoring(self) -> Dict[str, Any]:
        if self._start_time is None:
            raise RuntimeError("No monitoring in progress")
        
        elapsed = (time.perf_counter() - self._start_time) * 1000
        
        self._metrics['response_time_ms'] = elapsed
        self._metrics['operation_name'] = self._operation_name
        
        self._start_time = None
        self._operation_name = None
        
        return self._metrics.copy()
```

## Step 4: Platform-Specific Handling

### Windows Specifics

Windows requires special handling for Python extensions:

```python
# In your loader or __init__.py
if sys.platform == 'win32':
    # Windows can't use ctypes for .pyd files
    # Must import as Python modules
    try:
        import django_mercury._c_performance
        HAS_C_EXTENSIONS = True
    except ImportError:
        HAS_C_EXTENSIONS = False
else:
    # Unix can use ctypes for .so files
    try:
        import ctypes
        lib = ctypes.CDLL('./libperformance.so')
        HAS_C_EXTENSIONS = True
    except OSError:
        HAS_C_EXTENSIONS = False
```

### macOS Universal Binaries

Support both Intel and Apple Silicon:

```python
# In setup.py
if sys.platform == 'darwin':
    import platform
    
    if platform.machine() == 'arm64':
        # Apple Silicon
        extra_compile_args = ['-arch', 'arm64']
    elif platform.machine() == 'x86_64':
        # Intel
        extra_compile_args = ['-arch', 'x86_64']
```

### Linux GLIBC Compatibility

For broad Linux compatibility:

```toml
# pyproject.toml
[tool.cibuildwheel.linux]
manylinux-x86_64-image = "manylinux2014"
manylinux-aarch64-image = "manylinux2014"
```

## Step 5: CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/build.yml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip setuptools wheel
        pip install -e .[test]
    
    - name: Build C extensions
      run: python setup.py build_ext --inplace
    
    - name: Run tests
      run: pytest tests/
    
    - name: Test pure Python fallback
      env:
        DJANGO_MERCURY_PURE_PYTHON: "1"
      run: pytest tests/

  build_wheels:
    needs: test
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build wheels
      uses: pypa/cibuildwheel@v2
      env:
        CIBW_BUILD: "cp38-* cp39-* cp310-* cp311-* cp312-*"
        CIBW_SKIP: "*-win32 *-musllinux_*"
    
    - uses: actions/upload-artifact@v4
      with:
        name: wheels-${{ matrix.os }}
        path: ./wheelhouse/*.whl
```

### cibuildwheel Configuration

```toml
# pyproject.toml
[tool.cibuildwheel]
build-verbosity = 1
test-requires = "pytest"
test-command = "pytest {package}/tests"

[tool.cibuildwheel.linux]
before-all = "yum install -y gcc"
environment = {CIBUILDWHEEL="1"}
repair-wheel-command = "auditwheel repair -w {dest_dir} {wheel}"

[tool.cibuildwheel.macos]
environment = {CIBUILDWHEEL="1", MACOSX_DEPLOYMENT_TARGET="10.9"}

[tool.cibuildwheel.windows]
environment = {CIBUILDWHEEL="1"}
```

## Step 6: Testing the Implementation

### Verification Script

Create a script to verify your build:

```python
# scripts/verify_build.py
#!/usr/bin/env python3
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def verify_c_extensions():
    """Verify C extensions are working."""
    print("Checking C extensions...")
    
    try:
        import django_mercury._c_performance
        print("✓ _c_performance loaded")
    except ImportError as e:
        print(f"✗ _c_performance failed: {e}")
        return False
    
    try:
        import django_mercury._c_metrics
        print("✓ _c_metrics loaded")
    except ImportError as e:
        print(f"✗ _c_metrics failed: {e}")
        return False
    
    return True

def verify_fallback():
    """Verify fallback works."""
    print("\nChecking pure Python fallback...")
    
    os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '1'
    
    try:
        from django_mercury import PerformanceMonitor
        monitor = PerformanceMonitor()
        monitor.start_monitoring("test")
        metrics = monitor.stop_monitoring()
        print(f"✓ Fallback works: {metrics}")
        return True
    except Exception as e:
        print(f"✗ Fallback failed: {e}")
        return False

if __name__ == "__main__":
    c_ok = verify_c_extensions()
    fallback_ok = verify_fallback()
    
    if c_ok and fallback_ok:
        print("\n✅ All systems operational")
        sys.exit(0)
    else:
        print("\n❌ Some components failed")
        sys.exit(1)
```

### Test Runner Script

```bash
#!/bin/bash
# scripts/test_all.sh

echo "Testing with C extensions..."
python -m pytest tests/

echo "Testing with pure Python fallback..."
DJANGO_MERCURY_PURE_PYTHON=1 python -m pytest tests/

echo "Checking performance difference..."
python scripts/benchmark.py
```

## Step 7: Deployment

### Building for PyPI

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build source distribution
python -m build --sdist

# Build wheels for current platform
python -m build --wheel

# For all platforms, use cibuildwheel
python -m cibuildwheel --output-dir dist

# Check the distributions
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation
pip install -i https://test.pypi.org/simple/ django-mercury-performance

# Upload to PyPI
twine upload dist/*
```

## Common Issues and Solutions

### Issue: "C extensions not building on Windows"

**Solution**: Windows requires Visual Studio Build Tools. Users without it will automatically use the pure Python fallback.

### Issue: "Symbol not found on macOS"

**Solution**: Ensure you're using the correct deployment target:
```bash
export MACOSX_DEPLOYMENT_TARGET=10.9
python setup.py build_ext
```

### Issue: "GLIBC version errors on Linux"

**Solution**: Build wheels using manylinux2014 or newer:
```bash
docker run -v $(pwd):/io quay.io/pypa/manylinux2014_x86_64 \
    /io/scripts/build_linux_wheels.sh
```

### Issue: "Pure Python fallback not working"

**Solution**: Ensure your pure Python implementation is complete:
```python
# Test both paths explicitly
DJANGO_MERCURY_PURE_PYTHON=1 python -c "from django_mercury import PerformanceMonitor"
DJANGO_MERCURY_PURE_PYTHON=0 python -c "from django_mercury import PerformanceMonitor"
```

## Performance Comparison

Here's what we achieved with Django Mercury:

| Operation | Pure Python | C Extension | Speedup |
|-----------|------------|-------------|---------|
| Query Analysis | 45ms | 0.5ms | 90x |
| Metrics Calculation | 12ms | 0.2ms | 60x |
| N+1 Detection | 89ms | 1.2ms | 74x |
| Full Test Suite | 8.2s | 2.1s | 3.9x |

## Key Lessons Learned

1. **Always provide a fallback**: Not everyone can compile C extensions
2. **Test both paths in CI**: Ensure both C and Python implementations work
3. **Use cibuildwheel**: It handles platform-specific complexity
4. **Document clearly**: Users need to know what's happening
5. **Platform differences matter**: Windows .pyd files work differently than Unix .so files

## Conclusion

Django Mercury's approach to C extensions provides:
- **Performance**: 10-100x speedup for critical operations
- **Compatibility**: Works on all platforms
- **Reliability**: Graceful fallback ensures it always works
- **User-friendly**: Simple `pip install` experience

This architecture has been tested across 15+ OS versions and successfully deployed to PyPI, processing millions of performance tests in production Django applications.

https://gist.github.com/smattymatty/2d41d5c4dbbcb7c785b70deb9190a1f4

For the complete implementation, see the [Django Mercury repository](https://github.com/Django-Mercury/Performance-Testing).