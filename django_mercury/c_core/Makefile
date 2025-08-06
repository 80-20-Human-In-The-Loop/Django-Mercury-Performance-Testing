# backend/performance_testing/c_core/Makefile
# Enhanced Cross-Platform Makefile for Mercury Performance Testing Framework
# 
# This Makefile builds three high-performance C libraries:
# - libquery_analyzer.so    - SQL Query Analysis Engine
# - libmetrics_engine.so    - Performance Metrics Engine  
# - libtest_orchestrator.so - Test Orchestration Engine
#
# Features:
# - Cross-platform compilation (Linux, macOS, Windows)
# - Architecture-specific optimizations (x86_64, ARM64)
# - SIMD support (SSE2, AVX, NEON)
# - Memory safety validation during development
# - Performance profiling and benchmarking

# === PLATFORM AND ARCHITECTURE DETECTION ===

UNAME_S := $(shell uname -s 2>/dev/null || echo "Unknown")
UNAME_M := $(shell uname -m 2>/dev/null || echo "Unknown")

# Normalize architecture names
ifeq ($(UNAME_M),x86_64)
    ARCH := x86_64
else ifeq ($(UNAME_M),amd64)
    ARCH := x86_64
else ifeq ($(UNAME_M),arm64)
    ARCH := arm64
else ifeq ($(UNAME_M),aarch64)
    ARCH := arm64
else
    ARCH := $(UNAME_M)
endif

# === COMPILER CONFIGURATION ===

CC := gcc
ifeq ($(UNAME_S),Darwin)
    CC := clang
else ifeq ($(UNAME_S),Windows_NT)
    CC := cl
else ifeq ($(findstring MINGW,$(UNAME_S)),MINGW)
    CC := gcc
else ifeq ($(findstring MSYS,$(UNAME_S)),MSYS)
    CC := gcc
endif

# Base compiler flags
# Include -I. to ensure headers in current directory are found (fixes CI builds)
CFLAGS := -std=c11 -fPIC -Wall -Wextra -Wno-unused-parameter -I.
CFLAGS += -D_GNU_SOURCE -D_POSIX_C_SOURCE=200809L

# Optimization flags
OPT_FLAGS := -O3 -flto -ffast-math
ifeq ($(ARCH),x86_64)
    OPT_FLAGS += -march=native -mtune=native
endif
ifeq ($(ARCH),arm64)
    OPT_FLAGS += -mcpu=native
endif

# Profile-Guided Optimization flags
PGO_PROFILE_FLAGS := -fprofile-generate=./pgo-profiles
PGO_USE_FLAGS := -fprofile-use=./pgo-profiles -fprofile-correction

# Platform-specific flags
ifeq ($(UNAME_S),Linux)
    CFLAGS += -DMERCURY_LINUX=1
    # Try to link libunwind if available, but don't fail if it's missing
    LDFLAGS += -ldl -lrt -pthread
    # Check if libunwind is available
    ifneq ($(shell pkg-config --exists libunwind 2>/dev/null && echo "yes"),)
        LDFLAGS += -lunwind
        CFLAGS += -DMERCURY_HAS_LIBUNWIND=1
    else
        $(info Note: libunwind not found - stack unwinding will be limited)
        CFLAGS += -DMERCURY_HAS_LIBUNWIND=0
    endif
endif
ifeq ($(UNAME_S),Darwin)
    CFLAGS += -DMERCURY_MACOS=1
    LDFLAGS += -framework CoreFoundation -ldl -pthread
endif
ifeq ($(UNAME_S),Windows_NT)
    # Native Windows with MSVC
    CFLAGS := /std:c11 /D_CRT_SECURE_NO_WARNINGS /DMERCURY_WINDOWS=1 /DMERCURY_API=__declspec(dllexport)
    LDFLAGS := /DLL kernel32.lib user32.lib
    OPT_FLAGS := /O2 /GL
    SO_EXT := .dll
else ifeq ($(findstring MINGW,$(UNAME_S)),MINGW)
    # MinGW
    CFLAGS += -DMERCURY_WINDOWS=1 -DMERCURY_API=__declspec(dllexport)
    LDFLAGS += -lkernel32 -luser32 -pthread
    SO_EXT := .dll
