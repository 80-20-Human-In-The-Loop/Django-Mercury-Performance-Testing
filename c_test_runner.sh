#!/bin/bash
# Django Mercury C Core Test Runner
# Easy helper script to run C tests from anywhere in the project
# Version: 2.0.0

set -e  # Exit on error
set -o pipefail  # Fail on pipe errors

# ============================================================================
# CONFIGURATION
# ============================================================================

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

# Paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
C_CORE_DIR="$SCRIPT_DIR/django_mercury/c_core"
TEST_DIR="$C_CORE_DIR/tests"
COVERAGE_DIR="$TEST_DIR/coverage"
CONSOLIDATION_DIR="$TEST_DIR/consolidation"
SECURITY_DIR="$TEST_DIR/security"

# Test executables (cached)
declare -a TEST_EXECUTABLES=(
    "simple_test_common"
    "simple_test_advanced"
    "simple_test_query_analyzer"
    "simple_test_metrics_engine"
    "simple_test_test_orchestrator"
    "comprehensive_test_test_orchestrator"
    "edge_test_test_orchestrator"
)

# ============================================================================
# COMMAND LINE PARSING
# ============================================================================

# Default values
COMMAND=""
DEBUG=0
EXPLAIN=0
SPECIFIC_TEST=""
FIX_ONLY=0
VERBOSE=0
SHOW_WARNINGS=0
PARALLEL=0
NO_BUILD=0
QUIET=0

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
        --verbose)
            VERBOSE=1
            export TEST_VERBOSE=1
            shift
            ;;
        --warnings)
            SHOW_WARNINGS=1
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
        --parallel)
            PARALLEL=1
            shift
            ;;
        --no-build)
            NO_BUILD=1
            shift
            ;;
        --quiet|-q)
            QUIET=1
            shift
            ;;
        test|tests|coverage|all|clean|build|benchmark|memcheck|help|--help|-h|enhanced|security|--security)
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

# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

# Function to print colored messages
print_header() {
    [ $QUIET -eq 1 ] && return
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          Django Mercury C Core Test Runner                ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    [ $QUIET -eq 1 ] && return
    echo -e "${GREEN}[PASS] $1${NC}"
}

print_error() {
    echo -e "${RED}[FAIL] $1${NC}" >&2
}

print_info() {
    [ $QUIET -eq 1 ] && return
    echo -e "${BLUE}[INFO] $1${NC}"
}

