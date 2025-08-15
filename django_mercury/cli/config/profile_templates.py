"""
Audience Profile Templates for Mercury

Defines the three core audiences and their default configurations:
- Students: Learning Django testing and performance
- Experts: Professional developers optimizing systems
- Agents: AI/LLM tools and automation
"""

from typing import Dict, Any, List

# Plugin configurations with audience mappings
PLUGIN_CONFIGS = {
    'wizard': {
        'audiences': ['student', 'expert'],
        'priority': 20,
        'complexity': 2,
        'description': 'Interactive test selection wizard',
        'settings': {
            'save_commands': True,
            'show_tips': True,
            'default_verbosity': 1,
        }
    },
    'visual_progress': {  # Correct plugin name
        'audiences': ['student', 'expert'],
        'priority': 50,
        'complexity': 2,
        'description': 'Rich visual feedback during test execution',
        'settings': {
            'theme': 'default',  # Options: default, minimal, detailed
            'refresh_rate_ms': 100,
            'show_memory_usage': True,
            'show_query_details': True,
        }
    },
    'discovery': {
        'audiences': ['student', 'expert'],
        'priority': 10,
        'complexity': 1,
        'description': 'Intelligent manage.py discovery with caching',
        'settings': {
            'cache_results': True,
            'cache_duration_minutes': 60,
            'search_depth': 3,
            'smart_detection': True,
        },
        'warning': 'Only enable if running from Django project root directory'
    },
    'learn': {
        'audiences': ['student'],
        'priority': 60,
        'complexity': 1,
        'description': 'Interactive learning with explanations and quizzes',
        'settings': {
            'quiz_enabled': True,
            'explain_level': 'detailed',  # Options: brief, normal, detailed
            'track_progress': True,
        }
    },
    'hints': {
        'audiences': ['student'],
        'priority': 90,
        'complexity': 1,
        'description': 'Show performance tips for slow tests',
        'settings': {
            'hint_threshold_seconds': 10.0,
            'show_random_tips': True,
            'max_hints_per_session': 5,
        }
    },
}

# Audience profile definitions
AUDIENCE_PROFILES = {
    'student': {
        'description': 'Learning-focused configuration for students and beginners',
        'long_description': (
            'Optimized for learning Django testing and performance optimization. '
            'Includes educational explanations, interactive tutorials, and helpful tips.'
        ),
        'enabled_plugins': ['discovery', 'wizard', 'learn', 'hints', 'visual_progress'],
        'disabled_plugins': [],  # All useful plugins enabled for students
        'settings': {
            'educational_mode': True,
            'verbosity': 2,
            'pause_on_errors': True,
            'show_tips': True,
            'save_command_history': True,
            'interactive': True,
        },
        'performance': {
            # More lenient thresholds for learning
            'response_time_ms': 300,
            'memory_overhead_mb': 75,
            'query_count_max': 30,
            'cache_hit_ratio_min': 0.5,
        }
    },
    'expert': {
        'description': 'Efficient configuration for experienced developers',
        'long_description': (
            'Optimized for professional development with fast execution and detailed metrics. '
            'Minimal interruptions, maximum information density.'
        ),
        'enabled_plugins': ['discovery', 'visual_progress', 'wizard'],
        'disabled_plugins': ['learn', 'hints'],  # Educational plugins disabled for experts
        'settings': {
            'educational_mode': False,
            'verbosity': 1,
            'pause_on_errors': False,
            'show_tips': False,
            'save_command_history': True,
            'interactive': True,
        },
        'performance': {
            # Strict thresholds for production
            'response_time_ms': 200,
            'memory_overhead_mb': 50,
            'query_count_max': 20,
            'cache_hit_ratio_min': 0.7,
        }
    },
    'agent': {
        'description': 'Structured output for AI agents and automation',
        'long_description': (
            'Designed for AI/LLM integration and CI/CD pipelines. '
            'Provides structured JSON output with no interactive elements.'
        ),
        'enabled_plugins': [],
        'disabled_plugins': ['wizard', 'visual_progress', 'discovery', 'learn', 'hints'],
        'settings': {
            'output_format': 'json',
            'batch_mode': True,
            'interactive': False,
            'verbosity': 0,
            'educational_mode': False,
            'pause_on_errors': False,
            'show_tips': False,
        },
        'performance': {
            # Standard thresholds for automation
            'response_time_ms': 250,
            'memory_overhead_mb': 60,
            'query_count_max': 25,
            'cache_hit_ratio_min': 0.6,
        }
    },
}

def get_profile_config(profile: str) -> Dict[str, Any]:
    """
    Get the configuration for a specific audience profile.
    
    Args:
        profile: One of 'student', 'expert', or 'agent'
        
    Returns:
        Complete configuration dictionary for the profile
        
    Raises:
        ValueError: If profile is not recognized
    """
    if profile not in AUDIENCE_PROFILES:
        raise ValueError(
            f"Unknown profile '{profile}'. "
            f"Valid profiles: {', '.join(AUDIENCE_PROFILES.keys())}"
        )
    
    return AUDIENCE_PROFILES[profile]

def get_plugins_for_audience(audience: str) -> List[str]:
    """
    Get all plugins that support a specific audience.
    
    Args:
        audience: One of 'student', 'expert', or 'agent'
        
    Returns:
        List of plugin names that support this audience
    """
    plugins = []
    for plugin_name, config in PLUGIN_CONFIGS.items():
        if audience in config.get('audiences', []):
            plugins.append(plugin_name)
    return plugins

def get_plugin_config(plugin_name: str) -> Dict[str, Any]:
    """
    Get the configuration for a specific plugin.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        Plugin configuration dictionary
        
    Raises:
        KeyError: If plugin is not found
    """
    if plugin_name not in PLUGIN_CONFIGS:
        raise KeyError(f"Unknown plugin '{plugin_name}'")
    
    return PLUGIN_CONFIGS[plugin_name]