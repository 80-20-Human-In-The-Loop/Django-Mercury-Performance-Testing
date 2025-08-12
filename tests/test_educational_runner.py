"""Test for Educational Test Runner

This test verifies that the educational test runner works correctly
and triggers educational interventions when performance issues are detected.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django_mercury.test_runner import EducationalTestRunner, EducationalTestResult
from django_mercury.python_bindings.educational_monitor import EducationalMonitor


class TestEducationalRunner(unittest.TestCase):
    """Test the educational test runner functionality."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        # Clean environment
        os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)
        
    def test_educational_mode_detection(self) -> None:
        """Test that --edu flag is properly detected."""
        # Simulate --edu flag in argv
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['test', '--edu', 'test_module']
            
            # Create runner
            runner = EducationalTestRunner(verbosity=1, interactive=False)
            
            # Check that educational mode is enabled
            self.assertTrue(runner.educational_mode)
            
            # Check that --edu was removed from argv
            self.assertNotIn('--edu', sys.argv)
            
            # Check environment variable was set
            self.assertEqual(os.environ.get('MERCURY_EDUCATIONAL_MODE'), 'true')
            
        finally:
            sys.argv = original_argv
            os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)
    
    def test_educational_mode_disabled(self) -> None:
        """Test that educational mode is disabled without --edu flag."""
        # Create runner without --edu flag
        runner = EducationalTestRunner(verbosity=1, interactive=False)
        
        # Check that educational mode is disabled
        self.assertFalse(runner.educational_mode)
        
        # Check environment variable was not set
        self.assertIsNone(os.environ.get('MERCURY_EDUCATIONAL_MODE'))
    
    def test_educational_components_initialization(self) -> None:
        """Test that educational components are initialized."""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['test', '--edu']
            
            with patch('django_mercury.test_runner.Console') as MockConsole:
                runner = EducationalTestRunner(verbosity=1, interactive=False)
                
                # Check that components are initialized
                if runner.educational_monitor:
                    self.assertIsInstance(runner.educational_monitor, EducationalMonitor)
                
        finally:
            sys.argv = original_argv
            os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)
    
    def test_educational_result_class(self) -> None:
        """Test the EducationalTestResult class."""
        # Create a mock test
        mock_test = Mock()
        mock_test.__str__ = Mock(return_value="test_example")
        
        # Create result instance
        result = EducationalTestResult(
            stream=Mock(),
            descriptions=True,
            verbosity=1,
            educational_monitor=Mock()
        )
        
        # Test performance issue detection
        # The error tuple should have 3 elements: (type, value, traceback)
        error = (None, Exception("Performance threshold exceeded: Query count 150 exceeds limit 10"), None)
        result.addFailure(mock_test, error)
        
        # Check that performance issue was recorded
        self.assertEqual(len(result.performance_issues), 1)
        self.assertEqual(result.performance_issues[0]['type'], 'n_plus_one')
    
    def test_issue_type_detection(self) -> None:
        """Test detection of different issue types."""
        result = EducationalTestResult(
            stream=Mock(),
            descriptions=True,
            verbosity=1
        )
        
        # Test various issue types
        test_cases = [
            ("Query count exceeded", "n_plus_one"),
            ("Response time too slow", "slow_response"),
            ("Memory usage too high", "memory_leak"),
            ("Cache hit ratio too low", "cache_miss"),
            ("Performance threshold exceeded", "general_performance")
        ]
        
        for error_msg, expected_type in test_cases:
            detected_type = result._detect_issue_type(error_msg)
            self.assertEqual(detected_type, expected_type)
    
    @patch('django_mercury.test_runner.DiscoverRunner.build_suite')
    def test_build_suite_with_educational_mode(self, mock_build_suite) -> None:
        """Test that build_suite works with educational mode."""
        # Mock the parent's build_suite
        mock_suite = Mock()
        mock_suite.countTestCases.return_value = 5
        mock_build_suite.return_value = mock_suite
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['test', '--edu']
            
            runner = EducationalTestRunner(verbosity=1, interactive=False)
            suite = runner.build_suite()
            
            # Check that suite was built
            self.assertEqual(suite, mock_suite)
            mock_build_suite.assert_called_once()
            
        finally:
            sys.argv = original_argv
            os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)
    
    def test_environment_cleanup(self) -> None:
        """Test that environment is cleaned up after tests."""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['test', '--edu']
            
            runner = EducationalTestRunner(verbosity=1, interactive=False)
            
            # Environment should be set
            self.assertEqual(os.environ.get('MERCURY_EDUCATIONAL_MODE'), 'true')
            
            # Manually clean up the educational mode (simulating teardown)
            if runner.educational_mode:
                os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)
            
            # Environment should be cleaned
            self.assertIsNone(os.environ.get('MERCURY_EDUCATIONAL_MODE'))
            
        finally:
            sys.argv = original_argv
            os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)
    
    def test_run_tests_with_education_function(self) -> None:
        """Test the convenience function for running tests with education."""
        from django_mercury.test_runner import run_tests_with_education
        
        with patch('django_mercury.test_runner.EducationalTestRunner.run_tests') as mock_run:
            mock_run.return_value = 0
            
            # Run tests with education
            failures = run_tests_with_education(
                test_labels=['test_module'],
                verbosity=2,
                interactive=False
            )
            
            # Check that tests were run
            mock_run.assert_called_once_with(['test_module'])
            self.assertEqual(failures, 0)
            
            # Check environment was set
            self.assertEqual(os.environ.get('MERCURY_EDUCATIONAL_MODE'), 'true')
        
        # Clean up
        os.environ.pop('MERCURY_EDUCATIONAL_MODE', None)


