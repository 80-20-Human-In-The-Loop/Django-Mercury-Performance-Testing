#!/usr/bin/env python3
"""
Performance Testing Framework Test Runner

A comprehensive test runner for the performance testing framework
that runs all unit tests and provides coverage reporting.

Usage:
    python test_runner.py [--coverage] [--verbose] [--module MODULE_NAME]
"""

import sys
import os
import unittest
import argparse
import faulthandler
import time
import signal
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
from contextlib import contextmanager

# Enable faulthandler to get better segfault diagnostics
faulthandler.enable()


# --- Timed Test Runner Classes ---

class TestTimeout(Exception):
    """Raised when a test exceeds the timeout limit."""
    pass


class TimedTextTestResult(unittest.TextTestResult):
    """Custom test result that tracks timing for each test."""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.verbosity = verbosity  # Store verbosity for later use
        self.test_times: Dict[str, float] = {}
        self.current_test_start: Optional[float] = None
        self.current_test_name: Optional[str] = None
        self.slow_tests: List[Tuple[str, float]] = []
        self.module_times: Dict[str, float] = defaultdict(float)
        
        # Enhanced performance tracking
        self.color_counts = {'🟢': 0, '🟡': 0, '🔴': 0, '💀': 0}
        self.color_tests = {'🟢': [], '🟡': [], '🔴': [], '💀': []}
        self.module_color_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'🟢': 0, '🟡': 0, '🔴': 0, '💀': 0})
        self.all_tests_with_times: List[Tuple[str, float, str]] = []  # (test_name, time, color)
        
    def startTest(self, test):
        """Called when a test starts."""
        super().startTest(test)
        self.current_test_start = time.time()
        self.current_test_name = test.id()
        
        # Show test name in real-time
        if self.verbosity >= 2:
            self.stream.write(f"\n🏃 Running: {test.id()} ... ")
            self.stream.flush()
    
    def stopTest(self, test):
        """Called when a test completes."""
        if self.current_test_start:
            elapsed = time.time() - self.current_test_start
            test_id = test.id()
            self.test_times[test_id] = elapsed
            
            # Track module time
            module_name = test_id.split('.')[0]
            self.module_times[module_name] += elapsed
            
            # Determine color category and track statistics
            color_emoji = ''
            if elapsed > 2.0:
                # Critical - purple/black for tests over 2 seconds
                indicator = f"\033[35m💀 {elapsed:.3f}s - CRITICAL SLOWNESS!\033[0m"
                color_emoji = '💀'
                self.slow_tests.append((test_id, elapsed))
            elif elapsed > 0.5:
                # Big red warning for tests over 0.5 seconds
                indicator = f"\033[1;31m🔴 {elapsed:.3f}s - TOO SLOW!\033[0m"
                color_emoji = '🔴'
                self.slow_tests.append((test_id, elapsed))
            elif elapsed > 0.1:
                # Yellow warning for tests 0.1-0.5 seconds
                indicator = f"\033[33m🟡 {elapsed:.3f}s\033[0m"
                color_emoji = '🟡'
            else:
                # Green for fast tests
                indicator = f"\033[32m🟢 {elapsed:.3f}s\033[0m"
                color_emoji = '🟢'
            
            # Track color statistics
            self.color_counts[color_emoji] += 1
            self.color_tests[color_emoji].append((test_id, elapsed))
            self.module_color_stats[module_name][color_emoji] += 1
            self.all_tests_with_times.append((test_id, elapsed, color_emoji))
            
            if self.verbosity >= 2:
                self.stream.write(indicator)
                self.stream.flush()
            elif self.verbosity == 1 and elapsed > 0.5:
                # Even in normal verbosity, show slow tests
                self.stream.write(f"\n⚠️  SLOW TEST: {test_id} took {indicator}")
                self.stream.flush()
                
        super().stopTest(test)
        
    def addSuccess(self, test):
        """Called when a test passes."""
        super().addSuccess(test)
        if self.verbosity >= 2:
            self.stream.write(" ✅")
            self.stream.flush()
            
    def addError(self, test, err):
        """Called when a test has an error."""
        super().addError(test, err)
        if self.verbosity >= 2:
            self.stream.write(" 💥")
            self.stream.flush()
            
    def addFailure(self, test, err):
        """Called when a test fails."""
        super().addFailure(test, err)
        if self.verbosity >= 2:
            self.stream.write(" ❌")
            self.stream.flush()
            
    def addSkip(self, test, reason):
        """Called when a test is skipped."""
        super().addSkip(test, reason)
        if self.verbosity >= 2:
            self.stream.write(" ⏭️")
            self.stream.flush()


