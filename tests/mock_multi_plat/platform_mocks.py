"""Core platform mocking utilities for cross-platform testing.

This module provides decorators and context managers to mock different
operating systems, enabling comprehensive testing of platform-specific
code paths regardless of the host OS.
"""

import os
import sys
import platform
import tempfile
from pathlib import Path, PurePath, PureWindowsPath, PurePosixPath
from unittest.mock import patch, MagicMock, Mock, PropertyMock
from functools import wraps
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable, Union


def create_mock_path(target_platform: str):
    """Create a mock Path class for the target platform.
    
    Returns a class that behaves like Path but uses Pure paths
    that work cross-platform.
    """
    if target_platform == "Windows":
        base_class = PureWindowsPath
        from pathlib import _windows_flavour
        flavour = _windows_flavour
    else:
        base_class = PurePosixPath
        from pathlib import _posix_flavour
        flavour = _posix_flavour
    
    class MockPath(base_class):
        """Mock Path that works across platforms."""
        
        # Add _flavour attribute for pathlib compatibility
        _flavour = flavour
        
        def __new__(cls, *args, **kwargs):
            """Create new MockPath instance."""
            if args and len(args) == 1 and isinstance(args[0], str):
                # Handle string paths
                return base_class.__new__(cls, args[0])
            elif args:
                # Handle multiple path components
                return base_class.__new__(cls, *args)
            else:
                # Handle empty path
                return base_class.__new__(cls, '.')
        
        def exists(self):
            """Mock exists check."""
            str_path = str(self)
            
            if target_platform == "Windows":
                # Common Windows paths that should "exist"
                windows_paths = [
                    'C:\\Windows',
                    'C:\\Program Files',
                    'C:\\Users',
                    'D:\\a\\Django-Mercury-Performance-Testing',
                    'D:/a/Django-Mercury-Performance-Testing',
                ]
                return any(str_path.startswith(p) for p in windows_paths)
            elif target_platform == "Darwin":
                # Common macOS paths that should "exist"
                macos_paths = [
                    '/usr/local',
                    '/opt/homebrew',
                    '/System/Library',
                    '/Applications',
                    '/Users/runner/work',
                ]
                return any(str_path.startswith(p) for p in macos_paths)
            else:
                # Linux paths
                linux_paths = [
                    '/usr/local',
                    '/usr/lib',
                    '/home/runner/work',
                ]
                return any(str_path.startswith(p) for p in linux_paths)
        
        def is_dir(self):
            """Mock is_dir check."""
            return self.exists()
        
        def is_file(self):
            """Mock is_file check."""
            # For our mocking purposes, treat existing paths as files
            return self.exists() and not str(self).endswith('/')
        
        def glob(self, pattern):
            """Mock glob operation."""
            return []
        
        def resolve(self):
            """Mock resolve operation."""
            return self
        
        @classmethod
        def cwd(cls):
            """Mock current working directory."""
            if target_platform == "Windows":
                # Return Windows CI path when in CI
                if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
                    return cls("D:\\a\\Django-Mercury-Performance-Testing\\Django-Mercury-Performance-Testing")
                return cls("C:\\Users\\TestUser\\Mercury")
            elif target_platform == "Darwin":
                if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
                    return cls("/Users/runner/work/Django-Mercury-Performance-Testing/Django-Mercury-Performance-Testing")
                return cls("/Users/testuser/Mercury")
            else:
                if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
                    return cls("/home/runner/work/Django-Mercury-Performance-Testing/Django-Mercury-Performance-Testing")
                return cls("/home/testuser/Mercury")
    
    return MockPath


def get_current_platform() -> str:
    """Get the actual platform we're running on.
    
    Returns:
        'Windows', 'Darwin' (macOS), or 'Linux'
    """
    return platform.system()


def mock_platform(target_platform: str):
    """Decorator to mock a specific platform.
    
    Only mocks if we're NOT on that platform. If we're already on the
    target platform, the test runs normally without mocking.
    
    Args:
        target_platform: 'Windows', 'Darwin', or 'Linux'
    
    Example:
        @mock_platform("Windows")
        def test_windows_paths(self):
            # Runs with real behavior on Windows
            # Runs with mocked behavior on Linux/macOS
    """
    def decorator(test_func: Callable) -> Callable:
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            current = get_current_platform()
            
            if current == target_platform:
                # We're on the target platform - run test normally
                return test_func(*args, **kwargs)
            else:
                # We're on a different platform - mock it
                with PlatformMocker(target_platform) as mocker:
                    # Pass mocker as keyword argument if test accepts it
                    import inspect
                    sig = inspect.signature(test_func)
                    if 'platform_mocker' in sig.parameters:
                        kwargs['platform_mocker'] = mocker
                    return test_func(*args, **kwargs)
        return wrapper
    return decorator


