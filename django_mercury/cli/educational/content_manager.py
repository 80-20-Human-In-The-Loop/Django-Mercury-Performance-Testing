"""
Content Manager for Django Mercury Educational Mode

Manages educational content including:
- Performance optimization concepts
- Django best practices
- Testing strategies
- Interactive tutorials
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ContentType(Enum):
    """Types of educational content."""
    CONCEPT = "concept"
    PATTERN = "pattern"
    METRIC = "metric"
    TIP = "tip"
    QUIZ = "quiz"
    TUTORIAL = "tutorial"


@dataclass
class QuizQuestion:
    """Represents a quiz question."""
    question: str
    options: List[str]
    correct_answer: int  # Index of correct option
    explanation: str = ""
    

@dataclass
class EducationalContent:
    """Represents a piece of educational content."""
    id: str
    title: str
    type: ContentType
    brief: str
    detailed: str = ""
    examples: List[str] = field(default_factory=list)
    solutions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    difficulty: str = "beginner"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quiz_questions: List[QuizQuestion] = field(default_factory=list)


class ContentManager:
    """Manages educational content for Django Mercury."""
    
    def __init__(self):
        """Initialize the content manager with built-in content."""
        self.content_db: Dict[str, EducationalContent] = {}
        self._load_builtin_content()
    
    def _load_builtin_content(self):
        """Load built-in educational content."""
        # Performance concepts
        self.add_content(EducationalContent(
            id="n_plus_one",
            title="N+1 Query Problem",
            type=ContentType.CONCEPT,
            brief="Multiple queries for related data that could be fetched in one query",
            detailed="""
The N+1 query problem occurs when your code executes N additional queries 
to fetch related data that could have been retrieved in the original query.

Example:
```python
# Bad: N+1 queries
users = User.objects.all()  # 1 query
for user in users:
    print(user.profile.bio)  # N queries

# Good: 2 queries total
users = User.objects.select_related('profile')
for user in users:
    print(user.profile.bio)  # No additional queries
```
""",
            solutions=[
                "Use select_related() for ForeignKey/OneToOne relationships",
                "Use prefetch_related() for ManyToMany/reverse ForeignKey",
                "Consider using only() or defer() to limit fields",
            ],
            difficulty="intermediate",
            tags=["database", "performance", "orm"],
            quiz_questions=[
                QuizQuestion(
                    question="What is the N+1 query problem?",
                    options=[
                        "Running N queries instead of 1",
                        "Running 1 query to get N objects, then N more queries for related data",
                        "Running N+1 database migrations",
                        "Having N+1 models in your Django app"
                    ],
                    correct_answer=1,
                    explanation="The N+1 problem occurs when you fetch N objects with 1 query, then make N additional queries to get related data for each object."
                ),
                QuizQuestion(
                    question="Which Django method helps prevent N+1 queries for ForeignKey relationships?",
                    options=[
                        "prefetch_related()",
                        "select_related()",
                        "only()",
                        "defer()"
                    ],
                    correct_answer=1,
                    explanation="select_related() performs a SQL join to fetch related ForeignKey/OneToOne objects in a single query."
                ),
                QuizQuestion(
                    question="For a ManyToMany relationship, which method should you use?",
                    options=[
                        "select_related()",
                        "defer()",
                        "prefetch_related()",
                        "annotate()"
                    ],
                    correct_answer=2,
                    explanation="prefetch_related() is used for ManyToMany and reverse ForeignKey relationships, executing separate queries but minimizing total queries."
                )
            ]
        ))
        
        self.add_content(EducationalContent(
            id="test_isolation",
            title="Test Isolation Issues",
            type=ContentType.CONCEPT,
            brief="Tests failing due to shared state between test methods",
            detailed="""
Test isolation issues occur when tests share mutable state and interfere 
with each other. This is especially common with Django's setUpTestData().

The Problem:
- setUpTestData() creates data ONCE for all test methods in a class
- If one test modifies this data, other tests see the changes
- Tests may pass alone but fail when run together

