#!/usr/bin/env python
"""
Demo script for Django Mercury Educational Mode

This script demonstrates how the educational mode works with:
1. Interactive quiz questions
2. Performance issue detection 
3. Educational explanations
4. Non-interactive fallback

Run this in different modes:
- Interactive terminal: python demo_educational_mode.py
- Non-interactive: python demo_educational_mode.py < /dev/null
- Force non-interactive: MERCURY_NON_INTERACTIVE=1 python demo_educational_mode.py
"""

import os
import sys
import time

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_interactive_features():
    """Demonstrate the educational mode features."""
    
    print("=" * 70)
    print("Django Mercury Educational Mode Demo")
    print("=" * 70)
    print()
    
    # Set up educational environment
    os.environ['MERCURY_EDUCATIONAL_MODE'] = 'true'
    os.environ['MERCURY_EDU_LEVEL'] = 'beginner'
    
    # Import components
    from django_mercury.cli.educational.quiz_system import QuizSystem
    from django_mercury.cli.educational.interactive_ui import InteractiveUI
    from django_mercury.cli.educational.utils import is_interactive_environment
    from django_mercury.python_bindings.educational_monitor import EducationalMonitor
    
    # Check environment
    is_interactive = is_interactive_environment()
    print(f"📍 Running in {'INTERACTIVE' if is_interactive else 'NON-INTERACTIVE'} mode")
    print()
    
    if not is_interactive:
        print("ℹ️  Non-interactive mode detected. Educational content will be shown")
        print("   without pausing for user input.")
        print()
        print("   To run in interactive mode:")
        print("   - Run in a terminal: python demo_educational_mode.py")
        print("   - Or use: python -u demo_educational_mode.py")
    else:
        print("✅ Interactive mode active! You'll be asked questions and can")
        print("   interact with the educational content.")
    print()
    
    # Initialize components
    try:
        from rich.console import Console
        console = Console()
        ui = InteractiveUI(console=console)
        print("✅ Rich console initialized - enhanced display enabled")
    except ImportError:
        console = None
        ui = InteractiveUI()
        print("ℹ️  Rich not installed - using text-only display")
    
    quiz_system = QuizSystem(console=console, level="beginner")
    monitor = EducationalMonitor(
        console=console,
        quiz_system=quiz_system,
        interactive_mode=True
    )
    
    print("\n" + "-" * 70)
    print("DEMO 1: Performance Issue Detection")
    print("-" * 70)
    print("\nSimulating a test that detects an N+1 query problem...")
    time.sleep(1)
    
    # Simulate a performance issue
    ui.show_performance_issue(
        test_name="test_user_list_api",
        issue_type="n_plus_one_queries",
        metrics={
            "query_count": 156,
            "expected_max": 10,
            "response_time_ms": 750,
            "queries_per_item": 1.5
        },
        severity="error"
    )
    
    print("\n" + "-" * 70)
    print("DEMO 2: Interactive Quiz")
    print("-" * 70)
    print("\nNow let's test your understanding with a quiz...")
    time.sleep(1)
    
    # Run an interactive quiz
    result = quiz_system.ask_quiz_for_concept("n+1_queries")
    
    if result['answered']:
        print(f"\n📊 Quiz Result: {'✅ Correct!' if result['correct'] else '❌ Incorrect'}")
        if result['wants_to_learn']:
            print("📚 Showing additional learning resources...")
    else:
        print("\n⏭️  Quiz was skipped or not available")
    
    print("\n" + "-" * 70)
    print("DEMO 3: Full Educational Flow")
    print("-" * 70)
    print("\nSimulating a complete educational intervention...")
    time.sleep(1)
    
    # Run the full educational monitor flow
    error_msg = "Performance threshold exceeded: Query count 230 exceeds limit 10"
    monitor.handle_performance_issue("test_product_search", error_msg)
    
    print("\n" + "-" * 70)
    print("DEMO 4: Different Issue Types")
    print("-" * 70)
    
    # Show different types of issues
    issues = [
        ("Slow response time", "Performance threshold exceeded: Response time 450ms exceeds limit 200ms"),
        ("Memory usage", "Performance threshold exceeded: Memory usage 75MB exceeds limit 50MB"),
        ("Cache misses", "Performance threshold exceeded: Cache hit ratio 0.3 below minimum 0.7"),
    ]
    
    for issue_name, error in issues:
        print(f"\n📍 {issue_name}:")
        print(f"   Error: {error}")
        # In non-interactive mode, just show what would happen
        if not is_interactive:
            issue_type = monitor._detect_issue_type(error)
            print(f"   Detected type: {issue_type}")
            print(f"   Educational content would be shown for: {issue_type}")
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("📚 What you've seen:")
    print("✅ Performance issue detection and display")
    print("✅ Interactive quizzes (in interactive mode)")
    print("✅ Educational explanations")
    print("✅ Graceful non-interactive fallback")
    print()
    
    if is_interactive:
        print("🎯 Try running with MERCURY_NON_INTERACTIVE=1 to see non-interactive mode")
    else:
        print("🎯 Try running in a terminal to experience interactive mode")
    
    print("\n💡 To use in your Django tests:")
    print("   1. Add to settings.py:")
    print("      if '--edu' in sys.argv:")
    print("          TEST_RUNNER = 'django_mercury.test_runner.EducationalTestRunner'")
    print("   2. Run tests: python manage.py test --edu")
    print()

if __name__ == "__main__":
    try:
        demo_interactive_features()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)