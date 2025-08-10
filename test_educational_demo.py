#!/usr/bin/env python
"""
Simple test script to demonstrate educational mode functionality.
"""

import os
import sys

# Set up educational mode environment
os.environ['MERCURY_EDUCATIONAL_MODE'] = 'true'
os.environ['MERCURY_EDU_LEVEL'] = 'beginner'

# Import educational components
from django_mercury.cli.educational.quiz_system import QuizSystem
from django_mercury.cli.educational.interactive_ui import InteractiveUI
from django_mercury.python_bindings.educational_monitor import EducationalMonitor

def test_educational_features():
    """Test that educational features work correctly."""
    
    print("=== Testing Django Mercury Educational Mode ===\n")
    
    # Initialize components
    try:
        from rich.console import Console
        console = Console()
        print("✅ Rich console available - full interactive features enabled")
    except ImportError:
        console = None
        print("⚠️  Rich not available - using fallback text mode")
    
    ui = InteractiveUI(console=console)
    quiz_system = QuizSystem(console=console, level="beginner")
    monitor = EducationalMonitor(
        console=console,
        quiz_system=quiz_system,
        interactive_mode=True
    )
    
    print("\n1. Testing UI display of performance issue...")
    ui.show_performance_issue(
        test_name="test_user_list_view",
        issue_type="n_plus_one_queries",
        metrics={
            "query_count": 150,
            "expected_max": 10,
            "response_time_ms": 850
        },
        severity="error"
    )
    
    print("\n2. Testing quiz system...")
    print("This should ask you an interactive question about N+1 queries:")
    result = quiz_system.ask_quiz_for_concept("n_plus_one_queries")
    
    print(f"\nQuiz result: {result}")
    
    print("\n3. Testing educational monitor...")
    print("This simulates what happens when a test fails with a performance issue:")
    monitor.handle_performance_issue(
        test="test_api_endpoint",
        error_msg="Performance threshold exceeded: Query count 230 exceeds limit 10"
    )
    
    print("\n=== Educational Mode Test Complete ===")
    print("\nIf you saw:")
    print("✅ Performance issue display")
    print("✅ Interactive quiz question")
    print("✅ User input prompts")
    print("✅ Educational explanations")
    print("\nThen educational mode is working correctly!")

if __name__ == "__main__":
    test_educational_features()