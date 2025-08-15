"""
Explain Plugin for Mercury-Test CLI

Provides educational explanations and context about:
- Django testing concepts
- Performance optimization techniques
- Mercury features and metrics
- Best practices and patterns
- Common issues and solutions

Integrates with the educational content system to provide
contextual help during test execution.
"""

import os
import sys
import json
import random
from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional, Dict, List, Any
from textwrap import dedent, wrap

from django_mercury.cli.plugins.base import MercuryPlugin
from django_mercury.cli.educational.content_manager import ContentManager, QuizQuestion

# Try to import rich for better formatting
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ExplainPlugin(MercuryPlugin):
    """Plugin for interactive learning about Django performance optimization."""
    
    name = "learn"
    description = "Interactive learning with explanations and quizzes"
    priority = 60  # Medium-low priority
    version = "1.0.0"
    
    # Audience targeting
    audiences = ["student"]  # Educational content specifically for learners
    complexity_level = 1  # Simple and approachable
    requires_capabilities = []  # Works with basic terminal
    
    def __init__(self):
        super().__init__()
        self.console = Console() if RICH_AVAILABLE else None
        self.content_manager = ContentManager()
        self.context_stack = []  # Track context for relevant explanations
        self.shown_explanations = set()  # Avoid repeating explanations
        
        # Load explanation database
        self.explanations = self._load_explanations()
    
    def _load_explanations(self) -> Dict[str, Any]:
        """Load the explanation database."""
        # For now, use built-in explanations
        # Later this could load from a JSON file or database
        return {
            "concepts": {
                "n_plus_one": {
                    "title": "N+1 Query Problem",
                    "brief": "Multiple queries for related data that could be fetched in one query",
                    "detailed": dedent("""
                        The N+1 query problem occurs when your code executes N additional 
                        queries to fetch related data that could have been retrieved in 
                        the original query.
                        
                        Example:
                        ```python
                        # Bad: N+1 queries
                        users = User.objects.all()  # 1 query
                        for user in users:
                            print(user.profile.bio)  # N queries
                        
                        # Good: 2 queries total
                        users = User.objects.select_related('profile')
                        for user in users:
                            print(user.profile.bio)  # No additional queries
                        ```
                    """),
                    "solutions": [
                        "Use select_related() for ForeignKey/OneToOne relationships",
                        "Use prefetch_related() for ManyToMany/reverse ForeignKey",
                        "Consider using only() or defer() to limit fields",
                    ],
                    "impact": "high",
                    "category": "database"
                },
                "slow_queries": {
                    "title": "Slow Database Queries",
                    "brief": "Queries taking excessive time to execute",
                    "detailed": dedent("""
                        Slow queries can severely impact application performance.
                        Common causes include:
                        - Missing database indexes
                        - Fetching too much data
                        - Complex joins
                        - Suboptimal query structure
                    """),
                    "solutions": [
                        "Add indexes to frequently queried columns",
                        "Use select_related/prefetch_related appropriately",
                        "Limit results with pagination",
                        "Consider database query optimization",
                        "Use Django Debug Toolbar to analyze queries"
                    ],
                    "impact": "high",
                    "category": "database"
                },
                "memory_leaks": {
                    "title": "Memory Leaks in Tests",
                    "brief": "Memory not being properly released between tests",
                    "detailed": dedent("""
                        Memory leaks in tests can cause:
                        - Slow test execution
                        - Test failures due to resource exhaustion
                        - Unreliable test results
                        
                        Common causes:
                        - Not cleaning up test data
                        - Circular references
                        - Cached objects not being cleared
                    """),
                    "solutions": [
                        "Use tearDown() to clean up resources",
                        "Clear caches between tests",
                        "Use weak references for circular dependencies",
                        "Monitor memory usage with Mercury"
                    ],
                    "impact": "medium",
                    "category": "memory"
                },
                "test_isolation": {
                    "title": "Test Isolation",
                    "brief": "Tests should be independent and not affect each other",
                    "detailed": dedent("""
                        Each test should:
                        - Set up its own data
                        - Clean up after itself
                        - Not depend on other tests
                        - Not affect other tests
                        
                        Poor isolation causes flaky tests and hard-to-debug failures.
                    """),
                    "solutions": [
                        "Use setUp() and tearDown() properly",
                        "Avoid global state modifications",
                        "Use test fixtures appropriately",
                        "Reset database between tests with TransactionTestCase"
                    ],
                    "impact": "high",
                    "category": "testing"
                }
            },
            "metrics": {
                "response_time": {
                    "title": "Response Time",
                    "brief": "Time taken for a request to complete",
                    "thresholds": {
                        "excellent": "< 50ms",
                        "good": "50-200ms",
                        "acceptable": "200-500ms",
                        "poor": "> 500ms"
                    },
                    "factors": [
                        "Database query efficiency",
                        "Template rendering time",
                        "Middleware processing",
                        "Network latency"
                    ]
                },
                "query_count": {
                    "title": "Query Count",
                    "brief": "Number of database queries per request",
                    "thresholds": {
                        "excellent": "< 5",
                        "good": "5-10",
                        "acceptable": "10-20",
                        "poor": "> 20"
                    },
                    "optimization": [
                        "Use select_related/prefetch_related",
                        "Implement query result caching",
                        "Batch similar queries",
                        "Review ORM usage patterns"
                    ]
                },
                "memory_usage": {
                    "title": "Memory Usage",
                    "brief": "Amount of memory consumed during execution",
                    "thresholds": {
                        "excellent": "< 10MB",
                        "good": "10-50MB",
                        "acceptable": "50-100MB",
                        "poor": "> 100MB"
                    },
                    "tips": [
                        "Use generators for large datasets",
                        "Clear unused variables",
                        "Optimize data structures",
                        "Monitor for memory leaks"
                    ]
                }
            },
            "patterns": {
                "repository": {
                    "title": "Repository Pattern",
                    "brief": "Encapsulate data access logic",
                    "example": dedent("""
                        ```python
                        class UserRepository:
                            def get_active_users(self):
                                return User.objects.filter(is_active=True)
                            
                            def get_users_with_profiles(self):
                                return User.objects.select_related('profile')
                        ```
                    """)
                },
                "service_layer": {
                    "title": "Service Layer Pattern",
                    "brief": "Business logic separate from views and models",
                    "example": dedent("""
                        ```python
                        class UserService:
                            def create_user_with_profile(self, user_data, profile_data):
                                with transaction.atomic():
                                    user = User.objects.create(**user_data)
                                    Profile.objects.create(user=user, **profile_data)
                                return user
                        ```
                    """)
                }
            },
            "tips": [
                "Run tests frequently during development",
                "Keep tests fast - aim for < 1 second per test",
                "Use Mercury's educational mode to learn optimization techniques",
                "Profile before optimizing - measure, don't guess",
                "Write tests first (TDD) for better design",
                "Use fixtures and factories for test data",
                "Mock external services in tests",
                "Test edge cases and error conditions"
            ]
        }
    
    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register learn plugin arguments."""
        parser.add_argument(
            '--learn',
            nargs='?',
            const='all',
            help='Interactive learning mode (topic optional, e.g., --learn n_plus_one)'
        )
        
        parser.add_argument(
            '--learn-metrics',
            action='store_true',
            help='Learn about performance metrics and thresholds'
        )
        
        parser.add_argument(
            '--learn-patterns',
            action='store_true',
            help='Learn Django design patterns and best practices'
        )
        
        parser.add_argument(
            '--tips',
            action='store_true',
            help='Show testing and optimization tips'
        )
        
        # Don't register --no-hints if it's already registered by another plugin
        # This is handled by the hints plugin
    
    def can_handle(self, args: Namespace) -> bool:
        """Check if this plugin should handle the request."""
        return any([
            getattr(args, 'learn', None),
            getattr(args, 'learn_metrics', False),
            getattr(args, 'learn_patterns', False),
            getattr(args, 'tips', False)
        ])
    
    def execute(self, args: Namespace) -> int:
        """Execute learning commands."""
        if getattr(args, 'learn', None):
            return self._handle_learn(args.learn)
        
        if getattr(args, 'learn_metrics', False):
            return self._show_metrics_explanation()
        
        if getattr(args, 'learn_patterns', False):
            return self._show_patterns()
        
        if getattr(args, 'tips', False):
            return self._show_tips()
        
        return 0
    
    def _handle_learn(self, topic: str) -> int:
        """Handle learn command with optional topic and quiz."""
        if topic == 'all' or topic is True:
            return self._show_all_concepts()
        
        # Look for specific topic
        # First check ContentManager for topics with quizzes
        content = self.content_manager.get_content(topic)
        if content:
            self._show_content_with_quiz(content)
        elif topic in self.explanations['concepts']:
            self._show_concept(topic, self.explanations['concepts'][topic])
        elif topic in self.explanations['metrics']:
            self._show_metric(topic, self.explanations['metrics'][topic])
        else:
            self._show_topic_not_found(topic)
        
        return 0
    
    def _show_all_concepts(self) -> int:
        """Show all available concepts."""
        if RICH_AVAILABLE and self.console:
            self.console.print("\n[bold cyan]Django Mercury Educational Concepts[/bold cyan]\n")
            
            # Group by category
            categories = {}
            for key, concept in self.explanations['concepts'].items():
                category = concept.get('category', 'general')
                if category not in categories:
                    categories[category] = []
                categories[category].append((key, concept))
            
            for category, concepts in categories.items():
                self.console.print(f"\n[yellow]{category.upper()}[/yellow]")
                
                for key, concept in concepts:
                    impact_color = {
                        'high': 'red',
                        'medium': 'yellow',
                        'low': 'green'
                    }.get(concept.get('impact', 'medium'), 'white')
                    
                    self.console.print(
                        f"  • [bold]{concept['title']}[/bold] "
                        f"([{impact_color}]{concept.get('impact', 'medium')} impact[/{impact_color}])"
                    )
                    self.console.print(f"    {concept['brief']}")
                    self.console.print(f"    [dim]Use: mercury-test --learn {key}[/dim]")
        else:
            print("\nDjango Mercury Educational Concepts\n")
            print("=" * 60)
            
            for key, concept in self.explanations['concepts'].items():
                print(f"\n{concept['title']} ({concept.get('impact', 'medium')} impact)")
                print(f"  {concept['brief']}")
                print(f"  Use: mercury-test --learn {key}")
        
        return 0
    
    def _show_content_with_quiz(self, content):
        """Show content from ContentManager with quiz support."""
        if RICH_AVAILABLE and self.console:
            # Create panel with title and brief
            self.console.print(Panel(
                f"[bold cyan]{content.title}[/bold cyan]\n"
                f"[italic]{content.brief}[/italic]",
                title=f"📚 {content.title}",
                border_style="cyan",
                padding=(1, 2)
            ))
            
            if content.detailed:
                # Process markdown-like content
                detailed = content.detailed
                if '```' in detailed:
                    # Has code blocks - split and display
                    parts = detailed.split('```')
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            if part.strip():
                                self.console.print(part.strip())
                        else:
                            # Code block
                            lines = part.split('\n')
                            lang = lines[0] if lines[0] else 'python'
                            code = '\n'.join(lines[1:])
                            syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                            self.console.print(syntax)
                else:
                    self.console.print(detailed)
            
            if content.solutions:
                self.console.print("\n[bold yellow]Solutions:[/bold yellow]")
                for solution in content.solutions:
                    self.console.print(f"  [green]•[/green] {solution}")
            
            self.console.print()  # Add spacing
            
            # Offer quiz if available
            if content.quiz_questions:
                self._offer_quiz_from_content(content)
        else:
            # Simple text output
            print(f"\n{content.title}")
            print("=" * len(content.title))
            print(f"\n{content.brief}\n")
            
            if content.detailed:
                print(content.detailed)
            
            if content.solutions:
                print("\nSolutions:")
                for solution in content.solutions:
                    print(f"  • {solution}")
            
            print()
            
            if content.quiz_questions:
                self._offer_quiz_from_content_simple(content)
    
    def _offer_quiz_from_content(self, content):
        """Offer to run a quiz from ContentManager content."""
        if RICH_AVAILABLE and self.console:
            from rich.prompt import Confirm
            
            # Ask if user wants to take the quiz
            take_quiz = Confirm.ask(
                "\n[bold cyan]📝 Would you like to test your understanding with a quiz?[/bold cyan]",
                default=True
            )
            
            if take_quiz:
                self._run_quiz_from_content(content)
    
    def _offer_quiz_from_content_simple(self, content):
        """Simple version of quiz offer."""
        response = input("\n📝 Would you like to test your understanding with a quiz? (y/n): ")
        if response.lower() in ['y', 'yes']:
            self._run_quiz_from_content_simple(content)
    
    def _run_quiz_from_content(self, content):
        """Run quiz from ContentManager content."""
        from rich.prompt import Prompt
        from rich.panel import Panel
        
        questions = content.quiz_questions
        if not questions:
            return
        
        self.console.print("\n[bold magenta]🎯 Quiz Time![/bold magenta]\n")
        
        score = 0
        total = len(questions)
        
        for i, q in enumerate(questions, 1):
            # Display question
            self.console.print(Panel(
                f"[bold]Question {i}/{total}:[/bold]\n{q.question}",
                border_style="blue"
            ))
            
            # Display options
            for j, option in enumerate(q.options):
                self.console.print(f"  {j+1}. {option}")
            
            # Get answer
            while True:
                answer = Prompt.ask(
                    "\n[cyan]Your answer (1-{})[/cyan]".format(len(q.options)),
                    default="1"
                )
                try:
                    answer_idx = int(answer) - 1
                    if 0 <= answer_idx < len(q.options):
                        break
                    else:
                        self.console.print("[red]Please enter a valid option number.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a number.[/red]")
            
            # Check answer
            if answer_idx == q.correct_answer:
                score += 1
                self.console.print("\n[bold green]✅ Correct![/bold green]")
            else:
                self.console.print(
                    f"\n[bold red]❌ Incorrect.[/bold red] "
                    f"The correct answer was: [yellow]{q.options[q.correct_answer]}[/yellow]"
                )
            
            # Show explanation
            if q.explanation:
                self.console.print(f"\n[dim]💡 {q.explanation}[/dim]")
            
            self.console.print()  # Add spacing
        
        # Show final score
        self._show_quiz_score(score, total)
    
    def _run_quiz_from_content_simple(self, content):
        """Simple text quiz from ContentManager content."""
        questions = content.quiz_questions
        if not questions:
            return
        
        print("\n🎯 Quiz Time!\n")
        
        score = 0
        total = len(questions)
        
        for i, q in enumerate(questions, 1):
            print(f"Question {i}/{total}:")
            print(q.question)
            print()
            
            for j, option in enumerate(q.options):
                print(f"  {j+1}. {option}")
            
            while True:
                answer = input(f"\nYour answer (1-{len(q.options)}): ")
                try:
                    answer_idx = int(answer) - 1
                    if 0 <= answer_idx < len(q.options):
                        break
                    else:
                        print("Please enter a valid option number.")
                except ValueError:
                    print("Please enter a number.")
            
            if answer_idx == q.correct_answer:
                score += 1
                print("\n✅ Correct!")
            else:
                print(f"\n❌ Incorrect. The correct answer was: {q.options[q.correct_answer]}")
            
            if q.explanation:
                print(f"\n💡 {q.explanation}")
            
            print("-" * 40)
        
        self._show_quiz_score_simple(score, total)
    
    def _show_quiz_score(self, score: int, total: int):
        """Show quiz score with rich formatting."""
        percentage = (score / total) * 100
        if percentage >= 80:
            grade_color = "green"
            grade_emoji = "🏆"
            grade_text = "Excellent!"
        elif percentage >= 60:
            grade_color = "yellow"
            grade_emoji = "👍"
            grade_text = "Good job!"
        else:
            grade_color = "red"
            grade_emoji = "📚"
            grade_text = "Keep learning!"
        
        self.console.print(Panel(
            f"[bold {grade_color}]{grade_emoji} Quiz Complete![/bold {grade_color}]\n\n"
            f"Score: {score}/{total} ({percentage:.0f}%)\n"
            f"{grade_text}",
            border_style=grade_color
        ))
    
    def _show_quiz_score_simple(self, score: int, total: int):
        """Show quiz score in simple text."""
        percentage = (score / total) * 100
        print(f"\n📊 Quiz Complete!")
        print(f"Score: {score}/{total} ({percentage:.0f}%)")
        
        if percentage >= 80:
            print("🏆 Excellent!")
        elif percentage >= 60:
            print("👍 Good job!")
        else:
            print("📚 Keep learning!")
    
    def _show_concept(self, key: str, concept: Dict[str, Any]):
        """Show detailed explanation of a concept."""
        if RICH_AVAILABLE and self.console:
            # Create panel with title and brief
            self.console.print(Panel(
                f"[bold cyan]{concept['title']}[/bold cyan]\n"
                f"[italic]{concept['brief']}[/italic]",
                title=f"📚 {concept['title']}",
                border_style="cyan",
                padding=(1, 2)
            ))
            
            if 'detailed' in concept:
                # Process markdown-like content
                detailed = concept['detailed']
                if '```' in detailed:
                    # Has code blocks - split and display
                    parts = detailed.split('```')
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            if part.strip():
                                self.console.print(part.strip())
                        else:
                            # Code block
                            lines = part.split('\n')
                            lang = lines[0] if lines[0] else 'python'
                            code = '\n'.join(lines[1:])
                            syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                            self.console.print(syntax)
                else:
                    self.console.print(detailed)
            
            if 'solutions' in concept:
                self.console.print("\n[bold yellow]Solutions:[/bold yellow]")
                for solution in concept['solutions']:
                    self.console.print(f"  [green]•[/green] {solution}")
            
            self.console.print()  # Add spacing
            
            # Offer quiz if available
            if concept.get('quiz_questions'):
                self._offer_quiz(concept)
            
            # Show related content
            if 'category' in concept:
                self._suggest_related_topics(key, concept['category'])
        else:
            # Simple text output
            print(f"\n{concept['title']}")
            print("=" * len(concept['title']))
            print(f"\n{concept['brief']}\n")
            
            if 'detailed' in concept:
                print(concept['detailed'])
            
            if 'solutions' in concept:
                print("\nSolutions:")
                for solution in concept['solutions']:
                    print(f"  • {solution}")
            
            print()
    
    def _show_metric(self, key: str, metric: Dict[str, Any]):
        """Show detailed explanation of a metric."""
        if RICH_AVAILABLE and self.console:
            table = Table(title=f"📊 {metric['title']}", show_header=True)
            table.add_column("Threshold", style="cyan")
            table.add_column("Range", style="white")
            
            for level, value in metric.get('thresholds', {}).items():
                style = {
                    'excellent': 'green',
                    'good': 'blue',
                    'acceptable': 'yellow',
                    'poor': 'red'
                }.get(level, 'white')
                table.add_row(level.capitalize(), f"[{style}]{value}[/{style}]")
            
            self.console.print(table)
            
            if 'factors' in metric:
                self.console.print("\n[yellow]Contributing Factors:[/yellow]")
                for factor in metric['factors']:
                    self.console.print(f"  • {factor}")
            
            if 'optimization' in metric:
                self.console.print("\n[green]Optimization Tips:[/green]")
                for tip in metric['optimization']:
                    self.console.print(f"  • {tip}")
            
            if 'tips' in metric:
                self.console.print("\n[blue]Best Practices:[/blue]")
                for tip in metric['tips']:
                    self.console.print(f"  • {tip}")
        else:
            print(f"\n{metric['title']}")
            print("=" * len(metric['title']))
            print(f"\n{metric['brief']}\n")
            
            if 'thresholds' in metric:
                print("Thresholds:")
                for level, value in metric['thresholds'].items():
                    print(f"  {level}: {value}")
            
            if 'factors' in metric:
                print("\nContributing Factors:")
                for factor in metric['factors']:
                    print(f"  • {factor}")
            
            if 'optimization' in metric:
                print("\nOptimization Tips:")
                for tip in metric['optimization']:
                    print(f"  • {tip}")
            
            print()
    
    def _show_metrics_explanation(self) -> int:
        """Show explanation of all metrics."""
        if RICH_AVAILABLE and self.console:
            self.console.print("\n[bold cyan]Performance Metrics Guide[/bold cyan]\n")
            
            for key, metric in self.explanations['metrics'].items():
                self._show_metric(key, metric)
                self.console.print()
        else:
            print("\nPerformance Metrics Guide")
            print("=" * 40)
            
            for key, metric in self.explanations['metrics'].items():
                self._show_metric(key, metric)
        
        return 0
    
    def _show_patterns(self) -> int:
        """Show design patterns and best practices."""
        if RICH_AVAILABLE and self.console:
            self.console.print("\n[bold cyan]Django Design Patterns[/bold cyan]\n")
            
            for key, pattern in self.explanations['patterns'].items():
                panel = Panel(
                    f"[bold]{pattern['title']}[/bold]\n\n"
                    f"{pattern['brief']}\n\n"
                    f"{pattern.get('example', '')}",
                    title=f"🏗️ {pattern['title']}",
                    border_style="blue"
                )
                self.console.print(panel)
                self.console.print()
        else:
            print("\nDjango Design Patterns")
            print("=" * 40)
            
            for key, pattern in self.explanations['patterns'].items():
                print(f"\n{pattern['title']}")
                print("-" * len(pattern['title']))
                print(f"{pattern['brief']}")
                if 'example' in pattern:
                    print(f"\nExample:\n{pattern['example']}")
                print()
        
        return 0
    
    def _show_tips(self) -> int:
        """Show testing and optimization tips."""
        tips = self.explanations.get('tips', [])
        
        if RICH_AVAILABLE and self.console:
            panel = Panel(
                "\n".join([f"💡 {tip}" for tip in tips]),
                title="🎯 Testing & Optimization Tips",
                border_style="green"
            )
            self.console.print(panel)
        else:
            print("\nTesting & Optimization Tips")
            print("=" * 40)
            for tip in tips:
                print(f"• {tip}")
            print()
        
        return 0
    
    def _show_topic_not_found(self, topic: str):
        """Show message when topic is not found."""
        available = list(self.explanations['concepts'].keys()) + \
                   list(self.explanations['metrics'].keys())
        
        if RICH_AVAILABLE and self.console:
            self.console.print(f"\n[red]Topic '{topic}' not found.[/red]\n")
            self.console.print("[yellow]Available topics:[/yellow]")
            for t in available:
                self.console.print(f"  • {t}")
            self.console.print("\n[dim]Use: mercury-test --learn [topic][/dim]")
        else:
            print(f"\nTopic '{topic}' not found.\n")
            print("Available topics:")
            for t in available:
                print(f"  • {t}")
            print("\nUse: mercury-test --learn [topic]")
    
    def _offer_quiz(self, concept: Dict[str, Any]):
        """Offer to run a quiz for the concept."""
        if RICH_AVAILABLE and self.console:
            from rich.prompt import Confirm
            
            # Ask if user wants to take the quiz
            take_quiz = Confirm.ask(
                "\n[bold cyan]📝 Would you like to test your understanding with a quiz?[/bold cyan]",
                default=True
            )
            
            if take_quiz:
                self._run_quiz(concept)
        else:
            # Simple text version
            response = input("\n📝 Would you like to test your understanding with a quiz? (y/n): ")
            if response.lower() in ['y', 'yes']:
                self._run_quiz_simple(concept)
    
    def _run_quiz(self, concept: Dict[str, Any]):
        """Run an interactive quiz with rich formatting."""
        from rich.prompt import Prompt
        from rich.panel import Panel
        
        questions = concept.get('quiz_questions', [])
        if not questions:
            return
        
        self.console.print("\n[bold magenta]🎯 Quiz Time![/bold magenta]\n")
        
        score = 0
        total = len(questions)
        
        for i, q in enumerate(questions, 1):
            # Display question
            self.console.print(Panel(
                f"[bold]Question {i}/{total}:[/bold]\n{q.question}",
                border_style="blue"
            ))
            
            # Display options
            for j, option in enumerate(q.options):
                self.console.print(f"  {j+1}. {option}")
            
            # Get answer
            while True:
                answer = Prompt.ask(
                    "\n[cyan]Your answer (1-{})[/cyan]".format(len(q.options)),
                    default="1"
                )
                try:
                    answer_idx = int(answer) - 1
                    if 0 <= answer_idx < len(q.options):
                        break
                    else:
                        self.console.print("[red]Please enter a valid option number.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a number.[/red]")
            
            # Check answer
            if answer_idx == q.correct_answer:
                score += 1
                self.console.print("\n[bold green]✅ Correct![/bold green]")
            else:
                self.console.print(
                    f"\n[bold red]❌ Incorrect.[/bold red] "
                    f"The correct answer was: [yellow]{q.options[q.correct_answer]}[/yellow]"
                )
            
            # Show explanation
            if q.explanation:
                self.console.print(f"\n[dim]💡 {q.explanation}[/dim]")
            
            self.console.print()  # Add spacing
        
        # Show final score
        percentage = (score / total) * 100
        if percentage >= 80:
            grade_color = "green"
            grade_emoji = "🏆"
            grade_text = "Excellent!"
        elif percentage >= 60:
            grade_color = "yellow"
            grade_emoji = "👍"
            grade_text = "Good job!"
        else:
            grade_color = "red"
            grade_emoji = "📚"
            grade_text = "Keep learning!"
        
        self.console.print(Panel(
            f"[bold {grade_color}]{grade_emoji} Quiz Complete![/bold {grade_color}]\n\n"
            f"Score: {score}/{total} ({percentage:.0f}%)\n"
            f"{grade_text}",
            border_style=grade_color
        ))
    
    def _run_quiz_simple(self, concept: Dict[str, Any]):
        """Run a simple text-based quiz."""
        questions = concept.get('quiz_questions', [])
        if not questions:
            return
        
        print("\n🎯 Quiz Time!\n")
        
        score = 0
        total = len(questions)
        
        for i, q in enumerate(questions, 1):
            print(f"Question {i}/{total}:")
            print(q.question)
            print()
            
            for j, option in enumerate(q.options):
                print(f"  {j+1}. {option}")
            
            while True:
                answer = input(f"\nYour answer (1-{len(q.options)}): ")
                try:
                    answer_idx = int(answer) - 1
                    if 0 <= answer_idx < len(q.options):
                        break
                    else:
                        print("Please enter a valid option number.")
                except ValueError:
                    print("Please enter a number.")
            
            if answer_idx == q.correct_answer:
                score += 1
                print("\n✅ Correct!")
            else:
                print(f"\n❌ Incorrect. The correct answer was: {q.options[q.correct_answer]}")
            
            if q.explanation:
                print(f"\n💡 {q.explanation}")
            
            print("-" * 40)
        
        percentage = (score / total) * 100
        print(f"\n📊 Quiz Complete!")
        print(f"Score: {score}/{total} ({percentage:.0f}%)")
        
        if percentage >= 80:
            print("🏆 Excellent!")
        elif percentage >= 60:
            print("👍 Good job!")
        else:
            print("📚 Keep learning!")
    
    def _suggest_related_topics(self, current_topic: str, category: str):
        """Suggest related topics based on category."""
        related = []
        for key, concept in self.explanations['concepts'].items():
            if key != current_topic and concept.get('category') == category:
                related.append((key, concept['title']))
        
        if related and RICH_AVAILABLE and self.console:
            self.console.print("\n[dim]Related topics:[/dim]")
            for key, title in related[:3]:  # Show max 3 related
                self.console.print(f"  • mercury-test --learn {key} ({title})")
    
    def pre_test_hook(self, args: Namespace) -> None:
        """Provide context before tests start."""
        if getattr(args, 'no_hints', False):
            return
        
        # Show a random tip at start (educational)
        if random.random() < 0.3:  # 30% chance
            tip = random.choice(self.explanations.get('tips', []))
            if RICH_AVAILABLE and self.console:
                self.console.print(f"\n💡 [cyan]Tip:[/cyan] {tip}\n")
            else:
                print(f"\n💡 Tip: {tip}\n")
    
    def post_test_hook(self, args: Namespace, result: int, elapsed_time: float) -> None:
        """Provide educational feedback after tests complete."""
        if getattr(args, 'no_hints', False):
            return
        
        # Provide performance feedback
        if elapsed_time > 60:
            self._provide_performance_hints(elapsed_time)
        
        # Suggest relevant topics based on test results
        if result != 0:
            self._suggest_failure_resources()
    
    def _provide_performance_hints(self, elapsed_time: float):
        """Provide hints for slow test execution."""
        hints = []
        
        if elapsed_time > 300:
            hints.append("Consider using --parallel for faster test execution")
            hints.append("Review slow queries with --learn slow_queries")
        
        if elapsed_time > 120:
            hints.append("Profile your tests with Mercury to find bottlenecks")
            hints.append("Learn about query optimization: --learn n_plus_one")
        
        if hints and RICH_AVAILABLE and self.console:
            self.console.print("\n[yellow]Performance Suggestions:[/yellow]")
            for hint in hints:
                self.console.print(f"  • {hint}")
            self.console.print()
    
    def _suggest_failure_resources(self):
        """Suggest resources when tests fail."""
        suggestions = [
            "Review test isolation: --learn test_isolation",
            "Check for memory issues: --learn memory_leaks",
            "Learn about debugging: mercury-test --tips"
        ]
        
        if RICH_AVAILABLE and self.console:
            self.console.print("\n[cyan]Need help debugging?[/cyan]")
            suggestion = random.choice(suggestions)
            self.console.print(f"  • {suggestion}\n")
        else:
            print("\nNeed help debugging?")
            suggestion = random.choice(suggestions)
            print(f"  • {suggestion}\n")