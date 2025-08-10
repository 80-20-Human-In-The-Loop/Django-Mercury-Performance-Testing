"""Django Mercury API Test Case - Intelligent Performance Testing Framework

Mercury is an advanced, self-managing performance testing framework for Django REST Framework
applications. It provides automatic performance monitoring, intelligent threshold management,
N+1 query detection, and comprehensive optimization guidance with minimal configuration.

Key Features:
    - Automatic performance monitoring for all test methods
    - Smart threshold management based on operation complexity
    - Advanced N+1 query pattern detection with severity analysis
    - Performance scoring system with letter grades (S, A+, A, B, C, D, F)
    - Executive summaries with actionable optimization recommendations
    - Educational guidance for performance issues

Usage:
    class MyAPITestCase(DjangoMercuryAPITestCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.configure_mercury(
                enabled=True,
                auto_scoring=True,
            )

        def test_user_list_performance(self):
            # Mercury automatically monitors this test
            response = self.client.get('/api/users/')
            self.assertEqual(response.status_code, 200)
            # Performance is automatically analyzed and scored

Author: EduLite Performance Team
Version: 2.0.0
"""

# backend/performance_testing/python_bindings/django_integration_mercury.py
# A streamlined, intelligent system that automatically handles performance monitoring, scoring, analysis, and optimization guidance with minimal boilerplate code.

import time
import sys
import os
import json
import inspect

from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Union, Tuple
from dataclasses import dataclass, asdict
from functools import wraps
from datetime import datetime

from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework.response import Response

from .django_integration import DjangoPerformanceAPITestCase
from .monitor import EnhancedPerformanceMetrics_Python, EnhancedPerformanceMonitor
from .monitor import monitor_django_view, DjangoPerformanceIssues, PerformanceScore
from .colors import colors, EduLiteColorScheme
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceBaseline:
    """Performance baseline for tracking historical performance metrics."""

    operation_type: str
    avg_response_time: float
    avg_memory_usage: float
    avg_query_count: float
    sample_count: int
    last_updated: str

    def update_with_new_measurement(self, metrics):
        """Update baseline with a new measurement using weighted average (10% new, 90% old)."""
        # Handle both EnhancedPerformanceMetrics_Python objects and simple dicts
        if hasattr(metrics, "response_time"):
            response_time = metrics.response_time
            memory_usage = metrics.memory_usage
            query_count = metrics.query_count
        else:
            # Assume it's a dict-like object
            response_time = metrics.get("response_time", 0)
            memory_usage = metrics.get("memory_usage", 0)
            query_count = metrics.get("query_count", 0)

        # Use weighted average: 90% old, 10% new for smoothing
        self.avg_response_time = 0.9 * self.avg_response_time + 0.1 * response_time
        self.avg_memory_usage = 0.9 * self.avg_memory_usage + 0.1 * memory_usage
        self.avg_query_count = 0.9 * self.avg_query_count + 0.1 * query_count
        self.sample_count += 1
        self.last_updated = datetime.now().isoformat()


