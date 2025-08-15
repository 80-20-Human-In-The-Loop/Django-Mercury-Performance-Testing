"""
Performance Hints Database for Visual Test Runner

Contains actionable performance optimization hints based on test metrics.
Organized by performance issue type with different levels of detail.
"""

import random
from typing import Dict, List, Optional


class PerformanceHints:
    """Database of performance optimization hints."""
    
    # Hints organized by issue type
    HINTS_DATABASE = {
        'high_queries': {
            'title': 'Too Many Database Queries',
            'threshold': 20,
            'student_hints': [
                "Use select_related() for ForeignKey relationships to avoid extra queries",
                "Use prefetch_related() for ManyToMany and reverse ForeignKey relationships",
                "Consider using only() to load specific fields instead of entire models",
                "Check for N+1 query patterns - queries inside loops are usually bad",
                "Use bulk_create() instead of multiple create() calls",
                "Review your serializer - nested serializers can cause extra queries"
            ],
            'expert_hints': [
                "select_related() for FK, prefetch_related() for M2M/reverse FK",
                "Use only()/defer() to limit fields",
                "Check for N+1 patterns",
                "Consider bulk operations"
            ]
        },
        'slow_response': {
            'title': 'Slow Response Time',
            'threshold': 200,  # milliseconds
            'student_hints': [
                "Profile your code to find the slowest parts",
                "Add database indexes on fields you filter or order by",
                "Use caching for expensive computations that don't change often",
                "Optimize your serializer - remove unnecessary fields",
                "Consider pagination for large datasets instead of loading everything",
                "Check if you're doing unnecessary work in the view"
            ],
            'expert_hints': [
                "Profile bottlenecks",
                "Add DB indexes",
                "Implement caching",
                "Optimize serializers",
                "Use pagination"
            ]
        },
        'n_plus_one': {
            'title': 'N+1 Query Pattern Detected',
            'threshold': 1,  # Any N+1 is bad
            'student_hints': [
                "N+1 queries happen when you load a list, then query for each item",
                "Use select_related() for ForeignKey relationships",
                "Use prefetch_related() for ManyToMany or reverse relationships",
                "Check your serializer's depth setting - deep nesting causes N+1",
                "Avoid accessing relationships inside loops"
            ],
            'expert_hints': [
                "Use select_related() for FK relationships",
                "Use prefetch_related() for M2M/reverse FK",
                "Review serializer depth",
                "Avoid relationship access in loops"
            ]
        },
        'memory_usage': {
            'title': 'High Memory Usage',
            'threshold': 100,  # MB
            'student_hints': [
                "Use iterator() for large querysets instead of loading all at once",
                "Clear Django caches between operations with cache.clear()",
                "Use values() or values_list() instead of full model instances",
                "Stream large responses instead of building them in memory",
                "Consider chunking large operations"
            ],
            'expert_hints': [
                "Use iterator() for large querysets",
                "Clear caches between operations",
                "Use values()/values_list()",
                "Stream responses"
            ]
        }
    }
    
    # Learning resources for students
    LEARNING_RESOURCES = {
        'student': [
            "Django Query Optimization: https://docs.djangoproject.com/en/stable/topics/db/optimization/",
            "Understanding select_related: https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related",
            "Database Performance: https://docs.djangoproject.com/en/stable/topics/db/optimization/#use-select-related",
            "DRF Performance: https://www.django-rest-framework.org/api-guide/serializers/#dealing-with-nested-representations"
        ],
        'expert': [],  # Experts don't need learning resources
        'agent': []
    }

    @classmethod
    def get_hint_for_issue(cls, issue_type: str, profile: str = 'expert') -> Optional[str]:
        """
        Get a random hint for a specific performance issue.
        
        Args:
            issue_type: Type of performance issue ('high_queries', 'slow_response', etc.)
            profile: User profile ('student', 'expert', 'agent')
            
        Returns:
            Random hint string, or None if issue type not found
        """
        if issue_type not in cls.HINTS_DATABASE:
            return None
            
        hints_key = 'student_hints' if profile == 'student' else 'expert_hints'
        hints = cls.HINTS_DATABASE[issue_type].get(hints_key, [])
        
        if not hints:
            return None
            
        return random.choice(hints)
    
    @classmethod
    def get_hints_for_metrics(cls, query_count: int, response_time_ms: float, 
                            memory_mb: float, n_plus_one: bool, 
                            profile: str = 'expert') -> List[str]:
        """
        Get relevant hints based on test metrics.
        
        Args:
            query_count: Number of database queries
            response_time_ms: Response time in milliseconds
            memory_mb: Memory usage in MB
            n_plus_one: Whether N+1 pattern was detected
            profile: User profile
            
        Returns:
            List of relevant hints
        """
        hints = []
        
        # Check each performance issue
        if n_plus_one:
            hint = cls.get_hint_for_issue('n_plus_one', profile)
            if hint:
                hints.append(hint)
        
        if query_count >= cls.HINTS_DATABASE['high_queries']['threshold']:
            hint = cls.get_hint_for_issue('high_queries', profile)
            if hint:
                hints.append(hint)
        
        if response_time_ms >= cls.HINTS_DATABASE['slow_response']['threshold']:
            hint = cls.get_hint_for_issue('slow_response', profile)
            if hint:
                hints.append(hint)
        
        if memory_mb >= cls.HINTS_DATABASE['memory_usage']['threshold']:
            hint = cls.get_hint_for_issue('memory_usage', profile)
            if hint:
                hints.append(hint)
        
        return hints
    
    @classmethod
    def get_learning_resources(cls, profile: str) -> List[str]:
        """
        Get learning resources for the given profile.
        
        Args:
            profile: User profile
            
        Returns:
            List of learning resource URLs/descriptions
        """
        return cls.LEARNING_RESOURCES.get(profile, [])
    
    @classmethod
    def get_issue_title(cls, issue_type: str) -> str:
        """
        Get the display title for an issue type.
        
        Args:
            issue_type: Type of performance issue
            
        Returns:
            Human-readable title
        """
        return cls.HINTS_DATABASE.get(issue_type, {}).get('title', issue_type.title())