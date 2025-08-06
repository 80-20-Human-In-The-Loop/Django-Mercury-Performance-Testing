#!/usr/bin/env python
"""
Test script to verify Windows loading strategy for C extensions.
This simulates what will happen on Windows CI.
"""

import os
import sys
import platform
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_windows_loading():
    """Test the Windows loading strategy."""
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print("-" * 60)
    
    # Force Windows mode for testing
    original_platform = platform.system
    if '--simulate-windows' in sys.argv:
        platform.system = lambda: "Windows"
        print("SIMULATING WINDOWS ENVIRONMENT")
        print("-" * 60)
    
    try:
        # Import c_bindings
        from django_mercury.python_bindings import c_bindings
        
        # Check platform detection
        print(f"IS_WINDOWS detected: {c_bindings.IS_WINDOWS}")
        
        # Check library configuration
        print("\nLibrary Configuration:")
        for lib_key, lib_config in c_bindings.LIBRARY_CONFIG.items():
            print(f"  {lib_key}: {lib_config['name']}")
        
        # Try to initialize
        print("\nAttempting to initialize C extensions...")
        c_bindings.initialize_c_extensions(force_reinit=True)
        
        # Check what got loaded
        ext = c_bindings.c_extensions
        print("\nLoaded extensions:")
        print(f"  query_analyzer: {type(ext.query_analyzer).__name__ if ext.query_analyzer else 'None'}")
        print(f"  metrics_engine: {type(ext.metrics_engine).__name__ if ext.metrics_engine else 'None'}")
        print(f"  test_orchestrator: {type(ext.test_orchestrator).__name__ if ext.test_orchestrator else 'None'}")
        
        # Check if we're in fallback mode
        if not any([ext.query_analyzer, ext.metrics_engine, ext.test_orchestrator]):
            print("\n⚠️  No C extensions loaded - will use Python fallback")
        else:
            print("\n✅ C extensions loaded successfully!")
            
            # On Windows, check if they're Python modules
            if c_bindings.IS_WINDOWS:
                if ext.query_analyzer and hasattr(ext.query_analyzer, '__file__'):
                    print("   ✓ Extensions are Python modules (correct for Windows)")
                elif ext.query_analyzer:
                    print("   ✗ Extensions are CDLL objects (incorrect for Windows)")
            else:
                if ext.query_analyzer and not hasattr(ext.query_analyzer, '__file__'):
                    print("   ✓ Extensions are CDLL objects (correct for Unix)")
                elif ext.query_analyzer:
                    print("   ✗ Extensions are Python modules (incorrect for Unix)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original platform function
        if '--simulate-windows' in sys.argv:
            platform.system = original_platform

if __name__ == "__main__":
    print("=" * 60)
    print("Django Mercury Windows Loading Test")
    print("=" * 60)
    
    success = test_windows_loading()
    
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED")
    else:
        print("TEST FAILED")
    print("=" * 60)
    
    sys.exit(0 if success else 1)