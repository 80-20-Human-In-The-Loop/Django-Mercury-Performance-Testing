"""
General Django Tips

Tips focused on Django framework best practices, model design,
view optimization, and general Django development patterns.
"""

TIPS = {
    "model_relationships": {
        "title": "🔗 Choosing Model Relationships",
        "content": "Choose the right relationship field\nfor your use case. Wrong choice leads\nto poor performance and confusing code.",
        "code_example": "# One-to-many (User has many Posts)\nclass Post(models.Model):\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n\n# Many-to-many (Users can have many Groups)\nclass User(models.Model):\n    groups = models.ManyToManyField(Group)\n\n# One-to-one (User has one Profile)\nclass Profile(models.Model):\n    user = models.OneToOneField(User, on_delete=models.CASCADE)",
        "keywords": ["django", "model", "relationships", "foreignkey"],
        "difficulty": "beginner",
        "learn_more": "django-models",
        "category": "django",
    },
    "queryset_evaluation": {
        "title": "🔍 QuerySet Lazy Evaluation",
        "content": "QuerySets are lazy - they don't hit\nthe database until you evaluate them.\nUse this to build complex queries\nefficiently.",
        "code_example": "# These don't hit the database yet:\nusers = User.objects.filter(is_active=True)\nusers = users.select_related('profile')\nusers = users.order_by('username')\n\n# This hits the database:\nfor user in users:  # Evaluation happens here\n    print(user.username)",
        "keywords": ["django", "queryset", "lazy", "evaluation"],
        "difficulty": "intermediate",
        "learn_more": "django-orm",
        "category": "django",
    },
    "model_methods_vs_managers": {
        "title": "🏗️ Model Methods vs Managers",
        "content": "Use model methods for instance behavior,\nuse managers for queryset behavior.\nThis keeps your code organized and\nreusable.",
        "code_example": "class UserManager(models.Manager):\n    def active_users(self):\n        return self.filter(is_active=True)\n\nclass User(models.Model):\n    is_active = models.BooleanField(default=True)\n    objects = UserManager()\n    \n    def get_full_name(self):  # Instance method\n        return f'{self.first_name} {self.last_name}'\n\n# Usage:\nactive_users = User.objects.active_users()  # Manager\nfull_name = user.get_full_name()  # Instance method",
        "keywords": ["django", "model", "manager", "methods"],
        "difficulty": "intermediate",
        "learn_more": "django-models",
        "category": "django",
    },
    "signals_performance": {
        "title": "📡 Django Signals & Performance",
        "content": "Be careful with Django signals - they\ncan cause performance issues if not\nused properly. Avoid heavy operations\nin signal handlers.",
        "code_example": "from django.db.models.signals import post_save\nfrom django.dispatch import receiver\n\n@receiver(post_save, sender=User)\ndef create_user_profile(sender, instance, created, **kwargs):\n    if created:\n        # Good: Simple, fast operation\n        UserProfile.objects.create(user=instance)\n        \n        # Bad: Slow operation in signal\n        # send_welcome_email(instance)  # Use Celery instead!",
        "keywords": ["django", "signals", "performance"],
        "difficulty": "advanced",
        "learn_more": "django-signals",
        "category": "django",
    },
    "admin_optimization": {
        "title": "⚙️ Django Admin Optimization",
        "content": "Optimize Django Admin for better\nperformance with list_select_related\nand raw_id_fields for large datasets.",
        "code_example": "@admin.register(Post)\nclass PostAdmin(admin.ModelAdmin):\n    list_display = ['title', 'author', 'created_at']\n    list_select_related = ['author']  # Avoid N+1 in admin\n    raw_id_fields = ['author']  # Better for large FK datasets\n    list_filter = ['created_at', 'author']\n    search_fields = ['title', 'content']",
        "keywords": ["django", "admin", "optimization"],
        "difficulty": "intermediate",
        "learn_more": "django-admin",
        "category": "django",
    },
    "custom_migrations": {
        "title": "🔄 Safe Database Migrations",
        "content": "Write safe migrations for production.\nUse RunPython for data migrations and\nalways include reverse operations.",
        "code_example": "from django.db import migrations\n\ndef populate_slugs(apps, schema_editor):\n    Post = apps.get_model('blog', 'Post')\n    for post in Post.objects.all():\n        post.slug = post.title.lower().replace(' ', '-')\n        post.save()\n\ndef reverse_populate_slugs(apps, schema_editor):\n    # Always provide reverse operation\n    Post = apps.get_model('blog', 'Post')\n    Post.objects.update(slug='')\n\nclass Migration(migrations.Migration):\n    operations = [\n        migrations.RunPython(\n            populate_slugs,\n            reverse_populate_slugs\n        )\n    ]",
        "keywords": ["django", "migrations", "database"],
        "difficulty": "advanced",
        "learn_more": "django-migrations",
        "category": "django",
    },
}
