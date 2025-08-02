#!/usr/bin/env python
"""
Safe setup script that always succeeds, even without C extensions.
"""

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_version():
    init_file = os.path.join(BASE_DIR, 'django_mercury', '__init__.py')
    with open(init_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip("'\"")
    return '0.0.1'

def get_long_description():
    readme_file = os.path.join(BASE_DIR, 'README.md')
    try:
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "Django Mercury Performance Testing Framework"

class OptionalBuildExt(build_ext):
    """A custom build extension that never fails."""
    
    def run(self):
        try:
            super().run()
        except:
            print("WARNING: C extensions could not be built.")
            print("Django Mercury will use pure Python implementation.")
    
    def build_extension(self, ext):
        try:
            super().build_extension(ext)
        except:
            print(f"Skipping {ext.name}")

# Try to get C extensions, but don't fail if we can't
def get_c_extensions():
    if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
        return []
    
    try:
        extensions = [
            Extension(
                'django_mercury._c_performance',
                sources=['django_mercury/c_core/python_wrapper.c', 'django_mercury/c_core/common.c'],
                include_dirs=['django_mercury/c_core'],
                libraries=['m'],
                extra_compile_args=['-O2', '-fPIC'] if sys.platform != 'win32' else [],
            ),
            Extension(
                'django_mercury._c_metrics',
                sources=['django_mercury/c_core/metrics_wrapper.c', 'django_mercury/c_core/common.c'],
                include_dirs=['django_mercury/c_core'],
                libraries=['m'],
                extra_compile_args=['-O2', '-fPIC'] if sys.platform != 'win32' else [],
            ),
            Extension(
                'django_mercury._c_analyzer',
                sources=['django_mercury/c_core/analyzer_wrapper.c', 'django_mercury/c_core/common.c'],
                include_dirs=['django_mercury/c_core'],
                libraries=['m'],
                extra_compile_args=['-O2', '-fPIC'] if sys.platform != 'win32' else [],
            ),
            Extension(
                'django_mercury._c_orchestrator',
                sources=['django_mercury/c_core/orchestrator_wrapper.c', 'django_mercury/c_core/common.c'],
                include_dirs=['django_mercury/c_core'],
                libraries=['m'],
                extra_compile_args=['-O2', '-fPIC'] if sys.platform != 'win32' else [],
            ),
        ]
        return extensions
    except:
        return []

setup(
    name='django-mercury-performance',
    version=get_version(),
    author='Django Mercury Team',
    author_email='mercury@djangoperformance.dev',
    description='A performance testing framework for Django',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/Django-Mercury/Performance-Testing',
    license='GPL-3.0-or-later',
    
    packages=find_packages(exclude=['tests*', '_long_haul_research*', 'test_build*']),
    include_package_data=True,
    
    ext_modules=get_c_extensions(),
    cmdclass={'build_ext': OptionalBuildExt},
    
    python_requires='>=3.8',
    install_requires=[
        'Django>=3.2,<6.0',
        'djangorestframework>=3.12.0',
        'psutil>=5.8.0',
        'memory-profiler>=0.60.0',
        'colorlog>=6.6.0',
        'jsonschema>=4.0.0',
    ],
    
    entry_points={
        'console_scripts': [
            'mercury-analyze=django_mercury.python_bindings.cli:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Testing',
    ],
)