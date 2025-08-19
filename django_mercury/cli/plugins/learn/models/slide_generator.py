"""
Modern tutorial slide generator with learn-then-test flow.

Converts Tutorial structures into slideshow presentations with proper
educational pacing: content slides → question → content → question → assessment.
All slides wait for user input before advancing, with warnings about upcoming questions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Union, Optional

from .tutorial_types import Tutorial, LearningSection, ContentSlide, Question

try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class SlideType(Enum):
    """Types of slides in the tutorial slideshow."""

    WELCOME = "welcome"
    CONTENT = "content"
    QUESTION = "question"
    FEEDBACK = "feedback"
    PROGRESS = "progress"
    TRANSITION = "transition"


@dataclass(frozen=True)
class SlideContent:
    """Immutable slide content with type safety."""

    slide_type: SlideType
    title: str
    content: Union[str, List[str]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate slide content structure."""
        if not self.title:
            raise ValueError("Slide must have a title")
        if not self.content:
            raise ValueError("Slide must have content")


class TutorialSlideGenerator:
    """
    Generates slideshow from Tutorial with proper learn-then-test flow.

    Flow: Welcome → [Content → Content → Question] × N → [Question × 2] → Progress
    """

    def __init__(self) -> None:
        self._slide_counter = 0

    def generate_slides(self, tutorial: Union[Tutorial, dict]) -> List[SlideContent]:
        """Generate complete slideshow from tutorial structure (handles both new and legacy formats)."""

        slides: List[SlideContent] = []
        self._slide_counter = 0

        # Handle nested tutorial structure (legacy format)
        if "tutorial" in tutorial:
            tutorial = tutorial["tutorial"]

        # 1. Welcome slide with tutorial overview
        slides.append(self._create_welcome_slide(tutorial))

        # 2. Learning sections (content → question pattern)
        # Handle both "learning_sections" (new) and "sections" (legacy)
        sections = tutorial.get("learning_sections", tutorial.get("sections", []))
        for i, section in enumerate(sections):
            slides.extend(self._create_section_slides(section, i))

        # 3. Final assessment - only if it exists in the new format
        if "final_assessment" in tutorial:
            # Transition to final assessment
            slides.append(self._create_assessment_transition_slide(tutorial))
            # Final assessment questions
            slides.extend(self._create_assessment_slides(tutorial["final_assessment"]))

        # 4. Progress and completion slide
        slides.append(self._create_completion_slide(tutorial))

        return slides

    def _create_welcome_slide(self, tutorial: Union[Tutorial, dict]) -> SlideContent:
        """Create tutorial welcome and overview slide (handles both new and legacy formats)."""

        # Get sections and count questions
        sections = tutorial.get("learning_sections", tutorial.get("sections", []))
        sections_count = len(sections)

        # Count total questions (legacy format has multiple questions per section)
        total_questions = 0
        for section in sections:
            if "questions" in section:  # Legacy format
                total_questions += len(section["questions"])
            elif "question" in section:  # New format
                total_questions += 1

        # Add final assessment questions if they exist (new format)
        if final_assessment := tutorial.get("final_assessment"):
            total_questions += len(final_assessment.get("questions", []))

        content = [
            f"🎓 {tutorial['title']}",
            "",
            f"📚 {tutorial['description']}",
            "",
            f"📋 **What you'll learn:**",
            f"• {sections_count} core concepts with hands-on questions",
            f"• Total: {total_questions} interactive questions",
            "",
            f"⏱️ Estimated time: {tutorial.get('estimated_time', 15)} minutes",
            "",
            "🎯 **Tutorial Format:**",
            "Learn concepts → Apply knowledge → Master the topic",
            "",
            "Press Enter to begin your learning journey! 🚀",
        ]

        return SlideContent(
            slide_type=SlideType.WELCOME,
            title="Welcome to Tutorial",
            content=content,
            metadata={
                "tutorial_id": tutorial["id"],
                "difficulty": tutorial["difficulty"],
                "concept": tutorial["concept"],
            },
        )

    def _create_section_slides(
        self, section: Union[LearningSection, dict], section_index: int
    ) -> List[SlideContent]:
        """Create slides for one learning section: content slides + question(s)."""

        slides: List[SlideContent] = []

        # Content slides (1-2 educational slides)
        for i, content_slide in enumerate(section["content_slides"]):
            slides.append(self._create_content_slide(content_slide, section_index, i))

        # Handle questions - both single question (new format) and multiple questions (legacy)
        if "question" in section:
            # New format: single question per section
            slides.append(self._create_question_slide(section["question"], section_index))
        elif "questions" in section:
            # Legacy format: multiple questions per section
            for q_index, question in enumerate(section["questions"]):
                slides.append(self._create_legacy_question_slide(question, section_index, q_index))

        return slides

    def _create_content_slide(
        self, content_slide: Union[ContentSlide, dict], section_index: int, slide_index: int
    ) -> SlideContent:
        """Create an educational content slide (handles both new and legacy formats)."""

        # Get title - use type-based title if no explicit title
        title = content_slide.get("title")
        if not title:
            slide_type = content_slide.get("type", "content")
            if slide_type == "scenario":
                title = "Real-World Scenario"
            elif slide_type == "concept":
                title = "Core Concept"
            else:
                title = f"{slide_type.title()} Overview"

        # Build rich content with visual formatting
        content_lines = [f"📚 **{title}**", ""]

        # Handle main content - could be string or list
        content = content_slide.get("content", "")
        if isinstance(content, str):
            content_lines.append(content)
        elif isinstance(content, list):
            for line in content:
                if line.startswith("•"):
                    content_lines.append(f"  {line}")  # Indent bullet points
                else:
                    content_lines.append(line)

        # Add key points (legacy format)
        if key_points := content_slide.get("key_points"):
            content_lines.extend(["", "🔑 **Key Points:**"])
            for point in key_points:
                content_lines.append(f"  • {point}")

        # Add examples (legacy format)
        if examples := content_slide.get("examples"):
            content_lines.extend(["", "📝 **Examples:**"])
            for example in examples:
                content_lines.append(f"  • {example}")

        # Handle scenario content (legacy format)
        if scenario := content_slide.get("scenario"):
            content_lines.extend(["", f"📖 **Scenario:** {scenario}"])
        if problem := content_slide.get("problem"):
            content_lines.extend(["", f"⚠️ **Problem:** {problem}"])

        # Add optional code example with syntax highlighting hint
        if code_example := content_slide.get("code_example"):
            content_lines.extend(["", "💻 **Code Example:**", f"```python", code_example, "```"])

        # Add key takeaway if provided
        if takeaway := content_slide.get("key_takeaway"):
            content_lines.extend(["", f"🎯 **Key Takeaway:** {takeaway}"])

        return SlideContent(
            slide_type=SlideType.CONTENT,
            title=f"Section {section_index + 1}: {title}",
            content=content_lines,
            metadata={
                "section_index": section_index,
                "slide_index": slide_index,
                "content_type": content_slide.get("type", "content"),
                "visual_aids": content_slide.get("visual_aids", []),
            },
        )

    def _create_question_slide(self, question: Question, section_index: int) -> SlideContent:
        """Create a question slide for interactive testing."""

        content_lines = [
            f"🤔 **Question {section_index + 1}**",
            "",
            question["text"],
            "",
            "**Options:**",
        ]

        # Add answer options with numbering
        for i, answer in enumerate(question["answers"], 1):
            content_lines.append(f"{i}. {answer['text']}")

        content_lines.extend(["", "Use ↑↓ arrows to navigate • Enter to select • 'h' for hint"])

        return SlideContent(
            slide_type=SlideType.QUESTION,
            title=f"Test Your Knowledge",
            content=content_lines,
            metadata={
                "question_id": question["id"],
                "section_index": section_index,
                "answers": question["answers"],
                "correct_index": next(
                    i for i, answer in enumerate(question["answers"]) if answer["is_correct"]
                ),
                "explanation": question["explanation"],
                "concept": question["concept"],
            },
        )

    def _create_legacy_question_slide(
        self, question: dict, section_index: int, question_index: int
    ) -> SlideContent:
        """Create a question slide for legacy format with 'choices' instead of 'answers'."""

        content_lines = [
            f"🤔 **Question {section_index + 1}.{question_index + 1}**",
            "",
            question["text"],
            "",
            "**Options:**",
        ]

        # Legacy format uses 'choices' instead of 'answers'
        choices = question.get("choices", [])
        for i, choice in enumerate(choices, 1):
            content_lines.append(f"{i}. {choice['text']}")

        content_lines.extend(["", "Use ↑↓ arrows to navigate • Enter to select • 'h' for hint"])

        return SlideContent(
            slide_type=SlideType.QUESTION,
            title=f"Test Your Knowledge",
            content=content_lines,
            metadata={
                "question_id": f"legacy_q_{section_index}_{question_index}",
                "section_index": section_index,
                "question_index": question_index,
                "answers": choices,  # Convert choices to answers format
                "correct_index": next(
                    i for i, choice in enumerate(choices) if choice["is_correct"]
                ),
                "explanation": question["explanation"],
                "concept": f"section_{section_index}",
            },
        )

    def _create_assessment_transition_slide(self, tutorial: Tutorial) -> SlideContent:
        """Create transition slide before final assessment."""

        assessment = tutorial["final_assessment"]
        questions_count = len(assessment["questions"])

        content = [
            "🎯 **Ready for the Final Assessment?**",
            "",
            f"📝 **What's Coming:**",
            f"• {questions_count} comprehensive questions",
            f"• Tests your understanding of ALL concepts covered",
            f"• Passing score: {int(assessment['passing_threshold'] * 100)}%",
            "",
            "🧠 **Quick Review:**",
            "Think back to the key concepts you just learned:",
        ]

        # Add concepts from each section
        for i, section in enumerate(tutorial["learning_sections"], 1):
            content.append(f"  {i}. {section['concept'].replace('_', ' ').title()}")

        content.extend(
            [
                "",
                "💪 **You've got this!** Take your time and apply what you learned.",
                "",
                "Press Enter when ready to begin the assessment...",
            ]
        )

        return SlideContent(
            slide_type=SlideType.TRANSITION,
            title="Final Assessment",
            content=content,
            metadata={"assessment_info": assessment, "total_questions": questions_count},
        )

    def _create_assessment_slides(self, assessment: dict[str, Any]) -> List[SlideContent]:
        """Create slides for final assessment questions."""

        slides: List[SlideContent] = []

        for i, question in enumerate(assessment["questions"]):
            slides.append(self._create_assessment_question_slide(question, i))

        return slides

    def _create_assessment_question_slide(
        self, question: Question, question_index: int
    ) -> SlideContent:
        """Create an assessment question slide."""

        content_lines = [
            f"📊 **Assessment Question {question_index + 1}**",
            "",
            question["text"],
            "",
            "**Choose the best answer:**",
        ]

        # Add answer options
        for i, answer in enumerate(question["answers"], 1):
            content_lines.append(f"{i}. {answer['text']}")

        content_lines.extend(["", "💡 Take your time - think about the concepts you learned!"])

        return SlideContent(
            slide_type=SlideType.QUESTION,
            title="Final Assessment",
            content=content_lines,
            metadata={
                "question_id": question["id"],
                "question_index": question_index,
                "is_assessment": True,
                "answers": question["answers"],
                "correct_index": next(
                    i for i, answer in enumerate(question["answers"]) if answer["is_correct"]
                ),
                "explanation": question["explanation"],
                "concept": question["concept"],
            },
        )

    def _create_completion_slide(self, tutorial: Union[Tutorial, dict]) -> SlideContent:
        """Create tutorial completion and progress slide (handles both new and legacy formats)."""

        # Get sections and count questions for both formats
        sections = tutorial.get("learning_sections", tutorial.get("sections", []))
        total_sections = len(sections)

        # Count total questions
        total_questions = 0
        for section in sections:
            if "questions" in section:  # Legacy format
                total_questions += len(section["questions"])
            elif "question" in section:  # New format
                total_questions += 1

        # Add final assessment questions if they exist (new format)
        if final_assessment := tutorial.get("final_assessment"):
            total_questions += len(final_assessment.get("questions", []))

        concept = tutorial.get("concept", "performance").replace("_", " ")

        content = [
            "🎉 **Tutorial Complete!**",
            "",
            f"✅ **What You Accomplished:**",
            f"• Learned {total_sections} core {concept} concepts",
            f"• Answered {total_questions} questions with detailed explanations",
            f"• Mastered practical Django performance optimization",
            "",
            "🚀 **Next Steps:**",
        ]

        # Add next topic suggestions if available
        if next_topics := tutorial.get("next_topics"):
            content.append("**Recommended follow-up topics:**")
            for topic in next_topics:
                content.append(f"  • mercury-test --learn {topic}")
        else:
            content.extend(
                [
                    "  • Apply these concepts in your Django projects",
                    "  • Explore other performance optimization topics",
                    "  • Share your knowledge with your team!",
                ]
            )

        content.extend(
            [
                "",
                "💡 **Remember:** Performance optimization is about measuring first,",
                "then applying the 80-20 rule to focus on the biggest impact areas.",
                "",
                "Great work on investing in your Django expertise! 🎓",
            ]
        )

        return SlideContent(
            slide_type=SlideType.PROGRESS,
            title="Congratulations!",
            content=content,
            metadata={
                "tutorial_id": tutorial["id"],
                "completion": True,
                "concept": tutorial.get("concept", "performance"),
            },
        )


