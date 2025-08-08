"""Educational guidance and color schemes for Django Mercury.

This module provides educational content formatting and color schemes
for the interactive learning experience.
"""

from typing import Dict, Optional


class EduLiteColorScheme:
    """Color scheme for educational output following EduLite branding."""
    
    def __init__(self):
        """Initialize the EduLite color scheme."""
        # Define colors for different message types
        self.colors = {
            'success': '#75a743',  # Green
            'warning': '#de9e41',  # Orange
            'error': '#a53030',    # Red
            'info': '#4f8fba',     # Blue
            'excellent': '#73bed3', # Light blue
            'educational': '#f4c430', # Gold/yellow for learning moments
        }
        
        # ANSI color codes for terminal output
        self.ansi_colors = {
            'success': '\033[32m',    # Green
            'warning': '\033[33m',    # Yellow
            'error': '\033[31m',      # Red
            'info': '\033[34m',       # Blue
            'excellent': '\033[36m',  # Cyan
            'educational': '\033[93m', # Bright yellow
            'reset': '\033[0m',       # Reset
            'bold': '\033[1m',        # Bold
        }
    
    def colorize(self, text: str, color_type: str = 'info', bold: bool = False) -> str:
        """Apply color to text for terminal output.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply
            bold: Whether to make text bold
            
        Returns:
            Colorized text string
        """
        if color_type not in self.ansi_colors:
            return text
            
        color_code = self.ansi_colors[color_type]
        if bold:
            color_code = self.ansi_colors['bold'] + color_code
            
        return f"{color_code}{text}{self.ansi_colors['reset']}"
    
    def get_hex_color(self, color_type: str) -> Optional[str]:
        """Get hex color code for a given type.
        
        Args:
            color_type: Type of color
            
        Returns:
            Hex color code or None if not found
        """
        return self.colors.get(color_type)
    
    def format_educational_header(self, title: str) -> str:
        """Format a header for educational content.
        
        Args:
            title: Title text
            
        Returns:
            Formatted header string
        """
        border = "=" * 60
        return f"\n{self.colorize(border, 'educational')}\n{self.colorize(title, 'educational', bold=True)}\n{self.colorize(border, 'educational')}\n"
    
    def format_success_message(self, message: str) -> str:
        """Format a success message.
        
        Args:
            message: Success message text
            
        Returns:
            Formatted success message
        """
        return self.colorize(f"✅ {message}", 'success', bold=True)
    
    def format_warning_message(self, message: str) -> str:
        """Format a warning message.
        
        Args:
            message: Warning message text
            
        Returns:
            Formatted warning message
        """
        return self.colorize(f"⚠️  {message}", 'warning', bold=True)
    
    def format_error_message(self, message: str) -> str:
        """Format an error message.
        
        Args:
            message: Error message text
            
        Returns:
            Formatted error message
        """
        return self.colorize(f"❌ {message}", 'error', bold=True)
    
    def format_info_message(self, message: str) -> str:
        """Format an informational message.
        
        Args:
            message: Info message text
            
        Returns:
            Formatted info message
        """
        return self.colorize(f"ℹ️  {message}", 'info')
    
    def format_quiz_prompt(self, question: str, options: list) -> str:
        """Format a quiz question with options.
        
        Args:
            question: Quiz question text
            options: List of answer options
            
        Returns:
            Formatted quiz prompt
        """
        formatted = self.colorize("🤔 Quick Check:", 'educational', bold=True)
        formatted += f"\n{question}\n\n"
        for i, option in enumerate(options, 1):
            formatted += f"  [{i}] {option}\n"
        return formatted


