"""
Testing Best Practices Tips

Tips focused on Django testing patterns, test organization,
test data management, and testing performance.
"""

TIPS = {
    'descriptive_test_names': {
        'title': '🧪 Descriptive Test Names',
        'content': 'Use clear, descriptive test method names\nthat explain what behavior is being tested.\nThis makes debugging much easier.',
        'code_example': "# Good test names:\ndef test_user_can_update_own_profile(self):\ndef test_user_cannot_update_other_profile(self):\ndef test_admin_can_update_any_profile(self):\n\n# Bad test names:\ndef test_profile(self):\ndef test_update(self):",
        'keywords': ['testing', 'test', 'names'],
        'difficulty': 'beginner',
        'learn_more': 'testing-patterns',
        'category': 'testing'
    },
    
    'setup_vs_setuptestdata': {
        'title': '🔄 setUp vs setUpTestData',
        'content': 'Use setUp() for data that changes during\ntests. Use setUpTestData() only for\nread-only reference data that never\ngets modified.',
        'code_example': "class UserTests(TestCase):\n    @classmethod\n    def setUpTestData(cls):\n        # Read-only reference data\n        cls.admin_user = User.objects.create_user(\n            'admin', 'admin@test.com'\n        )\n    \n    def setUp(self):\n        # Data that might be modified\n        self.user = User.objects.create_user(\n            'testuser', 'test@test.com'\n        )",
        'keywords': ['testing', 'setup', 'test', 'data'],
        'difficulty': 'intermediate',
        'learn_more': 'test-data-patterns',
        'category': 'testing'
    },
    
    'test_organization': {
        'title': '🎯 Test Organization',
        'content': 'Organize tests by functionality using\nseparate test classes. This makes tests\neasier to find and maintain.',
        'code_example': "class UserProfileTests(TestCase):\n    # All profile-related tests\n    \nclass UserAuthenticationTests(TestCase):\n    # All auth-related tests\n    \nclass UserPermissionTests(TestCase):\n    # All permission-related tests",
        'keywords': ['testing', 'organization', 'structure'],
        'difficulty': 'beginner',
        'learn_more': 'test-organization',
        'category': 'testing'
    },
    
    'test_client_usage': {
        'title': '📋 Django Test Client',
        'content': 'Use Django\'s test client for testing\nviews and API endpoints. It handles\nauthentication and provides useful\nassertion methods.',
        'code_example': "def test_user_profile_view(self):\n    # Test authenticated access\n    self.client.force_login(self.user)\n    response = self.client.get('/profile/')\n    self.assertEqual(response.status_code, 200)\n    \n    # Test unauthenticated access\n    self.client.logout()\n    response = self.client.get('/profile/')\n    self.assertEqual(response.status_code, 302)",
        'keywords': ['testing', 'client', 'views', 'api'],
        'difficulty': 'beginner',
        'learn_more': 'view-testing',
        'category': 'testing'
    },
    
    'performance_testing_scales': {
        'title': '📈 Test with Different Scales',
        'content': 'Always test performance with realistic\ndata sizes. Performance characteristics\nchange dramatically with scale.',
        'code_example': "def test_user_search_performance(self):\n    # Test with 1 user\n    self._create_users(1)\n    self._assert_search_performance()\n    \n    # Test with 100 users  \n    self._create_users(100)\n    self._assert_search_performance()\n    \n    # Test with 1000 users\n    self._create_users(1000)\n    self._assert_search_performance()",
        'keywords': ['testing', 'performance', 'scale', 'data'],
        'difficulty': 'advanced',
        'learn_more': 'performance-testing',
        'category': 'testing'
    },
    
    'mock_external_services': {
        'title': '🎭 Mock External Services',
        'content': 'Always mock external services in tests.\nThis makes tests faster, more reliable,\nand independent of external systems.',
        'code_example': "from unittest.mock import patch, Mock\n\nclass EmailTests(TestCase):\n    @patch('myapp.services.send_email')\n    def test_user_registration_sends_email(self, mock_send):\n        mock_send.return_value = True\n        \n        response = self.client.post('/register/', {\n            'username': 'newuser',\n            'email': 'new@test.com'\n        })\n        \n        mock_send.assert_called_once()",
        'keywords': ['testing', 'mock', 'external', 'services'],
        'difficulty': 'intermediate',
        'learn_more': 'mocking-patterns',
        'category': 'testing'
    }
}