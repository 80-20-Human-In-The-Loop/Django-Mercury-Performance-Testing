"""
Comprehensive Usage Examples for Django Mercury Educational Mode

This file demonstrates practical usage scenarios for the Django Mercury
educational system, showing how it helps developers learn performance
optimization through real-world examples.

Run with: python manage.py test --edu examples.educational_examples
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rest_framework.test import APITestCase
from rest_framework import serializers
from typing import Dict, Any

# Example models for educational demonstrations
class Author(models.Model):
    """Example author model for N+1 query demonstrations."""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),  # Good indexing example
        ]


class Category(models.Model):
    """Example category model for relationship optimization."""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    

class Post(models.Model):
    """Example post model demonstrating various optimization scenarios."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    tags = models.ManyToManyField('Tag', related_name='posts', blank=True)
    view_count = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at', 'is_published']),  # Composite index
            models.Index(fields=['view_count']),  # For popular posts
        ]


class Tag(models.Model):
    """Example tag model for many-to-many optimization."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)


class Comment(models.Model):
    """Example comment model for nested relationship optimization."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)


# Import Mercury test case - will use educational features if --edu flag is present
try:
    from django_mercury import DjangoMercuryAPITestCase
    MERCURY_AVAILABLE = True
except ImportError:
    # Fallback for when Mercury isn't installed
    DjangoMercuryAPITestCase = APITestCase
    MERCURY_AVAILABLE = False