IMPORTANT: The solution is NOT to create all data fresh in each test!
Instead, understand what data needs isolation:
- Immutable/Reference data (Users, Categories) → setUpTestData() ✓
- Mutable/Test subjects (Friend requests, Orders) → setUp() ✓

Example of the problem:
```python
class FriendRequestTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # WRONG: Friend request is mutable!
        cls.friend_request = FriendRequest.objects.create(...)
    
    def test_accept_request(self):
        self.friend_request.accept()  # Modifies shared data!
    
    def test_reject_request(self):
        # FAILS: Request already accepted by previous test
        self.friend_request.reject()
```

The fix:
```python
class FriendRequestTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # GOOD: Users are read-only reference data
        cls.sender = User.objects.create(username='sender')
        cls.receiver = User.objects.create(username='receiver')
    
    def setUp(self):
        # GOOD: Create fresh friend request for each test
        self.friend_request = FriendRequest.objects.create(
            sender=self.sender,
            receiver=self.receiver
        )
```
""",
            solutions=[
                "Use setUpTestData() for read-only reference data only",
                "Use setUp() for data that will be modified during tests",
                "Consider TransactionTestCase for complex state management",
                "Use factory methods to create test-specific instances",
                "Clean up properly in tearDown() if needed"
            ],
            examples=[
                """
# GOOD PATTERN: Separation of concerns
@classmethod
def setUpTestData(cls):
    # Immutable reference data
    cls.admin_user = User.objects.create_superuser('admin')
    cls.category = Category.objects.create(name='Electronics')
    cls.permissions = Permission.objects.filter(...)

def setUp(self):
    super().setUp()
    # Mutable test subjects
    self.product = Product.objects.create(
        category=self.category,
        name='Test Product'
    )
    self.order = Order.objects.create(user=self.admin_user)
""",
                """
# For complex scenarios, use TransactionTestCase
class ComplexIntegrationTest(TransactionTestCase):
    # Each test gets its own database transaction
    # Complete isolation but slower execution
"""
            ],
            difficulty="intermediate",
            tags=["testing", "django", "database", "best-practices"],
            quiz_questions=[
                QuizQuestion(
                    question="When should you use setUp() instead of setUpTestData()?",
                    options=[
                        "Always - fresh data is always better",
                        "Never - setUpTestData() is more efficient",
                        "For data that will be modified during the test",
                        "Only for creating User objects"
                    ],
                    correct_answer=2,
                    explanation="Use setUp() for mutable data that tests will modify, like friend requests that get accepted/rejected."
                ),
                QuizQuestion(
                    question="What data is safe to create in setUpTestData()?",
                    options=[
                        "Friend requests that will be accepted",
                        "Orders that will be processed",
                        "User accounts for authentication",
                        "Products that will be deleted"
                    ],
                    correct_answer=2,
                    explanation="User accounts are typically read-only reference data. The other options involve modifying the data during tests."
                ),
                QuizQuestion(
                    question="How do you diagnose a test isolation issue?",
                    options=[
                        "Run the failing test alone with -k test_name",
                        "Add more print statements",
                        "Increase test timeout",
                        "Run tests sequentially"
                    ],
                    correct_answer=0,
                    explanation="If a test fails in the suite but passes alone (with -k), it's likely an isolation issue."
                )
            ]
        ))
        
        self.add_content(EducationalContent(
            id="slow_queries",
            title="Slow Database Queries",
            type=ContentType.CONCEPT,
            brief="Queries taking excessive time to execute",
            detailed="""
