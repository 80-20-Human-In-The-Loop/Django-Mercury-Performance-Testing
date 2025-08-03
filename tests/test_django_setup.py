"""
Test to verify Django setup is working properly for CI/CD.
"""

import pytest
import django
from django.conf import settings


def test_django_configured():
    """Test that Django is properly configured."""
    assert settings.configured
    assert hasattr(settings, 'SECRET_KEY')
    assert settings.SECRET_KEY == 'django-mercury-test-secret-key-not-for-production'


def test_django_apps_installed():
    """Test that required apps are installed."""
    installed_apps = settings.INSTALLED_APPS
    assert 'django.contrib.contenttypes' in installed_apps
    assert 'django.contrib.auth' in installed_apps
    assert 'rest_framework' in installed_apps


def test_database_configured():
    """Test that database is configured."""
    db_config = settings.DATABASES['default']
    assert db_config['ENGINE'] == 'django.db.backends.sqlite3'
    assert db_config['NAME'] == ':memory:'


@pytest.mark.django_db
def test_can_use_django_db():
    """Test that we can use Django's database functionality."""
    from django.contrib.auth.models import User
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert User.objects.count() == 1


def test_mercury_imports():
    """Test that Django Mercury imports work."""
    # These imports should work if Django is properly configured
    from django_mercury import DjangoMercuryAPITestCase, DjangoPerformanceAPITestCase
    from django_mercury import monitor_django_view
    
    # Basic class checks
    assert hasattr(DjangoMercuryAPITestCase, 'configure_mercury')
    assert hasattr(DjangoPerformanceAPITestCase, 'assertPerformance')
    assert callable(monitor_django_view)