class TimedTextTestRunner(unittest.TextTestRunner):
    """Custom test runner that uses TimedTextTestResult."""
    
    resultclass = TimedTextTestResult
    
    def __init__(self, timeout_seconds=5.0, **kwargs):
        super().__init__(**kwargs)
        self.timeout_seconds = timeout_seconds
        
    @contextmanager
    def timeout_handler(self, test_name):
        """Context manager for test timeouts."""
        def timeout_handler(signum, frame):
            raise TestTimeout(f"Test '{test_name}' exceeded {self.timeout_seconds}s timeout!")
        
        # Set up the timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.timeout_seconds))
        
        try:
            yield
        finally:
            # Disable the timeout
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def run(self, test):
        """Run the test suite with timing."""
        self.stream.write("\n🚀 Starting Timed Test Run\n")
        self.stream.write("=" * 70 + "\n")
        self.stream.write("Legend: 🟢 <0.1s | 🟡 0.1-0.5s | 🔴 >0.5s | 💀 >2s\n")
        self.stream.write("=" * 70 + "\n")
        
        # Set a flag to prevent recursive test runs
        if hasattr(self, '_running') and self._running:
            self.stream.write("\n⚠️  WARNING: Recursive test run detected! Skipping...\n")
            return unittest.TestResult()
        
        self._running = True
        try:
            start_time = time.time()
            result = super().run(test)
            total_time = time.time() - start_time
            
            # Print performance summary
            self._print_performance_summary(result, total_time)
            
            return result
        finally:
            self._running = False
    
    def _print_performance_summary(self, result, total_time):
        """Print a detailed performance summary."""
        self.stream.write("\n" + "=" * 70 + "\n")
        self.stream.write("📊 PERFORMANCE SUMMARY\n")
        self.stream.write("=" * 70 + "\n")
        
        # Overall stats
        self.stream.write(f"Total time: {total_time:.3f}s\n")
        self.stream.write(f"Total tests: {result.testsRun}\n")
        if result.testsRun > 0:
            avg_time = total_time / result.testsRun
            self.stream.write(f"Average time per test: {avg_time:.3f}s\n")
        
        # Slow tests report
        if result.slow_tests:
            self.stream.write("\n🐌 SLOWEST TESTS:\n")
            self.stream.write("-" * 50 + "\n")
            sorted_slow = sorted(result.slow_tests, key=lambda x: x[1], reverse=True)
            for i, (test_name, elapsed) in enumerate(sorted_slow[:10], 1):
                if elapsed > 2.0:
                    self.stream.write(f"{i}. \033[35m💀 {test_name}: {elapsed:.3f}s\033[0m\n")
                elif elapsed > 0.5:
                    self.stream.write(f"{i}. \033[31m🔴 {test_name}: {elapsed:.3f}s\033[0m\n")
                else:
                    self.stream.write(f"{i}. \033[33m🟡 {test_name}: {elapsed:.3f}s\033[0m\n")
        
        # Module timing breakdown
        if result.module_times:
            self.stream.write("\n📦 TIME BY MODULE:\n")
            self.stream.write("-" * 50 + "\n")
            sorted_modules = sorted(result.module_times.items(), key=lambda x: x[1], reverse=True)
            for module, module_time in sorted_modules:
                percentage = (module_time / total_time) * 100
                self.stream.write(f"{module}: {module_time:.3f}s ({percentage:.1f}%)\n")
        
        # Warnings
        if any(t[1] > 2.0 for t in result.slow_tests):
            self.stream.write("\n\033[1;31m⚠️  CRITICAL WARNING: Some tests took over 2 seconds!\033[0m\n")
            self.stream.write("Consider:\n")
            self.stream.write("- Checking for time.sleep() calls\n")
            self.stream.write("- Optimizing database queries\n")
            self.stream.write("- Mocking external services\n")
            self.stream.write("- Using faster test fixtures\n")
        
        # Enhanced performance analytics
        self._analyze_color_distribution(result, total_time)
        self._analyze_module_performance(result)
        self._get_performance_insights(result)
    
    def _analyze_color_distribution(self, result, total_time):
        """Analyze and display color distribution statistics."""
        total_tests = result.testsRun
        if total_tests == 0:
            return
            
        self.stream.write("\n🎯 PERFORMANCE ANALYTICS\n")
        self.stream.write("=" * 70 + "\n")
        self.stream.write("Test Distribution:\n")
        
        for color, count in [('💀', result.color_counts['💀']), 
                           ('🔴', result.color_counts['🔴']), 
                           ('🟡', result.color_counts['🟡']), 
                           ('🟢', result.color_counts['🟢'])]:
            if count > 0:
                percentage = (count / total_tests) * 100
                if color == '💀':
                    category = "Critical (>2s)"
                elif color == '🔴':
                    category = "Slow (0.5-2s)"
                elif color == '🟡':
                    category = "Medium (0.1-0.5s)"
                else:
                    category = "Fast (<0.1s)"
                self.stream.write(f"  {color} {category}: {count} tests ({percentage:.1f}%)\n")
    
    def _analyze_module_performance(self, result):
        """Analyze and display module performance statistics."""
        if not result.module_color_stats:
            return
            
        self.stream.write("\n📊 MODULE PERFORMANCE ANALYSIS\n")
        self.stream.write("-" * 70 + "\n")
        
        # Find modules with slow tests
        modules_with_slow_tests = []
        for module, stats in result.module_color_stats.items():
            slow_count = stats['🔴'] + stats['💀']
            if slow_count > 0:
                modules_with_slow_tests.append((module, slow_count, stats))
        
        if modules_with_slow_tests:
            self.stream.write("Modules with most slow tests:\n")
            # Sort by total slow tests (red + critical)
            modules_with_slow_tests.sort(key=lambda x: x[1], reverse=True)
            
            for i, (module, slow_count, stats) in enumerate(modules_with_slow_tests[:5], 1):
                detail = []
                if stats['💀'] > 0:
                    detail.append(f"{stats['💀']}💀")
                if stats['🔴'] > 0:
                    detail.append(f"{stats['🔴']}🔴")
                if stats['🟡'] > 0:
                    detail.append(f"{stats['🟡']}🟡")
                detail_str = ", ".join(detail) if detail else ""
                self.stream.write(f"  {i}. {module}: {slow_count} slow tests ({detail_str})\n")
        else:
            self.stream.write("🎉 No modules have slow tests!\n")
    
    def _get_performance_insights(self, result):
        """Generate smart performance insights based on test distribution."""
        self.stream.write("\n📈 PERFORMANCE INSIGHTS\n")
        self.stream.write("-" * 70 + "\n")
        
        # Smart reporting based on what categories exist
        if result.color_counts['💀'] > 0:
            # Focus on critical tests
            self.stream.write("🚨 CRITICAL ATTENTION NEEDED:\n")
            critical_tests = sorted(result.color_tests['💀'], key=lambda x: x[1], reverse=True)
            for i, (test_name, elapsed) in enumerate(critical_tests[:5], 1):
                self.stream.write(f"  {i}. {test_name}: {elapsed:.3f}s\n")
                
        elif result.color_counts['🔴'] > 0:
            # Focus on slow tests
            self.stream.write("⚠️  SLOW TESTS NEED OPTIMIZATION:\n")
            slow_tests = sorted(result.color_tests['🔴'], key=lambda x: x[1], reverse=True)
            for i, (test_name, elapsed) in enumerate(slow_tests[:5], 1):
                self.stream.write(f"  {i}. {test_name}: {elapsed:.3f}s\n")
                
        elif result.color_counts['🟡'] > 0:
            # Focus on medium tests if no slow ones
            self.stream.write("📊 SLOWEST MEDIUM TESTS:\n")
            medium_tests = sorted(result.color_tests['🟡'], key=lambda x: x[1], reverse=True)
            for i, (test_name, elapsed) in enumerate(medium_tests[:5], 1):
                self.stream.write(f"  {i}. {test_name}: {elapsed:.3f}s\n")
                
        else:
            # Only green tests - show slowest greens
            self.stream.write("✨ ALL TESTS ARE FAST! Slowest green tests:\n")
            green_tests = sorted(result.color_tests['🟢'], key=lambda x: x[1], reverse=True)
            for i, (test_name, elapsed) in enumerate(green_tests[:5], 1):
                self.stream.write(f"  {i}. {test_name}: {elapsed:.3f}s\n")
        
        # Add summary recommendation
        total_slow = result.color_counts['💀'] + result.color_counts['🔴']
        if total_slow > 0:
            self.stream.write(f"\n💡 RECOMMENDATION: Focus on optimizing {total_slow} slow tests for better performance.\n")
        elif result.color_counts['🟡'] > 0:
            self.stream.write(f"\n✅ GOOD: No slow tests! Consider optimizing {result.color_counts['🟡']} medium tests.\n")
        else:
            self.stream.write("\n🎉 EXCELLENT: All tests are fast! Great job optimizing your test suite!\n")

