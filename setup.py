#!/usr/bin/env python
"""
Setup script for Django Mercury Performance Testing

This script configures the C extensions for optimal performance monitoring
while providing pure Python fallbacks when C compilation isn't available.
"""

import os
import sys
import platform
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# Get the directory containing this setup.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Read version from __init__.py
def get_version():
    init_file = os.path.join(BASE_DIR, 'django_mercury', '__init__.py')
    with open(init_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip("'\"")
    return '0.0.1'

# Read long description from README
def get_long_description():
    readme_file = os.path.join(BASE_DIR, 'README.md')
    with open(readme_file, 'r', encoding='utf-8') as f:
        return f.read()

class OptionalBuildExt(build_ext):
    """Build extensions optionally, falling back to pure Python if compilation fails."""
    
    def build_extensions(self):
        # Check if we're being forced to use pure Python
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
            print("DJANGO_MERCURY_PURE_PYTHON set - skipping C extension build")
            # Clear extensions list so nothing tries to copy them
            self.extensions = []
            return
        
        # Keep track of successfully built extensions
        built_extensions = []
        failed_extensions = []
        
        # Try to build each extension individually
        for ext in self.extensions:
            try:
                super().build_extension(ext)
                built_extensions.append(ext)
            except Exception as e:
                print(f"WARNING: Failed to build {ext.name}: {e}")
                print(f"Skipping {ext.name} - will use pure Python fallback")
                failed_extensions.append(ext)
                continue
        
        # Remove failed extensions from the list so they don't cause copy errors
        self.extensions = built_extensions
        
        # If no extensions built successfully, show help message
        if not built_extensions:
            print("WARNING: No C extensions could be built.")
            print("Django Mercury will use pure Python implementations.")
            print("Performance will be reduced. For optimal performance, install build tools:")
            
            if sys.platform == 'linux':
                print("  Ubuntu/Debian: sudo apt-get install python3-dev build-essential")
                print("  RHEL/CentOS: sudo yum install python3-devel gcc")
            elif sys.platform == 'darwin':
                print("  macOS: Install Xcode Command Line Tools")
                print("  xcode-select --install")
            elif sys.platform == 'win32':
                print("  Windows: Install Visual Studio Build Tools")
                print("  https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio")
    
    def build_extension(self, ext):
        """Build a single extension."""
        try:
            super().build_extension(ext)
        except Exception as e:
            # Log the error but don't fail the entire build
            print(f"WARNING: Could not compile {ext.name}: {e}")
            # Don't re-raise - just skip this extension

def get_c_extensions():
    """
    Define all C extensions for Django Mercury.
    Returns empty list if pure Python mode is requested.
    """
    
    # Check for pure Python mode
    if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
        return []
    
    # Common source files used by multiple extensions
    common_sources = [
        'django_mercury/c_core/common.c',
    ]
    
    # Include directories
    include_dirs = [
        'django_mercury/c_core',
        '/usr/include',
        '/usr/local/include',
    ]
    
    # Platform-specific compilation flags  
    if sys.platform == 'win32':
        # Windows with MSVC
        compile_args = ['/O2', '/W3']
        link_args = []
        libraries = []
    elif sys.platform == 'darwin':
        # macOS
        compile_args = [
            '-O2', '-fPIC',
            '-std=c99',
        ]
        link_args = []
        libraries = ['m']  # Math library
    else:
        # Linux and other Unix-like systems
        compile_args = [
            '-O2', '-fPIC',
            '-std=c99',
        ]
        link_args = []
        libraries = ['m']  # Math library only
    
    # Check if we're building in cibuildwheel
    if os.environ.get('CIBUILDWHEEL', '0') == '1':
        # Add flags for better compatibility
        if sys.platform == 'linux':
            # Static linking for manylinux compatibility
            link_args.append('-static-libgcc')
        elif sys.platform == 'darwin':
            # Universal binary support
            if platform.machine() == 'arm64' or 'universal2' in os.environ.get('ARCHFLAGS', ''):
                compile_args.extend(['-arch', 'x86_64', '-arch', 'arm64'])
                link_args.extend(['-arch', 'x86_64', '-arch', 'arm64'])
    
    # Define extensions
    extensions = [
        Extension(
            name='django_mercury._c_performance',
            sources=[
                'django_mercury/c_core/python_wrapper.c',  # Use Python wrapper
            ] + common_sources,
            include_dirs=include_dirs,
            libraries=libraries,
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language='c',
        ),
        Extension(
            name='django_mercury._c_metrics',
            sources=[
                'django_mercury/c_core/metrics_wrapper.c',  # Use Python wrapper
            ] + common_sources,
            include_dirs=include_dirs,
            libraries=libraries,
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language='c',
        ),
        Extension(
            name='django_mercury._c_analyzer',
            sources=[
                'django_mercury/c_core/analyzer_wrapper.c',  # Use Python wrapper
            ] + common_sources,
            include_dirs=include_dirs,
            libraries=libraries,
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language='c',
        ),
        Extension(
            name='django_mercury._c_orchestrator',
            sources=[
                'django_mercury/c_core/orchestrator_wrapper.c',  # Use Python wrapper
            ] + common_sources,
            include_dirs=include_dirs,
            libraries=libraries,
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language='c',
        ),
    ]
    
    return extensions

# Main setup configuration
setup(
    name='django-mercury-performance',
    version=get_version(),
    author='Django Mercury Team',
    author_email='mercury@djangoperformance.dev',
    description='A performance testing framework for Django that helps you understand and fix performance issues',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/Django-Mercury/Performance-Testing',
    license='GPL-3.0-or-later',
    
    # Package configuration
    packages=find_packages(exclude=['tests*', '_long_haul_research*']),
    package_data={
        'django_mercury': [
            'py.typed',
            '*.md',
        ],
        'django_mercury.c_core': [
            '*.h',
            '*.c',
            'Makefile',
            'BUILD.md',
        ],
        'django_mercury.documentation': [
            '*.md',
        ],
        'django_mercury.examples': [
            '*.py',
        ],
    },
    include_package_data=True,
    
    # C Extensions
    ext_modules=get_c_extensions(),
    cmdclass={
        'build_ext': OptionalBuildExt,
    },
    
    # Dependencies
    python_requires='>=3.8',
    install_requires=[
        'Django>=3.2,<6.0',
        'djangorestframework>=3.12.0',
        'psutil>=5.8.0',
        'memory-profiler>=0.60.0',
        'colorlog>=6.6.0',
        'jsonschema>=4.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'isort>=5.10.0',
            'mypy>=0.950',
            'flake8>=4.0.0',
            'coverage>=6.0.0',
        ],
        'rich': [
            'rich>=12.0.0',
        ],
    },
    
    # Entry points
    entry_points={
        'console_scripts': [
            'mercury-analyze=django_mercury.python_bindings.cli:main',
        ],
    },
    
    # PyPI classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: C',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
    ],
    keywords=[
        'django',
        'performance',
        'testing',
        'monitoring',
        'optimization',
        'n+1',
        'queries',
        'profiling',
        'mercury',
    ],
)