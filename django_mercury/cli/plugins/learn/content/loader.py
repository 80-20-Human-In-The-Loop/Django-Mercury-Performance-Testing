"""Content loader for quiz and learning materials."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models.quiz import Quiz, Question, Answer, DifficultyLevel, QuestionType


class ContentLoader:
    """Load quiz content from JSON files and convert to models."""

    def __init__(self):
        self.content_dir = Path(__file__).parent.parent / "data" / "quizzes"

    def load_quiz_from_file(self, filepath: Path) -> Optional[Quiz]:
        """Load a single quiz from a JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            quiz_data = data.get("quiz", {})
            if not quiz_data:
                return None

            # Convert questions
            questions = []
            for q_data in quiz_data.get("questions", []):
                # Convert answers
                answers = []
                for ans_data in q_data.get("answers", []):
                    answer = Answer(
                        text=ans_data.get("text", ""),
                        is_correct=ans_data.get("is_correct", False),
                        explanation=ans_data.get("explanation"),
                        hint=ans_data.get("hint"),
                    )
                    answers.append(answer)

                # Create question
                question = Question(
                    id=q_data.get("id", ""),
                    question_type=QuestionType(q_data.get("question_type", "multiple_choice")),
                    text=q_data.get("text", ""),
                    answers=answers,
                    explanation=q_data.get("explanation", ""),
                    hints=q_data.get("hints", []),
                    difficulty=DifficultyLevel(q_data.get("difficulty", "beginner")),
                    concept=q_data.get("concept", ""),
                    tags=q_data.get("tags", []),
                )
                questions.append(question)

            # Create quiz
            quiz = Quiz(
                id=quiz_data.get("id", ""),
                title=quiz_data.get("title", ""),
                description=quiz_data.get("description", ""),
                questions=questions,
                difficulty=DifficultyLevel(quiz_data.get("difficulty", "beginner")),
                concept=quiz_data.get("concept", ""),
                tags=quiz_data.get("tags", []),
                passing_score=quiz_data.get("passing_score", 0.7),
            )

            return quiz

        except Exception as e:
            print(f"Error loading quiz from {filepath}: {e}")
            return None

    def load_quiz_by_concept(self, concept: str) -> Optional[Quiz]:
        """Load quiz by concept name (e.g., 'n+1-queries')."""
        # Normalize the concept for comparison
        concept_normalized = concept.lower().replace("-", "_").replace(" ", "_")
        concept_with_dashes = concept.lower().replace("_", "-").replace(" ", "-")

        # Check all difficulty levels
        for difficulty in ["beginner", "intermediate", "advanced"]:
            quiz_dir = self.content_dir / difficulty
            if not quiz_dir.exists():
                continue

            # Look for files matching the concept (try both normalized forms)
            for quiz_file in quiz_dir.glob("*.json"):
                filename_lower = quiz_file.stem.lower()
                filename_normalized = filename_lower.replace("-", "_").replace(" ", "_")

                # Try multiple matching strategies
                if (
                    concept_normalized in filename_normalized
                    or concept_with_dashes in filename_lower
                    or concept.lower() in filename_lower
                ):
                    quiz = self.load_quiz_from_file(quiz_file)
                    if quiz:
                        return quiz

        return None

    def load_all_quizzes(self) -> List[Quiz]:
        """Load all available quizzes."""
        quizzes = []

        # Iterate through all difficulty directories
        for difficulty_dir in self.content_dir.iterdir():
            if not difficulty_dir.is_dir():
                continue

            # Load all JSON files in this directory
            for quiz_file in difficulty_dir.glob("*.json"):
                quiz = self.load_quiz_from_file(quiz_file)
                if quiz:
                    quizzes.append(quiz)

        return quizzes

    def get_available_concepts(self) -> List[str]:
        """Get list of all available quiz concepts."""
        concepts = set()

        for quiz in self.load_all_quizzes():
            if quiz.concept:
                concepts.add(quiz.concept)

        return sorted(list(concepts))

    def get_quiz_for_performance_hierarchy(self) -> Optional[Quiz]:
        """Get the specific performance hierarchy quiz."""
        return self.load_quiz_by_concept("performance-hierarchy")

    def get_quiz_for_n1_queries(self) -> Optional[Quiz]:
        """Get the N+1 queries quiz."""
        return self.load_quiz_by_concept("n1-queries")

    def load_tutorial_from_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Load a tutorial from a JSON file.

        Returns the raw tutorial data dictionary for now, since tutorial_types
        may not be available in all environments.
        """
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return data.get("tutorial")
        except Exception as e:
            print(f"Error loading tutorial from {filepath}: {e}")
            return None

    def load_tutorial_by_concept(self, concept: str) -> Optional[Dict[str, Any]]:
        """Load tutorial by concept name."""
        # Normalize the concept for comparison
        concept_normalized = concept.lower().replace("-", "_").replace(" ", "_")
        concept_with_dashes = concept.lower().replace("_", "-").replace(" ", "-")

        # Check tutorials directory (parallel to quizzes)
        tutorial_dir = self.content_dir.parent / "tutorials"
        if not tutorial_dir.exists():
            return None

        # Look for files matching the concept
        for tutorial_file in tutorial_dir.glob("*.json"):
            filename_lower = tutorial_file.stem.lower()
            filename_normalized = filename_lower.replace("-", "_").replace(" ", "_")

            # Try multiple matching strategies
            if (
                concept_normalized in filename_normalized
                or concept_with_dashes in filename_lower
                or concept.lower() in filename_lower
            ):
                tutorial = self.load_tutorial_from_file(tutorial_file)
                if tutorial:
                    return tutorial

        return None
