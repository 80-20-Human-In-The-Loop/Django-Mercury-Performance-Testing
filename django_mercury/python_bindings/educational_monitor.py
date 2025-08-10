"""
Educational Monitor for Django Mercury

This module provides real-time educational interventions during test execution,
implementing the 80-20 Human-in-the-Loop philosophy.
"""

import os
import sys
import time
from typing import Any, Dict, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, IntPrompt
    from rich.text import Text
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class EducationalMonitor:
    """
    Monitors test execution and provides educational interventions.
    
    This class intercepts performance issues during testing and provides
    interactive educational content to help developers understand and fix issues.
    """
    
    def __init__(
        self,
        console: Optional[Any] = None,
        quiz_system: Optional[Any] = None,
        progress_tracker: Optional[Any] = None,
        interactive_mode: bool = True
    ):
        """
        Initialize the educational monitor.
        
        Args:
            console: Rich console for output
            quiz_system: Quiz system for interactive questions
            progress_tracker: Progress tracking system
            interactive_mode: Whether to pause for interactions
        """
        self.console = console
        self.quiz_system = quiz_system
        self.progress_tracker = progress_tracker
        self.interactive_mode = interactive_mode
        self.issues_found = []
        self.current_test = None
    
    def handle_performance_issue(self, test, error_msg: str):
        """
        Handle a performance issue with educational intervention.
        
        Args:
            test: The test that failed
            error_msg: The error message from the failure
        """
        # Parse the issue type
        issue_type = self._detect_issue_type(error_msg)
        test_name = str(test).split()[0] if test else "Unknown test"
        
        # Store issue for summary (always record, even in non-interactive mode)
        self.issues_found.append({
            'test': test_name,
            'type': issue_type,
            'error': error_msg
        })
        
        # Track the concept if we have a tracker (always track, not just in interactive mode)
        if self.progress_tracker:
            self.progress_tracker.add_concept(issue_type)
        
        # Only show educational content in interactive mode
        if not self.interactive_mode:
            return
        
        # Display educational content
        if self.console and RICH_AVAILABLE:
            self._show_rich_educational_content(test_name, issue_type, error_msg)
        else:
            self._show_text_educational_content(test_name, issue_type, error_msg)
    
    def _detect_issue_type(self, error_msg: str) -> str:
        """Detect the type of performance issue from error message."""
        error_lower = error_msg.lower()
        
        if "query count" in error_lower or "n+1" in error_lower:
            return "n_plus_one_queries"  # Match test expectations
        elif "response time" in error_lower or "timeout" in error_lower:
            return "slow_response_time"
        elif "memory" in error_lower or "leak" in error_lower:
            return "memory_optimization"  # Match test expectations
        elif "cache" in error_lower or "caching" in error_lower:
            return "cache_optimization"
        else:
            return "general_performance"
    
    def _show_rich_educational_content(self, test_name: str, issue_type: str, error_msg: str):
        """Display rich educational content using Rich library."""
        # Clear some space
        self.console.print("\n")
        
        # Extract specific metrics for context
        import re
        query_count = None
        response_time = None
        query_match = re.search(r"Query count (\d+)", error_msg)
        if query_match:
            query_count = int(query_match.group(1))
        time_match = re.search(r"Response time (\d+\.?\d*)ms", error_msg)
        if time_match:
            response_time = float(time_match.group(1))
        
        # Show issue panel with contextual information
        issue_text = f"[bold red]⚠️  Performance Issue Detected![/bold red]\n\n"
        issue_text += f"[yellow]Test:[/yellow] {test_name}\n"
        issue_text += f"[yellow]Issue Type:[/yellow] {issue_type.replace('_', ' ').title()}\n"
        issue_text += f"[yellow]Details:[/yellow] {self._extract_issue_details(error_msg)}"
        
        # Add contextual advice based on metrics
        if query_count and query_count > 100:
            issue_text += f"\n\n[red]⚠️ CRITICAL:[/red] {query_count} queries is extremely high!"
            issue_text += "\nThis will cause serious performance problems in production."
        elif query_count and query_count > 50:
            issue_text += f"\n\n[yellow]⚠️ WARNING:[/yellow] {query_count} queries is quite high."
            issue_text += "\nConsider optimizing before deployment."
        
        issue_panel = Panel(
            Text.from_markup(issue_text),
            title="[bold]Learning Opportunity[/bold]",
            border_style="red",
            padding=(1, 2)
        )
        self.console.print(issue_panel)
        
        # Get educational content for this issue type
        content = self._get_educational_content_contextual(issue_type, test_name, query_count, response_time)
        
        # Show explanation
        explanation_panel = Panel(
            Markdown(content['explanation']),
            title="[bold cyan]📚 What's Happening?[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(explanation_panel)
        
        # Run quiz if available
        if self.quiz_system and self.interactive_mode:
            self.console.print("\n[bold cyan]🤔 Quick Check:[/bold cyan]")
            quiz_result = self.quiz_system.ask_quiz_for_concept(issue_type)
            
            if quiz_result and quiz_result.get('wants_to_learn'):
                # Show detailed fix guide
                self._show_fix_guide(issue_type, content)
        
        # Ask if user wants to continue
        if self.interactive_mode:
            # Check if we can actually interact
            from django_mercury.cli.educational.utils import is_interactive_environment, safe_confirm
            
            if is_interactive_environment():
                self.console.print()
                try:
                    continue_choice = Confirm.ask(
                        "[yellow]Ready to continue testing?[/yellow]",
                        default=True
                    )
                except (EOFError, KeyboardInterrupt):
                    continue_choice = True
                    
                if not continue_choice:
                    # User wants more information
                    self._show_additional_resources(issue_type)
            else:
                # Non-interactive environment - just show the content without pausing
                self.console.print("\n[dim](Running in non-interactive mode - not pausing)[/dim]")
    
    def _show_text_educational_content(self, test_name: str, issue_type: str, error_msg: str):
        """Display simple text educational content."""
        print("\n" + "="*60)
        print("⚠️  PERFORMANCE ISSUE DETECTED - Learning Opportunity")
        print("="*60)
        print(f"Test: {test_name}")
        print(f"Issue: {issue_type.replace('_', ' ').title()}")
        print(f"Error: {self._extract_issue_details(error_msg)}")
        print()
        
        # Get educational content
        content = self._get_educational_content(issue_type)
        
        print("📚 EXPLANATION:")
        print("-" * 40)
        print(content['explanation'])
        print()
        
        print("🔧 HOW TO FIX:")
        print("-" * 40)
        print(content['fix_summary'])
        print()
        
        if self.interactive_mode:
            from django_mercury.cli.educational.utils import is_interactive_environment, safe_input
            
            if is_interactive_environment():
                safe_input("Press Enter to continue testing...")
            else:
                print("(Running in non-interactive mode - not pausing)")
    
    def _extract_issue_details(self, error_msg: str) -> str:
        """Extract relevant details from error message."""
        import re
        
        # Try to extract specific metrics
        details = []
        
        # Response time
        time_match = re.search(r"Response time (\d+\.?\d*)ms", error_msg)
        if time_match:
            details.append(f"Response time: {time_match.group(1)}ms")
        
        # Query count
        query_match = re.search(r"Query count (\d+)", error_msg)
        if query_match:
            details.append(f"Queries executed: {query_match.group(1)}")
        
        # Memory
        memory_match = re.search(r"Memory (\d+\.?\d*)MB", error_msg)
        if memory_match:
            details.append(f"Memory used: {memory_match.group(1)}MB")
        
        return " | ".join(details) if details else error_msg[:100]
    
    def _get_educational_content(self, issue_type: str) -> Dict[str, str]:
        """Get educational content for a specific issue type."""
        content_db = {
            "n_plus_one_queries": {
                "explanation": """
## The N+1 Query Problem

When you fetch a list of objects and then access their related data, Django makes:
- 1 query to get the list
- N additional queries (one for each item's related data)

This creates N+1 total queries, which can severely impact performance.

### Example:
```python
# Bad: Creates N+1 queries
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # Each access = new query
```

### Why It Happens:
Django uses lazy loading by default. Related objects are only fetched when accessed,
not when the parent object is retrieved.
""",
                "fix_summary": "Use select_related() for ForeignKey/OneToOne, prefetch_related() for ManyToMany",
                "fix_code": """
# Good: Only 2 queries total
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No additional query!

# For many-to-many:
posts = Post.objects.prefetch_related('tags').all()
"""
            },
            "slow_response_time": {
                "explanation": """
## Slow Response Time

Your view is taking too long to respond. Common causes:
- Inefficient database queries
- Missing database indexes
- Too much data processing
- No pagination on large datasets

### Impact:
Slow responses lead to poor user experience and can cause timeouts under load.
""",
                "fix_summary": "Add database indexes, optimize queries, implement caching",
                "fix_code": """
# Add indexes in your model:
class MyModel(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at', 'status']),
        ]

# Use only() to limit fields:
users = User.objects.only('id', 'username', 'email')

# Implement pagination:
from django.core.paginator import Paginator
paginator = Paginator(queryset, 25)
"""
            },
            "memory_optimization": {
                "explanation": """
## Memory Usage Issue

Your test is using excessive memory. Common causes:
- Loading too much data into memory at once
- Not using queryset iterators for large datasets
- Memory leaks from unclosed resources

### Why It Matters:
High memory usage can cause your application to crash under load or increase hosting costs.
""",
                "fix_summary": "Use iterator() for large querysets, implement pagination, clear caches",
                "fix_code": """
# Use iterator for large datasets:
for user in User.objects.all().iterator(chunk_size=1000):
    process(user)

# Clear caches when needed:
from django.core.cache import cache
cache.clear()

# Use values() to get only needed data:
data = Model.objects.values('id', 'name')
"""
            },
            "cache_optimization": {
                "explanation": """
## Cache Optimization Needed

Your application is not effectively using caching. Benefits of caching:
- Reduce database load
- Faster response times
- Better scalability

### Cache Levels:
1. Database query caching
2. View/fragment caching
3. Full-page caching
""",
                "fix_summary": "Implement Redis/Memcached, use cache_page decorator, cache expensive queries",
                "fix_code": """
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# Cache entire view for 15 minutes:
@cache_page(60 * 15)
def my_view(request):
    return render(request, 'template.html')

# Cache expensive queries:
def get_expensive_data():
    data = cache.get('expensive_data')
    if data is None:
        data = ExpensiveModel.objects.aggregate(...)
        cache.set('expensive_data', data, 3600)
    return data
"""
            },
            "general_performance": {
                "explanation": """
## General Performance Issue

Your test exceeded performance thresholds. Key areas to investigate:
- Database query efficiency
- Algorithm complexity
- External API calls
- File I/O operations

### Performance Testing Best Practices:
- Set realistic thresholds
- Test with production-like data
- Monitor trends over time
""",
                "fix_summary": "Profile your code, optimize algorithms, implement caching",
                "fix_code": """
# Profile your code:
from django.test.utils import override_settings
from silk.profiling.profiler import silk_profile

@silk_profile(name='View Profile')
def my_view(request):
    # Your code here
    pass

# Use Django Debug Toolbar in development
# Check slow query log
# Implement database connection pooling
"""
            }
        }
        
        return content_db.get(issue_type, content_db['general_performance'])
    
    def _get_educational_content_contextual(self, issue_type: str, test_name: str, query_count: Optional[int] = None, response_time: Optional[float] = None) -> Dict[str, str]:
        """Get educational content with test-specific context."""
        # Start with base content
        base_content = self._get_educational_content(issue_type)
        
        # Add contextual information for N+1 queries
        if issue_type == "n_plus_one_queries" and query_count:
            # Calculate likely N+1 pattern
            likely_items = query_count - 1  # Subtract initial query
            
            contextual_explanation = f"""
## The N+1 Query Problem in '{test_name}'

Your test made **{query_count} queries** to the database. This suggests you're loading approximately {likely_items} items, 
with each item triggering an additional query for its related data.

### What's happening in your test:
1. First query loads the main list (~1 query)
2. Each item loads its related data separately (~{likely_items} queries)
3. Total: {query_count} queries

### Why this is bad:
- With 10 items: ~11 queries (manageable)
- With 100 items: ~101 queries (slow)
- With 1000 items: ~1001 queries (timeout!)
- **Your case ({likely_items} items): {query_count} queries**

### How to fix it:
```python
# Bad (your current code likely looks like this):
items = Model.objects.all()
for item in items:
    print(item.related_field.name)  # Each access = new query!

# Good (what you should do):
items = Model.objects.select_related('related_field').all()
for item in items:
    print(item.related_field.name)  # No additional queries!
```
"""
            base_content['explanation'] = contextual_explanation
            
            # Add specific fix based on test name
            if 'user' in test_name.lower():
                base_content['fix_summary'] = f"For {query_count} queries on users: Use User.objects.select_related('profile').prefetch_related('groups')"
            elif 'product' in test_name.lower():
                base_content['fix_summary'] = f"For {query_count} queries on products: Use Product.objects.select_related('category', 'manufacturer')"
            elif 'api' in test_name.lower():
                base_content['fix_summary'] = f"For {query_count} queries in API: Add select_related/prefetch_related to your viewset's queryset"
        
        return base_content
    
    def _show_fix_guide(self, issue_type: str, content: Dict[str, str]):
        """Show detailed fix guide."""
        if not self.console:
            return
        
        # Show fix code
        fix_panel = Panel(
            Markdown(f"```python\n{content.get('fix_code', 'No specific code available')}\n```"),
            title="[bold green]✅ How to Fix[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(fix_panel)
        
        # Show step-by-step guide
        steps = self._get_fix_steps(issue_type)
        if steps:
            self.console.print("\n[bold]Step-by-Step Fix:[/bold]")
            for i, step in enumerate(steps, 1):
                self.console.print(f"  {i}. {step}")
    
    def _get_fix_steps(self, issue_type: str) -> list:
        """Get step-by-step fix instructions."""
        steps_db = {
            "n_plus_one_queries": [
                "Identify the relationship causing extra queries",
                "Add select_related() for ForeignKey/OneToOne relationships",
                "Add prefetch_related() for ManyToMany/reverse ForeignKey",
                "Verify query count reduction using Django Debug Toolbar",
                "Add test assertion for maximum query count"
            ],
            "slow_response_time": [
                "Profile the view to identify bottlenecks",
                "Check database queries with EXPLAIN ANALYZE",
                "Add appropriate database indexes",
                "Implement query result caching",
                "Consider async processing for heavy operations"
            ],
            "memory_optimization": [
                "Use .iterator() for large querysets",
                "Implement pagination for list views",
                "Use .only() or .values() to limit fields",
                "Clear caches after bulk operations",
                "Monitor memory with memory_profiler"
            ],
            "cache_optimization": [
                "Install and configure Redis/Memcached",
                "Identify expensive, frequently-accessed data",
                "Implement cache warming strategies",
                "Set appropriate cache TTLs",
                "Add cache invalidation logic"
            ]
        }
        
        return steps_db.get(issue_type, [])
    
    def _show_additional_resources(self, issue_type: str):
        """Show additional learning resources."""
        if not self.console:
            return
        
        resources = Panel(
            Text.from_markup(
                "[bold]📖 Learn More:[/bold]\n\n"
                f"• Django docs on optimization\n"
                f"• Django Debug Toolbar usage\n"
                f"• Database indexing strategies\n"
                f"• Caching best practices\n\n"
                "[dim]Visit https://docs.djangoproject.com/en/stable/topics/performance/[/dim]"
            ),
            title="Additional Resources",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(resources)
        
        input("\nPress Enter to continue...")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of educational session."""
        issue_types = {}
        for issue in self.issues_found:
            issue_type = issue['type']
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        return {
            'total_issues': len(self.issues_found),
            'issue_types': issue_types,
            'tests_affected': list(set(i['test'] for i in self.issues_found))
        }