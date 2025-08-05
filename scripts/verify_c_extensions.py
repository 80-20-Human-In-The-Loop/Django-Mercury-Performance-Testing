#!/usr/bin/env python3
"""
Verify C extension build and loading for Django Mercury.

This script helps debug C extension loading issues in CI and locally.
"""

import os
import sys
from pathlib import Path
import platform

def check_library_files():
    """Check for built library files."""
    print("🔍 Checking for C library files...")
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print()
    
    # Expected library extension
    if platform.system() == "Linux":
        ext = ".so"
    elif platform.system() == "Darwin":
        ext = ".dylib"
    elif platform.system() == "Windows":
        ext = ".dll"
    else:
        ext = ".so"
    
    # Check various locations
    project_root = Path(__file__).parent.parent
    locations = [
        project_root / "django_mercury" / "c_core",
        project_root / "django_mercury" / "python_bindings",
        project_root / "django_mercury",
    ]
    
    found_libs = []
    for location in locations:
        if location.exists():
            libs = list(location.glob(f"*{ext}"))
            if libs:
                print(f"✅ Found in {location}:")
                for lib in libs:
                    print(f"   - {lib.name}")
                    found_libs.append(lib)
            else:
                print(f"❌ No {ext} files in {location}")
    
    print(f"\nTotal libraries found: {len(found_libs)}")
    return found_libs

def test_c_extensions():
    """Test loading C extensions."""
    print("\n🧪 Testing C extension loading...")
    
    # Set debug mode
    os.environ['DEBUG_C_LOADING'] = '1'
    
    try:
        from django_mercury.python_bindings.loader import (
            check_c_extensions, 
            get_implementation_info,
            get_performance_monitor
        )
        
        # Get implementation info
        info = get_implementation_info()
        print(f"\nImplementation type: {info['type']}")
        print(f"C extensions available: {info['c_extensions_available']}")
        print(f"Forced pure Python: {info['forced_pure_python']}")
        
        # Check extensions
        available, details = check_c_extensions()
        print(f"\nC extensions functional: {available}")
        if 'error' in details:
            print(f"Error: {details['error']}")
        
        # Try to create a monitor
        print("\n🔨 Testing monitor creation...")
        Monitor = get_performance_monitor()
        monitor = Monitor()
        print(f"Monitor class: {Monitor.__name__}")
        print(f"Monitor instance: {type(monitor)}")
        
        # Check if it's actually using C
        if hasattr(monitor, '_using_fallback'):
            print(f"Using fallback: {monitor._using_fallback}")
        
        return available
        
    except Exception as e:
        print(f"❌ Error testing C extensions: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification function."""
    print("Django Mercury C Extension Verification")
    print("=" * 50)
    
    # Check library files
    libs = check_library_files()
    
    # Test loading
    functional = test_c_extensions()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    if libs and functional:
        print("✅ C extensions are built and functional!")
        return 0
    elif libs and not functional:
        print("⚠️  Libraries found but not loading correctly")
        print("   Check library dependencies and Python paths")
        return 1
    else:
        print("❌ No C libraries found")
        print("   Run: cd django_mercury/c_core && make && make install")
        return 2

if __name__ == "__main__":
    sys.exit(main())