class BeginnerN1QueryExamples(DjangoMercuryAPITestCase):
    """
    Beginner-level examples demonstrating N+1 query problems.
    
    These examples will trigger educational interventions when run with --edu flag,
    helping developers understand the most common Django performance issues.
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if MERCURY_AVAILABLE:
            # Configure for educational mode with beginner thresholds
            cls.set_performance_thresholds({
                'response_time_ms': 100,     # Strict for learning
                'query_count_max': 5,        # Very low to trigger N+1 detection
                'memory_overhead_mb': 20,    # Reasonable memory limit
            })
    
    def setUp(self):
        """Set up test data that will expose N+1 problems."""
        # Create test data
        self.authors = []
        for i in range(10):
            author = Author.objects.create(
                name=f"Author {i}",
                email=f"author{i}@example.com",
                bio=f"Biography for author {i}"
            )
            self.authors.append(author)
        
        self.category = Category.objects.create(
            name="Technology",
            description="Tech-related posts"
        )
        
        # Create posts for each author
        for author in self.authors:
            for j in range(3):
                Post.objects.create(
                    title=f"Post {j} by {author.name}",
                    content=f"Content for post {j}",
                    author=author,
                    category=self.category,
                    view_count=j * 10
                )
    
    def test_classic_n_plus_one_problem(self):
        """
        Classic N+1 query problem: Loading posts and accessing author info.
        
        Educational Learning Goals:
        - Recognize N+1 query patterns
        - Understand the performance impact
        - Learn when to use select_related()
        
        Expected Educational Intervention:
        - Mercury will detect 31+ queries (1 for posts + 30 for authors)
        - Interactive quiz about N+1 problem recognition
        - Code challenge to fix with select_related()
        """
        
        # This will create an N+1 query problem
        # 1 query to get posts + N queries to get each author
        posts = Post.objects.all()  # 1 query
        
        authors_info = []
        for post in posts:  # This loop triggers N queries (30 queries)
            authors_info.append({
                'post_title': post.title,
                'author_name': post.author.name,  # Query for each author!
                'author_email': post.author.email  # Same query repeated
            })
        
        # Mercury will detect this and provide educational guidance
        self.assertGreater(len(authors_info), 0)
    
    def test_fixed_n_plus_one_with_select_related(self):
        """
        Optimized version using select_related() to eliminate N+1 queries.
        
        Educational Learning Goals:
        - Learn select_related() syntax and usage
        - See dramatic query reduction (30+ queries → 1 query)
        - Understand foreign key optimization patterns
        
        Expected Educational Intervention:
        - Mercury will detect only 1 query
        - Performance comparison with previous test
        - Congratulatory message for good optimization
        """
        
        # Optimized version - only 1 query total
        posts = Post.objects.select_related('author').all()
        
        authors_info = []
        for post in posts:  # No additional queries needed!
            authors_info.append({
                'post_title': post.title,
                'author_name': post.author.name,      # No query - already loaded
                'author_email': post.author.email     # No query - already loaded
            })
        
        self.assertGreater(len(authors_info), 0)
        # Mercury should give this an excellent performance score
    
    def test_many_to_many_n_plus_one_problem(self):
        """
        N+1 problem with many-to-many relationships.
        
        Educational Learning Goals:
        - Understand that N+1 affects many-to-many relationships too
        - Learn when select_related() doesn't work
        - Introduction to prefetch_related() concept
        """
        
        # Create some tags and assign them to posts
        tags = [
            Tag.objects.create(name=f"Tag {i}", slug=f"tag-{i}")
            for i in range(5)
        ]
        
        # Assign tags to posts
        for i, post in enumerate(Post.objects.all()[:10]):
            post.tags.add(tags[i % len(tags)])
        
        # This creates N+1 queries with many-to-many
        posts = Post.objects.all()[:10]  # 1 query
        
        posts_with_tags = []
        for post in posts:  # N queries for tags
            tag_names = [tag.name for tag in post.tags.all()]  # Query per post!
            posts_with_tags.append({
                'title': post.title,
                'tags': tag_names
            })
        
        # Mercury will detect this many-to-many N+1 pattern
        self.assertGreater(len(posts_with_tags), 0)


class IntermediateOptimizationExamples(DjangoMercuryAPITestCase):
    """
    Intermediate-level optimization examples.
    
    Demonstrates more sophisticated optimization techniques and scenarios.
    """
    
    @classmethod 
    def setUpClass(cls):
        super().setUpClass()
        if MERCURY_AVAILABLE:
            cls.set_performance_thresholds({
                'response_time_ms': 75,      # Stricter for intermediate level  
                'query_count_max': 8,        # Allow a few more queries
                'memory_overhead_mb': 30,    # Higher memory operations
            })
    
    def setUp(self):
        """Set up more complex test scenarios."""
        # Create test data with nested relationships
        self.authors = Author.objects.bulk_create([
            Author(name=f"Author {i}", email=f"author{i}@example.com")
            for i in range(15)
        ])
        
        self.categories = Category.objects.bulk_create([
            Category(name=f"Category {i}", description=f"Description {i}")
            for i in range(5)
        ])
        
        # Create posts with relationships
        posts = []
        for i, author in enumerate(self.authors):
            for j in range(4):  # 60 posts total
                posts.append(Post(
                    title=f"Post {j} by {author.name}",
                    content=f"Content for post {j}" * 50,  # Larger content
                    author=author,
                    category=self.categories[i % len(self.categories)],
                    view_count=(i * j) + 10
                ))
        
        Post.objects.bulk_create(posts)
    
    def test_memory_optimization_with_only(self):
        """
        Demonstrate memory optimization using only() for large datasets.
        
        Educational Learning Goals:
        - Understand memory impact of loading full model instances
        - Learn only() for selective field loading
        - See memory usage reduction in practice
        """
        
        # Memory-inefficient approach - loads all fields
        posts_full = list(Post.objects.all())  # Loads all fields including large content
        
        # Memory-efficient approach - only needed fields
        posts_optimized = list(Post.objects.only('title', 'view_count', 'created_at').all())
        
        # Mercury will measure memory usage and show the difference
        self.assertEqual(len(posts_full), len(posts_optimized))
    
    def test_values_optimization_for_api_responses(self):
        """
        Using values() for efficient API data preparation.
        
        Educational Learning Goals:
        - Learn values() for lightweight data extraction
        - Understand when to avoid full model instances
        - API response optimization patterns
        """
        
        # Efficient API data preparation
        api_data = Post.objects.select_related('author', 'category').values(
            'title',
            'author__name', 
            'category__name',
            'view_count',
            'created_at'
        )
        
        # Mercury will recognize this as an optimized pattern
        results = list(api_data)
        self.assertGreater(len(results), 0)
        
        # Verify we have the expected fields
        if results:
            expected_fields = {'title', 'author__name', 'category__name', 'view_count', 'created_at'}
            self.assertEqual(set(results[0].keys()), expected_fields)
    
    def test_complex_prefetch_optimization(self):
        """
        Advanced prefetch_related() with custom querysets.
        
        Educational Learning Goals:
        - Learn Prefetch objects for advanced optimization
        - Understand conditional prefetching
        - Master nested relationship optimization
        """
        from django.db.models import Prefetch
        
        # Create comments for some posts
        posts_with_comments = Post.objects.all()[:10]
        for post in posts_with_comments:
            for i in range(3):
                Comment.objects.create(
                    post=post,
                    author=post.author,
                    content=f"Comment {i} on {post.title}"
                )
        
        # Advanced prefetch with custom queryset
        posts = Post.objects.select_related('author', 'category').prefetch_related(
            Prefetch(
                'comments',
                queryset=Comment.objects.select_related('author').order_by('-created_at')[:5],
                to_attr='recent_comments'
            )
        ).all()[:10]
        
        # Access the optimized data
        posts_data = []
        for post in posts:
            posts_data.append({
                'title': post.title,
                'author': post.author.name,
                'category': post.category.name,
                'comment_count': len(post.recent_comments),
                'latest_comments': [
                    f"{comment.author.name}: {comment.content[:50]}"
                    for comment in post.recent_comments
                ]
            })
        
        # Mercury will recognize this sophisticated optimization
        self.assertGreater(len(posts_data), 0)


class AdvancedPerformanceExamples(DjangoMercuryAPITestCase):
    """
    Advanced optimization examples for expert-level learning.
    
    Demonstrates sophisticated patterns and edge cases.
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if MERCURY_AVAILABLE:
            cls.set_performance_thresholds({
                'response_time_ms': 50,      # Very strict for advanced level
                'query_count_max': 5,        # Demanding query efficiency
                'memory_overhead_mb': 25,    # Tight memory constraints
            })
    
    def test_annotation_optimization(self):
        """
        Using database annotations for computed fields.
        
        Educational Learning Goals:
        - Move calculations to database level
        - Understand annotation performance benefits  
        - Learn complex aggregation patterns
        """
        from django.db.models import Count, Avg, Max
        
        # Efficient database-level calculations
        authors_with_stats = Author.objects.annotate(
            post_count=Count('posts'),
            avg_views=Avg('posts__view_count'),
            max_views=Max('posts__view_count'),
            latest_post=Max('posts__created_at')
        ).filter(
            post_count__gt=0  # Only authors with posts
        ).order_by('-post_count')
        
        # Mercury will recognize this database-efficient pattern
        stats_data = []
        for author in authors_with_stats:
            stats_data.append({
                'name': author.name,
                'posts': author.post_count,           # Computed in database
                'avg_views': author.avg_views,        # Computed in database
                'max_views': author.max_views,        # Computed in database
                'latest_post': author.latest_post     # Computed in database
            })
        
        self.assertGreater(len(stats_data), 0)
    
    def test_bulk_operations_optimization(self):
        """
        Efficient bulk operations for large datasets.
        
        Educational Learning Goals:
        - Learn bulk_create(), bulk_update() patterns
        - Understand batch processing benefits
        - Database-efficient data manipulation
        """
        
        # Create many posts efficiently
        new_posts = []
        author = self.authors[0] if hasattr(self, 'authors') else Author.objects.first()
        category = Category.objects.first()
        
        if author and category:
            for i in range(100):  # Large batch
                new_posts.append(Post(
                    title=f"Bulk Post {i}",
                    content=f"Content for bulk post {i}",
                    author=author,
                    category=category,
                    view_count=i
                ))
            
            # Single database operation instead of 100
            created_posts = Post.objects.bulk_create(new_posts, batch_size=50)
            
            # Mercury will recognize this efficient bulk pattern
            self.assertEqual(len(created_posts), 100)
    
    def test_iterator_for_large_datasets(self):
        """
        Memory-efficient processing of large datasets.
        
        Educational Learning Goals:  
        - Learn iterator() for memory efficiency
        - Understand chunk processing patterns
        - Handle large datasets without memory issues
        """
        
        # Memory-efficient processing of large queryset
        total_views = 0
        processed_count = 0
        
        # iterator() processes in chunks, doesn't cache in memory
        for post in Post.objects.iterator(chunk_size=10):
            total_views += post.view_count
            processed_count += 1
        
        # Mercury will measure memory usage and approve efficiency
        self.assertGreater(processed_count, 0)
        self.assertGreaterEqual(total_views, 0)


