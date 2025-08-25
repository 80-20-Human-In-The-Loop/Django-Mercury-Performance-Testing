"""Core UI Components for Django Mercury Plugin System.

This module provides reusable UI components that any plugin can use to create
beautiful terminal interfaces. Components follow the 80-20 principle with
simple APIs that handle complex terminal rendering automatically.

Components:
- SlideShow: Full-screen slideshow navigation system
- ProgressTracker: Visual progress bars and completion tracking
- InteractiveChoice: Beautiful multiple choice selection interface
- UserProgress: Persistent user progress and learning analytics
"""

from .components import SlideShow, ProgressTracker, InteractiveChoice
from .persistence import UserProgress, Preferences
from .themes import Theme, get_theme

__all__ = [
    "SlideShow",
    "ProgressTracker",
    "InteractiveChoice",
    "UserProgress",
    "Preferences",
    "Theme",
    "get_theme",
]
