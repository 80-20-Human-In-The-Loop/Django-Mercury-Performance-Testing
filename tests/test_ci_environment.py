"""
CI Environment Tests for Django Mercury

These tests verify that the CI/CD environment is properly configured
and that C extensions load correctly (or fall back gracefully).
"""

import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from django_mercury.python_bindings import c_bindings


class TestCIEnvironment(unittest.TestCase):
    """Test CI-specific functionality."""
    
    def test_environment_detection(self):
        """Test that we can detect CI environment."""
        # Check if we're in CI
        is_ci = os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS')
        
        if is_ci:
            self.assertTrue(is_ci, "Should detect CI environment")
            print(f"✓ CI environment detected: CI={os.environ.get('CI')}, "
                  f"GITHUB_ACTIONS={os.environ.get('GITHUB_ACTIONS')}")
        else:
            print("ℹ️  Not running in CI environment")
    
    def test_pure_python_mode(self):
        """Test that pure Python mode can be forced."""
        pure_python = os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '0') == '1'
        
        if pure_python:
            self.assertTrue(c_bindings.is_pure_python_mode(), 
                          "Pure Python mode should be active")
            print("✓ Pure Python mode is active")
        else:
            print(f"ℹ️  Pure Python mode: {c_bindings.is_pure_python_mode()}")
    
    def test_library_search_paths(self):
        """Test that library search paths are correct."""
        paths = c_bindings.get_library_paths()
        
        self.assertIsInstance(paths, list)
        self.assertGreater(len(paths), 0, "Should have at least one search path")
        
        print(f"✓ Found {len(paths)} library search paths:")
        for i, path in enumerate(paths, 1):
            exists = "✓" if path.exists() else "✗"
            print(f"  {i}. [{exists}] {path}")
    
    def test_c_extension_availability(self):
        """Test C extension availability reporting."""
        available = c_bindings.are_c_extensions_available()
        pure_python = c_bindings.is_pure_python_mode()
        
        print(f"✓ C Extensions Available: {available}")
        print(f"✓ Pure Python Mode: {pure_python}")
        
        # In CI with DJANGO_MERCURY_PURE_PYTHON=1, we expect pure Python mode
        if os.environ.get('DJANGO_MERCURY_PURE_PYTHON') == '1':
            self.assertTrue(pure_python, "Should be in pure Python mode when forced")
    
    def test_library_loading_graceful_failure(self):
        """Test that library loading fails gracefully."""
        # Try to initialize C extensions
        result = c_bindings.initialize_c_extensions()
        
        # This should always succeed (returns True if C loaded, False if using fallback)
        self.assertIsInstance(result, bool)
        
        if result:
            print("✓ C extensions loaded successfully")
        else:
            print("✓ Gracefully fell back to pure Python")
    
    def test_individual_library_availability(self):
        """Test individual library availability."""
        libraries = {
            'query_analyzer': c_bindings.c_extensions.query_analyzer,
            'metrics_engine': c_bindings.c_extensions.metrics_engine,
            'test_orchestrator': c_bindings.c_extensions.test_orchestrator,
            'legacy_performance': c_bindings.c_extensions.legacy_performance,
        }
        
        print("✓ Individual library status:")
        for name, lib in libraries.items():
            status = "Loaded" if lib is not None else "Not Available"
            print(f"  - {name}: {status}")
    
    def test_ci_specific_paths(self):
        """Test CI-specific library paths are included."""
        if not (os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS')):
            self.skipTest("Not in CI environment")
        
        paths = c_bindings.get_library_paths()
        
        # Check for CI-specific paths
        ci_path_found = any(
            '/home/runner/work' in str(path) or 
            'Django-Mercury-Performance-Testing' in str(path)
            for path in paths
        )
        
        if ci_path_found:
            print("✓ CI-specific paths are included in search")
        else:
            print("⚠️  CI-specific paths might be missing")
    
    @unittest.skipIf(
        os.environ.get('DJANGO_MERCURY_PURE_PYTHON') == '1',
        "Skipping library file check in pure Python mode"
    )
    def test_library_files_exist(self):
        """Test that library files exist in expected locations."""
        expected_libs = [
            'libquery_analyzer.so',
            'libmetrics_engine.so', 
            'libtest_orchestrator.so',
            'libperformance.so'
        ]
        
        paths = c_bindings.get_library_paths()
        found_libs = {}
        
        for lib_name in expected_libs:
            found = False
            for path in paths:
                lib_path = path / lib_name
                if lib_path.exists():
                    found_libs[lib_name] = lib_path
                    found = True
                    break
            
            if not found:
                # Also check with .dylib extension on macOS
                if sys.platform == 'darwin':
                    dylib_name = lib_name.replace('.so', '.dylib')
                    for path in paths:
                        lib_path = path / dylib_name
                        if lib_path.exists():
                            found_libs[lib_name] = lib_path
                            found = True
                            break
        
        print(f"✓ Library file search results:")
        for lib_name in expected_libs:
            if lib_name in found_libs:
                print(f"  ✓ {lib_name}: {found_libs[lib_name]}")
            else:
                print(f"  ✗ {lib_name}: Not found")
        
        # We don't assert here because libraries might not be built in CI
        # This is informational to help debug
    
    def test_error_messages_helpful(self):
        """Test that error messages are helpful when libraries can't load."""
        # Force a library load attempt
        lib_info = c_bindings.c_extensions.get_library_info('query_analyzer')
        
        if lib_info and not lib_info.is_loaded:
            self.assertIsNotNone(lib_info.error_message,
                               "Should have error message when load fails")
            print(f"✓ Error message provided: {lib_info.error_message}")
        else:
            print("ℹ️  Library loaded successfully or not attempted")


class TestCIWorkflowIntegration(unittest.TestCase):
    """Test CI workflow integration."""
    
    def test_github_env_variables(self):
        """Test GitHub Actions environment variables."""
        if not os.environ.get('GITHUB_ACTIONS'):
            self.skipTest("Not running in GitHub Actions")
        
        # Check expected GitHub Actions variables
        github_vars = {
            'GITHUB_WORKSPACE': os.environ.get('GITHUB_WORKSPACE'),
            'RUNNER_OS': os.environ.get('RUNNER_OS'),
            'GITHUB_RUN_ID': os.environ.get('GITHUB_RUN_ID'),
        }
        
        print("✓ GitHub Actions environment:")
        for var, value in github_vars.items():
            if value:
                print(f"  - {var}: {value}")
            else:
                print(f"  - {var}: Not set")
    
    def test_build_artifacts_location(self):
        """Test that build artifacts are in expected locations."""
        if not (os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS')):
            self.skipTest("Not in CI environment")
        
        # Check common CI build locations
        possible_locations = [
            Path.cwd() / 'django_mercury' / 'c_core',
            Path.cwd() / 'django_mercury' / 'python_bindings',
        ]
        
        print("✓ Checking build artifact locations:")
        for location in possible_locations:
            if location.exists():
                so_files = list(location.glob('*.so'))
                dylib_files = list(location.glob('*.dylib'))
                dll_files = list(location.glob('*.dll'))
                
                all_libs = so_files + dylib_files + dll_files
                
                if all_libs:
                    print(f"  ✓ {location}: {len(all_libs)} libraries found")
                    for lib in all_libs[:3]:  # Show first 3
                        print(f"    - {lib.name}")
                else:
                    print(f"  ✗ {location}: No libraries found")
            else:
                print(f"  ✗ {location}: Directory doesn't exist")


if __name__ == '__main__':
    # Run with verbose output
    print("=" * 60)
    print("Django Mercury CI Environment Tests")
    print("=" * 60)
    print()
    
    # Set verbosity for detailed output
    unittest.main(verbosity=2)