# Add the backend directory to Python path so performance_testing can be imported as a package
PERFORMANCE_TESTING_ROOT = Path(__file__).parent
BACKEND_ROOT = PERFORMANCE_TESTING_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Global flag to prevent recursive test runner execution
_TEST_RUNNER_ACTIVE = False

# Configure Django settings for testing
try:
    import django
    from django.conf import settings
    
    # Configure minimal Django settings for testing
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY='test-secret-key-for-mercury-testing',
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'rest_framework',
            ],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            REST_FRAMEWORK={
                'TEST_REQUEST_DEFAULT_FORMAT': 'json',
                'TEST_REQUEST_RENDERER_CLASSES': [
                    'rest_framework.renderers.JSONRenderer',
                ],
            }
        )
    django.setup()
    DJANGO_AVAILABLE = True
except ImportError:
    # Django not available, tests will skip Django-specific functionality
    DJANGO_AVAILABLE = False
except Exception as e:
    # Django configuration failed, continue without it
    DJANGO_AVAILABLE = False
    print(f"⚠️  Django setup failed: {e}")

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    print("⚠️  Coverage module not available. Install with: pip install coverage")


def get_test_modules() -> List[str]:
    """Get list of all test modules in the tests directory."""
    tests_dir = PERFORMANCE_TESTING_ROOT / "tests"
    test_modules = []
    
    # Define test subdirectories
    test_subdirs = [
        'monitor',
        'django_integration/mercury_api',
        'django_integration/performance_api',
        'hooks',
        'bindings',
        'core',
        'config',
        'integration'
    ]
    
    # Discover tests from each subdirectory
    for subdir in test_subdirs:
        subdir_path = tests_dir / subdir
        if subdir_path.exists():
            # Get all test files in this subdirectory
            for test_file in subdir_path.glob("test_*.py"):
                # Construct the module path
                module_parts = ['tests'] + subdir.split('/') + [test_file.stem]
                module_name = '.'.join(module_parts)
                test_modules.append(module_name)
    
    return test_modules


