#!/bin/bash
# Django Mercury C Core Test Runner
# Easy helper script to run C tests from anywhere in the project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Find project root (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
C_CORE_DIR="$SCRIPT_DIR/django_mercury/c_core"

# Default command
COMMAND="${1:-test}"

# Save current directory to return later
ORIGINAL_DIR=$(pwd)

# Function to print colored messages
print_header() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          Django Mercury C Core Test Runner                ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to run make command in c_core directory
run_c_tests() {
    local cmd=$1
    local description=$2
    
    echo -e "${CYAN}🔧 $description${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    cd "$C_CORE_DIR" || {
        print_error "Failed to navigate to C core directory: $C_CORE_DIR"
        exit 1
    }
    
    if make $cmd; then
        print_success "$description completed successfully!"
        return 0
    else
        print_error "$description failed!"
        return 1
    fi
}

# Function to check for required tools
check_requirements() {
    local missing_tools=()
    
    # Check for gcc or clang
    if ! command -v gcc &> /dev/null && ! command -v clang &> /dev/null; then
        missing_tools+=("gcc/clang")
    fi
    
    # Check for make
    if ! command -v make &> /dev/null; then
        missing_tools+=("make")
    fi
    
    # Check for gcov (for coverage)
    if [[ "$1" == "coverage" ]] && ! command -v gcov &> /dev/null; then
        missing_tools+=("gcov")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo ""
        echo "Installation instructions:"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "  Ubuntu/Debian: sudo apt-get install build-essential"
            echo "  RHEL/CentOS: sudo yum install gcc make"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  macOS: xcode-select --install"
        fi
        return 1
    fi
    return 0
}

# Main script
print_header

# Check if c_core directory exists
if [ ! -d "$C_CORE_DIR" ]; then
    print_error "C core directory not found: $C_CORE_DIR"
    exit 1
fi

# Check if Makefile exists
if [ ! -f "$C_CORE_DIR/Makefile" ]; then
    print_error "Makefile not found in: $C_CORE_DIR"
    exit 1
fi

case "$COMMAND" in
    test|tests)
        print_info "Running simple C tests..."
        check_requirements || exit 1
        run_c_tests "test" "Simple tests"
        ;;
        
    coverage)
        print_info "Running C tests with coverage analysis..."
        check_requirements "coverage" || exit 1
        run_c_tests "coverage" "Coverage analysis"
        ;;
        
    all)
        print_info "Running all C tests and coverage..."
        check_requirements "coverage" || exit 1
        
        # Run simple tests first
        run_c_tests "test" "Simple tests"
        echo ""
        
        # Then run coverage
        run_c_tests "coverage" "Coverage analysis"
        ;;
        
    clean)
        print_info "Cleaning C test artifacts..."
        run_c_tests "clean" "Clean"
        run_c_tests "clean-coverage" "Clean coverage" 2>/dev/null || true
        ;;
        
    build)
        print_info "Building C libraries..."
        check_requirements || exit 1
        run_c_tests "all" "Build libraries"
        ;;
        
    benchmark)
        print_info "Running performance benchmarks..."
        check_requirements || exit 1
        run_c_tests "benchmark" "Performance benchmark"
        ;;
        
    memcheck)
        print_info "Running memory safety checks..."
        check_requirements || exit 1
        run_c_tests "memcheck" "Memory check"
        ;;
        
    help|--help|-h)
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  test       Run simple C tests (default)"
        echo "  coverage   Run tests with coverage analysis"
        echo "  all        Run all tests and coverage"
        echo "  clean      Clean test artifacts"
        echo "  build      Build C libraries only"
        echo "  benchmark  Run performance benchmarks"
        echo "  memcheck   Run memory safety checks (Linux only)"
        echo "  help       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0              # Run simple tests"
        echo "  $0 coverage     # Run with coverage"
        echo "  $0 all          # Run everything"
        ;;
        
    *)
        print_error "Unknown command: $COMMAND"
        echo "Run '$0 help' for usage information"
        cd "$ORIGINAL_DIR"
        exit 1
        ;;
esac

# Return to original directory
cd "$ORIGINAL_DIR"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Print summary based on command
if [[ "$COMMAND" == "coverage" ]] || [[ "$COMMAND" == "all" ]]; then
    # Try to show coverage summary if it exists
    COVERAGE_FILE="$C_CORE_DIR/tests/coverage/coverage_summary.txt"
    if [ -f "$COVERAGE_FILE" ]; then
        echo -e "${GREEN}📊 Coverage Summary:${NC}"
        tail -n 20 "$COVERAGE_FILE" 2>/dev/null || true
    fi
fi

print_success "C test runner completed!"