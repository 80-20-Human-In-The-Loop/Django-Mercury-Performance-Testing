"""Comprehensive tests for Educational Monitor module.

This test module ensures full coverage of the educational monitoring functionality
including issue detection, content generation, and interactive features.
"""

import os
import sys
import unittest
from unittest.mock import Mock, MagicMock, patch, call

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from django_mercury.python_bindings.educational_monitor import EducationalMonitor


class TestEducationalMonitorInit(unittest.TestCase):
    """Test EducationalMonitor initialization."""
    
    def test_init_defaults(self):
        """Test initialization with default parameters."""
        monitor = EducationalMonitor()
        self.assertIsNone(monitor.console)
        self.assertIsNone(monitor.quiz_system)
        self.assertIsNone(monitor.progress_tracker)
        self.assertTrue(monitor.interactive_mode)
        self.assertEqual(monitor.issues_found, [])
        self.assertIsNone(monitor.current_test)
        
    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        mock_console = Mock()
        mock_quiz = Mock()
        mock_tracker = Mock()
        
        monitor = EducationalMonitor(
            console=mock_console,
            quiz_system=mock_quiz,
            progress_tracker=mock_tracker,
            interactive_mode=False
        )
        
        self.assertEqual(monitor.console, mock_console)
        self.assertEqual(monitor.quiz_system, mock_quiz)
        self.assertEqual(monitor.progress_tracker, mock_tracker)
        self.assertFalse(monitor.interactive_mode)


