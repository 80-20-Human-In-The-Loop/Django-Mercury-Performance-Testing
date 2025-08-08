"""Progress tracking system for Django Mercury educational mode.

Tracks learning progress, concepts mastered, and adapts difficulty
based on the 80-20 Human-in-the-Loop philosophy.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProgressTracker:
    """Tracks user's learning progress across sessions."""

    def __init__(
        self,
        level: str = "beginner",
        storage_path: Optional[Path] = None,
    ) -> None:
        """Initialize progress tracker.

        Args:
            level: Starting difficulty level
            storage_path: Custom path for progress storage
        """
        self.level = level
        self.storage_path = storage_path or (
            Path.home() / ".django_mercury" / "learning_progress.json"
        )
        self.progress_data = self._load_progress()
        self.session_data = {
            "concepts_covered": [],
            "quiz_results": [],
            "optimizations_learned": [],
            "start_time": datetime.now().isoformat(),
        }

    def _load_progress(self) -> Dict[str, Any]:
        """Load progress from persistent storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    # Ensure all required fields exist
                    return self._validate_progress_data(data)
            except (OSError, json.JSONDecodeError):
                pass

        return self._create_initial_progress()

    def _validate_progress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix progress data structure."""
        default = self._create_initial_progress()

        # Ensure all required keys exist
        for key in default:
            if key not in data:
                data[key] = default[key]

        return data

    def _create_initial_progress(self) -> Dict[str, Any]:
        """Create initial progress structure."""
        return {
            "level": self.level,
            "total_sessions": 0,
            "concepts_mastered": [],
            "concepts_in_progress": [],
            "quiz_history": {},
            "optimization_patterns": {},
            "achievements": [],
            "statistics": {
                "total_tests_run": 0,
                "total_issues_found": 0,
                "total_issues_fixed": 0,
                "quiz_accuracy": 0.0,
                "favorite_optimization": None,
            },
            "learning_path": {
                "current_module": "basics",
                "completed_modules": [],
                "next_suggested": None,
            },
            "last_session": None,
        }

    def save(self) -> None:
        """Save progress to persistent storage."""
        # Update session end time
        self.session_data["end_time"] = datetime.now().isoformat()

        # Update overall progress with session data
        self._merge_session_data()

        # Save to file
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.progress_data, f, indent=2)

    def _merge_session_data(self) -> None:
        """Merge session data into overall progress."""
        self.progress_data["total_sessions"] += 1
        self.progress_data["last_session"] = self.session_data

        # Update concepts mastered
        for concept in self.session_data["concepts_covered"]:
            if concept not in self.progress_data["concepts_mastered"]:
                if concept in self.progress_data["concepts_in_progress"]:
                    # Check if concept is mastered (e.g., 3 correct quizzes)
                    quiz_results = [
                        r for r in self.session_data["quiz_results"]
                        if r.get("concept") == concept and r.get("correct")
                    ]
                    if len(quiz_results) >= 2:
                        self.progress_data["concepts_in_progress"].remove(concept)
                        self.progress_data["concepts_mastered"].append(concept)
                else:
                    self.progress_data["concepts_in_progress"].append(concept)

        # Update quiz statistics
        if self.session_data["quiz_results"]:
            correct = sum(1 for r in self.session_data["quiz_results"] if r.get("correct"))
            total = len(self.session_data["quiz_results"])
            session_accuracy = (correct / total) * 100

            # Update rolling average
            current_accuracy = self.progress_data["statistics"]["quiz_accuracy"]
            total_sessions = self.progress_data["total_sessions"]
            new_accuracy = (
                (current_accuracy * (total_sessions - 1) + session_accuracy)
                / total_sessions
            )
            self.progress_data["statistics"]["quiz_accuracy"] = new_accuracy

    def record_concept_learned(self, concept: str) -> None:
        """Record that a concept was covered in this session.

        Args:
            concept: The concept identifier
        """
        if concept not in self.session_data["concepts_covered"]:
            self.session_data["concepts_covered"].append(concept)

    def record_quiz_result(
        self,
        concept: str,
        correct: bool,
        difficulty: str,
    ) -> None:
        """Record the result of a quiz question.

        Args:
            concept: The concept being tested
            correct: Whether the answer was correct
            difficulty: The difficulty level of the question
        """
        result = {
            "concept": concept,
            "correct": correct,
            "difficulty": difficulty,
            "timestamp": datetime.now().isoformat(),
        }
        self.session_data["quiz_results"].append(result)

        # Update quiz history
        if concept not in self.progress_data["quiz_history"]:
            self.progress_data["quiz_history"][concept] = {
                "attempts": 0,
                "correct": 0,
            }

        self.progress_data["quiz_history"][concept]["attempts"] += 1
        if correct:
            self.progress_data["quiz_history"][concept]["correct"] += 1

    def record_optimization_learned(
        self,
        optimization_type: str,
        before_metric: Any,
        after_metric: Any,
    ) -> None:
        """Record an optimization that was successfully applied.

        Args:
            optimization_type: Type of optimization (e.g., "select_related")
            before_metric: Metric before optimization
            after_metric: Metric after optimization
        """
        optimization = {
            "type": optimization_type,
            "before": before_metric,
            "after": after_metric,
            "improvement": self._calculate_improvement(before_metric, after_metric),
            "timestamp": datetime.now().isoformat(),
        }
        self.session_data["optimizations_learned"].append(optimization)

        # Track optimization patterns
        if optimization_type not in self.progress_data["optimization_patterns"]:
            self.progress_data["optimization_patterns"][optimization_type] = 0
        self.progress_data["optimization_patterns"][optimization_type] += 1

        # Update favorite optimization
        most_used = max(
            self.progress_data["optimization_patterns"].items(),
            key=lambda x: x[1],
        )
        self.progress_data["statistics"]["favorite_optimization"] = most_used[0]

    def _calculate_improvement(self, before: Any, after: Any) -> float:
        """Calculate percentage improvement between metrics."""
        try:
            before_val = float(before)
            after_val = float(after)
            if before_val == 0:
                return 100.0 if after_val == 0 else 0.0
            return ((before_val - after_val) / before_val) * 100
        except (TypeError, ValueError):
            return 0.0

    def get_adaptive_difficulty(self) -> str:
        """Get recommended difficulty based on performance.

        Returns:
            Recommended difficulty level
        """
        accuracy = self.progress_data["statistics"]["quiz_accuracy"]
        concepts_mastered = len(self.progress_data["concepts_mastered"])

        if accuracy >= 80 and concepts_mastered >= 10:
            return "advanced"
        elif accuracy >= 60 and concepts_mastered >= 5:
            return "intermediate"
        else:
            return "beginner"

    def should_show_quiz(self, concept: str) -> bool:
        """Determine if a quiz should be shown for this concept.

        Args:
            concept: The concept to potentially quiz on

        Returns:
            True if quiz should be shown
        """
        # Always quiz on new concepts
        if concept not in self.progress_data["quiz_history"]:
            return True

        # Quiz on concepts that need reinforcement
        history = self.progress_data["quiz_history"][concept]
        if history["attempts"] == 0:
            return True

        accuracy = (history["correct"] / history["attempts"]) * 100

        # Re-quiz if accuracy is low
        if accuracy < 70:
            return True

        # Occasionally re-quiz mastered concepts for reinforcement
        if concept in self.progress_data["concepts_mastered"]:
            import random
            return random.random() < 0.1  # 10% chance

        return False

    def get_next_learning_suggestion(self) -> str:
        """Get a suggestion for what to learn next.

        Returns:
            Learning suggestion string
        """
        concepts_in_progress = len(self.progress_data["concepts_in_progress"])
        concepts_mastered = len(self.progress_data["concepts_mastered"])

        if concepts_mastered == 0:
            return "Start with N+1 query detection - it's the most common performance issue!"
        elif concepts_in_progress > 3:
            return "Focus on mastering your current concepts before learning new ones."
        elif "n+1_queries" in self.progress_data["concepts_mastered"]:
            if "caching" not in self.progress_data["concepts_mastered"]:
                return "Learn about caching strategies to further improve performance."
            elif "database_optimization" not in self.progress_data["concepts_mastered"]:
                return "Explore database indexing and query optimization techniques."

        return "You're doing great! Try running tests on more complex views."

    def get_motivational_message(self) -> str:
        """Get a motivational message based on progress.

        Returns:
            Motivational message string
        """
        total_sessions = self.progress_data["total_sessions"]
        concepts_mastered = len(self.progress_data["concepts_mastered"])
        accuracy = self.progress_data["statistics"]["quiz_accuracy"]

        if total_sessions == 1:
            return "🎉 Welcome to Django Mercury! Every expert was once a beginner."
        elif concepts_mastered == 0:
            return "💪 Keep going! Learning takes time and practice."
        elif concepts_mastered < 5:
            return "🚀 You're building a strong foundation. Well done!"
        elif concepts_mastered < 10:
            return "⭐ Impressive progress! You're becoming a performance expert."
        elif accuracy >= 80:
            return "🏆 Outstanding! You've mastered Django performance optimization!"
        else:
            return "📈 Great job! Your skills are improving with every session."

    def get_session_concepts(self) -> List[str]:
        """Get concepts covered in current session.

        Returns:
            List of concept identifiers
        """
        return self.session_data["concepts_covered"]

    def get_all_concepts(self) -> List[str]:
        """Get all concepts ever learned.

        Returns:
            List of concept identifiers
        """
        return self.progress_data["concepts_mastered"]

    def reset(self) -> None:
        """Reset all progress data."""
        self.progress_data = self._create_initial_progress()
        self.session_data = {
            "concepts_covered": [],
            "quiz_results": [],
            "optimizations_learned": [],
            "start_time": datetime.now().isoformat(),
        }
        self.save()

    def check_achievement(self, achievement_id: str) -> bool:
        """Check if an achievement has been earned.

        Args:
            achievement_id: The achievement identifier

        Returns:
            True if achievement earned
        """
        if achievement_id in self.progress_data["achievements"]:
            return False

        # Define achievement criteria
        achievements = {
            "first_optimization": len(self.session_data["optimizations_learned"]) > 0,
            "quiz_master": self.progress_data["statistics"]["quiz_accuracy"] >= 90,
            "speed_demon": any(
                opt.get("improvement", 0) > 50
                for opt in self.session_data["optimizations_learned"]
            ),
            "persistent_learner": self.progress_data["total_sessions"] >= 10,
            "concept_collector": len(self.progress_data["concepts_mastered"]) >= 5,
        }

        if achievements.get(achievement_id, False):
            self.progress_data["achievements"].append(achievement_id)
            return True

        return False

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of learning progress.

        Returns:
            Dictionary with progress metrics
        """
        return {
            "level": self.get_adaptive_difficulty(),
            "sessions_completed": self.progress_data["total_sessions"],
            "concepts_mastered": len(self.progress_data["concepts_mastered"]),
            "concepts_in_progress": len(self.progress_data["concepts_in_progress"]),
            "quiz_accuracy": self.progress_data["statistics"]["quiz_accuracy"],
            "achievements_earned": len(self.progress_data["achievements"]),
            "favorite_optimization": self.progress_data["statistics"]["favorite_optimization"],
            "next_suggestion": self.get_next_learning_suggestion(),
            "motivational_message": self.get_motivational_message(),
        }
