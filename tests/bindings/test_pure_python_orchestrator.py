"""
Comprehensive tests for PythonTestOrchestrator in pure_python.py
Tests test orchestration and coordination without C extensions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from django_mercury.python_bindings.pure_python import PythonTestOrchestrator


class TestPythonTestOrchestrator(unittest.TestCase):
    """Test the PythonTestOrchestrator class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.orchestrator = PythonTestOrchestrator()
    
    def test_initialization(self) -> None:
        """Test orchestrator initializes correctly."""
        self.assertEqual(self.orchestrator.test_results, [])
        self.assertIsNone(self.orchestrator.current_test)
        self.assertEqual(self.orchestrator.monitors, {})
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_start_test(self, mock_monitor_class, mock_time) -> None:
        """Test starting a test."""
        mock_time.return_value = 1234567890.0
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        self.orchestrator.start_test('test_example')
        
        # Check current test is set
        self.assertIsNotNone(self.orchestrator.current_test)
        self.assertEqual(self.orchestrator.current_test['name'], 'test_example')
        self.assertEqual(self.orchestrator.current_test['start_time'], 1234567890.0)
        self.assertEqual(self.orchestrator.current_test['status'], 'running')
        self.assertEqual(self.orchestrator.current_test['metrics'], {})
        
        # Check monitor was created and started
        self.assertIn('test_example', self.orchestrator.monitors)
        mock_monitor.start_monitoring.assert_called_once()
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_end_test_passed(self, mock_monitor_class, mock_time) -> None:
        """Test ending a test with passed status."""
        mock_time.side_effect = [1000.0, 1010.0]  # Start and end times
        
        mock_monitor = Mock()
        mock_monitor.get_metrics.return_value = {
            'response_time_ms': 100.0,
            'query_count': 5
        }
        mock_monitor_class.return_value = mock_monitor
        
        # Start and end test
        self.orchestrator.start_test('test_example')
        result = self.orchestrator.end_test('test_example', 'passed')
        
        # Check result
        self.assertEqual(result['name'], 'test_example')
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['start_time'], 1000.0)
        self.assertEqual(result['end_time'], 1010.0)
        self.assertEqual(result['duration'], 10.0)
        self.assertEqual(result['metrics']['response_time_ms'], 100.0)
        
        # Check monitor was stopped
        mock_monitor.stop_monitoring.assert_called_once()
        
        # Check test was added to results
        self.assertEqual(len(self.orchestrator.test_results), 1)
        
        # Check cleanup
        self.assertIsNone(self.orchestrator.current_test)
        self.assertNotIn('test_example', self.orchestrator.monitors)
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_end_test_failed(self, mock_monitor_class, mock_time) -> None:
        """Test ending a test with failed status."""
        mock_time.side_effect = [1000.0, 1005.0]
        
        mock_monitor = Mock()
        mock_monitor.get_metrics.return_value = {'response_time_ms': 50.0}
        mock_monitor_class.return_value = mock_monitor
        
        self.orchestrator.start_test('test_failure')
        result = self.orchestrator.end_test('test_failure', 'failed')
        
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['duration'], 5.0)
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_end_test_skipped(self, mock_monitor_class, mock_time) -> None:
        """Test ending a test with skipped status."""
        mock_time.side_effect = [1000.0, 1001.0]
        
        mock_monitor = Mock()
        mock_monitor.get_metrics.return_value = {}
        mock_monitor_class.return_value = mock_monitor
        
        self.orchestrator.start_test('test_skip')
        result = self.orchestrator.end_test('test_skip', 'skipped')
        
        self.assertEqual(result['status'], 'skipped')
    
    def test_end_test_without_starting(self) -> None:
        """Test ending a test that was never started."""
        result = self.orchestrator.end_test('non_existent_test', 'passed')
        
        self.assertEqual(result, {})
        self.assertEqual(len(self.orchestrator.test_results), 0)
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_end_test_wrong_name(self, mock_monitor_class, mock_time) -> None:
        """Test ending a test with wrong name."""
        mock_time.return_value = 1000.0
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        self.orchestrator.start_test('test_a')
        result = self.orchestrator.end_test('test_b', 'passed')
        
        # Should return empty dict
        self.assertEqual(result, {})
        
        # Current test should still be running
        self.assertIsNotNone(self.orchestrator.current_test)
        self.assertEqual(self.orchestrator.current_test['name'], 'test_a')
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_multiple_tests_sequential(self, mock_monitor_class, mock_time) -> None:
        """Test running multiple tests sequentially."""
        mock_time.side_effect = [1000.0, 1010.0, 1020.0, 1025.0, 1030.0, 1040.0]
        
        mock_monitor = Mock()
        mock_monitor.get_metrics.return_value = {'response_time_ms': 100.0}
        mock_monitor_class.return_value = mock_monitor
        
        # Run three tests
        self.orchestrator.start_test('test_1')
        self.orchestrator.end_test('test_1', 'passed')
        
        self.orchestrator.start_test('test_2')
        self.orchestrator.end_test('test_2', 'failed')
        
        self.orchestrator.start_test('test_3')
        self.orchestrator.end_test('test_3', 'passed')
        
        # Check results
        self.assertEqual(len(self.orchestrator.test_results), 3)
        self.assertEqual(self.orchestrator.test_results[0]['status'], 'passed')
        self.assertEqual(self.orchestrator.test_results[1]['status'], 'failed')
        self.assertEqual(self.orchestrator.test_results[2]['status'], 'passed')
    
    def test_get_summary_empty(self) -> None:
        """Test getting summary with no tests."""
        summary = self.orchestrator.get_summary()
        
        self.assertEqual(summary['total_tests'], 0)
        self.assertEqual(summary['passed'], 0)
        self.assertEqual(summary['failed'], 0)
        self.assertEqual(summary['implementation'], 'pure_python')
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_get_summary_with_tests(self, mock_monitor_class, mock_time) -> None:
        """Test getting summary with multiple tests."""
        # Set up times for 4 tests
        mock_time.side_effect = [
            1000.0, 1010.0,  # Test 1: 10s
            1020.0, 1025.0,  # Test 2: 5s
            1030.0, 1045.0,  # Test 3: 15s
            1050.0, 1060.0,  # Test 4: 10s
        ]
        
        # Set up different metrics for each test
        mock_monitor = Mock()
        mock_monitor.get_metrics.side_effect = [
            {'response_time_ms': 100.0},
            {'response_time_ms': 50.0},
            {'response_time_ms': 150.0},
            {'response_time_ms': 100.0},
        ]
        mock_monitor_class.return_value = mock_monitor
        
        # Run tests
        self.orchestrator.start_test('test_1')
        self.orchestrator.end_test('test_1', 'passed')
        
        self.orchestrator.start_test('test_2')
        self.orchestrator.end_test('test_2', 'failed')
        
        self.orchestrator.start_test('test_3')
        self.orchestrator.end_test('test_3', 'passed')
        
        self.orchestrator.start_test('test_4')
        self.orchestrator.end_test('test_4', 'passed')
        
        # Get summary
        summary = self.orchestrator.get_summary()
        
        self.assertEqual(summary['total_tests'], 4)
        self.assertEqual(summary['passed'], 3)
        self.assertEqual(summary['failed'], 1)
        self.assertEqual(summary['total_duration'], 40.0)  # 10 + 5 + 15 + 10
        self.assertEqual(summary['avg_response_time_ms'], 100.0)  # (100 + 50 + 150 + 100) / 4
        self.assertEqual(summary['implementation'], 'pure_python')
    
    def test_get_summary_with_missing_metrics(self) -> None:
        """Test summary calculation when some tests have missing metrics."""
        # Manually add test results with varying metrics
        self.orchestrator.test_results = [
            {
                'name': 'test_1',
                'status': 'passed',
                'duration': 5.0,
                'metrics': {'response_time_ms': 100.0}
            },
            {
                'name': 'test_2',
                'status': 'failed',
                'duration': 3.0,
                'metrics': {}  # No response_time_ms
            },
            {
                'name': 'test_3',
                'status': 'passed',
                'duration': 4.0,
                'metrics': {'response_time_ms': 200.0}
            },
        ]
        
        summary = self.orchestrator.get_summary()
        
        self.assertEqual(summary['total_tests'], 3)
        self.assertEqual(summary['passed'], 2)
        self.assertEqual(summary['failed'], 1)
        self.assertEqual(summary['total_duration'], 12.0)
        self.assertEqual(summary['avg_response_time_ms'], 100.0)  # (100 + 0 + 200) / 3
    
    def test_get_summary_with_missing_duration(self) -> None:
        """Test summary when some tests have missing duration."""
        self.orchestrator.test_results = [
            {'name': 'test_1', 'status': 'passed', 'duration': 5.0, 'metrics': {}},
            {'name': 'test_2', 'status': 'passed', 'metrics': {}},  # No duration
            {'name': 'test_3', 'status': 'passed', 'duration': 3.0, 'metrics': {}},
        ]
        
        summary = self.orchestrator.get_summary()
        
        self.assertEqual(summary['total_duration'], 8.0)  # 5 + 0 + 3
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_monitor_lifecycle(self, mock_monitor_class, mock_time) -> None:
        """Test that monitors are properly created and cleaned up."""
        # Need times for: start_test1, start_test2, end_test2
        mock_time.side_effect = [1000.0, 1010.0, 1020.0]
        
        mock_monitor1 = Mock()
        mock_monitor2 = Mock()
        mock_monitor_class.side_effect = [mock_monitor1, mock_monitor2]
        
        # Start first test
        self.orchestrator.start_test('test_1')
        self.assertEqual(len(self.orchestrator.monitors), 1)
        self.assertIn('test_1', self.orchestrator.monitors)
        
        # Start second test without ending first
        self.orchestrator.start_test('test_2')
        self.assertEqual(len(self.orchestrator.monitors), 2)
        self.assertIn('test_2', self.orchestrator.monitors)
        
        # End first test (won't return full results since current_test is test_2)
        mock_monitor1.get_metrics.return_value = {}
        result = self.orchestrator.end_test('test_1', 'passed')
        self.assertEqual(result, {})  # Empty since test_1 is not current
        self.assertEqual(len(self.orchestrator.monitors), 1)
        self.assertNotIn('test_1', self.orchestrator.monitors)
        self.assertIn('test_2', self.orchestrator.monitors)
        
        # End second test (will return full results)
        mock_monitor2.get_metrics.return_value = {}
        result = self.orchestrator.end_test('test_2', 'passed')
        self.assertNotEqual(result, {})  # Has results since test_2 is current
        self.assertEqual(len(self.orchestrator.monitors), 0)
    
    def test_get_summary_various_statuses(self) -> None:
        """Test summary with various test statuses."""
        self.orchestrator.test_results = [
            {'name': 'test_1', 'status': 'passed', 'duration': 1.0, 'metrics': {}},
            {'name': 'test_2', 'status': 'failed', 'duration': 1.0, 'metrics': {}},
            {'name': 'test_3', 'status': 'skipped', 'duration': 0.1, 'metrics': {}},
            {'name': 'test_4', 'status': 'passed', 'duration': 1.0, 'metrics': {}},
            {'name': 'test_5', 'status': 'error', 'duration': 0.5, 'metrics': {}},
        ]
        
        summary = self.orchestrator.get_summary()
        
        self.assertEqual(summary['total_tests'], 5)
        self.assertEqual(summary['passed'], 2)  # Only 'passed' status counts
        self.assertEqual(summary['failed'], 1)  # Only 'failed' status counts
        # skipped and error are not counted in passed/failed
    
    @patch('django_mercury.python_bindings.pure_python.time.time')
    @patch('django_mercury.python_bindings.pure_python.PythonPerformanceMonitor')
    def test_concurrent_test_attempts(self, mock_monitor_class, mock_time) -> None:
        """Test behavior when trying to start a test while another is running."""
        mock_time.return_value = 1000.0
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Start first test
        self.orchestrator.start_test('test_1')
        current_test_1 = self.orchestrator.current_test
        
        # Try to start second test (will overwrite current_test)
        self.orchestrator.start_test('test_2')
        current_test_2 = self.orchestrator.current_test
        
        # Current test should be the second one
        self.assertEqual(current_test_2['name'], 'test_2')
        self.assertNotEqual(current_test_1, current_test_2)
        
        # Both monitors should exist
        self.assertEqual(len(self.orchestrator.monitors), 2)
        self.assertIn('test_1', self.orchestrator.monitors)
        self.assertIn('test_2', self.orchestrator.monitors)


if __name__ == '__main__':
    unittest.main()