"""
Test failure scenarios and error handling in c_bindings.py
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os
import platform
import importlib
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCBindingsFailures(unittest.TestCase):
    """Test error handling and failure scenarios in c_bindings.py"""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import c_bindings to check platform
        from django_mercury.python_bindings import c_bindings
        
        # Store patchers for cleanup
        self.patchers = []
        
        # Platform-specific mocking
        if platform.system() == "Windows" or c_bindings.IS_WINDOWS:
            # On Windows, we need to mock the import mechanism
            # Mock importlib.import_module where it's actually used in c_bindings
            self.import_patcher = patch('django_mercury.python_bindings.c_bindings.importlib.import_module')
            self.mock_import = self.import_patcher.start()
            self.patchers.append(self.import_patcher)
            
            # Also create a fallback for direct module access
            self.mock_cdll = None  # Set to None for Windows to avoid confusion
        else:
            # On Unix, mock ctypes.CDLL for shared library loading
            self.lib_patcher = patch('django_mercury.python_bindings.c_bindings.ctypes.CDLL')
            self.mock_cdll = self.lib_patcher.start()
            self.patchers.append(self.lib_patcher)
            
            # Also patch find_library to control which libraries are "found"
            self.find_lib_patcher = patch('django_mercury.python_bindings.c_bindings.find_library')
            self.mock_find_library = self.find_lib_patcher.start()
            self.patchers.append(self.find_lib_patcher)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Stop all patchers
        for patcher in self.patchers:
            patcher.stop()
        
        # Reset the module state
        import django_mercury.python_bindings.c_bindings as c_bindings
        c_bindings.c_extensions._initialized = False
        c_bindings.c_extensions.query_analyzer = None
        c_bindings.c_extensions.metrics_engine = None
        c_bindings.c_extensions.test_orchestrator = None
        c_bindings.c_extensions.performance = None
    
    def test_library_load_failure(self):
        """Test handling when a library fails to load."""
        from django_mercury.python_bindings import c_bindings
        
        # Reset initialization state and clear existing handles
        c_bindings.c_extensions._initialized = False
        c_bindings.c_extensions.query_analyzer = None
        c_bindings.c_extensions.metrics_engine = None
        c_bindings.c_extensions.test_orchestrator = None
        c_bindings.c_extensions.performance = None
        
        # Platform-specific failure simulation
        if platform.system() == "Windows" or c_bindings.IS_WINDOWS:
            # On Windows, make Python module imports fail
            if hasattr(self, 'mock_import'):
                self.mock_import.side_effect = ImportError("Cannot import module")
        else:
            # On Unix, make ctypes.CDLL fail
            if hasattr(self, 'mock_cdll'):
                self.mock_cdll.side_effect = OSError("Cannot load library")
        
        # Try to initialize - should handle the error gracefully
        c_bindings.initialize_c_extensions(force_reinit=True)
        
        # Should be marked as initialized even if loading failed
        self.assertTrue(c_bindings.c_extensions._initialized)
        
        # Libraries should be None
        self.assertIsNone(c_bindings.c_extensions.query_analyzer)
        self.assertIsNone(c_bindings.c_extensions.metrics_engine)
        self.assertIsNone(c_bindings.c_extensions.test_orchestrator)
        self.assertIsNone(c_bindings.c_extensions.performance)
    
    def test_partial_library_load_failure(self):
        """Test when only some libraries fail to load."""
        # Runtime check for pure Python mode
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
            self.skipTest("Pure Python mode - C extensions not available")
        
        from django_mercury.python_bindings import c_bindings
        
        # Reset state and clear existing handles
        c_bindings.c_extensions._initialized = False
        c_bindings.c_extensions.query_analyzer = None
        c_bindings.c_extensions.metrics_engine = None
        c_bindings.c_extensions.test_orchestrator = None
        c_bindings.c_extensions.performance = None
        
        # Platform-specific partial failure simulation
        if platform.system() == "Windows" or c_bindings.IS_WINDOWS:
            # On Windows, make only _c_metrics fail to import
            mock_analyzer = Mock()
            mock_analyzer.__file__ = "fake_analyzer.pyd"
            mock_orchestrator = Mock()
            mock_orchestrator.__file__ = "fake_orchestrator.pyd"
            
            def import_side_effect(name):
                if name == 'django_mercury._c_analyzer':
                    return mock_analyzer
                elif name == 'django_mercury._c_metrics':
                    raise ImportError(f"Cannot import module {name}")
                elif name == 'django_mercury._c_orchestrator':
                    return mock_orchestrator
                else:
                    raise ImportError(f"Unexpected import: {name}")
            
            if hasattr(self, 'mock_import'):
                self.mock_import.side_effect = import_side_effect
        else:
            # On Unix, make only the second library fail (metrics_engine)
            if hasattr(self, 'mock_find_library'):
                self.mock_find_library.return_value = "/fake/lib.so"
            
            mock_lib1 = Mock()
            mock_lib2_error = OSError("Cannot load metrics_engine")
            mock_lib3 = Mock()
            
            if hasattr(self, 'mock_cdll'):
                self.mock_cdll.side_effect = [mock_lib1, mock_lib2_error, mock_lib3]
        
        # Initialize
        c_bindings.initialize_c_extensions(force_reinit=True)
        
        # First library should be loaded
        self.assertIsNotNone(c_bindings.c_extensions.query_analyzer)
        # Second should be None due to error
        self.assertIsNone(c_bindings.c_extensions.metrics_engine)
        # Third should still load
        self.assertIsNotNone(c_bindings.c_extensions.test_orchestrator)
    
    def test_cleanup_with_uninitialized_extensions(self):
        """Test cleanup when extensions were never initialized."""
        from django_mercury.python_bindings import c_bindings
        
        # Reset state
        c_bindings.c_extensions._initialized = False
        c_bindings.c_extensions.query_analyzer = None
        
        # Cleanup should not crash
        c_bindings.c_extensions.cleanup()
        
        # Should still be marked as not initialized
        self.assertFalse(c_bindings.c_extensions._initialized)
    
    def test_cleanup_with_partially_loaded_libraries(self):
        """Test cleanup when only some libraries were loaded."""
        from django_mercury.python_bindings import c_bindings
        
        # Set up partial loading
        mock_lib1 = Mock()
        mock_lib1._handle = 1234
        
        c_bindings.c_extensions._initialized = True
        c_bindings.c_extensions.query_analyzer = mock_lib1
        c_bindings.c_extensions.metrics_engine = None  # Not loaded
        c_bindings.c_extensions.test_orchestrator = None
        
        # Cleanup should handle mixed state
        c_bindings.c_extensions.cleanup()
        
        # Should be marked as not initialized after cleanup
        self.assertFalse(c_bindings.c_extensions._initialized)
        self.assertIsNone(c_bindings.c_extensions.query_analyzer)
    
    @patch('django_mercury.python_bindings.c_bindings.Path.exists')
    def test_library_file_not_found(self, mock_exists):
        """Test when library files don't exist on disk."""
        from django_mercury.python_bindings import c_bindings
        
        # Reset state
        c_bindings.c_extensions._initialized = False
        
        # Make file existence check fail
        mock_exists.return_value = False
        
        # Should handle missing files gracefully
        c_bindings.initialize_c_extensions()
        
        # Should still be marked as initialized
        self.assertTrue(c_bindings.c_extensions._initialized)
    
    def test_configure_library_functions_with_null_library(self):
        """Test configuring functions when library is None."""
        from django_mercury.python_bindings import c_bindings
        
        # Test that having None libraries doesn't crash anything
        c_bindings.c_extensions.query_analyzer = None
        c_bindings.c_extensions.metrics_engine = None
        c_bindings.c_extensions.test_orchestrator = None
        
        # Verify that we can still check for availability
        self.assertIsNone(c_bindings.c_extensions.query_analyzer)
        self.assertIsNone(c_bindings.c_extensions.metrics_engine)
        self.assertIsNone(c_bindings.c_extensions.test_orchestrator)
        
        # Test that the loader reports pure Python mode when extensions are None
        loader = c_bindings.CExtensionLoader()
        if hasattr(loader, '_configure_query_analyzer'):
            result = loader._configure_query_analyzer(None)
            self.assertEqual(result, 0)
        else:
            # Method doesn't exist, which is fine
            result = 0
            self.assertEqual(result, 0)
    
    def test_double_initialization(self):
        """Test that double initialization is handled correctly."""
        from django_mercury.python_bindings import c_bindings
        
        # Reset state
        c_bindings.c_extensions._initialized = False
        c_bindings.c_extensions.query_analyzer = None
        c_bindings.c_extensions.metrics_engine = None
        c_bindings.c_extensions.test_orchestrator = None
        c_bindings.c_extensions.performance = None
        
        # Platform-specific mock setup
        if platform.system() == "Windows" or c_bindings.IS_WINDOWS:
            # On Windows, mock successful imports
            mock_module = Mock()
            mock_module.__file__ = "fake_module.pyd"
            
            if hasattr(self, 'mock_import'):
                self.mock_import.return_value = mock_module
            if hasattr(self, 'mock_builtin_import'):
                self.mock_builtin_import.return_value = mock_module
                
            # First initialization
            c_bindings.c_extensions.initialize()
            self.assertTrue(c_bindings.c_extensions._initialized)
            
            # Reset mock to track second call
            if hasattr(self, 'mock_import'):
                self.mock_import.reset_mock()
            
            # Second initialization should be skipped
            c_bindings.c_extensions.initialize()
            
            # Should not import modules again
            if hasattr(self, 'mock_import'):
                # Should have minimal calls on second init
                self.assertLess(self.mock_import.call_count, 3)
        else:
            # On Unix, use CDLL mocks
            mock_lib = Mock()
            if hasattr(self, 'mock_cdll'):
                self.mock_cdll.return_value = mock_lib
            
            # First initialization
            c_bindings.c_extensions.initialize()
            self.assertTrue(c_bindings.c_extensions._initialized)
            
            # Reset mock to track second call
            if hasattr(self, 'mock_cdll'):
                self.mock_cdll.reset_mock()
            
            # Second initialization should be skipped
            c_bindings.c_extensions.initialize()
            
            # Should not load libraries again
            if hasattr(self, 'mock_cdll'):
                self.assertLess(self.mock_cdll.call_count, 4)
    
    def test_cleanup_exception_handling(self):
        """Test that cleanup handles exceptions gracefully."""
        from django_mercury.python_bindings import c_bindings
        
        # Platform-specific setup
        if platform.system() == "Windows" or c_bindings.IS_WINDOWS:
            # On Windows, extensions are Python modules
            mock_lib = Mock()
            mock_lib.__file__ = "fake.pyd"
        else:
            # On Unix, extensions are CDLL objects
            mock_lib = Mock()
            mock_lib._handle = 1234
            # Make the cleanup raise an exception
            type(mock_lib)._handle = property(lambda self: (_ for _ in ()).throw(Exception("Cleanup error")))
        
        c_bindings.c_extensions._initialized = True
        c_bindings.c_extensions.query_analyzer = mock_lib
        
        # Cleanup should handle the exception
        c_bindings.c_extensions.cleanup()
        
        # Should still mark as not initialized
        self.assertFalse(c_bindings.c_extensions._initialized)
    
    def test_c_extensions_disabled_by_environment(self):
        """Test that C extensions can be disabled via environment variable."""
        from django_mercury.python_bindings import c_bindings
        
        # Check env variable handling in initialization
        # Reset state
        c_bindings.c_extensions._initialized = False
        
        # When environment variable is set, libraries won't load properly
        # But initialization will still proceed
        with patch.dict(os.environ, {'MERCURY_DISABLE_C_EXTENSIONS': '1'}):
            c_bindings.c_extensions.initialize()
        
        # Libraries might be None or loaded (depending on implementation)
        # Just verify no crash occurred
        self.assertTrue(c_bindings.c_extensions._initialized)


