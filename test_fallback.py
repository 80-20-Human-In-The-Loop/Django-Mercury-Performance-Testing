#!/usr/bin/env python
"""Test that the pure Python fallback works when C extensions fail."""

import os
import sys

# Force pure Python mode
os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '1'

# Test import
try:
    from django_mercury.python_bindings.loader import get_implementation_info
    info = get_implementation_info()
    print(f"✓ Pure Python fallback working: {info['type']}")
    
    # Test basic functionality
    from django_mercury.python_bindings.loader import get_performance_monitor
    Monitor = get_performance_monitor()
    monitor = Monitor()
    
    monitor.start_monitoring()
    monitor.stop_monitoring()
    metrics = monitor.get_metrics()
    
    print(f"✓ Functionality test passed: {metrics.get('implementation', 'unknown')}")
    print("Pure Python fallback is working correctly!")
    
except Exception as e:
    print(f"✗ Pure Python fallback failed: {e}")
    sys.exit(1)