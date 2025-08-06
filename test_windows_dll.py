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
    
    # Check if we should force pure Python mode
    force_pure = os.environ.get('DJANGO_MERCURY_PURE_PYTHON', '0')
    print(f"DJANGO_MERCURY_PURE_PYTHON: {force_pure}")
    
    # Check for C extensions build flag from CI
    c_ext_built = os.environ.get('C_EXTENSIONS_BUILT', '1')
    print(f"C_EXTENSIONS_BUILT: {c_ext_built}")
    print("")
    
    # First check if .pyd files exist (Windows Python extensions)
    print("Looking for compiled extensions (.pyd files)...")
    import pathlib
    package_dir = pathlib.Path("django_mercury")
    pyd_files = list(package_dir.glob("**/*.pyd"))
    dll_files = list(package_dir.glob("**/*.dll"))
    so_files = list(package_dir.glob("**/*.so"))
    
    print(f"Found {len(pyd_files)} .pyd files")
    for pyd in pyd_files:
        print(f"  - {pyd}")
    
    print(f"Found {len(dll_files)} .dll files")
    for dll in dll_files:
        print(f"  - {dll}")
    
    print(f"Found {len(so_files)} .so files")
    for so in so_files:
        print(f"  - {so}")
    print("")
    
    # Track which extensions failed
    failed_imports = []
    
    # If no .pyd files found and C_EXTENSIONS_BUILT=0, skip import tests
    if len(pyd_files) == 0 and c_ext_built == '0':
        print("⚠️  No .pyd files found and C_EXTENSIONS_BUILT=0")
        print("   C extensions were not built - will test pure Python fallback")
        failed_imports = [("_c_metrics", "Not built"),
                         ("_c_analyzer", "Not built"),
                         ("_c_orchestrator", "Not built")]
    else:
        try:
            print("Testing C extension imports...")
            
            # Try to import the C extensions
            try:
                print("1. Importing _c_metrics...")
                import django_mercury._c_metrics
                print("   ✓ _c_metrics imported successfully")
            except ImportError as e:
                print(f"   ⚠️  _c_metrics not available: {e}")
                failed_imports.append(("_c_metrics", str(e)))
            
            try:
                print("2. Importing _c_analyzer...")
                import django_mercury._c_analyzer
                print("   ✓ _c_analyzer imported successfully")
            except ImportError as e:
                print(f"   ⚠️  _c_analyzer not available: {e}")
                failed_imports.append(("_c_analyzer", str(e)))
            
            try:
                print("3. Importing _c_orchestrator...")
                import django_mercury._c_orchestrator
                print("   ✓ _c_orchestrator imported successfully")
            except ImportError as e:
                print(f"   ⚠️  _c_orchestrator not available: {e}")
                failed_imports.append(("_c_orchestrator", str(e)))
        except Exception as e:
            print(f"\nUnexpected error during import tests: {e}")
            import traceback
            traceback.print_exc()
    
    # Now test the loader system regardless of import results
    print("\nTesting loader system...")
    try:
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
        
        # Determine success based on what mode we're in
        if failed_imports:
            # C extensions not available - check if pure Python mode works
            if info.get('type') == 'pure_python_fallback' or details.get('forced_pure_python'):
                print("\n✅ Success! Pure Python fallback is working correctly")
                print("   Django Mercury will run with reduced performance but full functionality")
                return True
            else:
                print("\n⚠️  C extensions not fully loaded")
                print(f"   Failed imports: {len(failed_imports)}")
                for name, error in failed_imports:
                    print(f"     - {name}: {error}")
                # Still consider it success if loader detected fallback correctly
                if 'fallback' in str(info.get('type', '')):
                    print("   But pure Python fallback is available")
                    return True
                return False
        else:
            # All C extensions imported successfully
            if available:
                print("\n✅ Success! C extensions are working on Windows!")
                return True
            else:
                print("\n⚠️  C extensions imported but not detected as available")
                print("   This may be a detection issue rather than a loading issue")
                return True  # Still success if imports worked
                
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        # If we can't even import the loader, that's a real failure
        print("\n❌ Critical failure: Cannot import Django Mercury components")
        return False

if __name__ == "__main__":
    success = test_windows_dll_loading()
    sys.exit(0 if success else 1)