Slow queries can severely impact application performance.
Common causes include:
- Missing database indexes
- Fetching too much data
- Complex joins
- Suboptimal query structure
""",
            solutions=[
                "Add indexes to frequently queried columns",
                "Use select_related/prefetch_related appropriately",
                "Limit results with pagination",
                "Consider database query optimization",
                "Use Django Debug Toolbar to analyze queries"
            ],
            difficulty="advanced",
            tags=["database", "performance", "optimization"],
            quiz_questions=[
                QuizQuestion(
                    question="What is the MOST common cause of slow database queries?",
                    options=[
                        "Too many database connections",
                        "Missing indexes on frequently queried columns",
                        "Using PostgreSQL instead of MySQL",
                        "Having too many models"
                    ],
                    correct_answer=1,
                    explanation="Missing indexes force the database to scan entire tables instead of using efficient index lookups."
                ),
                QuizQuestion(
                    question="Which tool helps identify slow queries in Django?",
                    options=[
                        "Django Admin",
                        "Django Forms",
                        "Django Debug Toolbar",
                        "Django Templates"
                    ],
                    correct_answer=2,
                    explanation="Django Debug Toolbar shows detailed query information including execution time and EXPLAIN output."
                ),
                QuizQuestion(
                    question="What's the best way to limit query results for large datasets?",
                    options=[
                        "Use .all() and filter in Python",
                        "Implement pagination with limit/offset",
                        "Load everything into memory",
                        "Create more database tables"
                    ],
                    correct_answer=1,
                    explanation="Pagination limits the number of results fetched from the database, improving performance and memory usage."
                )
            ]
        ))
        
        # Memory management
        self.add_content(EducationalContent(
            id="memory_leaks",
            title="Memory Leaks in Tests",
            type=ContentType.CONCEPT,
            brief="Memory not being properly released between tests",
            detailed="""
Memory leaks in tests can cause:
- Slow test execution
- Test failures due to resource exhaustion
- Unreliable test results

Common causes:
- Not cleaning up test data
- Circular references
- Cached objects not being cleared
""",
            solutions=[
                "Use tearDown() to clean up resources",
                "Clear caches between tests",
                "Use weak references for circular dependencies",
                "Monitor memory usage with Mercury"
            ],
            difficulty="intermediate",
            tags=["memory", "testing", "performance"],
            quiz_questions=[
                QuizQuestion(
                    question="What is a common symptom of memory leaks in tests?",
                    options=[
                        "Tests run too quickly",
                        "Tests gradually slow down as more run",
                        "Tests produce more accurate results",
                        "Tests use less CPU"
                    ],
                    correct_answer=1,
                    explanation="Memory leaks cause tests to slow down over time as memory fills up and garbage collection works harder."
                ),
                QuizQuestion(
                    question="Which method should you use to clean up resources after each test?",
                    options=[
                        "setUp()",
                        "tearDown()",
                        "__del__()",
                        "cleanup()"
                    ],
                    correct_answer=1,
                    explanation="tearDown() is called after each test method to clean up resources and prevent memory leaks."
                ),
                QuizQuestion(
                    question="How can Django Mercury help with memory leak detection?",
                    options=[
                        "It automatically fixes memory leaks",
                        "It prevents memory allocation",
                        "It monitors and reports memory usage patterns",
                        "It disables garbage collection"
                    ],
                    correct_answer=2,
                    explanation="Mercury tracks memory usage during tests, helping identify tests that consume excessive memory or don't release it properly."
                )
            ]
        ))
        
        # Testing patterns
        self.add_content(EducationalContent(
            id="test_isolation",
            title="Test Isolation",
            type=ContentType.PATTERN,
            brief="Tests should be independent and not affect each other",
            detailed="""
Each test should:
- Set up its own data
- Clean up after itself
- Not depend on other tests
- Not affect other tests

Poor isolation causes flaky tests and hard-to-debug failures.
""",
            solutions=[
                "Use setUp() and tearDown() properly",
                "Avoid global state modifications",
                "Use test fixtures appropriately",
                "Reset database between tests with TransactionTestCase"
            ],
            difficulty="beginner",
            tags=["testing", "best-practices"],
            quiz_questions=[
                QuizQuestion(
                    question="Why is test isolation important?",
                    options=[
                        "It makes tests run faster",
                        "It prevents tests from affecting each other's results",
                        "It reduces code duplication",
                        "It improves code coverage"
                    ],
                    correct_answer=1,
                    explanation="Test isolation ensures each test runs independently, preventing false positives/negatives from test interdependencies."
                ),
                QuizQuestion(
                    question="Which Django TestCase method should you use to set up test data?",
                    options=[
                        "__init__()",
                        "setUp()",
                        "prepare()",
                        "initialize()"
                    ],
                    correct_answer=1,
                    explanation="setUp() is called before each test method, ensuring fresh data for every test."
                ),
                QuizQuestion(
                    question="What happens when tests share global state?",
                    options=[
                        "Tests run faster",
                        "Memory usage decreases",
                        "Tests become flaky and order-dependent",
                        "Code becomes more maintainable"
                    ],
                    correct_answer=2,
                    explanation="Shared global state makes tests dependent on execution order, causing unpredictable failures."
                )
            ]
        ))
        
        # Performance metrics
        self.add_content(EducationalContent(
            id="response_time",
            title="Response Time Metric",
            type=ContentType.METRIC,
            brief="Time taken for a request to complete",
            detailed="""
