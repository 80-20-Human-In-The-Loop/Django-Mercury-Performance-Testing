"""
Visual Progress Plugin Wrapper

This is a thin wrapper that imports the refactored visual progress plugin
from its new modular folder structure. This file exists to maintain compatibility
with the plugin discovery mechanism that looks for plugin_*.py files.
"""

# Use absolute import to avoid issues with plugin discovery
from django_mercury.cli.plugins.visual_progress.plugin import VisualProgressPlugin

# Export the plugin class so the plugin manager can find it
__all__ = ["VisualProgressPlugin"]
