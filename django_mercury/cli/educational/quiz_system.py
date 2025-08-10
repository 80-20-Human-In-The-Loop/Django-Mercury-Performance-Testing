"""Interactive quiz system for Django Mercury educational mode.

This module provides interactive quizzes that test understanding of
performance concepts following the 80-20 Human-in-the-Loop philosophy.
"""

import random
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import IntPrompt
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Quiz:
    """Represents a single quiz question with multiple choice answers."""

    def __init__(
        self,
        question: str,
        options: List[str],
        correct_answer: int,
        explanation: str,
        concept: str,
        difficulty: str = "beginner",
    ) -> None:
        """Initialize a quiz question.

        Args:
            question: The question text
            options: List of answer options
            correct_answer: Index of correct answer (0-based)
            explanation: Explanation of the correct answer
            concept: Concept being tested (e.g., "n+1_queries")
            difficulty: Difficulty level (beginner/intermediate/advanced)
        """
        self.question = question
        self.options = options
        self.correct_answer = correct_answer
        self.explanation = explanation
        self.concept = concept
        self.difficulty = difficulty


class QuizSystem:
    """Interactive quiz system for educational mode."""

    def __init__(
        self,
        console: Optional[Console] = None,
        level: str = "beginner",
        progress_tracker: Optional[Any] = None,
    ) -> None:
        """Initialize the quiz system.

        Args:
            console: Rich console for output
            level: Difficulty level
            progress_tracker: Progress tracking instance
        """
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.level = level
        self.progress_tracker = progress_tracker
        self.quiz_database = self._load_quiz_database()
        self.session_score = 0
        self.session_total = 0

    def _load_quiz_database(self) -> List[Quiz]:
        """Load quiz questions from the database."""
        # Built-in quiz questions for core concepts
        quizzes = [
            # N+1 Query Questions
            Quiz(
                question="Your test made 230 queries to load 100 users. This is called an 'N+1 Query Problem'. Why do you think this happened?",
                options=[
                    "The database is slow",
                    "We're loading each user's related data separately",
                    "We have too many users",
                    "The server needs more memory",
                ],
                correct_answer=1,
                explanation="When we fetch users without their related data, Django makes a new query for each relationship. This creates N+1 queries (1 for the list, N for each item's relations).",
                concept="n_plus_one_queries",
                difficulty="beginner",
            ),
            Quiz(
                question="If your view loads 50 blog posts and shows each author's name, how many queries would Django make without optimization?",
                options=[
                    "1 query total",
                    "2 queries total", 
                    "51 queries total (1 for posts + 50 for authors)",
                    "50 queries total",
                ],
                correct_answer=2,
                explanation="Without optimization, Django makes 1 query for the posts, then 1 query for each author (50 more), totaling 51 queries - a classic N+1 problem.",
                concept="n_plus_one_queries",
                difficulty="beginner",
            ),
            Quiz(
                question="What's the EASIEST way to spot N+1 query problems in your Django app?",
                options=[
                    "Reading all your code carefully",
                    "Using Django Debug Toolbar to see query counts",
                    "Waiting for users to complain about slow pages",
                    "Checking server CPU usage",
                ],
                correct_answer=1,
                explanation="Django Debug Toolbar shows you exactly how many queries each page makes, making N+1 problems obvious. Django Mercury also detects these automatically!",
                concept="n_plus_one_queries",
                difficulty="beginner",
            ),
            Quiz(
                question="Your product list page is slow. Debug toolbar shows 201 queries for 200 products. What's likely happening?",
                options=[
                    "The database is broken",
                    "Each product is loading related data separately (N+1 problem)",
                    "You have too many products",
                    "The products table is too large",
                ],
                correct_answer=1,
                explanation="201 queries for 200 items is a telltale sign of N+1: 1 query for the list + 1 query per item for related data like category, manufacturer, etc.",
                concept="n_plus_one_queries",
                difficulty="beginner",
            ),
            Quiz(
                question="Which Django ORM method would fix an N+1 query problem when accessing foreign keys?",
                options=[
                    "filter()",
                    "select_related()",
                    "prefetch_related()",
                    "annotate()",
                ],
                correct_answer=1,
                explanation="select_related() performs a SQL join and includes related objects in a single query, perfect for ForeignKey and OneToOne relationships.",
                concept="n_plus_one_queries",
                difficulty="beginner",
            ),
            Quiz(
                question="When would you use prefetch_related() instead of select_related()?",
                options=[
                    "For ForeignKey relationships",
                    "For ManyToMany relationships",
                    "For OneToOne relationships",
                    "For filtering queries",
                ],
                correct_answer=1,
                explanation="prefetch_related() is designed for ManyToMany and reverse ForeignKey relationships, using separate queries then joining in Python.",
                concept="n_plus_one_queries",
                difficulty="intermediate",
            ),

            # Response Time Questions
            Quiz(
                question="Your API endpoint takes 500ms to respond. What's the FIRST thing you should check?",
                options=[
                    "Add more server memory",
                    "Check database query performance",
                    "Upgrade Python version",
                    "Increase worker processes",
                ],
                correct_answer=1,
                explanation="Database queries are often the primary bottleneck. Use Django Debug Toolbar or Mercury's monitoring to identify slow queries first.",
                concept="response_time",
                difficulty="beginner",
            ),
            Quiz(
                question="Which caching strategy would best improve list view performance?",
                options=[
                    "Cache individual objects",
                    "Cache the entire queryset",
                    "Cache only the count",
                    "Don't use caching",
                ],
                correct_answer=1,
                explanation="Caching the entire queryset for list views prevents repeated database hits, especially effective for data that doesn't change frequently.",
                concept="caching",
                difficulty="intermediate",
            ),

            # Memory Management Questions
            Quiz(
                question="Your test shows high memory usage when processing large querysets. What's the best approach?",
                options=[
                    "Use queryset.all() to load everything",
                    "Use queryset.iterator() for large datasets",
                    "Increase server RAM",
                    "Use raw SQL queries",
                ],
                correct_answer=1,
                explanation="iterator() processes results one at a time instead of loading the entire queryset into memory, ideal for large datasets.",
                concept="memory_optimization",
                difficulty="intermediate",
            ),
            Quiz(
                question="What causes a 'memory leak' in Django views?",
                options=[
                    "Using too many database queries",
                    "Storing data in module-level variables",
                    "Using class-based views",
                    "Having too many URL patterns",
                ],
                correct_answer=1,
                explanation="Module-level variables persist between requests and accumulate data, causing memory to grow continuously.",
                concept="memory_optimization",
                difficulty="advanced",
            ),

            # Serialization Questions
            Quiz(
                question="DRF serialization is slow for nested relationships. What's the best optimization?",
                options=[
                    "Use SerializerMethodField for everything",
                    "Remove all nested serializers",
                    "Use select_related/prefetch_related with serializers",
                    "Switch to JSONRenderer",
                ],
                correct_answer=2,
                explanation="Combining ORM optimization (select_related/prefetch_related) with serializers prevents N+1 queries during serialization.",
                concept="serialization",
                difficulty="intermediate",
            ),

            # Database Indexing Questions
            Quiz(
                question="When should you add a database index?",
                options=[
                    "On every field",
                    "On fields used in WHERE, ORDER BY, and JOIN clauses",
                    "Only on primary keys",
                    "Only on foreign keys",
                ],
                correct_answer=1,
                explanation="Indexes speed up queries that filter, sort, or join on specific fields, but have a write performance cost.",
                concept="database_optimization",
                difficulty="intermediate",
            ),

            # Testing Performance Questions
            Quiz(
                question="What does Django Mercury's grade 'S' mean for your test?",
                options=[
                    "Satisfactory performance",
                    "Slow performance",
                    "Superior/excellent performance",
                    "Standard performance",
                ],
                correct_answer=2,
                explanation="Grade 'S' indicates superior performance - your code is highly optimized and exceeds performance expectations!",
                concept="mercury_grading",
                difficulty="beginner",
            ),

            # ADVANCED EXPERT-LEVEL QUESTIONS

            # Advanced N+1 and Query Optimization
            Quiz(
                question="You have a complex view with nested relationships (User -> Profile -> Company -> Employees). What's the most efficient prefetching strategy?",
                options=[
                    "Use select_related() for everything",
                    "Combine select_related() for foreign keys and Prefetch() objects with nested prefetch_related()",
                    "Use prefetch_related() for all relationships",
                    "Make separate queries for each relationship",
                ],
                correct_answer=1,
                explanation="For nested relationships, combine select_related() for direct foreign keys (User->Profile) and Prefetch objects with nested prefetch_related() for reverse relationships and complex cases. This gives you fine-grained control over each relationship's optimization.",
                concept="advanced_query_optimization",
                difficulty="advanced",
            ),

            Quiz(
                question="When using Prefetch() objects, what's the benefit of customizing the queryset parameter?",
                options=[
                    "It makes queries run faster automatically",
                    "You can apply filters, ordering, and select_related() to the prefetched queryset",
                    "It reduces memory usage only",
                    "It's just syntactic sugar with no real benefit",
                ],
                correct_answer=1,
                explanation="Prefetch(queryset=...) lets you customize the prefetched queryset with filters, ordering, select_related(), and other optimizations. This prevents fetching unnecessary data and optimizes nested relationships.",
                concept="advanced_query_optimization", 
                difficulty="advanced",
            ),

            Quiz(
                question="In Django, what's the difference between iterator() and iterator(chunk_size=1000)?",
                options=[
                    "No difference, chunk_size is ignored",
                    "chunk_size controls database-level batching; default iterator() fetches all then yields one-by-one",
                    "chunk_size only affects memory usage, not database queries",
                    "iterator() always uses chunk_size=1000 by default",
                ],
                correct_answer=1,
                explanation="iterator(chunk_size=1000) fetches records in batches of 1000 from the database, while iterator() without chunk_size fetches ALL records at once then yields them individually. Using chunk_size is crucial for truly memory-efficient processing of large datasets.",
                concept="memory_optimization",
                difficulty="advanced",
            ),

            # Advanced Caching Strategies
            Quiz(
                question="What's the main risk of using Django's cache.get_or_set() in high-traffic applications?",
                options=[
                    "It's too slow compared to cache.get()",
                    "Cache stampede - multiple processes may execute the expensive function simultaneously",
                    "It uses too much memory",
                    "It doesn't support cache versioning",
                ],
                correct_answer=1,
                explanation="get_or_set() can cause cache stampede when the cache expires under high load - multiple processes simultaneously execute the expensive function. Use cache.add() with locks or probabilistic early expiration to prevent this.",
                concept="advanced_caching",
                difficulty="advanced",
            ),

            Quiz(
                question="For a high-traffic API with user-specific data, which caching pattern is most effective?",
                options=[
                    "Cache entire API responses for all users",
                    "Use fragment caching with user-specific cache keys for personalized parts",
                    "Don't use caching for user-specific data",
                    "Cache only database query results, not HTTP responses",
                ],
                correct_answer=1,
                explanation="Fragment caching allows you to cache shared components (like product lists) while keeping user-specific parts (like personalized recommendations) separate. Use cache keys like 'user:123:dashboard' for user-specific fragments.",
                concept="advanced_caching",
                difficulty="advanced",
            ),

            # Advanced Database Optimization  
            Quiz(
                question="You have a query filtering on created_at and category_id with ordering by updated_at. What's the optimal index strategy?",
                options=[
                    "Create separate indexes: (created_at), (category_id), (updated_at)",
                    "Create a composite index: (created_at, category_id, updated_at)",
                    "Create composite index for filtering: (created_at, category_id) and separate index for ordering: (updated_at)",
                    "Use database auto-indexing",
                ],
                correct_answer=2,
                explanation="Separate your filtering and ordering indexes. Composite indexes work best when all columns are in the WHERE clause. For queries that filter then order by different columns, separate indexes often perform better and are more reusable.",
                concept="database_optimization",
                difficulty="advanced",
            ),

            Quiz(
                question="What's the performance impact of using GenericForeignKey in Django models?",
                options=[
                    "No performance impact",
                    "Cannot use select_related() and creates complex queries across multiple tables",
                    "Only affects write performance",
                    "Improves performance by reducing the number of foreign key constraints",
                ],
                correct_answer=1,
                explanation="GenericForeignKey cannot use select_related() and often requires complex queries across multiple content types. Each access can trigger additional queries. Consider denormalizing data or using regular ForeignKeys with proper inheritance instead.",
                concept="database_optimization",
                difficulty="advanced",
            ),

            # Advanced Serialization and API Performance
            Quiz(
                question="In DRF, which SerializerMethodField pattern is most performance-efficient for calculated fields?",
                options=[
                    "Calculate the field value in the method every time",
                    "Use database annotations to calculate the field in the queryset",
                    "Cache the calculated value in Redis",
                    "Use prefetch_related() with the calculated field",
                ],
                correct_answer=1,
                explanation="Database annotations move calculations to the database level, computing values in a single query rather than in Python for each object. Use queryset.annotate(calculated_field=Count('related_objects')) and access it in the serializer.",
                concept="serialization_optimization",
                difficulty="advanced",
            ),

            Quiz(
                question="For paginated API endpoints with large datasets, which approach minimizes database load?",
                options=[
                    "Standard limit/offset pagination",
                    "Cursor-based pagination with indexed ordering fields",
                    "Load all data and paginate in Python",
                    "Use page numbers with COUNT(*) queries",
                ],
                correct_answer=1,
                explanation="Cursor-based pagination (e.g., 'created_at > 2023-01-01') with indexed ordering fields maintains constant performance regardless of dataset size, while limit/offset becomes exponentially slower on large datasets as offset increases.",
                concept="api_optimization",
                difficulty="advanced",
            ),

            # Advanced Testing and Monitoring
            Quiz(
                question="What's the most accurate way to measure Django view performance in production-like conditions?",
                options=[
                    "Use Django Debug Toolbar only",
                    "Combine APM tools (like Sentry) with database query logging and custom metrics",
                    "Time API requests with curl",
                    "Use unittest timing decorators",
                ],
                correct_answer=1,
                explanation="Production-like performance measurement requires APM tools for request tracing, database query logging for N+1 detection, and custom metrics for business logic timing. This provides comprehensive visibility into all performance aspects.",
                concept="performance_monitoring",
                difficulty="advanced",
            ),

            Quiz(
                question="In high-load Django applications, what's the primary benefit of database connection pooling?",
                options=[
                    "Faster query execution",
                    "Reduces connection overhead and prevents connection exhaustion",
                    "Automatic query optimization",
                    "Built-in caching of query results",
                ],
                correct_answer=1,
                explanation="Connection pooling reuses database connections across requests, eliminating the overhead of establishing new connections and preventing connection exhaustion under high load. This is crucial for applications with many concurrent users.",
                concept="scalability",
                difficulty="advanced",
            ),

            # Advanced Architecture and Scaling
            Quiz(
                question="For a Django app with read-heavy workloads, what's the most effective scaling strategy?",
                options=[
                    "Vertical scaling (bigger servers)",
                    "Read replicas with database routing and aggressive caching", 
                    "Microservices architecture",
                    "Horizontal scaling with load balancers only",
                ],
                correct_answer=1,
                explanation="Read-heavy workloads benefit most from read replicas (to distribute database load) combined with strategic caching (to eliminate database hits entirely for frequently accessed data). This provides massive scaling with minimal complexity.",
                concept="scalability",
                difficulty="advanced",
            ),

            Quiz(
                question="What's the main performance consideration when using Django's select_for_update()?",
                options=[
                    "It improves query performance",
                    "Row locks can create deadlocks and reduce concurrency under high load",
                    "It only works with PostgreSQL",
                    "It automatically optimizes queries",
                ],
                correct_answer=1,
                explanation="select_for_update() creates row locks which prevent concurrent access, potentially causing deadlocks and reducing throughput. Use it judiciously and consider optimistic concurrency control or atomic operations for high-concurrency scenarios.",
                concept="concurrency",
                difficulty="advanced",
            ),

            # Advanced Security and Performance
            Quiz(
                question="How does Django's ALLOWED_HOSTS setting impact performance in production?",
                options=[
                    "It doesn't affect performance, only security",
                    "Incorrect configuration can cause DNS lookups on every request",
                    "It only affects memory usage",
                    "It improves caching performance",
                ],
                correct_answer=1,
                explanation="If ALLOWED_HOSTS is misconfigured or uses wildcards unnecessarily, Django may perform DNS lookups to validate hosts on every request, adding latency. Use specific hostnames and avoid patterns that require DNS resolution.",
                concept="security_performance",
                difficulty="advanced",
            ),

            Quiz(
                question="What's the performance impact of Django's DEBUG=True in production?",
                options=[
                    "Minor impact, just extra logging",
                    "Severe impact: stores all SQL queries in memory, disables caching, adds debug overhead",
                    "Only affects error pages",
                    "Improves performance by showing bottlenecks",
                ],
                correct_answer=1,
                explanation="DEBUG=True stores ALL SQL queries in memory (causing memory leaks), disables view caching, includes debug middleware overhead, and exposes sensitive information. This can cause massive memory usage and performance degradation.",
                concept="security_performance",
                difficulty="advanced",
            ),
        ]

        # Filter by difficulty level if needed
        if self.level == "beginner":
            return [q for q in quizzes if q.difficulty in ["beginner"]]
        elif self.level == "intermediate":
            return [q for q in quizzes if q.difficulty in ["beginner", "intermediate"]]
        else:  # advanced
            return quizzes

    def get_quiz_for_concept(self, concept: str) -> Optional[Quiz]:
        """Get a quiz question for a specific concept.

        Args:
            concept: The concept to quiz on

        Returns:
            Quiz object or None if no quiz available
        """
        relevant_quizzes = [
            q for q in self.quiz_database
            if q.concept == concept
        ]

        if not relevant_quizzes:
            # Try to find a related quiz
            relevant_quizzes = [
                q for q in self.quiz_database
                if concept in q.concept or q.concept in concept
            ]

        return random.choice(relevant_quizzes) if relevant_quizzes else None

    def ask_quiz(
        self,
        quiz: Optional[Quiz] = None,
        context: Optional[str] = None,
    ) -> bool:
        """Ask an interactive quiz question.

        Args:
            quiz: Specific quiz to ask (or random if None)
            context: Additional context about why this quiz is being asked

        Returns:
            True if answered correctly, False otherwise
        """
        if not quiz:
            quiz = random.choice(self.quiz_database)

        self.session_total += 1

        if not self.console or not RICH_AVAILABLE:
            # Fallback to basic text output
            from django_mercury.cli.educational.utils import is_interactive_environment, safe_input
            
            print("\n" + "=" * 50)
            print("📚 QUIZ TIME!")
            if context:
                print(f"Context: {context}")
            print("\n" + quiz.question)
            for i, option in enumerate(quiz.options, 1):
                print(f"{i}) {option}")

            if is_interactive_environment():
                try:
                    answer_str = safe_input("\nYour answer [1-4]: ")
                    answer = int(answer_str) - 1 if answer_str.isdigit() else -1
                except (ValueError, EOFError):
                    answer = -1
            else:
                print("\n(Running in non-interactive mode - skipping quiz)")
                return False

            correct = answer == quiz.correct_answer
            if correct:
                print("✅ Correct!")
                self.session_score += 1
            else:
                print(f"❌ Not quite. The correct answer is {quiz.correct_answer + 1}.")

            print(f"\n💡 {quiz.explanation}")
            return correct

        # Rich console output
        quiz_panel = Panel(
            Text(quiz.question, style="bold"),
            title=f"📚 Quiz: {quiz.concept.replace('_', ' ').title()}",
            subtitle=f"Difficulty: {quiz.difficulty.capitalize()}",
            border_style="cyan",
        )
        self.console.print(quiz_panel)

        if context:
            self.console.print(f"[dim]Context: {context}[/dim]\n")

        # Display options
        for i, option in enumerate(quiz.options, 1):
            self.console.print(f"  [cyan]{i})[/cyan] {option}")

        # Get answer
        from django_mercury.cli.educational.utils import is_interactive_environment
        
        if is_interactive_environment():
            try:
                answer = IntPrompt.ask(
                    "\n[bold]Your answer[/bold]",
                    choices=["1", "2", "3", "4"],
                    show_choices=False,
                ) - 1
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[yellow]Quiz skipped[/yellow]")
                return False
        else:
            self.console.print("\n[dim](Running in non-interactive mode - quiz skipped)[/dim]")
            return False

        # Check answer
        correct = answer == quiz.correct_answer

        if correct:
            self.session_score += 1
            self.console.print("\n[bold green]✅ Correct![/bold green]")
            if self.progress_tracker:
                self.progress_tracker.record_concept_learned(quiz.concept)
        else:
            self.console.print(
                f"\n[red]❌ Not quite.[/red] The correct answer is "
                f"[bold]{quiz.correct_answer + 1}[/bold]"
            )

        # Show explanation
        explanation_panel = Panel(
            Text(quiz.explanation),
            title="💡 Explanation",
            border_style="yellow",
        )
        self.console.print(explanation_panel)

        # Update progress
        if self.progress_tracker:
            self.progress_tracker.record_quiz_result(
                quiz.concept,
                correct,
                quiz.difficulty,
            )

        return correct

    def ask_quiz_for_concept(self, concept: str) -> Dict[str, Any]:
        """Ask a quiz question for a specific concept and return the result.

        This method combines get_quiz_for_concept and ask_quiz to provide
        the complete interactive quiz experience for a given concept.

        Args:
            concept: The concept to quiz on (e.g., "n_plus_one_queries")

        Returns:
            Dictionary with quiz results including:
            - 'answered': True if quiz was answered, False if skipped
            - 'correct': True if answered correctly
            - 'wants_to_learn': True if user wants more information
            - 'concept': The concept that was tested
        """
        # Get a quiz for this concept
        quiz = self.get_quiz_for_concept(concept)
        
        if not quiz:
            # No quiz available for this concept
            return {
                'answered': False,
                'correct': False,
                'wants_to_learn': False,
                'concept': concept,
                'message': f"No quiz available for concept: {concept}"
            }
        
        # Ask the quiz
        correct = self.ask_quiz(quiz, context=f"Testing your understanding of {concept.replace('_', ' ')}")
        
        # Ask if they want to learn more
        from django_mercury.cli.educational.utils import is_interactive_environment, safe_confirm
        
        wants_to_learn = False
        if is_interactive_environment():
            if self.console and RICH_AVAILABLE:
                try:
                    from rich.prompt import Confirm
                    wants_to_learn = Confirm.ask(
                        "\n[yellow]Would you like to see detailed optimization guidance?[/yellow]",
                        default=True
                    )
                except (EOFError, KeyboardInterrupt):
                    pass
            else:
                # Fallback to basic input
                wants_to_learn = safe_confirm("\nWould you like to see detailed optimization guidance?", default=True)
        else:
            # Non-interactive mode - default to showing guidance
            wants_to_learn = True
        
        return {
            'answered': True,
            'correct': correct,
            'wants_to_learn': wants_to_learn,
            'concept': concept,
            'quiz': quiz.question if quiz else None
        }

    def show_session_summary(self) -> None:
        """Display a summary of the quiz session."""
        if self.session_total == 0:
            return

        percentage = (self.session_score / self.session_total) * 100

        if not self.console or not RICH_AVAILABLE:
            print("\n" + "=" * 50)
            print("Quiz Session Summary")
            print(f"Score: {self.session_score}/{self.session_total} ({percentage:.0f}%)")
            return

        # Create summary table
        table = Table(title="📊 Quiz Performance", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")

        table.add_row("Questions Answered", str(self.session_total))
        table.add_row("Correct Answers", str(self.session_score))
        table.add_row("Accuracy", f"{percentage:.0f}%")

        # Add encouragement based on score
        if percentage >= 80:
            table.add_row("Grade", "🌟 Excellent!")
        elif percentage >= 60:
            table.add_row("Grade", "✅ Good job!")
        else:
            table.add_row("Grade", "📚 Keep learning!")

        self.console.print(table)

    def create_contextual_quiz(
        self,
        issue_type: str,
        issue_details: Dict[str, Any],
    ) -> Optional[Quiz]:
        """Create a quiz based on a specific issue detected with real-time metrics.

        This method creates dynamic quizzes using actual performance data from tests,
        making the learning experience more relevant and contextual.

        Args:
            issue_type: Type of performance issue detected
            issue_details: Details about the issue including actual metrics

        Returns:
            Dynamically created quiz with real-time data or None
        """
        # Enhanced N+1 Query Detection
        if issue_type == "n_plus_one_queries":
            query_count = issue_details.get("query_count", 0)
            severity = issue_details.get("severity", "").upper()
            
            if severity in ["SEVERE", "CRITICAL"]:
                return Quiz(
                    question=f"🚨 CRITICAL: Your test executed {query_count} queries! This indicates a severe N+1 problem. What's the IMMEDIATE fix?",
                    options=[
                        "Add more database indexes",
                        "Use select_related() for ForeignKey relationships",
                        "Switch to a faster database server", 
                        "Implement caching for all queries",
                    ],
                    correct_answer=1,
                    explanation=f"With {query_count} queries, you have a severe N+1 issue. select_related() performs SQL JOINs to fetch related objects in one query instead of {query_count} separate queries. This is the most immediate and effective fix.",
                    concept="n_plus_one_queries",
                    difficulty="intermediate" if query_count > 50 else "beginner",
                )
            else:
                return Quiz(
                    question=f"Your test executed {query_count} queries, indicating an N+1 problem. Which Django ORM method should you try first?",
                    options=[
                        "annotate() with aggregations",
                        "select_related() for foreign keys",
                        "only() to limit fields",
                        "raw() SQL queries",
                    ],
                    correct_answer=1,
                    explanation=f"For {query_count} queries, start with select_related() to eliminate N+1 queries on ForeignKey relationships. This typically reduces query count by 80-90%.",
                    concept="n_plus_one_queries",
                    difficulty="beginner",
                )

        # High Query Count (without N+1)
        elif issue_type == "high_query_count":
            query_count = issue_details.get("query_count", 0)
            
            if query_count > 50:
                return Quiz(
                    question=f"Your test made {query_count} database queries. What optimization should you prioritize?",
                    options=[
                        "Add database connection pooling",
                        "Implement query optimization (select_related/prefetch_related)",
                        "Upgrade to a faster SSD drive",
                        "Use database query caching only",
                    ],
                    correct_answer=1,
                    explanation=f"With {query_count} queries, the priority is reducing query count through ORM optimization. Connection pooling and caching help, but won't address the root cause of excessive queries.",
                    concept="query_optimization",
                    difficulty="intermediate",
                )
            else:
                return Quiz(
                    question=f"Your test executed {query_count} queries. While not terrible, what could reduce this further?",
                    options=[
                        "Database indexing",
                        "select_related() and prefetch_related()",
                        "Using raw SQL everywhere", 
                        "Increasing database connections",
                    ],
                    correct_answer=1,
                    explanation=f"Even with {query_count} queries, there's room for improvement. select_related() and prefetch_related() can often reduce this to 1-3 queries total.",
                    concept="query_optimization", 
                    difficulty="beginner",
                )

        # Slow Response Time with Real Metrics
        elif issue_type == "slow_response_time":
            response_time = issue_details.get("response_time", 0)
            
            if response_time > 1000:  # > 1 second
                return Quiz(
                    question=f"🐌 Your endpoint took {response_time:.0f}ms (over 1 second!). What's the most critical issue to fix?",
                    options=[
                        "Server CPU is too slow",
                        "Database queries are the bottleneck",
                        "Network latency issues",
                        "Python code needs optimization",
                    ],
                    correct_answer=1,
                    explanation=f"Response times over 1 second usually indicate database bottlenecks. Django Mercury's query analysis will show which queries are slowest. Database optimization typically provides 10-100x improvements.",
                    concept="response_time_optimization",
                    difficulty="intermediate",
                )
            elif response_time > 500:
                return Quiz(
                    question=f"Your endpoint took {response_time:.0f}ms. For a good user experience, what should your target be?",
                    options=[
                        "Under 1000ms is fine",
                        "Under 200ms for API endpoints",
                        "Under 5000ms is acceptable",
                        "Response time doesn't matter",
                    ],
                    correct_answer=1,
                    explanation=f"Your {response_time:.0f}ms is above the recommended 200ms for API endpoints. Users start noticing delays above 200ms, and engagement drops significantly above 400ms.",
                    concept="response_time_optimization",
                    difficulty="beginner",
                )
            else:
                return Quiz(
                    question=f"Good job! Your endpoint took only {response_time:.0f}ms. What makes response times fast?",
                    options=[
                        "Faster server hardware only",
                        "Efficient database queries and minimal round trips", 
                        "Using more expensive hosting",
                        "Having fewer users",
                    ],
                    correct_answer=1,
                    explanation=f"Your {response_time:.0f}ms is excellent! This typically results from optimized database queries, minimal N+1 issues, proper indexing, and efficient code paths.",
                    concept="response_time_optimization",
                    difficulty="beginner",
                )

        # Memory Usage with Real Data
        elif issue_type == "memory_optimization":
            memory_usage = issue_details.get("memory_usage", 0)
            
            if memory_usage > 100:
                return Quiz(
                    question=f"Your test used {memory_usage:.1f}MB of memory. For large datasets, what's the best approach?",
                    options=[
                        "Load all data into memory for speed",
                        "Use queryset.iterator() to process in chunks",
                        "Buy more server RAM",
                        "Switch to a different programming language",
                    ],
                    correct_answer=1,
                    explanation=f"Using {memory_usage:.1f}MB suggests you're loading too much data at once. iterator() processes results in chunks without caching, reducing memory usage by 90%+ for large datasets.",
                    concept="memory_optimization",
                    difficulty="intermediate",
                )
            else:
                return Quiz(
                    question=f"Your memory usage is good at {memory_usage:.1f}MB. What Django method helps keep memory usage low?",
                    options=[
                        "select_related() for everything",
                        "values() and values_list() for specific fields",
                        "Using raw SQL only",
                        "Prefetching all related objects",
                    ],
                    correct_answer=1,
                    explanation=f"Your {memory_usage:.1f}MB is efficient! values() and values_list() return lightweight dictionaries/tuples instead of full model instances, keeping memory usage minimal.",
                    concept="memory_optimization", 
                    difficulty="beginner",
                )

        # Performance Score-Based Quizzes
        elif issue_type == "general_performance":
            score = issue_details.get("score", 0)
            grade = issue_details.get("grade", "F")
            
            if score < 50:  # F grade
                return Quiz(
                    question=f"Your performance score is {score}/100 (Grade {grade}). What's the most impactful first step?",
                    options=[
                        "Rewrite everything in a different framework",
                        "Focus on database query optimization first",
                        "Add more servers to handle the load",
                        "Implement advanced caching strategies",
                    ],
                    correct_answer=1,
                    explanation=f"A {score}/100 score indicates fundamental performance issues. Database queries typically account for 80%+ of performance problems in Django apps. Fix queries first, then tackle other optimizations.",
                    concept="performance_fundamentals",
                    difficulty="intermediate",
                )
            elif score >= 90:  # A or S grade
                return Quiz(
                    question=f"Excellent! Your score is {score}/100 (Grade {grade}). What likely contributed to this excellent performance?",
                    options=[
                        "Lucky timing",
                        "Well-optimized database queries and proper ORM usage",
                        "Powerful server hardware",
                        "Simple test with no database operations",
                    ],
                    correct_answer=1,
                    explanation=f"A {score}/100 score reflects excellent optimization! This typically comes from proper use of select_related(), minimal N+1 queries, appropriate indexing, and efficient code patterns.",
                    concept="performance_fundamentals",
                    difficulty="beginner",
                )

        return None