@dataclass
class OperationProfile:
    """Smart operation profile that adapts thresholds based on complexity."""

    operation_name: str
    expected_query_range: Tuple[int, int]  # (min, max) expected queries
    response_time_baseline: float  # Expected baseline response time
    memory_overhead_tolerance: float  # Acceptable memory overhead
    complexity_factors: Dict[str, Any]  # Factors affecting complexity

    def calculate_dynamic_thresholds(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate dynamic thresholds based on operation context."""
        # Base thresholds
        thresholds = {
            "response_time": self.response_time_baseline,
            "memory_usage": 80 + self.memory_overhead_tolerance,  # Django baseline + tolerance
            "query_count": self.expected_query_range[1],
        }

        # Adjust based on context
        if "page_size" in context:
            page_size = context["page_size"]
            # Linear scaling for pagination
            thresholds["response_time"] *= 1 + page_size / 100
            thresholds["memory_usage"] += page_size * 0.5  # ~0.5MB per additional item

        if "include_relations" in context and context["include_relations"]:
            # Additional queries and processing for relations
            thresholds["response_time"] *= 1.5
            thresholds["query_count"] += 3
            thresholds["memory_usage"] += 10

        if "search_complexity" in context:
            complexity = context["search_complexity"]
            if complexity == "high":
                thresholds["response_time"] *= 2
                thresholds["query_count"] += 2

        return thresholds


@dataclass
class TestExecutionSummary:
    """Comprehensive summary of test execution with insights."""

    total_tests: int
    passed_tests: int
    failed_tests: int
    average_score: float
    grade_distribution: Dict[str, int]
    critical_issues: List[str]
    optimization_opportunities: List[str]
    performance_trends: Dict[str, str]
    execution_time: float
    recommendations: List[str]


class MercuryThresholdOverride:
    """Context manager for temporarily overriding performance thresholds."""

    def __init__(self, test_instance):
        self.test_instance = test_instance
        self.original_thresholds = None
        self.override_thresholds = None

    def __call__(self, thresholds: Dict[str, Union[int, float]]):
        """Set the thresholds to override."""
        self.override_thresholds = thresholds
        return self

    def __enter__(self):
        """Apply the threshold overrides."""
        self.original_thresholds = self.test_instance._per_test_thresholds
        self.test_instance._per_test_thresholds = self.override_thresholds
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore the original thresholds."""
        self.test_instance._per_test_thresholds = self.original_thresholds


class DjangoMercuryAPITestCase(DjangoPerformanceAPITestCase):
    """
    🎓 Django Mercury Learning & Investigation Test Case
    
    A performance learning tool for understanding and investigating Django app performance.
    Use this to discover performance issues, then switch to DjangoPerformanceAPITestCase
    for production tests.
    
    Purpose: LEARNING AND INVESTIGATION, not production testing
    
    What it does:
    - Automatically monitors every test method
    - Identifies the #1 performance issue to investigate
    - Provides focused, educational guidance
    - Teaches you what to look for and why
    
    Workflow:
    1. Inherit from DjangoMercuryAPITestCase to investigate
    2. Run tests to discover performance patterns
    3. Learn from the focused insights
    4. Switch to DjangoPerformanceAPITestCase with specific assertions
    
    Note: Output is intentionally minimal and educational.
    For detailed metrics, use DjangoPerformanceAPITestCase.
    """

    # Class-level configuration - Optimized for learning
    _mercury_enabled = True
    _auto_scoring = True  # Show grade to understand performance level
    _auto_threshold_adjustment = True  # Smart defaults based on operation
    _generate_summaries = True  # One summary at the end
    _verbose_reporting = False  # Keep output focused
    _educational_guidance = True  # Core feature: teaching
    _summary_generated = False  # Prevent double printing
    _learning_mode = True  # New flag to indicate learning focus

    # Custom performance thresholds (set by user in setUpClass)
    _custom_thresholds: Optional[Dict[str, Any]] = None

    # Per-test threshold overrides (temporary, resets after each test)
    _per_test_thresholds: Optional[Dict[str, Any]] = None

    # Class-level tracking
    _test_executions: List[EnhancedPerformanceMetrics_Python] = []
    _test_failures: List[str] = []
    _optimization_recommendations: List[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._operation_profiles = self._initialize_operation_profiles()
        self._test_context: Dict[str, Any] = {}

    def setUp(self):
        """Enhanced setup with automatic Mercury initialization."""
        super().setUp()
        # Silent setup - let the results do the talking

    def _initialize_operation_profiles(self) -> Dict[str, OperationProfile]:
        """Initialize smart operation profiles for different API operations with realistic Django defaults."""
        return {
            "list_view": OperationProfile(
                operation_name="list_view",
                expected_query_range=(3, 25),  # More realistic for Django with potential N+1 issues
                response_time_baseline=200,  # More forgiving default
                memory_overhead_tolerance=30,  # Allow for serialization overhead
                complexity_factors={"pagination": True, "serialization": "moderate"},
            ),
            "detail_view": OperationProfile(
                operation_name="detail_view",
                expected_query_range=(1, 10),  # Allow for related model access
                response_time_baseline=150,
                memory_overhead_tolerance=20,
                complexity_factors={"relations": "optional", "serialization": "simple"},
            ),
            "create_view": OperationProfile(
                operation_name="create_view",
                expected_query_range=(2, 15),  # Allow for validation queries and signals
                response_time_baseline=250,
                memory_overhead_tolerance=25,
                complexity_factors={"validation": True, "signals": True},
            ),
            "update_view": OperationProfile(
                operation_name="update_view",
                expected_query_range=(2, 12),
                response_time_baseline=200,
                memory_overhead_tolerance=20,
                complexity_factors={"validation": True, "signals": True},
            ),
            "delete_view": OperationProfile(
                operation_name="delete_view",
                expected_query_range=(1, 30),  # DELETE operations naturally require more queries
                response_time_baseline=300,  # Allow more time for cascade deletions
                memory_overhead_tolerance=40,
                complexity_factors={
                    "cascade_deletions": True,
                    "foreign_keys": True,
                    "cleanup": True,
                },
            ),
            "search_view": OperationProfile(
                operation_name="search_view",
                expected_query_range=(1, 30),  # Search can be complex
                response_time_baseline=300,
                memory_overhead_tolerance=40,
                complexity_factors={"filtering": True, "ordering": True},
            ),
            "authentication": OperationProfile(
                operation_name="authentication",
                expected_query_range=(0, 8),  # Auth can involve several lookups
                response_time_baseline=100,
                memory_overhead_tolerance=15,
                complexity_factors={"security": True},
            ),
        }

    def _detect_operation_type(self, test_method_name: str, test_function: Callable) -> str:
        """Intelligently detect operation type from test method name and function."""
        method_name = test_method_name.lower()

        # Analyze method name patterns - prioritize DELETE detection
        if any(keyword in method_name for keyword in ["delete", "destroy", "remove"]):
            return "delete_view"
        elif any(keyword in method_name for keyword in ["list", "get_all", "index"]):
            return "list_view"
        elif any(keyword in method_name for keyword in ["detail", "retrieve", "get_single"]):
            return "detail_view"
        elif any(keyword in method_name for keyword in ["create", "post", "add"]):
            return "create_view"
        elif any(keyword in method_name for keyword in ["update", "put", "patch", "edit"]):
            return "update_view"
        elif any(keyword in method_name for keyword in ["search", "filter", "query"]):
            return "search_view"

        # Analyze test function for HTTP method patterns - prioritize DELETE detection
        if test_function:
            try:
                source = inspect.getsource(test_function)
                if "client.delete" in source:
                    return "delete_view"
                elif "client.get" in source and any(
                    param in source for param in ["?search=", "?filter=", "?q="]
                ):
                    return "search_view"
                elif "client.get" in source and ("/" in source and not "list" in method_name):
                    return "detail_view"
                elif "client.get" in source:
                    return "list_view"
                elif "client.post" in source:
                    return "create_view"
                elif any(method in source for method in ["client.put", "client.patch"]):
                    return "update_view"
            except (OSError, TypeError):
                # If we can't get source, fall back to method name analysis
                pass

        # Smart fallback based on common patterns
        if "can_" in method_name or "cannot_" in method_name:
            # Permission/authorization tests - analyze further
            if "delete" in method_name:
                return "delete_view"
            elif "update" in method_name or "edit" in method_name:
                return "update_view"
            elif "create" in method_name or "add" in method_name:
                return "create_view"
            else:
                return "detail_view"  # Most permission tests are about viewing

        # Default fallback - be more intelligent
        return "detail_view"  # Changed from 'list_view' to more neutral default

    def _try_extract_threshold_setting(self, test_function: Callable) -> None:
        """Try to extract and execute threshold setting from test method source."""
        try:
            import ast
            import re

            # Get the source code of the test function
            source = inspect.getsource(test_function)

            # Look for set_test_performance_thresholds call
            pattern = r"self\.set_test_performance_thresholds\(\s*({[^}]+})\s*\)"
            match = re.search(pattern, source)

            if match:
                # Extract the threshold dictionary
                threshold_dict_str = match.group(1)

                # Safely evaluate the dictionary
                try:
                    # Parse the dictionary string into an AST
                    tree = ast.parse(threshold_dict_str, mode="eval")

                    # Only allow dict literals with string keys and numeric values
                    if isinstance(tree.body, ast.Dict):
                        thresholds = {}
                        for key, value in zip(tree.body.keys, tree.body.values):
                            if isinstance(key, ast.Str) and isinstance(
                                value, (ast.Num, ast.Constant)
                            ):
                                key_str = key.s if hasattr(key, "s") else str(key.value)
                                value_num = value.n if hasattr(value, "n") else value.value
                                thresholds[key_str] = value_num

                        if thresholds:
                            # Set the thresholds
                            self._per_test_thresholds = thresholds

                except (ValueError, SyntaxError, AttributeError):
                    # If parsing fails, ignore and continue
                    pass

        except (OSError, TypeError, ImportError):
            # If we can't get source or parse it, ignore and continue
            pass

    def _extract_test_context(self, test_function: Callable) -> Dict[str, Any]:
        """Extract context information from test function for smart threshold adjustment."""
        context = {}

        if test_function:
            try:
                source = inspect.getsource(test_function)

                # Detect pagination
                if "page_size" in source:
                    # Try to extract page_size value
                    import re

                    match = re.search(r"page_size[=:](\d+)", source)
                    if match:
                        context["page_size"] = int(match.group(1))
                    else:
                        context["page_size"] = 20  # Default assumption

                # Detect relation includes
                if any(
                    keyword in source
                    for keyword in ["select_related", "prefetch_related", "include"]
                ):
                    context["include_relations"] = True

                # Detect search complexity
                if any(keyword in source for keyword in ["search", "filter", "Q("]):
                    if any(
                        complex_pattern in source
                        for complex_pattern in ["Q(", "__icontains", "__in"]
                    ):
                        context["search_complexity"] = "high"
                    else:
                        context["search_complexity"] = "medium"

            except Exception:
                pass  # Fallback gracefully if source analysis fails

        return context

    def _calculate_intelligent_thresholds(
        self, operation_type: str, context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate intelligent thresholds based on operation type, context, and custom overrides."""

        # Priority: per-test overrides > class-wide custom thresholds > intelligent defaults
        if self._per_test_thresholds:
            # Use per-test thresholds directly if provided
            thresholds = {
                "response_time": self._per_test_thresholds.get("response_time_ms", 500),
                "memory_usage": 80 + self._per_test_thresholds.get("memory_overhead_mb", 50),
                "query_count": self._per_test_thresholds.get("query_count_max", 50),
            }
            return thresholds
        elif self._custom_thresholds:
            # Use custom thresholds directly if provided
            thresholds = {
                "response_time": self._custom_thresholds.get("response_time_ms", 500),
                "memory_usage": 80 + self._custom_thresholds.get("memory_overhead_mb", 50),
                "query_count": self._custom_thresholds.get("query_count_max", 50),
            }
            return thresholds

        # Get operation profile for defaults
        profile = self._operation_profiles.get(
            operation_type, self._operation_profiles["list_view"]
        )

        # Calculate dynamic thresholds
        thresholds = profile.calculate_dynamic_thresholds(context)

        return thresholds

    def _generate_contextual_recommendations(
        self, metrics: EnhancedPerformanceMetrics_Python, operation_type: str
    ) -> List[str]:
        """Generate contextual optimization recommendations based on operation type and issues."""
        recommendations = []

        # Get base recommendations from metrics
        base_recommendations = metrics._get_recommendations()
        recommendations.extend(base_recommendations)

        # Add operation-specific recommendations
        if operation_type == "list_view":
            if metrics.query_count > 5:
                recommendations.append(
                    "🔧 List View: Implement select_related() and prefetch_related() for all foreign keys"
                )
                recommendations.append(
                    "📄 List View: Consider implementing cursor pagination for large datasets"
                )

            if metrics.response_time > 200:
                recommendations.append(
                    "⚡ List View: Add database indexes for filtering/ordering fields"
                )
                recommendations.append(
                    "💾 List View: Implement caching for frequently accessed list data"
                )

        elif operation_type == "detail_view":
            if metrics.query_count > 3:
                recommendations.append(
                    "🔧 Detail View: Use select_related() for all foreign keys in the queryset"
                )

            if metrics.memory_overhead > 15:
                recommendations.append(
                    "💾 Detail View: Review serializer field selection - consider using 'fields' parameter"
                )

        elif operation_type == "create_view":
            if metrics.query_count > 8:
                recommendations.append(
                    "🔧 Create View: Consider optimizing Django signals - use bulk_create() where possible"
                )
                recommendations.append(
                    "🔧 Create View: Review post_save signals for unnecessary database queries"
                )
                recommendations.append(
                    "🔧 Create View: Consider combining related object creation into fewer transactions"
                )

            if metrics.response_time > 300:
                recommendations.append(
                    "⚡ Create View: Move heavy signal processing to background tasks (Celery)"
                )
                recommendations.append(
                    "⚡ Create View: Consider using select_for_update() to prevent race conditions"
                )
                recommendations.append(
                    "⚡ Create View: Cache validation queries (username/email uniqueness)"
                )

            if metrics.query_count > 5:
                recommendations.append(
                    "🔧 Create View: Consider using get_or_create() instead of separate queries"
                )
                recommendations.append(
                    "🔧 Create View: Review serializer validation - combine database lookups"
                )

        elif operation_type == "delete_view":
            if metrics.query_count > 15:
                recommendations.append(
                    "🗑️ Delete View: Consider database-level CASCADE constraints for better performance"
                )

            if metrics.response_time > 500:
                recommendations.append(
                    "🚀 Delete View: Consider implementing soft deletes for complex relationships"
                )
                recommendations.append(
                    "📋 Delete View: Queue deletion operations for background processing with Celery"
                )

        elif operation_type == "search_view":
            if metrics.response_time > 300:
                recommendations.append("🔍 Search View: Add database indexes for search fields")
                recommendations.append(
                    "🔍 Search View: Consider using full-text search (PostgreSQL) or Elasticsearch"
                )

            if metrics.query_count > 10:
                recommendations.append(
                    "🔧 Search View: Optimize search querysets with select_related/prefetch_related"
                )

        # Add executive-level recommendations for high-impact issues
        if metrics.django_issues.has_n_plus_one:
            severity = metrics.django_issues.n_plus_one_analysis.severity_text
            if severity in ["SEVERE", "CRITICAL"]:
                recommendations.insert(
                    0,
                    "🚨 EXECUTIVE PRIORITY: N+1 query issue will impact production performance significantly",
                )
                recommendations.insert(
                    1,
                    "💼 Business Impact: This issue can cause database overload and slow user experience",
                )

        return recommendations

    def _check_educational_opportunities(
        self, 
        test_name: str, 
        metrics: "EnhancedPerformanceMetrics_Python", 
        operation_type: str, 
        context: Dict[str, Any]
    ) -> None:
        """Check for educational opportunities and trigger interventions when appropriate.
        
        This method integrates with the interactive educational system to provide
        learning moments based on actual test performance data.
        
        Args:
            test_name: Name of the test method
            metrics: Performance metrics from the test
            operation_type: Type of operation (list_view, create_view, etc.)
            context: Test context information
        """
        try:
            from django_mercury.cli.educational.interactive_ui import InteractiveUI
            from django_mercury.cli.educational.quiz_system import QuizSystem
            from django_mercury.cli.educational.progress_tracker import ProgressTracker
            from django_mercury.python_bindings.educational_monitor import EducationalMonitor
            
            # Initialize educational components if needed
            if not hasattr(self, '_educational_ui'):
                self._educational_ui = InteractiveUI()
                self._educational_progress = ProgressTracker()
                self._educational_quiz = QuizSystem(
                    console=self._educational_ui.console,
                    progress_tracker=self._educational_progress
                )
                self._educational_monitor = EducationalMonitor(
                    console=self._educational_ui.console,
                    quiz_system=self._educational_quiz,
                    progress_tracker=self._educational_progress,
                    interactive_mode=not os.environ.get('MERCURY_AGENT_MODE') == 'true'
                )
            
            # Check for various learning opportunities based on metrics
            issues_found = []
            
            # N+1 Query Detection
            if (hasattr(metrics, 'django_issues') and 
                metrics.django_issues and 
                metrics.django_issues.has_n_plus_one):
                issues_found.append({
                    'type': 'n_plus_one_queries',
                    'severity': metrics.django_issues.n_plus_one_analysis.severity_text,
                    'query_count': metrics.query_count,
                    'message': f"N+1 queries detected: {metrics.query_count} queries executed"
                })
            
            # High Query Count (even without N+1)
            elif metrics.query_count > 10:
                issues_found.append({
                    'type': 'high_query_count', 
                    'query_count': metrics.query_count,
                    'message': f"High query count: {metrics.query_count} queries executed"
                })
            
            # Slow Response Time
            if metrics.response_time > 200:
                issues_found.append({
                    'type': 'slow_response_time',
                    'response_time': metrics.response_time,
                    'message': f"Slow response time: {metrics.response_time:.2f}ms"
                })
            
            # High Memory Usage
            if metrics.memory_usage > 50:
                issues_found.append({
                    'type': 'memory_optimization',
                    'memory_usage': metrics.memory_usage,
                    'message': f"High memory usage: {metrics.memory_usage:.2f}MB"
                })
            
            # Poor Performance Score
            if (hasattr(metrics, 'performance_score') and 
                metrics.performance_score and 
                metrics.performance_score.total_score < 70):
                issues_found.append({
                    'type': 'general_performance',
                    'score': metrics.performance_score.total_score,
                    'grade': metrics.performance_score.letter_grade,
                    'message': f"Performance score: {metrics.performance_score.letter_grade} ({metrics.performance_score.total_score:.0f}/100)"
                })
            
            # If educational opportunities exist, handle them
            if issues_found:
                for issue in issues_found:
                    # Record the learning opportunity
                    self._educational_progress.record_concept_learned(issue['type'])
                    
                    # Handle the issue educationally if interactive
                    if self._educational_monitor.interactive_mode:
                        self._educational_monitor.handle_performance_issue(
                            test=test_name,
                            error_msg=issue['message']
                        )
                    
                    # Check if we should show a quiz for this concept
                    if (self._educational_quiz and 
                        self._educational_progress.should_show_quiz(issue['type'])):
                        
                        # Get contextual quiz for this specific issue
                        quiz = self._educational_quiz.create_contextual_quiz(
                            issue['type'], issue
                        )
                        
                        if quiz and self._educational_monitor.interactive_mode:
                            self._educational_quiz.ask_quiz(
                                quiz=quiz,
                                context=f"Based on {test_name} performance analysis"
                            )
            
            # Even if no issues, check for learning opportunities on good performance
            elif (hasattr(metrics, 'performance_score') and 
                  metrics.performance_score and 
                  metrics.performance_score.total_score >= 90):
                
                # Celebrate excellent performance occasionally
                import random
                if random.random() < 0.1 and self._educational_monitor.interactive_mode:  # 10% chance
                    self._educational_ui.show_celebration(
                        f"Excellent performance in {test_name}! "
                        f"Grade: {metrics.performance_score.letter_grade}"
                    )
                    
                    # Maybe ask a quiz about what made this test perform well
                    excellence_quiz = self._educational_quiz.get_quiz_for_concept("general_performance")
                    if excellence_quiz and random.random() < 0.3:  # 30% chance
                        self._educational_quiz.ask_quiz(
                            quiz=excellence_quiz,
                            context=f"Understanding why {test_name} performed excellently"
                        )
                        
        except ImportError:
            # Educational components not available, skip silently
            pass
        except Exception as e:
            # Log educational system errors but don't break tests
            logger.debug(f"Educational system error in {test_name}: {e}")

    def _auto_wrap_test_method(self, original_method: Callable) -> Callable:
        """Automatically wrap test methods with performance monitoring."""

        @wraps(original_method)
        def wrapped_test_method(self_inner):
            if not self._mercury_enabled:
                return original_method(self_inner)

            # Detect operation type and context
            operation_type = self._detect_operation_type(original_method.__name__, original_method)
            context = self._extract_test_context(original_method)

            # Create operation name
            operation_name = f"{self.__class__.__name__}.{original_method.__name__}"

            # Try to extract and execute threshold setting from test method
            self_inner._try_extract_threshold_setting(original_method)

            # Calculate thresholds now that per-test thresholds might be set
            context["max_response_time"] = (
                self._per_test_thresholds.get("response_time_ms", 500)
                if self._per_test_thresholds
                else 500
            )
            thresholds = (
                self._calculate_intelligent_thresholds(operation_type, context)
                if self._auto_threshold_adjustment
                else {}
            )

            # Set up monitoring
            def test_function():
                return original_method(self_inner)

            test_executed = False
            metrics = None
            response_time = None

            try:
                # Capture test context information from the original method
                import inspect

                test_file = inspect.getfile(original_method)
                test_line = original_method.__code__.co_firstlineno
                test_method = original_method.__name__

                # Run comprehensive analysis with intelligent settings, but catch threshold failures
                start_time = time.perf_counter()
                try:

                    # Run analysis with test context and educational guidance
                    metrics: EnhancedPerformanceMetrics_Python = (
                        self_inner.run_comprehensive_analysis(
                            operation_name=operation_name,
                            test_function=test_function,
                            operation_type=operation_type,
                            expect_response_under=thresholds.get("response_time"),
                            expect_memory_under=thresholds.get("memory_usage"),
                            expect_queries_under=thresholds.get("query_count"),
                            print_analysis=False if self._learning_mode else self._verbose_reporting,
                            show_scoring=False if self._learning_mode else self._auto_scoring,
                            auto_detect_n_plus_one=True,
                            test_file=test_file,
                            test_line=test_line,
                            test_method=test_method,
                            enable_educational_guidance=self._educational_guidance,
                            operation_context=context,
                        )
                    )
                    test_executed = True
                    context["response_time"] = metrics.response_time  # directly from monitor
                    
                    # Enhanced Educational Integration - Always check for learning opportunities
                    if os.environ.get('MERCURY_EDUCATIONAL_MODE') == 'true' and metrics:
                        self_inner._check_educational_opportunities(
                            test_method or operation_name,
                            metrics,
                            operation_type,
                            context
                        )
                except Exception as monitor_exception:
                    response_time = (
                        time.perf_counter() - start_time
                    ) * 1000  # from python time (monitor failed)
                    context["response_time"] = response_time
                    # If the monitor failed, we still want to capture metrics if they exist
                    # Try to get metrics from the monitor even if it threw an exception
                    if "Performance thresholds exceeded" in str(monitor_exception):
                        # This is likely a threshold failure, try to extract metrics from the monitor
                        # We'll catch the exception and re-raise it after tracking
                        test_executed = True
                        
                        # Check for educational mode and trigger intervention
                        if os.environ.get('MERCURY_EDUCATIONAL_MODE') == 'true':
                            try:
                                from django_mercury.python_bindings.educational_monitor import EducationalMonitor
                                from django_mercury.cli.educational.interactive_ui import InteractiveUI
                                
                                # Create educational components
                                ui = InteractiveUI()
                                monitor = EducationalMonitor(
                                    console=ui.console,
                                    interactive_mode=True
                                )
                                
                                # Handle the performance issue educationally
                                monitor.handle_performance_issue(
                                    test=test_method or operation_name,
                                    error_msg=str(monitor_exception)
                                )
                            except ImportError:
                                # Educational components not available, continue normally
                                pass
                        
                        raise monitor_exception
                    else:
                        # Some other error, re-raise immediately
                        raise

            except Exception as e:
                error_msg = str(e)

                # Provide educational guidance for threshold failures
                if "Performance thresholds exceeded" in error_msg and self._educational_guidance:
                    context["message"] = (
                        f"Exceded {context['max_response_time']}ms by {round(context['response_time'] - context['max_response_time'], 2)}ms"
                    )
                    self_inner._provide_threshold_guidance(
                        original_method.__name__, error_msg, operation_type, context
                    )

                self_inner._test_failures.append(f"❌ {original_method.__name__}: {error_msg}")

                # For threshold failures, we might still be able to get metrics
                # Let's try to run the test function directly with monitoring to get metrics
                if "Performance thresholds exceeded" in error_msg and test_executed:
                    try:
                        # Run without thresholds to get metrics
                        monitor = self_inner.monitor_django_view(f"{operation_name}.metrics_only")
                        with monitor:
                            test_function()
                        metrics = monitor.metrics
                    except Exception as e:
                        # If this fails too, we can't get metrics
                        logger.warning(f"Failed to get metrics in Mercury test: {e}")
                        pass

                # Always re-raise to fail the test
                raise

            finally:
                # Always track execution if we got metrics (even if test failed)
                if test_executed and metrics:

                    # Generate contextual recommendations
                    recommendations = self_inner._generate_contextual_recommendations(
                        metrics, operation_type
                    )
                    self_inner._optimization_recommendations.extend(recommendations)

                    # ALWAYS track execution for summary (even if test failed)
                    self_inner._test_executions.append(metrics)

                    # In learning mode, only show critical issues per test
                    if self._learning_mode and not self._verbose_reporting:
                        # Only show output if there's something to learn
                        if metrics.performance_score.grade in ['D', 'F'] or (
                            metrics.django_issues.has_n_plus_one and 
                            metrics.django_issues.n_plus_one_analysis.severity_level > 0 and
                            metrics.django_issues.n_plus_one_analysis.query_count > 0
                        ):
                            # Show ONE key learning point per test
                            test_display_name = f"{original_method.__name__}"
                            
                            if metrics.django_issues.has_n_plus_one and metrics.django_issues.n_plus_one_analysis.query_count > 0:
                                print(f"\n💡 {test_display_name}: N+1 Query Pattern Detected ({metrics.django_issues.n_plus_one_analysis.query_count} queries)")
                                print(f"   → Fix: Use select_related() or prefetch_related()")
                            elif metrics.response_time > 200:
                                print(f"\n⏱️  {test_display_name}: Slow Response ({metrics.response_time:.0f}ms)")
                                print(f"   → Investigate: Database indexes, query optimization")
                            elif metrics.query_count > 20:
                                print(f"\n🗃️  {test_display_name}: High Query Count ({metrics.query_count} queries)")
                                print(f"   → Consider: Query optimization, caching")

                # Reset per-test thresholds after each test
                self_inner._per_test_thresholds = None

            return metrics

        return wrapped_test_method

    def _provide_threshold_guidance(
        self, test_name: str, error_msg: str, operation_type: str, context: Dict[str, Any]
    ):
        """Provide educational guidance when performance thresholds are exceeded."""
        self._provide_educational_guidance(test_name, error_msg, operation_type, context)

    def _provide_technical_diagnostics(
        self, test_name: str, error_msg: str, operation_type: str, context: Dict[str, Any]
    ):
        """Provide concise technical diagnostics for performance issues."""
        # Get file location context using improved stack frame walking
        import inspect

        frame = inspect.currentframe()
        test_file = "unknown"
        test_line = 0
        actual_test_name = test_name

        # Walk up the stack to find the actual test file (skip Mercury framework)
        try:
            while frame:
                frame_info = inspect.getframeinfo(frame)
                filename = frame_info.filename
                function = frame_info.function

                # Skip Mercury framework files
                if "performance_testing" in filename:
                    frame = frame.f_back
                    continue

                # Look for actual test files with test methods
                if "/tests/" in filename and (function.startswith("test_") or "test_" in function):
                    test_file = filename
                    test_line = frame_info.lineno
                    actual_test_name = function
                    break

                frame = frame.f_back
        except Exception:
            pass  # Fallback to basic file detection

        # Extract relative path for cleaner display
        if test_file != "unknown":
            try:
                from pathlib import Path

                test_file = str(Path(test_file).relative_to(Path.cwd()))
            except ValueError:
                # If relative path fails, just use the filename
                test_file = Path(test_file).name

        # Parse error message for specific metrics
        response_time = None
        query_count = None
        expected_time = None
        expected_queries = None

        if "Response time" in error_msg:
            import re

            time_match = re.search(r"Response time (\d+\.?\d*)ms > (\d+)ms", error_msg)
            if time_match:
                response_time = float(time_match.group(1))
                expected_time = int(time_match.group(2))

        if "Query count" in error_msg:
            import re

            query_match = re.search(r"Query count (\d+) > (\d+)", error_msg)
            if query_match:
                query_count = int(query_match.group(1))
                expected_queries = int(query_match.group(2))

        # Calculate performance score based on available data
        score = "F"  # Default failing score
        if response_time and expected_time:
            if response_time <= expected_time * 1.2:
                score = "D"
            elif response_time <= expected_time * 2:
                score = "C"

        print(
            f"\n{colors.colorize('🚨 Performance Issue', EduLiteColorScheme.CRITICAL, bold=True)}: {colors.colorize(test_name, EduLiteColorScheme.WARNING)}"
        )
        print(
            f"{colors.colorize('📁 File', EduLiteColorScheme.INFO)}: {colors.colorize(f'{test_file}:{test_line}', EduLiteColorScheme.ACCENT)}"
        )

        if response_time and expected_time:
            over_time = response_time - expected_time
            print(
                f"{colors.colorize('⏱️  Response', EduLiteColorScheme.WARNING)}: {colors.colorize(f'{response_time:.0f}ms', EduLiteColorScheme.CRITICAL)} (expected <{expected_time}ms) {colors.colorize(f'+{over_time:.0f}ms over', EduLiteColorScheme.CRITICAL)}"
            )

        if query_count and expected_queries:
            extra_queries = query_count - expected_queries
            print(
                f"{colors.colorize('🗃️  Queries', EduLiteColorScheme.WARNING)}: {colors.colorize(str(query_count), EduLiteColorScheme.CRITICAL)} (expected <{expected_queries}) {colors.colorize(f'+{extra_queries} extra queries', EduLiteColorScheme.CRITICAL)}"
            )

        print(
            f"{colors.colorize('🎯 Score', EduLiteColorScheme.INFO)}: {colors.colorize(f'{score} (failing)', EduLiteColorScheme.CRITICAL)}"
        )

        # Provide specific technical fix
        print(f"\n{colors.colorize('🔧 Fix', EduLiteColorScheme.OPTIMIZATION)}: ", end="")
        if operation_type == "detail_view" and query_count and query_count > 3:
            print(
                colors.colorize(
                    "Add select_related() to UserRetrieveView queryset",
                    EduLiteColorScheme.OPTIMIZATION,
                )
            )
            print(
                f"  {colors.colorize('→', EduLiteColorScheme.FADE)} queryset = User.objects.select_related('userprofile').prefetch_related('groups')"
            )
        elif operation_type == "list_view" and query_count and query_count > 5:
            print(
                colors.colorize(
                    "Implement select_related/prefetch_related for list queries",
                    EduLiteColorScheme.OPTIMIZATION,
                )
            )
        elif response_time and response_time > 200:
            print(
                colors.colorize(
                    "Check database indexes and optimize queries", EduLiteColorScheme.OPTIMIZATION
                )
            )
        else:
            print(
                colors.colorize(
                    f"Adjust thresholds: response_time_ms: {int(response_time * 1.5) if response_time else 200}, query_count_max: {query_count + 2 if query_count else 10}",
                    EduLiteColorScheme.OPTIMIZATION,
                )
            )

    def _provide_educational_guidance(
        self, test_name: str, error_msg: str, operation_type: str, context: Dict[str, Any]
    ):
        """Provide educational guidance with backward compatibility."""
        # Always show EDUCATIONAL for test compatibility
        print(f"\n📚 MERCURY EDUCATIONAL GUIDANCE")
        print(f"{'=' * 60}")
        print(f"🎯 Test: {test_name}")
        print(f"⚠️  Default thresholds exceeded")
        print(f"🔍 Operation Type: {operation_type}")

        # Parse and display exceedance amounts
        if "Response time" in error_msg:
            import re

            time_match = re.search(r"Response time (\d+\.?\d*)ms > (\d+)ms", error_msg)
            if time_match:
                actual_time = float(time_match.group(1))
                expected_time = int(time_match.group(2))
                over_time = actual_time - expected_time
                percent_over = ((actual_time / expected_time) - 1) * 100
                print(
                    f"⏱️  {colors.colorize('Response Time:', EduLiteColorScheme.WARNING)} {colors.colorize(f'{actual_time:.0f}ms', EduLiteColorScheme.CRITICAL)} (limit: {expected_time}ms)"
                )
                print(
                    f"   {colors.colorize(f'→ {over_time:.0f}ms over limit ({percent_over:.0f}% exceeded)', EduLiteColorScheme.CRITICAL)}"
                )

        if "Query count" in error_msg:
            import re

            query_match = re.search(r"Query count (\d+) > (\d+)", error_msg)
            if query_match:
                actual_queries = int(query_match.group(1))
                expected_queries = int(query_match.group(2))
                extra_queries = actual_queries - expected_queries
                percent_over = ((actual_queries / expected_queries) - 1) * 100
                print(
                    f"🗃️  {colors.colorize('Query Count:', EduLiteColorScheme.WARNING)} {colors.colorize(str(actual_queries), EduLiteColorScheme.CRITICAL)} (limit: {expected_queries})"
                )
                print(
                    f"   {colors.colorize(f'→ {extra_queries} extra queries ({percent_over:.0f}% exceeded)', EduLiteColorScheme.CRITICAL)}"
                )

        if "Memory usage" in error_msg:
            import re

            mem_match = re.search(r"Memory usage (\d+\.?\d*)MB > (\d+)MB", error_msg)
            if mem_match:
                actual_mem = float(mem_match.group(1))
                expected_mem = int(mem_match.group(2))
                over_mem = actual_mem - expected_mem
                percent_over = ((actual_mem / expected_mem) - 1) * 100
                print(
                    f"🧠 {colors.colorize('Memory Usage:', EduLiteColorScheme.WARNING)} {colors.colorize(f'{actual_mem:.1f}MB', EduLiteColorScheme.CRITICAL)} (limit: {expected_mem}MB)"
                )
                print(
                    f"   {colors.colorize(f'→ {over_mem:.1f}MB over limit ({percent_over:.0f}% exceeded)', EduLiteColorScheme.CRITICAL)}"
                )

        # The rest of the original educational guidance code...
        if "Query count" in error_msg:
            print(
                f"\n💡 {colors.colorize('SOLUTION: Configure Custom Query Thresholds', EduLiteColorScheme.OPTIMIZATION, bold=True)}"
            )
            if operation_type == "delete_view":
                print(f"   DELETE operations naturally require more database queries due to:")
                print(f"   • CASCADE relationships (UserProfile -> User)")
                print(f"   • Foreign key cleanup (ProfileFriendRequest references)")
                print(f"   • Many-to-many cleanup (friends relationship)")
                print(f"   • Related model cleanup (privacy settings, notifications)")
            elif operation_type == "create_view":
                print(
                    f"   CREATE operations with complex models often require more database queries due to:"
                )
                print(f"   • Django signals creating related objects")
                print(f"   • Validation queries (email uniqueness, username uniqueness)")
                print(f"   • Transaction handling across multiple models")
            else:
                print(
                    f"   Consider optimizing queries with select_related() and prefetch_related()"
                )

        # Generate recommended thresholds based on actual values
        recommended_thresholds = {}
        if "Response time" in error_msg:
            import re

            time_match = re.search(r"Response time (\d+\.?\d*)ms", error_msg)
            if time_match:
                actual_time = float(time_match.group(1))
                # Recommend 50% buffer above actual time
                recommended_thresholds["response_time_ms"] = int(actual_time * 1.5)

        if "Query count" in error_msg:
            import re

            query_match = re.search(r"Query count (\d+)", error_msg)
            if query_match:
                actual_queries = int(query_match.group(1))
                # Recommend 20% buffer above actual queries
                recommended_thresholds["query_count_max"] = int(actual_queries * 1.2) + 1

        if "Memory usage" in error_msg:
            import re

            mem_match = re.search(r"Memory usage (\d+\.?\d*)MB", error_msg)
            if mem_match:
                actual_mem = float(mem_match.group(1))
                # Recommend 10% buffer above actual memory
                recommended_thresholds["memory_overhead_mb"] = (
                    int(actual_mem - 80) + 5
                )  # Subtract Django baseline

        print(
            f"\n{colors.colorize('🛠️  Quick Fix: Add to your test class:', EduLiteColorScheme.ACCENT, bold=True)}"
        )
        if recommended_thresholds:
            print(f"   cls.set_performance_thresholds({recommended_thresholds})")
        else:
            print(
                f"   cls.set_performance_thresholds({{'response_time_ms': 200, 'query_count_max': 10}})"
            )
        print(f"\n{colors.colorize('=' * 60, EduLiteColorScheme.BORDER)}")

    @classmethod
    def set_performance_thresholds(cls, thresholds: Dict[str, Union[int, float]]):
        """
        Set custom performance thresholds for all tests in this class.

        Args:
            thresholds: Dictionary with keys:
                - response_time_ms: Maximum response time in milliseconds
                - query_count_max: Maximum number of database queries
                - memory_overhead_mb: Maximum memory overhead in MB

        Example:
            cls.set_performance_thresholds({
                'response_time_ms': 300,
                'query_count_max': 15,
                'memory_overhead_mb': 40,
            })
        """
        cls._custom_thresholds = thresholds
        logger.info("🎯 Custom performance thresholds configured")
        for key, value in thresholds.items():
            unit = (
                "ms"
                if "time" in key
                else "MB" if "memory" in key else "%" if "efficiency" in key else ""
            )
            logger.info(f"   • {key}: {value}{unit}")

    def set_test_performance_thresholds(self, thresholds: Dict[str, Union[int, float]]):
        """
        Set custom performance thresholds for the current test only.
        These thresholds override class-wide thresholds for this test only.
        After the test completes, thresholds revert to class-wide configuration.

        Args:
            thresholds: Dictionary with keys:
                - response_time_ms: Maximum response time in milliseconds
                - query_count_max: Maximum number of database queries
                - memory_overhead_mb: Maximum memory overhead in MB

        Example:
            def test_expensive_operation(self):
                # Allow higher thresholds for this specific test
                self.set_test_performance_thresholds({
                    'response_time_ms': 1000,  # Allow 1 second for this test
                    'query_count_max': 50,     # Allow more queries
                })

                response = self.client.get('/api/expensive-operation/')
                self.assertEqual(response.status_code, 200)
        """
        self._per_test_thresholds = thresholds
        logger.info("⚡ Per-test performance thresholds set")
        for key, value in thresholds.items():
            unit = (
                "ms"
                if "time" in key
                else "MB" if "memory" in key else "%" if "efficiency" in key else ""
            )
            logger.info(f"   • {key}: {value}{unit} (this test only)")

    @property
    def mercury_override_thresholds(self):
        """
        Context manager for temporarily overriding performance thresholds.

        Example:
            def test_something(self):
                with self.mercury_override_thresholds({'query_count_max': 50}):
                    # Code that might need more queries
                    response = self.client.get('/api/complex-endpoint/')
                    self.assertEqual(response.status_code, 200)
        """
        return MercuryThresholdOverride(self)

    def __new__(cls, *args, **kwargs):
        """Auto-wrap test methods with Mercury monitoring."""
        instance = super().__new__(cls)

        # Auto-wrap all test methods
        for attr_name in dir(cls):
            if attr_name.startswith("test_") and callable(getattr(cls, attr_name)):
                original_method = getattr(cls, attr_name)
                if not hasattr(original_method, "_mercury_wrapped"):
                    wrapped_method = instance._auto_wrap_test_method(original_method)
                    wrapped_method._mercury_wrapped = True
                    setattr(instance, attr_name, wrapped_method.__get__(instance, cls))

        return instance

    @classmethod
    def tearDownClass(cls):
        """Generate comprehensive Mercury performance summary."""
        super().tearDownClass()

        if not cls._mercury_enabled or not cls._test_executions or cls._summary_generated:
            return

        cls._summary_generated = True  # Prevent double printing
        cls._generate_mercury_executive_summary()

    @classmethod
    def _generate_mercury_executive_summary(cls):
        """Generate executive summary with backward compatibility."""
        
        # Always create dashboard for test compatibility
        if cls._test_executions:
            cls._create_mercury_dashboard()
        
        # Show ANALYSIS header for test compatibility
        print(f"\n{colors.colorize('🎯 MERCURY INTELLIGENT PERFORMANCE ANALYSIS', EduLiteColorScheme.ACCENT, bold=True)}")
        print(f"{colors.colorize('=' * 80, EduLiteColorScheme.BORDER)}")
        
        if not cls._test_executions:
            print(f"{colors.colorize('No performance data collected.', EduLiteColorScheme.WARNING)}")
            return

        # Calculate aggregate statistics
        total_tests = len(cls._test_executions)
        scores = [m.performance_score.total_score for m in cls._test_executions]
        grades = [m.performance_score.grade for m in cls._test_executions]

        avg_score = sum(scores) / len(scores)
        avg_response_time = sum(m.response_time for m in cls._test_executions) / total_tests
        avg_query_count = sum(m.query_count for m in cls._test_executions) / total_tests

        # Grade distribution
        from collections import Counter

        grade_counts = Counter(grades)

        # Critical issues analysis (safely handle Mock objects in tests)
        n_plus_one_tests = 0
        try:
            n_plus_one_tests = sum(
                1
                for m in cls._test_executions
                if m.django_issues.has_n_plus_one
                and m.django_issues.n_plus_one_analysis.severity_level > 0
                and m.django_issues.n_plus_one_analysis.query_count > 0  # Exclude false positives
            )
        except (AttributeError, TypeError):
            # Handle Mock objects in tests
            pass
        critical_issues = []

        if n_plus_one_tests > 0:
            critical_issues.append(
                f"N+1 Query Issues: {n_plus_one_tests}/{total_tests} tests affected"
            )

        slow_tests = sum(1 for m in cls._test_executions if m.response_time > 300)
        if slow_tests > 0:
            critical_issues.append(
                f"Slow Response Times: {slow_tests}/{total_tests} tests over 300ms"
            )

        # Grade distribution
        print(f"\n📊 {colors.colorize('GRADE DISTRIBUTION', EduLiteColorScheme.INFO, bold=True)}")
        for grade in ["S", "A+", "A", "B", "C", "D", "F"]:
            count = grade_counts.get(grade, 0)
            if count > 0:
                percentage = (count / total_tests) * 100
                grade_color = {
                    "S": EduLiteColorScheme.EXCELLENT,
                    "A+": EduLiteColorScheme.EXCELLENT,
                    "A": EduLiteColorScheme.GOOD,
                    "B": EduLiteColorScheme.ACCEPTABLE,
                    "C": EduLiteColorScheme.WARNING,
                    "D": EduLiteColorScheme.CRITICAL,
                    "F": EduLiteColorScheme.CRITICAL,
                }.get(grade, EduLiteColorScheme.TEXT)

                print(
                    f"   {colors.colorize(f'{grade}: {count} tests ({percentage:.1f}%)', grade_color)}"
                )

        # Critical issues
        if critical_issues:
            print(
                f"\n🚨 {colors.colorize('CRITICAL ISSUES', EduLiteColorScheme.CRITICAL, bold=True)}"
            )
            for issue in critical_issues:
                print(f"   • {colors.colorize(issue, EduLiteColorScheme.CRITICAL)}")

        # Test failures
        if cls._test_failures:
            print(f"\n⚠️  {colors.colorize('ISSUES', EduLiteColorScheme.WARNING, bold=True)}")
            for failure in cls._test_failures[:5]:  # Show first 5
                print(f"   • {colors.colorize(failure, EduLiteColorScheme.WARNING)}")

            if len(cls._test_failures) > 5:
                print(
                    f"   • {colors.colorize(f'... and {len(cls._test_failures) - 5} more issues', EduLiteColorScheme.FADE)}"
                )

        # Top optimization opportunities
        if cls._optimization_recommendations:
            print(
                f"\n💡 {colors.colorize('TOP OPTIMIZATION OPPORTUNITIES', EduLiteColorScheme.OPTIMIZATION, bold=True)}"
            )

            # Prioritize recommendations by impact and remove duplicates more aggressively
            recommendations = list(
                set(cls._optimization_recommendations)
            )  # Remove exact duplicates

            # Remove similar/redundant recommendations
            unique_recs = []
            seen_keywords = set()
            for rec in recommendations:
                # Check if we've already seen a similar recommendation
                rec_keywords = set(rec.lower().split())
                if not any(keyword in seen_keywords for keyword in rec_keywords):
                    unique_recs.append(rec)
                    seen_keywords.update(rec_keywords)

            priority_keywords = ["URGENT", "EXECUTIVE PRIORITY", "Business Impact", "N+1"]

            priority_recs = [
                r for r in unique_recs if any(keyword in r for keyword in priority_keywords)
            ]
            other_recs = [
                r for r in unique_recs if not any(keyword in r for keyword in priority_keywords)
            ]

            # Show priority recommendations first - limit to avoid spam
            for rec in priority_recs[:2]:  # Reduced from 3 to 2
                print(f"   🔥 {colors.colorize(rec, EduLiteColorScheme.CRITICAL)}")

            for rec in other_recs[:3]:  # Reduced from 5 to 3
                print(f"   • {colors.colorize(rec, EduLiteColorScheme.OPTIMIZATION)}")

        # Potential improvements
        cls._show_optimization_potential()

        # Executive summary
        print(f"\n💼 {colors.colorize('EXECUTIVE SUMMARY', EduLiteColorScheme.ACCENT, bold=True)}")

        if avg_score >= 80:
            print(
                f"   ✅ {colors.colorize('Performance is generally acceptable for production', EduLiteColorScheme.SUCCESS)}"
            )
        elif avg_score >= 60:
            print(
                f"   ⚠️  {colors.colorize('Performance needs optimization before production', EduLiteColorScheme.WARNING)}"
            )
        else:
            print(
                f"   🚨 {colors.colorize('Critical performance issues must be addressed', EduLiteColorScheme.CRITICAL)}"
            )

        if n_plus_one_tests > total_tests * 0.3:
            print(
                f"   🔥 {colors.colorize('N+1 query issues are affecting multiple endpoints', EduLiteColorScheme.CRITICAL)}"
            )
            print(
                f"   💼 {colors.colorize('Business Impact: Database load will increase significantly with user growth', EduLiteColorScheme.WARNING)}"
            )

        print(
            f"\n{colors.colorize('Mercury Analysis Complete - Performance Intelligence Enabled', EduLiteColorScheme.ACCENT, bold=True)}"
        )
        print(f"{colors.colorize('=' * 80, EduLiteColorScheme.BORDER)}")

    @classmethod
    def _calculate_overall_grade(cls, avg_score: float) -> str:
        """Calculate overall grade from average score."""
        if avg_score >= 95:
            return "S"
        elif avg_score >= 90:
            return "A+"
        elif avg_score >= 80:
            return "A"
        elif avg_score >= 70:
            return "B"
        elif avg_score >= 60:
            return "C"
        elif avg_score >= 50:
            return "D"
        else:
            return "F"

    @classmethod
    def _show_optimization_potential(cls):
        """Show potential score improvements if issues are fixed."""
        if not cls._test_executions:
            return

        n_plus_one_tests = [m for m in cls._test_executions if m.django_issues.has_n_plus_one]

        if n_plus_one_tests:
            current_avg = sum(m.performance_score.total_score for m in cls._test_executions) / len(
                cls._test_executions
            )

            # Calculate potential improvement
            potential_scores = []
            for m in cls._test_executions:
                if m.django_issues.has_n_plus_one:
                    potential_score = min(
                        100,
                        m.performance_score.total_score + m.performance_score.n_plus_one_penalty,
                    )
                    potential_scores.append(potential_score)
                else:
                    potential_scores.append(m.performance_score.total_score)

    @classmethod
    def _generate_learning_summary(cls):
        """Generate focused learning summary for investigation mode."""
        if not cls._test_executions:
            return
            
        # Count critical issues (safely handle Mock objects in tests)
        n_plus_one_tests = 0
        try:
            n_plus_one_tests = sum(
                1 for m in cls._test_executions
                if m.django_issues.has_n_plus_one 
                and m.django_issues.n_plus_one_analysis.query_count > 0
            )
        except (AttributeError, TypeError):
            # Handle Mock objects in tests
            pass
        
        slow_tests = sum(1 for m in cls._test_executions if m.response_time > 200)
        high_query_tests = sum(1 for m in cls._test_executions if m.query_count > 20)
        failed_tests = len([m for m in cls._test_executions if m.performance_score.grade in ['D', 'F']])
        
        # Calculate averages
        total_tests = len(cls._test_executions)
        avg_response = sum(m.response_time for m in cls._test_executions) / total_tests
        avg_queries = sum(m.query_count for m in cls._test_executions) / total_tests
        
        print("\n" + "="*60)
        print("🎓 MERCURY LEARNING SUMMARY")
        print("="*60)
        
        # Show the #1 issue to investigate
        if n_plus_one_tests > 0:
            print(f"\n📍 PRIMARY ISSUE: N+1 Query Pattern")
            print(f"   Found in {n_plus_one_tests}/{total_tests} tests")
            print(f"   → Next Step: Add select_related() and prefetch_related()")
            print(f"   → Learn more: https://docs.djangoproject.com/en/stable/topics/db/optimization/")
        elif slow_tests > total_tests / 2:
            print(f"\n📍 PRIMARY ISSUE: Slow Response Times")
            print(f"   {slow_tests}/{total_tests} tests over 200ms (avg: {avg_response:.0f}ms)")
            print(f"   → Next Step: Profile slow views and add database indexes")
        elif high_query_tests > 0:
            print(f"\n📍 PRIMARY ISSUE: High Query Count")
            print(f"   {high_query_tests}/{total_tests} tests with >20 queries")
            print(f"   → Next Step: Optimize queries and implement caching")
        else:
            print(f"\n✅ Performance looks good!")
            print(f"   Avg response: {avg_response:.0f}ms")
            print(f"   Avg queries: {avg_queries:.1f}")
        
        # Quick stats
        print(f"\n📊 Quick Stats:")
        print(f"   Tests run: {total_tests}")
        print(f"   Avg response time: {avg_response:.0f}ms")
        print(f"   Avg query count: {avg_queries:.1f}")
        
        # Show grades distribution only if there are issues
        if failed_tests > 0:
            grades = [m.performance_score.grade for m in cls._test_executions]
            from collections import Counter
            grade_counts = Counter(grades)
            print(f"   Grades: {', '.join(f'{g}:{c}' for g, c in sorted(grade_counts.items()))}")
        
        # Actionable next step
        print(f"\n💡 Ready to optimize?")
        print(f"   Switch to DjangoPerformanceAPITestCase for production tests")
        print(f"   Add specific assertions: assertResponseTimeLess(), assertQueriesLess()")
        
        print("="*60 + "\n")
    
    @classmethod
    def _create_mercury_dashboard(cls):
        """Create enhanced dashboard for Mercury test suite summary."""
        if not cls._test_executions:
            return

        # Calculate aggregate metrics
        total_tests = len(cls._test_executions)
        avg_response_time = sum(m.response_time for m in cls._test_executions) / total_tests
        avg_memory_usage = sum(m.memory_usage for m in cls._test_executions) / total_tests
        total_queries = sum(m.query_count for m in cls._test_executions)
        avg_query_count = total_queries / total_tests

        # Calculate overall scores
        scores = [m.performance_score.total_score for m in cls._test_executions]
        avg_score = sum(scores) / len(scores)
        overall_grade = cls._calculate_overall_grade(avg_score)

        # Critical issues count (safely handle Mock objects)
        n_plus_one_count = 0
        try:
            n_plus_one_count = sum(
                1
                for m in cls._test_executions
                if m.django_issues.has_n_plus_one
                and m.django_issues.n_plus_one_analysis.severity_level > 0
            )
        except (AttributeError, TypeError):
            # Handle Mock objects in tests
            pass
        slow_tests = sum(1 for m in cls._test_executions if m.response_time > 300)

        # Format performance status
        if avg_score >= 90:
            status = "EXCELLENT"
            status_color = EduLiteColorScheme.EXCELLENT
        elif avg_score >= 80:
            status = "GOOD"
            status_color = EduLiteColorScheme.GOOD
        elif avg_score >= 60:
            status = "ACCEPTABLE"
            status_color = EduLiteColorScheme.ACCEPTABLE
        else:
            status = "NEEDS IMPROVEMENT"
            status_color = EduLiteColorScheme.CRITICAL

        # Create dashboard
        # Note: Using print() for the dashboard as it's user-facing test output
        print(
            f"\n{colors.colorize(f'🎨 MERCURY PERFORMANCE DASHBOARD - {cls.__name__}', EduLiteColorScheme.ACCENT, bold=True)}"
        )
        print(
            f"{colors.colorize('╭─────────────────────────────────────────────────────────────╮', EduLiteColorScheme.BORDER)}"
        )
        print(
            f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('🚀 Overall Status:', EduLiteColorScheme.TEXT, bold=True)} {colors.colorize(status, status_color, bold=True):<20} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
        )
        print(
            f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('🎓 Overall Grade:', EduLiteColorScheme.TEXT)} {colors.colorize(f'{overall_grade} ({avg_score:.1f}/100)', status_color, bold=True):<25} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
        )
        print(
            f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('📊 Tests Executed:', EduLiteColorScheme.TEXT)} {total_tests:<25} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
        )
        print(
            f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('⏱️  Avg Response Time:', EduLiteColorScheme.TEXT)} {avg_response_time:.1f}ms{'':<20} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
        )
        print(
            f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('🧠 Avg Memory Usage:', EduLiteColorScheme.TEXT)} {avg_memory_usage:.1f}MB{'':<20} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
        )
        print(
            f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('🗃️  Total Queries:', EduLiteColorScheme.TEXT)} {total_queries} ({avg_query_count:.1f} avg){'':<10} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
        )

        if n_plus_one_count > 0:
            print(
                f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('🚨 N+1 Issues:', EduLiteColorScheme.CRITICAL)} {n_plus_one_count}/{total_tests} tests affected{'':<10} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
            )

        if slow_tests > 0:
            print(
                f"{colors.colorize('│', EduLiteColorScheme.BORDER)} {colors.colorize('⏳ Slow Tests:', EduLiteColorScheme.WARNING)} {slow_tests}/{total_tests} over 300ms{'':<12} {colors.colorize('│', EduLiteColorScheme.BORDER)}"
            )

        print(
            f"{colors.colorize('╰─────────────────────────────────────────────────────────────╯', EduLiteColorScheme.BORDER)}"
        )

    # Configuration methods for easy customization
    @classmethod
    def configure_mercury(
        cls,
        enabled: bool = True,
        auto_scoring: bool = True,
        auto_threshold_adjustment: bool = True,
        generate_summaries: bool = True,
        verbose_reporting: bool = False,
        educational_guidance: bool = True,
    ):
        """Configure Mercury behavior for the test class."""
        cls._mercury_enabled = enabled
        cls._auto_scoring = auto_scoring
        cls._auto_threshold_adjustment = auto_threshold_adjustment
        cls._generate_summaries = generate_summaries
        cls._verbose_reporting = verbose_reporting
        cls._educational_guidance = educational_guidance

        # Reset tracking variables for fresh test run
        cls._test_executions = []
        cls._test_failures = []
        cls._optimization_recommendations = []
        cls._summary_generated = False

    # Convenience methods that maintain backward compatibility
    def assert_mercury_performance_excellent(self, metrics: EnhancedPerformanceMetrics_Python):
        """Assert that performance meets excellent standards (Grade A or above)."""
        self.assertGreaterEqual(
            metrics.performance_score.total_score,
            80,
            f"Performance score {metrics.performance_score.total_score:.1f} below excellent threshold (80)",
        )
        self.assertLess(
            metrics.response_time,
            100,
            "Response time should be under 100ms for excellent performance",
        )
        self.assertFalse(
            metrics.django_issues.has_n_plus_one, "N+1 queries prevent excellent performance"
        )

    def assert_mercury_performance_production_ready(
        self, metrics: EnhancedPerformanceMetrics_Python
    ):
        """Assert that performance is ready for production deployment."""
        self.assertGreaterEqual(
            metrics.performance_score.total_score,
            60,
            f"Performance score {metrics.performance_score.total_score:.1f} below production threshold (60)",
        )
        self.assertLess(
            metrics.response_time, 300, "Response time should be under 300ms for production"
        )

        if metrics.django_issues.has_n_plus_one:
            severity = metrics.django_issues.n_plus_one_analysis.severity_level
            self.assertLess(
                severity, 4, f"N+1 severity {severity} too high for production (must be < 4)"
            )
