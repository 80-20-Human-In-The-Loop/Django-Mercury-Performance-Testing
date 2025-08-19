"""
Mercury-Test Plugin System

This package contains the plugin system for mercury-test CLI.
Each plugin extends the core functionality in a modular way.
"""

from .base import MercuryPlugin
from .plugin_manager import PluginManager

__all__ = ["MercuryPlugin", "PluginManager"]
