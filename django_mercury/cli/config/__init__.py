"""
Mercury Configuration System

Manages TOML-based configuration for Mercury test runner.
Supports three audience profiles: student, expert, and agent.
"""

from .config_manager import MercuryConfigManager
from .config_generator import MercuryConfigGenerator
from .profile_templates import AUDIENCE_PROFILES

__all__ = [
    "MercuryConfigManager",
    "MercuryConfigGenerator",
    "AUDIENCE_PROFILES",
]
