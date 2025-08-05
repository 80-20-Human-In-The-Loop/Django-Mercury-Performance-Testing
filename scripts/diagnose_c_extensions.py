#!/usr/bin/env python
"""Diagnose C extension build and loading issues."""

import os
import sys
import platform
import pathlib
import subprocess

def main():
    print("=== C Extension Diagnostics ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()}")
    print(f"Machine: {platform.machine()}")
    print()
    
    # Check environment variables
    print("Environment variables:")
    for var in ['DJANGO_MERCURY_PURE_PYTHON', 'PYTHONIOENCODING', 'CIBUILDWHEEL']:
        value = os.environ.get(var, '<not set>')
        print(f"  {var}: {value}")
    print()
    
    # Check for C compiler
    print("C Compiler check:")
    if platform.system() == 'Windows':
        # Check for MSVC
        try:
            result = subprocess.run(['where', 'cl.exe'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  MSVC found: {result.stdout.strip()}")
            else:
                print("  MSVC (cl.exe) not found in PATH")
        except Exception as e:
            print(f"  Error checking for MSVC: {e}")
            
        # Check for MinGW
        try:
            result = subprocess.run(['where', 'gcc.exe'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  GCC found: {result.stdout.strip()}")
            else:
                print("  GCC not found in PATH")
        except Exception as e:
            print(f"  Error checking for GCC: {e}")
    else:
        # Unix-like systems
        try:
            result = subprocess.run(['which', 'gcc'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  GCC found: {result.stdout.strip()}")
                # Get version
                version_result = subprocess.run(['gcc', '--version'], capture_output=True, text=True)
                if version_result.returncode == 0:
                    first_line = version_result.stdout.split('\n')[0]
                    print(f"  GCC version: {first_line}")
        except Exception as e:
            print(f"  Error checking for GCC: {e}")
    print()
    
    # Check for built extensions
    print("Looking for C extensions:")
    package_dir = pathlib.Path("django_mercury")
    
    # Extension patterns by platform
    if platform.system() == 'Windows':
        patterns = ['*.pyd', '*.dll']
    elif platform.system() == 'Darwin':
        patterns = ['*.so', '*.dylib']
    else:
        patterns = ['*.so']
    
    found_extensions = []
    for pattern in patterns:
        extensions = list(package_dir.glob(f"**/{pattern}"))
        found_extensions.extend(extensions)
        if extensions:
            print(f"  {pattern} files:")
            for ext in extensions:
                print(f"    - {ext}")
    
    if not found_extensions:
        print("  No C extensions found!")
    print()
    
    # Test imports
    print("Testing C extension imports:")
    extensions_to_test = ['_c_metrics', '_c_analyzer', '_c_orchestrator']
    import_results = []
    
    for ext_name in extensions_to_test:
        full_name = f"django_mercury.{ext_name}"
        try:
            print(f"  Importing {full_name}...", end=" ")
            __import__(full_name)
            # Use ASCII characters for better Windows compatibility
            success_marker = "OK" if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower() else "✓"
            print(f"{success_marker} SUCCESS")
            import_results.append((ext_name, True, None))
        except ImportError as e:
            # Use ASCII characters for better Windows compatibility
            fail_marker = "FAILED" if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower() else "✗"
            print(f"{fail_marker}: {e}")
            import_results.append((ext_name, False, str(e)))
    print()
    
    # Check loader
    print("Testing loader system:")
    try:
        from django_mercury.python_bindings.loader import get_implementation_info, check_c_extensions
        
        info = get_implementation_info()
        print("  Implementation info:")
        for key, value in info.items():
            print(f"    {key}: {value}")
        
        available, details = check_c_extensions()
        print(f"  C extensions available: {available}")
    except Exception as e:
        print(f"  Error testing loader: {e}")
    print()
    
    # Summary
    print("=== Summary ===")
    success_count = sum(1 for _, success, _ in import_results if success)
    total_count = len(import_results)
    
    # Use ASCII characters for better Windows compatibility
    is_utf = sys.stdout.encoding and 'utf' in sys.stdout.encoding.lower()
    
    if success_count == total_count:
        marker = "✅" if is_utf else "[OK]"
        print(f"{marker} All {total_count} C extensions loaded successfully!")
        return 0
    elif success_count > 0:
        marker = "⚠️ " if is_utf else "[WARNING]"
        print(f"{marker} {success_count}/{total_count} C extensions loaded")
        return 1
    else:
        marker = "❌" if is_utf else "[FAILED]"
        print(f"{marker} No C extensions could be loaded ({total_count} tested)")
        return 2

if __name__ == "__main__":
    sys.exit(main())