Response time is critical for user experience.
Thresholds:
- Excellent: < 50ms
- Good: 50-200ms
- Acceptable: 200-500ms
- Poor: > 500ms
""",
            solutions=[
                "Optimize database queries",
                "Cache frequently accessed data",
                "Use CDN for static assets",
                "Minimize middleware overhead"
            ],
            difficulty="intermediate",
            tags=["performance", "metrics", "monitoring"],
            quiz_questions=[
                QuizQuestion(
                    question="What is considered an 'excellent' response time for a web request?",
                    options=[
                        "< 1 second",
                        "< 500ms",
                        "< 200ms",
                        "< 50ms"
                    ],
                    correct_answer=3,
                    explanation="Response times under 50ms are considered excellent, providing near-instantaneous feedback to users."
                ),
                QuizQuestion(
                    question="Which optimization has the BIGGEST impact on response time?",
                    options=[
                        "Minifying JavaScript files",
                        "Optimizing database queries",
                        "Compressing images",
                        "Using a faster web server"
                    ],
                    correct_answer=1,
                    explanation="Database queries are often the bottleneck in web applications, making query optimization crucial for response time."
                ),
                QuizQuestion(
                    question="How does caching improve response time?",
                    options=[
                        "It makes the server faster",
                        "It reduces network latency",
                        "It avoids expensive recomputation of results",
                        "It compresses data"
                    ],
                    correct_answer=2,
                    explanation="Caching stores computed results to avoid repeating expensive operations like database queries or complex calculations."
                )
            ]
        ))
        
        # Query count metric
        self.add_content(EducationalContent(
            id="query_count",
            title="Query Count Metric",
            type=ContentType.METRIC,
            brief="Number of database queries per request",
            detailed="""
Minimizing query count is essential for performance.
Thresholds:
- Excellent: < 5 queries
- Good: 5-10 queries
- Acceptable: 10-20 queries
- Poor: > 20 queries
""",
            solutions=[
                "Use select_related/prefetch_related",
                "Implement query result caching",
                "Batch similar queries",
                "Review ORM usage patterns"
            ],
            difficulty="intermediate",
            tags=["database", "performance", "metrics"],
            quiz_questions=[
                QuizQuestion(
                    question="What is a good target for queries per request?",
                    options=[
                        "< 100 queries",
                        "< 50 queries",
                        "< 20 queries",
                        "< 10 queries"
                    ],
                    correct_answer=3,
                    explanation="Keeping queries under 10 per request ensures good performance. More than 20 often indicates N+1 problems."
                ),
                QuizQuestion(
                    question="How can you reduce query count in Django?",
                    options=[
                        "Use more models",
                        "Use select_related() and prefetch_related()",
                        "Avoid using the ORM",
                        "Add more database indexes"
                    ],
                    correct_answer=1,
                    explanation="select_related() and prefetch_related() fetch related objects in fewer queries, preventing N+1 problems."
                )
            ]
        ))
        
        # Memory usage metric
        self.add_content(EducationalContent(
            id="memory_usage",
            title="Memory Usage Metric",
            type=ContentType.METRIC,
            brief="Amount of memory consumed during execution",
            detailed="""
