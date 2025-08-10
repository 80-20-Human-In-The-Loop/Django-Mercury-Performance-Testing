#!/usr/bin/env python
"""
Minimal setup script for Django Mercury C extensions.

All package metadata is defined in pyproject.toml.
This file only handles C extension building for compatibility.
"""

import os
import sys
import platform
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

class OptionalBuildExt(build_ext):
    """Build extensions optionally, falling back to pure Python if compilation fails."""
    
    def build_extensions(self):
        # Check if we're being forced to use pure Python
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
            print("DJANGO_MERCURY_PURE_PYTHON set - skipping C extension build")
            # Clear extensions list so nothing tries to copy them
            self.extensions = []
            return
        
        # On Windows, check if we have build tools
        if sys.platform == 'win32':
            try:
                from distutils import msvccompiler
                from distutils.msvccompiler import get_build_version
                msvc_ver = get_build_version()
                if msvc_ver:
                    print(f"Found MSVC version {msvc_ver}")
            except ImportError:
                # distutils is deprecated, try alternative check
                import subprocess
                try:
                    result = subprocess.run(['cl'], capture_output=True, text=True)
                    if result.returncode == 0 or 'Microsoft' in result.stderr:
                        print("Found MSVC compiler")
                except:
                    print("WARNING: MSVC not found: cannot import name 'msvccompiler' from 'distutils'")
                    print("C extensions may not build on Windows without Visual Studio Build Tools")
        
        # Try to build each extension
        for ext in self.extensions:
            try:
                super().build_extension(ext)
                print(f"Successfully built {ext.name}")
            except Exception as e:
                print(f"WARNING: Failed to build {ext.name}: {e}")
                print(f"Django Mercury will use pure Python fallback for {ext.name}")

def get_c_extensions():
    """Get the list of C extensions to build."""
    # Skip if explicitly disabled
    if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
        return []
    
    # Skip on PyPy (doesn't support C extensions well)
    if hasattr(sys, 'pypy_version_info'):
        print("PyPy detected - skipping C extensions")
        return []
    
    # Common compile arguments
    compile_args = ['-O2', '-fPIC', '-std=c99']
    libraries = ['m']  # Math library
    
    # Platform-specific settings
    if sys.platform == 'darwin':
        # macOS
        compile_args.extend(['-stdlib=libc++', '-mmacosx-version-min=10.9'])
    elif sys.platform.startswith('win'):
        # Windows
        compile_args = ['/O2']
        libraries = []
    else:
        # Linux and other Unix-like systems
        compile_args.append('-pthread')
        libraries.append('pthread')
        
        # Don't link libunwind for wheel builds (better compatibility)
        compile_args.append('-DMERCURY_HAS_LIBUNWIND=0')
    
    # Define extensions
    extensions = []
    
    # Performance monitor wrapper (minimal functionality)
    extensions.append(Extension(
        'django_mercury._c_performance',
        sources=[
            'django_mercury/c_core/common.c',
            'django_mercury/c_core/performance_wrapper.c',
        ],
        include_dirs=['django_mercury/c_core', '/usr/include', '/usr/local/include'],
        libraries=libraries,
        extra_compile_args=compile_args,
        language='c'
    ))
    
    # Metrics engine wrapper
    extensions.append(Extension(
        'django_mercury._c_metrics',
        sources=[
            'django_mercury/c_core/common.c',
            'django_mercury/c_core/metrics_engine.c',
            'django_mercury/c_core/metrics_wrapper.c',
        ],
        include_dirs=['django_mercury/c_core', '/usr/include', '/usr/local/include'],
        libraries=libraries,
        extra_compile_args=compile_args,
        language='c'
    ))
    
    # Query analyzer wrapper
    extensions.append(Extension(
        'django_mercury._c_analyzer',
        sources=[
            'django_mercury/c_core/analyzer_wrapper.c',
            'django_mercury/c_core/common.c',
            'django_mercury/c_core/query_analyzer.c',
        ],
        include_dirs=['django_mercury/c_core', '/usr/include', '/usr/local/include'],
        libraries=libraries,
        extra_compile_args=compile_args,
        language='c'
    ))
    
    # Test orchestrator wrapper
    extensions.append(Extension(
        'django_mercury._c_orchestrator',
        sources=[
            'django_mercury/c_core/common.c',
            'django_mercury/c_core/orchestrator_wrapper.c',
            'django_mercury/c_core/test_orchestrator.c',
        ],
        include_dirs=['django_mercury/c_core', '/usr/include', '/usr/local/include'],
        libraries=libraries,
        extra_compile_args=compile_args,
        language='c'
    ))
    
    return extensions

# Minimal setup - all metadata comes from pyproject.toml
# But we need to specify packages for direct setup.py calls (e.g., cibuildwheel)
setup(
    # Package discovery - needed when setup.py is called directly
    packages=find_packages(exclude=['tests*', '_long_haul_research*']),
    package_data={
        'django_mercury': ['*.md', 'py.typed'],
        # Only include source files, not built libraries (they're Python extensions now)
        'django_mercury.c_core': ['*.h', '*.c', 'Makefile', 'BUILD.md'],
        'django_mercury.documentation': ['*.md'],
        'django_mercury.examples': ['*.py'],
    },
    # C extension configuration
    ext_modules=get_c_extensions(),
    cmdclass={'build_ext': OptionalBuildExt},
)