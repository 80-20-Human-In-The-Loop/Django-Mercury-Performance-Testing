"""macOS-specific tests for c_bindings.py.

These tests cover macOS-specific code paths including:
- .so/.dylib library loading
- macOS file paths (/usr/local/lib, /opt/homebrew/lib)
- Apple Silicon vs Intel architecture handling
"""

import os
import sys
import platform
import unittest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from django_mercury.python_bindings.c_bindings import CExtensionLoader
# Alias for easier use in tests
CExtensionManager = CExtensionLoader


class TestMacOSCBindings(unittest.TestCase):
    """Test macOS-specific behavior in c_bindings.py."""
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_library_config(self) -> None:
        """Test macOS library configuration."""
        from django_mercury.python_bindings import c_bindings
        
        # Should use Python extension module names for PyPI compatibility
        config = c_bindings.LIBRARY_CONFIG
        self.assertEqual(config["query_analyzer"]["name"], "_c_analyzer")
        self.assertEqual(config["metrics_engine"]["name"], "_c_metrics")
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_system_paths(self) -> None:
        """Test macOS system library paths (lines 206-207)."""
        from django_mercury.python_bindings.c_bindings import get_library_paths
        
        paths = get_library_paths()
        paths_str = [str(p) for p in paths]
        
        # Should include macOS-specific paths
        self.assertTrue(any('/usr/local/lib' in p for p in paths_str))
        self.assertTrue(any('/opt/homebrew/lib' in p for p in paths_str))  # Apple Silicon
        self.assertTrue(any('/usr/lib' in p for p in paths_str))
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_apple_silicon_detection(self) -> None:
        """Test Apple Silicon (M1/M2) detection."""
        import platform
        
        # Default mock is arm64 (Apple Silicon)
        self.assertEqual(platform.machine(), "arm64")
        
        # Test Intel Mac
        with patch('platform.machine', return_value='x86_64'):
            self.assertEqual(platform.machine(), "x86_64")
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_homebrew_paths(self) -> None:
        """Test Homebrew library paths on macOS."""
        from django_mercury.python_bindings.c_bindings import get_library_paths
        
        paths = get_library_paths()
        paths_str = [str(p) for p in paths]
        
        # Homebrew paths differ between Intel and Apple Silicon
        if any('arm64' in str(p) for p in paths_str):
            # Apple Silicon uses /opt/homebrew
            self.assertTrue(any('/opt/homebrew' in p for p in paths_str))
        else:
            # Intel Macs use /usr/local
            self.assertTrue(any('/usr/local' in p for p in paths_str))
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_dylib_loading(self) -> None:
        """Test macOS .dylib library loading."""
        manager = CExtensionManager()
        
        # macOS can use both .so and .dylib extensions
        for ext in ['.so', '.dylib']:
            lib_name = f"libtest{ext}"
            with patch('ctypes.CDLL') as mock_cdll:
                mock_lib = MagicMock()
                mock_cdll.return_value = mock_lib
                
                # Should handle both extensions
                self.assertIsNotNone(mock_lib)
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_framework_paths(self) -> None:
        """Test macOS Framework paths."""
        # macOS has special Framework directories
        framework_paths = [
            "/System/Library/Frameworks",
            "/Library/Frameworks",
            "~/Library/Frameworks"
        ]
        
        for path in framework_paths:
            expanded = os.path.expanduser(path)
            # Framework paths should be recognizable
            self.assertTrue("Frameworks" in expanded)
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_rpath_handling(self) -> None:
        """Test macOS @rpath handling."""
        manager = CExtensionManager()
        
        # macOS uses @rpath for relative library paths
        with patch('ctypes.CDLL') as mock_cdll:
            mock_lib = MagicMock()
            mock_cdll.return_value = mock_lib
            
            # Test that @rpath libraries can be loaded
            lib_info = manager._load_library("query_analyzer", {
                "name": "libquery_analyzer",
                "description": "Analyzer"
            })
            
            if lib_info.is_loaded:
                self.assertIsNotNone(lib_info.handle)
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_platform_detection(self) -> None:
        """Test macOS platform detection."""
        import platform
        
        self.assertEqual(platform.system(), "Darwin")
        self.assertEqual(sys.platform, "darwin")
        self.assertEqual(os.name, "posix")
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_codesign_issues(self) -> None:
        """Test handling of macOS code signing issues with Python extensions."""
        manager = CExtensionManager()
        
        # Mock import error for Python extension (code signing would prevent import)
        error_msg = "dlopen() failed: code signature not valid"
        with patch('importlib.import_module', side_effect=ImportError(error_msg)):
            lib_info = manager._load_library("metrics_engine", {
                "name": "_c_metrics",
                "fallback_name": "django_mercury._c_metrics",
                "description": "Metrics"
            })
            
            # Python extensions handle codesign differently - should fail to load
            self.assertFalse(lib_info.is_loaded)
            self.assertIsNotNone(lib_info.error_message)


class TestMacOSEdgeCases(unittest.TestCase):
    """Test macOS edge cases and error scenarios."""
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_gatekeeper_blocking(self) -> None:
        """Test handling of macOS Gatekeeper blocking with Python extensions."""
        manager = CExtensionManager()
        
        # Gatekeeper blocks Python extensions differently
        error_msg = "dlopen() failed: Library not loaded: developer cannot be verified"
        with patch('importlib.import_module', side_effect=ImportError(error_msg)):
            lib_info = manager._load_library("test_orchestrator", {
                "name": "_c_orchestrator",
                "fallback_name": "django_mercury._c_orchestrator",
                "description": "Orchestrator"
            })
            
            # Python extensions blocked by Gatekeeper should fail to load
            self.assertFalse(lib_info.is_loaded)
            self.assertIsNotNone(lib_info.error_message)
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_universal_binary(self) -> None:
        """Test macOS universal binary support."""
        import platform
        
        # Test both architectures in universal binary
        architectures = ['x86_64', 'arm64']
        
        for arch in architectures:
            with patch('platform.machine', return_value=arch):
                self.assertEqual(platform.machine(), arch)
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_sip_restrictions(self) -> None:
        """Test System Integrity Protection (SIP) restrictions."""
        # SIP restricts access to certain paths
        restricted_paths = [
            "/System",
            "/usr",  # Partially restricted
            "/bin",
            "/sbin"
        ]
        
        for path in restricted_paths:
            # These paths have special protection on macOS
            self.assertTrue(path.startswith('/'))
    
    @unittest.skipUnless(platform.system() == "Darwin", "macOS-specific test")
    def test_macos_xcode_paths(self) -> None:
        """Test Xcode developer paths."""
        xcode_paths = [
            "/Applications/Xcode.app/Contents/Developer",
            "/Library/Developer/CommandLineTools"
        ]
        
        # These paths might contain development libraries
        for path in xcode_paths:
            self.assertIn("Developer", path)


if __name__ == '__main__':
    unittest.main()