class SerializerOptimizationExamples(DjangoMercuryAPITestCase):
    """
    Django REST Framework serialization optimization examples.
    
    Shows how to optimize API serializers for performance.
    """
    
    def setUp(self):
        """Set up test data for serializer examples."""
        # Create test data
        self.author = Author.objects.create(
            name="Test Author",
            email="test@example.com",
            bio="Test biography"
        )
        
        self.category = Category.objects.create(
            name="Test Category",
            description="Test category description"
        )
        
        # Create posts
        self.posts = []
        for i in range(20):
            post = Post.objects.create(
                title=f"Post {i}",
                content=f"Content for post {i}",
                author=self.author,
                category=self.category,
                view_count=i * 10
            )
            self.posts.append(post)
    
    def test_inefficient_serializer_pattern(self):
        """
        Demonstrate inefficient serializer causing N+1 queries.
        
        Educational Learning Goals:
        - Recognize serializer-induced N+1 problems
        - Understand SerializerMethodField performance impact
        - Learn to identify API performance bottlenecks
        """
        
        class InefficientPostSerializer(serializers.ModelSerializer):
            author_name = serializers.SerializerMethodField()
            category_name = serializers.SerializerMethodField()
            
            class Meta:
                model = Post
                fields = ['title', 'content', 'author_name', 'category_name', 'view_count']
            
            def get_author_name(self, obj):
                return obj.author.name  # Causes query per post!
            
            def get_category_name(self, obj):
                return obj.category.name  # Causes query per post!
        
        # This will cause N+1 queries in serialization
        posts = Post.objects.all()[:15]  # 1 query
        serializer = InefficientPostSerializer(posts, many=True)
        serialized_data = serializer.data  # Triggers 30+ additional queries!
        
        # Mercury will detect the serialization N+1 problem
        self.assertEqual(len(serialized_data), 15)
    
    def test_optimized_serializer_pattern(self):
        """
        Optimized serializer with proper prefetching.
        
        Educational Learning Goals:
        - Learn to combine ORM optimization with serializers
        - Understand source parameter optimization
        - Master API performance optimization patterns
        """
        
        class OptimizedPostSerializer(serializers.ModelSerializer):
            author_name = serializers.CharField(source='author.name', read_only=True)
            category_name = serializers.CharField(source='category.name', read_only=True)
            
            class Meta:
                model = Post
                fields = ['title', 'content', 'author_name', 'category_name', 'view_count']
        
        # Optimized queryset with prefetching
        posts = Post.objects.select_related('author', 'category').all()[:15]  # 1 optimized query
        serializer = OptimizedPostSerializer(posts, many=True)
        serialized_data = serializer.data  # No additional queries!
        
        # Mercury will recognize this excellent optimization
        self.assertEqual(len(serialized_data), 15)
        
        # Verify the data structure is correct
        if serialized_data:
            first_post = serialized_data[0]
            required_fields = {'title', 'content', 'author_name', 'category_name', 'view_count'}
            self.assertEqual(set(first_post.keys()), required_fields)


