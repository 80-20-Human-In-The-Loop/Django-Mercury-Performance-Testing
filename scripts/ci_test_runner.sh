#!/usr/bin/env bash
#
# CI Test Runner for Django Mercury
# Runs tests in CI/CD environments
#
# Usage:
#   ./scripts/ci_test_runner.sh [linux|macos|windows]
#
# Exit codes:
#   0 - All tests passed
#   1 - Python tests failed
#   2 - Invalid platform specified

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

# Export environment variables
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"

echo "Environment:"
echo "  PYTHONPATH=$PYTHONPATH"
echo "  Python version: $(python --version)"
echo ""

case $PLATFORM in
  linux|macos|windows)
    echo "=== Installing Django Mercury ==="
    pip install -e .
    echo ""
    
    echo "=== Verifying Installation ==="
    python scripts/verify_build.py
    echo ""
    
    echo "=== Running Python Tests ==="
    pytest tests/ -v --tb=short
    echo ""
    
    echo "✅ All tests passed successfully!"
    exit 0
    ;;
    
  *)
    echo "❌ Invalid platform: $PLATFORM"
    echo "Valid options: linux, macos, windows"
    exit 2
    ;;
esac