print_warning() {
    [ $QUIET -eq 1 ] && return
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_separator() {
    [ $QUIET -eq 1 ] && return
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Function to run make command in c_core directory
run_c_tests() {
    local cmd=$1
    local description=$2
    
    [ $QUIET -eq 0 ] && echo -e "${CYAN}🔧 $description${NC}"
    [ $QUIET -eq 0 ] && print_separator
    
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

# Check if test executables exist
check_test_binaries() {
    local missing=0
    for exe in "${TEST_EXECUTABLES[@]}"; do
        if [ ! -f "$C_CORE_DIR/$exe" ]; then
            missing=1
            break
        fi
    done
    return $missing
}

# Build test executables if needed
build_tests_if_needed() {
    if [ $NO_BUILD -eq 1 ]; then
        return 0
    fi
    
    if ! check_test_binaries || [ ! -f "$C_CORE_DIR/libquery_analyzer.so" ]; then
        print_info "Test executables not found, building first..."
        [ $QUIET -eq 0 ] && echo -e "${CYAN}🔨 Building C extensions and test executables...${NC}"
        
        cd "$C_CORE_DIR" || exit 1
        
        # First build the shared libraries
        if ! make all > /dev/null 2>&1; then
            print_error "Failed to build C extensions"
            echo ""
            echo "Build output above. Common issues:"
            echo "  - Missing dependencies (check error messages)"
            echo "  - Compilation errors in C code"
            echo "  - Permission issues"
            exit 1
        fi
        
        print_success "Libraries built successfully!"
        echo ""
    fi
}

# Filter test output based on verbosity settings
filter_test_output() {
    local output="$1"
    
    if [ $VERBOSE -eq 0 ] && [ $SHOW_WARNINGS -eq 0 ]; then
        # Filter out compilation warnings and info messages
        echo "$output" | grep -v "warning:" | grep -v "note:" | grep -v "\[MERCURY INFO\]" | grep -v "Suppressing further"
    else
        echo "$output"
    fi
}

# Parse test results from output
parse_test_results() {
    local output="$1"
    local -n total_ref=$2
    local -n passed_ref=$3
    local -n failed_ref=$4
    
    total_ref=0
    passed_ref=0
    failed_ref=0
    
    # Decision: Use Total lines if present, otherwise count assertions
    local has_totals=0
    if echo "$output" | grep -q "Total:"; then
        has_totals=1
    fi
    
    # Parse the output
    while IFS= read -r line; do
        if [ $has_totals -eq 1 ]; then
            # We have Total lines, only count those
            # Strip ANSI color codes first
            local clean_line=$(echo "$line" | sed 's/\x1b\[[0-9;]*m//g')
            if [[ $clean_line =~ Total:[\ ]*([0-9]+),[\ ]*Passed:[\ ]*([0-9]+),[\ ]*Failed:[\ ]*([0-9]+) ]]; then
                local suite_total="${BASH_REMATCH[1]}"
                local suite_passed="${BASH_REMATCH[2]}"
                local suite_failed="${BASH_REMATCH[3]}"
                total_ref=$((total_ref + suite_total))
                passed_ref=$((passed_ref + suite_passed))
                failed_ref=$((failed_ref + suite_failed))
            fi
        else
            # No Total lines, count individual assertions
            if [[ $line =~ ([0-9]+)[\ ]+assertions?[\ ]+passed ]]; then
                local assertions="${BASH_REMATCH[1]}"
                passed_ref=$((passed_ref + assertions))
                total_ref=$((total_ref + assertions))
            fi
        fi
    done <<< "$output"
    
    # Sanity checks
    if [ $total_ref -eq 0 ] && [ $passed_ref -gt 0 ]; then
        total_ref=$passed_ref
    fi
    
    # If passed > total, use passed as total (handles incorrect test output)
    if [ $passed_ref -gt $total_ref ]; then
        total_ref=$passed_ref
    fi
}

# Run test executable with timeout
run_test_with_timeout() {
    local test_exe="$1"
    local timeout_sec="${2:-30}"
    
    if command -v timeout &> /dev/null; then
        timeout "$timeout_sec" "$test_exe"
    else
        "$test_exe"
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

# ============================================================================
# TEST EXECUTION FUNCTIONS
# ============================================================================

# Run simple tests
run_simple_tests() {
    print_info "Running simple C tests..."
    check_requirements || exit 1
    
    # Build if needed
    build_tests_if_needed
    
    cd "$C_CORE_DIR" || exit 1
    
    [ $QUIET -eq 0 ] && echo -e "${CYAN}🔧 Running all tests${NC}"
    [ $QUIET -eq 0 ] && print_separator
    
    # Run tests and capture output
    local TEST_OUTPUT
    TEST_OUTPUT=$(make test 2>&1)
    local TEST_EXIT_CODE=$?
    
    # Check if tests failed
    if [ $TEST_EXIT_CODE -ne 0 ]; then
        print_error "Tests failed with exit code $TEST_EXIT_CODE"
        echo ""
        echo "Test output:"
        echo "$TEST_OUTPUT"
        echo ""
        print_error "Test execution failed. Check the output above for details."
        return $TEST_EXIT_CODE
    fi
    
    # Filter and display output
    local FILTERED_OUTPUT
    FILTERED_OUTPUT=$(filter_test_output "$TEST_OUTPUT")
    [ $QUIET -eq 0 ] && echo "$FILTERED_OUTPUT"
    
    # Parse test results
    local TOTAL_COUNT TOTAL_PASSED TOTAL_FAILED
    parse_test_results "$TEST_OUTPUT" TOTAL_COUNT TOTAL_PASSED TOTAL_FAILED
    
    # Capture failures
    local FAILURES=""
    while IFS= read -r line; do
        if [[ $line =~ ✗\ FAIL:|Failed\ to\ run\ test|test\(s\)\ failed! ]]; then
            FAILURES="${FAILURES}\n${line}"
        fi
    done <<< "$TEST_OUTPUT"
    
    # Display summary
    if [ $QUIET -eq 0 ]; then
        echo ""
        print_separator
        echo -e "${BOLD}📊 Test Summary:${NC}"
        echo -e "   Total tests: ${BOLD}$TOTAL_COUNT${NC}"
        echo -e "   Passed: ${GREEN}${BOLD}$TOTAL_PASSED${NC}"
        echo -e "   Failed: ${RED}${BOLD}$TOTAL_FAILED${NC}"
    fi
    
    if [ $TOTAL_FAILED -gt 0 ]; then
        echo ""
        echo -e "${RED}${BOLD}❌ FAILURES:${NC}"
        echo -e "$FAILURES"
        return 1
    else
        print_success "All tests passed!"
        return 0
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

case "$COMMAND" in
    test|tests)
        run_simple_tests
        EXIT_CODE=$?
        cd "$ORIGINAL_DIR"
        exit $EXIT_CODE
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
        
    security|--security)
        print_info "Running security vulnerability tests..."
        check_requirements || exit 1
        
        if [ $QUIET -eq 0 ]; then
            echo -e "${YELLOW}"
            echo "╔════════════════════════════════════════════════════════════╗"
            echo "║           🔒 SECURITY VULNERABILITY TESTING 🔒            ║"
            echo "║                                                            ║"
            echo "║  Testing for:                                              ║"
            echo "║  • Command injection vulnerabilities                      ║"
            echo "║  • Buffer overflow protections                            ║"
            echo "║  • Input validation                                       ║"
            echo "║  • Memory safety                                          ║"
            echo "╚════════════════════════════════════════════════════════════╝"
            echo -e "${NC}"
        fi
        
        # Check if security test exists
        if [ ! -f "$SECURITY_DIR/security_test" ]; then
            print_warning "Security test not found, building..."
            cd "$C_CORE_DIR" || exit 1
            make sec_test > /dev/null 2>&1
        fi
        
        run_c_tests "sec_test" "Security tests"
        EXIT_CODE=$?
        
        # Check exit code
        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}"
            echo "✅ All security tests passed!"
            echo "No critical vulnerabilities detected."
            echo -e "${NC}"
        else
            echo -e "${RED}"
            echo "⚠️  SECURITY VULNERABILITIES DETECTED!"
            echo "Review the failed tests above and fix all issues before deployment."
            echo -e "${NC}"
            cd "$ORIGINAL_DIR"
            exit 1
        fi
        cd "$ORIGINAL_DIR"
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
        
        # Check if enhanced test exists
        ENHANCED_TEST="$COVERAGE_DIR/comprehensive_test_query_analyzer_enhanced"
        if [ ! -f "$ENHANCED_TEST" ] || [ $NO_BUILD -eq 0 ]; then
            # Compile with enhanced framework
            [ $QUIET -eq 0 ] && echo -e "${BLUE}🔨 Building enhanced tests...${NC}"
            
            mkdir -p "$COVERAGE_DIR"
            
            # Build the comprehensive test with fixes
            gcc -g -O0 -DUSE_ENHANCED_TESTS \
                -I./tests \
                -o "$ENHANCED_TEST" \
                tests/comprehensive_test_query_analyzer.c \
                query_analyzer.c common.c \
                -lm -pthread
            
            if [ $? -ne 0 ]; then
                print_error "Failed to build enhanced tests"
                cd "$ORIGINAL_DIR"
                exit 1
            fi
            
            [ $QUIET -eq 0 ] && echo -e "${GREEN}✓ Build successful${NC}\n"
        fi
        
        # Run the enhanced test
        if [ $QUIET -eq 0 ]; then
            echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
            echo -e "${BOLD}Running Enhanced Tests with Educational Features${NC}"
            echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}\n"
            
            if [ $DEBUG -eq 1 ]; then
                echo -e "${YELLOW}🔍 Debug mode enabled${NC}"
            fi
            
            if [ $EXPLAIN -eq 1 ]; then
                echo -e "${YELLOW}📚 Educational explanations enabled${NC}\n"
            fi
        fi
        
        # Run the test
        "$ENHANCED_TEST"
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -ne 0 ] && [ $EXPLAIN -eq 1 ] && [ $QUIET -eq 0 ]; then
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
        
        cd "$ORIGINAL_DIR"
        exit $EXIT_CODE
        ;;
        
    help|--help|-h)
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "${BOLD}Commands:${NC}"
        echo "  test       Run simple C tests (default)"
        echo "  coverage   Run tests with coverage analysis"
        echo "  enhanced   Run tests with enhanced debugging features"
        echo "  security   Run security vulnerability tests 🔒"
        echo "  all        Run all tests and coverage"
        echo "  clean      Clean test artifacts"
        echo "  build      Build C libraries only"
        echo "  benchmark  Run performance benchmarks"
        echo "  memcheck   Run memory safety checks (Linux only)"
        echo "  help       Show this help message"
        echo ""
        echo "${BOLD}Options:${NC}"
        echo "  --debug       Enable debug mode with verbose output"
        echo "  --verbose     Show all test assertions (default: only failures)"
        echo "  --warnings    Show compilation warnings and info messages"
        echo "  --explain     Enable educational mode with explanations"
        echo "  --single TEST Run a specific test file"
        echo "  --fix-only    Only compile with fixes, don't run"
        echo "  --parallel    Run tests in parallel (experimental)"
        echo "  --no-build    Skip building if binaries exist"
        echo "  --quiet, -q   Minimal output (errors only)"
        echo ""
        echo "${BOLD}Environment Variables:${NC}"
        echo "  TEST_DEBUG=1   Enable debug output in tests"
        echo "  TEST_TRACE=1   Enable function tracing"
        echo "  FORCE_COLOR=1  Force colored output (CI environments)"
        echo ""
        echo "${BOLD}Examples:${NC}"
        echo "  $0                      # Run simple tests"
        echo "  $0 --verbose            # Run tests with all assertions shown"
        echo "  $0 --quiet              # Minimal output"
        echo "  $0 coverage             # Run with coverage"
        echo "  $0 enhanced --debug     # Enhanced tests with debug"
        echo "  $0 enhanced --explain   # Enhanced tests with explanations"
        echo "  $0 security             # Run security tests"
        echo "  $0 all                  # Run everything"
        echo "  $0 --no-build --quiet   # Quick test run"
        echo ""
        echo "${BOLD}Educational Features (enhanced mode):${NC}"
        echo "  • Detailed failure messages with expected vs actual values"
        echo "  • Hex dumps for buffer comparisons"
        echo "  • Query analyzer state inspection"
        echo "  • Memory leak detection"
        echo "  • Performance timing information"
        echo ""
        echo "${BOLD}Performance Tips:${NC}"
        echo "  • Use --no-build to skip rebuilding if binaries exist"
        echo "  • Use --quiet for CI/automation"
        echo "  • Use --parallel for faster execution (experimental)"
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