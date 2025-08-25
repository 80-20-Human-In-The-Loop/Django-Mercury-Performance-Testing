"""User progress tracking models for the Learn plugin.

These models track user learning progress, quiz results, and provide
analytics for personalized learning recommendations.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os
from pathlib import Path


class ProficiencyLevel(Enum):
    """User proficiency levels for different concepts."""

    UNKNOWN = "unknown"
    LEARNING = "learning"  # 0-59%
    DEVELOPING = "developing"  # 60-79%
    PROFICIENT = "proficient"  # 80-89%
    MASTERED = "mastered"  # 90%+


@dataclass
class QuizResult:
    """Individual quiz result record."""

    quiz_id: str
    score: int
    total_questions: int
    percentage: float
    time_taken: int  # seconds
    timestamp: datetime
    concept: str
    difficulty: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Whether the quiz was passed (70% or higher)."""
        return self.percentage >= 70.0

    @property
    def proficiency_level(self) -> ProficiencyLevel:
        """Get proficiency level based on percentage."""
        if self.percentage >= 90:
            return ProficiencyLevel.MASTERED
        elif self.percentage >= 80:
            return ProficiencyLevel.PROFICIENT
        elif self.percentage >= 60:
            return ProficiencyLevel.DEVELOPING
        else:
            return ProficiencyLevel.LEARNING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "quiz_id": self.quiz_id,
            "score": self.score,
            "total_questions": self.total_questions,
            "percentage": self.percentage,
            "time_taken": self.time_taken,
            "timestamp": self.timestamp.isoformat(),
            "concept": self.concept,
            "difficulty": self.difficulty,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuizResult":
        """Create QuizResult from dictionary."""
        return cls(
            quiz_id=data["quiz_id"],
            score=data["score"],
            total_questions=data["total_questions"],
            percentage=data["percentage"],
            time_taken=data["time_taken"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            concept=data["concept"],
            difficulty=data["difficulty"],
            details=data.get("details", {}),
        )


@dataclass
class ConceptProgress:
    """Progress tracking for a specific concept."""

    concept: str
    attempts: int = 0
    best_score: float = 0.0
    latest_score: float = 0.0
    average_score: float = 0.0
    total_time_spent: int = 0  # seconds
    last_practiced: Optional[datetime] = None
    proficiency_level: ProficiencyLevel = ProficiencyLevel.UNKNOWN
    quiz_results: List[QuizResult] = field(default_factory=list)

    def add_quiz_result(self, result: QuizResult) -> None:
        """Add a new quiz result and update progress."""
        self.quiz_results.append(result)
        self.attempts += 1
        self.latest_score = result.percentage
        self.total_time_spent += result.time_taken
        self.last_practiced = result.timestamp

        # Update best score
        if result.percentage > self.best_score:
            self.best_score = result.percentage

        # Recalculate average
        total_score = sum(r.percentage for r in self.quiz_results)
        self.average_score = total_score / len(self.quiz_results)

        # Update proficiency level based on recent performance
        recent_scores = [r.percentage for r in self.quiz_results[-3:]]  # Last 3 attempts
        recent_average = sum(recent_scores) / len(recent_scores)

        if recent_average >= 90:
            self.proficiency_level = ProficiencyLevel.MASTERED
        elif recent_average >= 80:
            self.proficiency_level = ProficiencyLevel.PROFICIENT
        elif recent_average >= 60:
            self.proficiency_level = ProficiencyLevel.DEVELOPING
        else:
            self.proficiency_level = ProficiencyLevel.LEARNING

    def get_improvement_trend(self) -> str:
        """Get trend direction (improving, stable, declining)."""
        if len(self.quiz_results) < 2:
            return "insufficient_data"

        recent = self.quiz_results[-3:]  # Last 3 attempts
        if len(recent) < 2:
            return "insufficient_data"

        first_avg = sum(r.percentage for r in recent[: len(recent) // 2]) / (len(recent) // 2)
        second_avg = sum(r.percentage for r in recent[len(recent) // 2 :]) / (
            len(recent) - len(recent) // 2
        )

        if second_avg > first_avg + 5:
            return "improving"
        elif second_avg < first_avg - 5:
            return "declining"
        else:
            return "stable"

    def needs_practice(self) -> bool:
        """Whether this concept needs more practice."""
        if self.proficiency_level in [ProficiencyLevel.UNKNOWN, ProficiencyLevel.LEARNING]:
            return True

        # Check if it's been a while since last practice
        if self.last_practiced:
            days_since = (datetime.now() - self.last_practiced).days
            if days_since > 14:  # 2 weeks
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "concept": self.concept,
            "attempts": self.attempts,
            "best_score": self.best_score,
            "latest_score": self.latest_score,
            "average_score": self.average_score,
            "total_time_spent": self.total_time_spent,
            "last_practiced": self.last_practiced.isoformat() if self.last_practiced else None,
            "proficiency_level": self.proficiency_level.value,
            "quiz_results": [r.to_dict() for r in self.quiz_results],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConceptProgress":
        """Create ConceptProgress from dictionary."""
        quiz_results = [QuizResult.from_dict(r) for r in data.get("quiz_results", [])]
        last_practiced = None
        if data.get("last_practiced"):
            last_practiced = datetime.fromisoformat(data["last_practiced"])

        return cls(
            concept=data["concept"],
            attempts=data.get("attempts", 0),
            best_score=data.get("best_score", 0.0),
            latest_score=data.get("latest_score", 0.0),
            average_score=data.get("average_score", 0.0),
            total_time_spent=data.get("total_time_spent", 0),
            last_practiced=last_practiced,
            proficiency_level=ProficiencyLevel(data.get("proficiency_level", "unknown")),
            quiz_results=quiz_results,
        )


@dataclass
class LearningSession:
    """Individual learning session record."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    quizzes_taken: List[str] = field(default_factory=list)
    concepts_practiced: List[str] = field(default_factory=list)
    total_questions: int = 0
    correct_answers: int = 0
    session_type: str = "mixed"  # quiz, learn, practice

    @property
    def duration(self) -> timedelta:
        """Get session duration."""
        end = self.end_time or datetime.now()
        return end - self.start_time

    @property
    def accuracy(self) -> float:
        """Get session accuracy percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100


class UserProgress:
    """Persistent user progress tracking across learning sessions."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.concept_progress: Dict[str, ConceptProgress] = {}
        self.learning_sessions: List[LearningSession] = []
        self.preferences: Dict[str, Any] = {
            "difficulty_preference": "adaptive",
            "session_length": "medium",
            "reminder_frequency": "weekly",
        }
        self.total_time_spent = 0
        self.total_quizzes_taken = 0
        self.total_concepts_learned = 0
        self.achievement_unlocked: List[str] = []

        # Load existing progress
        self.load_progress()

    def get_progress_file_path(self) -> Path:
        """Get path to user progress file."""
        # Store in user's home directory under .mercury/progress/
        home_dir = Path.home()
        progress_dir = home_dir / ".mercury" / "progress"
        progress_dir.mkdir(parents=True, exist_ok=True)
        return progress_dir / f"{self.user_id}_progress.json"

    def load_progress(self) -> None:
        """Load user progress from disk."""
        progress_file = self.get_progress_file_path()

        if not progress_file.exists():
            return

        try:
            with open(progress_file, "r") as f:
                data = json.load(f)

            # Load concept progress
            for concept, progress_data in data.get("concept_progress", {}).items():
                self.concept_progress[concept] = ConceptProgress.from_dict(progress_data)

            # Load other data
            self.preferences = data.get("preferences", self.preferences)
            self.total_time_spent = data.get("total_time_spent", 0)
            self.total_quizzes_taken = data.get("total_quizzes_taken", 0)
            self.total_concepts_learned = data.get("total_concepts_learned", 0)
            self.achievement_unlocked = data.get("achievement_unlocked", [])

        except (json.JSONDecodeError, KeyError) as e:
            # If there's an error loading, start fresh
            print(f"Warning: Could not load progress file: {e}")

    def save_progress(self) -> None:
        """Save user progress to disk."""
        progress_file = self.get_progress_file_path()

        data = {
            "user_id": self.user_id,
            "concept_progress": {
                concept: progress.to_dict() for concept, progress in self.concept_progress.items()
            },
            "preferences": self.preferences,
            "total_time_spent": self.total_time_spent,
            "total_quizzes_taken": self.total_quizzes_taken,
            "total_concepts_learned": self.total_concepts_learned,
            "achievement_unlocked": self.achievement_unlocked,
            "last_updated": datetime.now().isoformat(),
        }

        try:
            with open(progress_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save progress: {e}")

    def record_quiz_result(self, result: QuizResult) -> None:
        """Record a new quiz result and update progress."""
        # Get or create concept progress
        if result.concept not in self.concept_progress:
            self.concept_progress[result.concept] = ConceptProgress(concept=result.concept)

        # Add the result
        self.concept_progress[result.concept].add_quiz_result(result)

        # Update totals
        self.total_quizzes_taken += 1
        self.total_time_spent += result.time_taken

        # Check for new achievements
        self._check_achievements(result)

        # Save progress
        self.save_progress()

    def get_concept_progress(self, concept: str) -> ConceptProgress:
        """Get progress for a specific concept."""
        if concept not in self.concept_progress:
            self.concept_progress[concept] = ConceptProgress(concept=concept)
        return self.concept_progress[concept]

    def get_overall_progress(self) -> Dict[str, Any]:
        """Get overall learning progress summary."""
        total_concepts = len(self.concept_progress)
        mastered_concepts = sum(
            1
            for p in self.concept_progress.values()
            if p.proficiency_level == ProficiencyLevel.MASTERED
        )

        if total_concepts == 0:
            completion_rate = 0.0
        else:
            completion_rate = (mastered_concepts / total_concepts) * 100

        return {
            "total_concepts_studied": total_concepts,
            "mastered_concepts": mastered_concepts,
            "completion_rate": completion_rate,
            "total_time_spent": self.total_time_spent,
            "total_quizzes_taken": self.total_quizzes_taken,
            "achievements": len(self.achievement_unlocked),
        }

    def get_recommended_concepts(self) -> List[str]:
        """Get concepts that need practice or are new."""
        needs_practice = []

        for concept, progress in self.concept_progress.items():
            if progress.needs_practice():
                needs_practice.append(concept)

        return needs_practice[:5]  # Top 5 recommendations

    def _check_achievements(self, result: QuizResult) -> None:
        """Check and unlock new achievements."""
        achievements = []

        # First quiz achievement
        if self.total_quizzes_taken == 1:
            achievements.append("first_quiz")

        # Perfect score achievement
        if result.percentage == 100 and "perfect_score" not in self.achievement_unlocked:
            achievements.append("perfect_score")

        # Speed demon (fast completion)
        if result.time_taken <= 30 and "speed_demon" not in self.achievement_unlocked:
            achievements.append("speed_demon")

        # Concept master
        concept_progress = self.concept_progress[result.concept]
        if (
            concept_progress.proficiency_level == ProficiencyLevel.MASTERED
            and f"master_{result.concept}" not in self.achievement_unlocked
        ):
            achievements.append(f"master_{result.concept}")

        # Quiz milestone achievements
        milestones = [10, 25, 50, 100]
        for milestone in milestones:
            achievement = f"quiz_milestone_{milestone}"
            if (
                self.total_quizzes_taken >= milestone
                and achievement not in self.achievement_unlocked
            ):
                achievements.append(achievement)

        # Add new achievements
        for achievement in achievements:
            if achievement not in self.achievement_unlocked:
                self.achievement_unlocked.append(achievement)
