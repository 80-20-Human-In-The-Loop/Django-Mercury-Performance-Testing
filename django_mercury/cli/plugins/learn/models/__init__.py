"""Data models for the Learn plugin.

This module contains the core data structures for quizzes, questions,
user progress, and learning content.
"""

from .quiz import Quiz, Question, Answer
from .progress import UserProgress, LearningSession
from .content import LearningContent, ContentMetadata
from .tutorial_types import Tutorial, LearningSection, ContentSlide, Question as TutorialQuestion
from .slide_generator import TutorialSlideGenerator
from .interactive_quiz import InteractiveQuizHandler

__all__ = [
    "Quiz",
    "Question",
    "Answer",
    "UserProgress",
    "LearningSession",
    "LearningContent",
    "ContentMetadata",
    "Tutorial",
    "LearningSection",
    "ContentSlide",
    "TutorialQuestion",
    "TutorialSlideGenerator",
    "InteractiveQuizHandler",
]
