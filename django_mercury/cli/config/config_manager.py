"""
Mercury Configuration Manager

Manages loading, saving, and validation of Mercury TOML configurations.
Handles config file operations and profile management.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import toml
except ImportError:
    print("Error: toml package is required for Mercury configuration")
    print("Install with: pip install toml")
    sys.exit(1)

from .config_generator import MercuryConfigGenerator
from .profile_templates import AUDIENCE_PROFILES, PLUGIN_CONFIGS

logger = logging.getLogger(__name__)


class MercuryConfigManager:
    """Manages Mercury TOML configuration files."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            project_root: Path to Django project root. If None, will try to detect.
        """
        self.project_root = Path(project_root) if project_root else self._find_project_root()
        self.config_path = self.project_root / "mercury_config.toml" if self.project_root else None
        self.config: Dict[str, Any] = {}
        self._original_config: Dict[str, Any] = {}  # For detecting changes
    
    def _find_project_root(self) -> Optional[Path]:
        """
        Try to find the Django project root by looking for manage.py.
        
        Returns:
            Path to project root or None if not found
        """
        current = Path.cwd()
        
        # Check current directory and up to 3 parent directories
        for _ in range(4):
            if (current / 'manage.py').exists():
                return current
            if current == current.parent:
                break
            current = current.parent
        
        return None
    
    def load_or_create(self, profile: Optional[str] = None, 
                      interactive: bool = False) -> Dict[str, Any]:
        """
        Load existing config or create a new one.
        
        Args:
            profile: Force a specific profile for new configs
            interactive: Use interactive setup for new configs
            
        Returns:
            Loaded or newly created configuration
        """
        if not self.project_root:
            raise FileNotFoundError(
                "Could not find Django project root (no manage.py found). "
                "Please run from your Django project directory."
            )
        
        if self.config_path.exists():
            return self.load_config()
        else:
            return self.create_config(profile, interactive)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from TOML file.
        
        Returns:
            Parsed configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            toml.TomlDecodeError: If config file is invalid
        """
        if not self.config_path or not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = toml.load(f)
                self._original_config = self.config.copy()
                logger.info(f"Loaded config from {self.config_path}")
                return self.config
        except toml.TomlDecodeError as e:
            logger.error(f"Invalid TOML in {self.config_path}: {e}")
            raise
    
    def create_config(self, profile: Optional[str] = None, 
                     interactive: bool = False) -> Dict[str, Any]:
        """
        Create a new configuration file.
        
        Args:
            profile: Force a specific profile
            interactive: Use interactive setup
            
        Returns:
            Newly created configuration
        """
        generator = MercuryConfigGenerator(self.project_root)
        self.config = generator.generate(profile, interactive)
        
        # Handle discovery plugin if selected during interactive setup
        if interactive and generator.should_enable_discovery():
            if 'discovery' in self.config['plugins']['disabled']:
                self.config['plugins']['disabled'].remove('discovery')
            if 'discovery' not in self.config['plugins']['enabled']:
                self.config['plugins']['enabled'].append('discovery')
        
        self.save_config()
        
        # Print creation message
        profile_name = self.config['mercury']['profile']
        print(f"✨ Created mercury_config.toml with '{profile_name}' profile")
        print(f"📁 Location: {self.config_path}")
        
        # Profile-specific messages
        if profile_name == 'student':
            print("📚 Educational mode activated - you'll get explanations and tips!")
            print("🎓 Plugins enabled: " + ", ".join(self.config['plugins']['enabled']))
        elif profile_name == 'expert':
            print("⚡ Expert mode activated - optimized for speed and efficiency!")
            print("🔧 Plugins enabled: " + ", ".join(self.config['plugins']['enabled']))
        elif profile_name == 'agent':
            print("🤖 Agent mode activated - structured output for automation!")
            print("📊 JSON output enabled for CI/CD integration")
        
        return self.config
    
    def save_config(self) -> None:
        """
        Save current configuration to TOML file.
        
        Raises:
            IOError: If unable to write config file
        """
        if not self.config_path:
            raise IOError("No config path set")
        
        try:
            # No need to clean None values anymore since we don't use them
            
            with open(self.config_path, 'w') as f:
                # Write header comments
                f.write("# Mercury Test Configuration\n")
                f.write(f"# Auto-generated for: {self.project_root}\n")
                f.write("# Documentation: https://github.com/80-20-Human-In-The-Loop/Django-Mercury\n")
                f.write("# \n")
                f.write("# Plugins are loaded ONLY from this configuration\n")
                f.write("# No auto-discovery - you must explicitly enable plugins here\n\n")
                
                # Write main config
                try:
                    toml.dump(self.config, f)
                except (TypeError, ValueError) as e:
                    print(f"❌ Error: Invalid configuration structure for TOML")
                    print(f"   Details: {e}")
                    logger.error(f"TOML serialization error: {e}")
                    raise IOError(f"Could not serialize config to TOML: {e}")
                
            # Verify file was actually created
            if not self.config_path.exists():
                raise IOError(f"Config file was not created at {self.config_path}")
                
            logger.info(f"Saved config to {self.config_path}")
            
        except IOError:
            raise  # Re-raise IOError as-is
        except Exception as e:
            logger.error(f"Unexpected error saving config: {e}")
            print(f"❌ Unexpected error saving config: {e}")
            raise IOError(f"Could not save config to {self.config_path}: {e}")
    
    def _clean_for_toml(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean configuration for TOML serialization.
        
        Note: Since we no longer use None values or comment keys,
        this method is kept for backwards compatibility but
        essentially just returns the config as-is.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration ready for TOML (currently unchanged)
        """
        # No cleaning needed with the new structure
        return config
    
    def get_profile(self) -> str:
        """
        Get the current profile name.
        
        Returns:
            Profile name ('student', 'expert', or 'agent')
        """
        return self.config.get('mercury', {}).get('profile', 'student')
    
    def set_profile(self, profile: str, save: bool = True) -> None:
        """
        Switch to a different profile.
        
        Args:
            profile: New profile name
            save: Whether to save changes immediately
            
        Raises:
            ValueError: If profile is invalid
        """
        if profile not in AUDIENCE_PROFILES:
            raise ValueError(
                f"Invalid profile '{profile}'. "
                f"Valid profiles: {', '.join(AUDIENCE_PROFILES.keys())}"
            )
        
        # Update configuration with new profile
        profile_config = AUDIENCE_PROFILES[profile]
        
        self.config['mercury']['profile'] = profile
        self.config['mercury']['settings'] = profile_config['settings']
        self.config['plugins']['enabled'] = profile_config['enabled_plugins'].copy()
        self.config['plugins']['disabled'] = profile_config['disabled_plugins'].copy()
        self.config['performance'] = profile_config['performance']
        
        if save:
            self.save_config()
        
        print(f"✅ Switched to '{profile}' profile")
    
    def get_enabled_plugins(self) -> List[str]:
        """
        Get list of enabled plugins.
        
        Returns:
            List of enabled plugin names
        """
        return self.config.get('plugins', {}).get('enabled', [])
    
    def get_disabled_plugins(self) -> List[str]:
        """
        Get list of disabled plugins.
        
        Returns:
            List of disabled plugin names
        """
        return self.config.get('plugins', {}).get('disabled', [])
    
    def enable_plugin(self, plugin_name: str, save: bool = True) -> None:
        """
        Enable a specific plugin.
        
        Args:
            plugin_name: Name of plugin to enable
            save: Whether to save changes immediately
            
        Raises:
            ValueError: If plugin is unknown
        """
        if plugin_name not in PLUGIN_CONFIGS:
            raise ValueError(f"Unknown plugin '{plugin_name}'")
        
        # Remove from disabled if present
        disabled = self.config.get('plugins', {}).get('disabled', [])
        if plugin_name in disabled:
            disabled.remove(plugin_name)
        
        # Add to enabled if not present
        enabled = self.config.get('plugins', {}).get('enabled', [])
        if plugin_name not in enabled:
            enabled.append(plugin_name)
        
        if save:
            self.save_config()
        
        # Show warning for discovery plugin
        if plugin_name == 'discovery':
            print("⚠️  Note: Discovery plugin only works when running from project root")
        
        print(f"✅ Enabled plugin '{plugin_name}'")
    
    def disable_plugin(self, plugin_name: str, save: bool = True) -> None:
        """
        Disable a specific plugin.
        
        Args:
            plugin_name: Name of plugin to disable
            save: Whether to save changes immediately
            
        Raises:
            ValueError: If plugin is unknown
        """
        if plugin_name not in PLUGIN_CONFIGS:
            raise ValueError(f"Unknown plugin '{plugin_name}'")
        
        # Remove from enabled if present
        enabled = self.config.get('plugins', {}).get('enabled', [])
        if plugin_name in enabled:
            enabled.remove(plugin_name)
        
        # Add to disabled if not present
        disabled = self.config.get('plugins', {}).get('disabled', [])
        if plugin_name not in disabled:
            disabled.append(plugin_name)
        
        if save:
            self.save_config()
        
        print(f"✅ Disabled plugin '{plugin_name}'")
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration dictionary
        """
        return self.config.get('plugins', {}).get(plugin_name, {})
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get Mercury settings.
        
        Returns:
            Settings dictionary
        """
        return self.config.get('mercury', {}).get('settings', {})
    
    def get_performance_thresholds(self) -> Dict[str, Any]:
        """
        Get performance thresholds.
        
        Returns:
            Performance thresholds dictionary
        """
        return self.config.get('performance', {})
    
    def validate_config(self) -> List[str]:
        """
        Validate the current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required sections
        if 'mercury' not in self.config:
            errors.append("Missing 'mercury' section")
        
        if 'plugins' not in self.config:
            errors.append("Missing 'plugins' section")
        
        # Check profile
        profile = self.get_profile()
        if profile not in AUDIENCE_PROFILES:
            errors.append(f"Invalid profile '{profile}'")
        
        # Check for plugin conflicts
        enabled = set(self.get_enabled_plugins())
        disabled = set(self.get_disabled_plugins())
        conflicts = enabled & disabled
        if conflicts:
            errors.append(f"Plugins in both enabled and disabled: {conflicts}")
        
        # Check for unknown plugins
        all_plugins = enabled | disabled
        known_plugins = set(PLUGIN_CONFIGS.keys())
        unknown = all_plugins - known_plugins
        if unknown:
            errors.append(f"Unknown plugins: {unknown}")
        
        return errors