#!/usr/bin/env python
"""
Test interactive educational mode with simulated inputs.
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Set up educational mode environment
os.environ['MERCURY_EDUCATIONAL_MODE'] = 'true'
os.environ['MERCURY_EDU_LEVEL'] = 'beginner'

def test_with_mocked_input():
    """Test educational mode with mocked interactive inputs."""
    
    # Import after setting environment
    from django_mercury.cli.educational.quiz_system import QuizSystem
    from django_mercury.python_bindings.educational_monitor import EducationalMonitor
    
    print("=== Testing Interactive Educational Mode ===\n")
    
    # Mock rich components for controlled testing
    with patch('rich.prompt.IntPrompt') as mock_prompt, \
         patch('rich.prompt.Confirm') as mock_confirm:
        
        # Set up mock responses
        mock_prompt.ask.return_value = 2  # Answer "2" to quiz question
        mock_confirm.ask.return_value = True  # Want to learn more / Ready to continue
        
        # Create console and quiz system
        from rich.console import Console
        console = Console()
        quiz_system = QuizSystem(console=console, level="beginner")
        
        print("1. Testing quiz interaction:")
        print("-" * 40)
        
        # Get a quiz about N+1 queries
        quiz = quiz_system.get_quiz_for_concept("n+1_queries")
        if quiz:
            print(f"Question: {quiz.question}")
            print("\nOptions:")
            for i, option in enumerate(quiz.options, 1):
                print(f"  {i}) {option}")
            
            print("\n[Simulated answer: 2]")
            
            # Check if answer is correct
            is_correct = (2 - 1) == quiz.correct_answer
            print(f"Result: {'✅ Correct!' if is_correct else '❌ Incorrect'}")
            print(f"\n💡 Explanation: {quiz.explanation}")
        
        print("\n2. Testing full educational monitor flow:")
        print("-" * 40)
        
        monitor = EducationalMonitor(
            console=console,
            quiz_system=quiz_system,
            interactive_mode=True
        )
        
        # Simulate a performance issue
        error_msg = "Performance threshold exceeded: Query count 150 exceeds limit 10"
        
        print(f"Simulated error: {error_msg}")
        print("\nEducational monitor will now:")
        print("1. Detect this is an N+1 query issue")
        print("2. Show educational content")
        print("3. Ask a quiz question")
        print("4. Ask if you want to learn more")
        print("5. Ask if ready to continue")
        
        # Call the handler
        monitor.handle_performance_issue("test_example", error_msg)
        
        # Check what was called
        print("\n3. Verification of interactive calls:")
        print("-" * 40)
        if mock_prompt.ask.called:
            print("✅ Quiz question was asked interactively")
        else:
            print("❌ Quiz question was NOT asked")
            
        if mock_confirm.ask.called:
            print(f"✅ User was asked confirmation questions ({mock_confirm.ask.call_count} times)")
        else:
            print("❌ User was NOT asked confirmation questions")
    
    print("\n=== Test Complete ===")
    print("\nEducational mode is INTERACTIVE if both checkmarks (✅) appear above.")

if __name__ == "__main__":
    test_with_mocked_input()