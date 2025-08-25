"""Django Mercury Learn Plugin.

A comprehensive learning system with slideshow-style quizzes, progress tracking,
and adaptive content delivery. This plugin transforms performance testing into
an educational experience following the 80-20 Human-in-the-Loop philosophy.

Features:
- 🎪 Slideshow-style quiz interface with rich terminal UI
- 📊 Progress tracking across learning sessions
- 🎯 Contextual quizzes based on actual test performance
- 🧠 Adaptive difficulty and personalized recommendations
- 📚 Extensive content library for Django performance optimization

Usage:
    mercury-test --learn                    # Interactive topic selection
    mercury-test --learn n+1-queries        # Specific topic
    mercury-test --learn --quiz             # Quick quiz mode
    mercury-test --learn --progress         # Show learning progress
"""

from .plugin import LearnPlugin
from .models import Quiz, Question, UserProgress
from .ui import SlideShow, QuizInterface, ProgressDisplay

__all__ = [
    "LearnPlugin",
    "Quiz",
    "Question",
    "UserProgress",
    "SlideShow",
    "QuizInterface",
    "ProgressDisplay",
]

__version__ = "1.0.0"
__author__ = "Django Mercury Team"