class TestEducationalMonitorIssueHandling(unittest.TestCase):
    """Test issue handling and detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EducationalMonitor(interactive_mode=False)
        
    def test_detect_issue_type_n_plus_one(self):
        """Test detection of N+1 query issues."""
        test_cases = [
            "Query count 150 exceeds limit",
            "N+1 queries detected in view",
            "Potential N+1 query problem found",
        ]
        
        for error_msg in test_cases:
            issue_type = self.monitor._detect_issue_type(error_msg)
            self.assertEqual(issue_type, "n_plus_one_queries")
            
    def test_detect_issue_type_slow_response(self):
        """Test detection of slow response issues."""
        test_cases = [
            "Response time 500ms exceeds threshold",
            "Request timeout after 30 seconds",
            "Slow response time detected",
        ]
        
        for error_msg in test_cases:
            issue_type = self.monitor._detect_issue_type(error_msg)
            self.assertEqual(issue_type, "slow_response_time")
            
    def test_detect_issue_type_memory(self):
        """Test detection of memory issues."""
        test_cases = [
            "Memory usage 100MB exceeds limit",
            "Potential memory leak detected",
            "High memory consumption",
        ]
        
        for error_msg in test_cases:
            issue_type = self.monitor._detect_issue_type(error_msg)
            self.assertEqual(issue_type, "memory_optimization")
            
    def test_detect_issue_type_cache(self):
        """Test detection of cache issues."""
        test_cases = [
            "Cache hit ratio 0.2 below threshold",
            "Cache miss rate too high",
            "Caching not configured properly",
        ]
        
        for error_msg in test_cases:
            issue_type = self.monitor._detect_issue_type(error_msg)
            self.assertEqual(issue_type, "cache_optimization")
            
    def test_detect_issue_type_general(self):
        """Test detection of general performance issues."""
        error_msg = "Some other performance problem"
        issue_type = self.monitor._detect_issue_type(error_msg)
        self.assertEqual(issue_type, "general_performance")
        
    def test_handle_performance_issue_non_interactive(self):
        """Test handling performance issues in non-interactive mode."""
        self.monitor.interactive_mode = False
        
        test_obj = Mock()
        test_obj.__str__ = Mock(return_value="test_example TestCase")
        
        self.monitor.handle_performance_issue(
            test=test_obj,
            error_msg="Query count 100 exceeds limit"
        )
        
        # Issue should be recorded even in non-interactive mode
        self.assertEqual(len(self.monitor.issues_found), 1)
        self.assertEqual(self.monitor.issues_found[0]['type'], 'n_plus_one_queries')
        self.assertEqual(self.monitor.issues_found[0]['test'], 'test_example')
        
    @patch('django_mercury.python_bindings.educational_monitor.RICH_AVAILABLE', True)
    def test_handle_performance_issue_interactive_with_rich(self):
        """Test handling performance issues in interactive mode with Rich."""
        mock_console = Mock()
        self.monitor = EducationalMonitor(
            console=mock_console,
            interactive_mode=True
        )
        
        with patch.object(self.monitor, '_show_rich_educational_content') as mock_show:
            self.monitor.handle_performance_issue(
                test="test_example",
                error_msg="Response time 500ms exceeds threshold"
            )
            
            mock_show.assert_called_once_with(
                "test_example",
                "slow_response_time",
                "Response time 500ms exceeds threshold"
            )
            
    @patch('django_mercury.python_bindings.educational_monitor.RICH_AVAILABLE', False)
    def test_handle_performance_issue_interactive_without_rich(self):
        """Test handling performance issues in interactive mode without Rich."""
        self.monitor = EducationalMonitor(interactive_mode=True)
        
        with patch.object(self.monitor, '_show_text_educational_content') as mock_show:
            self.monitor.handle_performance_issue(
                test="test_memory",
                error_msg="Memory usage too high"
            )
            
            mock_show.assert_called_once_with(
                "test_memory",
                "memory_optimization",
                "Memory usage too high"
            )
            
    def test_handle_performance_issue_with_progress_tracker(self):
        """Test handling issues with progress tracker."""
        mock_tracker = Mock()
        self.monitor = EducationalMonitor(
            progress_tracker=mock_tracker,
            interactive_mode=False
        )
        
        self.monitor.handle_performance_issue(
            test="test_cache",
            error_msg="Cache miss rate too high"
        )
        
        mock_tracker.add_concept.assert_called_once_with("cache_optimization")


class TestEducationalContent(unittest.TestCase):
    """Test educational content generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EducationalMonitor()
        
    def test_extract_issue_details_response_time(self):
        """Test extracting response time from error message."""
        details = self.monitor._extract_issue_details(
            "Response time 250.5ms exceeds limit"
        )
        self.assertIn("250.5ms", details)
        
    def test_extract_issue_details_query_count(self):
        """Test extracting query count from error message."""
        details = self.monitor._extract_issue_details(
            "Query count 42 exceeds maximum"
        )
        self.assertIn("42", details)
        
    def test_extract_issue_details_memory(self):
        """Test extracting memory usage from error message."""
        details = self.monitor._extract_issue_details(
            "Memory 128.5MB exceeds threshold"
        )
        self.assertIn("128.5MB", details)
        
    def test_extract_issue_details_combined(self):
        """Test extracting multiple metrics from error message."""
        details = self.monitor._extract_issue_details(
            "Response time 100ms, Query count 50, Memory 20MB"
        )
        self.assertIn("100ms", details)
        self.assertIn("50", details)
        self.assertIn("20MB", details)
        
    def test_extract_issue_details_no_metrics(self):
        """Test extracting details when no specific metrics found."""
        error_msg = "General performance issue detected"
        details = self.monitor._extract_issue_details(error_msg)
        self.assertEqual(details, error_msg[:100])
        
    def test_get_educational_content_all_types(self):
        """Test getting educational content for all issue types."""
        issue_types = [
            "n_plus_one_queries",
            "slow_response_time",
            "memory_optimization",
            "cache_optimization",
            "general_performance"
        ]
        
        for issue_type in issue_types:
            content = self.monitor._get_educational_content(issue_type)
            
            # Verify required fields
            self.assertIn('explanation', content)
            self.assertIn('fix_summary', content)
            self.assertIn('fix_code', content)
            
            # Verify content is not empty
            self.assertTrue(len(content['explanation']) > 0)
            self.assertTrue(len(content['fix_summary']) > 0)
            
    def test_get_fix_steps_all_types(self):
        """Test getting fix steps for all issue types."""
        test_cases = [
            ("n_plus_one_queries", 5),  # Expected 5 steps
            ("slow_response_time", 5),
            ("memory_optimization", 5),
            ("cache_optimization", 5),
        ]
        
        for issue_type, expected_count in test_cases:
            steps = self.monitor._get_fix_steps(issue_type)
            self.assertIsInstance(steps, list)
            self.assertEqual(len(steps), expected_count)
            
    def test_get_fix_steps_unknown_type(self):
        """Test getting fix steps for unknown issue type."""
        steps = self.monitor._get_fix_steps("unknown_issue")
        self.assertEqual(steps, [])


