#!/usr/bin/env python3
"""
Debug C Extension Loading Issues

This script provides comprehensive debugging for C extension loading problems.
It can be run locally or in CI to diagnose why C extensions aren't loading.

Usage:
    python scripts/debug_c_extensions.py [--verbose]
"""

import ctypes
import os
import sys
import platform
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Colors for output (disabled in CI)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @classmethod
    def disable(cls):
        cls.HEADER = ''
        cls.OKBLUE = ''
        cls.OKCYAN = ''
        cls.OKGREEN = ''
        cls.WARNING = ''
        cls.FAIL = ''
        cls.ENDC = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''

# Disable colors in CI
if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
    Colors.disable()

def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

def get_python_info() -> Dict[str, str]:
    """Get Python environment information."""
    return {
        'version': sys.version,
        'executable': sys.executable,
        'platform': platform.platform(),
        'architecture': platform.machine(),
        'sys.path': sys.path,
        'cwd': os.getcwd(),
        'ctypes_file': ctypes.__file__ if hasattr(ctypes, '__file__') else 'unknown',
    }

def find_libraries() -> Dict[str, List[Path]]:
    """Find all C library files in the project."""
    root = Path(__file__).parent.parent
    libraries = {
        'libquery_analyzer': [],
        'libmetrics_engine': [],
        'libtest_orchestrator': [],
    }
    
    # Platform-specific extensions
    if platform.system() == 'Windows':
        extensions = ['.dll', '.pyd']
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
                found = list(search_dir.rglob(pattern))
                libraries[lib_base].extend(found)
    
    return libraries

def test_ctypes_loading(lib_path: Path) -> Tuple[bool, str, Optional[ctypes.CDLL]]:
    """Test loading a library with ctypes."""
    try:
        # Try with RTLD_GLOBAL if available
        if hasattr(ctypes, 'RTLD_GLOBAL'):
            handle = ctypes.CDLL(str(lib_path), mode=ctypes.RTLD_GLOBAL)
        else:
            handle = ctypes.CDLL(str(lib_path))
        return True, "Successfully loaded", handle
    except OSError as e:
        return False, f"OSError: {e}", None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None

