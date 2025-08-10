"""
Utility functions for educational mode.
"""

import os
import sys


def is_interactive_environment() -> bool:
    """Check if we're in an interactive environment where we can get user input.
    
    Returns False if:
    - stdin is not a tty (piped input, CI environment)
    - MERCURY_NON_INTERACTIVE is set
    - CI environment variables are detected
    - Running under pytest without capturing disabled
    
    Returns:
        True if we can safely prompt for user input, False otherwise
    """
    # Check for explicit non-interactive flag
    if os.environ.get('MERCURY_NON_INTERACTIVE', '').lower() in ('1', 'true', 'yes'):
        return False
    
    # Check for CI environments
    ci_env_vars = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS']
    if any(os.environ.get(var) for var in ci_env_vars):
        return False
    
    # Check if stdin is available and is a terminal
    if not hasattr(sys.stdin, 'isatty'):
        return False
    
    try:
        # Check if stdin is a tty (terminal)
        if not sys.stdin.isatty():
            return False
    except (AttributeError, ValueError):
        # Some environments don't have proper isatty
        return False
    
    # Check if we're in pytest with capture enabled
    # pytest captures stdin by default unless --capture=no is used
    if 'pytest' in sys.modules:
        import pytest
        config = pytest.config if hasattr(pytest, 'config') else None
        if config and config.getoption('capture') != 'no':
            return False
    
    # Check if stdin is closed or not readable
    if sys.stdin.closed:
        return False
    
    return True


def safe_input(prompt: str, default: str = "") -> str:
    """Safely get input from user, returning default if not interactive.
    
    Args:
        prompt: The prompt to show the user
        default: Default value if input is not available
        
    Returns:
        User input or default value
    """
    if not is_interactive_environment():
        return default
    
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return default
    except Exception:
        # Any other exception, just return default
        return default


def safe_confirm(prompt: str, default: bool = True) -> bool:
    """Safely get yes/no confirmation from user.
    
    Args:
        prompt: The prompt to show the user
        default: Default value if input is not available
        
    Returns:
        True for yes, False for no, or default if not interactive
    """
    if not is_interactive_environment():
        return default
    
    try:
        response = input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
        if not response:
            return default
        return response in ('y', 'yes', 'true', '1')
    except (EOFError, KeyboardInterrupt):
        return default
    except Exception:
        return default