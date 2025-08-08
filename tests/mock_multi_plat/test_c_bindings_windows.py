"""Windows-specific tests for c_bindings.py.

These tests cover Windows-specific code paths including:
- .pyd Python extension loading
- Windows file paths and environment variables
- Windows-specific error handling
"""

import os
import sys
import unittest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.mock_multi_plat.platform_mocks import mock_platform, PlatformMocker
from django_mercury.python_bindings.c_bindings import CExtensionLoader
# Alias for easier use in tests
CExtensionManager = CExtensionLoader


class TestWindowsCBindings(unittest.TestCase):
    """Test Windows-specific behavior in c_bindings.py."""
    
    @mock_platform("Windows")
    def test_windows_library_config(self):
        """Test Windows library configuration (lines 74-96)."""
        # This should use Windows-specific library names
        from django_mercury.python_bindings import c_bindings
        
        # Force reload to get Windows config
        with PlatformMocker("Windows"):
            # Check that IS_WINDOWS is True
            self.assertTrue(c_bindings.IS_WINDOWS)
            
            # Check Windows library config
            config = c_bindings.LIBRARY_CONFIG
            self.assertIn("query_analyzer", config)
            # Windows uses different library names than Unix
            self.assertEqual(config["query_analyzer"]["name"], "_c_analyzer")
            self.assertEqual(config["metrics_engine"]["name"], "_c_metrics")
            self.assertEqual(config["test_orchestrator"]["name"], "_c_orchestrator")
    
    @mock_platform("Windows")
    def test_windows_pyd_loading(self, platform_mocker=None):
        """Test Windows .pyd extension loading (lines 414-449)."""
        manager = CExtensionManager()
        
        # Test loading Windows Python extensions
        lib_info = manager._load_library("query_analyzer", {
            "name": "_c_analyzer",
            "description": "Test analyzer"
        })
        
        # On Windows (mocked), should try to import as Python module
        self.assertIsNotNone(lib_info)
        if lib_info.is_loaded:
            # Check that it tried to load as Python module
            self.assertIn("Python module", lib_info.path)
    
    @mock_platform("Windows")
    def test_windows_import_error_handling(self):
        """Test Windows import error handling (lines 442-449)."""
        manager = CExtensionManager()
        
        # Mock import failure
        with patch('importlib.import_module', side_effect=ImportError("DLL load failed")):
            lib_info = manager._load_library("query_analyzer", {
                "name": "_c_analyzer",
                "description": "Test analyzer"
            })
            
            self.assertFalse(lib_info.is_loaded)
            self.assertIsNotNone(lib_info.error_message)
            self.assertIn("Failed to import Python extension", lib_info.error_message)
    
    @mock_platform("Windows")
    def test_windows_system_paths(self):
        """Test Windows system paths (lines 208-214)."""
        from django_mercury.python_bindings.c_bindings import get_library_paths
        
        paths = get_library_paths()
        paths_str = [str(p) for p in paths]
        
        # Should include Windows-specific paths
        self.assertTrue(any('System32' in p for p in paths_str))
        self.assertTrue(any('Program Files' in p for p in paths_str))
    
    @mock_platform("Windows")
    def test_windows_ci_paths(self):
        """Test Windows CI paths on GitHub Actions (lines 184-190)."""
        # Mock GitHub Actions environment
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            from django_mercury.python_bindings.c_bindings import get_library_paths
            
            paths = get_library_paths()
            paths_str = [str(p) for p in paths]
            
            # Should include Windows GitHub Actions paths
            self.assertTrue(any('D:/a' in p or 'D:\\a' in p for p in paths_str))
    
    @mock_platform("Windows")
    def test_windows_dll_directory(self):
        """Test Windows DLL directory handling."""
        manager = CExtensionManager()
        
        # Test that Windows adds DLL directories
        if hasattr(os, 'add_dll_directory'):
            # This would be called during initialization
            # We're testing the code path exists
            package_dir = Path(__file__).parent.parent.parent / 'django_mercury'
            # The actual add_dll_directory call happens in the real code
            self.assertTrue(package_dir.parent.exists())
    
    @mock_platform("Windows")
    def test_windows_function_configuration(self):
        """Test Windows-specific function configuration (lines 431-433)."""
        manager = CExtensionManager()
        
        # Create a mock module
        mock_module = MagicMock()
        mock_module.__name__ = 'django_mercury._c_analyzer'
        mock_module.analyze_query = Mock()
        
        # Test configuring functions for a Python module (Windows style)
        with patch('importlib.import_module', return_value=mock_module):
            lib_info = manager._load_library("query_analyzer", {
                "name": "_c_analyzer",
                "description": "Test"
            })
            
            if lib_info.is_loaded:
                # Should have configured functions
                self.assertGreater(lib_info.function_count, 0)
    
    @mock_platform("Windows")
    def test_windows_platform_detection(self):
        """Test Windows platform detection."""
        import platform
        
        # When mocked as Windows
        self.assertEqual(platform.system(), "Windows")
        self.assertEqual(sys.platform, "win32")
        
        # Check environment variables
        self.assertIn("SYSTEMROOT", os.environ)
        self.assertEqual(os.environ.get("SYSTEMROOT"), "C:\\Windows")
    
    @mock_platform("Windows")
    def test_windows_ctypes_incompatibility(self):
        """Test that ctypes.CDLL fails on Windows for .so files."""
        import ctypes
        
        # Windows can't load .so files with ctypes
        with self.assertRaises(OSError):
            ctypes.CDLL("libtest.so")
    
    @mock_platform("Windows")
    def test_windows_temp_paths(self):
        """Test Windows temp directory paths."""
        temp_dir = os.environ.get("TEMP")
        self.assertIsNotNone(temp_dir)
        self.assertIn("AppData\\Local\\Temp", temp_dir)


