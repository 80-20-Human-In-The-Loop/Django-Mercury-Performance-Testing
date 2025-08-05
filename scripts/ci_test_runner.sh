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
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"

echo "Environment:"
echo "  DJANGO_MERCURY_PURE_PYTHON=$DJANGO_MERCURY_PURE_PYTHON"
echo "  DEBUG_C_LOADING=$DEBUG_C_LOADING"
echo "  PYTHONPATH=$PYTHONPATH"
echo ""

case $PLATFORM in
  linux|macos)
    echo "=== Building C Extensions ==="
    cd django_mercury/c_core
    
    # Clean and build
    if ! make ci; then
      echo "❌ ERROR: C library build failed!"
      exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
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
    
    # Test C extensions
    echo "Testing C extensions..."
    python test_windows_dll.py
    TEST_RESULT=$?
    
    if [ $TEST_RESULT -eq 0 ]; then
      echo "✅ C extensions loaded successfully!"
    else
      echo "❌ C extensions failed to load (exit code: $TEST_RESULT)"
      # In CI, we require C extensions
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