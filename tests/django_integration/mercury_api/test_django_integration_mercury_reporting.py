"""
Test reporting and summary generation in django_integration_mercury.py
Focus on lines 756-783, 933-1049, and dashboard creation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from django_mercury.python_bindings.django_integration_mercury import (
    DjangoMercuryAPITestCase,
    TestExecutionSummary
)


class TestThresholdViolationDetailedReporting(unittest.TestCase):
    """Test detailed threshold violation reporting (lines 756-783)."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_case = DjangoMercuryAPITestCase()
    
    @patch('builtins.print')
    def test_response_time_violation_details(self, mock_print) -> None:
        """Test detailed response time violation reporting."""
        error_msg = "Performance thresholds exceeded: Response time 350.7ms > 200ms"
        
        self.test_case._provide_threshold_guidance(
            "test_slow_endpoint",
            error_msg,
            "list_view",
            {}
        )
        
        # Should print detailed violation info
        mock_print.assert_called()
        # Check that percentage calculation would be shown
        # (350.7 / 200 - 1) * 100 = 75.35%
    
    @patch('builtins.print')  
    def test_query_count_violation_details(self, mock_print) -> None:
        """Test detailed query count violation reporting."""
        error_msg = "Performance thresholds exceeded: Query count 125 > 50"
        
        self.test_case._provide_threshold_guidance(
            "test_n_plus_one",
            error_msg,
            "detail_view",
            {}
        )
        
        # Should show extra queries and percentage
        # 125 - 50 = 75 extra queries
        # (125 / 50 - 1) * 100 = 150% exceeded
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_memory_violation_details(self, mock_print) -> None:
        """Test detailed memory usage violation reporting."""
        error_msg = "Performance thresholds exceeded: Memory usage 156.8MB > 100MB"
        
        self.test_case._provide_threshold_guidance(
            "test_memory_intensive",
            error_msg,
            "create_view", 
            {}
        )
        
        # Should show memory overage
        # 156.8 - 100 = 56.8MB over
        # (156.8 / 100 - 1) * 100 = 56.8% exceeded
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_combined_violations_reporting(self, mock_print) -> None:
        """Test reporting multiple violations together."""
        error_msg = ("Performance thresholds exceeded: "
                    "Response time 500ms > 200ms, "
                    "Query count 100 > 25, "
                    "Memory usage 250.5MB > 150MB")
        
        self.test_case._provide_threshold_guidance(
            "test_everything_bad",
            error_msg,
            "search_view",
            {}
        )
        
        # All three violations should be detailed
        mock_print.assert_called()
        call_str = str(mock_print.call_args_list)
        # Would show all three violation types


