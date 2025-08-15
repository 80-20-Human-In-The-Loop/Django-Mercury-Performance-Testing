"""
Performance Optimization Tips

Tips focused on Django ORM optimization, query performance,
caching, and general performance best practices.
"""

TIPS = {
    'select_related_foreignkey': {
        'title': '⚡ ForeignKey Optimization',
        'content': 'Use select_related() for ForeignKey and\nOneToOne relationships to avoid N+1\nqueries. This loads related objects\nin a single JOIN query.',
        'code_example': "# Bad: N+1 queries\nfor user in User.objects.all():\n    print(user.profile.bio)  # Extra query each time!\n\n# Good: Single query\nfor user in User.objects.select_related('profile'):\n    print(user.profile.bio)  # No extra queries!",
        'keywords': ['performance', 'select_related', 'foreignkey'],
        'difficulty': 'beginner',
        'learn_more': 'django-orm',
        'category': 'performance'
    },
    
    'prefetch_related_m2m': {
        'title': '🔄 Many-to-Many Optimization', 
        'content': 'Use prefetch_related() for ManyToMany\nand reverse ForeignKey relationships.\nThis uses separate queries but avoids\nthe N+1 pattern.',
        'code_example': "# Good for M2M:\nusers = User.objects.prefetch_related('groups')\nfor user in users:\n    for group in user.groups.all():  # No extra queries!\n        print(group.name)",
        'keywords': ['performance', 'prefetch_related', 'm2m', 'manytomany'],
        'difficulty': 'intermediate',
        'learn_more': 'django-orm',
        'category': 'performance'
    },
    
    'bulk_operations': {
        'title': '📦 Bulk Database Operations',
        'content': 'Use bulk operations for creating or\nupdating multiple objects. This reduces\ndatabase round trips significantly.',
        'code_example': "# Create many objects:\nUser.objects.bulk_create([\n    User(username=f'user{i}', email=f'user{i}@test.com')\n    for i in range(100)\n])\n\n# Update many objects:\nUser.objects.filter(\n    is_active=False\n).update(is_active=True)",
        'keywords': ['performance', 'bulk', 'create', 'update'],
        'difficulty': 'intermediate', 
        'learn_more': 'bulk-operations',
        'category': 'performance'
    },
    
    'query_only_fields': {
        'title': '📊 Limit Query Fields',
        'content': 'Use only() to load specific fields\ninstead of entire model instances.\nThis reduces memory usage and\nimproves query performance.',
        'code_example': "# Load only needed fields:\nusers = User.objects.only('username', 'email')\n\n# Or use values() for dictionaries:\nuser_data = User.objects.values('username', 'email')",
        'keywords': ['performance', 'only', 'values', 'fields'],
        'difficulty': 'intermediate',
        'learn_more': 'query-optimization',
        'category': 'performance'
    },
    
    'database_indexes': {
        'title': '🏗️ Database Indexes',
        'content': 'Add database indexes on fields you\nfrequently filter or order by. This\ndramatically improves query speed.',
        'code_example': "class User(models.Model):\n    email = models.EmailField(db_index=True)\n    created_at = models.DateTimeField(\n        auto_now_add=True,\n        db_index=True\n    )\n    \n    class Meta:\n        indexes = [\n            models.Index(fields=['username', 'email']),\n        ]",
        'keywords': ['performance', 'index', 'database', 'query'],
        'difficulty': 'advanced',
        'learn_more': 'database-optimization', 
        'category': 'performance'
    },
    
    'caching_patterns': {
        'title': '🚀 Caching for Performance',
        'content': 'Cache expensive operations to avoid\nrepeated calculations or database hits.\nUse Django\'s caching framework wisely.',
        'code_example': "from django.core.cache import cache\n\n# Cache expensive calculation:\nresult = cache.get('expensive_key')\nif result is None:\n    result = expensive_calculation()\n    cache.set('expensive_key', result, 300)  # 5 min\n\nreturn result",
        'keywords': ['performance', 'cache', 'caching'],
        'difficulty': 'advanced',
        'learn_more': 'caching-strategies',
        'category': 'performance'
    }
}