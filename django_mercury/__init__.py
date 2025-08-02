"""Django Mercury Performance Testing Framework

A performance testing framework for Django that helps you understand and fix performance issues, 
not just detect them.

Basic Usage:
    from django_mercury import DjangoMercuryAPITestCase
    
    class MyAPITestCase(DjangoMercuryAPITestCase):
        def test_performance(self):
            response = self.client.get('/api/endpoint/')
            self.assertEqual(response.status_code, 200)
            # Performance is automatically monitored and analyzed
"""

__version__ = '0.0.1'
__author__ = 'Django Mercury Team'

# Public API imports for convenience
from .python_bindings.django_integration_mercury import DjangoMercuryAPITestCase
from .python_bindings.django_integration import DjangoPerformanceAPITestCase
from .python_bindings.monitor import (
    monitor_django_view,
    monitor_django_model,
    monitor_serializer,
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python
)
from .python_bindings.constants import (
    RESPONSE_TIME_THRESHOLDS,
    MEMORY_THRESHOLDS,
    QUERY_COUNT_THRESHOLDS,
    N_PLUS_ONE_THRESHOLDS
)

__all__ = [
    'DjangoMercuryAPITestCase',
    'DjangoPerformanceAPITestCase',
    'monitor_django_view',
    'monitor_django_model', 
    'monitor_serializer',
    'EnhancedPerformanceMonitor',
    'EnhancedPerformanceMetrics_Python',
    'RESPONSE_TIME_THRESHOLDS',
    'MEMORY_THRESHOLDS',
    'QUERY_COUNT_THRESHOLDS',
    'N_PLUS_ONE_THRESHOLDS',
]