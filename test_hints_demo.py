"""
Simple test to demonstrate Mercury hints functionality.
"""
import time
from django.test import TestCase
from django_mercury import DjangoPerformanceAPITestCase, monitor_django_view


class HintsDemoTest(DjangoPerformanceAPITestCase):
    """Simple test to demonstrate hints in visual runner."""
    
    def test_slow_operation_with_many_queries(self):
        """Test that triggers performance hints."""
        with monitor_django_view("slow_operation") as monitor:
            # Simulate a slow operation with many database queries
            from django.contrib.auth.models import User
            
            # Create multiple queries to trigger high query count hint
            for i in range(25):
                User.objects.filter(username=f"user_{i}").exists()
            
            # Add some delay to trigger slow response hint
            time.sleep(0.05)  # 50ms delay
        
        # This test should trigger both high query count and slow response hints
        self.assertQueriesLess(monitor.metrics, 30, "Should have fewer than 30 queries")
        self.assertResponseTimeLess(monitor.metrics, 100, "Should respond in under 100ms")
    
    def test_good_performance(self):
        """Test with good performance - should not trigger hints."""
        with monitor_django_view("good_operation") as monitor:
            # Simple operation that should be fast
            from django.contrib.auth.models import User
            User.objects.filter(username="nonexistent").exists()
        
        self.assertQueriesLess(monitor.metrics, 5, "Should use few queries")
        self.assertResponseTimeLess(monitor.metrics, 50, "Should be fast")