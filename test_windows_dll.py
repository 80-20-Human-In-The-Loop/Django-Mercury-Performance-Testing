#!/usr/bin/env python
"""Test script to verify Windows DLL loading for C extensions."""

import os
import sys
import platform

def test_windows_dll_loading():
    """Test that C extensions can load on Windows."""
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()}")
    print(f"Machine: {platform.machine()}")
    print("")
    
    # Force pure Python mode off
    os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '0'
    
    try:
        print("Testing C extension imports...")
        
        # Try to import the C extensions
        print("1. Importing _c_metrics...")
        import django_mercury._c_metrics
        print("   ✓ _c_metrics imported successfully")
        
        print("2. Importing _c_analyzer...")
        import django_mercury._c_analyzer
        print("   ✓ _c_analyzer imported successfully")
        
        print("3. Importing _c_orchestrator...")
        import django_mercury._c_orchestrator
        print("   ✓ _c_orchestrator imported successfully")
        
        print("\nTesting loader system...")
        from django_mercury.python_bindings.loader import get_implementation_info, check_c_extensions
        
        info = get_implementation_info()
        print(f"\nImplementation info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        available, details = check_c_extensions()
        print(f"\nC extensions available: {available}")
        print(f"Details:")
        for key, value in details.items():
            print(f"  {key}: {value}")
        
        if available:
            print("\n✅ Success! C extensions are working on Windows!")
            return True
        else:
            print("\n❌ C extensions loaded but not functional")
            return False
            
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nFalling back to pure Python implementation...")
        
        # Test pure Python fallback
        os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '1'
        from django_mercury.python_bindings.loader import get_implementation_info
        info = get_implementation_info()
        print(f"\nPure Python mode:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        return False

if __name__ == "__main__":
    success = test_windows_dll_loading()
    sys.exit(0 if success else 1)