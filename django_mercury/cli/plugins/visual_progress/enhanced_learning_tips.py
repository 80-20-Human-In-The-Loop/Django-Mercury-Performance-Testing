"""
Enhanced Contextual Learning Tips System

Uses the new modular architecture for easy expansion and better organization.
Provides contextual tips with learn more links and difficulty progression.
"""

import random
import time
from typing import Dict, List, Optional, Set

from .tips import ALL_TIPS, KEYWORD_MAPPING, DIFFICULTY_LEVELS


class EnhancedLearningTipsDatabase:
    """Enhanced learning tips database with modular architecture."""

    def __init__(self):
        """Initialize the enhanced tips database."""
        self.last_tip_time = 0
        self.current_tip_id = None
        self.tip_rotation_interval = 10  # seconds
        self.shown_tips: Set[str] = set()  # Track shown tips to avoid repetition
        self.user_level = "beginner"  # Track user progression

    def get_contextual_tip(self, test_name: str = "", test_results: Dict = None) -> Dict:
        """
        Get a contextual tip with learn more information.

        Args:
            test_name: Current or recent test name
            test_results: Optional test results for context

        Returns:
            Dict with tip data including learn more info
        """
        current_time = time.time()

        # Check if it's time to rotate tips
        if (current_time - self.last_tip_time) >= self.tip_rotation_interval:
            self.current_tip_id = self._select_tip_id(test_name, test_results)
            self.last_tip_time = current_time

        if not self.current_tip_id:
            self.current_tip_id = self._select_tip_id(test_name, test_results)
            self.last_tip_time = current_time

        return self._format_tip_display(self.current_tip_id, test_name, test_results)

    def _select_tip_id(self, test_name: str, test_results: Dict = None) -> str:
        """Select appropriate tip ID based on context and difficulty."""
        test_name_lower = test_name.lower()

        # Find matching keywords
        matching_tip_ids = set()
        for keyword, tip_ids in KEYWORD_MAPPING.items():
            if keyword in test_name_lower:
                matching_tip_ids.update(tip_ids)

        # Add performance-based tips
        if test_results:
            if test_results.get("query_count", 0) > 20:
                matching_tip_ids.update(KEYWORD_MAPPING.get("performance", []))
            if "f" in str(test_results.get("grade", "")).lower():
                matching_tip_ids.update(KEYWORD_MAPPING.get("performance", []))

        # Filter by difficulty level and shown status
        available_tips = []
        for tip_id in matching_tip_ids:
            if tip_id in ALL_TIPS:
                tip_difficulty = ALL_TIPS[tip_id].get("difficulty", "beginner")
                # Prefer tips appropriate for user level, but allow variety
                if tip_difficulty == self.user_level or tip_id not in self.shown_tips:
                    available_tips.append(tip_id)

        # If no contextual tips, fall back to general tips by difficulty
        if not available_tips:
            difficulty_tips = DIFFICULTY_LEVELS.get(self.user_level, [])
            available_tips = [tip_id for tip_id in difficulty_tips if tip_id not in self.shown_tips]

            # If all shown, reset and use all tips
            if not available_tips:
                self.shown_tips.clear()
                available_tips = difficulty_tips

        if available_tips:
            selected_tip = random.choice(available_tips)
            self.shown_tips.add(selected_tip)
            return selected_tip

        # Ultimate fallback
        return random.choice(list(ALL_TIPS.keys()))

    def _format_tip_display(self, tip_id: str, test_name: str, test_results: Dict) -> Dict:
        """Format tip for display with learn more information."""
        if tip_id not in ALL_TIPS:
            return self._get_fallback_tip()

        tip_data = ALL_TIPS[tip_id]

        # Build the display text
        display_text = f"{tip_data['title']}\n\n{tip_data['content']}"

        # Add code example if available
        if "code_example" in tip_data:
            display_text += f"\n\n{tip_data['code_example']}"

        # Get related tips for learn more
        learn_more_commands = self._get_learn_more_commands(tip_id, test_name)

        return {
            "text": display_text,
            "tip_id": tip_id,
            "category": tip_data.get("category", "general"),
            "difficulty": tip_data.get("difficulty", "beginner"),
            "learn_more_commands": learn_more_commands,
            "learn_more_count": len(learn_more_commands),
        }

    def _get_learn_more_commands(self, tip_id: str, test_name: str) -> List[str]:
        """Generate learn more commands based on tip and context."""
        commands = []

        if tip_id not in ALL_TIPS:
            return ["mercury-test --learn performance"]

        tip_data = ALL_TIPS[tip_id]

        # Add the specific learn more command for this tip
        if "learn_more" in tip_data:
            commands.append(f"mercury-test --learn {tip_data['learn_more']}")

        # Add category-based commands
        category = tip_data.get("category", "general")
        if category == "performance":
            commands.extend(
                ["mercury-test --learn django-orm", "mercury-test --learn query-optimization"]
            )
        elif category == "testing":
            commands.extend(
                ["mercury-test --learn testing-patterns", "mercury-test --learn test-organization"]
            )
        elif category == "api":
            commands.extend(
                ["mercury-test --learn drf-optimization", "mercury-test --learn api-design"]
            )
        elif category == "django":
            commands.extend(
                ["mercury-test --learn django-models", "mercury-test --learn django-best-practices"]
            )

        # Add context-based commands from test name
        test_name_lower = test_name.lower()
        if "user" in test_name_lower:
            commands.append("mercury-test --learn user-optimization")
        if "api" in test_name_lower or "serializer" in test_name_lower:
            commands.append("mercury-test --learn api-testing")
        if "friend" in test_name_lower:
            commands.append("mercury-test --learn relationship-optimization")

        # Remove duplicates and limit to 3-4 commands
        unique_commands = list(dict.fromkeys(commands))  # Preserves order
        return unique_commands[:4]

    def _get_fallback_tip(self) -> Dict:
        """Get a fallback tip when no specific tip is found."""
        return {
            "text": "🧪 Testing Best Practices\n\nUse descriptive test method names\nthat explain the expected behavior.\nThis makes debugging much easier!",
            "tip_id": "fallback",
            "category": "testing",
            "difficulty": "beginner",
            "learn_more_commands": ["mercury-test --learn testing-patterns"],
            "learn_more_count": 1,
        }

    def get_next_tip_countdown(self) -> int:
        """Get seconds until next tip rotation."""
        elapsed = time.time() - self.last_tip_time
        remaining = max(0, self.tip_rotation_interval - elapsed)
        return int(remaining)

    def force_rotation(self):
        """Force tip rotation on next request."""
        self.last_tip_time = 0

    def set_user_level(self, level: str):
        """Set user difficulty level for tip selection."""
        if level in ["beginner", "intermediate", "advanced"]:
            self.user_level = level

    def get_available_tip_count(self, test_name: str = "", test_results: Dict = None) -> int:
        """Get count of available tips for current context."""
        test_name_lower = test_name.lower()

        # Count matching tips
        matching_tip_ids = set()
        for keyword, tip_ids in KEYWORD_MAPPING.items():
            if keyword in test_name_lower:
                matching_tip_ids.update(tip_ids)

        return len(matching_tip_ids) if matching_tip_ids else len(ALL_TIPS)


# Global instance for the visual display
enhanced_learning_tips_db = EnhancedLearningTipsDatabase()
