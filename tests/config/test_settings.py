"""
Minimal Django settings for testing Django Mercury Performance Testing.
"""

SECRET_KEY : str = 'django-mercury-test-secret-key-not-for-production'

DEBUG : bool = True

ALLOWED_HOSTS : List[str] = ['*']

INSTALLED_APPS : List[str] = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# REST Framework settings for testing
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Minimal middleware
MIDDLEWARE: List[str] = []

# URL Configuration
ROOT_URLCONF = 'tests.urls'

# Templates (minimal)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [],
        },
    },
]

# Testing specific settings
USE_TZ = True
TIME_ZONE = 'UTC'
