#!/bin/bash
# Django Mercury C Core Test Runner
# Easy helper script to run C tests from anywhere in the project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Find project root (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
C_CORE_DIR="$SCRIPT_DIR/django_mercury/c_core"

# Parse command line arguments
COMMAND=""
DEBUG=0
EXPLAIN=0
SPECIFIC_TEST=""
FIX_ONLY=0

# Process arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG=1
            export TEST_DEBUG=1
            shift
            ;;
        --explain)
            EXPLAIN=1
            shift
            ;;
        --fix-only)
            FIX_ONLY=1
            shift
            ;;
        --single)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        test|tests|coverage|all|clean|build|benchmark|memcheck|help|--help|-h|enhanced)
            COMMAND="$1"
            shift
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            fi
            shift
            ;;
    esac
done

# Default command if none specified
COMMAND="${COMMAND:-test}"

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
        
    enhanced)
        print_info "Running enhanced tests with educational features..."
        check_requirements || exit 1
        
        # Set up for enhanced testing
        export TEST_DEBUG=$DEBUG
        
        cd "$C_CORE_DIR" || exit 1
        
        # Compile with enhanced framework
        echo -e "${BLUE}🔨 Building enhanced tests...${NC}"
        
        # Build the comprehensive test with fixes
        gcc -g -O0 -DUSE_ENHANCED_TESTS \
            -I./tests \
            -o tests/coverage/comprehensive_test_query_analyzer_enhanced \
            tests/comprehensive_test_query_analyzer.c \
            query_analyzer.c common.c \
            -lm -pthread
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Build successful${NC}\n"
            
            # Run the enhanced test
            echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
            echo -e "${BOLD}Running Enhanced Tests with Educational Features${NC}"
            echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}\n"
            
            if [ $DEBUG -eq 1 ]; then
                echo -e "${YELLOW}🔍 Debug mode enabled${NC}"
            fi
            
            if [ $EXPLAIN -eq 1 ]; then
                echo -e "${YELLOW}📚 Educational explanations enabled${NC}\n"
            fi
            
            # Run the test
            tests/coverage/comprehensive_test_query_analyzer_enhanced
            EXIT_CODE=$?
            
            if [ $EXIT_CODE -ne 0 ] && [ $EXPLAIN -eq 1 ]; then
                echo -e "\n${YELLOW}📚 Educational Analysis:${NC}"
                echo -e "${DIM}The test failures above show detailed information about${NC}"
                echo -e "${DIM}what was expected vs what was actually returned.${NC}\n"
                
                echo -e "${MAGENTA}💡 Common Issues:${NC}"
                echo "  • Boundary conditions: Check if values at exact boundaries"
                echo "    (like 12 queries) trigger different behavior than expected"
                echo "  • String format mismatches: Verify the exact text format"
                echo "    (e.g., 'queries' vs 'occurrences')"
                echo "  • Off-by-one errors: Common in loop and array operations\n"
            fi
            
            if [ $EXIT_CODE -eq 0 ]; then
                print_success "All enhanced tests passed!"
            else
                print_warning "Some tests failed - review the output above"
            fi
        else
            print_error "Failed to build enhanced tests"
            exit 1
        fi
        ;;
        
    help|--help|-h)
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "${BOLD}Commands:${NC}"
        echo "  test       Run simple C tests (default)"
        echo "  coverage   Run tests with coverage analysis"
        echo "  enhanced   Run tests with enhanced debugging features"
        echo "  all        Run all tests and coverage"
        echo "  clean      Clean test artifacts"
        echo "  build      Build C libraries only"
        echo "  benchmark  Run performance benchmarks"
        echo "  memcheck   Run memory safety checks (Linux only)"
        echo "  help       Show this help message"
        echo ""
        echo "${BOLD}Options:${NC}"
        echo "  --debug    Enable debug mode with verbose output"
        echo "  --explain  Enable educational mode with explanations"
        echo "  --single TEST  Run a specific test file"
        echo "  --fix-only Only compile with fixes, don't run"
        echo ""
        echo "${BOLD}Environment Variables:${NC}"
        echo "  TEST_DEBUG=1  Enable debug output in tests"
        echo "  TEST_TRACE=1  Enable function tracing"
        echo ""
        echo "${BOLD}Examples:${NC}"
        echo "  $0                      # Run simple tests"
        echo "  $0 coverage             # Run with coverage"
        echo "  $0 enhanced --debug     # Enhanced tests with debug"
        echo "  $0 enhanced --explain   # Enhanced tests with explanations"
        echo "  $0 all                  # Run everything"
        echo ""
        echo "${BOLD}Educational Features (enhanced mode):${NC}"
        echo "  • Detailed failure messages with expected vs actual values"
        echo "  • Hex dumps for buffer comparisons"
        echo "  • Query analyzer state inspection"
        echo "  • Memory leak detection"
        echo "  • Performance timing information"
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