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
                concept="n+1_queries",
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
                concept="n+1_queries",
                difficulty="intermediate",
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
                concept="n+1_queries",
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
                concept="memory_management",
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
                concept="memory_management",
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
            print("\n" + "=" * 50)
            print("📚 QUIZ TIME!")
            if context:
                print(f"Context: {context}")
            print("\n" + quiz.question)
            for i, option in enumerate(quiz.options, 1):
                print(f"{i}) {option}")

            try:
                answer = int(input("\nYour answer [1-4]: ")) - 1
            except (ValueError, EOFError):
                answer = -1

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
        try:
            answer = IntPrompt.ask(
                "\n[bold]Your answer[/bold]",
                choices=["1", "2", "3", "4"],
                show_choices=False,
            ) - 1
        except (EOFError, KeyboardInterrupt):
            self.console.print("\n[yellow]Quiz skipped[/yellow]")
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
        """Create a quiz based on a specific issue detected.

        Args:
            issue_type: Type of performance issue detected
            issue_details: Details about the issue

        Returns:
            Dynamically created quiz or None
        """
        if issue_type == "high_query_count":
            query_count = issue_details.get("query_count", 0)
            return Quiz(
                question=f"Your test executed {query_count} queries. What's the most likely cause?",
                options=[
                    "Database connection issues",
                    "Missing select_related() or prefetch_related()",
                    "Too much test data",
                    "Slow database server",
                ],
                correct_answer=1,
                explanation="High query counts usually indicate N+1 problems. Use select_related() for ForeignKeys and prefetch_related() for ManyToMany relationships.",
                concept="n+1_queries",
                difficulty="beginner",
            )

        elif issue_type == "slow_response":
            response_time = issue_details.get("response_time_ms", 0)
            return Quiz(
                question=f"This endpoint took {response_time}ms. What should you investigate first?",
                options=[
                    "Network latency",
                    "Database query performance",
                    "Python version",
                    "Server location",
                ],
                correct_answer=1,
                explanation="Slow responses are often due to inefficient database queries. Use Django Mercury's monitoring to identify the slowest queries.",
                concept="response_time",
                difficulty="beginner",
            )

        return None