class CachingOptimizationExamples(DjangoMercuryAPITestCase):
    """
    Caching optimization examples for performance improvement.
    
    Demonstrates effective caching strategies.
    """
    
    def test_view_level_caching_simulation(self):
        """
        Simulate view-level caching performance improvement.
        
        Educational Learning Goals:
        - Understand caching performance benefits
        - Learn when and how to implement caching
        - See dramatic performance improvements from caching
        """
        from django.core.cache import cache
        
        # Expensive operation simulation
        def expensive_operation():
            # Simulate complex database operations
            posts = Post.objects.select_related('author', 'category').all()
            return list(posts)
        
        cache_key = 'expensive_posts_operation'
        
        # First call - cache miss (slow)
        cached_result = cache.get(cache_key)
        if cached_result is None:
            result = expensive_operation()  # Expensive
            cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
        else:
            result = cached_result  # Fast cache hit
        
        # Mercury will measure the performance difference
        self.assertIsNotNone(result)
    
    def test_cache_effectiveness_comparison(self):
        """
        Compare cached vs uncached operation performance.
        
        Educational Learning Goals:
        - Measure actual caching performance benefits
        - Understand cache hit ratio importance
        - Learn cache performance monitoring
        """
        
        # Uncached version - always hits database
        uncached_posts = list(Post.objects.select_related('author').all())
        
        # Cached version - hits cache after first time
        from django.core.cache import cache
        cache_key = 'all_posts_with_authors'
        
        cached_posts = cache.get(cache_key)
        if cached_posts is None:
            cached_posts = list(Post.objects.select_related('author').all())
            cache.set(cache_key, cached_posts, timeout=600)
        
        # Mercury will show the performance comparison
        self.assertEqual(len(uncached_posts), len(cached_posts))


