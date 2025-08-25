"""
Base Plugin Interface for Mercury-Test CLI

This module defines the base plugin class that all mercury-test plugins must inherit from.
Follows the small core philosophy - minimal interface, maximum extensibility.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Callable, Optional, List


class MercuryPlugin(ABC):
    """Base class for all Mercury-Test plugins.

    Each plugin is a self-contained module that extends mercury-test functionality.
    Plugins can:
    - Add command-line arguments
    - Handle specific command modes
    - Enhance core functionality (like manage.py discovery)
    - Hook into test lifecycle (before/after tests)
    """

    # Plugin metadata - override in subclasses
    name: str = ""
    description: str = ""
    priority: int = 100  # Loading order: lower = earlier
    version: str = "1.0.0"

    # Audience targeting - NEW fields for three audiences pattern
    audiences: List[str] = []  # ['student', 'expert', 'agent']
    complexity_level: int = 1  # 1-5 scale (1=simple, 5=complex)
    requires_capabilities: List[str] = []  # ['rich', 'django', 'c_extensions']

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Add plugin-specific arguments to the CLI parser.

        Args:
            parser: The main argument parser to extend

        Example:
            parser.add_argument('--my-flag', action='store_true',
                              help='Enable my plugin feature')
        """
        pass

    def can_handle(self, args: Namespace) -> bool:
        """Check if this plugin should handle the request completely.

        Args:
            args: Parsed command-line arguments

        Returns:
            True if this plugin should take over execution

        Example:
            return args.wizard  # Handle --wizard flag exclusively
        """
        return False

    def execute(self, args: Namespace) -> int:
        """Execute plugin functionality when handling request completely.

        Args:
            args: Parsed command-line arguments

        Returns:
            Exit code (0 for success, non-zero for failure)

        Note:
            Only called if can_handle() returns True
        """
        return 0

    def enhance_discovery(self, current_search: Callable) -> Callable:
        """Enhance the manage.py discovery process.

        Args:
            current_search: Current discovery function

        Returns:
            Enhanced discovery function (can be same or different)

        Example:
            def enhanced_search(args):
                # Try smart discovery first
                result = self.smart_discovery(args)
                if result:
                    return result
                # Fall back to current method
                return current_search(args)
            return enhanced_search
        """
        return current_search

    def pre_test_hook(self, args: Namespace) -> None:
        """Called before Django tests start running.

        Args:
            args: Parsed command-line arguments

        Use for:
            - Setup operations
            - Validation
            - User notifications
        """
        pass

    def post_test_hook(self, args: Namespace, result: int, elapsed: float) -> None:
        """Called after Django tests complete.

        Args:
            args: Parsed command-line arguments
            result: Test exit code
            elapsed: Test execution time in seconds

        Use for:
            - Performance analysis
            - Cleanup operations
            - User feedback
        """
        pass

    def is_enabled(self, args: Namespace) -> bool:
        """Check if this plugin is enabled for the current request.

        Args:
            args: Parsed command-line arguments

        Returns:
            True if plugin should be active

        Default implementation checks for --disable-plugin flag.
        """
        disabled_plugins = getattr(args, "disable_plugin", [])
        if isinstance(disabled_plugins, str):
            disabled_plugins = [disabled_plugins]

        return self.name not in disabled_plugins

    def get_config(self, key: str, default=None):
        """Get plugin configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value

        Note:
            Will be enhanced to read from config files in future
        """
        # TODO: Implement config file reading
        return default

    @classmethod
    def from_config(cls, config: dict) -> "MercuryPlugin":
        """
        Create plugin instance from TOML configuration.

        Args:
            config: Plugin configuration from TOML

        Returns:
            Configured plugin instance
        """
        instance = cls()

        # Apply configuration if provided
        if "priority" in config:
            instance.priority = config["priority"]
        if "audiences" in config:
            instance.audiences = config["audiences"]
        if "complexity_level" in config:
            instance.complexity_level = config["complexity_level"]
        if "requires_capabilities" in config:
            instance.requires_capabilities = config["requires_capabilities"]

        return instance

    def supports_audience(self, audience: str) -> bool:
        """
        Check if this plugin supports a specific audience.

        Args:
            audience: Audience name ('student', 'expert', or 'agent')

        Returns:
            True if plugin supports this audience
        """
        return audience in self.audiences

    def __repr__(self) -> str:
        """String representation for debugging."""
        audiences_str = f", audiences={self.audiences}" if self.audiences else ""
        return f"<{self.__class__.__name__}(name='{self.name}', priority={self.priority}{audiences_str})>"


class PluginError(Exception):
    """Base exception for plugin-related errors."""

    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""

    pass


class PluginConfigError(PluginError):
    """Raised when a plugin has invalid configuration."""

    pass
