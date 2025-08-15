"""
User and Profile Related Tips

Tips focused on Django User model, user profiles, authentication,
and user-related functionality optimization.
"""

TIPS = {
    'user_profile_select_related': {
        'title': '💡 User Profile Optimization',
        'content': 'When testing user-related functionality,\nuse select_related() to load user profiles\nefficiently in a single query.',
        'code_example': "User.objects.select_related('profile')",
        'keywords': ['user', 'profile'],
        'difficulty': 'beginner',
        'learn_more': 'user-optimization',
        'category': 'performance'
    },
    
    'user_auth_testing': {
        'title': '🔐 User Authentication Testing',
        'content': 'For user authentication tests, use\nDjango\'s test client force_login()\nto skip password hashing and speed\nup your tests significantly.',
        'code_example': "self.client.force_login(user)",
        'keywords': ['user', 'auth', 'login'],
        'difficulty': 'beginner',
        'learn_more': 'testing-patterns',
        'category': 'testing'
    },
    
    'user_relationships_prefetch': {
        'title': '👥 User Relationships',
        'content': 'When testing user relationships,\nuse prefetch_related() for Many-to-Many\nfields like groups or permissions.',
        'code_example': "User.objects.prefetch_related('groups')",
        'keywords': ['user', 'groups', 'permissions'],
        'difficulty': 'intermediate',
        'learn_more': 'django-orm',
        'category': 'performance'
    },
    
    'user_profile_n_plus_one': {
        'title': '⚠️ Profile N+1 Prevention',
        'content': 'User profiles are a common source of\nN+1 queries! Always use select_related()\nwhen accessing user.profile to avoid\nmultiple database hits.',
        'code_example': "# Good:\nusers = User.objects.select_related('profile')\nfor user in users:\n    print(user.profile.bio)  # No extra queries!",
        'keywords': ['user', 'profile', 'n+1'],
        'difficulty': 'intermediate',
        'learn_more': 'n-plus-one-patterns',
        'category': 'performance'
    },
    
    'user_file_uploads': {
        'title': '🖼️ User File Upload Testing',
        'content': 'When testing file uploads like profile\npictures, use Django\'s SimpleUploadedFile\nfor clean, reliable test data.',
        'code_example': "from django.core.files.uploadedfile import SimpleUploadedFile\n\nfile = SimpleUploadedFile(\n    'profile.jpg',\n    b'fake_image_content',\n    content_type='image/jpeg'\n)",
        'keywords': ['user', 'profile', 'upload', 'files'],
        'difficulty': 'intermediate',
        'learn_more': 'file-testing',
        'category': 'testing'
    },
    
    'user_settings_testing': {
        'title': '⚙️ User Settings & Preferences',
        'content': 'For user settings tests, consider using\nsetUp() instead of setUpTestData() when\nyou modify the settings during tests.\nsetUpTestData() is for read-only data only.',
        'code_example': "def setUp(self):\n    self.user = User.objects.create_user(...)\n    self.settings = UserSettings.objects.create(\n        user=self.user,\n        theme='dark'\n    )",
        'keywords': ['user', 'settings', 'preferences'],
        'difficulty': 'beginner',
        'learn_more': 'test-data-patterns',
        'category': 'testing'
    }
}