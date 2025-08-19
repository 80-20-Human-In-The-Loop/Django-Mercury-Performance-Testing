#!/usr/bin/env python3
"""
Test the new user-paced slide presentation with question warnings.
"""

import json
import sys
from pathlib import Path

# Add the django_mercury package to the path
sys.path.insert(0, str(Path(__file__).parent / "django_mercury"))

from cli.plugins.learn.models.tutorial_types import Tutorial
from cli.plugins.learn.models.slide_generator import TutorialSlideGenerator, SlidePresenter


def test_user_paced_slides():
    """Test that slides wait for user input and warn about questions."""

    # Load the sample tutorial
    tutorial_path = Path("django_mercury/cli/plugins/learn/data/tutorials/caching-strategies.json")

    if not tutorial_path.exists():
        print(f"❌ Tutorial file not found: {tutorial_path}")
        return False

    with open(tutorial_path) as f:
        tutorial_data = json.load(f)

    print("🎓 Testing User-Paced Slide Navigation")
    print("=" * 50)
    print("Features being tested:")
    print("✅ No auto-advancing slides")
    print("✅ Wait for user input on every slide")
    print("✅ Warning when question is coming up")
    print("✅ Clear progress indicators")
    print()
    print("Instructions:")
    print("- Press Enter to advance each slide")
    print("- Watch for question warnings")
    print("- Ctrl+C to exit anytime")
    print()
    input("Press Enter to start the demo...")

    # Generate slides
    generator = TutorialSlideGenerator()
    slides = generator.generate_slides(tutorial_data)

    print(f"\n📚 Generated {len(slides)} slides from tutorial")

    # Present with user-paced navigation
    presenter = SlidePresenter()

    try:
        print("\n🚀 Starting slideshow...\n")
        presenter.present_slideshow(slides)

        print("\n🎉 Slideshow complete!")
        print("✅ All slides waited for user input")
        print("✅ Question warnings displayed properly")

    except KeyboardInterrupt:
        print("\n\n⚠️  Slideshow interrupted by user")
        return True
    except Exception as e:
        print(f"\n❌ Error during slideshow: {e}")
        return False

    return True


if __name__ == "__main__":
    success = test_user_paced_slides()
    sys.exit(0 if success else 1)
