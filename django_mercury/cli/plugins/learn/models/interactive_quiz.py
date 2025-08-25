"""
Interactive quiz handler with real user input and dynamic feedback.

Handles the user interaction layer of the tutorial system, capturing actual
user choices and generating appropriate feedback based on their selections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple, List, Optional, Any
from abc import ABC, abstractmethod

try:
    from rich.console import Console
    from rich.prompt import IntPrompt, Prompt
    from rich.panel import Panel
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class UserInteraction(Protocol):
    """Protocol defining user interaction interface."""

    def get_user_choice(self, question_text: str, options: List[str]) -> int:
        """Get user's choice index (0-based)."""
        ...

    def show_feedback(
        self,
        user_choice: int,
        correct_choice: int,
        user_answer: str,
        correct_answer: str,
        explanation: str,
        is_correct: bool,
    ) -> None:
        """Show dynamic feedback based on user's actual choice."""
        ...

    def show_hint(self, hint: str) -> None:
        """Show a hint to help the user."""
        ...


@dataclass(frozen=True)
class QuizResult:
    """Immutable result of a quiz question."""

    user_choice: int
    correct_choice: int
    is_correct: bool
    user_answer: str
    correct_answer: str
    explanation: str
    question_id: str
    time_taken: float = 0.0

    @property
    def score_percentage(self) -> float:
        """Get score as percentage (0.0 or 100.0)."""
        return 100.0 if self.is_correct else 0.0