def run_tests_with_coverage(test_modules: List[str], verbose: bool = False, no_timing: bool = False) -> bool:
    """Run tests with coverage reporting."""
    if not COVERAGE_AVAILABLE:
        print("❌ Coverage not available, running tests without coverage")
        return run_tests_without_coverage(test_modules, verbose, no_timing)
    
    # Configure coverage
    cov = coverage.Coverage(
        source=[str(PERFORMANCE_TESTING_ROOT / 'django_mercury' / 'python_bindings')],
        omit=[
            '*/tests/*',
            '*/test_*',
            '*/__pycache__/*',
            '*/.*'
        ]
    )
    
    print("🔍 Starting tests with coverage analysis...")
    cov.start()
    
    try:
        # Run the tests
        success = run_tests_without_coverage(test_modules, verbose, no_timing)
        
        # Stop coverage
        cov.stop()
        cov.save()
        
        # Generate coverage report
        print("\n" + "="*60)
        print("📊 COVERAGE REPORT")
        print("="*60)
        
        # Console report
        cov.report(show_missing=True)
        
        # HTML report
        html_dir = BACKEND_ROOT / "performance_testing" / "htmlcov"
        cov.html_report(directory=str(html_dir))
        print(f"\n📄 HTML coverage report generated in: {html_dir}")
        
        # Check for 100% coverage
        total_coverage = cov.report(show_missing=False)
        if total_coverage >= 100.0:
            print("🎉 EXCELLENT! 100% test coverage achieved!")
        elif total_coverage >= 95.0:
            print(f"✅ Great! {total_coverage:.1f}% coverage (very close to 100%)")
        elif total_coverage >= 80.0:
            print(f"👍 Good! {total_coverage:.1f}% coverage")
        else:
            print(f"⚠️  Coverage is {total_coverage:.1f}% - needs improvement")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during coverage analysis: {e}")
        cov.stop()
        return False