class SlidePresenter:
    """
    Presents slides with proper user-paced navigation and warnings.

    Never auto-advances - always waits for user input. Warns users
    about upcoming questions to help them prepare.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console if RICH_AVAILABLE else None
        self.current_slide = 0
        self.total_slides = 0

    def present_slideshow(self, slides: List[SlideContent]) -> None:
        """Present complete slideshow with user-paced navigation."""
        self.total_slides = len(slides)

        for i, slide in enumerate(slides):
            self.current_slide = i + 1
            self._present_slide(slide, i, slides)

    def _present_slide(
        self, slide: SlideContent, slide_index: int, all_slides: List[SlideContent]
    ) -> None:
        """Present individual slide with navigation controls."""

        # Clear screen for cleaner presentation
        if self.console:
            self.console.clear()
        else:
            print("\n" * 50)  # Simple clear for non-Rich terminals

        # Show slide content
        self._display_slide_content(slide)

        # Show navigation footer with warnings
        self._show_navigation_footer(slide, slide_index, all_slides)

        # Wait for user input
        self._wait_for_user_input(slide)

    def _display_slide_content(self, slide: SlideContent) -> None:
        """Display the slide content with proper formatting."""

        if not self.console:
            # Simple text display
            print(f"\n=== {slide.title} ===\n")
            if isinstance(slide.content, list):
                for line in slide.content:
                    print(line)
            else:
                print(slide.content)
            return

        # Rich display with panels
        if isinstance(slide.content, list):
            content_text = "\n".join(slide.content)
        else:
            content_text = slide.content

        # Choose panel style based on slide type
        style_map = {
            SlideType.WELCOME: "bold blue",
            SlideType.CONTENT: "green",
            SlideType.QUESTION: "yellow",
            SlideType.TRANSITION: "magenta",
            SlideType.PROGRESS: "bold green",
        }

        border_style = style_map.get(slide.slide_type, "white")

        panel = Panel(
            content_text,
            title=f"[bold]{slide.title}[/bold]",
            border_style=border_style,
            padding=(1, 2),
        )

        self.console.print(panel)

    def _show_navigation_footer(
        self, current_slide: SlideContent, slide_index: int, all_slides: List[SlideContent]
    ) -> None:
        """Show navigation info and warnings about upcoming content."""

        progress = f"[{self.current_slide}/{self.total_slides}]"

        # Check what's coming next
        next_slide_warning = self._get_next_slide_warning(slide_index, all_slides)

        if not self.console:
            # Simple text footer
            print(f"\n--- {progress} ---")
            if next_slide_warning:
                print(f"⚠️  {next_slide_warning}")
            print("Press Enter to continue...")
            return

        # Rich footer with warnings
        footer_text = Text()
        footer_text.append(f"{progress} ", style="dim")

        if next_slide_warning:
            footer_text.append("⚠️  ", style="yellow")
            footer_text.append(next_slide_warning, style="yellow bold")
            footer_text.append("\n")

        footer_text.append("Press Enter to continue...", style="dim cyan")

        footer_panel = Panel(footer_text, border_style="dim", padding=(0, 1))

        self.console.print(footer_panel)

    def _get_next_slide_warning(
        self, current_index: int, all_slides: List[SlideContent]
    ) -> Optional[str]:
        """Generate warning message about upcoming slide content."""

        # Check the next slide
        if current_index + 1 >= len(all_slides):
            return None

        next_slide = all_slides[current_index + 1]

        warnings = {
            SlideType.QUESTION: "QUESTION COMING UP! Get ready to test your knowledge.",
            SlideType.TRANSITION: "Assessment time! Final questions ahead.",
            SlideType.PROGRESS: "Almost done! Summary coming up.",
        }

        return warnings.get(next_slide.slide_type)

    def _wait_for_user_input(self, slide: SlideContent) -> None:
        """Wait for user to press Enter before continuing."""

        try:
            if self.console and RICH_AVAILABLE:
                Prompt.ask("", default="")
            else:
                input()
        except (EOFError, KeyboardInterrupt):
            # Allow graceful exit
            if self.console:
                self.console.print("\n[yellow]Tutorial interrupted. Goodbye![/yellow]")
            else:
                print("\nTutorial interrupted. Goodbye!")
            raise SystemExit(0)
