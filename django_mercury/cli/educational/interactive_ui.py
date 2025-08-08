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

    def run_interactive_tutorial(
        self, 
        tutorial_name: str, 
        tutorial_stages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run an interactive step-by-step tutorial with multiple stages.
        
        This provides guided learning experiences where users progress through
        optimization tutorials at their own pace with hands-on exercises.
        
        Args:
            tutorial_name: Name of the tutorial
            tutorial_stages: List of tutorial stage dictionaries
            
        Returns:
            Dictionary with tutorial completion results
        """
        if not self.console or not RICH_AVAILABLE:
            return self._run_text_tutorial(tutorial_name, tutorial_stages)
        
        # Welcome to tutorial
        welcome_panel = Panel(
            Text.from_markup(
                f"[bold cyan]🎓 Interactive Tutorial: {tutorial_name}[/bold cyan]\n\n"
                f"[yellow]Stages:[/yellow] {len(tutorial_stages)}\n"
                f"[yellow]Estimated Time:[/yellow] {sum(stage.get('estimated_minutes', 5) for stage in tutorial_stages)} minutes\n\n"
                "[italic]Let's learn Django performance optimization step by step![/italic]"
            ),
            title="[bold]Tutorial Starting[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(welcome_panel)
        
        if not Confirm.ask("\n[yellow]Ready to start the tutorial?[/yellow]", default=True):
            return {'completed': False, 'reason': 'user_cancelled'}
        
        completed_stages = []
        current_stage = 0
        
        for i, stage in enumerate(tutorial_stages, 1):
            current_stage = i
            
            # Stage header
            self.console.print(f"\n{'='*60}")
            stage_header = Panel(
                Text.from_markup(
                    f"[bold yellow]📝 Stage {i}/{len(tutorial_stages)}: {stage['title']}[/bold yellow]\n\n"
                    f"[white]{stage.get('description', '')}[/white]\n\n"
                    f"[cyan]Estimated time: {stage.get('estimated_minutes', 5)} minutes[/cyan]"
                ),
                border_style="yellow",
                padding=(1, 2)
            )
            self.console.print(stage_header)
            
            # Show stage content
            if stage.get('explanation'):
                self.show_educational_content(
                    "Understanding the Problem",
                    stage['explanation'],
                    "explanation"
                )
            
            # Show before code (problem)
            if stage.get('before_code'):
                self.show_educational_content(
                    "❌ Current (Problematic) Code",
                    stage['before_code'],
                    "code",
                    "python"
                )
            
            # Interactive element - ask user to identify the issue
            if stage.get('challenge_question'):
                challenge_result = self.run_quiz(
                    stage['challenge_question'],
                    stage.get('challenge_options', ['Option 1', 'Option 2', 'Option 3', 'Option 4']),
                    stage.get('challenge_answer', 0),
                    stage.get('challenge_explanation', 'Here\'s why this is the correct approach.')
                )
                
                if challenge_result['correct']:
                    self.console.print("\n[bold green]✅ Excellent understanding![/bold green]")
                else:
                    self.console.print(f"\n[yellow]📚 No worries! Let's learn together.[/yellow]")
            
            # Show the solution
            if stage.get('after_code'):
                self.show_educational_content(
                    "✅ Optimized Solution",
                    stage['after_code'],
                    "code", 
                    "python"
                )
            
            # Show performance improvement if available
            if stage.get('performance_improvement'):
                improvement_panel = Panel(
                    Text.from_markup(
                        f"[bold green]📊 Performance Improvement[/bold green]\n\n"
                        f"{stage['performance_improvement']}"
                    ),
                    border_style="green",
                    padding=(1, 2)
                )
                self.console.print(improvement_panel)
            
            # Key takeaways
            if stage.get('key_takeaways'):
                takeaways = "\n".join([f"• {takeaway}" for takeaway in stage['key_takeaways']])
                self.show_educational_content(
                    "🎯 Key Takeaways",
                    takeaways,
                    "tip"
                )
            
            # Video tutorial placeholder
            if stage.get('video_url'):
                video_panel = Panel(
                    Text.from_markup(
                        f"[bold blue]📹 Video Tutorial Available[/bold blue]\n\n"
                        f"Watch a detailed walkthrough of this optimization:\n"
                        f"[cyan]{stage['video_url']}[/cyan]\n\n"
                        f"[italic]This video shows the step-by-step process with real-world examples.[/italic]"
                    ),
                    border_style="blue",
                    title="Video Resource",
                    padding=(1, 2)
                )
                self.console.print(video_panel)
            
            # Stage completion
            completed_stages.append({
                'stage_number': i,
                'stage_title': stage['title'],
                'completed_at': time.time(),
                'challenge_correct': challenge_result.get('correct', False) if 'challenge_question' in stage else None
            })
            
            # Ask if ready for next stage
            if i < len(tutorial_stages):
                self.console.print(f"\n[bold green]✅ Stage {i} completed![/bold green]")
                
                if not Confirm.ask("\n[yellow]Continue to next stage?[/yellow]", default=True):
                    break
            else:
                self.console.print(f"\n[bold green]🎉 Tutorial completed![/bold green]")
        
        # Tutorial completion summary
        completion_panel = Panel(
            Text.from_markup(
                f"[bold green]🎓 Tutorial Complete: {tutorial_name}[/bold green]\n\n"
                f"[yellow]Stages Completed:[/yellow] {len(completed_stages)}/{len(tutorial_stages)}\n"
                f"[yellow]Success Rate:[/yellow] {self._calculate_tutorial_success_rate(completed_stages)}%\n\n"
                "[italic]Great job learning Django performance optimization![/italic]"
            ),
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(completion_panel)
        
        return {
            'completed': len(completed_stages) == len(tutorial_stages),
            'tutorial_name': tutorial_name,
            'stages_completed': len(completed_stages),
            'total_stages': len(tutorial_stages),
            'completion_details': completed_stages,
            'success_rate': self._calculate_tutorial_success_rate(completed_stages)
        }

    def _run_text_tutorial(
        self, 
        tutorial_name: str, 
        tutorial_stages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run tutorial in plain text mode."""
        print(f"\n📚 TUTORIAL: {tutorial_name}")
        print("=" * 60)
        
        for i, stage in enumerate(tutorial_stages, 1):
            print(f"\nSTAGE {i}: {stage['title']}")
            print("-" * 40)
            
            if stage.get('description'):
                print(f"Description: {stage['description']}")
            
            if stage.get('before_code'):
                print(f"\nBefore (Problematic):\n{stage['before_code']}")
            
            if stage.get('after_code'):
                print(f"\nAfter (Optimized):\n{stage['after_code']}")
            
            if stage.get('key_takeaways'):
                print("\nKey Takeaways:")
                for takeaway in stage['key_takeaways']:
                    print(f"  • {takeaway}")
            
            if i < len(tutorial_stages):
                input("\nPress Enter to continue to next stage...")
        
        print(f"\n✅ Tutorial '{tutorial_name}' completed!")
        return {'completed': True, 'stages_completed': len(tutorial_stages)}

    def _calculate_tutorial_success_rate(self, completed_stages: List[Dict[str, Any]]) -> int:
        """Calculate success rate based on challenge question performance."""
        if not completed_stages:
            return 0
            
        challenges_with_answers = [
            stage for stage in completed_stages 
            if stage.get('challenge_correct') is not None
        ]
        
        if not challenges_with_answers:
            return 100  # No challenges, consider it successful completion
        
        correct_answers = sum(
            1 for stage in challenges_with_answers 
            if stage.get('challenge_correct', False)
        )
        
        return int((correct_answers / len(challenges_with_answers)) * 100)

    def run_code_challenge(
        self,
        challenge_name: str,
        problem_description: str,
        problematic_code: str,
        expected_solution_patterns: List[str],
        performance_context: Dict[str, Any],
        hints: List[str] = None,
        difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Run an interactive code-fixing challenge where users practice optimizing real Django code.
        
        This provides hands-on learning experiences where users can practice fixing
        actual performance issues they encounter in real Django applications.
        
        Args:
            challenge_name: Name of the coding challenge
            problem_description: Description of the performance issue
            problematic_code: The code that needs optimization
            expected_solution_patterns: List of patterns the solution should contain
            performance_context: Context about the performance issue (query count, etc.)
            hints: Optional hints to help users
            difficulty: Challenge difficulty level
            
        Returns:
            Dictionary with challenge completion results
        """
        if not self.console or not RICH_AVAILABLE:
            return self._run_text_code_challenge(
                challenge_name, problem_description, problematic_code, expected_solution_patterns
            )
        
        # Challenge introduction
        challenge_panel = Panel(
            Text.from_markup(
                f"[bold cyan]💻 Interactive Code Challenge: {challenge_name}[/bold cyan]\\n\\n"
                f"[yellow]Difficulty:[/yellow] {difficulty.capitalize()}\\n"
                f"[yellow]Performance Issue:[/yellow] {problem_description}\\n\\n"
                f"[italic]Your mission: Fix the performance problem in the code below![/italic]"
            ),
            title="[bold]Hands-On Learning[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(challenge_panel)
        
        # Show performance context
        if performance_context:
            context_content = []
            for key, value in performance_context.items():
                formatted_key = key.replace('_', ' ').title()
                context_content.append(f"• [red]{formatted_key}:[/red] {value}")
            
            context_panel = Panel(
                Text.from_markup("\\n".join(context_content)),
                title="[bold red]⚠️  Performance Problems Detected[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            self.console.print(context_panel)
        
        # Show the problematic code
        self.show_educational_content(
            "❌ Current Code (Needs Optimization)",
            problematic_code,
            "code",
            "python"
        )
        
        # Show hints if available
        if hints:
            hints_text = "\\n".join([f"💡 {hint}" for hint in hints])
            self.show_educational_content(
                "🔍 Hints to Help You",
                hints_text,
                "tip"
            )
        
        # Interactive coding session
        attempts = 0
        max_attempts = 3
        success = False
        
        while attempts < max_attempts and not success:
            attempts += 1
            
            self.console.print(f"\\n[bold yellow]Attempt {attempts}/{max_attempts}:[/bold yellow]")
            self.console.print("[dim]Enter your optimized code below. Type 'DONE' on a new line when finished:[/dim]\\n")
            
            # Collect user's solution
            user_code_lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "DONE":
                        break
                    user_code_lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\\n[yellow]Challenge cancelled by user[/yellow]")
                    return {'completed': False, 'reason': 'user_cancelled'}
            
            user_code = "\\n".join(user_code_lines)
            
            if not user_code.strip():
                self.console.print("[red]❌ No code provided. Please try again.[/red]")
                continue
            
            # Check the solution
            feedback = self._check_code_solution(user_code, expected_solution_patterns)
            success = feedback['correct']
            
            if success:
                # Show success with celebration
                self.console.print(f"\\n[bold green]🎉 Excellent work! Challenge completed in {attempts} attempts![/bold green]")
                
                # Show their optimized code
                self.show_educational_content(
                    "✅ Your Optimized Solution",
                    user_code,
                    "code",
                    "python"
                )
                
                # Show the improvements made
                if feedback.get('improvements'):
                    improvements_text = "\\n".join([f"✅ {improvement}" for improvement in feedback['improvements']])
                    self.show_educational_content(
                        "🚀 Improvements You Made",
                        improvements_text,
                        "success"
                    )
                
                # Estimated performance improvement
                estimated_improvement = self._estimate_performance_gain(expected_solution_patterns, performance_context)
                if estimated_improvement:
                    improvement_panel = Panel(
                        Text.from_markup(
                            f"[bold green]📈 Estimated Performance Improvement[/bold green]\\n\\n"
                            f"{estimated_improvement}"
                        ),
                        border_style="green",
                        padding=(1, 2)
                    )
                    self.console.print(improvement_panel)
                
            else:
                # Show constructive feedback
                feedback_panel = Panel(
                    Text.from_markup(
                        f"[yellow]🤔 Not quite right yet, but you're learning![/yellow]\\n\\n"
                        f"[bold]What we're looking for:[/bold]\\n"
                        f"{feedback.get('missing_patterns', 'Please review the hints and try again.')}"
                    ),
                    border_style="yellow",
                    title="Feedback",
                    padding=(1, 2)
                )
                self.console.print(feedback_panel)
                
                # Offer additional hints after first attempt
                if attempts == 1 and len(expected_solution_patterns) > 0:
                    hint_text = f"💡 Try using: {expected_solution_patterns[0]}"
                    self.console.print(f"\\n[cyan]{hint_text}[/cyan]")
        
        # Challenge summary
        if not success:
            # Show the expected solution
            self.console.print(f"\\n[yellow]📚 Let's learn from the solution:[/yellow]")
            
            # Generate an example solution
            example_solution = self._generate_example_solution(problematic_code, expected_solution_patterns)
            
            self.show_educational_content(
                "📖 Example Solution",
                example_solution,
                "code", 
                "python"
            )
            
            # Explain the key concepts
            concept_explanation = self._explain_solution_concepts(expected_solution_patterns)
            if concept_explanation:
                self.show_educational_content(
                    "🧠 Key Concepts",
                    concept_explanation,
                    "explanation"
                )
        
        # Video tutorial placeholder for this specific challenge
        video_placeholder = Panel(
            Text.from_markup(
                f"[bold blue]📹 Video Tutorial Available[/bold blue]\\n\\n"
                f"Watch a detailed walkthrough of this challenge:\\n"
                f"[cyan]https://tutorials.djangomercury.com/challenges/{challenge_name.lower().replace(' ', '-')}[/cyan]\\n\\n"
                f"[italic]This video shows the complete solution with explanations of each optimization technique.[/italic]"
            ),
            border_style="blue",
            title="Video Resource",
            padding=(1, 2)
        )
        self.console.print(video_placeholder)
        
        return {
            'completed': success,
            'attempts': attempts,
            'challenge_name': challenge_name,
            'difficulty': difficulty,
            'success_rate': 100 if success else 0,
            'feedback': feedback,
            'estimated_improvement': estimated_improvement if success else None
        }

    def _run_text_code_challenge(
        self,
        challenge_name: str,
        problem_description: str,
        problematic_code: str,
        expected_solution_patterns: List[str]
    ) -> Dict[str, Any]:
        """Run code challenge in plain text mode."""
        print(f"\\n💻 CODE CHALLENGE: {challenge_name}")
        print("=" * 60)
        print(f"Problem: {problem_description}\\n")
        print("Current Code (Problematic):")
        print("-" * 40)
        print(problematic_code)
        print("-" * 40)
        print("\\nYour task: Optimize this code to fix the performance issue.")
        print("Enter your solution below, then type 'DONE' on a new line:")
        
        user_code_lines = []
        while True:
            try:
                line = input()
                if line.strip() == "DONE":
                    break
                user_code_lines.append(line)
            except (EOFError, KeyboardInterrupt):
                print("\\nChallenge cancelled.")
                return {'completed': False, 'reason': 'user_cancelled'}
        
        user_code = "\\n".join(user_code_lines)
        feedback = self._check_code_solution(user_code, expected_solution_patterns)
        
        if feedback['correct']:
            print("\\n✅ Excellent! Challenge completed!")
            print("\\nYour optimized code:")
            print(user_code)
        else:
            print("\\n📚 Here's what we were looking for:")
            example = self._generate_example_solution(problematic_code, expected_solution_patterns)
            print(example)
        
        return {
            'completed': feedback['correct'],
            'attempts': 1,
            'challenge_name': challenge_name
        }

    def _check_code_solution(self, user_code: str, expected_patterns: List[str]) -> Dict[str, Any]:
        """Check if user's code contains the expected optimization patterns."""
        user_code_lower = user_code.lower()
        found_patterns = []
        missing_patterns = []
        improvements = []
        
        # Pattern matching for common Django optimizations
        pattern_checks = {
            "select_related": {
                "patterns": ["select_related(", "select_related "],
                "improvement": "Using select_related() to eliminate N+1 queries on foreign keys"
            },
            "prefetch_related": {
                "patterns": ["prefetch_related(", "prefetch_related "],
                "improvement": "Using prefetch_related() to optimize many-to-many relationships"
            },
            "only": {
                "patterns": ["only(", ".only "],
                "improvement": "Using only() to limit fields and reduce memory usage"
            },
            "values": {
                "patterns": ["values(", ".values "],
                "improvement": "Using values() for lightweight data retrieval"
            },
            "values_list": {
                "patterns": ["values_list(", ".values_list "],
                "improvement": "Using values_list() for even more efficient data access"
            },
            "iterator": {
                "patterns": ["iterator(", ".iterator "],
                "improvement": "Using iterator() for memory-efficient processing of large datasets"
            },
            "bulk_create": {
                "patterns": ["bulk_create(", ".bulk_create "],
                "improvement": "Using bulk_create() for efficient batch insertion"
            },
            "annotate": {
                "patterns": ["annotate(", ".annotate "],
                "improvement": "Using annotate() to move calculations to the database"
            },
            "cache": {
                "patterns": ["cache.get", "cache.set", "@cache_page", "{% cache %}"],
                "improvement": "Implementing caching to reduce database load"
            }
        }
        
        for expected_pattern in expected_patterns:
            pattern_found = False
            
            # Check for exact pattern match first
            if expected_pattern.lower() in user_code_lower:
                found_patterns.append(expected_pattern)
                pattern_found = True
            else:
                # Check for related patterns
                for pattern_key, pattern_info in pattern_checks.items():
                    if expected_pattern.lower() in pattern_key or pattern_key in expected_pattern.lower():
                        for check_pattern in pattern_info["patterns"]:
                            if check_pattern in user_code_lower:
                                found_patterns.append(expected_pattern)
                                improvements.append(pattern_info["improvement"])
                                pattern_found = True
                                break
                    if pattern_found:
                        break
            
            if not pattern_found:
                missing_patterns.append(expected_pattern)
        
        # Determine if solution is correct
        correct = len(missing_patterns) == 0 or (len(found_patterns) >= len(expected_patterns) * 0.7)
        
        missing_feedback = ""
        if missing_patterns:
            missing_feedback = f"Missing optimizations: {', '.join(missing_patterns)}"
        
        return {
            'correct': correct,
            'found_patterns': found_patterns,
            'missing_patterns': missing_feedback,
            'improvements': improvements
        }

    def _generate_example_solution(self, original_code: str, patterns: List[str]) -> str:
        """Generate an example solution based on the expected patterns."""
        # This is a simplified approach - in a full implementation,
        # you'd have more sophisticated code transformation logic
        
        example_solutions = {
            "select_related": """# Optimized with select_related()
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No additional queries!""",
            
            "prefetch_related": """# Optimized with prefetch_related()
authors = Author.objects.prefetch_related('posts').all()
for author in authors:
    for post in author.posts.all():  # Efficient access
        print(post.title)""",
            
            "iterator": """# Optimized with iterator()
for user in User.objects.all().iterator(chunk_size=1000):
    process_user(user)  # Memory-efficient processing""",
            
            "only": """# Optimized with only()
users = User.objects.only('username', 'email').all()
# Only loads specified fields, reducing memory usage""",
            
            "annotate": """# Optimized with annotate()
authors = Author.objects.annotate(
    post_count=Count('posts')
).all()
# Calculation done in database, not Python"""
        }
        
        # Find the most relevant example
        for pattern in patterns:
            for key, example in example_solutions.items():
                if key in pattern.lower():
                    return example
        
        return f"""# Example optimization for the patterns: {', '.join(patterns)}
# The key is to reduce database queries and optimize data access
{original_code}

# Optimized version would use techniques like:
# - select_related() for foreign keys
# - prefetch_related() for many-to-many relationships
# - only() to limit fields
# - iterator() for large datasets"""

    def _explain_solution_concepts(self, patterns: List[str]) -> str:
        """Explain the key concepts behind the solution patterns."""
        concept_explanations = {
            "select_related": """**select_related()**: Performs SQL JOINs to fetch related objects in a single query. 
Perfect for ForeignKey and OneToOne relationships. Eliminates N+1 query problems.""",
            
            "prefetch_related": """**prefetch_related()**: Uses separate queries then joins data in Python. 
Best for ManyToMany and reverse ForeignKey relationships.""",
            
            "iterator": """**iterator()**: Processes results one at a time instead of loading everything into memory. 
Essential for large datasets to prevent memory issues.""",
            
            "only": """**only()**: Loads only specified fields from the database. 
Reduces memory usage and network overhead for large models.""",
            
            "annotate": """**annotate()**: Performs calculations at the database level using SQL functions. 
Much faster than calculating in Python, especially for aggregations.""",
            
            "cache": """**Caching**: Stores computed results to avoid repeated expensive operations. 
Can reduce database load by 90%+ for frequently accessed data."""
        }
        
        explanations = []
        for pattern in patterns:
            for key, explanation in concept_explanations.items():
                if key in pattern.lower():
                    explanations.append(explanation)
        
        return "\\n\\n".join(explanations) if explanations else "The key is optimizing database access and reducing computational overhead."

    def _estimate_performance_gain(self, patterns: List[str], context: Dict[str, Any]) -> str:
        """Estimate the performance improvement from the optimizations."""
        current_queries = context.get('query_count', 10)
        current_time = context.get('response_time', 500)
        
        # Estimate improvements based on patterns
        query_reduction = 1.0
        time_reduction = 1.0
        
        for pattern in patterns:
            if 'select_related' in pattern.lower():
                query_reduction *= 0.1  # 90% query reduction
                time_reduction *= 0.3   # 70% time reduction
            elif 'prefetch_related' in pattern.lower():
                query_reduction *= 0.2  # 80% query reduction  
                time_reduction *= 0.4   # 60% time reduction
            elif 'cache' in pattern.lower():
                time_reduction *= 0.1   # 90% time reduction
            elif 'iterator' in pattern.lower():
                # Mainly memory benefits, some time improvement
                time_reduction *= 0.8   # 20% time reduction
        
        estimated_queries = max(1, int(current_queries * query_reduction))
        estimated_time = max(10, int(current_time * time_reduction))
        
        return f"""**Before Optimization:**
• Database queries: {current_queries}
• Response time: {current_time}ms

**After Your Optimization:**
• Database queries: {estimated_queries} (reduced by {int((1-query_reduction)*100)}%)
• Response time: ~{estimated_time}ms (improved by {int((1-time_reduction)*100)}%)

🚀 **Impact**: Your changes could make this view {int(current_time/estimated_time)}x faster!"""

    def show_performance_comparison(
        self,
        before_metrics: Dict[str, Any],
        after_metrics: Dict[str, Any],
        optimization_name: str = "Optimization",
        show_grades: bool = True
    ) -> None:
        """
        Display a before/after performance comparison with visual indicators.
        
        Shows the impact of optimizations with clear visual feedback including
        metrics changes, grade improvements, and performance impact analysis.
        
        Args:
            before_metrics: Performance metrics before optimization
            after_metrics: Performance metrics after optimization  
            optimization_name: Name of the optimization applied
            show_grades: Whether to show letter grades
        """
        if not self.console or not RICH_AVAILABLE:
            self._show_text_performance_comparison(before_metrics, after_metrics, optimization_name)
            return
        
        # Create comparison table
        comparison_table = Table(
            title=f"📊 Performance Impact: {optimization_name}",
            show_header=True,
            header_style="bold cyan",
            title_style="bold cyan"
        )
        
        comparison_table.add_column("Metric", style="white", width=25)
        comparison_table.add_column("Before", style="red", justify="right", width=15)
        comparison_table.add_column("After", style="green", justify="right", width=15)  
        comparison_table.add_column("Improvement", style="bold green", justify="center", width=20)
        
        # Extract and compare key metrics
        metrics_to_compare = [
            ("Query Count", "query_count", "queries", False),
            ("Response Time", "response_time", "ms", False),
            ("Memory Usage", "memory_usage", "MB", False),
            ("Cache Hit Rate", "cache_hit_rate", "%", True),
        ]
        
        improvements = []
        
        for metric_name, metric_key, unit, higher_is_better in metrics_to_compare:
            before_val = before_metrics.get(metric_key, 0)
            after_val = after_metrics.get(metric_key, 0)
            
            if before_val == 0 and after_val == 0:
                continue  # Skip metrics that aren't available
                
            # Calculate improvement
            if before_val > 0:
                if higher_is_better:
                    improvement_pct = ((after_val - before_val) / before_val) * 100
                    improvement_direction = "↗️" if improvement_pct > 0 else ("↘️" if improvement_pct < 0 else "→")
                else:
                    improvement_pct = ((before_val - after_val) / before_val) * 100
                    improvement_direction = "↗️" if improvement_pct > 0 else ("↘️" if improvement_pct < 0 else "→")
                
                improvement_text = f"{improvement_direction} {abs(improvement_pct):.1f}%"
                improvements.append((metric_name, improvement_pct, higher_is_better))
            else:
                improvement_text = "N/A"
            
            # Format values
            before_display = f"{before_val:.1f} {unit}" if isinstance(before_val, (int, float)) else str(before_val)
            after_display = f"{after_val:.1f} {unit}" if isinstance(after_val, (int, float)) else str(after_val)
            
            comparison_table.add_row(
                metric_name,
                before_display,
                after_display,
                improvement_text
            )
        
        # Add overall scores if available
        if show_grades and 'score' in before_metrics and 'score' in after_metrics:
            before_score = before_metrics['score']
            after_score = after_metrics['score']
            before_grade = self._score_to_grade(before_score)
            after_grade = self._score_to_grade(after_score)
            
            score_improvement = after_score - before_score
            grade_improvement = "📈" if score_improvement > 0 else ("📉" if score_improvement < 0 else "📊")
            
            comparison_table.add_row(
                "Overall Score",
                f"{before_score:.1f} ({before_grade})",
                f"{after_score:.1f} ({after_grade})",
                f"{grade_improvement} {score_improvement:+.1f}"
            )
        
        self.console.print()
        self.console.print(comparison_table)
        
        # Show impact summary
        self._show_impact_summary(improvements, optimization_name)
        
        # Show visual performance bar chart
        self._show_performance_bars(before_metrics, after_metrics)
        
        # Show optimization recommendations if performance is still not optimal
        if after_metrics.get('score', 0) < 85:
            self._show_further_optimization_suggestions(after_metrics)

    def _show_text_performance_comparison(
        self,
        before_metrics: Dict[str, Any],
        after_metrics: Dict[str, Any],
        optimization_name: str
    ) -> None:
        """Show performance comparison in plain text."""
        print(f"\n📊 PERFORMANCE IMPACT: {optimization_name}")
        print("=" * 60)
        
        metrics = [
            ("Query Count", "query_count"),
            ("Response Time (ms)", "response_time"),
            ("Memory Usage (MB)", "memory_usage"),
        ]
        
        for metric_name, key in metrics:
            before = before_metrics.get(key, 0)
            after = after_metrics.get(key, 0)
            
            if before > 0:
                improvement = ((before - after) / before) * 100
                print(f"{metric_name:20} | {before:8.1f} → {after:8.1f} | {improvement:+5.1f}%")
        
        print("=" * 60)

    def _show_impact_summary(self, improvements: List[tuple], optimization_name: str) -> None:
        """Show a summary of the optimization impact."""
        if not improvements:
            return
            
        # Calculate overall impact
        significant_improvements = [imp for imp in improvements if abs(imp[1]) > 10]
        
        if significant_improvements:
            summary_text = []
            
            for metric_name, improvement_pct, higher_is_better in significant_improvements[:3]:  # Top 3
                if improvement_pct > 50:
                    impact = "🚀 Massive"
                elif improvement_pct > 25:
                    impact = "⚡ Significant"  
                elif improvement_pct > 10:
                    impact = "✅ Good"
                else:
                    impact = "📈 Modest"
                    
                summary_text.append(f"• {impact} {metric_name.lower()} improvement ({improvement_pct:.0f}%)")
            
            if summary_text:
                impact_panel = Panel(
                    Text.from_markup(
                        f"[bold green]🎯 Optimization Impact Summary[/bold green]\n\n" +
                        "\n".join(summary_text) +
                        f"\n\n[italic]Great work! Your {optimization_name.lower()} made a real difference.[/italic]"
                    ),
                    border_style="green",
                    padding=(1, 2)
                )
                self.console.print(impact_panel)

    def _show_performance_bars(
        self, 
        before_metrics: Dict[str, Any], 
        after_metrics: Dict[str, Any]
    ) -> None:
        """Show visual performance bars for key metrics."""
        if not self.console:
            return
            
        # Create visual bars for key metrics
        bar_metrics = [
            ("Response Time", "response_time", 1000, False),  # Lower is better, max 1000ms
            ("Query Count", "query_count", 50, False),        # Lower is better, max 50 queries
            ("Overall Score", "score", 100, True),            # Higher is better, max 100
        ]
        
        self.console.print("\n[bold]📊 Visual Performance Comparison[/bold]\n")
        
        for metric_name, key, max_val, higher_is_better in bar_metrics:
            before_val = before_metrics.get(key, 0)
            after_val = after_metrics.get(key, 0)
            
            if before_val == 0 and after_val == 0:
                continue
                
            # Calculate bar lengths (out of 30 characters)
            before_bar_len = min(30, int((before_val / max_val) * 30))
            after_bar_len = min(30, int((after_val / max_val) * 30))
            
            # Choose colors
            before_color = "green" if higher_is_better else "red"
            after_color = "green" if (higher_is_better and after_val >= before_val) or (not higher_is_better and after_val <= before_val) else "red"
            
            # Create bars
            before_bar = "█" * before_bar_len + "░" * (30 - before_bar_len)
            after_bar = "█" * after_bar_len + "░" * (30 - after_bar_len)
            
            self.console.print(f"[bold]{metric_name}[/bold]")
            self.console.print(f"  Before: [{before_color}]{before_bar}[/{before_color}] {before_val}")
            self.console.print(f"  After:  [{after_color}]{after_bar}[/{after_color}] {after_val}")
            self.console.print()

    def _show_further_optimization_suggestions(self, current_metrics: Dict[str, Any]) -> None:
        """Show suggestions for further optimization if performance is still suboptimal."""
        suggestions = []
        
        # Analyze current metrics for further improvement opportunities
        query_count = current_metrics.get('query_count', 0)
        response_time = current_metrics.get('response_time', 0)
        memory_usage = current_metrics.get('memory_usage', 0)
        cache_hit_rate = current_metrics.get('cache_hit_rate', 100)
        
        if query_count > 10:
            suggestions.append("🔍 Query count is still high - consider additional select_related() or prefetch_related() optimizations")
        
        if response_time > 200:
            suggestions.append("⚡ Response time could be faster - look into database indexing or caching strategies")
            
        if memory_usage > 50:
            suggestions.append("💾 Memory usage is elevated - consider using only() or values() for lighter queries")
            
        if cache_hit_rate < 80:
            suggestions.append("📦 Cache hit rate is low - review caching strategy and cache invalidation logic")
        
        if suggestions:
            suggestions_text = "\n".join(suggestions)
            suggestions_panel = Panel(
                Text.from_markup(
                    f"[bold yellow]🎯 Further Optimization Opportunities[/bold yellow]\n\n"
                    f"{suggestions_text}\n\n"
                    f"[italic]Keep optimizing! Every improvement makes your users happier.[/italic]"
                ),
                border_style="yellow",
                title="Next Steps",
                padding=(1, 2)
            )
            self.console.print(suggestions_panel)

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 97:
            return "S"
        elif score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "C+"
        elif score >= 65:
            return "C"
        elif score >= 60:
            return "D+"
        elif score >= 55:
            return "D"
        else:
            return "F"

    def show_optimization_timeline(
        self,
        optimization_history: List[Dict[str, Any]],
        title: str = "Optimization Journey"
    ) -> None:
        """
        Show a timeline of optimizations applied with cumulative performance impact.
        
        This helps users understand how each optimization contributed to the overall
        performance improvement and see their learning journey.
        
        Args:
            optimization_history: List of optimization steps with metrics
            title: Title for the timeline display
        """
        if not self.console or not RICH_AVAILABLE:
            self._show_text_optimization_timeline(optimization_history, title)
            return
            
        if not optimization_history:
            return
            
        # Timeline header
        timeline_panel = Panel(
            Text.from_markup(
                f"[bold cyan]📈 {title}[/bold cyan]\n\n"
                f"[yellow]Total Steps:[/yellow] {len(optimization_history)}\n"
                f"[italic]See how each optimization improved your application's performance![/italic]"
            ),
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(timeline_panel)
        
        # Create timeline table
        timeline_table = Table(
            show_header=True,
            header_style="bold cyan"
        )
        timeline_table.add_column("Step", style="cyan", width=5)
        timeline_table.add_column("Optimization", style="white", width=25)
        timeline_table.add_column("Query Count", style="yellow", justify="right", width=12)
        timeline_table.add_column("Response Time", style="blue", justify="right", width=15)
        timeline_table.add_column("Score", style="green", justify="right", width=8)
        timeline_table.add_column("Grade", style="bold green", justify="center", width=8)
        
        for i, step in enumerate(optimization_history, 1):
            metrics = step.get('metrics', {})
            optimization_name = step.get('name', f'Step {i}')
            
            query_count = metrics.get('query_count', 0)
            response_time = metrics.get('response_time', 0)
            score = metrics.get('score', 0)
            grade = self._score_to_grade(score)
            
            # Add visual indicators for improvements
            if i > 1:
                prev_metrics = optimization_history[i-2].get('metrics', {})
                query_indicator = "↓" if query_count < prev_metrics.get('query_count', 0) else ("↑" if query_count > prev_metrics.get('query_count', 0) else "→")
                time_indicator = "↓" if response_time < prev_metrics.get('response_time', 0) else ("↑" if response_time > prev_metrics.get('response_time', 0) else "→")
            else:
                query_indicator = ""
                time_indicator = ""
            
            timeline_table.add_row(
                str(i),
                optimization_name,
                f"{query_count} {query_indicator}",
                f"{response_time:.0f}ms {time_indicator}",
                f"{score:.1f}",
                grade
            )
        
        self.console.print(timeline_table)
        
        # Show overall improvement summary
        if len(optimization_history) >= 2:
            first_metrics = optimization_history[0].get('metrics', {})
            last_metrics = optimization_history[-1].get('metrics', {})
            
            self._show_journey_summary(first_metrics, last_metrics)

    def _show_text_optimization_timeline(
        self,
        optimization_history: List[Dict[str, Any]],
        title: str
    ) -> None:
        """Show optimization timeline in plain text."""
        print(f"\n📈 {title}")
        print("=" * 60)
        
        for i, step in enumerate(optimization_history, 1):
            metrics = step.get('metrics', {})
            name = step.get('name', f'Step {i}')
            score = metrics.get('score', 0)
            
            print(f"Step {i}: {name}")
            print(f"  Score: {score:.1f} ({self._score_to_grade(score)})")
            print(f"  Queries: {metrics.get('query_count', 0)}")
            print(f"  Time: {metrics.get('response_time', 0):.0f}ms")
            print()

    def _show_journey_summary(
        self, 
        first_metrics: Dict[str, Any], 
        last_metrics: Dict[str, Any]
    ) -> None:
        """Show overall journey improvement summary."""
        # Calculate total improvements
        query_improvement = 0
        time_improvement = 0
        score_improvement = 0
        
        if first_metrics.get('query_count', 0) > 0:
            query_improvement = ((first_metrics['query_count'] - last_metrics.get('query_count', 0)) / first_metrics['query_count']) * 100
        
        if first_metrics.get('response_time', 0) > 0:
            time_improvement = ((first_metrics['response_time'] - last_metrics.get('response_time', 0)) / first_metrics['response_time']) * 100
        
        score_improvement = last_metrics.get('score', 0) - first_metrics.get('score', 0)
        
        journey_text = []
        
        if query_improvement > 0:
            journey_text.append(f"🔍 Reduced queries by {query_improvement:.0f}%")
        if time_improvement > 0:
            journey_text.append(f"⚡ Improved response time by {time_improvement:.0f}%")
        if score_improvement > 0:
            journey_text.append(f"📈 Increased score by {score_improvement:.1f} points")
        
        if journey_text:
            first_grade = self._score_to_grade(first_metrics.get('score', 0))
            last_grade = self._score_to_grade(last_metrics.get('score', 0))
            
            journey_summary = Panel(
                Text.from_markup(
                    f"[bold green]🎉 Your Optimization Journey Results[/bold green]\n\n" +
                    "\n".join([f"• {improvement}" for improvement in journey_text]) +
                    f"\n\n[bold]Grade Improvement:[/bold] {first_grade} → {last_grade}\n\n"
                    f"[italic]Congratulations! You've significantly improved your application's performance.[/italic]"
                ),
                border_style="green",
                title="Journey Complete",
                padding=(1, 2)
            )
            self.console.print(journey_summary)
    
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