class EducationalContentProvider:
    """Provides educational content for different performance issues."""
    
    def __init__(self):
        """Initialize the content provider."""
        self.content_db = {
            'n_plus_one': {
                'title': 'N+1 Query Problem',
                'explanation': 'Your code makes 1 query to get a list, then N queries for related data.',
                'impact': 'This creates N+1 total queries, making your app slow.',
                'solution': 'Use select_related() for ForeignKey or prefetch_related() for ManyToMany.',
                'example': '''# ❌ Bad: Creates N+1 queries
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # Each access = 1 query

# ✅ Good: Only 2 queries total  
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No additional queries

# ✅ For reverse relationships
users = User.objects.prefetch_related('posts').all()
for user in users:
    print(user.posts.count())  # Efficient access''',
            },
            'slow_response': {
                'title': 'Slow Response Time',
                'explanation': 'Your view takes too long to respond to requests.',
                'impact': 'Users experience delays and may abandon your app.',
                'solution': 'Add database indexes, optimize queries, or implement caching.',
                'example': '''# ❌ Bad: No database index for filtering
class PostViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Post.objects.filter(created_at__gte=last_week)

# ✅ Good: Add database index in model
class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),  # Speeds up date filtering
            models.Index(fields=['author', 'created_at']),  # Composite index
        ]

# ✅ Even better: Optimize the queryset too
class PostViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Post.objects.select_related('author')\
            .filter(created_at__gte=last_week)\
            .only('title', 'author__name', 'created_at')''',
            },
            'high_memory': {
                'title': 'High Memory Usage',
                'explanation': 'Your code loads too much data into memory at once.',
                'impact': 'Can cause server crashes and increased hosting costs.',
                'solution': 'Use iterator() for large querysets or implement pagination.',
                'example': '''# ❌ Bad: Loads everything into memory
def export_users():
    users = User.objects.all()  # Loads ALL users at once
    for user in users:
        export_user_data(user)

# ✅ Good: Process in chunks
def export_users():
    users = User.objects.all().iterator(chunk_size=1000)
    for user in users:  # Processes 1000 at a time
        export_user_data(user)

# ✅ For specific fields only
def get_user_emails():
    return User.objects.values_list('email', flat=True)\
        .iterator(chunk_size=2000)  # Lightweight data only

# ✅ With pagination for APIs
class UserViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = User.objects.select_related('profile')''',
            },
            'missing_cache': {
                'title': 'Missing Cache Optimization',
                'explanation': 'Your code repeatedly computes the same expensive operations.',
                'impact': 'Wastes server resources and slows down responses.',
                'solution': 'Implement caching with Redis or Memcached.',
                'example': '''# ❌ Bad: Expensive calculation every time
def get_user_stats(user_id):
    user = User.objects.get(id=user_id)
    post_count = user.posts.count()  # Database hit every time
    return {"posts": post_count}

# ✅ Good: Cache expensive operations
from django.core.cache import cache

def get_user_stats(user_id):
    cache_key = f"user_stats_{user_id}"
    stats = cache.get(cache_key)
    
    if stats is None:
        user = User.objects.get(id=user_id)
        post_count = user.posts.count()
        stats = {"posts": post_count}
        cache.set(cache_key, stats, timeout=3600)  # Cache for 1 hour
    
    return stats

# ✅ Fragment caching in templates
{% load cache %}
{% cache 500 user_posts user.id %}
    <!-- Expensive template rendering -->
    {% for post in user.posts.all %}
        {{ post.title }}
    {% endfor %}
{% endcache %}

# ✅ Advanced: Cache invalidation
def invalidate_user_cache(user_id):
    cache_keys = [
        f"user_stats_{user_id}",
        f"user_posts_{user_id}",
    ]
    cache.delete_many(cache_keys)''',
            },
            
            # NEW ENHANCED EXAMPLES
            'advanced_query_optimization': {
                'title': 'Advanced Query Optimization',
                'explanation': 'Complex nested relationships require sophisticated prefetching strategies.',
                'impact': 'Poor optimization can cause exponential query growth in complex views.',
                'solution': 'Combine select_related(), prefetch_related(), and Prefetch objects strategically.',
                'example': '''# ❌ Bad: Creates massive N+1 queries
def get_company_data():
    companies = Company.objects.all()
    for company in companies:
        for employee in company.employees.all():  # N+1 here
            print(employee.profile.bio)  # And here
            for project in employee.projects.all():  # And here
                print(project.tasks.count())  # And here!

# ✅ Good: Strategic prefetching
from django.db.models import Prefetch

def get_company_data():
    companies = Company.objects.prefetch_related(
        # Nested prefetch with optimization
        Prefetch(
            'employees',
            queryset=Employee.objects.select_related('profile')\
                .prefetch_related(
                    Prefetch(
                        'projects',
                        queryset=Project.objects.prefetch_related('tasks')
                    )
                )
        )
    ).all()
    
    # Now all data is efficiently loaded
    for company in companies:
        for employee in company.employees.all():  # No queries
            print(employee.profile.bio)  # No queries  
            for project in employee.projects.all():  # No queries
                print(project.tasks.count())  # No queries!

# ✅ Advanced: Conditional prefetching
def get_active_company_data():
    companies = Company.objects.prefetch_related(
        Prefetch(
            'employees',
            queryset=Employee.objects.filter(is_active=True)\
                .select_related('profile')\
                .prefetch_related(
                    Prefetch(
                        'projects', 
                        queryset=Project.objects.filter(status='active')\
                            .prefetch_related('tasks')
                    )
                ),
            to_attr='active_employees'  # Custom attribute name
        )
    ).all()''',
            },
            
            'serialization_optimization': {
                'title': 'DRF Serialization Performance',
                'explanation': 'Serializers can create hidden N+1 queries and performance bottlenecks.',
                'impact': 'API endpoints become slow as data size increases.',
                'solution': 'Optimize serializers with annotations, prefetching, and efficient patterns.',
                'example': '''# ❌ Bad: SerializerMethodField with queries
class AuthorSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()
    
    def get_post_count(self, obj):
        return obj.posts.count()  # Query for each author!
    
    class Meta:
        model = Author
        fields = ['name', 'email', 'post_count']

# ✅ Good: Use database annotations
class AuthorListView(generics.ListAPIView):
    serializer_class = AuthorSerializer
    
    def get_queryset(self):
        return Author.objects.annotate(
            post_count=Count('posts')  # Calculated in database
        )

class AuthorSerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Author  
        fields = ['name', 'email', 'post_count']

# ✅ Advanced: Nested serializer optimization
class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name')
    category_name = serializers.CharField(source='category.name')
    
    class Meta:
        model = Post
        fields = ['title', 'author_name', 'category_name']

class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    
    def get_queryset(self):
        return Post.objects.select_related('author', 'category')\
            .only('title', 'author__name', 'category__name')

# ✅ Complex nested with prefetch
class AuthorDetailSerializer(serializers.ModelSerializer):
    recent_posts = PostSerializer(many=True, read_only=True)
    
    class Meta:
        model = Author
        fields = ['name', 'email', 'recent_posts']

class AuthorDetailView(generics.RetrieveAPIView):
    serializer_class = AuthorDetailSerializer
    
    def get_queryset(self):
        return Author.objects.prefetch_related(
            Prefetch(
                'posts',
                queryset=Post.objects.select_related('category')\
                    .filter(created_at__gte=timezone.now() - timedelta(days=30))\
                    .order_by('-created_at')[:5],
                to_attr='recent_posts'
            )
        )''',
            },
            
            'api_optimization': {
                'title': 'API Performance Patterns',
                'explanation': 'APIs need specific optimization patterns for pagination, filtering, and caching.',
                'impact': 'Poor API design leads to slow responses and high server load.',
                'solution': 'Implement efficient pagination, filtering, and response optimization.',
                'example': '''# ❌ Bad: No pagination, inefficient queries
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()  # Returns everything!
    serializer_class = PostSerializer
    
    def list(self, request):
        posts = self.get_queryset()
        for post in posts:
            post.view_count += 1  # N+1 update queries!
            post.save()
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

# ✅ Good: Optimized API with pagination
from django.core.paginator import Paginator
from django.core.cache import cache

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'view_count']
    
    def get_queryset(self):
        return Post.objects.select_related('author', 'category')\
            .prefetch_related('tags')\
            .order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        cache_key = 'trending_posts'
        trending = cache.get(cache_key)
        
        if trending is None:
            trending = self.get_queryset()\
                .filter(created_at__gte=timezone.now() - timedelta(days=7))\
                .order_by('-view_count')[:10]
            cache.set(cache_key, trending, timeout=1800)  # 30 min cache
        
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)

# ✅ Advanced: Cursor pagination for large datasets
from rest_framework.pagination import CursorPagination

class PostCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'  # Must be unique and indexed
    cursor_query_param = 'cursor'

class PostViewSet(viewsets.ModelViewSet):
    pagination_class = PostCursorPagination  # Consistent performance
    
    def get_queryset(self):
        queryset = Post.objects.select_related('author')
        
        # Conditional prefetching based on request
        if 'include_comments' in self.request.query_params:
            queryset = queryset.prefetch_related('comments__author')
        
        return queryset''',
            },
            
            'memory_management': {
                'title': 'Memory Management Patterns',
                'explanation': 'Efficient memory usage prevents server crashes and reduces hosting costs.',
                'impact': 'Memory leaks and inefficient usage can crash servers under load.',
                'solution': 'Use streaming, chunking, and efficient data structures.',
                'example': '''# ❌ Bad: Memory-intensive operations
def export_all_users():
    users = User.objects.all()  # Loads everything
    data = []
    for user in users:
        user_data = {
            'profile': user.profile,  # More objects in memory
            'posts': list(user.posts.all()),  # Even more!
            'comments': list(user.comments.all()),  # Memory explosion!
        }
        data.append(user_data)
    return JsonResponse({'users': data})

# ✅ Good: Memory-efficient streaming
def export_users_stream():
    def generate():
        yield '{"users": ['
        first = True
        
        for user in User.objects.iterator(chunk_size=100):
            if not first:
                yield ','
            first = False
            
            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            }
            yield json.dumps(user_data)
        
        yield ']}'
    
    return StreamingHttpResponse(
        generate(),
        content_type='application/json'
    )

# ✅ Advanced: Values-only queries for large exports
def export_user_emails():
    # Only load email field, not full objects
    emails = User.objects.values_list('email', flat=True)\
        .iterator(chunk_size=5000)
    
    def generate():
        yield '['
        first = True
        for email in emails:
            if not first:
                yield ','
            first = False
            yield f'"{email}"'
        yield ']'
    
    return StreamingHttpResponse(generate())

# ✅ Bulk operations instead of loops
def update_user_stats():
    # ❌ Bad: N queries
    for user in User.objects.all():
        user.post_count = user.posts.count()
        user.save()
    
    # ✅ Good: Single query with annotation
    User.objects.update(
        post_count=Subquery(
            User.objects.filter(id=OuterRef('id'))
            .annotate(count=Count('posts'))
            .values('count')
        )
    )''',
            },
            
            'advanced_caching': {
                'title': 'Advanced Caching Strategies',
                'explanation': 'Sophisticated caching patterns for high-performance applications.',
                'impact': 'Proper caching can reduce database load by 90%+ and dramatically improve response times.',
                'solution': 'Implement multi-level caching with smart invalidation strategies.',
                'example': '''# ❌ Bad: No caching strategy
def get_dashboard_data(user):
    stats = calculate_user_stats(user)  # Expensive
    notifications = get_notifications(user)  # Database query
    activity = get_recent_activity(user)  # Another query
    return {
        'stats': stats,
        'notifications': notifications,
        'activity': activity,
    }

# ✅ Good: Multi-level caching
from django.core.cache import cache
from functools import wraps

def cache_per_user(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            cache_key = f"{func.__name__}:user:{user.id}"
            result = cache.get(cache_key)
            
            if result is None:
                result = func(user, *args, **kwargs)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

@cache_per_user(timeout=600)  # 10 minute cache
def get_user_stats(user):
    return {
        'posts': user.posts.count(),
        'followers': user.followers.count(),
        'reputation': calculate_reputation(user),
    }

def get_dashboard_data(user):
    # Multi-level caching approach
    cache_key = f"dashboard:user:{user.id}"
    data = cache.get(cache_key)
    
    if data is None:
        # Each component cached separately
        stats = get_user_stats(user)  # Cached separately
        notifications = get_cached_notifications(user)
        activity = get_cached_activity(user)
        
        data = {
            'stats': stats,
            'notifications': notifications,
            'activity': activity,
        }
        
        # Cache the combined result too
        cache.set(cache_key, data, timeout=180)  # 3 minutes
    
    return data

# ✅ Advanced: Cache invalidation patterns
class UserCacheManager:
    @staticmethod
    def invalidate_user_caches(user_id):
        patterns = [
            f"dashboard:user:{user_id}",
            f"get_user_stats:user:{user_id}",
            f"notifications:user:{user_id}",
            f"activity:user:{user_id}",
        ]
        cache.delete_many(patterns)
    
    @staticmethod
    def invalidate_related_caches(user_id):
        # Invalidate caches that depend on this user
        user = User.objects.get(id=user_id)
        
        # Invalidate follower caches
        for follower in user.followers.all():
            cache.delete(f"dashboard:user:{follower.id}")
        
        # Invalidate group caches
        for group in user.groups.all():
            cache.delete(f"group_stats:{group.id}")

# ✅ Cache stampede prevention
import time
import random

def get_with_lock(key, func, timeout=300, lock_timeout=60):
    """Prevent cache stampede with distributed locks."""
    result = cache.get(key)
    
    if result is None:
        lock_key = f"{key}:lock"
        
        # Try to acquire lock
        if cache.add(lock_key, "locked", lock_timeout):
            try:
                # We got the lock, calculate the value
                result = func()
                cache.set(key, result, timeout)
            finally:
                cache.delete(lock_key)
        else:
            # Someone else is calculating, wait briefly and try again
            time.sleep(random.uniform(0.1, 0.5))
            result = cache.get(key)
            
            if result is None:
                # Still no result, just calculate it
                result = func()
    
    return result''',
            },
        }
    
    def get_content(self, issue_type: str) -> Dict[str, str]:
        """Get educational content for a specific issue type.
        
        Args:
            issue_type: Type of performance issue
            
        Returns:
            Dictionary with educational content
        """
        return self.content_db.get(issue_type, {
            'title': 'Performance Issue',
            'explanation': 'A performance issue was detected.',
            'impact': 'This may affect your application performance.',
            'solution': 'Review the specific issue details for guidance.',
            'example': '',
        })
    
    def format_educational_content(self, issue_type: str, color_scheme: Optional[EduLiteColorScheme] = None) -> str:
        """Format educational content for display.
        
        Args:
            issue_type: Type of performance issue
            color_scheme: Optional color scheme to use
            
        Returns:
            Formatted educational content string
        """
        if color_scheme is None:
            color_scheme = EduLiteColorScheme()
            
        content = self.get_content(issue_type)
        
        formatted = color_scheme.format_educational_header(f"📚 Learning Moment: {content['title']}")
        formatted += f"\n{color_scheme.colorize('What happened:', 'info', bold=True)}\n{content['explanation']}\n"
        formatted += f"\n{color_scheme.colorize('Why it matters:', 'warning', bold=True)}\n{content['impact']}\n"
        formatted += f"\n{color_scheme.colorize('How to fix:', 'success', bold=True)}\n{content['solution']}\n"
        
        if content['example']:
            formatted += f"\n{color_scheme.colorize('Example:', 'excellent', bold=True)}\n{content['example']}\n"
            
        return formatted