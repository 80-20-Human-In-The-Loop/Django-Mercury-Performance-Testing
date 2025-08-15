"""
Discovery Utilities for Mercury-Test CLI

Shared utilities for finding manage.py files without plugin registration.
"""

from pathlib import Path
from typing import Optional
from argparse import Namespace


def find_manage_py(args: Optional[Namespace] = None) -> Optional[str]:
    """Find manage.py using smart discovery without plugin registration.
    
    This is a wrapper that creates a discovery plugin instance just for
    finding manage.py without registering command-line arguments.
    
    Args:
        args: Command line arguments (optional)
        
    Returns:
        Path to manage.py or None if not found
    """
    # Import here to avoid circular imports
    from django_mercury.cli.plugins.plugin_discovery import SmartDiscoveryPlugin
    
    # Create instance just for discovery (not for argument registration)
    discovery = SmartDiscoveryPlugin()
    
    # Use the smart discovery method
    return discovery.smart_find_manage_py(args)