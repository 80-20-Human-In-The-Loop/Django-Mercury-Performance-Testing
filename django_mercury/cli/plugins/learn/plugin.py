"""Main Learn plugin implementation.

This is the entry point for the --learn plugin that provides slideshow-style
quizzes and educational content for Django performance optimization.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..base import MercuryPlugin
from .models import Quiz, Question, UserProgress
from .ui import SlideShow
from .content.loader import ContentLoader

# Import new architecture inline since modules have import issues
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Union, Optional, Protocol, Tuple


# Add the necessary classes inline
class SlideType(Enum):
    WELCOME = "welcome"
    CONTENT = "content"
    QUESTION = "question"
    FEEDBACK = "feedback"
    PROGRESS = "progress"
    TRANSITION = "transition"


@dataclass(frozen=True)
class SlideContent:
    slide_type: SlideType
    title: str
    content: Union[str, List[str]]
    metadata: dict[str, Any] = field(default_factory=dict)


class UserInteraction(Protocol):
    def get_user_choice(self, question_text: str, options: List[str]) -> int: ...
    def show_feedback(
        self,
        user_choice: int,
        correct_choice: int,
        user_answer: str,
        correct_answer: str,
        explanation: str,
        is_correct: bool,
    ) -> None: ...
    def show_hint(self, hint: str) -> None: ...


@dataclass(frozen=True)
class QuizResult:
    user_choice: int
    correct_choice: int
    is_correct: bool
    user_answer: str
    correct_answer: str
    explanation: str
    question_id: str
    time_taken: float = 0.0


class LearnPlugin(MercuryPlugin):
    """Learn plugin for interactive educational content and quizzes."""

    name = "learn"
    description = "Interactive learning with slideshow quizzes and explanations"

    def __init__(self):
        super().__init__()
        self.console = Console() if RICH_AVAILABLE else None
        self.progress_tracker = UserProgress()
        self.slideshow = SlideShow(console=self.console)
        self.content_loader = ContentLoader()

    def get_name(self) -> str:
        """Get plugin name."""
        return "learn"

    def get_description(self) -> str:
        """Get plugin description."""
        return "Interactive learning system with slideshow quizzes"

    def register_arguments(self, parser) -> None:
        """Register learn plugin arguments."""
        parser.add_argument(
            "--learn",
            nargs="?",
            const="",
            help="Interactive learning mode (topic optional, e.g., --learn n_plus_one)",
        )

    def can_handle(self, args) -> bool:
        """Check if this plugin should handle the request completely."""
        return hasattr(args, "learn") and args.learn is not None

    def execute(self, args: Any) -> int:
        """Execute the learn command."""
        if not hasattr(args, "learn") or args.learn is None:
            return 1

        topic = args.learn if args.learn else None

        if topic:
            # Learn specific topic
            return self._show_topic_slideshow(topic)
        else:
            # Interactive topic selection
            return self._show_topic_menu()

    def _show_topic_menu(self) -> int:
        """Show interactive topic selection menu."""
        topics = [
            "n+1-queries",
            "response-time",
            "memory-optimization",
            "database-indexing",
            "caching-strategies",
            "testing-patterns",
            "n-plus-one-patterns",
            "test-organization",
            "django-orm",
        ]

        if RICH_AVAILABLE and self.console:
            from rich.prompt import Prompt
            from rich.panel import Panel
            from rich.text import Text

            # Show welcome screen
            welcome_text = Text()
            welcome_text.append("🎓 Django Mercury Learning Center", style="bold cyan")
            welcome_text.append("\n\nChoose a topic to learn about:")

            # Check which topics have tutorial or quiz data available
            available_topics = []
            for i, topic in enumerate(topics, 1):
                # Check if tutorial or quiz data exists
                topic_mapping = self._get_topic_mapping()
                concept = topic_mapping.get(topic.lower(), topic.lower().replace("-", "_"))

                # Check tutorial first, then quiz
                tutorial = self.content_loader.load_tutorial_by_concept(concept)
                if tutorial is None:
                    tutorial = self.content_loader.load_tutorial_by_concept(topic)

                quiz = None
                if tutorial is None:
                    quiz = self.content_loader.load_quiz_by_concept(concept)
                    if quiz is None:
                        quiz = self.content_loader.load_quiz_by_concept(topic)

                has_data = tutorial is not None or quiz is not None

                # Get user progress
                progress = self.progress_tracker.get_concept_progress(topic)
                progress_status = (
                    f"({progress.proficiency_level.value})" if progress.attempts > 0 else ""
                )

                # Determine availability status
                if has_data:
                    available_topics.append(str(i))
                    status_icon = "✅"
                    status_text = f"Ready {progress_status}".strip()
                    style = "green"
                else:
                    status_icon = "🚧"
                    status_text = "Coming Soon"
                    style = "yellow"

                welcome_text.append(f"\n{i}. ", style="")
                welcome_text.append(f"{status_icon} {topic.replace('-', ' ').title()}", style=style)
                welcome_text.append(f" - {status_text}", style="dim")

            welcome_panel = Panel(welcome_text, title="Available Topics", border_style="cyan")
            self.console.print(welcome_panel)

            # Add instruction text
            instruction_text = Text()
            instruction_text.append("💡 Only topics marked with ✅ are available.", style="yellow")
            instruction_text.append(
                " Coming soon topics (🚧) will show a preview message.", style="dim"
            )
            instruction_panel = Panel(instruction_text, border_style="yellow")
            self.console.print(instruction_panel)

            try:
                choice = Prompt.ask(
                    "Enter topic number (1-5) or 'q' to quit",
                    choices=available_topics + ["q"],
                    default="1" if "1" in available_topics else "q",
                )

                if choice == "q":
                    return 0
                elif choice.isdigit():
                    selected_topic = topics[int(choice) - 1]
                    return self._show_topic_slideshow(selected_topic)
                else:
                    return 0

            except (EOFError, KeyboardInterrupt):
                return 0
        else:
            # Simple text menu
            print("\n=== Django Mercury Learning Center ===\n")
            print("Available topics:")

            available_choices = []
            for i, topic in enumerate(topics, 1):
                # Check if tutorial or quiz data exists
                topic_mapping = self._get_topic_mapping()
                concept = topic_mapping.get(topic.lower(), topic.lower().replace("-", "_"))

                # Check tutorial first, then quiz
                tutorial = self.content_loader.load_tutorial_by_concept(concept)
                if tutorial is None:
                    tutorial = self.content_loader.load_tutorial_by_concept(topic)

                quiz = None
                if tutorial is None:
                    quiz = self.content_loader.load_quiz_by_concept(concept)
                    if quiz is None:
                        quiz = self.content_loader.load_quiz_by_concept(topic)

                has_data = tutorial is not None or quiz is not None

                if has_data:
                    available_choices.append(str(i))
                    status = "✅ Ready"
                else:
                    status = "🚧 Coming Soon"

                print(f"{i}. {topic.replace('-', ' ').title()} - {status}")

            print(f"\n💡 Only topics marked with ✅ are available.")

            try:
                choice = input(
                    f"\nEnter topic number ({', '.join(available_choices)}) or 'q' to quit: "
                ).strip()
                if choice == "q":
                    return 0
                elif choice.isdigit() and choice in available_choices:
                    selected_topic = topics[int(choice) - 1]
                    return self._show_topic_slideshow(selected_topic)
                else:
                    print("Invalid choice or topic not available yet")
                    return 1
            except (EOFError, KeyboardInterrupt):
                return 0

    def _get_topic_mapping(self) -> Dict[str, str]:
        """Map topic names to tutorial/quiz file names for loading."""
        return {
            "n+1-queries": "n-plus-one-queries",  # Point to our new tutorial!
            "n1-queries": "n-plus-one-queries",
            "performance": "performance-hierarchy",
            "performance-hierarchy": "performance-hierarchy",
            "response-time": "response-time",
            "memory-optimization": "memory-optimization",
            "database-indexing": "database-indexing",
            "caching-strategies": "caching-strategies",
            "testing-patterns": "testing-patterns",
            "n-plus-one-patterns": "n-plus-one-patterns",
            "test-organization": "test-organization",
            "django-orm": "django-orm",
        }

    def _show_new_tutorial_slideshow(self, tutorial_data: Dict[str, Any]) -> int:
        """Show tutorial using enhanced user-paced slideshow (fallback to improved legacy for now)."""
        # For now, use the improved legacy system that has user-paced navigation
        # This provides the key improvement (no auto-advancing) while we work on full integration
        return self._convert_tutorial_to_slideshow_legacy(tutorial_data)

    def _convert_tutorial_to_slideshow_legacy(self, tutorial_data: Dict[str, Any]) -> int:
        """Legacy tutorial slideshow - uses old auto-advancing system."""
        # Clear any existing slides and reset quiz score
        self.slideshow.slides.clear()
        self.slideshow.reset_quiz_score()

        # Add welcome slide
        self.slideshow.add_welcome_slide(
            title=f"🎓 {tutorial_data.get('title', 'Learning Tutorial')}",
            description=tutorial_data.get("description", ""),
            progress_info=f"📚 Learn-then-test format • Progress will be saved automatically",
        )

        # Add tutorial sections (learn-then-test flow)
        sections = tutorial_data.get("sections", [])
        total_questions = sum(len(section.get("questions", [])) for section in sections)
        current_question = 0

        for section in sections:
            # Add content slides for this section
            content_slides = section.get("content_slides", [])
            for slide in content_slides:
                if slide.get("type") == "concept":
                    # Create concept content using available methods
                    title = slide.get("title", "")
                    content = slide.get("content", "")
                    examples = slide.get("examples", [])
                    key_points = slide.get("key_points", [])

                    # Build content text
                    content_text = f"📖 {title}\n\n{content}"
                    if key_points:
                        content_text += "\n\n🔑 Key Points:"
                        for point in key_points:
                            content_text += f"\n• {point}"
                    if examples:
                        content_text += "\n\n💡 Examples:"
                        for example in examples:
                            content_text += f"\n  {example}"

                    # Remove auto-advancing - wait for user input
                    self.slideshow.add_slide(content_text, auto_advance=False)

                elif slide.get("type") == "scenario":
                    self.slideshow.add_context_slide(
                        scenario=slide.get("scenario", ""), problem=slide.get("problem", "")
                    )

            # Add questions for this section (knowledge checks)
            questions = section.get("questions", [])
            for question in questions:
                current_question += 1
                choices = question.get("choices", [])
                options = [choice.get("text", "") for choice in choices]

                # Find correct answer index
                correct_index = 0
                correct_answer_text = ""
                for i, choice in enumerate(choices):
                    if choice.get("is_correct", False):
                        correct_index = i
                        correct_answer_text = choice.get("text", "")
                        break

                # Add interactive question slide with real answer data
                self.slideshow.add_question_slide(
                    question=question.get("text", ""),
                    options=options,
                    question_number=current_question,
                    total_questions=total_questions,
                    correct_index=correct_index,
                    explanation=question.get("explanation", ""),
                    question_data=question,
                )

                # No separate feedback slide needed - the interactive handler shows feedback directly

        # Add progress slide
        concept = tutorial_data.get("concept", "")
        progress_data = {}
        if concept:
            concept_progress = self.progress_tracker.get_concept_progress(concept)
            progress_data[concept.replace("_", " ").title()] = concept_progress.average_score

        # Get actual quiz scores from slideshow
        quiz_score, quiz_total = self.slideshow.get_quiz_score()
        accuracy = (quiz_score / quiz_total * 100) if quiz_total > 0 else 0.0

        self.slideshow.add_progress_slide(
            score=quiz_score,
            total=quiz_total,
            accuracy=accuracy,
            concept_progress=progress_data,
            next_steps="Great work! Try other topics or run `mercury-test --learn` for more options.",
        )

        # Show the slideshow
        try:
            self.slideshow.show()
            return 0
        except Exception as e:
            if self.console:
                self.console.print(f"[red]Error showing slideshow: {e}[/red]")
            else:
                print(f"Error showing slideshow: {e}")
            return 1

    def _convert_quiz_to_slideshow(self, quiz: Quiz) -> None:
        """Convert a Quiz model to SlideShow slides (fallback for old format)."""
        # Clear any existing slides and reset quiz score
        self.slideshow.slides.clear()
        self.slideshow.reset_quiz_score()

        # Add welcome slide
        self.slideshow.add_welcome_slide(
            title=f"🎓 {quiz.title}",
            description=quiz.description,
            progress_info=f"📊 {len(quiz.questions)} questions • Progress will be saved automatically",
        )

        # Add context slide if we have tags that suggest a scenario
        if "scenario" in quiz.tags or "ecommerce" in quiz.tags:
            self.slideshow.add_context_slide(
                scenario="You're working on a Django application with performance issues.",
                problem="Let's learn how to identify and fix common problems step by step.",
            )

        # Add questions with interactive handling
        for i, question in enumerate(quiz.questions, 1):
            # Find correct answer first
            correct_answer_idx = 0
            correct_answer_text = ""
            for j, answer in enumerate(question.answers):
                if answer.is_correct:
                    correct_answer_idx = j
                    correct_answer_text = answer.text
                    break

            # Add interactive question slide with real answer data
            options = [answer.text for answer in question.answers]
            self.slideshow.add_question_slide(
                question=question.text,
                options=options,
                question_number=i,
                total_questions=len(quiz.questions),
                correct_index=correct_answer_idx,
                explanation=question.explanation,
            )

            # No separate feedback slide needed - the interactive handler shows feedback directly

        # Add progress slide
        progress_data = {}
        if quiz.concept:
            # Get current progress for this concept
            concept_progress = self.progress_tracker.get_concept_progress(quiz.concept)
            progress_data[quiz.concept.replace("_", " ").title()] = concept_progress.average_score

        # Get actual quiz scores from slideshow
        quiz_score, quiz_total = self.slideshow.get_quiz_score()
        accuracy = (quiz_score / quiz_total * 100) if quiz_total > 0 else 0.0

        self.slideshow.add_progress_slide(
            score=quiz_score,
            total=quiz_total,
            accuracy=accuracy,
            concept_progress=progress_data,
            next_steps=f"Great work! Try other topics or run `mercury-test --learn` for more options.",
        )

    def _show_topic_slideshow(self, topic: str) -> int:
        """Show slideshow for a specific topic, trying tutorials first then quizzes."""
        # Get the concept name for this topic
        topic_mapping = self._get_topic_mapping()
        concept = topic_mapping.get(topic.lower(), topic.lower().replace("-", "_"))

        # First, try to load tutorial data (new format)
        tutorial_data = self.content_loader.load_tutorial_by_concept(concept)
        if tutorial_data is None:
            tutorial_data = self.content_loader.load_tutorial_by_concept(topic)

        if tutorial_data:
            # Use new tutorial format with learn-then-test flow and user-paced navigation
            return self._show_new_tutorial_slideshow(tutorial_data)
        else:
            # Fallback to old quiz format
            quiz = self.content_loader.load_quiz_by_concept(concept)
            if quiz is None:
                quiz = self.content_loader.load_quiz_by_concept(topic)

            if quiz is None:
                # No data found at all
                if self.console:
                    self.console.print(
                        f"[red]❌ No tutorial or quiz data found for topic: {topic}[/red]"
                    )
                    self.console.print(
                        f"[yellow]💡 Available topics with data: caching-strategies, n+1-queries, performance-hierarchy[/yellow]"
                    )
                else:
                    print(f"❌ No tutorial or quiz data found for topic: {topic}")
                    print(
                        "💡 Available topics with data: caching-strategies, n+1-queries, performance-hierarchy"
                    )
                return 1

            # Convert quiz to slideshow slides (old format)
            self._convert_quiz_to_slideshow(quiz)

            # Show the slideshow
            try:
                self.slideshow.show()
                return 0
            except Exception as e:
                if self.console:
                    self.console.print(f"[red]Error showing slideshow: {e}[/red]")
                else:
                    print(f"Error showing slideshow: {e}")
                return 1
