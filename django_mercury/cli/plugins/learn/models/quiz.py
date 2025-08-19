"""Quiz and Question models for the Learn plugin.

These models represent quiz questions, answers, and quiz collections
with support for different question types, difficulty levels, and
contextual content generation.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid


class QuestionType(Enum):
    """Types of quiz questions supported."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    CONTEXTUAL = "contextual"  # Generated from test results
    CODE_REVIEW = "code_review"
    SCENARIO = "scenario"


class DifficultyLevel(Enum):
    """Difficulty levels for content adaptation."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class Answer:
    """Represents a single answer option."""

    text: str
    is_correct: bool = False
    explanation: Optional[str] = None
    hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "is_correct": self.is_correct,
            "explanation": self.explanation,
            "hint": self.hint,
        }


@dataclass
class Question:
    """Represents a single quiz question."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    text: str = ""
    answers: List[Answer] = field(default_factory=list)
    explanation: str = ""
    hints: List[str] = field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    concept: str = ""  # e.g., "n_plus_one_queries"
    tags: List[str] = field(default_factory=list)
    time_limit: Optional[int] = None  # seconds

    # Context for dynamic questions
    context_data: Dict[str, Any] = field(default_factory=dict)

    def get_correct_answers(self) -> List[Answer]:
        """Get all correct answers."""
        return [answer for answer in self.answers if answer.is_correct]

    def get_correct_indices(self) -> List[int]:
        """Get indices of correct answers (0-based)."""
        return [i for i, answer in enumerate(self.answers) if answer.is_correct]

    def is_correct_answer(self, answer_index: int) -> bool:
        """Check if given answer index is correct."""
        if 0 <= answer_index < len(self.answers):
            return self.answers[answer_index].is_correct
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "question_type": self.question_type.value,
            "text": self.text,
            "answers": [answer.to_dict() for answer in self.answers],
            "explanation": self.explanation,
            "hints": self.hints,
            "difficulty": self.difficulty.value,
            "concept": self.concept,
            "tags": self.tags,
            "time_limit": self.time_limit,
            "context_data": self.context_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        """Create Question from dictionary."""
        answers = [
            Answer(
                text=ans.get("text", ""),
                is_correct=ans.get("is_correct", False),
                explanation=ans.get("explanation"),
                hint=ans.get("hint"),
            )
            for ans in data.get("answers", [])
        ]

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            question_type=QuestionType(data.get("question_type", "multiple_choice")),
            text=data.get("text", ""),
            answers=answers,
            explanation=data.get("explanation", ""),
            hints=data.get("hints", []),
            difficulty=DifficultyLevel(data.get("difficulty", "beginner")),
            concept=data.get("concept", ""),
            tags=data.get("tags", []),
            time_limit=data.get("time_limit"),
            context_data=data.get("context_data", {}),
        )


@dataclass
class Quiz:
    """Represents a collection of questions on a topic."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    questions: List[Question] = field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    concept: str = ""  # Primary concept being tested
    tags: List[str] = field(default_factory=list)
    time_limit: Optional[int] = None  # Total time limit in seconds
    passing_score: float = 0.7  # 70% to pass
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_total_questions(self) -> int:
        """Get total number of questions."""
        return len(self.questions)

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get question by ID."""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def calculate_score(self, answers: Dict[str, int]) -> Dict[str, Any]:
        """Calculate quiz score based on user answers.

        Args:
            answers: Dict mapping question_id to answer_index

        Returns:
            Dict with score, percentage, passed status, and details
        """
        total_questions = len(self.questions)
        if total_questions == 0:
            return {"score": 0, "total": 0, "percentage": 0.0, "passed": False, "details": []}

        correct_answers = 0
        details = []

        for question in self.questions:
            user_answer = answers.get(question.id, -1)
            is_correct = question.is_correct_answer(user_answer)

            if is_correct:
                correct_answers += 1

            details.append(
                {
                    "question_id": question.id,
                    "question": question.text,
                    "user_answer": user_answer,
                    "correct_answers": question.get_correct_indices(),
                    "is_correct": is_correct,
                    "explanation": question.explanation,
                }
            )

        percentage = (correct_answers / total_questions) * 100
        passed = percentage >= (self.passing_score * 100)

        return {
            "score": correct_answers,
            "total": total_questions,
            "percentage": percentage,
            "passed": passed,
            "details": details,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "questions": [q.to_dict() for q in self.questions],
            "difficulty": self.difficulty.value,
            "concept": self.concept,
            "tags": self.tags,
            "time_limit": self.time_limit,
            "passing_score": self.passing_score,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quiz":
        """Create Quiz from dictionary."""
        questions = [Question.from_dict(q) for q in data.get("questions", [])]

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            questions=questions,
            difficulty=DifficultyLevel(data.get("difficulty", "beginner")),
            concept=data.get("concept", ""),
            tags=data.get("tags", []),
            time_limit=data.get("time_limit"),
            passing_score=data.get("passing_score", 0.7),
            metadata=data.get("metadata", {}),
        )