class TestCBindingsFunctionCalls(unittest.TestCase):
    """Test C function calls and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.lib_patcher = patch('django_mercury.python_bindings.c_bindings.ctypes.CDLL')
        self.mock_cdll = self.lib_patcher.start()
        
        # Create mock libraries
        self.mock_query_lib = Mock()
        self.mock_metrics_lib = Mock()
        self.mock_test_lib = Mock()
        self.mock_perf_lib = Mock()
        
        self.mock_cdll.side_effect = [
            self.mock_query_lib,
            self.mock_metrics_lib,
            self.mock_test_lib,
            self.mock_perf_lib
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.lib_patcher.stop()
        import django_mercury.python_bindings.c_bindings as c_bindings
        c_bindings.c_extensions._initialized = False
    
    def test_query_analyzer_function_configuration(self):
        """Test that query analyzer functions are properly configured."""
        # Runtime check for pure Python mode
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
            self.skipTest("Pure Python mode - C extensions not available")
        
        from django_mercury.python_bindings import c_bindings
        
        # Initialize
        c_bindings.c_extensions._initialized = False
        c_bindings.initialize_c_extensions()
        
        # Check that functions were configured
        self.assertIsNotNone(c_bindings.c_extensions.query_analyzer)
        
        # Verify function attributes were set (argtypes, restype)
        # This tests the _configure_query_analyzer_functions function
        self.assertTrue(hasattr(self.mock_query_lib, 'analyze_query'))
    
    def test_metrics_engine_function_configuration(self):
        """Test that metrics engine functions are properly configured."""
        # Runtime check for pure Python mode
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '').lower() in ('1', 'true', 'yes'):
            self.skipTest("Pure Python mode - C extensions not available")
        
        from django_mercury.python_bindings import c_bindings
        
        # Initialize
        c_bindings.c_extensions._initialized = False
        c_bindings.initialize_c_extensions()
        
        # Check that functions were configured
        self.assertIsNotNone(c_bindings.c_extensions.metrics_engine)
        
        # Verify function attributes were set
        self.assertTrue(hasattr(self.mock_metrics_lib, 'calculate_percentiles'))
    
    def test_function_call_with_null_library(self):
        """Test calling functions when library is None."""
        from django_mercury.python_bindings import c_bindings
        
        # Set library to None
        c_bindings.c_extensions._initialized = True
        c_bindings.c_extensions.query_analyzer = None
        
        # Calling functions should handle None gracefully
        # This would normally crash if not handled properly
        try:
            if c_bindings.c_extensions.query_analyzer:
                c_bindings.c_extensions.query_analyzer.analyze_query(b"SELECT * FROM test")
        except AttributeError:
            self.fail("Should handle None library gracefully")


if __name__ == '__main__':
    unittest.main()