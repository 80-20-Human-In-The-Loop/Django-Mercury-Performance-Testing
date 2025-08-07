"""
Interactive UI Components for Django Mercury Educational Mode

This module provides rich terminal UI components for interactive educational
experiences following the 80-20 Human-in-the-Loop philosophy.
"""

import time
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.layout import Layout
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


class InteractiveUI:
    """Provides interactive UI components for educational mode."""
    
    def __init__(self, console: Optional[Any] = None):
        """Initialize interactive UI."""
        self.console = console or (Console() if RICH_AVAILABLE else None)
    
    def show_performance_issue(
        self,
        test_name: str,
        issue_type: str,
        metrics: Dict[str, Any],
        severity: str = "warning"
    ):
        """
        Display a performance issue in an engaging way.
        
        Args:
            test_name: Name of the test that failed
            issue_type: Type of performance issue
            metrics: Performance metrics dict
            severity: Issue severity (warning/error/critical)
        """
        if not self.console or not RICH_AVAILABLE:
            self._show_text_issue(test_name, issue_type, metrics, severity)
            return
        
        # Determine colors based on severity
        severity_colors = {
            "warning": "yellow",
            "error": "red",
            "critical": "bold red"
        }
        color = severity_colors.get(severity, "yellow")
        
        # Create issue panel
        content = []
        content.append(f"[{color}]⚠️  Performance Issue Detected![/{color}]\n")
        content.append(f"[bold]Test:[/bold] {test_name}")
        content.append(f"[bold]Type:[/bold] {self._format_issue_type(issue_type)}")
        
        # Add metrics
        if metrics:
            content.append("\n[bold]Metrics:[/bold]")
            for key, value in metrics.items():
                formatted_key = key.replace('_', ' ').title()
                content.append(f"  • {formatted_key}: [{color}]{value}[/{color}]")
        
        panel = Panel(
            Text.from_markup("\n".join(content)),
            title="[bold]🚨 Learning Opportunity[/bold]",
            border_style=color,
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _show_text_issue(
        self,
        test_name: str,
        issue_type: str,
        metrics: Dict[str, Any],
        severity: str
    ):
        """Display issue in plain text."""
        print("\n" + "="*60)
        print(f"⚠️  PERFORMANCE ISSUE - {severity.upper()}")
        print("="*60)
        print(f"Test: {test_name}")
        print(f"Type: {self._format_issue_type(issue_type)}")
        
        if metrics:
            print("\nMetrics:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")
        print()
    
    def _format_issue_type(self, issue_type: str) -> str:
        """Format issue type for display."""
        formatted = issue_type.replace('_', ' ').title()
        
        # Special formatting for known types
        type_emojis = {
            "N Plus One Queries": "🔄 N+1 Queries",
            "Slow Response Time": "🐢 Slow Response",
            "Memory Optimization": "💾 Memory Issue",
            "Cache Optimization": "📦 Cache Miss",
            "General Performance": "⚡ Performance"
        }
        
        return type_emojis.get(formatted, formatted)
    
    def show_educational_content(
        self,
        title: str,
        content: str,
        content_type: str = "explanation",
        syntax_lang: Optional[str] = None
    ):
        """
        Display educational content in a formatted way.
        
        Args:
            title: Content title
            content: The educational content
            content_type: Type of content (explanation/code/tip)
            syntax_lang: Language for syntax highlighting (if code)
        """
        if not self.console or not RICH_AVAILABLE:
            self._show_text_content(title, content, content_type)
            return
        
        # Choose style based on content type
        styles = {
            "explanation": ("cyan", "📚"),
            "code": ("green", "💻"),
            "tip": ("yellow", "💡"),
            "warning": ("red", "⚠️"),
            "success": ("green", "✅")
        }
        
        style, emoji = styles.get(content_type, ("white", "📄"))
        
        # Create content panel
        if content_type == "code" and syntax_lang:
            rendered_content = Syntax(
                content,
                syntax_lang,
                theme="monokai",
                line_numbers=True
            )
        elif content_type == "explanation":
            rendered_content = Markdown(content)
        else:
            rendered_content = Text(content)
        
        panel = Panel(
            rendered_content,
            title=f"[bold {style}]{emoji} {title}[/bold {style}]",
            border_style=style,
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _show_text_content(
        self,
        title: str,
        content: str,
        content_type: str
    ):
        """Display content in plain text."""
        print(f"\n{title}")
        print("-" * len(title))
        print(content)
        print()
    
    def run_quiz(
        self,
        question: str,
        options: List[str],
        correct_answer: int,
        explanation: str
    ) -> Dict[str, Any]:
        """
        Run an interactive quiz question.
        
        Args:
            question: The quiz question
            options: List of answer options
            correct_answer: Index of correct answer (0-based)
            explanation: Explanation of the answer
            
        Returns:
            Dict with quiz results
        """
        if not self.console or not RICH_AVAILABLE:
            return self._run_text_quiz(question, options, correct_answer, explanation)
        
        # Display question
        question_panel = Panel(
            Text(question, style="bold"),
            title="[bold cyan]🤔 Quick Check[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(question_panel)
        
        # Display options
        self.console.print("\n[bold]Choose your answer:[/bold]\n")
        for i, option in enumerate(options, 1):
            self.console.print(f"  [{i}] {option}")
        
        # Get user answer
        self.console.print()
        answer = IntPrompt.ask(
            "[yellow]Your answer[/yellow]",
            choices=[str(i) for i in range(1, len(options) + 1)]
        )
        
        user_answer = answer - 1  # Convert to 0-based index
        is_correct = user_answer == correct_answer
        
        # Show result with animation
        self._show_quiz_result(is_correct, options[correct_answer], explanation)
        
        # Ask if they want to learn more
        wants_to_learn = False
        if not is_correct:
            wants_to_learn = Confirm.ask(
                "\n[yellow]Would you like to learn more about this?[/yellow]",
                default=True
            )
        
        return {
            'correct': is_correct,
            'user_answer': user_answer,
            'wants_to_learn': wants_to_learn
        }
    
    def _run_text_quiz(
        self,
        question: str,
        options: List[str],
        correct_answer: int,
        explanation: str
    ) -> Dict[str, Any]:
        """Run quiz in plain text mode."""
        print(f"\n🤔 QUIZ: {question}\n")
        
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        # Get answer
        while True:
            try:
                answer = int(input("\nYour answer (1-{}): ".format(len(options))))
                if 1 <= answer <= len(options):
                    break
                print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        user_answer = answer - 1
        is_correct = user_answer == correct_answer
        
        # Show result
        if is_correct:
            print("\n✅ Correct!")
        else:
            print(f"\n❌ Not quite. The correct answer is: {options[correct_answer]}")
        
        print(f"\nExplanation: {explanation}")
        
        return {
            'correct': is_correct,
            'user_answer': user_answer,
            'wants_to_learn': False
        }
    
    def _show_quiz_result(self, is_correct: bool, correct_answer: str, explanation: str):
        """Display quiz result with visual feedback."""
        if is_correct:
            # Success animation
            with self.console.status("[bold green]Checking answer...[/bold green]"):
                time.sleep(0.5)
            
            success_panel = Panel(
                Text.from_markup(
                    "[bold green]✅ Excellent! That's correct![/bold green]\n\n"
                    f"[dim]{explanation}[/dim]"
                ),
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(success_panel)
        else:
            # Incorrect animation
            with self.console.status("[bold yellow]Checking answer...[/bold yellow]"):
                time.sleep(0.5)
            
            feedback_panel = Panel(
                Text.from_markup(
                    "[bold yellow]Not quite right, but that's okay![/bold yellow]\n\n"
                    f"[bold]Correct answer:[/bold] {correct_answer}\n\n"
                    f"[cyan]Explanation:[/cyan] {explanation}"
                ),
                border_style="yellow",
                padding=(1, 2)
            )
            self.console.print(feedback_panel)
    
    def show_progress_bar(self, total: int, description: str = "Processing"):
        """
        Create a progress bar context manager.
        
        Args:
            total: Total number of items
            description: Description of the task
            
        Returns:
            Progress context manager
        """
        if not self.console or not RICH_AVAILABLE:
            return DummyProgress()
        
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
    
    def show_optimization_steps(self, steps: List[Dict[str, str]]):
        """
        Display optimization steps in an interactive way.
        
        Args:
            steps: List of step dictionaries with 'title' and 'description'
        """
        if not self.console or not RICH_AVAILABLE:
            self._show_text_steps(steps)
            return
        
        # Create steps table
        table = Table(
            title="🛠️  Optimization Steps",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("Step", style="cyan", width=5)
        table.add_column("Action", style="white")
        table.add_column("Impact", style="green", width=15)
        
        for i, step in enumerate(steps, 1):
            table.add_row(
                str(i),
                step.get('title', ''),
                step.get('impact', 'Performance+')
            )
        
        self.console.print(table)
        
        # Ask if user wants details
        if steps and Confirm.ask("\n[yellow]See detailed steps?[/yellow]", default=False):
            for i, step in enumerate(steps, 1):
                self.console.print(f"\n[bold]Step {i}: {step.get('title', '')}[/bold]")
                self.console.print(step.get('description', ''))
                
                if step.get('code'):
                    self.console.print("\n[dim]Example code:[/dim]")
                    self.console.print(
                        Syntax(
                            step['code'],
                            "python",
                            theme="monokai",
                            line_numbers=True
                        )
                    )
                
                if i < len(steps):
                    if not Confirm.ask("\n[yellow]Continue to next step?[/yellow]", default=True):
                        break
    
    def _show_text_steps(self, steps: List[Dict[str, str]]):
        """Display steps in plain text."""
        print("\n🛠️  OPTIMIZATION STEPS")
        print("="*40)
        
        for i, step in enumerate(steps, 1):
            print(f"\n{i}. {step.get('title', '')}")
            if step.get('description'):
                print(f"   {step['description']}")
    
    def wait_for_continue(self, message: str = "Press Enter to continue..."):
        """
        Wait for user to continue.
        
        Args:
            message: Message to display
        """
        if self.console and RICH_AVAILABLE:
            self.console.print(f"\n[dim]{message}[/dim]")
            input()
        else:
            input(f"\n{message}")
    
    def show_celebration(self, message: str = "Great job!"):
        """
        Show a celebration message for achievements.
        
        Args:
            message: Celebration message
        """
        if not self.console or not RICH_AVAILABLE:
            print(f"\n🎉 {message}")
            return
        
        celebration = Panel(
            Text.from_markup(
                f"[bold green]🎉 {message} 🎉[/bold green]\n\n"
                "[yellow]You're making great progress![/yellow]"
            ),
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(celebration)


class DummyProgress:
    """Dummy progress context manager for when Rich is not available."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def add_task(self, *args, **kwargs):
        return 0
    
    def update(self, *args, **kwargs):
        pass


# Convenience functions
def show_performance_issue(test_name: str, issue_type: str, metrics: Dict[str, Any]):
    """Show a performance issue using the default console."""
    ui = InteractiveUI()
    ui.show_performance_issue(test_name, issue_type, metrics)


def run_quiz(question: str, options: List[str], correct_answer: int, explanation: str) -> Dict[str, Any]:
    """Run a quiz using the default console."""
    ui = InteractiveUI()
    return ui.run_quiz(question, options, correct_answer, explanation)


def wait_for_continue(message: str = "Press Enter to continue..."):
    """Wait for user to continue using the default console."""
    ui = InteractiveUI()
    ui.wait_for_continue(message)