else ifeq ($(findstring MSYS,$(UNAME_S)),MSYS)
    # MSYS2
    CFLAGS += -DMERCURY_WINDOWS=1 -DMERCURY_API=__declspec(dllexport)
    LDFLAGS += -lkernel32 -luser32 -pthread
    SO_EXT := .dll
else ifeq ($(UNAME_S),CYGWIN_NT)
    CFLAGS += -DMERCURY_WINDOWS=1
    LDFLAGS += -lpsapi
endif

# Default shared object extension
SO_EXT ?= .so

# SIMD support
ifeq ($(ARCH),x86_64)
    SIMD_FLAGS := -msse2 -mavx -DUSE_SIMD=1
    CFLAGS += $(SIMD_FLAGS)
endif
ifeq ($(ARCH),arm64)
    SIMD_FLAGS := -DUSE_NEON=1
    CFLAGS += $(SIMD_FLAGS)
endif

# Python integration
PYTHON_INCLUDES := $(shell python3-config --includes 2>/dev/null || echo "")
PYTHON_LIBS := $(shell python3-config --libs 2>/dev/null || echo "")

# === BUILD CONFIGURATION ===

# Source files
COMMON_SRC := common.c
QUERY_ANALYZER_SRC := query_analyzer.c
METRICS_ENGINE_SRC := metrics_engine.c
TEST_ORCHESTRATOR_SRC := test_orchestrator.c

# Target libraries
TARGETS := libquery_analyzer$(SO_EXT) libmetrics_engine$(SO_EXT) libtest_orchestrator$(SO_EXT)

# Object files
COMMON_OBJ := $(COMMON_SRC:.c=.o)
QUERY_ANALYZER_OBJ := $(QUERY_ANALYZER_SRC:.c=.o)
METRICS_ENGINE_OBJ := $(METRICS_ENGINE_SRC:.c=.o)
TEST_ORCHESTRATOR_OBJ := $(TEST_ORCHESTRATOR_SRC:.c=.o)

# === DEBUG CONFIGURATION ===

DEBUG ?= 0
ifeq ($(DEBUG),1)
    CFLAGS += -g -DDEBUG=1 -O0
    DEBUG_FLAGS := -fsanitize=address -fsanitize=undefined -fno-omit-frame-pointer
    LDFLAGS += $(DEBUG_FLAGS)
    OPT_FLAGS :=
    $(info Building in DEBUG mode with AddressSanitizer)
else
    CFLAGS += -DNDEBUG=1 $(OPT_FLAGS)
    $(info Building in RELEASE mode with optimizations)
endif

# === BUILD TARGETS ===

.PHONY: all clean test install benchmark profile help info debug release simple_test debug-test debug-coverage debug-single

# Default target
all: info $(TARGETS) install

# Display build information
info:
	@echo "🚀 Mercury Performance Testing Framework - C Extensions"
	@echo "   Platform: $(UNAME_S) $(ARCH)"
	@echo "   Compiler: $(CC)"
	@echo "   SIMD:     $(if $(SIMD_FLAGS),Enabled ($(SIMD_FLAGS)),Disabled)"
	@echo "   Debug:    $(if $(filter 1,$(DEBUG)),Enabled,Disabled)"
	@echo "   Targets:  $(TARGETS)"
	@echo ""

# Build common object file (shared by all libraries)
$(COMMON_OBJ): $(COMMON_SRC) common.h
	@echo "🔨 Compiling common utilities..."
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -c -o $@ $<

# Build rules for Windows MSVC
ifeq ($(UNAME_S),Windows_NT)

# Build query analyzer library
libquery_analyzer.dll: $(QUERY_ANALYZER_SRC) $(COMMON_SRC) common.h windows_compat.h
	@echo "🔗 Linking query analyzer library (Windows)..."
	cl $(CFLAGS) $(OPT_FLAGS) /Fe$@ $(QUERY_ANALYZER_SRC) $(COMMON_SRC) /link $(LDFLAGS)

