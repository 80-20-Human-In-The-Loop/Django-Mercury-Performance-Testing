#!/usr/bin/env python3
"""
Build Verification Script for Django Mercury

This script verifies that the C extensions are properly built and installed.
It's designed to help debug CI/CD build issues.
"""

import os
import sys
import ctypes
import platform
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_environment() -> Dict[str, str]:
    """Check environment variables."""
    env_vars = {
        'CI': os.environ.get('CI', 'not set'),
        'GITHUB_ACTIONS': os.environ.get('GITHUB_ACTIONS', 'not set'),
        'DJANGO_MERCURY_PURE_PYTHON': os.environ.get('DJANGO_MERCURY_PURE_PYTHON', 'not set'),
        'DEBUG_C_LOADING': os.environ.get('DEBUG_C_LOADING', 'not set'),
        'PYTHONPATH': os.environ.get('PYTHONPATH', 'not set'),
        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', 'not set'),
    }
    
    return env_vars


def find_library_files() -> Dict[str, List[Path]]:
    """Find all library files in the project."""
    root = Path(__file__).parent.parent
    libraries = {
        'libquery_analyzer': [],
        'libmetrics_engine': [],
        'libtest_orchestrator': [],
        'libperformance': [],
    }
    
    # Search patterns based on platform
    if platform.system() == 'Windows':
        extensions = ['.dll']
    elif platform.system() == 'Darwin':
        extensions = ['.so', '.dylib']
    else:
        extensions = ['.so']
    
    # Search locations
    search_dirs = [
        root / 'django_mercury' / 'c_core',
        root / 'django_mercury' / 'python_bindings',
        root / 'build',
        root / 'dist',
    ]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for ext in extensions:
            for lib_base in libraries.keys():
                pattern = f"{lib_base}{ext}"
                found = list(search_dir.glob(pattern))
                libraries[lib_base].extend(found)
    
    return libraries


def test_library_loading(lib_path: Path) -> Tuple[bool, str]:
    """Test if a library can be loaded."""
    try:
        lib = ctypes.CDLL(str(lib_path))
        return True, "Successfully loaded"
    except OSError as e:
        return False, f"Failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_library_symbols(lib_path: Path) -> List[str]:
    """Check what symbols are exported by a library."""
    try:
        lib = ctypes.CDLL(str(lib_path))
        
        # Common functions we expect
        expected_functions = [
            'start_performance_monitoring_enhanced',
            'stop_performance_monitoring_enhanced',
            'get_elapsed_time_ms',
            'get_memory_usage_mb',
            'analyze_query',
            'create_test_context',
        ]
        
        found_functions = []
        for func_name in expected_functions:
            try:
                func = getattr(lib, func_name)
                found_functions.append(func_name)
            except AttributeError:
                pass
        
        return found_functions
    except Exception:
        return []


def verify_python_imports() -> Dict[str, bool]:
    """Verify Python imports work."""
    imports = {}
    
    # Try basic imports
    try:
        import django_mercury
        imports['django_mercury'] = True
    except ImportError:
        imports['django_mercury'] = False
    
    try:
        from django_mercury.python_bindings import c_bindings
        imports['c_bindings'] = True
    except ImportError:
        imports['c_bindings'] = False
    
    try:
        from django_mercury.python_bindings import monitor
        imports['monitor'] = True
    except ImportError:
        imports['monitor'] = False
    
    try:
        from django_mercury.python_bindings import pure_python
        imports['pure_python'] = True
    except ImportError:
        imports['pure_python'] = False
    
    return imports


def main():
    """Main verification routine."""
    print("=" * 70)
    print("Django Mercury Build Verification")
    print("=" * 70)
    print()
    
    # 1. Check environment
    print("📋 ENVIRONMENT VARIABLES:")
    print("-" * 40)
    env_vars = check_environment()
    for var, value in env_vars.items():
        marker = "✓" if value != "not set" else "✗"
        print(f"  {marker} {var}: {value}")
    print()
    
    # 2. Find library files
    print("📚 LIBRARY FILES:")
    print("-" * 40)
    libraries = find_library_files()
    total_found = 0
    for lib_name, paths in libraries.items():
        if paths:
            print(f"  ✓ {lib_name}:")
            for path in paths:
                print(f"    - {path}")
                # Test loading
                success, msg = test_library_loading(path)
                if success:
                    print(f"      ✓ Can load: {msg}")
                    # Check symbols
                    symbols = check_library_symbols(path)
                    if symbols:
                        print(f"      ✓ Found {len(symbols)} expected symbols")
                else:
                    print(f"      ✗ Cannot load: {msg}")
            total_found += len(paths)
        else:
            print(f"  ✗ {lib_name}: Not found")
    
    if total_found == 0:
        print("  ⚠️  No library files found!")
    print()
    
    # 3. Test Python imports
    print("🐍 PYTHON IMPORTS:")
    print("-" * 40)
    imports = verify_python_imports()
    for module, success in imports.items():
        marker = "✓" if success else "✗"
        print(f"  {marker} {module}")
    print()
    
    # 4. Test C extension availability
    print("🔧 C EXTENSION STATUS:")
    print("-" * 40)
    if imports.get('c_bindings'):
        from django_mercury.python_bindings import c_bindings
        
        # Initialize C extensions if deferred initialization is enabled
        if os.environ.get("MERCURY_DEFER_INIT", "0") == "1":
            print("  Initializing C extensions (MERCURY_DEFER_INIT=1)...")
            init_success = c_bindings.initialize_c_extensions()
            print(f"  Initialization result: {init_success}")
        
        available = c_bindings.are_c_extensions_available()
        pure_python = c_bindings.is_pure_python_mode()
        
        print(f"  C Extensions Available: {available}")
        print(f"  Pure Python Mode: {pure_python}")
        
        # Try to get stats
        stats = c_bindings.c_extensions.get_stats()
        print(f"  Libraries Loaded: {stats.libraries_loaded}")
        print(f"  Functions Configured: {stats.functions_configured}")
        
        if stats.errors_encountered > 0:
            print(f"  ⚠️  Errors Encountered: {stats.errors_encountered}")
    else:
        print("  ✗ Cannot import c_bindings module")
    print()
    
    # 5. Summary
    print("=" * 70)
    print("SUMMARY:")
    print("-" * 40)
    
    # Determine overall status
    issues = []
    
    if total_found == 0:
        issues.append("No C library files found")
    
    if not imports.get('django_mercury'):
        issues.append("Cannot import django_mercury")
    
    if env_vars['CI'] != 'not set' and total_found == 0:
        issues.append("Running in CI but no libraries built")
    
    if issues:
        print("❌ BUILD VERIFICATION FAILED")
        print()
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("Recommendations:")
        print("  1. Check that 'make all' completed successfully")
        print("  2. Verify libraries are copied to python_bindings/")
        print("  3. Check compilation errors in build logs")
        print("  4. Ensure build dependencies are installed")
        sys.exit(1)
    else:
        print("✅ BUILD VERIFICATION PASSED")
        print()
        if env_vars['DJANGO_MERCURY_PURE_PYTHON'] == '1':
            print("  Running in pure Python mode (as configured)")
        elif total_found > 0:
            print(f"  Found {total_found} C library file(s)")
            print("  C extensions should be available")
        else:
            print("  No C libraries found, will use pure Python fallback")
        sys.exit(0)


if __name__ == '__main__':
    main()