def check_library_dependencies(lib_path: Path) -> Optional[str]:
    """Check library dependencies using ldd/otool."""
    if platform.system() == 'Linux':
        try:
            result = subprocess.run(['ldd', str(lib_path)], 
                                  capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Failed to run ldd: {e}"
    elif platform.system() == 'Darwin':
        try:
            result = subprocess.run(['otool', '-L', str(lib_path)], 
                                  capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Failed to run otool: {e}"
    elif platform.system() == 'Windows':
        # On Windows, we can try dumpbin or Dependencies.exe if available
        return "Dependency checking not implemented for Windows"
    else:
        return "Unknown platform"

def check_library_symbols(handle: ctypes.CDLL) -> List[str]:
    """Check what symbols are available in a loaded library."""
    # Common functions we expect in our libraries
    expected_functions = {
        'libquery_analyzer': [
            'analyze_query',
            'get_duplicate_queries',
            'reset_query_analyzer',
        ],
        'libmetrics_engine': [
            'start_performance_monitoring_enhanced',
            'stop_performance_monitoring_enhanced',
            'free_metrics',
        ],
        'libtest_orchestrator': [
            'create_test_context',
            'update_test_context',
            'destroy_test_context',
        ],
    }
    
    found_functions = []
    # Try to find which library this is
    for lib_name, funcs in expected_functions.items():
        for func_name in funcs:
            try:
                func = getattr(handle, func_name)
                found_functions.append(func_name)
            except AttributeError:
                pass
    
    return found_functions

def test_django_mercury_import() -> Tuple[bool, str]:
    """Test importing Django Mercury and checking C extensions."""
    try:
        # Set debug mode
        os.environ['DEBUG_C_LOADING'] = '1'
        
        # Try to import
        import django_mercury
        from django_mercury.python_bindings.loader import (
            check_c_extensions, get_implementation_info
        )
        from django_mercury.python_bindings import c_bindings
        
        # Initialize C extensions if deferred initialization is enabled
        if os.environ.get("MERCURY_DEFER_INIT", "0") == "1":
            init_success = c_bindings.initialize_c_extensions()
            init_msg = f"  Deferred initialization: {'Success' if init_success else 'Failed'}\n"
        else:
            init_msg = ""
        
        # Check C extensions
        available, details = check_c_extensions()
        info = get_implementation_info()
        
        result = f"Django Mercury imported successfully\n"
        result += init_msg
        result += f"  Version: {getattr(django_mercury, '__version__', 'unknown')}\n"
        result += f"  C Extensions Available: {available}\n"
        result += f"  Implementation Type: {info.get('type', 'unknown')}\n"
        result += f"  Details: {details}"
        
        return available, result
    except Exception as e:
        return False, f"Import failed: {type(e).__name__}: {e}\n{traceback.format_exc()}"

def main():
    """Main debugging routine."""
    verbose = '--verbose' in sys.argv
    
    print_header("Django Mercury C Extension Debug Report")
    
    # 1. Python environment
    print_header("Python Environment")
    py_info = get_python_info()
    print(f"Version: {py_info['version'].strip()}")
    print(f"Executable: {py_info['executable']}")
    print(f"Platform: {py_info['platform']}")
    print(f"Architecture: {py_info['architecture']}")
    print(f"Working Directory: {py_info['cwd']}")
    print(f"ctypes module: {py_info['ctypes_file']}")
    
    if verbose:
        print("\nPython sys.path:")
        for i, path in enumerate(py_info['sys.path']):
            print(f"  {i:2d}. {path}")
    
    # 2. Find library files
    print_header("Library Files")
    libraries = find_libraries()
    total_found = 0
    
    for lib_name, paths in libraries.items():
        if paths:
            print_success(f"{lib_name}: Found {len(paths)} file(s)")
            for path in paths:
                print(f"    {path}")
                total_found += len(paths)
        else:
            print_error(f"{lib_name}: Not found")
    
    if total_found == 0:
        print_error("No C library files found!")
        print_info("Make sure to run 'make' in django_mercury/c_core/")
        sys.exit(1)
    
    # 3. Test ctypes loading
    print_header("ctypes Loading Test")
    all_loaded = True
    
    for lib_name, paths in libraries.items():
        for path in paths:
            print(f"\n{Colors.BOLD}Testing: {path}{Colors.ENDC}")
            print(f"  File size: {path.stat().st_size} bytes")
            print(f"  Permissions: {oct(path.stat().st_mode)}")
            
            success, msg, handle = test_ctypes_loading(path)
            if success:
                print_success(f"Loaded successfully: {msg}")
                
                # Check symbols
                symbols = check_library_symbols(handle)
                if symbols:
                    print_success(f"Found {len(symbols)} expected symbols")
                    if verbose:
                        for sym in symbols:
                            print(f"      - {sym}")
            else:
                print_error(f"Failed to load: {msg}")
                all_loaded = False
                
                # Check dependencies
                deps = check_library_dependencies(path)
                if deps:
                    print_warning("Library dependencies:")
                    for line in deps.split('\n'):
                        if line.strip():
                            print(f"    {line}")
                        # Check for "not found"
                        if "not found" in line.lower():
                            print_error(f"    Missing dependency: {line}")
    
    # 4. Test Django Mercury import
    print_header("Django Mercury Import Test")
    c_available, import_result = test_django_mercury_import()
    
    if c_available:
        print_success("C extensions loaded successfully")
    else:
        print_error("C extensions not available")
    
    print(import_result)
    
    # 5. Summary
    print_header("Summary")
    
    if total_found == 0:
        print_error("FAILED: No C libraries found")
        print_info("Run: cd django_mercury/c_core && make")
        exit_code = 2
    elif not all_loaded:
        print_error("FAILED: Some libraries could not be loaded with ctypes")
        print_info("Check the dependency errors above")
        print_info("On Linux: sudo apt-get install libunwind-dev")
        print_info("On macOS: brew install libunwind")
        exit_code = 3
    elif not c_available:
        print_error("FAILED: Django Mercury cannot use C extensions")
        print_info("Even though libraries exist and can be loaded by ctypes")
        print_info("Check the import errors above")
        exit_code = 4
    else:
        print_success("SUCCESS: All C extensions are working properly")
        exit_code = 0
    
    # Environment variables that might help
    print_header("Debugging Environment Variables")
    debug_vars = {
        'DJANGO_MERCURY_PURE_PYTHON': 'Force pure Python mode (1=yes)',
        'DEBUG_C_LOADING': 'Enable debug output (1=yes)',
        'LD_LIBRARY_PATH': 'Linux library search path',
        'DYLD_LIBRARY_PATH': 'macOS library search path',
        'PYTHONPATH': 'Python module search path',
    }
    
    for var, desc in debug_vars.items():
        value = os.environ.get(var, 'not set')
        if value != 'not set':
            print_info(f"{var}={value}")
        else:
            print(f"  {var}: {value} ({desc})")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()