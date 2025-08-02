#!/usr/bin/env python3
"""Quick test to identify segfault location"""

import sys
import os
import faulthandler
from pathlib import Path

faulthandler.enable()

# Add the backend directory to Python path
PERFORMANCE_TESTING_ROOT = Path(__file__).parent
BACKEND_ROOT = PERFORMANCE_TESTING_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Configure Django
EDULITE_DIR = BACKEND_ROOT / "EduLite"
if EDULITE_DIR.exists():
    os.chdir(str(EDULITE_DIR))
    sys.path.insert(0, str(EDULITE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduLite.settings')

try:
    import django
    django.setup()
except:
    pass

# Try to run just the validation tests since they come after thread_safety
print("Testing validation module...")
try:
    import unittest
    from tests import test_validation
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_validation)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    print("Validation tests completed successfully!")
except Exception as e:
    print(f"Error in validation tests: {e}")

# Try monitor tests which showed issues
print("\nTesting monitor module...")
try:
    from tests import test_monitor
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_monitor)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    print("Monitor tests completed successfully!")
except Exception as e:
    print(f"Error in monitor tests: {e}")