#!/usr/bin/env bash
#
# Test C Extension Loading
# Simple shell script to test if C extensions can be loaded
#
# Usage:
#   ./scripts/test_c_loading.sh
#
# Exit codes:
#   0 - All C extensions loaded successfully
#   1 - No .so files found
#   2 - Some .so files failed to load
#   3 - Python import of C extensions failed

set -e

# Colors (disabled in CI)
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    RESET=""
else
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    RESET='\033[0m'
fi

echo "=========================================="
echo "C Extension Loading Test"
echo "=========================================="
echo ""

# Get the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo ""

# Find .so files
echo "Looking for C library files..."
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    SO_FILES=$(find django_mercury -name "*.so" -o -name "*.dylib" 2>/dev/null || true)
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # Linux
    SO_FILES=$(find django_mercury -name "*.so" 2>/dev/null || true)
else
    # Windows (Git Bash)
    SO_FILES=$(find django_mercury -name "*.dll" -o -name "*.pyd" 2>/dev/null || true)
fi

if [ -z "$SO_FILES" ]; then
    echo -e "${RED}✗ No C library files found!${RESET}"
    echo "Please build them first:"
    echo "  cd django_mercury/c_core && make"
    exit 1
fi

echo -e "${GREEN}✓ Found C library files:${RESET}"
echo "$SO_FILES" | while read -r lib; do
    echo "  - $lib"
done
echo ""

# Test loading each library with Python ctypes
echo "Testing ctypes loading..."
FAILED=0
echo "$SO_FILES" | while read -r lib; do
    if [ -z "$lib" ]; then
        continue
    fi
    
    echo -n "  $lib ... "
    if python -c "import ctypes; ctypes.CDLL('$lib')" 2>/dev/null; then
        echo -e "${GREEN}✓ OK${RESET}"
    else
        echo -e "${RED}✗ FAILED${RESET}"
        FAILED=1
        
        # Try to get more info about why it failed
        if [ "$(uname)" == "Linux" ]; then
            echo "    Dependencies:"
            ldd "$lib" 2>&1 | grep -E "(not found|=>)" | sed 's/^/      /'
        fi
    fi
done

if [ $FAILED -eq 1 ]; then
    echo ""
    echo -e "${RED}Some libraries failed to load!${RESET}"
    exit 2
fi

echo ""
echo "Testing Django Mercury import..."

# Test actual import
python << 'EOF'
import os
import sys

# Enable debug mode
os.environ['DEBUG_C_LOADING'] = '1'

try:
    from django_mercury.python_bindings.loader import check_c_extensions, get_implementation_info
    
    available, details = check_c_extensions()
    info = get_implementation_info()
    
    print(f"  C Extensions Available: {available}")
    print(f"  Implementation Type: {info.get('type', 'unknown')}")
    
    if available:
        print("\n✓ C extensions are working!")
        sys.exit(0)
    else:
        print(f"\n✗ C extensions not available: {details}")
        sys.exit(3)
        
except Exception as e:
    print(f"\n✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(3)
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "SUCCESS: All C extensions working!"
    echo -e "==========================================${RESET}"
else
    echo -e "${RED}=========================================="
    echo "FAILED: C extensions not working!"
    echo -e "==========================================${RESET}"
fi

exit $EXIT_CODE