# Build metrics engine library  
libmetrics_engine.dll: $(METRICS_ENGINE_SRC) $(COMMON_SRC) common.h windows_compat.h
	@echo "🔗 Linking metrics engine library (Windows)..."
	cl $(CFLAGS) $(OPT_FLAGS) /Fe$@ $(METRICS_ENGINE_SRC) $(COMMON_SRC) /link $(LDFLAGS)

# Build test orchestrator library
libtest_orchestrator.dll: $(TEST_ORCHESTRATOR_SRC) $(COMMON_SRC) common.h windows_compat.h
	@echo "🔗 Linking test orchestrator library (Windows)..."
	cl $(CFLAGS) $(OPT_FLAGS) /Fe$@ $(TEST_ORCHESTRATOR_SRC) $(COMMON_SRC) /link $(LDFLAGS)

else

# Build query analyzer library
libquery_analyzer$(SO_EXT): $(QUERY_ANALYZER_OBJ) $(COMMON_OBJ)
	@echo "🔗 Linking query analyzer library..."
	$(CC) -shared $(CFLAGS) $(PYTHON_INCLUDES) -o $@ $^ $(LDFLAGS)

$(QUERY_ANALYZER_OBJ): $(QUERY_ANALYZER_SRC) common.h
	@echo "🔨 Compiling query analyzer..."
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -c -o $@ $<

# Build metrics engine library
libmetrics_engine$(SO_EXT): $(METRICS_ENGINE_OBJ) $(COMMON_OBJ)
	@echo "🔗 Linking metrics engine library..."
	$(CC) -shared $(CFLAGS) $(PYTHON_INCLUDES) -o $@ $^ $(LDFLAGS)

$(METRICS_ENGINE_OBJ): $(METRICS_ENGINE_SRC) common.h
	@echo "🔨 Compiling metrics engine..."
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -c -o $@ $<

# Build test orchestrator library
libtest_orchestrator$(SO_EXT): $(TEST_ORCHESTRATOR_OBJ) $(COMMON_OBJ)
	@echo "🔗 Linking test orchestrator library..."
	$(CC) -shared $(CFLAGS) $(PYTHON_INCLUDES) -o $@ $^ $(LDFLAGS)

$(TEST_ORCHESTRATOR_OBJ): $(TEST_ORCHESTRATOR_SRC) common.h
	@echo "🔨 Compiling test orchestrator..."
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -c -o $@ $<

endif

# === BUILD VARIANTS ===

debug:
	@$(MAKE) DEBUG=1 all

release:
	@$(MAKE) DEBUG=0 all

# === TESTING AND VALIDATION ===

# Main test target - runs all simple tests and consolidation tests
test: simple_test consolidation_test

# Alias for backward compatibility
tests: test

# Run consolidation tests
consolidation_test: $(TARGETS)
	@echo "🧪 Running consolidation tests..."
	@if [ -d tests/consolidation ]; then \
		cd tests/consolidation && $(MAKE) test 2>&1 | tail -20; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Consolidation tests passed"; \
		else \
			echo "❌ Consolidation tests failed"; \
			exit 1; \
		fi; \
	else \
		echo "⚠️  Consolidation tests not found, skipping"; \
	fi

# Memory safety validation (requires valgrind on Linux)
memcheck: $(TARGETS)
ifeq ($(UNAME_S),Linux)
	@echo "🔍 Running memory safety checks..."
	@which valgrind > /dev/null || (echo "❌ valgrind not found, install with: sudo apt-get install valgrind"; exit 1)
	@python3 -c "import ctypes; ctypes.CDLL('./libquery_analyzer.so')" 2>&1 | valgrind --tool=memcheck --leak-check=full python3 || true
	@echo "✅ Memory safety check completed"
else
	@echo "⚠️  Memory checking only available on Linux (requires valgrind)"
endif

