#!/usr/bin/env python3
"""
Build Verification Script for Django Mercury

This script verifies that Django Mercury is properly installed and configured.
Django Mercury is now a pure Python package with no C extensions.
"""

import os
import sys
from pathlib import Path
from typing import Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_environment() -> Dict[str, str]:
    """Check environment variables."""
    env_vars = {
        'CI': os.environ.get('CI', 'not set'),
        'GITHUB_ACTIONS': os.environ.get('GITHUB_ACTIONS', 'not set'),
        'PYTHONPATH': os.environ.get('PYTHONPATH', 'not set'),
    }
    
    return env_vars


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
    
    # 2. Test Python imports
    print("🐍 PYTHON IMPORTS:")
    print("-" * 40)
    imports = verify_python_imports()
    for module, success in imports.items():
        marker = "✓" if success else "✗"
        print(f"  {marker} {module}")
    print()
    
    # 3. Test implementation status
    print("🔧 IMPLEMENTATION STATUS:")
    print("-" * 40)
    if imports.get('c_bindings'):
        from django_mercury.python_bindings import c_bindings
        
        # Should always be False now (pure Python only)
        available = c_bindings.HAS_C_EXTENSIONS
        
        print(f"  Pure Python Mode: ✓ (Always enabled)")
        print(f"  C Extensions: {'✗ Removed' if not available else '⚠️ Unexpected'}")
        
        if available:
            print("  ⚠️ WARNING: C extensions should not be available!")
    else:
        print("  ✗ Cannot import c_bindings module")
    print()
    
    # 4. Summary
    print("=" * 70)
    print("SUMMARY:")
    print("-" * 40)
    
    # Determine overall status
    issues = []
    
    if not imports.get('django_mercury'):
        issues.append("Cannot import django_mercury")
    
    if not imports.get('pure_python'):
        issues.append("Cannot import pure_python module")
    
    if issues:
        print("❌ BUILD VERIFICATION FAILED")
        print()
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("Recommendations:")
        print("  1. Ensure package is properly installed: pip install -e .")
        print("  2. Check that all Python modules are present")
        print("  3. Verify Python version is >= 3.10")
        sys.exit(1)
    else:
        print("✅ BUILD VERIFICATION PASSED")
        print()
        print("  Django Mercury is properly installed")
        print("  Running in pure Python mode (no C extensions)")
        sys.exit(0)


if __name__ == '__main__':
    main()