"""
Mercury Configuration Generator

Generates default TOML configuration files for Mercury test runner.
Auto-detects the best profile based on project context.
"""

import os
import sys
import copy
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .profile_templates import (
    AUDIENCE_PROFILES,
    PLUGIN_CONFIGS,
    get_profile_config
)


class MercuryConfigGenerator:
    """Generates Mercury TOML configuration files."""
    
    def __init__(self, project_root: Path):
        """
        Initialize the config generator.
        
        Args:
            project_root: Path to Django project root (where manage.py lives)
        """
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "mercury_config.toml"
    
    def generate(self, profile: Optional[str] = None, interactive: bool = False) -> Dict[str, Any]:
        """
        Generate a complete Mercury configuration.
        
        Args:
            profile: Force a specific profile ('student', 'expert', 'agent')
            interactive: Whether to prompt user for choices
            
        Returns:
            Complete configuration dictionary ready for TOML serialization
        """
        if interactive:
            profile = self._interactive_setup()
        elif profile is None:
            profile = self.detect_best_profile()
            print(f"🔍 Auto-detected profile: '{profile}'")
        
        # Get base profile configuration
        profile_config = get_profile_config(profile)
        
        # Build complete configuration with proper nested structure
        # Use deepcopy to avoid circular references
        config = {
            'mercury': {
                'version': '1.0.0',
                'profile': profile,
                'project_root': '.',  # Relative to config file location
                'auto_update': True,  # Check for config schema updates
                'settings': copy.deepcopy(profile_config['settings']),
            },
            
            # Plugin configuration
            'plugins': {
                'enabled': list(profile_config['enabled_plugins']),  # Create new list
                'disabled': list(profile_config['disabled_plugins']),  # Create new list
            },
            
            # Profiles for reference (will be populated later)
            'profiles': {},
            
            # Performance thresholds
            'performance': copy.deepcopy(profile_config['performance']),
            
            # Project-specific section
            'project': {
                'name': self.project_root.name,
                'test_runner': 'django.test.runner.DiscoverRunner',
                'test_patterns': ['test*.py', '*_test.py', '*_tests.py'],
            }
        }
        
        # Add individual plugin configurations as nested dicts
        for plugin_name, plugin_cfg in PLUGIN_CONFIGS.items():
            config['plugins'][plugin_name] = {
                'audiences': list(plugin_cfg['audiences']),  # Create new list
                'priority': plugin_cfg['priority'],
                'complexity': plugin_cfg.get('complexity', 1),
                'description': plugin_cfg['description'],
            }
            
            # Add settings if present
            if 'settings' in plugin_cfg:
                config['plugins'][plugin_name]['settings'] = copy.deepcopy(plugin_cfg['settings'])
            
            # Add warning if present
            if 'warning' in plugin_cfg:
                config['plugins'][plugin_name]['warning'] = plugin_cfg['warning']
        
        # Add all profile templates for reference
        for profile_name, profile_data in AUDIENCE_PROFILES.items():
            config['profiles'][profile_name] = {
                'description': profile_data['description'],
                'enabled_plugins': list(profile_data['enabled_plugins']),
                'settings': copy.deepcopy(profile_data['settings']),
            }
        
        # Add performance by operation type
        config['performance']['by_operation'] = {
            'list_view': {
                'response_time_ms': 150,
                'query_count_max': 5,
            },
            'detail_view': {
                'response_time_ms': 80,
                'query_count_max': 3,
            },
            'search_view': {
                'response_time_ms': 250,
                'query_count_max': 8,
            },
            'create_view': {
                'response_time_ms': 120,
                'query_count_max': 6,
            },
        }
        
        return config
    
    def detect_best_profile(self) -> str:
        """
        Auto-detect the best profile based on project context.
        
        Returns:
            Profile name: 'student', 'expert', or 'agent'
        """
        # Check for CI/automation environment
        ci_indicators = [
            'CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS',
            'GITLAB_CI', 'JENKINS', 'TRAVIS', 'CIRCLECI',
            'BUILDKITE', 'DRONE', 'CODEBUILD'
        ]
        if any(os.getenv(indicator) for indicator in ci_indicators):
            return 'agent'
        
        # Check for learning/tutorial indicators
        if self._has_learning_indicators():
            return 'student'
        
        # Check for professional/production indicators
        if self._has_professional_indicators():
            return 'expert'
        
        # Default to student for new projects (educational first!)
        return 'student'
    
    def _has_learning_indicators(self) -> bool:
        """Check for indicators of a learning/educational project."""
        indicators = [
            'tutorial', 'learning', 'course', 'lesson', 'homework',
            'assignment', 'exercise', 'practice', 'student', 'education'
        ]
        
        # Check project name
        project_name = self.project_root.name.lower()
        if any(ind in project_name for ind in indicators):
            return True
        
        # Check for common learning files
        learning_files = [
            'README.tutorial.md', 'TUTORIAL.md', 'LEARNING.md',
            'tutorial.py', 'exercises.py', 'homework.py'
        ]
        for filename in learning_files:
            if (self.project_root / filename).exists():
                return True
        
        # Check if in a common learning directory structure
        path_parts = [p.lower() for p in self.project_root.parts]
        if any(ind in ' '.join(path_parts) for ind in indicators):
            return True
        
        return False
    
    def _has_professional_indicators(self) -> bool:
        """Check for indicators of a professional/production project."""
        indicators = [
            # Production config files
            '.env.production',
            'docker-compose.prod.yml',
            'Dockerfile',
            'requirements-prod.txt',
            # CI/CD files (but not running in CI)
            '.github/workflows',
            '.gitlab-ci.yml',
            'Jenkinsfile',
            # Professional tooling
            'Makefile',
            'tox.ini',
            '.pre-commit-config.yaml',
        ]
        
        for indicator in indicators:
            if (self.project_root / indicator).exists():
                return True
        
        # Check for large codebase (many Python files)
        py_files = list(self.project_root.rglob('*.py'))
        if len(py_files) > 100:  # Substantial codebase
            return True
        
        return False
    
    def _interactive_setup(self) -> str:
        """
        Interactive setup wizard for choosing profile.
        
        Returns:
            Selected profile name
        """
        print("\n🧙 Mercury Configuration Wizard")
        print("=" * 40)
        print("\nSelect your primary audience:\n")
        
        profiles = [
            ('student', '📚 Student', 'Learning Django testing and performance optimization'),
            ('expert', '⚡ Expert', 'Professional development with advanced features'),
            ('agent', '🤖 Agent', 'AI/LLM tools and CI/CD automation'),
        ]
        
        for i, (key, name, desc) in enumerate(profiles, 1):
            print(f"{i}. {name}")
            print(f"   {desc}\n")
        
        while True:
            try:
                choice = input("Your choice [1-3]: ").strip()
                if choice in ['1', '2', '3']:
                    profile_key = profiles[int(choice) - 1][0]
                    print(f"\n✅ Selected: {profiles[int(choice) - 1][1]}")
                    
                    # Ask about discovery plugin
                    if profile_key in ['student', 'expert']:
                        print("\n" + "=" * 40)
                        print("The 'discovery' plugin helps find manage.py automatically.")
                        print("⚠️  Note: Only enable if you'll run mercury-test from")
                        print("   your Django project root directory.\n")
                        
                        enable_discovery = input("Enable discovery plugin? [y/N]: ").strip().lower()
                        if enable_discovery in ['y', 'yes']:
                            print("✅ Discovery plugin will be enabled")
                            # This will be handled by the caller
                            self._enable_discovery = True
                        else:
                            print("⏭️  Discovery plugin will remain disabled")
                            self._enable_discovery = False
                    
                    return profile_key
                else:
                    print("Please enter 1, 2, or 3")
            except (ValueError, IndexError):
                print("Please enter 1, 2, or 3")
    
    def should_enable_discovery(self) -> bool:
        """Check if discovery should be enabled (set during interactive setup)."""
        return getattr(self, '_enable_discovery', False)