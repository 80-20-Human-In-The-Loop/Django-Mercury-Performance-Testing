"""
Advanced Learning Paths for Django Mercury Educational Mode

This module provides structured learning journeys that guide users from
basic to expert Django performance optimization skills following the
80-20 Human-in-the-Loop philosophy.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class SkillLevel(Enum):
    """Skill levels for learning progression."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ConceptStatus(Enum):
    """Status of concept mastery."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MASTERED = "mastered"


@dataclass
class LearningConcept:
    """Represents a single learning concept with prerequisites and outcomes."""
    id: str
    name: str
    description: str
    skill_level: SkillLevel
    prerequisites: List[str] = field(default_factory=list)
    estimated_time_minutes: int = 15
    quiz_questions: List[str] = field(default_factory=list)
    code_challenges: List[str] = field(default_factory=list)
    tutorial_stages: List[str] = field(default_factory=list)
    video_urls: List[str] = field(default_factory=list)
    practical_examples: List[str] = field(default_factory=list)


@dataclass
class LearningPath:
    """Represents a structured learning path with multiple concepts."""
    id: str
    name: str
    description: str
    target_audience: str
    skill_level: SkillLevel
    concepts: List[LearningConcept] = field(default_factory=list)
    estimated_total_time: int = 0
    difficulty_curve: str = "gradual"  # gradual, steep, mixed
    

@dataclass
class UserProgress:
    """Tracks user progress through learning paths and concepts."""
    user_id: str = "default"
    completed_concepts: Set[str] = field(default_factory=set)
    in_progress_concepts: Set[str] = field(default_factory=set)
    mastered_concepts: Set[str] = field(default_factory=set)
    current_skill_level: SkillLevel = SkillLevel.BEGINNER
    time_spent_minutes: int = 0
    quiz_scores: Dict[str, float] = field(default_factory=dict)
    challenge_completions: Dict[str, bool] = field(default_factory=dict)
    learning_preferences: Dict[str, Any] = field(default_factory=dict)


class LearningPathSystem:
    """Manages structured learning paths for Django performance optimization."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the learning path system."""
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.learning_paths: Dict[str, LearningPath] = {}
        self.concepts_db: Dict[str, LearningConcept] = {}
        self.user_progress = UserProgress()
        
        # Initialize with built-in learning paths
        self._load_builtin_paths()
    
    def _load_builtin_paths(self):
        """Load the built-in learning paths and concepts."""
        
        # Define core concepts
        concepts = [
            # Beginner Level Concepts
            LearningConcept(
                id="django_orm_basics",
                name="Django ORM Fundamentals",
                description="Understanding how Django ORM generates SQL queries and impacts performance",
                skill_level=SkillLevel.BEGINNER,
                estimated_time_minutes=20,
                quiz_questions=["django_orm_query_generation", "model_relationship_basics"],
                practical_examples=[
                    "Basic model queries and their SQL output",
                    "Understanding QuerySet lazy evaluation",
                    "Common ORM pitfalls for beginners"
                ]
            ),
            
            LearningConcept(
                id="n_plus_one_detection",
                name="N+1 Query Problem Recognition",
                description="Learning to identify and understand N+1 query problems in Django applications",
                skill_level=SkillLevel.BEGINNER,
                prerequisites=["django_orm_basics"],
                estimated_time_minutes=25,
                quiz_questions=["n_plus_one_identification", "query_count_analysis"],
                code_challenges=["fix_basic_n_plus_one"],
                tutorial_stages=["n_plus_one_tutorial_basic"],
                practical_examples=[
                    "Classic N+1 in user profile display",
                    "Blog posts with author information",
                    "Comment threads with user data"
                ]
            ),
            
            LearningConcept(
                id="select_related_basics",
                name="select_related() for Foreign Keys",
                description="Using select_related() to optimize foreign key relationships",
                skill_level=SkillLevel.BEGINNER,
                prerequisites=["n_plus_one_detection"],
                estimated_time_minutes=20,
                quiz_questions=["select_related_usage", "foreign_key_optimization"],
                code_challenges=["implement_select_related"],
                practical_examples=[
                    "User profile optimization",
                    "Post author optimization", 
                    "Order customer relationship optimization"
                ]
            ),
            
            LearningConcept(
                id="prefetch_related_basics",
                name="prefetch_related() for Reverse Relationships",
                description="Using prefetch_related() for many-to-many and reverse foreign key relationships",
                skill_level=SkillLevel.BEGINNER,
                prerequisites=["select_related_basics"],
                estimated_time_minutes=25,
                quiz_questions=["prefetch_related_usage", "many_to_many_optimization"],
                code_challenges=["implement_prefetch_related"],
                practical_examples=[
                    "Author posts optimization",
                    "Category products optimization",
                    "User permissions optimization"
                ]
            ),
            
            # Intermediate Level Concepts
            LearningConcept(
                id="database_indexing",
                name="Database Indexing for Performance",
                description="Understanding and implementing database indexes for query optimization",
                skill_level=SkillLevel.INTERMEDIATE,
                prerequisites=["prefetch_related_basics"],
                estimated_time_minutes=30,
                quiz_questions=["database_index_strategy", "composite_index_usage"],
                code_challenges=["add_strategic_indexes"],
                practical_examples=[
                    "Indexing frequently filtered fields",
                    "Composite indexes for complex queries",
                    "Index maintenance and trade-offs"
                ]
            ),
            
            LearningConcept(
                id="query_optimization_intermediate",
                name="Intermediate Query Optimization",
                description="only(), values(), defer() and other query optimization techniques",
                skill_level=SkillLevel.INTERMEDIATE,
                prerequisites=["database_indexing"],
                estimated_time_minutes=35,
                quiz_questions=["query_field_optimization", "memory_efficient_queries"],
                code_challenges=["optimize_large_querysets"],
                practical_examples=[
                    "Optimizing API serialization",
                    "Memory-efficient data exports",
                    "Selective field loading strategies"
                ]
            ),
            
            LearningConcept(
                id="caching_fundamentals", 
                name="Django Caching Strategies",
                description="Implementing effective caching with Django's cache framework",
                skill_level=SkillLevel.INTERMEDIATE,
                prerequisites=["query_optimization_intermediate"],
                estimated_time_minutes=40,
                quiz_questions=["cache_strategy_selection", "cache_invalidation"],
                code_challenges=["implement_view_caching", "implement_fragment_caching"],
                practical_examples=[
                    "View-level caching implementation",
                    "Template fragment caching",
                    "Cache invalidation strategies"
                ]
            ),
            
            LearningConcept(
                id="drf_serialization_optimization",
                name="DRF Serialization Performance",
                description="Optimizing Django REST Framework serializers for performance",
                skill_level=SkillLevel.INTERMEDIATE,
                prerequisites=["caching_fundamentals"],
                estimated_time_minutes=35,
                quiz_questions=["serializer_optimization_patterns", "api_performance_tuning"],
                code_challenges=["optimize_nested_serializers"],
                practical_examples=[
                    "SerializerMethodField optimization",
                    "Nested serializer performance",
                    "API pagination strategies"
                ]
            ),
            
            # Advanced Level Concepts
            LearningConcept(
                id="custom_prefetch_objects",
                name="Advanced Prefetch with Custom Querysets",
                description="Using Prefetch objects for sophisticated query optimization",
                skill_level=SkillLevel.ADVANCED,
                prerequisites=["drf_serialization_optimization"],
                estimated_time_minutes=45,
                quiz_questions=["prefetch_object_patterns", "nested_prefetch_strategies"],
                code_challenges=["implement_custom_prefetch"],
                practical_examples=[
                    "Conditional prefetching",
                    "Nested Prefetch objects",
                    "Dynamic relationship optimization"
                ]
            ),
            
            LearningConcept(
                id="database_connection_optimization",
                name="Database Connection and Pool Optimization",
                description="Optimizing database connections, connection pooling, and transaction management",
                skill_level=SkillLevel.ADVANCED,
                prerequisites=["custom_prefetch_objects"],
                estimated_time_minutes=50,
                quiz_questions=["connection_pool_configuration", "transaction_optimization"],
                code_challenges=["optimize_connection_usage"],
                practical_examples=[
                    "Connection pool configuration",
                    "Transaction optimization patterns",
                    "Database connection debugging"
                ]
            ),
            
            LearningConcept(
                id="advanced_caching_patterns",
                name="Advanced Caching and Cache Invalidation",
                description="Sophisticated caching patterns, cache stampede prevention, and invalidation strategies",
                skill_level=SkillLevel.ADVANCED,
                prerequisites=["database_connection_optimization"],
                estimated_time_minutes=55,
                quiz_questions=["cache_stampede_prevention", "distributed_cache_patterns"],
                code_challenges=["implement_cache_stampede_protection"],
                practical_examples=[
                    "Cache stampede prevention",
                    "Distributed cache invalidation",
                    "Multi-level cache hierarchies"
                ]
            ),
            
            # Expert Level Concepts
            LearningConcept(
                id="query_analysis_and_profiling",
                name="Advanced Query Analysis and Profiling",
                description="Deep query analysis, execution plan optimization, and performance profiling",
                skill_level=SkillLevel.EXPERT,
                prerequisites=["advanced_caching_patterns"],
                estimated_time_minutes=60,
                quiz_questions=["execution_plan_analysis", "query_profiling_techniques"],
                code_challenges=["optimize_complex_queries"],
                practical_examples=[
                    "Query execution plan analysis",
                    "Database-specific optimization",
                    "Performance profiling workflows"
                ]
            ),
            
            LearningConcept(
                id="scalability_architecture",
                name="Django Scalability Architecture Patterns",
                description="Designing Django applications for high-scale performance",
                skill_level=SkillLevel.EXPERT,
                prerequisites=["query_analysis_and_profiling"],
                estimated_time_minutes=90,
                quiz_questions=["scalability_patterns", "load_balancing_strategies"],
                code_challenges=["design_scalable_architecture"],
                practical_examples=[
                    "Read/write database splitting",
                    "Microservices integration patterns",
                    "Load balancing strategies"
                ]
            ),
            
            LearningConcept(
                id="performance_monitoring_mastery",
                name="Production Performance Monitoring",
                description="Advanced performance monitoring, alerting, and optimization in production",
                skill_level=SkillLevel.EXPERT,
                prerequisites=["scalability_architecture"],
                estimated_time_minutes=75,
                quiz_questions=["monitoring_strategy_design", "performance_alerting"],
                code_challenges=["setup_comprehensive_monitoring"],
                practical_examples=[
                    "APM tool integration",
                    "Custom metrics and dashboards",
                    "Performance alerting strategies"
                ]
            )
        ]
        
        # Store concepts in the database
        for concept in concepts:
            self.concepts_db[concept.id] = concept
        
        # Define learning paths
        paths = [
            # Beginner Path: Django Performance Basics
            LearningPath(
                id="django_performance_basics",
                name="Django Performance Fundamentals",
                description="Master the essential Django performance optimization techniques",
                target_audience="Django developers new to performance optimization",
                skill_level=SkillLevel.BEGINNER,
                concepts=[
                    self.concepts_db["django_orm_basics"],
                    self.concepts_db["n_plus_one_detection"], 
                    self.concepts_db["select_related_basics"],
                    self.concepts_db["prefetch_related_basics"]
                ],
                estimated_total_time=90,
                difficulty_curve="gradual"
            ),
            
            # Intermediate Path: Advanced Query Optimization
            LearningPath(
                id="advanced_query_optimization",
                name="Advanced Query Optimization Mastery",
                description="Learn sophisticated query optimization and caching techniques",
                target_audience="Django developers with basic performance knowledge",
                skill_level=SkillLevel.INTERMEDIATE,
                concepts=[
                    self.concepts_db["database_indexing"],
                    self.concepts_db["query_optimization_intermediate"],
                    self.concepts_db["caching_fundamentals"],
                    self.concepts_db["drf_serialization_optimization"]
                ],
                estimated_total_time=140,
                difficulty_curve="gradual"
            ),
            
            # Advanced Path: Enterprise Performance
            LearningPath(
                id="enterprise_performance_optimization",
                name="Enterprise-Scale Performance Engineering",
                description="Master advanced performance patterns for large-scale Django applications",
                target_audience="Senior developers and performance engineers",
                skill_level=SkillLevel.ADVANCED,
                concepts=[
                    self.concepts_db["custom_prefetch_objects"],
                    self.concepts_db["database_connection_optimization"],
                    self.concepts_db["advanced_caching_patterns"]
                ],
                estimated_total_time=150,
                difficulty_curve="steep"
            ),
            
            # Expert Path: Performance Architecture
            LearningPath(
                id="performance_architecture_mastery",
                name="Django Performance Architecture Mastery",
                description="Design and implement high-performance Django architectures",
                target_audience="Lead engineers and architects",
                skill_level=SkillLevel.EXPERT,
                concepts=[
                    self.concepts_db["query_analysis_and_profiling"],
                    self.concepts_db["scalability_architecture"],
                    self.concepts_db["performance_monitoring_mastery"]
                ],
                estimated_total_time=225,
                difficulty_curve="mixed"
            ),
            
            # Comprehensive Path: Complete Journey
            LearningPath(
                id="complete_performance_journey",
                name="Complete Django Performance Journey",
                description="The comprehensive path from beginner to expert performance optimization",
                target_audience="Developers committed to mastering Django performance",
                skill_level=SkillLevel.EXPERT,
                concepts=concepts,  # All concepts in order
                estimated_total_time=sum(c.estimated_time_minutes for c in concepts),
                difficulty_curve="mixed"
            )
        ]
        
        # Store paths
        for path in paths:
            self.learning_paths[path.id] = path
    
    def get_available_paths(self, skill_level: Optional[SkillLevel] = None) -> List[LearningPath]:
        """Get available learning paths, optionally filtered by skill level."""
        paths = list(self.learning_paths.values())
        
        if skill_level:
            # Filter paths suitable for the user's current skill level
            suitable_paths = []
            for path in paths:
                if path.skill_level == skill_level or self._is_path_accessible(path):
                    suitable_paths.append(path)
            return suitable_paths
        
        return paths
    
    def _is_path_accessible(self, path: LearningPath) -> bool:
        """Check if a learning path is accessible based on user progress."""
        # Check if user has completed prerequisite concepts
        for concept in path.concepts:
            if concept.prerequisites:
                for prereq_id in concept.prerequisites:
                    if prereq_id not in self.user_progress.completed_concepts:
                        return False
        return True
    
    def get_recommended_path(self) -> Optional[LearningPath]:
        """Get the recommended learning path for the user's current skill level."""
        skill_level = self.user_progress.current_skill_level
        
        # Find the most appropriate path
        available_paths = self.get_available_paths(skill_level)
        
        if not available_paths:
            return None
        
        # Prefer paths that match current skill level and have uncompeted concepts
        for path in available_paths:
            if path.skill_level == skill_level:
                uncompleted_concepts = [
                    c for c in path.concepts
                    if c.id not in self.user_progress.completed_concepts
                ]
                if uncompleted_concepts:
                    return path
        
        # Fall back to any available path
        return available_paths[0]
    
    def show_learning_paths(self, show_all: bool = False) -> None:
        """Display available learning paths with progress information."""
        if not self.console or not RICH_AVAILABLE:
            self._show_text_learning_paths(show_all)
            return
        
        # Header
        header_panel = Panel(
            Text.from_markup(
                "[bold cyan]🎓 Django Performance Learning Paths[/bold cyan]\n\n"
                f"[yellow]Current Level:[/yellow] {self.user_progress.current_skill_level.value.title()}\n"
                f"[yellow]Completed Concepts:[/yellow] {len(self.user_progress.completed_concepts)}\n"
                f"[yellow]Total Study Time:[/yellow] {self.user_progress.time_spent_minutes} minutes\n\n"
                "[italic]Choose your learning journey based on your current skill level and goals.[/italic]"
            ),
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(header_panel)
        
        # Get paths to display
        if show_all:
            paths_to_show = list(self.learning_paths.values())
        else:
            paths_to_show = self.get_available_paths()
        
        # Show each path
        for path in paths_to_show:
            self._show_path_summary(path)
    
    def _show_path_summary(self, path: LearningPath) -> None:
        """Show a summary of a single learning path."""
        if not self.console:
            return
            
        # Calculate progress
        completed_concepts = sum(
            1 for concept in path.concepts 
            if concept.id in self.user_progress.completed_concepts
        )
        total_concepts = len(path.concepts)
        progress_pct = (completed_concepts / total_concepts * 100) if total_concepts > 0 else 0
        
        # Determine path status
        if progress_pct == 0:
            status_color = "white"
            status_text = "Not Started"
        elif progress_pct == 100:
            status_color = "green"
            status_text = "Completed ✅"
        else:
            status_color = "yellow"
            status_text = f"In Progress ({completed_concepts}/{total_concepts})"
        
        # Create path panel
        path_content = Text.from_markup(
            f"[bold]{path.name}[/bold]\n\n"
            f"[white]{path.description}[/white]\n\n"
            f"[cyan]Target Audience:[/cyan] {path.target_audience}\n"
            f"[cyan]Skill Level:[/cyan] {path.skill_level.value.title()}\n"
            f"[cyan]Estimated Time:[/cyan] {path.estimated_total_time} minutes\n"
            f"[cyan]Concepts:[/cyan] {total_concepts}\n"
            f"[{status_color}]Status:[/{status_color}] {status_text}"
        )
        
        # Add progress bar
        if progress_pct > 0:
            progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
            path_content.append(f"\n[cyan]Progress:[/cyan] [{status_color}]{progress_bar}[/{status_color}] {progress_pct:.0f}%")
        
        path_panel = Panel(
            path_content,
            border_style=status_color,
            padding=(1, 2)
        )
        self.console.print(path_panel)
    
    def _show_text_learning_paths(self, show_all: bool = False) -> None:
        """Show learning paths in plain text mode."""
        print("\n🎓 DJANGO PERFORMANCE LEARNING PATHS")
        print("=" * 60)
        print(f"Current Level: {self.user_progress.current_skill_level.value.title()}")
        print(f"Completed Concepts: {len(self.user_progress.completed_concepts)}")
        print("=" * 60)
        
        paths_to_show = list(self.learning_paths.values()) if show_all else self.get_available_paths()
        
        for i, path in enumerate(paths_to_show, 1):
            completed = sum(
                1 for concept in path.concepts 
                if concept.id in self.user_progress.completed_concepts
            )
            total = len(path.concepts)
            
            print(f"\n{i}. {path.name}")
            print(f"   Level: {path.skill_level.value.title()}")
            print(f"   Time: {path.estimated_total_time} minutes")
            print(f"   Progress: {completed}/{total} concepts")
            print(f"   {path.description}")
    
    def show_path_details(self, path_id: str) -> None:
        """Show detailed information about a specific learning path."""
        if path_id not in self.learning_paths:
            if self.console:
                self.console.print(f"[red]❌ Path '{path_id}' not found[/red]")
            else:
                print(f"❌ Path '{path_id}' not found")
            return
        
        path = self.learning_paths[path_id]
        
        if not self.console or not RICH_AVAILABLE:
            self._show_text_path_details(path)
            return
        
        # Path header
        header = Panel(
            Text.from_markup(
                f"[bold cyan]📚 {path.name}[/bold cyan]\n\n"
                f"[white]{path.description}[/white]\n\n"
                f"[yellow]Skill Level:[/yellow] {path.skill_level.value.title()}\n"
                f"[yellow]Total Time:[/yellow] {path.estimated_total_time} minutes\n"
                f"[yellow]Concepts:[/yellow] {len(path.concepts)}\n"
                f"[yellow]Difficulty Curve:[/yellow] {path.difficulty_curve.title()}"
            ),
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(header)
        
        # Concept progression tree
        self._show_concept_tree(path)
        
        # Prerequisites and recommendations
        self._show_path_recommendations(path)
    
    def _show_concept_tree(self, path: LearningPath) -> None:
        """Show concepts in a tree structure with dependencies."""
        if not self.console:
            return
            
        tree = Tree(
            f"[bold cyan]📈 Learning Progression[/bold cyan]",
            style="cyan"
        )
        
        for i, concept in enumerate(path.concepts, 1):
            # Determine concept status
            if concept.id in self.user_progress.completed_concepts:
                status_icon = "✅"
                status_color = "green"
            elif concept.id in self.user_progress.in_progress_concepts:
                status_icon = "🔄"
                status_color = "yellow"
            else:
                status_icon = "⏳"
                status_color = "white"
            
            # Create concept node
            concept_text = f"[{status_color}]{status_icon} {concept.name}[/{status_color}]"
            if concept.estimated_time_minutes:
                concept_text += f" [dim]({concept.estimated_time_minutes}min)[/dim]"
            
            concept_branch = tree.add(concept_text)
            
            # Add concept details
            concept_branch.add(f"[dim]{concept.description}[/dim]")
            
            # Add prerequisites if any
            if concept.prerequisites:
                prereq_text = f"[yellow]Prerequisites:[/yellow] {', '.join(concept.prerequisites)}"
                concept_branch.add(prereq_text)
            
            # Add learning resources available
            resources = []
            if concept.quiz_questions:
                resources.append(f"{len(concept.quiz_questions)} quizzes")
            if concept.code_challenges:
                resources.append(f"{len(concept.code_challenges)} challenges")
            if concept.tutorial_stages:
                resources.append(f"{len(concept.tutorial_stages)} tutorials")
            
            if resources:
                concept_branch.add(f"[cyan]Resources:[/cyan] {', '.join(resources)}")
        
        self.console.print()
        self.console.print(tree)
    
    def _show_path_recommendations(self, path: LearningPath) -> None:
        """Show recommendations for the learning path."""
        if not self.console:
            return
            
        recommendations = []
        
        # Check prerequisites
        missing_prereqs = set()
        for concept in path.concepts:
            for prereq_id in concept.prerequisites:
                if prereq_id not in self.user_progress.completed_concepts:
                    missing_prereqs.add(prereq_id)
        
        if missing_prereqs:
            prereq_names = [
                self.concepts_db[prereq_id].name 
                for prereq_id in missing_prereqs 
                if prereq_id in self.concepts_db
            ]
            recommendations.append(
                f"📋 Complete these concepts first: {', '.join(prereq_names[:3])}"
            )
        
        # Time recommendations
        if path.estimated_total_time > 120:
            recommendations.append(
                "⏰ This is a substantial learning path. Consider breaking it into weekly sessions."
            )
        
        # Skill level recommendations
        if path.skill_level.value != self.user_progress.current_skill_level.value:
            if path.skill_level == SkillLevel.ADVANCED and self.user_progress.current_skill_level == SkillLevel.BEGINNER:
                recommendations.append(
                    "⚠️  This path may be challenging. Consider starting with 'Django Performance Fundamentals' first."
                )
        
        # Show recommendations
        if recommendations:
            recommendations_text = "\n".join([f"• {rec}" for rec in recommendations])
            rec_panel = Panel(
                Text.from_markup(
                    f"[bold yellow]💡 Recommendations[/bold yellow]\n\n"
                    f"{recommendations_text}\n\n"
                    f"[italic]These suggestions can help you get the most out of this learning path.[/italic]"
                ),
                border_style="yellow",
                title="Guidance",
                padding=(1, 2)
            )
            self.console.print(rec_panel)
    
    def _show_text_path_details(self, path: LearningPath) -> None:
        """Show path details in plain text mode."""
        print(f"\n📚 {path.name}")
        print("=" * 60)
        print(f"Description: {path.description}")
        print(f"Level: {path.skill_level.value.title()}")
        print(f"Time: {path.estimated_total_time} minutes")
        print(f"Concepts: {len(path.concepts)}")
        print("\nConcept Progression:")
        print("-" * 40)
        
        for i, concept in enumerate(path.concepts, 1):
            status = "✅" if concept.id in self.user_progress.completed_concepts else "⏳"
            print(f"{i}. {status} {concept.name} ({concept.estimated_time_minutes}min)")
            if concept.prerequisites:
                print(f"   Prerequisites: {', '.join(concept.prerequisites)}")
    
    def start_learning_path(self, path_id: str) -> bool:
        """Start a learning path and return the first concept to work on."""
        if path_id not in self.learning_paths:
            return False
        
        path = self.learning_paths[path_id]
        
        # Find the first incomplete concept
        for concept in path.concepts:
            if concept.id not in self.user_progress.completed_concepts:
                self.user_progress.in_progress_concepts.add(concept.id)
                
                if self.console:
                    start_panel = Panel(
                        Text.from_markup(
                            f"[bold green]🚀 Starting Learning Path: {path.name}[/bold green]\n\n"
                            f"[yellow]First Concept:[/yellow] {concept.name}\n"
                            f"[yellow]Estimated Time:[/yellow] {concept.estimated_time_minutes} minutes\n\n"
                            f"[white]{concept.description}[/white]\n\n"
                            f"[italic]Let's begin your journey to Django performance mastery![/italic]"
                        ),
                        border_style="green",
                        padding=(1, 2)
                    )
                    self.console.print(start_panel)
                else:
                    print(f"\n🚀 Starting: {path.name}")
                    print(f"First concept: {concept.name}")
                    print(f"Time: {concept.estimated_time_minutes} minutes")
                
                return True
        
        # All concepts completed
        if self.console:
            self.console.print(f"[green]✅ You've already completed all concepts in '{path.name}'![/green]")
        else:
            print(f"✅ You've already completed '{path.name}'!")
        
        return False
    
    def get_user_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of user progress across all learning paths."""
        summary = {
            'total_concepts': len(self.concepts_db),
            'completed_concepts': len(self.user_progress.completed_concepts),
            'in_progress_concepts': len(self.user_progress.in_progress_concepts),
            'mastered_concepts': len(self.user_progress.mastered_concepts),
            'current_skill_level': self.user_progress.current_skill_level.value,
            'total_time_spent': self.user_progress.time_spent_minutes,
            'completion_percentage': (
                len(self.user_progress.completed_concepts) / len(self.concepts_db) * 100
                if self.concepts_db else 0
            ),
            'paths_progress': {}
        }
        
        # Calculate progress for each path
        for path_id, path in self.learning_paths.items():
            completed = sum(
                1 for concept in path.concepts
                if concept.id in self.user_progress.completed_concepts
            )
            summary['paths_progress'][path_id] = {
                'name': path.name,
                'completed_concepts': completed,
                'total_concepts': len(path.concepts),
                'completion_percentage': (completed / len(path.concepts) * 100) if path.concepts else 0
            }
        
        return summary
    
    def save_progress(self, file_path: Optional[str] = None) -> None:
        """Save user progress to file."""
        if file_path is None:
            # Use default location
            home_path = Path.home()
            mercury_dir = home_path / '.django_mercury'
            mercury_dir.mkdir(exist_ok=True)
            file_path = str(mercury_dir / 'learning_progress.json')
        
        progress_data = {
            'user_id': self.user_progress.user_id,
            'completed_concepts': list(self.user_progress.completed_concepts),
            'in_progress_concepts': list(self.user_progress.in_progress_concepts),
            'mastered_concepts': list(self.user_progress.mastered_concepts),
            'current_skill_level': self.user_progress.current_skill_level.value,
            'time_spent_minutes': self.user_progress.time_spent_minutes,
            'quiz_scores': self.user_progress.quiz_scores,
            'challenge_completions': self.user_progress.challenge_completions,
            'learning_preferences': self.user_progress.learning_preferences
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            if self.console:
                self.console.print(f"[red]❌ Failed to save progress: {e}[/red]")
            else:
                print(f"❌ Failed to save progress: {e}")
    
    def load_progress(self, file_path: Optional[str] = None) -> bool:
        """Load user progress from file."""
        if file_path is None:
            home_path = Path.home()
            file_path = str(home_path / '.django_mercury' / 'learning_progress.json')
        
        try:
            with open(file_path, 'r') as f:
                progress_data = json.load(f)
            
            self.user_progress.user_id = progress_data.get('user_id', 'default')
            self.user_progress.completed_concepts = set(progress_data.get('completed_concepts', []))
            self.user_progress.in_progress_concepts = set(progress_data.get('in_progress_concepts', []))
            self.user_progress.mastered_concepts = set(progress_data.get('mastered_concepts', []))
            self.user_progress.current_skill_level = SkillLevel(
                progress_data.get('current_skill_level', 'beginner')
            )
            self.user_progress.time_spent_minutes = progress_data.get('time_spent_minutes', 0)
            self.user_progress.quiz_scores = progress_data.get('quiz_scores', {})
            self.user_progress.challenge_completions = progress_data.get('challenge_completions', {})
            self.user_progress.learning_preferences = progress_data.get('learning_preferences', {})
            
            return True
            
        except FileNotFoundError:
            # First time user, start fresh
            return True
        except Exception as e:
            if self.console:
                self.console.print(f"[red]❌ Failed to load progress: {e}[/red]")
            else:
                print(f"❌ Failed to load progress: {e}")
            return False