class TestEducationalDisplay(unittest.TestCase):
    """Test display methods for educational content."""
    
    @patch('django_mercury.python_bindings.educational_monitor.RICH_AVAILABLE', True)
    def test_show_rich_educational_content(self):
        """Test showing educational content with Rich."""
        mock_console = Mock()
        mock_quiz_system = Mock()
        mock_quiz_system.ask_quiz_for_concept.return_value = {
            'wants_to_learn': True
        }
        
        monitor = EducationalMonitor(
            console=mock_console,
            quiz_system=mock_quiz_system,
            interactive_mode=True
        )
        
        with patch.object(monitor, '_show_fix_guide') as mock_fix:
            with patch.object(monitor, '_show_additional_resources') as mock_resources:
                with patch('django_mercury.python_bindings.educational_monitor.Confirm') as MockConfirm:
                    MockConfirm.ask.return_value = False
                    
                    monitor._show_rich_educational_content(
                        "test_name",
                        "n_plus_one_queries",
                        "Query count 100"
                    )
                    
                    # Verify console output was called
                    self.assertTrue(mock_console.print.called)
                    
                    # Verify quiz was asked
                    mock_quiz_system.ask_quiz_for_concept.assert_called_with("n_plus_one_queries")
                    
                    # Verify fix guide was shown
                    mock_fix.assert_called_once()
                
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_show_text_educational_content(self, mock_print, mock_input):
        """Test showing educational content without Rich."""
        monitor = EducationalMonitor(interactive_mode=True)
        
        monitor._show_text_educational_content(
            "test_cache",
            "cache_optimization",
            "Cache hit ratio low"
        )
        
        # Verify output was printed
        mock_print.assert_called()
        
        # Check for expected content in prints
        all_prints = ' '.join(str(call) for call in mock_print.call_args_list)
        self.assertIn("PERFORMANCE ISSUE DETECTED", all_prints)
        self.assertIn("cache optimization", all_prints.lower())
        
    @patch('django_mercury.python_bindings.educational_monitor.RICH_AVAILABLE', True)
    def test_show_fix_guide(self):
        """Test showing fix guide with Rich."""
        mock_console = Mock()
        monitor = EducationalMonitor(console=mock_console)
        
        content = {
            'fix_code': 'User.objects.select_related("profile")'
        }
        
        monitor._show_fix_guide("n_plus_one_queries", content)
        
        # Verify console was used to show content
        mock_console.print.assert_called()
        
    @patch('django_mercury.python_bindings.educational_monitor.RICH_AVAILABLE', True)
    def test_show_additional_resources(self):
        """Test showing additional resources."""
        mock_console = Mock()
        monitor = EducationalMonitor(console=mock_console)
        
        with patch('builtins.input', return_value=''):
            monitor._show_additional_resources("slow_response_time")
        
        # Verify console was used
        mock_console.print.assert_called()


class TestEducationalSessionSummary(unittest.TestCase):
    """Test session summary functionality."""
    
    def test_get_session_summary_empty(self):
        """Test getting summary with no issues."""
        monitor = EducationalMonitor()
        summary = monitor.get_session_summary()
        
        self.assertEqual(summary['total_issues'], 0)
        self.assertEqual(summary['issue_types'], {})
        self.assertEqual(summary['tests_affected'], [])
        
    def test_get_session_summary_with_issues(self):
        """Test getting summary with multiple issues."""
        monitor = EducationalMonitor()
        
        # Add test issues
        monitor.issues_found = [
            {'test': 'test1', 'type': 'n_plus_one_queries', 'error': 'error1'},
            {'test': 'test2', 'type': 'n_plus_one_queries', 'error': 'error2'},
            {'test': 'test3', 'type': 'slow_response_time', 'error': 'error3'},
            {'test': 'test1', 'type': 'cache_optimization', 'error': 'error4'},
        ]
        
        summary = monitor.get_session_summary()
        
        self.assertEqual(summary['total_issues'], 4)
        self.assertEqual(summary['issue_types']['n_plus_one_queries'], 2)
        self.assertEqual(summary['issue_types']['slow_response_time'], 1)
        self.assertEqual(summary['issue_types']['cache_optimization'], 1)
        self.assertIn('test1', summary['tests_affected'])
        self.assertIn('test2', summary['tests_affected'])
        self.assertIn('test3', summary['tests_affected'])
        self.assertEqual(len(summary['tests_affected']), 3)  # 3 unique tests


class TestEducationalIntegration(unittest.TestCase):
    """Test integration with other components."""
    
    @patch('django_mercury.python_bindings.educational_monitor.RICH_AVAILABLE', True)
    def test_full_flow_with_quiz_and_learning(self):
        """Test complete flow with quiz interaction and learning."""
        mock_console = Mock()
        mock_quiz_system = Mock()
        mock_progress_tracker = Mock()
        
        # Set up quiz response
        mock_quiz_system.ask_quiz_for_concept.return_value = {
            'correct': False,
            'wants_to_learn': True
        }
        
        monitor = EducationalMonitor(
            console=mock_console,
            quiz_system=mock_quiz_system,
            progress_tracker=mock_progress_tracker,
            interactive_mode=True
        )
        
        with patch('django_mercury.python_bindings.educational_monitor.Confirm') as MockConfirm:
            MockConfirm.ask.side_effect = [True, False]  # Continue, then no more info
            
            with patch.object(monitor, '_show_fix_guide'):
                with patch.object(monitor, '_show_additional_resources'):
                    monitor.handle_performance_issue(
                        test="test_full_flow",
                        error_msg="Query count 200 exceeds limit"
                    )
                    
        # Verify full flow executed
        self.assertEqual(len(monitor.issues_found), 1)
        mock_quiz_system.ask_quiz_for_concept.assert_called_once()
        mock_progress_tracker.add_concept.assert_called_once_with("n_plus_one_queries")
        
    def test_non_interactive_performance(self):
        """Test that non-interactive mode is fast."""
        monitor = EducationalMonitor(interactive_mode=False)
        
        # Should complete quickly without any user interaction
        for i in range(10):
            monitor.handle_performance_issue(
                test=f"test_{i}",
                error_msg=f"Performance issue {i}"
            )
            
        self.assertEqual(len(monitor.issues_found), 10)


if __name__ == '__main__':
    unittest.main()