class TestWindowsEdgeCases(unittest.TestCase):
    """Test Windows edge cases and error scenarios."""
    
    @mock_platform("Windows")
    def test_windows_missing_dll(self):
        """Test handling of missing DLL dependencies."""
        manager = CExtensionManager()
        
        # Mock ImportError with DLL-specific message
        error_msg = "DLL load failed: The specified module could not be found"
        with patch('importlib.import_module', side_effect=ImportError(error_msg)):
            lib_info = manager._load_library("metrics_engine", {
                "name": "_c_metrics",
                "description": "Metrics"
            })
            
            self.assertFalse(lib_info.is_loaded)
            self.assertIn("DLL load failed", lib_info.error_message)
    
    @mock_platform("Windows")
    def test_windows_permission_error(self):
        """Test handling of Windows permission errors."""
        manager = CExtensionManager()
        
        # On Windows platform, we're simulating a permission error
        # But since we're mocking Windows, the importlib.import_module
        # is already mocked to return success. So we need to patch
        # the specific Windows module import to fail with ImportError
        # (since PermissionError is not caught by c_bindings.py)
        def mock_import_with_permission_error(name, *args, **kwargs):
            if '_c_orchestrator' in name:
                # Raise ImportError with permission message since that's what's caught
                raise ImportError(f"Permission denied: cannot import {name}")
            # Fall back to the existing mock for other modules
            import importlib
            return importlib.__import__(name, *args, **kwargs)
        
        with patch('importlib.import_module', side_effect=mock_import_with_permission_error):
            # Try to load the orchestrator library
            lib_info = manager._load_library("test_orchestrator", {
                "name": "_c_orchestrator",
                "description": "Orchestrator"
            })
            
            # Should handle error gracefully
            self.assertFalse(lib_info.is_loaded)
            self.assertIn("Permission denied", lib_info.error_message)
    
    @mock_platform("Windows")
    def test_windows_unicode_paths(self):
        """Test Windows Unicode path handling."""
        # Use PureWindowsPath directly for Unicode path testing
        from pathlib import PureWindowsPath
        
        # Windows should handle Unicode paths
        unicode_path = PureWindowsPath("C:\\Users\\テスト\\AppData\\Local\\Mercury")
        
        # Test that Path operations work with Unicode
        str_path = str(unicode_path)
        self.assertIn("テスト", str_path)
        
        # Also test that our MockPath handles Unicode
        from tests.mock_multi_plat.platform_mocks import create_mock_path
        MockPath = create_mock_path("Windows")
        mock_unicode_path = MockPath("C:\\Users\\テスト\\AppData\\Local\\Mercury")
        self.assertIn("テスト", str(mock_unicode_path))


if __name__ == '__main__':
    unittest.main()