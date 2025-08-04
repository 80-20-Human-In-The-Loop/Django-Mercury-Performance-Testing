"""Example test cases demonstrating the EduLite Performance Testing Framework

This file shows various usage patterns and best practices for performance testing
Django REST Framework APIs using the Mercury framework.
"""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from django_mercury import DjangoMercuryAPITestCase, monitor_django_view


class BasicPerformanceTestCase(DjangoMercuryAPITestCase):
    """Basic example with automatic performance monitoring."""

    def setUp(self):
        """Create test data."""
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_simple_endpoint(self):
        """Test a simple endpoint with automatic monitoring."""
        # Mercury automatically monitors this test
        response = self.client.get("/api/users/me/")

        # Standard assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

        # Performance is automatically analyzed and scored
        # You'll see output like:
        # 🎯 test_simple_endpoint - Grade A (45.2ms, 3Q, 12.5MB overhead)


class CustomThresholdTestCase(DjangoMercuryAPITestCase):
    """Example with custom performance thresholds."""

    @classmethod
    def setUpClass(cls):
        """Configure custom thresholds for the test class."""
        super().setUpClass()

        # Set stricter thresholds for this test class
        cls.set_performance_thresholds(
            {
                "response_time_ms": 100,  # Max 100ms (strict)
                "query_count_max": 5,  # Max 5 queries
                "memory_overhead_mb": 20,  # Max 20MB overhead
            }
        )

        # Configure Mercury behavior
        cls.configure_mercury(
            enabled=True,
            auto_scoring=True,
            verbose_reporting=False,  # Set True for debugging
            educational_guidance=True,  # Helpful for learning
        )

    def test_user_list_with_pagination(self):
        """Test paginated list view with custom thresholds."""
        # Create test data
        for i in range(25):
            User.objects.create_user(f"user{i}", f"user{i}@example.com")

        response = self.client.get("/api/users/?page_size=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)


class PerTestThresholdExample(DjangoMercuryAPITestCase):
    """Example with per-test threshold overrides."""

    def test_simple_operation(self):
        """Test with default thresholds."""
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_complex_aggregation(self):
        """Test with relaxed thresholds for complex operation."""
        # This specific test needs more time
        self.set_test_performance_thresholds(
            {
                "response_time_ms": 500,  # Allow 500ms for complex query
                "query_count_max": 20,  # Complex aggregation needs more queries
                "memory_overhead_mb": 60,  # More memory for data processing
            }
        )

        # Create complex test data
        for i in range(100):
            user = User.objects.create_user(f"user{i}", f"user{i}@example.com")
            # Create related data...

        response = self.client.get("/api/users/statistics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bulk_operation(self):
        """Test bulk operation with context manager for thresholds."""
        # Alternative syntax using context manager
        with self.mercury_override_thresholds({"query_count_max": 50, "response_time_ms": 1000}):
            data = {
                "users": [
                    {"username": f"bulk_user{i}", "email": f"bulk{i}@example.com"}
                    for i in range(50)
                ]
            }
            response = self.client.post("/api/users/bulk_create/", data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ManualMonitoringExample(DjangoMercuryAPITestCase):
    """Example using manual monitoring for fine-grained control."""

    def test_with_manual_monitoring(self):
        """Test with explicit performance monitoring."""
        # Manual monitoring gives you direct access to metrics
        with monitor_django_view("user_profile_detailed") as monitor:
            response = self.client.get("/api/users/1/detailed/")

        # Access metrics directly
        metrics = monitor.metrics
        print(f"Response time: {metrics.response_time:.2f}ms")
        print(f"Query count: {metrics.query_count}")
        print(f"Memory overhead: {metrics.memory_overhead:.2f}MB")

        # Make assertions on specific metrics
        self.assertLess(metrics.response_time, 150)
        self.assertLess(metrics.query_count, 8)

        # Get detailed reports
        print(metrics.get_performance_report_with_scoring())
        print(metrics.get_memory_analysis_report())

    def test_with_comprehensive_analysis(self):
        """Test using comprehensive analysis method."""
        metrics = self.run_comprehensive_analysis(
            operation_name="UserSearchView",
            test_function=lambda: self.client.get("/api/users/search/?q=john"),
            operation_type="search_view",
            expect_response_under=300,
            expect_queries_under=15,
            expect_memory_under=100,
            print_analysis=True,  # Print detailed analysis
            show_scoring=True,  # Include performance score
            auto_detect_n_plus_one=True,  # Detect N+1 patterns
        )

        # Assert using Mercury's convenience methods
        self.assert_mercury_performance_production_ready(metrics)

        # Or make specific assertions
        self.assertNoNPlusOne(metrics)
        self.assertPerformanceFast(metrics)


class NPlusOneDetectionExample(DjangoMercuryAPITestCase):
    """Example demonstrating N+1 query detection and fixes."""

    def test_n_plus_one_detection(self):
        """Test that triggers N+1 queries (for demonstration)."""
        # Create users with profiles
        from django.contrib.auth.models import User
        from myapp.models import UserProfile

        for i in range(20):
            user = User.objects.create_user(f"user{i}", f"user{i}@example.com")
            UserProfile.objects.create(user=user, bio=f"Bio for user {i}")

        # This will trigger N+1 if not using select_related
        response = self.client.get("/api/users/")

        # Mercury will detect and report:
        # 🚨 N+1 Query Issue: SEVERE (21 queries)
        # 💡 Fix: Use select_related('profile') in your User query

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_optimized_query(self):
        """Test with optimized queries (no N+1)."""
        # Same setup but with optimized view
        for i in range(20):
            user = User.objects.create_user(f"opt_user{i}", f"opt{i}@example.com")
            UserProfile.objects.create(user=user, bio=f"Bio for user {i}")

        # Assuming the view uses select_related('profile')
        response = self.client.get("/api/users/optimized/")

        # Mercury will show good performance
        # 🎯 test_optimized_query - Grade A (32.5ms, 2Q, 8.3MB overhead)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PerformanceAssertionExample(DjangoMercuryAPITestCase):
    """Example showing various performance assertion methods."""

    def test_with_multiple_assertions(self):
        """Test demonstrating different assertion styles."""
        # Perform the operation
        response = self.client.get("/api/users/")

        # Method 1: Let Mercury handle assertions automatically
        # (configured via thresholds)

        # Method 2: Explicit assertions on the last operation
        # (Mercury tracks the most recent operation)
        metrics = self._test_executions[-1] if hasattr(self, "_test_executions") else None

        if metrics:
            # Assert performance characteristics
            self.assertPerformanceFast(metrics)
            self.assertNoNPlusOne(metrics)
            self.assertMemoryEfficient(metrics)

            # Assert specific thresholds
            self.assertResponseTimeLess(metrics, 200)
            self.assertQueriesLess(metrics, 10)
            self.assertMemoryLess(metrics, 100)

            # Assert overall quality
            self.assert_mercury_performance_excellent(metrics)


class ProductionReadinessExample(DjangoMercuryAPITestCase):
    """Example for ensuring production readiness."""

    @classmethod
    def setUpClass(cls):
        """Configure for production standards."""
        super().setUpClass()

        # Production-grade thresholds
        cls.set_performance_thresholds(
            {
                "response_time_ms": 200,  # Strict for production
                "query_count_max": 10,  # Minimize database load
                "memory_overhead_mb": 30,  # Control memory usage
            }
        )

        # Enable all Mercury features
        cls.configure_mercury(
            enabled=True,
            auto_scoring=True,
            auto_threshold_adjustment=True,
            generate_summaries=True,
            educational_guidance=False,  # Disable in production tests
        )

    def test_critical_endpoint(self):
        """Test critical endpoint meets production standards."""
        response = self.client.get("/api/critical/endpoint/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure production readiness
        if hasattr(self, "_test_executions") and self._test_executions:
            metrics = self._test_executions[-1]
            self.assert_mercury_performance_production_ready(metrics)

            # Additional production checks
            self.assertGreaterEqual(
                metrics.performance_score.total_score,
                70,
                "Performance score must be at least 70 for production",
            )


class DebugModeExample(DjangoMercuryAPITestCase):
    """Example showing debug and troubleshooting features."""

    @classmethod
    def setUpClass(cls):
        """Enable verbose mode for debugging."""
        super().setUpClass()

        cls.configure_mercury(
            verbose_reporting=True,  # See detailed output
            educational_guidance=True,  # Get optimization hints
        )

    def test_with_debugging(self):
        """Test with full debugging output."""
        # Set very strict thresholds to trigger guidance
        self.set_test_performance_thresholds(
            {
                "response_time_ms": 10,  # Unrealistic threshold
                "query_count_max": 1,  # Very strict
            }
        )

        # This will likely exceed thresholds
        response = self.client.get("/api/users/")

        # Mercury will provide:
        # 1. Detailed performance report
        # 2. Educational guidance on why it failed
        # 3. Specific suggestions for fixing issues
        # 4. Example code for setting realistic thresholds


if __name__ == "__main__":
    # Run specific test class
    import unittest

    suite = unittest.TestLoader().loadTestsFromTestCase(BasicPerformanceTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
