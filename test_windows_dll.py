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
    
    # Track which extensions failed
    failed_imports = []
    
    try:
        print("Testing C extension imports...")
        
        # Try to import the C extensions
        try:
            print("1. Importing _c_metrics...")
            import django_mercury._c_metrics
            print("   ✓ _c_metrics imported successfully")
        except ImportError as e:
            print(f"   ❌ _c_metrics failed: {e}")
            failed_imports.append(("_c_metrics", str(e)))
        
        try:
            print("2. Importing _c_analyzer...")
            import django_mercury._c_analyzer
            print("   ✓ _c_analyzer imported successfully")
        except ImportError as e:
            print(f"   ❌ _c_analyzer failed: {e}")
            failed_imports.append(("_c_analyzer", str(e)))
        
        try:
            print("3. Importing _c_orchestrator...")
            import django_mercury._c_orchestrator
            print("   ✓ _c_orchestrator imported successfully")
        except ImportError as e:
            print(f"   ❌ _c_orchestrator failed: {e}")
            failed_imports.append(("_c_orchestrator", str(e)))
        
        # If any imports failed, report and exit
        if failed_imports:
            print("\n❌ C extension import failures:")
            for name, error in failed_imports:
                print(f"  - {name}: {error}")
            
            # Show diagnostics
            print("\nDiagnostics:")
            print("Looking for .pyd files in package:")
            import pathlib
            package_dir = pathlib.Path("django_mercury")
            pyd_files = list(package_dir.glob("**/*.pyd"))
            if pyd_files:
                for pyd in pyd_files:
                    print(f"  Found: {pyd}")
            else:
                print("  No .pyd files found!")
            
            return False
        
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
        
        if available and not failed_imports:
            print("\n✅ Success! C extensions are working on Windows!")
            return True
        else:
            print("\n❌ C extensions loaded but not functional")
            return False
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_windows_dll_loading()
    sys.exit(0 if success else 1)