"""
Investigative Monitor for Django Mercury

This module provides performance issue discovery and workflow guidance for the
two-phase Django Mercury testing approach:

1. INVESTIGATION PHASE (DjangoMercuryAPITestCase) - Use this monitor to discover issues
2. DOCUMENTATION PHASE (DjangoPerformanceAPITestCase) - Use specific assertions

The monitor is designed for umbrella investigation and performance issue discovery,
then guides users to transition to explicit documentation tests.
"""

import os
import re
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from .colors import colors, EduLiteColorScheme

    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False


@dataclass
class PerformanceIssue:
    """Represents a discovered performance issue."""

    issue_type: str
    severity: str
    test_name: str
    metrics: Dict[str, Any]
    suggested_assertions: List[str]
    fix_recommendations: List[str]


class InvestigativeMonitor:
    """
    Performance investigation monitor for Django Mercury.

    Focuses on:
    1. Discovering performance issues during umbrella investigation
    2. Generating specific assertions for DjangoPerformanceAPITestCase
    3. Guiding workflow transition from investigation to documentation
    4. Providing targeted fix recommendations

    Does NOT:
    - Provide educational content (handled by plugin system)
    - Interrupt testing flow (minimal output)
    - Duplicate functionality of modern CLI plugins
    """

    def __init__(self, console: Optional[Any] = None, minimal_output: bool = True):
        """
        Initialize the investigative monitor.

        Args:
            console: Rich console for output (optional)
            minimal_output: Whether to keep output minimal and focused
        """
        self.console = console
        self.minimal_output = minimal_output
        self.discovered_issues: List[PerformanceIssue] = []
        self.test_metrics: Dict[str, Dict[str, Any]] = {}

    def analyze_test_performance(
        self, test_name: str, metrics: Dict[str, Any], operation_type: str = "unknown"
    ) -> Optional[PerformanceIssue]:
        """
        Analyze test performance and discover issues.

        Args:
            test_name: Name of the test method
            metrics: Performance metrics from the test
            operation_type: Type of operation (list_view, detail_view, etc.)

        Returns:
            PerformanceIssue if significant issue found, None otherwise
        """
        # Store metrics for summary
        self.test_metrics[test_name] = {"operation_type": operation_type, **metrics}

        # Detect the most significant issue
        issue = self._detect_primary_issue(test_name, metrics, operation_type)

        if issue:
            self.discovered_issues.append(issue)

            # Show minimal guidance if not in quiet mode
            if not self.minimal_output:
                self._show_issue_guidance(issue)

        return issue

    def _detect_primary_issue(
        self, test_name: str, metrics: Dict[str, Any], operation_type: str
    ) -> Optional[PerformanceIssue]:
        """Detect the primary performance issue to focus on."""

        query_count = metrics.get("query_count", 0)
        response_time = metrics.get("response_time", 0)
        memory_usage = metrics.get("memory_usage", 0)
        has_n_plus_one = metrics.get("has_n_plus_one", False)

        # Priority 1: N+1 Query Issues (most critical)
        if has_n_plus_one and query_count > 10:
            return PerformanceIssue(
                issue_type="n_plus_one_queries",
                severity="HIGH",
                test_name=test_name,
                metrics=metrics,
                suggested_assertions=self._generate_n_plus_one_assertions(
                    query_count, operation_type
                ),
                fix_recommendations=self._generate_n_plus_one_fixes(operation_type),
            )

        # Priority 2: High Query Count (even without N+1)
        elif query_count > self._get_query_threshold(operation_type):
            return PerformanceIssue(
                issue_type="high_query_count",
                severity="MEDIUM",
                test_name=test_name,
                metrics=metrics,
                suggested_assertions=self._generate_query_count_assertions(
                    query_count, operation_type
                ),
                fix_recommendations=self._generate_query_optimization_fixes(operation_type),
            )

        # Priority 3: Slow Response Time
        elif response_time > self._get_response_threshold(operation_type):
            return PerformanceIssue(
                issue_type="slow_response",
                severity="MEDIUM",
                test_name=test_name,
                metrics=metrics,
                suggested_assertions=self._generate_response_time_assertions(
                    response_time, operation_type
                ),
                fix_recommendations=self._generate_response_time_fixes(operation_type),
            )

        # Priority 4: High Memory Usage
        elif memory_usage > 50:  # MB
            return PerformanceIssue(
                issue_type="high_memory",
                severity="LOW",
                test_name=test_name,
                metrics=metrics,
                suggested_assertions=self._generate_memory_assertions(memory_usage),
                fix_recommendations=self._generate_memory_optimization_fixes(),
            )

        return None

    def _get_query_threshold(self, operation_type: str) -> int:
        """Get query count threshold based on operation type."""
        thresholds = {
            "list_view": 15,
            "detail_view": 8,
            "create_view": 12,
            "update_view": 10,
            "delete_view": 25,
            "search_view": 20,
        }
        return thresholds.get(operation_type, 10)

    def _get_response_threshold(self, operation_type: str) -> float:
        """Get response time threshold based on operation type."""
        thresholds = {
            "list_view": 200,
            "detail_view": 150,
            "create_view": 250,
            "update_view": 200,
            "delete_view": 300,
            "search_view": 300,
        }
        return thresholds.get(operation_type, 200)

    def _generate_n_plus_one_assertions(self, query_count: int, operation_type: str) -> List[str]:
        """Generate specific assertions for N+1 query issues."""
        # Suggest conservative but realistic limits
        suggested_limit = max(5, query_count // 3)  # Aim for 3x reduction

        assertions = [
            f"self.assertQueriesLess({suggested_limit})",
            f"# Current: {query_count} queries - targeting {suggested_limit} with select_related/prefetch_related",
        ]

        if operation_type == "list_view":
            assertions.append("# List views should use prefetch_related for related models")
        elif operation_type == "detail_view":
            assertions.append("# Detail views should use select_related for ForeignKey fields")

        return assertions

    def _generate_query_count_assertions(self, query_count: int, operation_type: str) -> List[str]:
        """Generate query count assertions for high query count issues."""
        # Be more lenient than N+1, but still encourage optimization
        suggested_limit = max(query_count - 5, query_count // 2)

        return [
            f"self.assertQueriesLess({suggested_limit})",
            f"# Current: {query_count} queries - optimize to reduce database load",
        ]

    def _generate_response_time_assertions(
        self, response_time: float, operation_type: str
    ) -> List[str]:
        """Generate response time assertions."""
        # Add 50% buffer to current time, rounded up
        suggested_limit = int(response_time * 1.5)
        suggested_limit = ((suggested_limit + 49) // 50) * 50  # Round to nearest 50ms

        return [
            f"self.assertResponseTimeLess({suggested_limit})",
            f"# Current: {response_time:.0f}ms - targeting {suggested_limit}ms",
        ]

    def _generate_memory_assertions(self, memory_usage: float) -> List[str]:
        """Generate memory usage assertions."""
        # Add 20% buffer to current usage
        suggested_limit = int(memory_usage * 1.2)

        return [
            f"self.assertMemoryUsageLess({suggested_limit})",
            f"# Current: {memory_usage:.1f}MB - targeting {suggested_limit}MB",
        ]

    def _generate_n_plus_one_fixes(self, operation_type: str) -> List[str]:
        """Generate specific fixes for N+1 issues."""
        if operation_type == "list_view":
            return [
                "Add select_related() for ForeignKey fields",
                "Add prefetch_related() for ManyToMany and reverse ForeignKey fields",
                "Example: Model.objects.select_related('category').prefetch_related('tags')",
            ]
        elif operation_type == "detail_view":
            return [
                "Add select_related() to your queryset",
                "Example: Model.objects.select_related('user', 'category').get(pk=id)",
            ]
        else:
            return [
                "Use select_related() for ForeignKey/OneToOne relationships",
                "Use prefetch_related() for ManyToMany/reverse ForeignKey relationships",
            ]

    def _generate_query_optimization_fixes(self, operation_type: str) -> List[str]:
        """Generate query optimization recommendations."""
        return [
            "Review database queries and add select_related/prefetch_related",
            "Consider adding database indexes for frequently queried fields",
            "Implement query result caching for repeated data access",
        ]

    def _generate_response_time_fixes(self, operation_type: str) -> List[str]:
        """Generate response time optimization recommendations."""
        return [
            "Add database indexes on filtered/ordered fields",
            "Optimize Django ORM queries",
            "Consider implementing caching for expensive operations",
            "Review algorithm complexity in view logic",
        ]

    def _generate_memory_optimization_fixes(self) -> List[str]:
        """Generate memory optimization recommendations."""
        return [
            "Use queryset.iterator() for large datasets",
            "Implement pagination for list views",
            "Use .only() or .values() to limit loaded fields",
            "Clear caches after bulk operations",
        ]

    def _show_issue_guidance(self, issue: PerformanceIssue) -> None:
        """Show minimal guidance for discovered issue."""
        if self.console and RICH_AVAILABLE:
            self._show_rich_guidance(issue)
        else:
            self._show_text_guidance(issue)

    def _show_rich_guidance(self, issue: PerformanceIssue) -> None:
        """Show rich guidance using Rich library."""
        if not RICH_AVAILABLE or not self.console:
            self._show_text_guidance(issue)
            return

        severity_colors = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}

        color = severity_colors.get(issue.severity, "white")

        from rich.panel import Panel

        panel = Panel(
            f"[{color}]🔍 Investigation Found: {issue.issue_type.replace('_', ' ').title()}[/{color}]\n"
            f"Test: {issue.test_name}\n"
            f"Severity: {issue.severity}\n\n"
            f"[bold]Suggested DjangoPerformanceAPITestCase assertion:[/bold]\n"
            f"[green]{issue.suggested_assertions[0]}[/green]",
            title="[bold]Mercury Investigation[/bold]",
            border_style=color,
        )
        self.console.print(panel)

    def _show_text_guidance(self, issue: PerformanceIssue) -> None:
        """Show simple text guidance with color coding."""
        if COLORS_AVAILABLE:
            severity_colors = {
                "HIGH": EduLiteColorScheme.CRITICAL,
                "MEDIUM": EduLiteColorScheme.WARNING,
                "LOW": EduLiteColorScheme.INFO,
            }
            color = severity_colors.get(issue.severity, EduLiteColorScheme.TEXT)

            print(
                f"\n{colors.colorize('🔍 MERCURY INVESTIGATION:', EduLiteColorScheme.ACCENT)} {colors.colorize(issue.issue_type.replace('_', ' ').title(), color)}"
            )
            print(
                f"   {colors.colorize('Test:', EduLiteColorScheme.TEXT)} {colors.colorize(issue.test_name, EduLiteColorScheme.FADE)}"
            )
            print(
                f"   {colors.colorize('Severity:', EduLiteColorScheme.TEXT)} {colors.colorize(issue.severity, color)}"
            )
            print(
                f"   {colors.colorize('→ Suggested assertion:', EduLiteColorScheme.OPTIMIZATION)} {colors.colorize(issue.suggested_assertions[0], EduLiteColorScheme.SUCCESS)}"
            )
        else:
            # Fallback without colors
            print(f"\n🔍 MERCURY INVESTIGATION: {issue.issue_type.replace('_', ' ').title()}")
            print(f"   Test: {issue.test_name}")
            print(f"   Severity: {issue.severity}")
            print(f"   → Suggested assertion: {issue.suggested_assertions[0]}")

    def generate_workflow_transition_summary(self) -> Dict[str, Any]:
        """
        Generate a summary to guide transition from investigation to documentation phase.

        Returns summary with:
        - Discovered issues
        - Suggested DjangoPerformanceAPITestCase code
        - Workflow guidance
        """
        if not self.discovered_issues:
            return {
                "phase": "investigation_complete",
                "status": "no_issues_found",
                "message": "✅ No significant performance issues discovered. Ready for production testing.",
                "next_steps": [
                    "Switch to DjangoPerformanceAPITestCase for production tests",
                    "Add baseline performance assertions to prevent regressions",
                ],
            }

        # Group issues by severity
        high_issues = [i for i in self.discovered_issues if i.severity == "HIGH"]
        medium_issues = [i for i in self.discovered_issues if i.severity == "MEDIUM"]
        low_issues = [i for i in self.discovered_issues if i.severity == "LOW"]

        # Generate transition code
        suggested_assertions = []
        for issue in self.discovered_issues:
            suggested_assertions.extend(issue.suggested_assertions)

        return {
            "phase": "investigation_complete",
            "status": "issues_discovered",
            "total_issues": len(self.discovered_issues),
            "high_priority": len(high_issues),
            "medium_priority": len(medium_issues),
            "low_priority": len(low_issues),
            "primary_issue": (
                high_issues[0]
                if high_issues
                else (medium_issues[0] if medium_issues else low_issues[0])
            ),
            "suggested_assertions": suggested_assertions,
            "next_steps": [
                "🔧 Fix the discovered performance issues",
                "📋 Switch to DjangoPerformanceAPITestCase",
                "✅ Add specific performance assertions",
                "🚀 Run production-ready performance tests",
            ],
            "workflow_guidance": {
                "current_phase": "INVESTIGATION (DjangoMercuryAPITestCase) - TEMPORARY",
                "next_phase": "DOCUMENTATION (DjangoPerformanceAPITestCase) - PERMANENT",
                "transition_trigger": "After fixing discovered issues",
            },
        }

    def get_suggested_performance_test_class(self) -> str:
        """Generate suggested DjangoPerformanceAPITestCase code."""
        if not self.discovered_issues:
            return """
# No issues found - basic performance monitoring
class MyPerformanceTestCase(DjangoPerformanceAPITestCase):
    def test_endpoint_performance(self):
        with self.monitor_django_view("endpoint_performance") as monitor:
            response = self.client.get('/api/endpoint/')
            self.assertEqual(response.status_code, 200)
        
        # Add baseline assertions to prevent regressions
        self.assertResponseTimeLess(200)  # Adjust based on your requirements
        self.assertQueriesLess(10)        # Adjust based on your requirements
"""

        # Generate code with specific assertions based on discovered issues
        assertions = []
        for issue in self.discovered_issues:
            assertions.extend(issue.suggested_assertions)

        assertion_code = "\n        ".join(assertions)

        return f"""
# Performance test based on investigation findings
class MyPerformanceTestCase(DjangoPerformanceAPITestCase):
    def test_endpoint_performance(self):
        with self.monitor_django_view("endpoint_performance") as monitor:
            response = self.client.get('/api/endpoint/')
            self.assertEqual(response.status_code, 200)
        
        # Assertions based on Mercury investigation
        {assertion_code}
"""

    def show_workflow_guidance(self) -> None:
        """Show workflow transition guidance."""
        summary = self.generate_workflow_transition_summary()

        if COLORS_AVAILABLE:
            border = colors.colorize("=" * 60, EduLiteColorScheme.BORDER)
            print(f"\n{border}")
            print(
                colors.colorize(
                    "🎯 MERCURY INVESTIGATION → DOCUMENTATION WORKFLOW",
                    EduLiteColorScheme.ACCENT,
                    bold=True,
                )
            )
            print(border)

            if summary["status"] == "no_issues_found":
                print(
                    f"\n{colors.colorize('✅', EduLiteColorScheme.SUCCESS)} {colors.colorize(summary['message'], EduLiteColorScheme.SUCCESS)}"
                )
            else:
                total_issues_text = f"{summary['total_issues']} issues discovered"
                print(
                    f"\n{colors.colorize('🔍 Investigation Complete:', EduLiteColorScheme.INFO)} {colors.colorize(total_issues_text, EduLiteColorScheme.WARNING)}"
                )

                if summary.get("primary_issue"):
                    issue = summary["primary_issue"]
                    severity_color = (
                        EduLiteColorScheme.CRITICAL
                        if issue.severity == "HIGH"
                        else EduLiteColorScheme.WARNING
                    )
                    print(
                        f"\n{colors.colorize('📍 PRIMARY ISSUE:', EduLiteColorScheme.CRITICAL)} {colors.colorize(issue.issue_type.replace('_', ' ').title(), severity_color)}"
                    )
                    print(
                        f"   {colors.colorize('Test:', EduLiteColorScheme.TEXT)} {colors.colorize(issue.test_name, EduLiteColorScheme.FADE)}"
                    )
                    print(
                        f"   {colors.colorize('Severity:', EduLiteColorScheme.TEXT)} {colors.colorize(issue.severity, severity_color)}"
                    )

            print(f"\n{colors.colorize('🔄 WORKFLOW TRANSITION:', EduLiteColorScheme.ACCENT)}")
            print(
                f"   {colors.colorize('Current:', EduLiteColorScheme.TEXT)} {colors.colorize(summary['workflow_guidance']['current_phase'], EduLiteColorScheme.WARNING)}"
            )
            print(
                f"   {colors.colorize('Next:', EduLiteColorScheme.TEXT)} {colors.colorize(summary['workflow_guidance']['next_phase'], EduLiteColorScheme.SUCCESS)}"
            )

            print(f"\n{colors.colorize('📋 NEXT STEPS:', EduLiteColorScheme.ACCENT)}")
            for step in summary["next_steps"]:
                print(
                    f"   {colors.colorize('•', EduLiteColorScheme.OPTIMIZATION)} {colors.colorize(step, EduLiteColorScheme.TEXT)}"
                )

            # Show suggested code
            if summary["status"] == "issues_discovered":
                print(
                    f"\n{colors.colorize('💻 SUGGESTED PERFORMANCE TEST CODE:', EduLiteColorScheme.ACCENT)}"
                )
                print(colors.colorize("-" * 40, EduLiteColorScheme.BORDER))
                print(
                    colors.colorize(
                        self.get_suggested_performance_test_class(), EduLiteColorScheme.SUCCESS
                    )
                )

            print(border + "\n")
        else:
            # Fallback without colors
            print("\n" + "=" * 60)
            print("🎯 MERCURY INVESTIGATION → DOCUMENTATION WORKFLOW")
            print("=" * 60)

            if summary["status"] == "no_issues_found":
                print(f"\n✅ {summary['message']}")
            else:
                print(f"\n🔍 Investigation Complete: {summary['total_issues']} issues discovered")

                if summary.get("primary_issue"):
                    issue = summary["primary_issue"]
                    print(f"\n📍 PRIMARY ISSUE: {issue.issue_type.replace('_', ' ').title()}")
                    print(f"   Test: {issue.test_name}")
                    print(f"   Severity: {issue.severity}")

            print(f"\n🔄 WORKFLOW TRANSITION:")
            print(f"   Current: {summary['workflow_guidance']['current_phase']}")
            print(f"   Next: {summary['workflow_guidance']['next_phase']}")

            print(f"\n📋 NEXT STEPS:")
            for step in summary["next_steps"]:
                print(f"   • {step}")

            # Show suggested code
            if summary["status"] == "issues_discovered":
                print(f"\n💻 SUGGESTED PERFORMANCE TEST CODE:")
                print("-" * 40)
                print(self.get_suggested_performance_test_class())

            print("=" * 60 + "\n")
