"""Slideshow UI component for the Learn plugin.

This module provides a rich terminal slideshow interface that creates
an engaging presentation-style learning experience.
"""

from typing import List, Dict, Any, Optional, Callable, Union
import time
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.text import Text
    from rich.align import Align
    from rich.layout import Layout
    from rich.live import Live
    from rich.prompt import Confirm
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class Slide:
    """Individual slide in the slideshow."""

    content: Union[str, Panel, Any]  # Rich renderable or string
    title: Optional[str] = None
    subtitle: Optional[str] = None
    pause_before: float = 0.0  # Seconds to pause before showing
    pause_after: float = 2.0  # Seconds to pause after showing
    auto_advance: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SlideShow:
    """Rich terminal slideshow component with navigation and animation."""

    def __init__(self, console: Optional[Console] = None, theme: Optional[str] = None):
        """Initialize slideshow with optional console and theme."""
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.theme = theme or "default"
        self.slides: List[Slide] = []
        self.current_slide = 0
        self.is_playing = False
        self.auto_play = False
        self.transition_speed = 0.3

        # Navigation callbacks
        self.on_slide_change: Optional[Callable[[int], None]] = None
        self.on_complete: Optional[Callable[[], None]] = None

        # Quiz score tracking
        self.quiz_score = 0
        self.quiz_total = 0

    def add_slide(
        self,
        content: Union[str, Panel, Any],
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        auto_advance: bool = False,
        pause_before: float = 0.0,
        pause_after: float = 2.0,
        **metadata,
    ) -> None:
        """Add a slide to the slideshow."""
        slide = Slide(
            content=content,
            title=title,
            subtitle=subtitle,
            auto_advance=auto_advance,
            pause_before=pause_before,
            pause_after=pause_after,
            metadata=metadata,
        )
        self.slides.append(slide)

    def add_welcome_slide(self, title: str, description: str, progress_info: str = "") -> None:
        """Add a welcome slide with title and description."""
        if not RICH_AVAILABLE:
            content = f"{title}\n\n{description}\n{progress_info}"
        else:
            content_text = Text()
            content_text.append(f"🎓 {title}", style="bold cyan")
            content_text.append(f"\n{progress_info}", style="dim")
            content_text.append(f"\n\n📚 {description}", style="")
            content_text.append("\n\nPress Enter to begin or Q to quit", style="dim italic")

            content = Panel(
                Align.center(content_text),
                title="Welcome to Mercury Learning",
                border_style="cyan",
                padding=(2, 4),
            )

        self.add_slide(content, auto_advance=False, pause_after=0)

    def add_context_slide(self, scenario: str, problem: str) -> None:
        """Add a context-setting slide with real-world scenario."""
        if not RICH_AVAILABLE:
            content = f"Real Scenario\n\n{scenario}\n\n{problem}\n\nLet's learn how to fix this!"
        else:
            content_text = Text()
            content_text.append("💡 Real Scenario", style="bold yellow")
            content_text.append(f"\n\n{scenario}", style="")
            content_text.append(f"\n\n{problem}", style="red")
            content_text.append("\n\nLet's learn how to fix this! →", style="bold green")

            content = Panel(content_text, border_style="yellow", padding=(1, 2))

        self.add_slide(content, auto_advance=False, pause_after=0)

    def add_question_slide(
        self,
        question: str,
        options: List[str],
        question_number: int,
        total_questions: int,
        correct_index: int = 0,
        explanation: str = "",
        question_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an interactive quiz question slide with real input capture."""

        # Store question metadata for interactive handling
        question_metadata = {
            "question": question,
            "options": options,
            "correct_index": correct_index,
            "explanation": explanation,
            "question_number": question_number,
            "total_questions": total_questions,
            "question_data": question_data or {},
        }

        if not RICH_AVAILABLE:
            content = f"Question {question_number} of {total_questions}\n\n{question}\n\n"
            for i, option in enumerate(options, 1):
                content += f"{i}. {option}\n"
            content += f"\nEnter your choice (1-{len(options)}): "
        else:
            content_text = Text()
            content_text.append(
                f"🤔 Question {question_number} of {total_questions}", style="bold blue"
            )
            content_text.append(f"\n\n{question}", style="")
            content_text.append("\n")

            for i, option in enumerate(options, 1):
                content_text.append(
                    f"\n❶ " if i == 1 else f"\n❷ " if i == 2 else f"\n❸ " if i == 3 else f"\n❹ ",
                    style="cyan",
                )
                content_text.append(option, style="")

            content_text.append(f"\n\nEnter your choice (1-{len(options)}): ", style="bold yellow")

            content = Panel(content_text, border_style="blue", padding=(1, 2))

        # Mark this as an interactive question slide
        metadata = {"type": "interactive_question", **question_metadata}
        slide = Slide(
            content=content,
            title="",
            auto_advance=False,
            pause_after=0,
            pause_before=0,
            metadata=metadata,
        )
        self.slides.append(slide)

    def add_feedback_slide(
        self, correct: bool, explanation: str, selected_answer: str, correct_answer: str
    ) -> None:
        """Add feedback slide showing if answer was correct."""
        if not RICH_AVAILABLE:
            status = "✅ Correct!" if correct else "❌ Incorrect."
            content = f"{status}\n\n{explanation}\n\nPress Enter to continue"
        else:
            if correct:
                content_text = Text()
                content_text.append("✅ Correct! Outstanding reasoning!", style="bold green")
                content_text.append(f"\n\n🧠 Why: {explanation}", style="")

                content = Panel(
                    content_text, title="Excellent!", border_style="green", padding=(1, 2)
                )
            else:
                content_text = Text()
                content_text.append(f"❌ Not quite right.", style="bold red")
                content_text.append(f"\n\nYour answer: {selected_answer}", style="dim")
                content_text.append(f"\nCorrect answer: {correct_answer}", style="green")
                content_text.append(f"\n\n💡 Why: {explanation}", style="")

                content = Panel(
                    content_text, title="Learning Opportunity", border_style="red", padding=(1, 2)
                )

            content_text.append("\n\nPress Enter to continue →", style="dim italic")

        self.add_slide(content, auto_advance=False, pause_after=0)

    def add_solution_slide(
        self, title: str, code_before: str, code_after: str, impact: str
    ) -> None:
        """Add solution slide with before/after code."""
        if not RICH_AVAILABLE:
            content = f"{title}\n\n# Before\n{code_before}\n\n# After\n{code_after}\n\n{impact}"
        else:
            from rich.syntax import Syntax

            content_text = Text()
            content_text.append(f"⚡ {title}", style="bold yellow")
            content_text.append("\n\n# ❌ Before (inefficient)", style="red")

            # Add code syntax highlighting if available
            try:
                before_syntax = Syntax(code_before, "python", theme="monokai")
                after_syntax = Syntax(code_after, "python", theme="monokai")
            except:
                content_text.append(f"\n{code_before}", style="red")
                content_text.append("\n\n# ✅ After (optimized)", style="green")
                content_text.append(f"\n{code_after}", style="green")
            else:
                content = Panel(content_text, border_style="yellow", padding=(1, 2))
                # Handle syntax highlighting in a more complex layout
                return

            content_text.append(f"\n\n{impact} 🚀", style="bold green")

            content = Panel(content_text, border_style="yellow", padding=(1, 2))

        self.add_slide(content, auto_advance=False, pause_after=0)

    def add_progress_slide(
        self,
        score: int,
        total: int,
        accuracy: float,
        concept_progress: Dict[str, float],
        next_steps: str,
    ) -> None:
        """Add progress summary slide that will show current quiz scores."""
        # Store parameters for dynamic display - scores will be updated when shown
        metadata = {
            "type": "progress_summary",
            "concept_progress": concept_progress,
            "next_steps": next_steps,
        }

        # Create placeholder content - will be replaced dynamically
        if not RICH_AVAILABLE:
            content = "Quiz Complete! Calculating scores..."
        else:
            content_text = Text()
            content_text.append("🎉 Quiz Complete! Calculating scores...", style="bold green")
            content = Panel(
                content_text, title="Learning Progress", border_style="green", padding=(1, 2)
            )

        self.add_slide(content, auto_advance=False, pause_after=0, **metadata)

    def show(self, start_slide: int = 0, auto_play: bool = False) -> None:
        """Show the slideshow starting from specified slide."""
        if not self.slides:
            return

        self.current_slide = start_slide
        self.auto_play = auto_play
        self.is_playing = True

        if not RICH_AVAILABLE:
            self._show_simple()
        else:
            self._show_rich()

    def _show_simple(self) -> None:
        """Simple text-based slideshow for when Rich is not available."""
        while self.is_playing and self.current_slide < len(self.slides):
            slide = self.slides[self.current_slide]

            # Clear screen
            print("\n" * 50)

            # Show slide
            if slide.title:
                print(f"=== {slide.title} ===\n")

            if isinstance(slide.content, str):
                print(slide.content)
            else:
                print(str(slide.content))

            # Handle navigation
            if slide.auto_advance:
                time.sleep(slide.pause_after)
                self.next_slide()
            else:
                input("\nPress Enter to continue...")
                self.next_slide()

    def _show_rich(self) -> None:
        """Rich terminal slideshow with animations and styling."""
        try:
            while self.is_playing and self.current_slide < len(self.slides):
                slide = self.slides[self.current_slide]

                # Pause before showing slide
                if slide.pause_before > 0:
                    time.sleep(slide.pause_before)

                # Clear and show slide
                self.console.clear()

                if slide.title:
                    title_text = Text(slide.title, style="bold cyan")
                    self.console.print(Align.center(title_text))
                    self.console.print()

                # Show slide content
                if isinstance(slide.content, str):
                    self.console.print(Panel(slide.content, border_style="cyan"))
                else:
                    self.console.print(slide.content)

                # Handle different slide types
                if slide.auto_advance:
                    time.sleep(slide.pause_after)
                    self.next_slide()
                elif slide.metadata and slide.metadata.get("type") == "interactive_question":
                    # Handle interactive question with real input capture
                    user_answered_correctly = self._handle_interactive_question(slide)
                    # Track quiz score
                    self.quiz_total += 1
                    if user_answered_correctly:
                        self.quiz_score += 1

                    self.next_slide()
                elif slide.metadata and slide.metadata.get("type") == "progress_summary":
                    # Handle progress summary with dynamic scores
                    self._show_progress_summary(slide)
                    self.next_slide()
                else:
                    # Wait for user input
                    try:
                        from rich.prompt import Prompt

                        response = Prompt.ask(
                            "\n[dim]Press Enter to continue, 'q' to quit, 'b' for back[/dim]",
                            default="",
                            show_default=False,
                        )

                        if response.lower() == "q":
                            self.stop()
                        elif response.lower() == "b":
                            self.previous_slide()
                        else:
                            self.next_slide()
                    except (EOFError, KeyboardInterrupt):
                        self.stop()
                        break

                # Call slide change callback
                if self.on_slide_change:
                    self.on_slide_change(self.current_slide)

        except Exception as e:
            if self.console:
                self.console.print(f"[red]Error in slideshow: {e}[/red]")
            self.stop()

    def next_slide(self) -> bool:
        """Move to next slide. Returns False if at end."""
        if self.current_slide < len(self.slides) - 1:
            self.current_slide += 1
            return True
        else:
            self.stop()
            if self.on_complete:
                self.on_complete()
            return False

    def previous_slide(self) -> bool:
        """Move to previous slide. Returns False if at beginning."""
        if self.current_slide > 0:
            self.current_slide -= 1
            return True
        return False

    def jump_to_slide(self, slide_number: int) -> bool:
        """Jump to specific slide number (0-based)."""
        if 0 <= slide_number < len(self.slides):
            self.current_slide = slide_number
            return True
        return False

    def stop(self) -> None:
        """Stop the slideshow."""
        self.is_playing = False

    def get_slide_count(self) -> int:
        """Get total number of slides."""
        return len(self.slides)

    def get_current_slide_number(self) -> int:
        """Get current slide number (0-based)."""
        return self.current_slide

    def get_quiz_score(self) -> tuple[int, int]:
        """Get current quiz score (correct, total)."""
        return (self.quiz_score, self.quiz_total)

    def reset_quiz_score(self) -> None:
        """Reset quiz score tracking."""
        self.quiz_score = 0
        self.quiz_total = 0

    def _handle_interactive_question(self, slide: Slide) -> bool:
        """Handle interactive question with real user input and validation."""
        metadata = slide.metadata
        question = metadata.get("question", "")
        options = metadata.get("options", [])
        correct_index = metadata.get("correct_index", 0)
        explanation = metadata.get("explanation", "")

        try:
            from rich.prompt import Prompt

            while True:
                # Get user input
                try:
                    choice_str = Prompt.ask(
                        f"\n[bold yellow]Enter your choice (1-{len(options)})[/bold yellow]",
                        default="",
                        show_default=False,
                    )

                    # Validate input
                    if not choice_str.strip():
                        self.console.print(
                            f"[red]❌ Please enter an option! 1/{len(options)}![/red]"
                        )
                        continue

                    try:
                        choice = int(choice_str)
                        if choice < 1 or choice > len(options):
                            self.console.print(
                                f"[red]❌ Please enter an option! 1/{len(options)}![/red]"
                            )
                            continue
                    except ValueError:
                        self.console.print(
                            f"[red]❌ Please enter an option! 1/{len(options)}![/red]"
                        )
                        continue

                    # Valid choice - check if correct
                    user_index = choice - 1  # Convert to 0-based
                    is_correct = user_index == correct_index
                    user_answer = options[user_index]
                    correct_answer = options[correct_index]

                    # Show immediate feedback
                    self._show_question_feedback(
                        is_correct, user_answer, correct_answer, explanation
                    )

                    return is_correct

                except (EOFError, KeyboardInterrupt):
                    return False

        except ImportError:
            # Fallback for when Rich is not available
            while True:
                try:
                    choice_str = input(f"\nEnter your choice (1-{len(options)}): ").strip()

                    if not choice_str:
                        print(f"❌ Please enter an option! 1/{len(options)}!")
                        continue

                    try:
                        choice = int(choice_str)
                        if choice < 1 or choice > len(options):
                            print(f"❌ Please enter an option! 1/{len(options)}!")
                            continue
                    except ValueError:
                        print(f"❌ Please enter an option! 1/{len(options)}!")
                        continue

                    # Valid choice
                    user_index = choice - 1
                    is_correct = user_index == correct_index
                    user_answer = options[user_index]
                    correct_answer = options[correct_index]

                    # Show feedback
                    if is_correct:
                        print(f"\n✅ Correct! {explanation}")
                    else:
                        print(f"\n❌ Wrong! Your answer: {user_answer}")
                        print(f"✅ Correct answer: {correct_answer}")
                        print(f"💡 {explanation}")

                    input("\nPress Enter to continue...")
                    return is_correct

                except (EOFError, KeyboardInterrupt):
                    return False

    def _show_question_feedback(
        self, is_correct: bool, user_answer: str, correct_answer: str, explanation: str
    ) -> None:
        """Show feedback for question answer with Rich formatting."""
        if not RICH_AVAILABLE or not self.console:
            return

        from rich.text import Text
        from rich.panel import Panel

        if is_correct:
            feedback_text = Text()
            feedback_text.append("✅ Correct! Outstanding reasoning!", style="bold green")
            feedback_text.append(f"\n\n🎯 Your answer: {user_answer}", style="green")
            feedback_text.append(f"\n\n💡 Why it's correct: {explanation}", style="")

            panel = Panel(
                feedback_text, title="🎉 Excellent!", border_style="green", padding=(1, 2)
            )
        else:
            feedback_text = Text()
            feedback_text.append("❌ Not quite right.", style="bold red")
            feedback_text.append(f"\n\n🔴 Your answer: {user_answer}", style="red")
            feedback_text.append(f"\n✅ Correct answer: {correct_answer}", style="green")
            feedback_text.append(f"\n\n💡 Explanation: {explanation}", style="")

            panel = Panel(
                feedback_text, title="Learning Opportunity", border_style="red", padding=(1, 2)
            )

        self.console.print(panel)

        # Wait for user acknowledgment
        try:
            from rich.prompt import Prompt

            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
        except (EOFError, KeyboardInterrupt):
            pass

    def _show_progress_summary(self, slide: Slide) -> None:
        """Show progress summary with current quiz scores."""
        if not RICH_AVAILABLE or not self.console:
            return

        metadata = slide.metadata
        concept_progress = metadata.get("concept_progress", {})
        next_steps = metadata.get("next_steps", "Great work!")

        # Get current quiz scores
        quiz_score, quiz_total = self.get_quiz_score()
        accuracy = (quiz_score / quiz_total * 100) if quiz_total > 0 else 0.0

        from rich.text import Text
        from rich.panel import Panel

        content_text = Text()
        content_text.append(
            f"🎉 Quiz Complete! Score: {quiz_score}/{quiz_total} ({accuracy:.0f}%)",
            style="bold green",
        )
        content_text.append("\n\n📈 Your Progress:", style="bold")

        for concept, progress in concept_progress.items():
            status = "✓" if progress >= 80 else "↗" if progress >= 60 else "○"
            style = "green" if progress >= 80 else "yellow" if progress >= 60 else ""
            bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
            content_text.append(f"\n• {concept}: {bar} {progress:.0f}% {status}", style=style)

        content_text.append(f"\n\n🎯 {next_steps}", style="cyan")
        content_text.append("\n\nPress R to retake or Enter to continue", style="dim italic")

        panel = Panel(content_text, title="Learning Progress", border_style="green", padding=(1, 2))

        self.console.print(panel)

        # Wait for user input
        try:
            from rich.prompt import Prompt

            response = Prompt.ask(
                "\n[dim]Press Enter to continue, 'q' to quit, 'r' to retake[/dim]",
                default="",
                show_default=False,
            )

            if response.lower() == "q":
                self.stop()
            elif response.lower() == "r":
                # Handle retake - would need to reset quiz and restart
                pass
        except (EOFError, KeyboardInterrupt):
            self.stop()