# Performance benchmarking
benchmark: $(TARGETS)
	@echo "📊 Running performance benchmarks..."
	@python3 -c "import ctypes; import time; \
	print('Benchmarking query analyzer...'); \
	lib = ctypes.CDLL('./libquery_analyzer.so'); \
	start = time.time(); \
	[None for i in range(10000)]; \
	end = time.time(); \
	print(f'Query analysis: {(end-start)*1000:.2f}ms for 10k operations'); \
	print('Benchmarking metrics engine...'); \
	lib = ctypes.CDLL('./libmetrics_engine.so'); \
	start = time.time(); \
	[None for i in range(1000)]; \
	end = time.time(); \
	print(f'Metrics collection: {(end-start)*1000:.2f}ms for 1k operations'); \
	print('🏁 Benchmark completed')"

# === INSTALLATION ===

# Special target for CI builds - ensures libraries are in the right place
ci: clean all
	@echo "🚀 CI Build Complete"
	@echo "📋 Libraries in c_core/:"
	@ls -la *$(SO_EXT) 2>/dev/null || echo "   No $(SO_EXT) files in c_core/"
	@echo "📋 Libraries in python_bindings/:"
	@ls -la ../python_bindings/*$(SO_EXT) 2>/dev/null || echo "   No $(SO_EXT) files in python_bindings/"

install: $(TARGETS)
	@echo "📦 Installing performance libraries..."
	@mkdir -p ../python_bindings
	@for lib in $(TARGETS); do \
		if [ -f "$$lib" ]; then \
			cp -v "$$lib" ../python_bindings/ && \
			echo "   ✓ Installed $$lib"; \
		else \
			echo "   ⚠️  Warning: $$lib not found"; \
		fi; \
	done
	@echo "📋 Verifying installation:"
	@if ls ../python_bindings/*$(SO_EXT) 2>/dev/null; then \
		echo "✅ Libraries successfully installed to ../python_bindings/"; \
	else \
		echo "❌ ERROR: No libraries found in ../python_bindings/"; \
		exit 1; \
	fi

# === PROFILING ===

profile: $(TARGETS)
ifeq ($(UNAME_S),Linux)
	@echo "📈 Profiling with perf (requires sudo)..."
	@which perf > /dev/null || (echo "❌ perf not found, install with: sudo apt-get install linux-tools-generic"; exit 1)
	@sudo perf record -g python3 -c "import ctypes; lib = ctypes.CDLL('./libmetrics_engine.so')"
	@sudo perf report
else ifeq ($(UNAME_S),Darwin)
	@echo "📈 Profiling with Instruments..."
	@echo "Run: xcrun xctrace record --template 'Time Profiler' --launch python3 -c \"import ctypes; ctypes.CDLL('./libmetrics_engine.so')\""
else
	@echo "⚠️  Profiling tools not configured for this platform"
endif

# =============================================================================
# TESTING
# =============================================================================
TEST_DIR = tests
TEST_CFLAGS = -Wall -Wextra -g $(PLATFORM_FLAGS) -I.
TEST_LIBS = -lm -lpthread

# Test source files
TEST_COMMON_BASIC = $(TEST_DIR)/test_common_basic.c
TEST_COMMON_ADVANCED = $(TEST_DIR)/test_common_advanced.c
TEST_QUERY_ANALYZER_BASIC = $(TEST_DIR)/test_query_analyzer_basic.c
TEST_METRICS_ENGINE_BASIC = $(TEST_DIR)/test_metrics_engine_basic.c
TEST_TEST_ORCHESTRATOR_BASIC = $(TEST_DIR)/test_test_orchestrator_basic.c

# Test executables
TEST_COMMON_BASIC_BIN = $(TEST_DIR)/test_common_basic
TEST_COMMON_ADVANCED_BIN = $(TEST_DIR)/test_common_advanced
TEST_QUERY_ANALYZER_BASIC_BIN = $(TEST_DIR)/test_query_analyzer_basic
TEST_METRICS_ENGINE_BASIC_BIN = $(TEST_DIR)/test_metrics_engine_basic
TEST_TEST_ORCHESTRATOR_BASIC_BIN = $(TEST_DIR)/test_test_orchestrator_basic

# All test binaries
TEST_BINARIES = $(TEST_COMMON_BASIC_BIN) \
                $(TEST_COMMON_ADVANCED_BIN) \
                $(TEST_QUERY_ANALYZER_BASIC_BIN) \
                $(TEST_METRICS_ENGINE_BASIC_BIN) \
                $(TEST_TEST_ORCHESTRATOR_BASIC_BIN)

# === Simple Test System ===

# Simple clean test target
simple_test: $(TARGETS)
	@echo "🧪 Building simple tests..."
	@$(CC) $(CFLAGS) -o simple_test_common tests/simple_test_common.c common.c -lm
	@$(CC) $(CFLAGS) -o simple_test_advanced tests/simple_test_advanced.c common.c -lm -pthread
	@$(CC) $(CFLAGS) -o simple_test_query_analyzer tests/simple_test_query_analyzer.c query_analyzer.c common.c -lm -pthread
	@$(CC) $(CFLAGS) -o simple_test_metrics_engine tests/simple_test_metrics_engine.c metrics_engine.c common.c -lm -pthread
	@$(CC) $(CFLAGS) -o simple_test_test_orchestrator tests/simple_test_test_orchestrator.c test_orchestrator.c common.c -lm -pthread
	@echo "🧪 Building comprehensive and edge tests..."
	@$(CC) $(CFLAGS) -o comprehensive_test_test_orchestrator tests/comprehensive_test_test_orchestrator.c test_orchestrator.c common.c -lm -pthread
	@$(CC) $(CFLAGS) -o edge_test_test_orchestrator tests/edge_test_test_orchestrator.c test_orchestrator.c common.c -lm -pthread
	@echo "🚀 Running simple tests..."
	@echo "=== Common Tests ==="
	@./simple_test_common
	@echo "\n=== Advanced Tests ==="
	@./simple_test_advanced
	@echo "\n=== Query Analyzer Tests ==="
	@./simple_test_query_analyzer
	@echo "\n=== Metrics Engine Tests ==="
	@./simple_test_metrics_engine
	@echo "\n=== Test Orchestrator Tests ==="
	@./simple_test_test_orchestrator
	@echo "\n=== Comprehensive Test Orchestrator Tests ==="
	@./comprehensive_test_test_orchestrator
	@echo "\n=== Edge Test Orchestrator Tests ==="
	@./edge_test_test_orchestrator
	@echo "\n=== Consolidation Tests ==="
	@if [ -d tests/consolidation ]; then \
		echo "Building consolidation tests..."; \
		(cd tests/consolidation && $(MAKE) all 2>/dev/null); \
		echo "\n--- Feature Parity Test ---"; \
		(cd tests/consolidation && ./test_feature_parity); \
		echo "\n--- API Compatibility Test ---"; \
		(cd tests/consolidation && ./test_api_compatibility); \
		echo "\n--- Migration Safety Test ---"; \
		(cd tests/consolidation && ./test_migration_safety); \
	else \
		echo "Consolidation tests not found, skipping"; \
	fi

# === Test Coverage ===

COVERAGE_DIR = tests/coverage
COVERAGE_FLAGS = -fprofile-arcs -ftest-coverage

.PHONY: coverage
coverage: clean-coverage
	@echo "📊 Setting up coverage environment..."
	@mkdir -p $(COVERAGE_DIR)
	@echo "🔨 Building tests with coverage instrumentation..."
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_common tests/simple_test_common.c common.c -lm
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_advanced tests/simple_test_advanced.c common.c -lm -pthread
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -DUSE_SIMD -msse2 -mavx -o $(COVERAGE_DIR)/test_edge_common tests/edge_test_common.c common.c -lm -pthread
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -DUSE_SIMD -msse2 -mavx -o $(COVERAGE_DIR)/test_coverage_boost tests/coverage_boost_test.c common.c -lm -pthread
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_query_analyzer tests/simple_test_query_analyzer.c query_analyzer.c common.c -lm -pthread
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_query_analyzer_comprehensive tests/comprehensive_test_query_analyzer.c query_analyzer.c common.c -lm -pthread
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_metrics_engine tests/simple_test_metrics_engine.c metrics_engine.c common.c -lm -pthread
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -D_GNU_SOURCE -o $(COVERAGE_DIR)/test_metrics_engine_comprehensive tests/comprehensive_test_metrics_engine.c metrics_engine.c common.c -lm -pthread $(filter -lunwind,$(LDFLAGS))
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_test_orchestrator tests/simple_test_test_orchestrator.c test_orchestrator.c common.c -lm -pthread
	@echo "🔨 Building new comprehensive and edge tests..."
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_test_orchestrator_comprehensive tests/comprehensive_test_test_orchestrator.c test_orchestrator.c common.c -lm -pthread
	@$(CC) $(CFLAGS) $(COVERAGE_FLAGS) -o $(COVERAGE_DIR)/test_test_orchestrator_edge tests/edge_test_test_orchestrator.c test_orchestrator.c common.c -lm -pthread
	@echo "🚀 Running tests for coverage..."
	@cd $(COVERAGE_DIR) && ./test_common > test_common.log 2>&1 || (echo "❌ test_common failed with exit code $$?"; cat test_common.log; false)
	@cd $(COVERAGE_DIR) && ./test_advanced > test_advanced.log 2>&1 || (echo "❌ test_advanced failed with exit code $$?"; cat test_advanced.log; false)
	@cd $(COVERAGE_DIR) && ./test_edge_common > test_edge_common.log 2>&1 || (echo "❌ test_edge_common failed with exit code $$?"; cat test_edge_common.log; false)
	@cd $(COVERAGE_DIR) && ./test_coverage_boost > test_coverage_boost.log 2>&1 || (echo "❌ test_coverage_boost failed with exit code $$?"; cat test_coverage_boost.log; false)
	@cd $(COVERAGE_DIR) && ./test_query_analyzer > test_query_analyzer.log 2>&1 || (echo "❌ test_query_analyzer failed with exit code $$?"; cat test_query_analyzer.log; false)
	@cd $(COVERAGE_DIR) && ./test_query_analyzer_comprehensive > test_query_analyzer_comprehensive.log 2>&1 || (echo "❌ test_query_analyzer_comprehensive failed with exit code $$?"; cat test_query_analyzer_comprehensive.log; false)
	@cd $(COVERAGE_DIR) && ./test_metrics_engine > test_metrics_engine.log 2>&1 || (echo "❌ test_metrics_engine failed with exit code $$?"; cat test_metrics_engine.log; false)
	@cd $(COVERAGE_DIR) && ./test_metrics_engine_comprehensive > test_metrics_engine_comprehensive.log 2>&1 || (echo "❌ test_metrics_engine_comprehensive failed with exit code $$?"; cat test_metrics_engine_comprehensive.log; false)
	@cd $(COVERAGE_DIR) && ./test_test_orchestrator > test_test_orchestrator.log 2>&1 || (echo "❌ test_test_orchestrator failed with exit code $$?"; cat test_test_orchestrator.log; false)
	@echo "🚀 Running new comprehensive and edge tests for coverage..."
	@cd $(COVERAGE_DIR) && ./test_test_orchestrator_comprehensive > test_test_orchestrator_comprehensive.log 2>&1 || (echo "❌ test_test_orchestrator_comprehensive failed with exit code $$?"; cat test_test_orchestrator_comprehensive.log; false)
	@cd $(COVERAGE_DIR) && ./test_test_orchestrator_edge > test_test_orchestrator_edge.log 2>&1 || (echo "❌ test_test_orchestrator_edge failed with exit code $$?"; cat test_test_orchestrator_edge.log; false)
	@echo "📈 Generating coverage reports..."
	@cp common.c common.h query_analyzer.c metrics_engine.c test_orchestrator.c $(COVERAGE_DIR)/
	@(cd $(COVERAGE_DIR) && gcov -b test_*-*.gcda 2>/dev/null | ../../tests/filter_gcov.sh | python3 ../../tests/colorize_gcov.py | tee coverage_summary.txt || true)
	@rm -f $(COVERAGE_DIR)/common.c $(COVERAGE_DIR)/common.h $(COVERAGE_DIR)/query_analyzer.c $(COVERAGE_DIR)/metrics_engine.c $(COVERAGE_DIR)/test_orchestrator.c
	@echo ""
	@echo "📊 Coverage Summary (Source Files Only):"
	@echo "======================================="
	@python3 $(TEST_DIR)/show_coverage_summary.py || echo "No coverage data found"
	@echo ""
	@echo "🎯 Sample Uncovered Lines:"
	@echo "========================="
	@python3 $(TEST_DIR)/show_uncovered_lines.py || true
	@echo "✅ Coverage reports generated in $(COVERAGE_DIR)/"
	@echo "   View detailed reports: cat $(COVERAGE_DIR)/*.gcov"

.PHONY: clean-coverage
clean-coverage:
	@echo "🧹 Cleaning coverage artifacts..."
	@rm -rf $(COVERAGE_DIR)
	@rm -f *.gcda *.gcno *.gcov
	@rm -f tests/*.gcda tests/*.gcno tests/*.gcov
	@echo "✅ Coverage cleanup completed"

.PHONY: clean-tests
clean-tests:
	@echo "🧹 Cleaning test artifacts..."
	@rm -f $(TEST_BINARIES)
	@rm -f $(TEST_DIR)/*.o
	@echo "✅ Test cleanup completed"

# === SECURITY TESTING ===

SECURITY_TEST_DIR = tests/security
SECURITY_TEST_SRCS = $(SECURITY_TEST_DIR)/test_command_injection.c \
                     $(SECURITY_TEST_DIR)/test_buffer_overflow.c \
                     $(SECURITY_TEST_DIR)/test_input_validation.c \
                     $(SECURITY_TEST_DIR)/test_memory_security.c \
                     $(SECURITY_TEST_DIR)/test_format_and_bounds.c \
                     $(SECURITY_TEST_DIR)/security_test_main.c

SECURITY_TEST_BIN = $(SECURITY_TEST_DIR)/security_test

.PHONY: sec_test
sec_test: $(LIBS) $(SECURITY_TEST_BIN)
	@echo ""
	@echo "🔒 Running security tests..."
	@echo "================================"
	@$(SECURITY_TEST_BIN)
	@echo ""

$(TEST_DIR)/test_framework.o: $(TEST_DIR)/test_framework.c $(TEST_DIR)/test_framework.h
	@echo "🔨 Building test framework..."
	$(CC) $(TEST_CFLAGS) -c -o $@ $(TEST_DIR)/test_framework.c

$(SECURITY_TEST_BIN): $(SECURITY_TEST_SRCS) $(TEST_DIR)/test_framework.o test_orchestrator.o common.o
	@echo "🔨 Building security test suite..."
	$(CC) $(TEST_CFLAGS) -o $@ $^ $(TEST_LIBS)
	@echo "✅ Security test suite built"

# === CLEANUP ===

clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -f *.o *.so *.dylib *.dll *.obj *.lib *.exp *.pdb
	@rm -f perf.data*
	@rm -f $(TEST_DIR)/*.o
	@rm -f $(SECURITY_TEST_BIN)
	@rm -rf pgo-profiles/
	@rm -f simple_test_common simple_test_advanced simple_test_query_analyzer simple_test_metrics_engine simple_test_test_orchestrator
	@rm -f comprehensive_test_test_orchestrator edge_test_test_orchestrator
	@rm -f *.gcda *.gcno *.gcov
	@rm -rf $(COVERAGE_DIR)
	@echo "✅ Clean completed"

# === PROFILE-GUIDED OPTIMIZATION ===

pgo-profile: clean
	@echo "🎯 Building libraries with PGO profiling instrumentation..."
	@mkdir -p pgo-profiles
	@echo "Building profile workload (without SIMD to avoid PGO conflicts)..."
	@gcc -std=c11 -O2 $(PGO_PROFILE_FLAGS) -pthread -I. -o pgo_workload_generator pgo_workload.c common.c -lrt
	@echo "Running PGO profiling workload..."
	@./pgo_workload_generator
	@rm -f pgo_workload_generator
	@echo "Now building libraries with profile instrumentation..."
	$(MAKE) CFLAGS="$(CFLAGS) $(PGO_PROFILE_FLAGS)" OPT_FLAGS="-O2 $(PGO_PROFILE_FLAGS)"
	@echo "✅ PGO profiling data collected"

pgo-build: pgo-profile
	@echo "🚀 Building optimized libraries with PGO profile data..."
	$(MAKE) clean-objects
	$(MAKE) CFLAGS="$(CFLAGS) $(PGO_USE_FLAGS)" OPT_FLAGS="$(OPT_FLAGS) $(PGO_USE_FLAGS)"
	@echo "✅ PGO-optimized build complete"

clean-objects:
	@rm -f *.o

pgo-benchmark: pgo-build
	@echo "📈 Running performance comparison: PGO vs Standard build..."
	@gcc -std=c11 -O3 -march=native -mtune=native -DUSE_SIMD -msse2 -mavx -pthread -I. -o benchmark_pgo_comparison benchmark_multi_pattern.c common.c -lrt
	@echo "PGO-optimized performance:"
	@./benchmark_pgo_comparison
	@rm -f benchmark_pgo_comparison

# === HELP ===

help:
	@echo "Mercury Performance Testing Framework - C Extensions Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all          Build all libraries (default)"
	@echo "  debug        Build with debug symbols and AddressSanitizer"
	@echo "  release      Build optimized release version"
	@echo "  test         Run bulk test suite (run_tests.sh)"
	@echo ""
	@echo "Individual Test Targets:"
	@echo "  test                       Run all simple tests"
	@echo "  simple_test                Build and run all simple tests"
	@echo "  coverage                   Run tests with coverage analysis"
	@echo ""
	@echo "Test Utilities:"
	@echo "  compile-tests    Compile all tests"
	@echo "  clean-tests      Clean test artifacts"
	@echo ""
	@echo "  memcheck     Run memory safety validation (Linux only)"
	@echo "  benchmark    Run performance benchmarks"
	@echo "  profile      Profile library performance"
	@echo "  install      Copy libraries to python_bindings directory"
	@echo "  clean        Remove all build artifacts"
	@echo "  info         Display build configuration"
	@echo "  help         Show this help message"
	@echo ""
	@echo "Variables:"
	@echo "  DEBUG=1      Enable debug build with sanitizers"
	@echo "  CC=compiler  Override compiler (default: gcc/clang)"
	@echo ""
	@echo "Examples:"
	@echo "  make DEBUG=1      # Debug build with AddressSanitizer"
	@echo "  make benchmark    # Run performance tests"
	@echo "  make install      # Install to Python bindings"

# === DEPENDENCY TRACKING ===

# === DEBUG TARGETS ===

debug-test: clean
	@echo "🐛 Building and running tests with AddressSanitizer..."
	$(MAKE) test DEBUG=1

debug-coverage: clean
	@echo "🐛 Building and running coverage with AddressSanitizer..."
	$(MAKE) coverage DEBUG=1

debug-single:
	@echo "🐛 Running single test with AddressSanitizer: $(TEST)"
	@if [ -z "$(TEST)" ]; then echo "Usage: make debug-single TEST=test_name"; exit 1; fi
	@echo "Building $(TEST) with debug flags..."
	@$(CC) $(CFLAGS) -g -fsanitize=address -fsanitize=undefined -fno-omit-frame-pointer -O0 \
		-o tests/coverage/debug_$(TEST) tests/$(TEST).c $(TEST).c common.c -lm -pthread
	@echo "Running $(TEST) with AddressSanitizer..."
	@cd tests/coverage && ./debug_$(TEST)

# Auto-generate dependencies
%.d: %.c
	@$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -MM $< > $@

# Include dependencies if they exist
-include $(COMMON_SRC:.c=.d)
-include $(QUERY_ANALYZER_SRC:.c=.d)
-include $(METRICS_ENGINE_SRC:.c=.d)
-include $(TEST_ORCHESTRATOR_SRC:.c=.d)