# Educational test discovery helper
def get_educational_test_classes():
    """
    Helper function to get all educational example test classes.
    
    Useful for running specific educational scenarios:
    
    Example usage:
        from examples.educational_examples import get_educational_test_classes
        
        # Run beginner examples
        python manage.py test --edu examples.educational_examples.BeginnerN1QueryExamples
        
        # Run all examples
        python manage.py test --edu examples.educational_examples
    """
    return [
        BeginnerN1QueryExamples,
        IntermediateOptimizationExamples, 
        AdvancedPerformanceExamples,
        SerializerOptimizationExamples,
        CachingOptimizationExamples
    ]


if __name__ == '__main__':
    """
    Example usage and educational guidance.
    """
    print("""
    🎓 Django Mercury Educational Examples
    ======================================
    
    These examples demonstrate Django performance optimization through
    the Mercury educational system. Run with --edu flag for interactive learning!
    
    📚 Learning Levels:
    
    Beginner Level:
    - Classic N+1 query problems and solutions
    - Basic select_related() and prefetch_related() usage
    - Understanding query optimization fundamentals
    
    Intermediate Level:
    - Memory optimization with only() and values()
    - Complex prefetch patterns with Prefetch objects
    - API serialization optimization
    
    Advanced Level:
    - Database annotations and aggregations
    - Bulk operations for efficiency
    - Iterator patterns for large datasets
    
    🚀 How to Run:
    
    # Run all educational examples
    python manage.py test --edu examples.educational_examples
    
    # Run specific level
    python manage.py test --edu examples.educational_examples.BeginnerN1QueryExamples
    
    # Run with specific difficulty
    MERCURY_EDU_LEVEL=intermediate python manage.py test --edu examples.educational_examples
    
    💡 Educational Features You'll Experience:
    - Interactive quizzes when performance issues are detected
    - Code challenges to fix optimization problems  
    - Before/after performance comparisons
    - Step-by-step learning tutorials
    - Progress tracking across concepts
    
    📹 Video Tutorials:
    Each example includes placeholder links to video tutorials at:
    https://tutorials.djangomercury.com/
    
    Happy learning! 🎯
    """)