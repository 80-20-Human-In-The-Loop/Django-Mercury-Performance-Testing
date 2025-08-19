"""
Modern type-safe tutorial system definitions.

This module defines the core types for the learn-then-test tutorial architecture
using TypedDict for JSON compatibility and strict type checking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Literal, Union
from typing_extensions import NotRequired, TypedDict

if TYPE_CHECKING:
    pass

# Content slide types for different educational purposes
ContentSlideType = Literal["concept", "example", "code", "scenario", "comparison"]
DifficultyLevel = Literal["beginner", "intermediate", "advanced"]
QuestionType = Literal["multiple_choice", "true_false", "scenario"]


class ContentSlide(TypedDict):
    """A single educational content slide that teaches concepts."""

    type: ContentSlideType
    title: str
    content: List[str]  # Rich-formatted content lines (markdown-style)
    code_example: NotRequired[str]  # Optional code snippet with syntax highlighting
    visual_aids: NotRequired[List[str]]  # Emojis, diagrams, ASCII art
    key_takeaway: NotRequired[str]  # Summary point for the slide


class Answer(TypedDict):
    """A single answer option for a quiz question."""

    text: str
    is_correct: bool
    explanation: str  # Why this answer is right/wrong
    hint: NotRequired[str]  # Optional hint for learning


class Question(TypedDict):
    """A quiz question that tests understanding of concepts."""

    id: str
    question_type: QuestionType
    text: str  # The question text
    answers: List[Answer]  # All answer options (2-4 typically)
    explanation: str  # Overall explanation of the concept
    difficulty: DifficultyLevel
    concept: str  # What concept this tests
    tags: NotRequired[List[str]]  # Optional categorization tags


class LearningSection(TypedDict):
    """A learn-then-test section: 1-2 content slides followed by 1 question."""

    section_id: str
    concept: str  # Main concept being taught
    title: str  # Section title (e.g., "Understanding Cache Levels")
    content_slides: List[ContentSlide]  # 1-2 educational slides
    question: Question  # Quiz question testing this concept
    learning_objectives: NotRequired[List[str]]  # What users will learn


class FinalAssessment(TypedDict):
    """Final assessment with 2+ back-to-back questions."""

    title: str  # Assessment title
    description: str  # What this assessment covers
    questions: List[Question]  # 2+ questions testing overall understanding
    passing_threshold: float  # e.g., 0.7 for 70% to pass
    time_limit: NotRequired[int]  # Optional time limit in seconds


class Tutorial(TypedDict):
    """Complete tutorial with learn-then-test sections plus final assessment."""

    id: str
    title: str  # Tutorial title (e.g., "Django Caching Strategies")
    description: str  # What users will learn
    difficulty: DifficultyLevel
    concept: str  # Primary concept (e.g., "caching_strategies")
    tags: List[str]  # Categorization tags

    # Main tutorial content
    learning_sections: List[LearningSection]  # Learn-then-test sections
    final_assessment: FinalAssessment  # Comprehensive assessment

    # Metadata
    estimated_time: NotRequired[int]  # Estimated completion time in minutes
    prerequisites: NotRequired[List[str]]  # Required prior knowledge
    next_topics: NotRequired[List[str]]  # Suggested follow-up topics
    version: NotRequired[str]  # Content version for updates


# Runtime validation helpers
class TutorialValidationError(Exception):
    """Raised when tutorial structure is invalid."""

    pass


def validate_tutorial(tutorial: Tutorial) -> None:
    """Validate tutorial structure for common issues."""

    # Check required fields
    if not tutorial.get("learning_sections"):
        raise TutorialValidationError("Tutorial must have at least one learning section")

    if not tutorial.get("final_assessment", {}).get("questions"):
        raise TutorialValidationError("Tutorial must have final assessment questions")

    # Validate each learning section
    for i, section in enumerate(tutorial["learning_sections"]):
        if not section.get("content_slides"):
            raise TutorialValidationError(f"Section {i} must have content slides")

        if len(section["content_slides"]) > 3:
            raise TutorialValidationError(f"Section {i} has too many slides (max 3)")

        # Validate question structure
        question = section.get("question")
        if not question:
            raise TutorialValidationError(f"Section {i} must have a question")

        answers = question.get("answers", [])
        if len(answers) < 2:
            raise TutorialValidationError(f"Section {i} question must have at least 2 answers")

        correct_answers = [a for a in answers if a.get("is_correct")]
        if len(correct_answers) != 1:
            raise TutorialValidationError(
                f"Section {i} question must have exactly 1 correct answer"
            )

    # Validate final assessment
    final_questions = tutorial["final_assessment"].get("questions", [])
    if len(final_questions) < 2:
        raise TutorialValidationError("Final assessment must have at least 2 questions")


# Type aliases for common patterns
TutorialContent = Union[ContentSlide, Question, LearningSection]
TutorialMetadata = dict[str, Any]
