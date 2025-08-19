"""
API and Django REST Framework Tips

Tips focused on DRF optimization, serializer performance,
API design, and REST API best practices.
"""

TIPS = {
    "serializer_optimization": {
        "title": "🚀 DRF Serializer Optimization",
        "content": "DRF serializers can cause N+1 queries!\nUse select_related() and prefetch_related()\nin your viewsets to optimize database access.",
        "code_example": "class UserViewSet(viewsets.ModelViewSet):\n    serializer_class = UserSerializer\n    \n    def get_queryset(self):\n        return User.objects.select_related(\n            'profile'\n        ).prefetch_related(\n            'groups', 'user_permissions'\n        )",
        "keywords": ["api", "drf", "serializer", "performance"],
        "difficulty": "intermediate",
        "learn_more": "drf-optimization",
        "category": "api",
    },
    "limit_serializer_fields": {
        "title": "📦 Limit Serializer Fields",
        "content": "Only serialize the fields you actually\nneed. Limiting fields reduces response\nsize and improves performance.",
        "code_example": "class UserSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = ['id', 'username', 'email']  # Only what's needed\n        # Avoid: fields = '__all__'  # Too much data!\n        \n# Or use different serializers for different contexts:\nclass UserListSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = ['id', 'username']  # Minimal for lists\n        \nclass UserDetailSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = ['id', 'username', 'email', 'profile']  # More for detail",
        "keywords": ["api", "serializer", "fields", "performance"],
        "difficulty": "beginner",
        "learn_more": "serializer-design",
        "category": "api",
    },
    "pagination_for_performance": {
        "title": "⏱️ API Pagination",
        "content": "Use pagination to limit response size\nand improve API response times.\nNever return unlimited results.",
        "code_example": "# In settings.py:\nREST_FRAMEWORK = {\n    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',\n    'PAGE_SIZE': 20\n}\n\n# Or custom pagination:\nclass CustomPagination(PageNumberPagination):\n    page_size = 10\n    page_size_query_param = 'page_size'\n    max_page_size = 100",
        "keywords": ["api", "pagination", "performance", "response"],
        "difficulty": "beginner",
        "learn_more": "api-pagination",
        "category": "api",
    },
    "serializer_method_field_caution": {
        "title": "⚠️ SerializerMethodField Caution",
        "content": "SerializerMethodField can cause\nperformance issues. Each field means\na function call per object. Use\nsparingly and optimize carefully.",
        "code_example": "class UserSerializer(serializers.ModelSerializer):\n    # Potentially slow if not optimized:\n    friend_count = serializers.SerializerMethodField()\n    \n    def get_friend_count(self, obj):\n        # This runs for each user!\n        return obj.friends.count()  # Could be N+1!\n    \n    # Better: Annotate in queryset\n    # In viewset:\n    # queryset = User.objects.annotate(\n    #     friend_count=Count('friends')\n    # )",
        "keywords": ["api", "serializer", "method", "performance"],
        "difficulty": "intermediate",
        "learn_more": "serializer-optimization",
        "category": "api",
    },
    "api_testing_patterns": {
        "title": "📋 API Testing Best Practices",
        "content": "Test your APIs thoroughly with\nDRF's APITestCase. Test both success\nand error cases, authentication,\nand permissions.",
        "code_example": "from rest_framework.test import APITestCase\nfrom rest_framework import status\n\nclass UserAPITests(APITestCase):\n    def setUp(self):\n        self.user = User.objects.create_user(\n            username='testuser',\n            email='test@test.com'\n        )\n    \n    def test_get_user_list_authenticated(self):\n        self.client.force_authenticate(user=self.user)\n        response = self.client.get('/api/users/')\n        self.assertEqual(response.status_code, status.HTTP_200_OK)\n    \n    def test_get_user_list_unauthenticated(self):\n        response = self.client.get('/api/users/')\n        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)",
        "keywords": ["api", "testing", "drf", "apitestcase"],
        "difficulty": "intermediate",
        "learn_more": "api-testing",
        "category": "api",
    },
    "api_versioning": {
        "title": "🔄 API Versioning Strategy",
        "content": "Plan for API versioning from the start.\nUse URL versioning or header versioning\nto maintain backward compatibility.",
        "code_example": "# URL versioning:\nREST_FRAMEWORK = {\n    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning'\n}\n\n# In urls.py:\nurlpatterns = [\n    path('api/v1/', include('myapp.urls', namespace='v1')),\n    path('api/v2/', include('myapp.v2_urls', namespace='v2')),\n]\n\n# In views:\nclass UserViewSet(viewsets.ModelViewSet):\n    def get_serializer_class(self):\n        if self.request.version == 'v2':\n            return UserV2Serializer\n        return UserSerializer",
        "keywords": ["api", "versioning", "compatibility"],
        "difficulty": "advanced",
        "learn_more": "api-versioning",
        "category": "api",
    },
}