Memory efficiency is crucial for scalability.
Thresholds:
- Excellent: < 10MB
- Good: 10-50MB
- Acceptable: 50-100MB
- Poor: > 100MB
""",
            solutions=[
                "Use generators for large datasets",
                "Clear unused variables",
                "Optimize data structures",
                "Monitor for memory leaks"
            ],
            difficulty="advanced",
            tags=["memory", "performance", "metrics"],
            quiz_questions=[
                QuizQuestion(
                    question="When should you use generators instead of lists?",
                    options=[
                        "When data is small",
                        "When processing large datasets that don't fit in memory",
                        "When you need random access",
                        "When performance doesn't matter"
                    ],
                    correct_answer=1,
                    explanation="Generators process items one at a time, avoiding loading entire datasets into memory."
                ),
                QuizQuestion(
                    question="What's a sign of excessive memory usage in tests?",
                    options=[
                        "Tests run quickly",
                        "Tests pass consistently",
                        "Tests slow down or crash with large datasets",
                        "Tests have good coverage"
                    ],
                    correct_answer=2,
                    explanation="If tests slow down or crash with larger data, it often indicates inefficient memory usage or leaks."
                )
            ]
        ))
        
        # Tips
        self.add_content(EducationalContent(
            id="tip_fast_tests",
            title="Keep Tests Fast",
            type=ContentType.TIP,
            brief="Aim for < 1 second per test",
            detailed="Fast tests encourage frequent testing and improve developer productivity.",
            difficulty="beginner",
            tags=["testing", "performance"]
        ))
    
    def add_content(self, content: EducationalContent):
        """Add educational content to the database."""
        self.content_db[content.id] = content
    
    def get_content(self, content_id: str) -> Optional[EducationalContent]:
        """Get content by ID."""
        return self.content_db.get(content_id)
    
    def get_contents_by_type(self, content_type: ContentType) -> List[EducationalContent]:
        """Get all content of a specific type."""
        return [c for c in self.content_db.values() if c.type == content_type]
    
    def get_contents_by_tag(self, tag: str) -> List[EducationalContent]:
        """Get all content with a specific tag."""
        return [c for c in self.content_db.values() if tag in c.tags]
    
    def get_contents_by_difficulty(self, difficulty: str) -> List[EducationalContent]:
        """Get all content of a specific difficulty level."""
        return [c for c in self.content_db.values() if c.difficulty == difficulty]
    
    def search_content(self, query: str) -> List[EducationalContent]:
        """Search content by title, brief, or tags."""
        query_lower = query.lower()
        results = []
        
        for content in self.content_db.values():
            if (query_lower in content.title.lower() or
                query_lower in content.brief.lower() or
                any(query_lower in tag for tag in content.tags)):
                results.append(content)
        
        return results
    
    def get_all_content_ids(self) -> List[str]:
        """Get all content IDs."""
        return list(self.content_db.keys())
    
    def get_content_summary(self) -> Dict[str, int]:
        """Get summary statistics of content."""
        summary = {}
        for content_type in ContentType:
            count = len(self.get_contents_by_type(content_type))
            if count > 0:
                summary[content_type.value] = count
        return summary
    
    def export_content(self, file_path: Path):
        """Export content to JSON file."""
        content_list = []
        for content in self.content_db.values():
            content_dict = {
                'id': content.id,
                'title': content.title,
                'type': content.type.value,
                'brief': content.brief,
                'detailed': content.detailed,
                'examples': content.examples,
                'solutions': content.solutions,
                'references': content.references,
                'difficulty': content.difficulty,
                'tags': content.tags,
                'metadata': content.metadata
            }
            content_list.append(content_dict)
        
        with open(file_path, 'w') as f:
            json.dump(content_list, f, indent=2)
    
    def import_content(self, file_path: Path):
        """Import content from JSON file."""
        with open(file_path, 'r') as f:
            content_list = json.load(f)
        
        for content_dict in content_list:
            content = EducationalContent(
                id=content_dict['id'],
                title=content_dict['title'],
                type=ContentType(content_dict['type']),
                brief=content_dict['brief'],
                detailed=content_dict.get('detailed', ''),
                examples=content_dict.get('examples', []),
                solutions=content_dict.get('solutions', []),
                references=content_dict.get('references', []),
                difficulty=content_dict.get('difficulty', 'beginner'),
                tags=content_dict.get('tags', []),
                metadata=content_dict.get('metadata', {})
            )
            self.add_content(content)