class PlatformMocker:
    """Context manager for mocking different platforms.
    
    Provides comprehensive mocking of platform-specific behavior including:
    - platform.system() return value
    - sys.platform value
    - Environment variables
    - File system paths
    - Library loading behavior
    """
    
    def __init__(self, target_platform: str):
        """Initialize platform mocker.
        
        Args:
            target_platform: 'Windows', 'Darwin', or 'Linux'
        """
        self.target = target_platform
        self.patches = []
        self.original_values = {}
        
    def __enter__(self):
        """Enter context manager and apply mocks."""
        if self.target == "Windows":
            self._mock_windows()
        elif self.target == "Darwin":
            self._mock_macos()
        elif self.target == "Linux":
            self._mock_linux()
        return self
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and clean up mocks."""
        for p in reversed(self.patches):
            p.stop()
        self.patches.clear()
        
    def _mock_windows(self):
        """Mock Windows platform behavior."""
        # Mock platform.system()
        p1 = patch('platform.system', return_value='Windows')
        self.patches.append(p1)
        p1.start()
        
        # Mock sys.platform
        self.original_values['sys.platform'] = sys.platform
        sys.platform = 'win32'
        
        # Mock os.name
        p2 = patch('os.name', 'nt')
        self.patches.append(p2)
        p2.start()
        
        # Mock IS_WINDOWS flag in c_bindings
        p_flag = patch('django_mercury.python_bindings.c_bindings.IS_WINDOWS', True)
        self.patches.append(p_flag)
        p_flag.start()
        
        # Mock Windows-specific environment variables
        env_patch = patch.dict('os.environ', {
            'SYSTEMROOT': 'C:\\Windows',
            'PROGRAMFILES': 'C:\\Program Files',
            'PROGRAMFILES(X86)': 'C:\\Program Files (x86)',
            'WINDIR': 'C:\\Windows',
            'TEMP': 'C:\\Users\\TestUser\\AppData\\Local\\Temp',
            'TMP': 'C:\\Users\\TestUser\\AppData\\Local\\Temp',
        })
        self.patches.append(env_patch)
        env_patch.start()
        
        # Create Windows-aware MockPath class
        WindowsMockPath = create_mock_path("Windows")
        
        # Mock Path class to return WindowsMockPath
        p3 = patch('pathlib.Path', WindowsMockPath)
        self.patches.append(p3)
        p3.start()
        
        # Also patch imports that might use Path directly
        p4 = patch('django_mercury.python_bindings.c_bindings.Path', WindowsMockPath)
        self.patches.append(p4)
        p4.start()
        
        # Mock ctypes.CDLL to fail (Windows uses different mechanism)
        def windows_cdll_fail(name, *args, **kwargs):
            raise OSError("Windows cannot load .so files")
        
        p4 = patch('ctypes.CDLL', side_effect=windows_cdll_fail)
        self.patches.append(p4)
        p4.start()
        
        # Mock importlib to simulate .pyd imports
        self._mock_windows_imports()
        
    def _mock_windows_imports(self):
        """Mock Windows Python extension imports."""
        mock_modules = {}
        
        # Create mock C extension modules
        for module_name in ['django_mercury._c_analyzer', 
                           'django_mercury._c_metrics',
                           'django_mercury._c_orchestrator']:
            mock_module = MagicMock()
            mock_module.__name__ = module_name
            
            # Add mock functions
            if 'analyzer' in module_name:
                mock_module.analyze_query = Mock(return_value={'is_n_plus_one': False})
            elif 'metrics' in module_name:
                mock_module.start_performance_monitoring_enhanced = Mock(return_value=1)
                mock_module.stop_performance_monitoring_enhanced = Mock(return_value={
                    'response_time_ms': 10.5,
                    'query_count': 5
                })
            elif 'orchestrator' in module_name:
                mock_module.create_test_context = Mock(return_value=1)
                
            mock_modules[module_name] = mock_module
        
        def mock_import(name, *args, **kwargs):
            if name in mock_modules:
                return mock_modules[name]
            # Fall back to real import for other modules
            import importlib
            return importlib.__import__(name, *args, **kwargs)
        
        p = patch('importlib.import_module', side_effect=mock_import)
        self.patches.append(p)
        p.start()
        
    def _mock_macos(self):
        """Mock macOS platform behavior."""
        # Mock platform.system()
        p1 = patch('platform.system', return_value='Darwin')
        self.patches.append(p1)
        p1.start()
        
        # Mock sys.platform
        self.original_values['sys.platform'] = sys.platform
        sys.platform = 'darwin'
        
        # Mock os.name
        p2 = patch('os.name', 'posix')
        self.patches.append(p2)
        p2.start()
        
        # Mock platform.machine for Apple Silicon
        p3 = patch('platform.machine', return_value='arm64')
        self.patches.append(p3)
        p3.start()
        
        # Mock macOS-specific paths
        env_patch = patch.dict('os.environ', {
            'HOME': '/Users/testuser',
            'PATH': '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
            'TMPDIR': '/var/folders/xx/xxxxxxxxx/T/',
        })
        self.patches.append(env_patch)
        env_patch.start()
        
        # Create macOS-aware MockPath class
        MacOSMockPath = create_mock_path("Darwin")
        
        # Mock Path class to return MacOSMockPath
        p4 = patch('pathlib.Path', MacOSMockPath)
        self.patches.append(p4)
        p4.start()
        
        # Also patch imports that might use Path directly
        p5 = patch('django_mercury.python_bindings.c_bindings.Path', MacOSMockPath)
        self.patches.append(p5)
        p5.start()
        
        # Mock Path.exists for macOS paths
        def macos_path_exists(self):
            str_path = str(self)
            macos_paths = [
                '/usr/local/lib',
                '/opt/homebrew/lib',
                '/usr/lib',
                '/System/Library',
            ]
            return any(str_path.startswith(p) for p in macos_paths)
        
        p3 = patch.object(Path, 'exists', macos_path_exists)
        self.patches.append(p3)
        p3.start()
        
        # Mock platform.machine for Apple Silicon detection
        p4 = patch('platform.machine', return_value='arm64')
        self.patches.append(p4)
        p4.start()
        
    def _mock_linux(self):
        """Mock Linux platform behavior."""
        # Mock platform.system()
        p1 = patch('platform.system', return_value='Linux')
        self.patches.append(p1)
        p1.start()
        
        # Mock sys.platform
        self.original_values['sys.platform'] = sys.platform
        sys.platform = 'linux'
        
        # Mock os.name
        p2 = patch('os.name', 'posix')
        self.patches.append(p2)
        p2.start()
        
        # Mock Linux-specific paths
        env_patch = patch.dict('os.environ', {
            'HOME': '/home/testuser',
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'LD_LIBRARY_PATH': '/usr/local/lib:/usr/lib',
        })
        self.patches.append(env_patch)
        env_patch.start()
        
        # Create Linux-aware MockPath class
        LinuxMockPath = create_mock_path("Linux")
        
        # Mock Path class to return LinuxMockPath
        p3 = patch('pathlib.Path', LinuxMockPath)
        self.patches.append(p3)
        p3.start()
        
        # Also patch imports that might use Path directly
        p4 = patch('django_mercury.python_bindings.c_bindings.Path', LinuxMockPath)
        self.patches.append(p4)
        p4.start()
        
        # Mock successful ctypes loading for Linux
        mock_lib = MagicMock()
        mock_lib.start_monitoring = Mock(return_value=0)
        mock_lib.stop_monitoring = Mock(return_value=MagicMock())
        
        p5 = patch('ctypes.CDLL', return_value=mock_lib)
        self.patches.append(p5)
        p5.start()


class CIMocker:
    """Mock CI/CD environment variables and paths."""
    
    def __init__(self, ci_type: str = 'github_actions'):
        """Initialize CI mocker.
        
        Args:
            ci_type: Type of CI to mock ('github_actions', 'travis', 'jenkins')
        """
        self.ci_type = ci_type
        self.patches = []
        
    def __enter__(self):
        """Enter context and apply CI mocks."""
        if self.ci_type == 'github_actions':
            self._mock_github_actions()
        return self
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and clean up."""
        for p in reversed(self.patches):
            p.stop()
            
    def _mock_github_actions(self):
        """Mock GitHub Actions environment."""
        env_vars = {
            'CI': 'true',
            'GITHUB_ACTIONS': 'true',
            'GITHUB_WORKSPACE': '/home/runner/work/Django-Mercury-Performance-Testing/Django-Mercury-Performance-Testing',
            'GITHUB_RUN_ID': '123456789',
            'GITHUB_RUN_NUMBER': '42',
            'RUNNER_OS': 'Linux',
            'RUNNER_ARCH': 'X64',
        }
        
        p = patch.dict('os.environ', env_vars)
        self.patches.append(p)
        p.start()


@contextmanager
def mock_library_loading_failure():
    """Context manager to mock library loading failures."""
    with patch('ctypes.CDLL', side_effect=OSError("Library not found")):
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            yield


@contextmanager
def mock_c_extension_success():
    """Context manager to mock successful C extension loading."""
    # Create mock library
    mock_lib = MagicMock()
    mock_lib.initialize = Mock(return_value=0)
    mock_lib.cleanup = Mock(return_value=0)
    
    # Mock functions
    mock_lib.start_performance_monitoring_enhanced = Mock(return_value=1)
    mock_lib.stop_performance_monitoring_enhanced = Mock(return_value={
        'response_time_ms': 5.2,
        'query_count': 3,
        'memory_mb': 10.5
    })
    
    with patch('ctypes.CDLL', return_value=mock_lib):
        yield mock_lib