class TestEducationalMonitor(unittest.TestCase):
    """Test the EducationalMonitor class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.monitor = EducationalMonitor(
            console=None,
            quiz_system=None,
            progress_tracker=None,
            interactive_mode=False
        )
    
    def test_issue_type_detection(self) -> None:
        """Test that issue types are correctly detected."""
        test_cases = [
            ("Query count 150 exceeds limit", "n_plus_one_queries"),
            ("N+1 queries detected", "n_plus_one_queries"),
            ("Response time 500ms exceeds threshold", "slow_response_time"),
            ("Request timeout after 30 seconds", "slow_response_time"),
            ("Memory usage 100MB exceeds limit", "memory_optimization"),
            ("Potential memory leak detected", "memory_optimization"),
            ("Cache hit ratio 0.2 below threshold", "cache_optimization"),
            ("Some other performance issue", "general_performance")
        ]
        
        for error_msg, expected_type in test_cases:
            detected_type = self.monitor._detect_issue_type(error_msg)
            self.assertEqual(
                detected_type,
                expected_type,
                f"Failed for: {error_msg}"
            )
    
    def test_issue_details_extraction(self) -> None:
        """Test extraction of issue details from error messages."""
        # Test response time extraction
        details = self.monitor._extract_issue_details("Response time 250.5ms exceeds limit")
        self.assertIn("250.5ms", details)
        
        # Test query count extraction
        details = self.monitor._extract_issue_details("Query count 42 exceeds maximum")
        self.assertIn("42", details)
        
        # Test memory extraction
        details = self.monitor._extract_issue_details("Memory 128.5MB exceeds threshold")
        self.assertIn("128.5MB", details)
    
    def test_educational_content_retrieval(self) -> None:
        """Test that educational content is retrieved for issues."""
        # Test all issue types have content
        issue_types = [
            "n_plus_one_queries",
            "slow_response_time",
            "memory_optimization",
            "cache_optimization",
            "general_performance"
        ]
        
        for issue_type in issue_types:
            content = self.monitor._get_educational_content(issue_type)
            
            # Check that content has required fields
            self.assertIn('explanation', content)
            self.assertIn('fix_summary', content)
            self.assertIn('fix_code', content)
            
            # Check content is not empty
            self.assertTrue(len(content['explanation']) > 0)
            self.assertTrue(len(content['fix_summary']) > 0)
    
    def test_fix_steps_retrieval(self) -> None:
        """Test that fix steps are provided for issues."""
        # Test that fix steps exist for known issues
        known_issues = [
            "n_plus_one_queries",
            "slow_response_time",
            "memory_optimization",
            "cache_optimization"
        ]
        
        for issue_type in known_issues:
            steps = self.monitor._get_fix_steps(issue_type)
            
            # Check that steps exist
            self.assertIsInstance(steps, list)
            self.assertTrue(len(steps) > 0)
    
    def test_handle_performance_issue_non_interactive(self) -> None:
        """Test handling performance issues in non-interactive mode."""
        # Monitor should not do anything in non-interactive mode
        self.monitor.interactive_mode = False
        
        # This should not raise any errors
        self.monitor.handle_performance_issue(
            test="test_example",
            error_msg="Query count 100 exceeds limit"
        )
        
        # Issue should still be recorded
        self.assertEqual(len(self.monitor.issues_found), 1)
        self.assertEqual(self.monitor.issues_found[0]['type'], 'n_plus_one_queries')
    
    def test_session_summary(self) -> None:
        """Test generation of session summary."""
        # Add some test issues
        self.monitor.issues_found = [
            {'test': 'test1', 'type': 'n_plus_one_queries', 'error': 'error1'},
            {'test': 'test2', 'type': 'n_plus_one_queries', 'error': 'error2'},
            {'test': 'test3', 'type': 'slow_response_time', 'error': 'error3'},
        ]
        
        summary = self.monitor.get_session_summary()
        
        # Check summary structure
        self.assertEqual(summary['total_issues'], 3)
        self.assertEqual(summary['issue_types']['n_plus_one_queries'], 2)
        self.assertEqual(summary['issue_types']['slow_response_time'], 1)
        self.assertEqual(len(summary['tests_affected']), 3)


if __name__ == '__main__':
    unittest.main()