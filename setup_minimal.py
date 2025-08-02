#!/usr/bin/env python
"""
Minimal setup script for Django Mercury Performance Testing

This is a fallback setup.py that builds without C extensions if they fail.
"""

from setuptools import setup, find_packages
import os

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
    try:
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "Django Mercury Performance Testing Framework"

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
        'django_mercury': ['*.md', 'py.typed'],
        'django_mercury.c_core': ['*.h', '*.c', 'Makefile', 'BUILD.md'],
        'django_mercury.documentation': ['*.md'],
        'django_mercury.examples': ['*.py'],
        'django_mercury.python_bindings': ['*.py'],
    },
    include_package_data=True,
    
    # No C Extensions in minimal setup
    ext_modules=[],
    
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
        'Topic :: Software Development :: Testing',
    ],
)