def run_tests_without_coverage(test_modules: List[str], verbose: bool = False, no_timing: bool = False) -> bool:
    """Run tests without coverage."""
    print("🧪 Running unit tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            suite.addTests(loader.loadTestsFromModule(module))
            print(f"✅ Loaded tests from {module_name}")
        except ImportError as e:
            print(f"⚠️  Could not import {module_name}: {e}")
            print(f"   💡 Hint: Check for syntax errors or missing dependencies in the module")
            if "No module named" in str(e):
                print(f"   💡 Hint: Make sure the module path is correct and all required packages are installed")
        except Exception as e:
            print(f"❌ Error loading {module_name}: {e}")
            print(f"   💡 Hint: Check for syntax errors, import issues, or configuration problems")
            if "django" in str(e).lower() or "settings" in str(e).lower():
                print(f"   💡 Django Hint: Make sure Django settings are properly configured")
            if "false" in str(e).lower() and "not defined" in str(e).lower():
                print(f"   💡 Syntax Hint: Check for lowercase 'false/true' instead of 'False/True' in Python code")
    
    # Run tests with timing or standard runner
    verbosity = 2 if verbose else 1
    if no_timing:
        runner = unittest.TextTestRunner(verbosity=verbosity, buffer=False)
    else:
        runner = TimedTextTestRunner(verbosity=verbosity, buffer=False, timeout_seconds=5.0)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return success


def run_specific_module_tests(module_name: str, verbose: bool = False, with_coverage: bool = False, no_timing: bool = False) -> bool:
    """Run tests for a specific module."""
    test_module = f"tests.test_{module_name}"
    
    if with_coverage and COVERAGE_AVAILABLE:
        return run_tests_with_coverage([test_module], verbose, no_timing)
    else:
        return run_tests_without_coverage([test_module], verbose, no_timing)


def run_c_integration_tests(verbose: bool = False) -> bool:
    """Run C library integration tests."""
    print("\n" + "="*60)
    print("🔧 C LIBRARY INTEGRATION TESTS")
    print("="*60)
    
    # Check if C libraries are built
    c_core = PERFORMANCE_TESTING_ROOT / "c_core"
    required_libs = ["libperformance.so", "libquery_analyzer.so", "libmetrics_engine.so", "libtest_orchestrator.so"]
    missing_libs = [lib for lib in required_libs if not (c_core / lib).exists()]
    
    if missing_libs:
        print(f"⚠️  Missing C libraries: {', '.join(missing_libs)}")
        print("💡 Run 'make all' in the c_core directory to build them")
        return False
    
    # Run the integration test
    try:
        test_script = PERFORMANCE_TESTING_ROOT / "tests" / "bindings" / "test_c_integration_simple.py"
        if test_script.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            return result.returncode == 0
        else:
            # Inline basic C integration test
            import ctypes
            lib_path = c_core / "libperformance.so"
            lib = ctypes.CDLL(str(lib_path))
            
            # Basic smoke test
            lib.start_performance_monitoring_enhanced.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            lib.start_performance_monitoring_enhanced.restype = ctypes.c_int64
            
            handle = lib.start_performance_monitoring_enhanced(b"test", b"test")
            if handle > 0:
                print("✅ C library integration test passed")
                return True
            else:
                print("❌ C library integration test failed")
                return False
                
    except Exception as e:
        print(f"❌ C integration test error: {e}")
        return False


def setup_test_environment():
    """Set up the test environment."""
    import logging
    
    # Suppress verbose logging during tests
    logging.getLogger('django_mercury.python_bindings.c_bindings').setLevel(logging.WARNING)
    logging.getLogger('performance_testing.validation').setLevel(logging.ERROR)
    logging.getLogger('performance_testing.functional_test').setLevel(logging.ERROR)
    logging.getLogger('performance_testing.test_integration').setLevel(logging.ERROR)
    logging.getLogger('performance_testing.independent1').setLevel(logging.ERROR)
    logging.getLogger('performance_testing.independent2').setLevel(logging.ERROR)
    logging.getLogger('performance_testing.thread_safety').setLevel(logging.ERROR)
    
    # Ensure tests directory exists
    tests_dir = PERFORMANCE_TESTING_ROOT / "tests"
    tests_dir.mkdir(exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = tests_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Performance Testing Framework Tests\n")


def main():
    """Main entry point for the test runner."""
    global _TEST_RUNNER_ACTIVE
    
    # Prevent recursive execution
    if _TEST_RUNNER_ACTIVE:
        print("⚠️  Test runner is already active! Preventing recursive execution.")
        return
    
    _TEST_RUNNER_ACTIVE = True
    try:
        # Original main() implementation
        parser = argparse.ArgumentParser(
            description="Performance Testing Framework Test Runner"
        )
        parser.add_argument(
            "--coverage", 
            action="store_true", 
            help="Run tests with coverage analysis"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true", 
            help="Verbose test output"
        )
        parser.add_argument(
            "--module", "-m",
            type=str,
            help="Run tests for specific module (e.g., 'colors', 'metrics')"
        )
        parser.add_argument(
            "--list-modules",
            action="store_true",
            help="List all available test modules"
        )
        parser.add_argument(
            "--c-tests",
            action="store_true",
            help="Run C library integration tests"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Run all tests including C integration tests"
        )
        parser.add_argument(
            "--no-timing",
            action="store_true",
            help="Disable test timing (use standard runner)"
        )
        
        args = parser.parse_args()
        
        # Setup environment
        setup_test_environment()
        
        print("🚀 Performance Testing Framework Test Runner")
        print("="*50)
        
        if args.list_modules:
            print("📁 Available test modules:")
            test_modules = get_test_modules()
            if test_modules:
                for module in test_modules:
                    print(f"  - {module}")
            else:
                print("  No test modules found")
            return
        
        # Check if any test files exist
        test_modules = get_test_modules()
        if not test_modules:
            print("⚠️  No test files found in tests/ directory")
            print("Please create test files with names like test_colors.py, test_metrics.py, etc.")
            return
        
        # Run tests
        success = True
        
        if args.c_tests or args.all:
            # Run C integration tests
            c_success = run_c_integration_tests(args.verbose)
            success = success and c_success
        
        if args.module:
            print(f"🎯 Running tests for module: {args.module}")
            module_success = run_specific_module_tests(args.module, args.verbose, args.coverage, args.no_timing)
            success = success and module_success
        elif not args.c_tests or args.all:  # Run Python tests if not just C tests
            print(f"🧪 Running all tests ({len(test_modules)} modules)")
            if args.coverage:
                python_success = run_tests_with_coverage(test_modules, args.verbose, args.no_timing)
            else:
                python_success = run_tests_without_coverage(test_modules, args.verbose, args.no_timing)
            success = success and python_success
        
        # Final summary
        if args.all:
            print("\n" + "="*60)
            print("📊 OVERALL TEST SUMMARY")
            print("="*60)
            if success:
                print("✅ All tests (Python + C) passed!")
            else:
                print("❌ Some tests failed!")
    
        # Exit with appropriate code
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    finally:
        _TEST_RUNNER_ACTIVE = False


if __name__ == "__main__":
    main()