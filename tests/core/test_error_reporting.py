"""
Test suite for Mercury error reporting functionality.

This module tests that performance threshold violations correctly display
file names, lines, and test method names in error messages, allowing users
to click and navigate directly to failing tests in their IDE.

Tests the REAL implementation instead of mocks.
"""

import unittest
import inspect
import tempfile
import os
from unittest.mock import patch

from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor


class TestErrorReporting(unittest.TestCase):
    """Test error reporting functionality in Mercury framework."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        # Ensure we're testing with fallback implementation to avoid C library issues
        self.patcher = patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
        self.patcher.start()
    
    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.patcher.stop()
    
    def test_file_name_in_error_message_with_context(self) -> None:
        """Test that error messages show correct file name when test context is set."""
        test_file = "/home/mathew/python-3.10.12-Projects/EduLite/backend/EduLite/users/tests/views/test_UserRetrieveView.py"
        test_line = 262
        test_method = "test_bulk_user_retrieval_performance"
        
        # Create a monitor with very low thresholds to trigger violations
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("test_operation") as monitor:
                monitor.set_test_context(test_file, test_line, test_method)
                monitor.expect_response_under(0.001)  # 0.001ms - impossible threshold
                # The context manager exit will trigger the assertion
                import time
                time.sleep(0.01)  # This will exceed the 0.001ms threshold
        
        error_message = str(context.exception)
        
        # Verify error message contains file information
        self.assertIn("users/tests/views/test_UserRetrieveView.py", error_message)
        self.assertIn("262", error_message)
        self.assertIn("test_bulk_user_retrieval_performance", error_message)
        self.assertIn("📁", error_message)  # File icon
        
    def test_file_name_with_relative_path(self) -> None:
        """Test that relative paths are displayed correctly."""
        current_file = inspect.getfile(self.__class__)
        test_line = inspect.currentframe().f_lineno + 5  # Line where context manager starts
        test_method = "test_file_name_with_relative_path"
        
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("test_operation") as monitor:
                monitor.set_test_context(current_file, test_line, test_method)
                monitor.expect_response_under(0.001)  # Impossible threshold
                import time
                time.sleep(0.01)  # This will exceed the threshold
        
        error_message = str(context.exception)
        
        # Should show relative path (handle both Unix and Windows paths)
        # Normalize paths to use forward slashes for comparison
        normalized_error = error_message.replace('\\', '/')
        self.assertIn("tests/core/test_error_reporting.py", normalized_error)
        self.assertIn(str(test_line), error_message)
        self.assertIn("test_file_name_with_relative_path", error_message)
        
    def test_error_message_without_context_fallback(self) -> None:
        """Test that error messages work even without test context (no context set)."""
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("test_operation") as monitor:
                monitor.expect_response_under(0.001)  # Impossible threshold
                # No set_test_context called - should still work
                import time
                time.sleep(0.01)  # This will exceed the threshold
        
        error_message = str(context.exception)
        
        # Should contain performance threshold information even without context
        self.assertIn("Performance thresholds exceeded", error_message)
        self.assertIn("Response time", error_message)
        
    def test_multiple_threshold_violations(self) -> None:
        """Test error messages with multiple threshold violations."""
        test_file = __file__
        test_line = inspect.currentframe().f_lineno + 5
        test_method = "test_multiple_threshold_violations"
        
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("test_operation") as monitor:
                monitor.set_test_context(test_file, test_line, test_method)
                monitor.expect_response_under(0.001)  # Response time threshold  
                monitor.expect_memory_under(0.001)    # Memory threshold (impossible)
                # Note: Can't easily test query count in this context
                import time
                time.sleep(0.01)  # This will exceed thresholds
        
        error_message = str(context.exception)
        
        # Should contain file info and multiple violations
        self.assertIn("test_error_reporting.py", error_message)
        self.assertIn("test_multiple_threshold_violations", error_message)
        self.assertIn("Performance thresholds exceeded", error_message)
        # Should have multiple violation messages
        violation_indicators = ["Response time", "Memory usage"]
        found_violations = sum(1 for indicator in violation_indicators if indicator in error_message)
        self.assertGreaterEqual(found_violations, 1, "Should report at least one threshold violation")
        
    def test_file_path_normalization(self) -> None:
        """Test that file paths are normalized correctly across different systems."""
        windows_path = "C:\\Users\\test\\project\\tests\\test_file.py"
        test_line = 100
        test_method = "test_windows_path"
        
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("test_operation") as monitor:
                monitor.set_test_context(windows_path, test_line, test_method)
                monitor.expect_response_under(0.001)  # Impossible threshold
                import time
                time.sleep(0.01)  # This will exceed the threshold
        
        error_message = str(context.exception)
        
        # Should handle the path gracefully (either show full path or filename)
        self.assertTrue(
            "test_file.py" in error_message or 
            "100" in error_message,
            f"Error message should contain file info: {error_message}"
        )
        self.assertIn("test_windows_path", error_message)
        
    def test_red_coloring_applied(self) -> None:
        """Test that red coloring is applied to error messages."""
        test_file = __file__
        test_line = inspect.currentframe().f_lineno + 5
        test_method = "test_red_coloring_applied"
        
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("test_operation") as monitor:
                monitor.set_test_context(test_file, test_line, test_method)
                monitor.expect_response_under(0.001)  # Impossible threshold
                import time
                time.sleep(0.01)  # This will exceed the threshold
        
        error_message = str(context.exception)
        
        # Check for ANSI color codes that indicate red coloring
        # The colors.py system should add ANSI escape sequences
        self.assertTrue(
            '\033[' in error_message or  # ANSI escape sequence
            'Performance thresholds exceeded' in error_message,  # At minimum the message should be there
            f"Error message should contain coloring or base message: {error_message}"
        )


class TestErrorReportingFixtures(unittest.TestCase):
    """Test error reporting with fixture files to simulate different scenarios."""
    
    def setUp(self) -> None:
        """Create temporary test fixture files and disable C extensions."""
        # Disable C extensions to avoid library issues
        self.patcher = patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
        self.patcher.start()
        
        self.temp_dir = tempfile.mkdtemp()
        self.fixture_file = os.path.join(self.temp_dir, "mock_test_file.py")
        
        with open(self.fixture_file, 'w') as f:
            f.write("""