class RichUserInteraction:
    """Rich terminal implementation of user interaction."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console() if RICH_AVAILABLE else None

    def get_user_choice(self, question_text: str, options: List[str]) -> int:
        """Get user choice with Rich UI."""
        if not self.console:
            return self._get_simple_choice(question_text, options)

        # Display question with Rich formatting
        question_panel = Panel(question_text, title="🤔 Question", border_style="blue")
        self.console.print(question_panel)

        # Display options
        options_text = Text()
        for i, option in enumerate(options, 1):
            options_text.append(f"{i}. {option}\n", style="")

        options_panel = Panel(options_text, title="Choose your answer", border_style="cyan")
        self.console.print(options_panel)

        # Get user input with validation
        while True:
            try:
                choice = IntPrompt.ask(
                    f"Enter your choice (1-{len(options)}) or 'h' for hint",
                    choices=[str(i) for i in range(1, len(options) + 1)] + ["h"],
                    default="1",
                )

                if isinstance(choice, str) and choice.lower() == "h":
                    return -1  # Special value for hint request

                return int(choice) - 1  # Convert to 0-based index

            except (ValueError, EOFError, KeyboardInterrupt):
                self.console.print("[red]Invalid choice. Please try again.[/red]")
                continue

    def _get_simple_choice(self, question_text: str, options: List[str]) -> int:
        """Fallback simple text input when Rich unavailable."""
        print(f"\n🤔 {question_text}\n")

        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")

        while True:
            try:
                choice = input(f"\nEnter your choice (1-{len(options)}): ").strip()
                if choice.lower() == "h":
                    return -1

                choice_int = int(choice)
                if 1 <= choice_int <= len(options):
                    return choice_int - 1
                else:
                    print(f"Please enter a number between 1 and {len(options)}")

            except (ValueError, EOFError, KeyboardInterrupt):
                print("Invalid input. Please enter a number.")
                continue

    def show_feedback(
        self,
        user_choice: int,
        correct_choice: int,
        user_answer: str,
        correct_answer: str,
        explanation: str,
        is_correct: bool,
    ) -> None:
        """Show dynamic feedback with Rich formatting."""

        if not self.console:
            return self._show_simple_feedback(
                user_choice, correct_choice, user_answer, correct_answer, explanation, is_correct
            )

        # Create feedback based on user's actual choice
        if is_correct:
            feedback_text = Text()
            feedback_text.append("✅ Correct! Excellent reasoning!", style="bold green")
            feedback_text.append(f"\n\n🎯 Your answer: {user_answer}", style="green")
            feedback_text.append(f"\n\n💡 Why it's correct: {explanation}", style="")

            panel = Panel(feedback_text, title="🎉 Outstanding!", border_style="green")
        else:
            feedback_text = Text()
            feedback_text.append("❌ Not quite right.", style="bold red")
            feedback_text.append(f"\n\n🔴 Your answer: {user_answer}", style="red")
            feedback_text.append(f"\n✅ Correct answer: {correct_answer}", style="green")
            feedback_text.append(f"\n\n💡 Explanation: {explanation}", style="")

            panel = Panel(feedback_text, title="Learning Opportunity", border_style="red")

        self.console.print(panel)

        # Wait for user acknowledgment
        try:
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
        except (EOFError, KeyboardInterrupt):
            pass

    def _show_simple_feedback(
        self,
        user_choice: int,
        correct_choice: int,
        user_answer: str,
        correct_answer: str,
        explanation: str,
        is_correct: bool,
    ) -> None:
        """Fallback simple feedback when Rich unavailable."""

        if is_correct:
            print("\n✅ Correct! Excellent reasoning!")
            print(f"🎯 Your answer: {user_answer}")
        else:
            print("\n❌ Not quite right.")
            print(f"🔴 Your answer: {user_answer}")
            print(f"✅ Correct answer: {correct_answer}")

        print(f"\n💡 Explanation: {explanation}")

        try:
            input("\nPress Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            pass

    def show_hint(self, hint: str) -> None:
        """Show hint with Rich formatting."""
        if not self.console:
            print(f"\n💡 Hint: {hint}")
            return

        hint_text = Text()
        hint_text.append("💡 Hint: ", style="bold yellow")
        hint_text.append(hint, style="yellow")

        panel = Panel(hint_text, title="Need a hint?", border_style="yellow")
        self.console.print(panel)


class InteractiveQuizHandler:
    """Handles interactive quiz questions with real user input."""

    def __init__(self, interaction: UserInteraction):
        self.interaction = interaction
        self.results: List[QuizResult] = []

    def present_question(self, question_data: dict[str, Any], question_id: str) -> QuizResult:
        """
        Present question and return result with user's actual choice.

        Args:
            question_data: Dictionary with question text, answers, etc.
            question_id: Unique identifier for the question

        Returns:
            QuizResult with user's choice and correctness
        """
        import time

        start_time = time.time()

        question_text = question_data["text"]
        answers = question_data["answers"]
        explanation = question_data["explanation"]

        # Extract answer options and find correct index
        options = [answer["text"] for answer in answers]
        correct_choice = next(i for i, answer in enumerate(answers) if answer["is_correct"])

        # Handle hint requests
        while True:
            user_choice = self.interaction.get_user_choice(question_text, options)

            if user_choice == -1:  # Hint requested
                # Find and show hint from any answer or question
                hint = self._get_hint(question_data)
                if hint:
                    self.interaction.show_hint(hint)
                    continue
                else:
                    self.interaction.show_hint("No hint available for this question.")
                    continue
            else:
                break

        # Determine correctness and get answer texts
        is_correct = user_choice == correct_choice
        user_answer = options[user_choice] if 0 <= user_choice < len(options) else "Invalid"
        correct_answer = options[correct_choice]

        # Show immediate feedback
        self.interaction.show_feedback(
            user_choice=user_choice,
            correct_choice=correct_choice,
            user_answer=user_answer,
            correct_answer=correct_answer,
            explanation=explanation,
            is_correct=is_correct,
        )

        end_time = time.time()

        # Create and store result
        result = QuizResult(
            user_choice=user_choice,
            correct_choice=correct_choice,
            is_correct=is_correct,
            user_answer=user_answer,
            correct_answer=correct_answer,
            explanation=explanation,
            question_id=question_id,
            time_taken=end_time - start_time,
        )

        self.results.append(result)
        return result

    def _get_hint(self, question_data: dict[str, Any]) -> Optional[str]:
        """Extract hint from question data."""

        # Try to get hint from any answer
        for answer in question_data.get("answers", []):
            if hint := answer.get("hint"):
                return hint

        # Try to get hint from question metadata
        if hints := question_data.get("hints"):
            return hints[0] if hints else None

        return None

    def get_session_summary(self) -> dict[str, Any]:
        """Get summary of the entire quiz session."""

        if not self.results:
            return {"total_questions": 0, "correct_answers": 0, "accuracy": 0.0, "total_time": 0.0}

        correct_count = sum(1 for result in self.results if result.is_correct)
        total_time = sum(result.time_taken for result in self.results)

        return {
            "total_questions": len(self.results),
            "correct_answers": correct_count,
            "accuracy": (correct_count / len(self.results)) * 100,
            "total_time": total_time,
            "results": self.results,
        }

    def reset(self) -> None:
        """Reset handler for new quiz session."""
        self.results.clear()
