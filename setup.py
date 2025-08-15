#!/usr/bin/env python
"""
Setup script for Django Mercury - Pure Python Performance Testing Framework.

All package metadata is defined in pyproject.toml.
This is now a pure Python package with no C extensions.
"""

from setuptools import setup, find_packages

# Pure Python setup - all metadata comes from pyproject.toml
setup(
    # Package discovery
    packages=find_packages(exclude=['tests*', '_long_haul_research*']),
    package_data={
        'django_mercury': ['*.md', 'py.typed'],
        'django_mercury.documentation': ['*.md'],
        'django_mercury.examples': ['*.py'],
        'django_mercury.python_bindings': ['*.md'],
        'django_mercury.cli': ['*.md'],
        'django_mercury.cli.plugins': ['*.md'],
    },
    # No C extensions - pure Python package
    ext_modules=[],
)