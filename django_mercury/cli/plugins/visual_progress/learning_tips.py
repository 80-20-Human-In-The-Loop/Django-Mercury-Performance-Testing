"""
Contextual Learning Tips Database for Student Mode

Provides educational tips based on test context and keywords.
Tips rotate every 10 seconds to keep content fresh and engaging.
"""

import random
import time
from typing import Dict, List, Optional


class LearningTipsDatabase:
    """Database of contextual learning tips for student mode."""

    # Tips organized by context keywords found in test names
    CONTEXTUAL_TIPS = {
        "user": [
            "💡 User Model Optimization\n\nWhen testing user-related functionality,\nuse select_related('profile') to load\nuser profiles efficiently.\n\nExample:\nUser.objects.select_related('profile')",
            "🔐 User Authentication Tips\n\nFor user auth tests, consider using\nDjango's built-in test client:\n\nclient.force_login(user)\n\nThis skips password hashing and\nspeeds up your tests significantly!",
            "👥 User Relationships\n\nWhen testing user relationships,\nuse prefetch_related() for\nMany-to-Many fields:\n\nUser.objects.prefetch_related('groups')",
        ],
        "profile": [
            "📊 Profile Performance\n\nUser profiles often cause N+1 queries!\nAlways use select_related() when\naccessing user.profile:\n\nUser.objects.select_related('profile')\n\nThis loads both user and profile\nin a single query.",
            "🖼️ Profile Images & Files\n\nWhen testing file uploads, use\nDjango's SimpleUploadedFile:\n\nfrom django.core.files.uploadedfile\nimport SimpleUploadedFile\n\nPerfect for testing profile pictures!",
            "⚙️ Profile Settings\n\nFor profile settings tests,\nconsider using setUp() instead of\nsetUpTestData() when you modify\nthe profile data during tests.",
        ],
        "friend": [
            "🤝 Friend Relationships\n\nFriend systems often use M2M fields.\nUse prefetch_related() to avoid\nN+1 queries:\n\nuser.friends.prefetch_related('profile')\n\nThis loads all friends and their\nprofiles efficiently!",
            "📬 Friend Requests\n\nWhen testing friend requests,\nuse bulk operations for creating\nmultiple requests:\n\nFriendRequest.objects.bulk_create([\n    FriendRequest(from_user=u1, to_user=u2)\n])",
            "🔄 Friend Status Updates\n\nFor friend status changes, consider\nusing update() instead of save()\nfor better performance:\n\nFriendRequest.objects.filter(\n    id=request.id\n).update(status='accepted')",
        ],
        "search": [
            "🔍 Search Optimization\n\nFor search functionality, add\ndatabase indexes on searchable fields:\n\nclass Meta:\n    indexes = [\n        models.Index(fields=['name']),\n        models.Index(fields=['email'])\n    ]",
            "⚡ Search Performance\n\nUse icontains for case-insensitive\nsearch, but consider full-text search\nfor complex queries:\n\nUser.objects.filter(\n    name__icontains=query\n)\n\nFor PostgreSQL, use search vectors!",
            "📝 Search Testing\n\nWhen testing search, create test data\nwith predictable patterns:\n\nUser.objects.create(\n    name='test_user_searchable'\n)\n\nMakes assertions easier and reliable!",
        ],
        "api": [
            "🚀 API Performance\n\nDRF serializers can cause N+1 queries!\nUse select_related() and\nprefetch_related() in your viewsets:\n\nqueryset = User.objects.select_related(\n    'profile'\n).prefetch_related('groups')",
            "📦 API Serialization\n\nLimit serializer fields to only\nwhat you need:\n\nclass UserSerializer(serializers.ModelSerializer):\n    class Meta:\n        fields = ['id', 'username', 'email']\n        # Don't serialize everything!",
            "⏱️ API Response Time\n\nUse DRF's pagination to limit\nresponse size:\n\nREST_FRAMEWORK = {\n    'PAGE_SIZE': 20\n}\n\nPagination improves response times\nand reduces memory usage!",
        ],
        "serializer": [
            "📊 Serializer Optimization\n\nNested serializers cause extra queries!\nUse SerializerMethodField carefully:\n\nclass UserSerializer(ModelSerializer):\n    friend_count = SerializerMethodField()\n    \n    def get_friend_count(self, obj):\n        return obj.friends.count()  # Can be slow!",
            "🔧 Serializer Performance\n\nFor read-only serializers, use\nto_representation() to customize\noutput without database hits:\n\ndef to_representation(self, instance):\n    data = super().to_representation(instance)\n    data['display_name'] = f\"{instance.first} {instance.last}\"\n    return data",
            "📝 Serializer Testing\n\nTest serializer performance with\nlarge datasets:\n\nusers = User.objects.all()[:100]\nserializer = UserSerializer(users, many=True)\ndata = serializer.data  # Time this!",
        ],
        "view": [
            "🎯 View Optimization\n\nUse get_queryset() to optimize\ndatabase queries in your views:\n\ndef get_queryset(self):\n    return User.objects.select_related(\n        'profile'\n    ).prefetch_related('groups')",
            "📋 View Testing\n\nUse Django's test client for\nview testing:\n\nresponse = self.client.get('/api/users/')\nself.assertEqual(response.status_code, 200)\n\nTest both success and error cases!",
            "⚡ View Performance\n\nAvoid queries in templates!\nPrefetch related data in views:\n\n# In view:\nusers = User.objects.prefetch_related('posts')\n\n# In template:\n{% for post in user.posts.all %}",
        ],
        "model": [
            "🏗️ Model Optimization\n\nUse database indexes for frequently\nqueried fields:\n\nclass User(models.Model):\n    email = models.EmailField(db_index=True)\n    created_at = models.DateTimeField(\n        auto_now_add=True, db_index=True\n    )",
            "🔗 Model Relationships\n\nChoose the right relationship field:\n\n• ForeignKey: One-to-many\n• ManyToManyField: Many-to-many\n• OneToOneField: One-to-one\n\nWrong choice = bad performance!",
            "📊 Model Testing\n\nUse Model.objects.create() in tests\ninstead of Model.save():\n\nuser = User.objects.create(\n    username='testuser',\n    email='test@example.com'\n)\n\nMore explicit and testable!",
        ],
        "performance": [
            "⚡ Query Optimization\n\nUse select_related() for ForeignKey\nand OneToOne relationships:\n\n# Bad:\nfor user in User.objects.all():\n    print(user.profile.bio)  # N+1 queries!\n\n# Good:\nfor user in User.objects.select_related('profile'):\n    print(user.profile.bio)  # 1 query!",
            "🔄 Bulk Operations\n\nUse bulk operations for multiple\ndatabase changes:\n\n# Create many:\nUser.objects.bulk_create(users)\n\n# Update many:\nUser.objects.filter(\n    is_active=False\n).update(is_active=True)",
            "📈 Performance Testing\n\nAlways test with realistic data sizes:\n\n# Test with 1 user:\nassertions...\n\n# Test with 100 users:\nassertions...\n\n# Test with 1000 users:\nassertions...\n\nPerformance changes with scale!",
        ],
    }

    # General tips when no specific context is detected
    GENERAL_TIPS = [
        "🧪 Testing Best Practices\n\nUse descriptive test method names:\n\ndef test_user_can_update_own_profile()\ndef test_user_cannot_update_other_profile()\n\nClear names make debugging easier!",
        "🔄 Test Data Management\n\nUse setUp() for data that changes\nduring tests:\n\ndef setUp(self):\n    self.user = User.objects.create(...)\n\nUse setUpTestData() for read-only\nreference data only!",
        "⚡ Django Query Optimization\n\nThe golden rules:\n\n1. select_related() for ForeignKey\n2. prefetch_related() for M2M\n3. only() to limit fields\n4. Use bulk operations\n5. Add database indexes",
        "📊 Performance Monitoring\n\nUse django-debug-toolbar in\ndevelopment to see query counts:\n\npip install django-debug-toolbar\n\nIt shows exactly which queries\nare slow or repeated!",
        "🎯 Test Organization\n\nOrganize tests by functionality:\n\nclass UserProfileTests(TestCase):\nclass UserAuthenticationTests(TestCase):\nclass UserPermissionTests(TestCase):\n\nClear organization helps maintenance!",
        "🚀 Django Performance Tips\n\nCaching is your friend:\n\nfrom django.core.cache import cache\n\n# Cache expensive operations:\nresult = cache.get('expensive_key')\nif result is None:\n    result = expensive_operation()\n    cache.set('expensive_key', result, 300)",
    ]

    def __init__(self):
        """Initialize the tips database."""
        self.last_tip_time = 0
        self.current_tip = None
        self.tip_rotation_interval = 10  # seconds

    def get_contextual_tip(self, test_name: str = "", test_results: Dict = None) -> str:
        """
        Get a tip based on test context and timing.

        Args:
            test_name: Current or recent test name
            test_results: Optional test results for context

        Returns:
            Contextual tip string
        """
        current_time = time.time()

        # Check if it's time to rotate tips
        if (current_time - self.last_tip_time) >= self.tip_rotation_interval:
            self.current_tip = self._select_tip(test_name, test_results)
            self.last_tip_time = current_time

        return self.current_tip or self._select_tip(test_name, test_results)

    def _select_tip(self, test_name: str, test_results: Dict = None) -> str:
        """Select appropriate tip based on context."""
        # Extract keywords from test name
        test_name_lower = test_name.lower()

        # Find matching context keywords
        matching_contexts = []
        for context_key in self.CONTEXTUAL_TIPS.keys():
            if context_key in test_name_lower:
                matching_contexts.append(context_key)

        # Performance-based context from test results
        if test_results:
            if test_results.get("query_count", 0) > 20:
                matching_contexts.append("performance")
            if "slow" in str(test_results.get("grade", "")).lower():
                matching_contexts.append("performance")

        # Select tip from matching contexts
        if matching_contexts:
            context = random.choice(matching_contexts)
            return random.choice(self.CONTEXTUAL_TIPS[context])

        # Fall back to general tips
        return random.choice(self.GENERAL_TIPS)

    def get_next_tip_countdown(self) -> int:
        """Get seconds until next tip rotation."""
        elapsed = time.time() - self.last_tip_time
        remaining = max(0, self.tip_rotation_interval - elapsed)
        return int(remaining)

    def force_rotation(self):
        """Force tip rotation on next request."""
        self.last_tip_time = 0


# Global instance for the visual display
learning_tips_db = LearningTipsDatabase()