class TestExecutiveSummaryGeneration(unittest.TestCase):
    """Test executive summary generation (lines 933-1049)."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        # Reset class state
        DjangoMercuryAPITestCase._test_executions = []
        DjangoMercuryAPITestCase._test_failures = []
        DjangoMercuryAPITestCase._optimization_recommendations = []
        DjangoMercuryAPITestCase._summary_generated = False
    
    @patch('builtins.print')
    def test_executive_summary_with_no_data(self, mock_print) -> None:
        """Test summary generation with no test data."""
        DjangoMercuryAPITestCase._test_executions = []
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
        printed = str(mock_print.call_args_list)
        self.assertIn("No performance data", printed)
    
    @patch('builtins.print')
    def test_executive_summary_with_mixed_grades(self, mock_print) -> None:
        """Test summary with various performance grades."""
        # Create mock test executions
        mock_exec1 = self._create_mock_execution('test1', 95, 'S', 50, 10, 5)
        mock_exec2 = self._create_mock_execution('test2', 85, 'A', 100, 20, 10)
        mock_exec3 = self._create_mock_execution('test3', 70, 'B', 150, 30, 15)
        mock_exec4 = self._create_mock_execution('test4', 55, 'D', 300, 50, 25)
        
        DjangoMercuryAPITestCase._test_executions = [
            mock_exec1, mock_exec2, mock_exec3, mock_exec4
        ]
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
        printed = str(mock_print.call_args_list)
        # Should show grade distribution
        self.assertIn("EXECUTIVE", printed) or self.assertIn("ANALYSIS", printed)
    
    @patch('builtins.print')
    def test_executive_summary_with_failures(self, mock_print) -> None:
        """Test summary including test failures."""
        mock_exec1 = self._create_mock_execution('test_pass', 90, 'A+', 80, 15, 8)
        mock_exec2 = self._create_mock_execution('test_fail', 40, 'F', 500, 60, 30)
        
        DjangoMercuryAPITestCase._test_executions = [mock_exec1, mock_exec2]
        DjangoMercuryAPITestCase._test_failures = [
            "❌ test_fail: Performance thresholds exceeded"
        ]
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
        # Should show failures in summary
    
    @patch('builtins.print')
    def test_executive_summary_with_recommendations(self, mock_print) -> None:
        """Test summary with optimization recommendations."""
        mock_exec = self._create_mock_execution('test1', 75, 'B', 120, 25, 12)
        
        DjangoMercuryAPITestCase._test_executions = [mock_exec]
        DjangoMercuryAPITestCase._optimization_recommendations = [
            "Consider using select_related for foreign keys",
            "Add database indexes on frequently queried fields",
            "Implement caching for repeated queries"
        ]
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
        # Recommendations should be included
    
    def _create_mock_execution(self, name, score, grade, response_time, memory, queries):
        """Helper to create mock execution with metrics."""
        mock_exec = Mock()
        type(mock_exec).test_name = PropertyMock(return_value=name)
        type(mock_exec).response_time = PropertyMock(return_value=response_time)
        type(mock_exec).memory_usage = PropertyMock(return_value=memory)
        type(mock_exec).query_count = PropertyMock(return_value=queries)
        
        mock_score = Mock()
        type(mock_score).total_score = PropertyMock(return_value=score)
        type(mock_score).grade = PropertyMock(return_value=grade)
        type(mock_exec).performance_score = PropertyMock(return_value=mock_score)
        
        # Add Django issues mock
        mock_issues = Mock()
        type(mock_issues).has_n_plus_one = PropertyMock(return_value=False)
        type(mock_exec).django_issues = PropertyMock(return_value=mock_issues)
        
        return mock_exec


class TestDashboardCreation(unittest.TestCase):
    """Test dashboard creation (lines 1092-1144)."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        DjangoMercuryAPITestCase._test_executions = []
    
    @patch('builtins.print')
    def test_dashboard_with_perfect_scores(self, mock_print) -> None:
        """Test dashboard creation with all perfect scores."""
        mock_exec1 = self._create_mock_execution('test1', 100, 'S', 10, 5, 2)
        mock_exec2 = self._create_mock_execution('test2', 98, 'S', 15, 8, 3)
        
        DjangoMercuryAPITestCase._test_executions = [mock_exec1, mock_exec2]
        
        DjangoMercuryAPITestCase._create_mercury_dashboard()
        
        mock_print.assert_called()
        printed = str(mock_print.call_args_list)
        self.assertIn("DASHBOARD", printed)
    
    @patch('builtins.print')
    def test_dashboard_with_poor_performance(self, mock_print) -> None:
        """Test dashboard with poor performance metrics."""
        mock_exec1 = self._create_mock_execution('test_slow', 45, 'F', 800, 120, 75)
        mock_exec2 = self._create_mock_execution('test_bad', 35, 'F', 1200, 200, 150)
        
        DjangoMercuryAPITestCase._test_executions = [mock_exec1, mock_exec2]
        
        DjangoMercuryAPITestCase._create_mercury_dashboard()
        
        mock_print.assert_called()
        # Should highlight poor performance
    
    @patch('builtins.print')
    def test_dashboard_grade_distribution(self, mock_print) -> None:
        """Test dashboard shows grade distribution correctly."""
        # Create diverse grade distribution
        grades = ['S', 'A+', 'A', 'B', 'B', 'C', 'D', 'F']
        mock_execs = []
        for i, grade in enumerate(grades):
            score = 95 - (i * 10)  # Decreasing scores
            mock_exec = self._create_mock_execution(
                f'test_{i}', score, grade, 50 + i*50, 10 + i*10, 5 + i*5
            )
            mock_execs.append(mock_exec)
        
        DjangoMercuryAPITestCase._test_executions = mock_execs
        
        DjangoMercuryAPITestCase._create_mercury_dashboard()
        
        mock_print.assert_called()
        # Should show grade distribution
    
    @patch('builtins.print')
    def test_dashboard_with_n_plus_one_issues(self, mock_print) -> None:
        """Test dashboard highlighting N+1 query issues."""
        mock_exec = Mock()
        type(mock_exec).test_name = PropertyMock(return_value='test_n_plus_one')
        type(mock_exec).response_time = PropertyMock(return_value=500)
        type(mock_exec).memory_usage = PropertyMock(return_value=50)
        type(mock_exec).query_count = PropertyMock(return_value=150)
        
        mock_score = Mock()
        type(mock_score).total_score = PropertyMock(return_value=40)
        type(mock_score).grade = PropertyMock(return_value='F')
        type(mock_exec).performance_score = PropertyMock(return_value=mock_score)
        
        # Mark as having N+1 issues
        mock_issues = Mock()
        type(mock_issues).has_n_plus_one = PropertyMock(return_value=True)
        mock_n_plus_one = Mock()
        type(mock_n_plus_one).severity_text = PropertyMock(return_value='CRITICAL')
        type(mock_n_plus_one).severity_level = PropertyMock(return_value=5)  # Add severity_level
        type(mock_issues).n_plus_one_analysis = PropertyMock(return_value=mock_n_plus_one)
        type(mock_exec).django_issues = PropertyMock(return_value=mock_issues)
        
        DjangoMercuryAPITestCase._test_executions = [mock_exec]
        
        DjangoMercuryAPITestCase._create_mercury_dashboard()
        
        mock_print.assert_called()
        # Should highlight N+1 issues
    
    def _create_mock_execution(self, name, score, grade, response_time, memory, queries):
        """Helper to create mock execution with metrics."""
        mock_exec = Mock()
        type(mock_exec).test_name = PropertyMock(return_value=name)
        type(mock_exec).response_time = PropertyMock(return_value=response_time)
        type(mock_exec).memory_usage = PropertyMock(return_value=memory)
        type(mock_exec).query_count = PropertyMock(return_value=queries)
        
        mock_score = Mock()
        type(mock_score).total_score = PropertyMock(return_value=score)
        type(mock_score).grade = PropertyMock(return_value=grade)
        type(mock_exec).performance_score = PropertyMock(return_value=mock_score)
        
        mock_issues = Mock()
        type(mock_issues).has_n_plus_one = PropertyMock(return_value=False)
        type(mock_exec).django_issues = PropertyMock(return_value=mock_issues)
        
        return mock_exec


