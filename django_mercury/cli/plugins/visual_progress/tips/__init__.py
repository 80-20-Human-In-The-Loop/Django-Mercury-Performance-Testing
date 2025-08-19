"""
Modular Learning Tips System

This package contains organized learning tips that are easy to expand.
Each module focuses on a specific topic area for better organization.
"""

from .user_tips import TIPS as USER_TIPS
from .performance_tips import TIPS as PERFORMANCE_TIPS
from .testing_tips import TIPS as TESTING_TIPS
from .django_tips import TIPS as DJANGO_TIPS
from .api_tips import TIPS as API_TIPS

# Combine all tips into a searchable registry
ALL_TIPS = {**USER_TIPS, **PERFORMANCE_TIPS, **TESTING_TIPS, **DJANGO_TIPS, **API_TIPS}

# Create keyword to tips mapping for fast lookup
KEYWORD_MAPPING = {}
for tip_id, tip_data in ALL_TIPS.items():
    for keyword in tip_data.get("keywords", []):
        if keyword not in KEYWORD_MAPPING:
            KEYWORD_MAPPING[keyword] = []
        KEYWORD_MAPPING[keyword].append(tip_id)

# Create difficulty levels mapping
DIFFICULTY_LEVELS = {"beginner": [], "intermediate": [], "advanced": []}

for tip_id, tip_data in ALL_TIPS.items():
    difficulty = tip_data.get("difficulty", "beginner")
    if difficulty in DIFFICULTY_LEVELS:
        DIFFICULTY_LEVELS[difficulty].append(tip_id)

__all__ = ["ALL_TIPS", "KEYWORD_MAPPING", "DIFFICULTY_LEVELS"]
