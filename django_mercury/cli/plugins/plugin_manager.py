"""
Plugin Manager for Mercury-Test CLI

Handles automatic discovery, loading, and management of mercury-test plugins.
"""

import importlib.util
import inspect
import logging
from pathlib import Path
from typing import List, Type, Dict, Any, Optional
from argparse import Namespace

from django_mercury.cli.plugins.base import MercuryPlugin, PluginLoadError

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages mercury-test plugins with config-based loading."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, auto_discover: bool = False):
        """Initialize the plugin manager.

        Args:
            config: Configuration dictionary from TOML file
            auto_discover: Whether to auto-discover plugins (legacy mode)
        """
        self.plugins: List[MercuryPlugin] = []
        self.plugin_classes: Dict[str, Type[MercuryPlugin]] = {}
        self.config = config or {}

        if config:
            # Config-based loading (new way)
            self._load_from_config(config)
        elif auto_discover:
            # Auto-discovery (legacy mode - only if explicitly requested)
            self._discover_plugins()
        # Otherwise, no plugins loaded (safe default)

    def _load_from_config(self, config: Dict[str, Any]) -> None:
        """Load plugins based on configuration.

        Args:
            config: Configuration dictionary with 'plugins' section
        """
        plugins_config = config.get("plugins", {})
        enabled_plugins = plugins_config.get("enabled", [])

        logger.info(f"Loading plugins from config: {enabled_plugins}")

        # Get plugin directory
        plugin_dir = Path(__file__).parent

        # Special case mappings for plugins where filename != plugin name
        plugin_file_map = {
            "learn": "learn/plugin.py",  # Learn plugin is in learn/ directory
        }

        for plugin_name in enabled_plugins:
            try:
                # Special handling for learn plugin (directory-based)
                if plugin_name == "learn":
                    # Import learn plugin using module import to handle relative imports
                    self._load_learn_plugin()
                else:
                    # Map plugin name to file (with special cases)
                    if plugin_name in plugin_file_map:
                        plugin_file = plugin_dir / plugin_file_map[plugin_name]
                    else:
                        plugin_file = plugin_dir / f"plugin_{plugin_name}.py"

                    if not plugin_file.exists():
                        logger.warning(f"Plugin file not found: {plugin_file}")
                        continue

                    # Load the plugin
                    self._load_plugin_file(plugin_file)

                # Apply config to loaded plugin
                if plugin_name in plugins_config:
                    plugin_settings = plugins_config[plugin_name]
                    for plugin in self.plugins:
                        if plugin.name == plugin_name:
                            # Apply settings from config
                            if "priority" in plugin_settings:
                                plugin.priority = plugin_settings["priority"]
                            if "audiences" in plugin_settings:
                                plugin.audiences = plugin_settings["audiences"]
                            if "complexity" in plugin_settings:
                                plugin.complexity_level = plugin_settings["complexity"]
                            break

            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin_name}': {e}")

        # Sort plugins by priority
        self.plugins.sort(key=lambda p: p.priority)

        logger.info(f"Successfully loaded {len(self.plugins)} plugins from config")

    def _discover_plugins(self) -> None:
        """Auto-discover and load all plugins from plugins directory."""
        plugin_dir = Path(__file__).parent

        # Find all plugin files (plugin_*.py)
        plugin_files = list(plugin_dir.glob("plugin_*.py"))

        logger.debug(f"Discovered {len(plugin_files)} plugin files")

        for plugin_file in plugin_files:
            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                logger.warning(f"Failed to load plugin {plugin_file.name}: {e}")

        # Sort plugins by priority (lower priority = loaded first)
        self.plugins.sort(key=lambda p: p.priority)

        logger.info(f"Loaded {len(self.plugins)} plugins: {[p.name for p in self.plugins]}")

    def _load_plugin_file(self, plugin_file: Path) -> None:
        """Load a single plugin file and extract plugin classes.

        Args:
            plugin_file: Path to plugin Python file
        """
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)

        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Could not load spec for {plugin_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find all MercuryPlugin subclasses in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, MercuryPlugin)
                and obj is not MercuryPlugin
                and not obj.__name__.startswith("_")
            ):
                # Instantiate the plugin
                try:
                    plugin_instance = obj()
                    if plugin_instance.name:  # Only add plugins with names
                        self.plugin_classes[plugin_instance.name] = obj
                        self.plugins.append(plugin_instance)
                        logger.debug(f"Loaded plugin: {plugin_instance.name}")
                    else:
                        logger.warning(f"Plugin class {obj.__name__} has no name, skipping")
                except Exception as e:
                    logger.error(f"Failed to instantiate plugin {obj.__name__}: {e}")

    def _load_learn_plugin(self) -> None:
        """Load the learn plugin using module import to handle relative imports."""
        try:
            from .learn.plugin import LearnPlugin

            plugin_instance = LearnPlugin()
            if plugin_instance.name:  # Only add plugins with names
                self.plugin_classes[plugin_instance.name] = LearnPlugin
                self.plugins.append(plugin_instance)
                logger.debug(f"Loaded plugin: {plugin_instance.name}")
            else:
                logger.warning(f"Learn plugin has no name, skipping")
        except Exception as e:
            logger.error(f"Failed to load learn plugin: {e}")
            raise

    def get_active_plugins(self, args: Namespace) -> List[MercuryPlugin]:
        """Get all plugins that are enabled for the current request.

        Args:
            args: Parsed command-line arguments

        Returns:
            List of active plugins, sorted by priority
        """
        active = []

        for plugin in self.plugins:
            try:
                if plugin.is_enabled(args):
                    active.append(plugin)
                    logger.debug(f"Plugin {plugin.name} is active")
                else:
                    logger.debug(f"Plugin {plugin.name} is disabled")
            except Exception as e:
                logger.warning(f"Error checking if plugin {plugin.name} is enabled: {e}")

        return active

    def get_handler_plugins(self, args: Namespace) -> List[MercuryPlugin]:
        """Get plugins that can handle the request completely.

        Args:
            args: Parsed command-line arguments

        Returns:
            List of plugins that can handle the request
        """
        handlers = []

        for plugin in self.get_active_plugins(args):
            try:
                if plugin.can_handle(args):
                    handlers.append(plugin)
                    logger.debug(f"Plugin {plugin.name} can handle request")
            except Exception as e:
                logger.warning(f"Error checking if plugin {plugin.name} can handle request: {e}")

        return handlers

    def register_all_arguments(self, parser) -> None:
        """Register arguments from all plugins.

        Args:
            parser: ArgumentParser to extend
        """
        # Add plugin listing argument
        parser.add_argument(
            "--list-plugins", action="store_true", help="List all available plugins and exit"
        )

        # Register arguments from each plugin
        for plugin in self.plugins:
            try:
                plugin.register_arguments(parser)
                logger.debug(f"Registered arguments for plugin: {plugin.name}")
            except Exception as e:
                logger.warning(f"Plugin {plugin.name} failed to register arguments: {e}")

    def list_plugins(
        self, current_profile: Optional[str] = None, config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get a formatted list of all available plugins with enhanced display.

        Args:
            current_profile: Current profile name (student/expert/agent)
            config: Configuration dictionary for showing enabled/disabled status

        Returns:
            Formatted string listing all plugins with colors and status
        """
        if not self.plugins:
            return "No plugins available."

        # Terminal colors
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[31m"
        BLUE = "\033[34m"
        CYAN = "\033[36m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"

        lines = [f"{BOLD}{CYAN}🎯 Mercury-Test Plugin Status{RESET}", ""]

        # Show current profile prominently
        if current_profile and current_profile != "unknown":
            profile_color = (
                GREEN
                if current_profile == "student"
                else BLUE if current_profile == "expert" else YELLOW
            )
            lines.append(
                f"{BOLD}📋 Current Profile: {profile_color}{current_profile.title()}{RESET}"
            )
            lines.append("")
        elif current_profile == "unknown":
            lines.append(f"{BOLD}📋 Current Profile: {DIM}Unknown (no config){RESET}")
            lines.append("")

        # Get enabled/disabled lists from config
        enabled_plugins = []
        disabled_plugins = []
        if config and "plugins" in config:
            enabled_plugins = config["plugins"].get("enabled", [])
            disabled_plugins = config["plugins"].get("disabled", [])

        lines.append(f"{BOLD}📦 Available Plugins:{RESET}")
        lines.append("")

        for plugin in self.plugins:
            # Determine status
            is_enabled = plugin.name in enabled_plugins
            is_disabled = plugin.name in disabled_plugins

            if is_enabled:
                status = f"{GREEN}✅{RESET}"
                name_color = GREEN
            elif is_disabled:
                status = f"{RED}❌{RESET}"
                name_color = DIM
            else:
                status = f"{YELLOW}⚠️{RESET}"
                name_color = YELLOW

            # Plugin name and priority
            lines.append(
                f"{status} {name_color}{BOLD}{plugin.name}{RESET} {DIM}(priority: {plugin.priority}){RESET}"
            )

            # Description
            if plugin.description:
                desc_color = "" if is_enabled else DIM
                lines.append(f"   {desc_color}{plugin.description}{RESET}")
            else:
                lines.append(f"   {DIM}No description available{RESET}")

            # Show audiences if available
            if hasattr(plugin, "audiences") and plugin.audiences:
                audience_str = ", ".join(plugin.audiences)
                lines.append(f"   {DIM}Audiences: {audience_str}{RESET}")

            lines.append("")

        # Show disabled plugins that aren't loaded
        if disabled_plugins:
            missing_disabled = [
                p for p in disabled_plugins if p not in [plugin.name for plugin in self.plugins]
            ]
            if missing_disabled:
                lines.append(f"{BOLD}❌ Disabled Plugins:{RESET}")
                for plugin_name in missing_disabled:
                    lines.append(f"{RED}❌ {plugin_name}{RESET} {DIM}(not loaded){RESET}")
                lines.append("")

        return "\n".join(lines)

    def get_plugin_by_name(self, name: str) -> MercuryPlugin:
        """Get a plugin instance by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance

        Raises:
            KeyError: If plugin not found
        """
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin

        raise KeyError(f"Plugin '{name}' not found")

    def enhance_discovery(self, base_discovery_func):
        """Apply all discovery enhancements from plugins.

        Args:
            base_discovery_func: Base discovery function

        Returns:
            Enhanced discovery function
        """
        enhanced_func = base_discovery_func

        # Apply enhancements from all plugins
        for plugin in self.plugins:
            try:
                enhanced_func = plugin.enhance_discovery(enhanced_func)
                logger.debug(f"Applied discovery enhancement from: {plugin.name}")
            except Exception as e:
                logger.warning(f"Plugin {plugin.name} failed to enhance discovery: {e}")

        return enhanced_func

    def run_pre_test_hooks(self, args: Namespace) -> None:
        """Run pre-test hooks from all active plugins.

        Args:
            args: Parsed command-line arguments
        """
        for plugin in self.get_active_plugins(args):
            try:
                plugin.pre_test_hook(args)
                logger.debug(f"Ran pre-test hook for: {plugin.name}")
            except Exception as e:
                logger.warning(f"Plugin {plugin.name} pre-test hook failed: {e}")

    def run_post_test_hooks(self, args: Namespace, result: int, elapsed: float) -> None:
        """Run post-test hooks from all active plugins.

        Args:
            args: Parsed command-line arguments
            result: Test exit code
            elapsed: Test execution time
        """
        for plugin in self.get_active_plugins(args):
            try:
                plugin.post_test_hook(args, result, elapsed)
                logger.debug(f"Ran post-test hook for: {plugin.name}")
            except Exception as e:
                logger.warning(f"Plugin {plugin.name} post-test hook failed: {e}")

    def __len__(self) -> int:
        """Number of loaded plugins."""
        return len(self.plugins)

    def __iter__(self):
        """Iterate over plugins."""
        return iter(self.plugins)
