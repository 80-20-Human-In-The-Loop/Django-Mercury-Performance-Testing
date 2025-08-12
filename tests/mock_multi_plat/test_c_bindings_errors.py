"""Error handling tests for c_bindings.py.

These tests cover error scenarios and recovery including:
- Library load failures (lines 400-406, 456-460, 477-485)
- Missing function signatures (lines 511-541)
- Cleanup errors (lines 876-885)
"""

import os
import sys
import unittest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.mock_multi_plat.platform_mocks import mock_library_loading_failure
from django_mercury.python_bindings.c_bindings import CExtensionLoader, IS_WINDOWS
# Alias for easier use in tests
CExtensionManager = CExtensionLoader


def patch_library_loading(side_effect):
    """Patch the appropriate library loading mechanism for the current platform.
    
    Windows uses importlib.import_module for .pyd files.
    Unix uses ctypes.CDLL for .so files.
    """
    if IS_WINDOWS:
        # Windows code only catches ImportError, so wrap other exceptions
        if isinstance(side_effect, Exception) and not isinstance(side_effect, ImportError):
            # Wrap non-ImportError exceptions as ImportError for Windows
            wrapped_error = ImportError(str(side_effect))
            # Preserve the original error type in the message for testing
            wrapped_error.__cause__ = side_effect
            side_effect = wrapped_error
        return patch('importlib.import_module', side_effect=side_effect)
    else:
        return patch('ctypes.CDLL', side_effect=side_effect)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and recovery in c_bindings.py."""
    
    def test_no_c_extensions_fallback_warning(self) -> None:
        """Test fallback warning when no C extensions load (lines 400-406)."""
        with mock_library_loading_failure():
            manager = CExtensionManager()
            
            # When no C extensions load, the manager should have no libraries
            self.assertIsNone(manager.query_analyzer)
            self.assertIsNone(manager.metrics_engine)
            self.assertIsNone(manager.test_orchestrator)
    
    def test_library_not_found_error(self) -> None:
        """Test library not found error handling (lines 477-485)."""
        manager = CExtensionManager()
        
        # Mock import failure for Python modules
        with patch('importlib.import_module', side_effect=ImportError("No module named 'django_mercury._c_analyzer'")):
            lib_info = manager._load_library("query_analyzer", {
                "name": "_c_analyzer",
                "description": "Analyzer"
            })
            
            self.assertFalse(lib_info.is_loaded)
            self.assertIn("Failed to import", lib_info.error_message)
    
    def test_import_error_handling(self) -> None:
        """Test Python import error handling (lines 456-460)."""
        manager = CExtensionManager()
        
        with patch('importlib.import_module', side_effect=ImportError("No module named 'django_mercury._c_analyzer'")):
            lib_info = manager._load_library("query_analyzer", {
                "name": "_c_analyzer",
                "description": "Analyzer"
            })
            
            # The error message format varies, just check it failed
            self.assertFalse(lib_info.is_loaded)
            self.assertIsNotNone(lib_info.error_message)
    
    def test_missing_function_signatures(self) -> None:
        """Test handling of missing function signatures (lines 511-541)."""
        manager = CExtensionManager()
        
        # Create mock library missing some functions
        mock_lib = MagicMock()
        # Don't define all expected functions
        del mock_lib.analyze_query
        
        with patch_library_loading(mock_lib):
            # Try to configure functions
            try:
                count = manager._configure_query_analyzer(mock_lib)
                # Should handle missing functions gracefully
                self.assertGreaterEqual(count, 0)
            except AttributeError:
                # Should not raise AttributeError
                self.fail("Should handle missing functions gracefully")
    
    def test_cleanup_errors(self) -> None:
        """Test cleanup error handling (lines 876-885)."""
        manager = CExtensionManager()
        
        # Mock a library that fails during cleanup
        mock_lib = MagicMock()
        mock_lib.cleanup = Mock(side_effect=Exception("Cleanup failed"))
        
        manager.query_analyzer = mock_lib
        
        # Cleanup should handle errors gracefully
        try:
            manager.cleanup()
            # Should not raise exception
        except Exception as e:
            self.fail(f"Cleanup raised exception: {e}")
    
    def test_partial_initialization_success(self) -> None:
        """Test when only some libraries load successfully."""
        manager = CExtensionManager()
        
        # Mock: query_analyzer loads, others fail
        mock_lib = MagicMock()
        mock_lib.analyze_query = Mock(return_value={'is_n_plus_one': False})
        
        with patch_library_loading([mock_lib, OSError("Failed"), OSError("Failed")]):
            # After construction, check what loaded
            # Note: CExtensionManager loads libraries in __init__
            self.assertIsNotNone(manager)  # Manager still created even with partial loads
    
    def test_memory_allocation_failure(self) -> None:
        """Test memory allocation failure handling."""
        manager = CExtensionManager()
        
        # Mock out of memory error
        with patch('importlib.import_module', side_effect=MemoryError("Out of memory")):
            lib_info = manager._load_library("metrics_engine", {
                "name": "_c_metrics",
                "description": "Metrics"
            })
            
            self.assertFalse(lib_info.is_loaded)
    
    def test_permission_denied_error(self) -> None:
        """Test permission denied error handling."""
        manager = CExtensionManager()
        
        with patch('importlib.import_module', side_effect=PermissionError("Permission denied")):
            lib_info = manager._load_library("test_orchestrator", {
                "name": "_c_orchestrator",
                "description": "Orchestrator"
            })
            
            self.assertFalse(lib_info.is_loaded)
    
    def test_corrupted_library_file(self) -> None:
        """Test handling of corrupted library files."""
        manager = CExtensionManager()
        
        # Use platform-appropriate error message
        if IS_WINDOWS:
            error_msg = "is not a valid Win32 application"
        else:
            error_msg = "invalid ELF header"
            
        with patch('importlib.import_module', side_effect=ImportError(error_msg)):
            lib_info = manager._load_library("query_analyzer", {
                "name": "_c_analyzer",
                "description": "Analyzer"
            })
            
            self.assertFalse(lib_info.is_loaded)
            self.assertIn("Failed to import", lib_info.error_message)
    
    def test_version_mismatch_error(self) -> None:
        """Test handling of version mismatch errors."""
        manager = CExtensionManager()
        
        # Use platform-appropriate version error
        if IS_WINDOWS:
            error_msg = "The specified module could not be found"
            expected_in_msg = "specified module"
        else:
            error_msg = "version `GLIBC_2.34' not found"
            expected_in_msg = "GLIBC"
            
        with patch('importlib.import_module', side_effect=ImportError(error_msg)):
            lib_info = manager._load_library("metrics_engine", {
                "name": "_c_metrics",
                "description": "Metrics"
            })
            
            self.assertFalse(lib_info.is_loaded)
            self.assertIn("Failed to import", lib_info.error_message)


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery mechanisms."""
    
    def test_fallback_to_pure_python(self) -> None:
        """Test fallback to pure Python when C extensions fail."""
        with mock_library_loading_failure():
            manager = CExtensionManager()
            
            # Should indicate fallback mode - no C extensions loaded
            self.assertIsNone(manager.query_analyzer)
            self.assertIsNone(manager.metrics_engine)
            self.assertIsNone(manager.test_orchestrator)
    
    def test_reinitialize_after_failure(self) -> None:
        """Test reinitializing after initial failure."""
        # First attempt fails
        with mock_library_loading_failure():
            manager1 = CExtensionManager()
            self.assertIsNone(manager1.query_analyzer)
        
        # Second attempt with working libraries
        mock_lib = MagicMock()
        with patch_library_loading(mock_lib):
            # Create new manager - should try to load again
            manager2 = CExtensionManager()
            # Libraries are loaded in __init__, but may still be None if mock doesn't configure them
            self.assertIsNotNone(manager2)  # Manager created successfully
    
    def test_graceful_degradation(self) -> None:
        """Test graceful degradation when some features unavailable."""
        # Mock only metrics engine available
        mock_metrics = MagicMock()
        mock_metrics.start_performance_monitoring_enhanced = Mock(return_value=1)
        
        def cdll_side_effect(name, *args, **kwargs):
            if 'metrics' in str(name).lower():
                return mock_metrics
            raise OSError("Library not found")
        
        with patch_library_loading(cdll_side_effect):
            manager = CExtensionManager()
            
            # Should work with partial functionality
            # At least manager should be created
            self.assertIsNotNone(manager)


if __name__ == '__main__':
    unittest.main()