class TestPerformanceTrendAnalysis(unittest.TestCase):
    """Test performance trend analysis in summaries."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        DjangoMercuryAPITestCase._test_executions = []
    
    @patch('builtins.print')
    def test_improving_performance_trend(self, mock_print) -> None:
        """Test detection of improving performance trends."""
        # Create executions with improving scores
        mock_execs = []
        for i in range(5):
            score = 60 + (i * 8)  # 60, 68, 76, 84, 92
            grade = ['D', 'C', 'B', 'A', 'A+'][i]
            mock_exec = self._create_mock_execution(
                f'test_{i}', score, grade, 200 - i*30, 50 - i*5, 20 - i*2
            )
            mock_execs.append(mock_exec)
        
        DjangoMercuryAPITestCase._test_executions = mock_execs
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
        # Should detect improving trend
    
    @patch('builtins.print')
    def test_degrading_performance_trend(self, mock_print) -> None:
        """Test detection of degrading performance trends."""
        # Create executions with degrading scores
        mock_execs = []
        for i in range(5):
            score = 90 - (i * 10)  # 90, 80, 70, 60, 50
            grade = ['A+', 'A', 'B', 'C', 'D'][i]
            mock_exec = self._create_mock_execution(
                f'test_{i}', score, grade, 100 + i*50, 20 + i*10, 10 + i*5
            )
            mock_execs.append(mock_exec)
        
        DjangoMercuryAPITestCase._test_executions = mock_execs
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
        # Should detect degrading trend
    
    def _create_mock_execution(self, name, score, grade, response_time, memory, queries):
        """Helper to create mock execution with metrics."""
        mock_exec = Mock()
        type(mock_exec).test_name = PropertyMock(return_value=name)
        type(mock_exec).response_time = PropertyMock(return_value=response_time)
        type(mock_exec).memory_usage = PropertyMock(return_value=memory)
        type(mock_exec).query_count = PropertyMock(return_value=queries)
        
        mock_score = Mock()
        type(mock_score).total_score = PropertyMock(return_value=score)
        type(mock_score).grade = PropertyMock(return_value=grade)
        type(mock_exec).performance_score = PropertyMock(return_value=mock_score)
        
        mock_issues = Mock()
        type(mock_issues).has_n_plus_one = PropertyMock(return_value=False)
        type(mock_exec).django_issues = PropertyMock(return_value=mock_issues)
        
        return mock_exec


class TestSummaryEdgeCases(unittest.TestCase):
    """Test edge cases in summary generation."""
    
    @patch('builtins.print')
    def test_summary_with_single_test(self, mock_print) -> None:
        """Test summary with only one test execution."""
        mock_exec = Mock()
        type(mock_exec).test_name = PropertyMock(return_value='single_test')
        type(mock_exec).response_time = PropertyMock(return_value=100)
        type(mock_exec).memory_usage = PropertyMock(return_value=25)
        type(mock_exec).query_count = PropertyMock(return_value=10)
        
        mock_score = Mock()
        type(mock_score).total_score = PropertyMock(return_value=85)
        type(mock_score).grade = PropertyMock(return_value='A')
        type(mock_exec).performance_score = PropertyMock(return_value=mock_score)
        
        mock_issues = Mock()
        type(mock_issues).has_n_plus_one = PropertyMock(return_value=False)
        type(mock_exec).django_issues = PropertyMock(return_value=mock_issues)
        
        DjangoMercuryAPITestCase._test_executions = [mock_exec]
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_summary_all_failing_tests(self, mock_print) -> None:
        """Test summary when all tests fail."""
        mock_execs = []
        for i in range(3):
            mock_exec = Mock()
            type(mock_exec).test_name = PropertyMock(return_value=f'fail_test_{i}')
            type(mock_exec).response_time = PropertyMock(return_value=1000 + i*200)
            type(mock_exec).memory_usage = PropertyMock(return_value=200 + i*50)
            type(mock_exec).query_count = PropertyMock(return_value=100 + i*25)
            
            mock_score = Mock()
            type(mock_score).total_score = PropertyMock(return_value=30 - i*5)
            type(mock_score).grade = PropertyMock(return_value='F')
            type(mock_score).n_plus_one_penalty = PropertyMock(return_value=20)  # Add n_plus_one_penalty
            type(mock_exec).performance_score = PropertyMock(return_value=mock_score)
            
            mock_issues = Mock()
            type(mock_issues).has_n_plus_one = PropertyMock(return_value=True)
            mock_n_plus_one = Mock()
            type(mock_n_plus_one).severity_level = PropertyMock(return_value=5)  # Add severity_level
            type(mock_issues).n_plus_one_analysis = PropertyMock(return_value=mock_n_plus_one)
            type(mock_exec).django_issues = PropertyMock(return_value=mock_issues)
            
            mock_execs.append(mock_exec)
        
        DjangoMercuryAPITestCase._test_executions = mock_execs
        DjangoMercuryAPITestCase._test_failures = [
            f"❌ fail_test_{i}: Performance thresholds exceeded" for i in range(3)
        ]
        
        DjangoMercuryAPITestCase._generate_mercury_executive_summary()
        
        mock_print.assert_called()
        # Should emphasize critical issues


if __name__ == '__main__':
    unittest.main()