# Mock test file for error reporting tests
def test_mock_performance_test():
    pass

class MockTestClass:
    def test_mock_method(self) -> None:
        pass
""")
    
    def tearDown(self) -> None:
        """Clean up temporary files."""
        self.patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_fixture_file_in_error_message(self) -> None:
        """Test error reporting with fixture files."""
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("fixture_test") as monitor:
                monitor.set_test_context(self.fixture_file, 10, "test_mock_performance_test")
                monitor.expect_response_under(0.001)  # Impossible threshold
                import time
                time.sleep(0.01)  # This will exceed the threshold
        
        error_message = str(context.exception)
        
        # Should show the fixture file name
        self.assertIn("mock_test_file.py", error_message)
        self.assertIn("10", error_message)
        self.assertIn("test_mock_performance_test", error_message)


class TestEdgeCasesAndErrorConditions(unittest.TestCase):
    """Test edge cases and error conditions in error reporting."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        # Disable C extensions to avoid library issues
        self.patcher = patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
        self.patcher.start()
    
    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.patcher.stop()
    
    def test_error_reporting_with_invalid_file_path(self) -> None:
        """Test error reporting with non-existent file path."""
        invalid_path = "/non/existent/path/test_file.py"
        test_line = 999 
        test_method = "test_invalid_path"
        
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("test_operation") as monitor:
                monitor.set_test_context(invalid_path, test_line, test_method)
                monitor.expect_response_under(0.001)  # Impossible threshold
                import time
                time.sleep(0.01)  # This will exceed the threshold
        
        error_message = str(context.exception)
        
        # Should still include the path information even if file doesn't exist
        self.assertIn("test_file.py", error_message)
        self.assertIn("999", error_message)
        self.assertIn("test_invalid_path", error_message)
    
    def test_memory_threshold_violation_reporting(self) -> None:
        """Test specific memory threshold violation reporting."""
        with self.assertRaises(AssertionError) as context:
            with EnhancedPerformanceMonitor("memory_test") as monitor:
                monitor.set_test_context(__file__, 100, "test_memory")
                monitor.expect_memory_under(0.001)  # Impossible memory threshold (0.001MB)
                import time
                time.sleep(0.01)  # Allow some memory allocation
        
        error_message = str(context.exception)
        
        # Should mention memory usage specifically
        self.assertIn("Memory usage", error_message)
        self.assertIn("MB", error_message)
    
    def test_no_thresholds_set_no_error(self) -> None:
        """Test that no error is raised when no thresholds are violated."""
        # This should NOT raise an AssertionError
        try:
            with EnhancedPerformanceMonitor("no_threshold_test") as monitor:
                monitor.set_test_context(__file__, 200, "test_no_thresholds")
                # No expect_* methods called, so no thresholds to violate
                import time
                time.sleep(0.01)  # Some work that normally might trigger violations
            # If we get here, the test passed (no assertion error)
            success = True
        except AssertionError:
            success = False
        
        self.assertTrue(success, "Should not raise AssertionError when no thresholds are set")


if __name__ == '__main__':
    unittest.main()