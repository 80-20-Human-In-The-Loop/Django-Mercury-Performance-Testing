#!/usr/bin/env bash
#
# CI Test Runner for Django Mercury
# Wraps all test logic for CI/CD environments
#
# Usage:
#   ./scripts/ci_test_runner.sh [linux|macos|windows]
#
# Exit codes:
#   0 - All tests passed
#   1 - C extension build failed
#   2 - C extension loading failed
#   3 - Python tests failed
#   4 - Invalid platform specified

set -e

# Get platform
PLATFORM=${1:-linux}

echo "=========================================="
echo "Django Mercury CI Test Runner"
echo "Platform: $PLATFORM"
echo "=========================================="
echo ""

# Change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Export CI environment variables
export DJANGO_MERCURY_PURE_PYTHON=0
export DEBUG_C_LOADING=1
export MERCURY_DEFER_INIT=1  # Prevent auto-initialization on import
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"

echo "Environment:"
echo "  DJANGO_MERCURY_PURE_PYTHON=$DJANGO_MERCURY_PURE_PYTHON"
echo "  DEBUG_C_LOADING=$DEBUG_C_LOADING"
echo "  MERCURY_DEFER_INIT=$MERCURY_DEFER_INIT"
echo "  PYTHONPATH=$PYTHONPATH"
echo ""

case $PLATFORM in
  linux|macos)
    echo "=== Building C Extensions ==="
    
    # Build raw .so libraries using Makefile (for c_bindings.py)
    echo "Building raw C libraries..."
    cd django_mercury/c_core
    if ! make ci; then
      echo "❌ ERROR: C library build failed!"
      exit 1
    fi
    cd "$PROJECT_ROOT"
    
    # Also build Python extensions for loader.py tests
    echo "Building Python extension modules..."
    if python setup.py build_ext --inplace 2>&1; then
      echo "✅ Python extensions built successfully"
      # List the built extensions
      find . -name "_c_*.cpython*.so" -o -name "_c_*.so" | head -10
    else
      echo "⚠️  Python extensions build failed - loader.py will use pure Python fallback"
    fi
    
    echo ""
    echo "=== Verifying Build ==="
    if ! python scripts/verify_build.py; then
      echo "❌ ERROR: Build verification failed!"
      exit 1
    fi
    
    echo ""
    echo "=== Testing C Extension Loading ==="
    if ! python scripts/debug_c_extensions.py; then
      echo "❌ ERROR: C extensions not loading properly!"
      echo "Running detailed diagnostics..."
      ./scripts/test_c_loading.sh || true
      exit 2
    fi
    
    echo ""
    echo "=== Running Python Tests ==="
    if ! python test_runner.py --coverage --ci; then
      echo "❌ ERROR: Python tests failed!"
      exit 3
    fi
    
    echo ""
    echo "=== Running C Unit Tests ==="
    ./c_test_runner.sh test || echo "C tests completed with status: $?"
    
    if [ "$PLATFORM" == "linux" ]; then
      echo ""
      echo "=== Running C Coverage Analysis ==="
      ./c_test_runner.sh coverage || echo "Coverage completed with status: $?"
    fi
    ;;
    
  windows)
    echo "=== Windows Test Flow ==="
    
    # Test C extensions or pure Python fallback
    echo "Testing C extensions..."
    TEST_RESULT=$?
    
    if [ $TEST_RESULT -eq 0 ]; then
      echo "✅ Extension loading test passed!"
      # Check what mode we're in
      if [ "$C_EXTENSIONS_BUILT" = "1" ]; then
        echo "   Running with C extensions"
      else
        echo "   Running in pure Python mode"
      fi
    else
      echo "❌ Extension loading test failed (exit code: $TEST_RESULT)"
      # This is a real failure - neither C nor pure Python worked
      exit 2
    fi
    
    echo ""
    echo "=== Running Python Tests ==="
    if ! python test_runner.py --coverage --ci; then
      echo "❌ ERROR: Python tests failed!"
      exit 3
    fi
    ;;
    
  *)
    echo "❌ ERROR: Invalid platform '$PLATFORM'"
    echo "Usage: $0 [linux|macos|windows]"
    exit 4
    ;;
esac

echo ""
echo "=========================================="
echo "✅ All CI tests passed!"
echo "=========================================="
exit 0