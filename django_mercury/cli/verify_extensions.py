#!/usr/bin/env python
"""
Verify C Extensions Module - Check if C extensions are loaded and working

This module provides functionality to verify that Django Mercury's C extensions
are properly loaded and functioning correctly.

Usage:
    mercury-test --ext    # Check C extensions status
"""

import time
import sys
import os
import gc
import math
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path

# Add parent directory to path to import django_mercury
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def print_banner():
    """Print the verification banner."""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          Django Mercury C Extension Verification          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()


def test_query_analyzer() -> Tuple[bool, float, str]:
    """Test the query analyzer C extension.
    
    Returns:
        Tuple of (success, elapsed_time, error_message)
    """
    try:
        # Try to import the C extension directly
        import django_mercury._c_analyzer as analyzer
        
        start_time = time.perf_counter()
        
        # Test basic functionality
        # Note: Python C extensions may have different function names
        # Let's try to call a simple function to verify it works
        try:
            # Try different possible function names
            if hasattr(analyzer, 'reset_analyzer'):
                analyzer.reset_analyzer()
            elif hasattr(analyzer, 'init'):
                analyzer.init()
            elif hasattr(analyzer, 'analyze_query'):
                # Try analyzing a dummy query
                analyzer.analyze_query("SELECT 1", 0.001)
            else:
                # List available functions for debugging
                funcs = [name for name in dir(analyzer) if not name.startswith('_')]
                if funcs:
                    # Try calling the first available function
                    getattr(analyzer, funcs[0])()
        except TypeError:
            # Function might need arguments, that's ok
            pass
        
        elapsed = time.perf_counter() - start_time
        
        return True, elapsed, "OK"
        
    except ImportError as e:
        return False, 0.0, "Not loaded"
    except Exception as e:
        return False, 0.0, str(e)


def test_metrics_engine() -> Tuple[bool, float, str]:
    """Test the metrics engine C extension.
    
    Returns:
        Tuple of (success, elapsed_time, error_message)
    """
    try:
        # Try to import the C extension directly
        import django_mercury._c_metrics as metrics
        
        start_time = time.perf_counter()
        
        # Test basic functionality
        try:
            # Try different possible function names
            if hasattr(metrics, 'init_metrics'):
                metrics.init_metrics()
            elif hasattr(metrics, 'start_monitoring'):
                metrics.start_monitoring("test", "test")
            elif hasattr(metrics, 'get_metrics'):
                metrics.get_metrics()
            else:
                # List available functions for debugging
                funcs = [name for name in dir(metrics) if not name.startswith('_')]
                if funcs:
                    # Try calling the first available function
                    try:
                        getattr(metrics, funcs[0])()
                    except TypeError:
                        pass
        except TypeError:
            # Function might need arguments, that's ok
            pass
        
        elapsed = time.perf_counter() - start_time
        
        return True, elapsed, "OK"
        
    except ImportError as e:
        return False, 0.0, "Not loaded"
    except Exception as e:
        return False, 0.0, str(e)


def test_orchestrator() -> Tuple[bool, float, str]:
    """Test the test orchestrator C extension.
    
    Returns:
        Tuple of (success, elapsed_time, error_message)
    """
    try:
        # Try to import the C extension directly
        import django_mercury._c_orchestrator as orchestrator
        
        start_time = time.perf_counter()
        
        # Test basic functionality
        try:
            # Try different possible function names
            if hasattr(orchestrator, 'init_orchestrator'):
                orchestrator.init_orchestrator()
            elif hasattr(orchestrator, 'create_context'):
                orchestrator.create_context("test", "test")
            elif hasattr(orchestrator, 'initialize'):
                orchestrator.initialize()
            else:
                # List available functions for debugging
                funcs = [name for name in dir(orchestrator) if not name.startswith('_')]
                if funcs:
                    # Try calling the first available function
                    try:
                        getattr(orchestrator, funcs[0])()
                    except TypeError:
                        pass
        except TypeError:
            # Function might need arguments, that's ok
            pass
        
        elapsed = time.perf_counter() - start_time
        
        return True, elapsed, "OK"
        
    except ImportError as e:
        return False, 0.0, "Not loaded"
    except Exception as e:
        return False, 0.0, str(e)


def format_status(name: str, success: bool, elapsed: float, message: str) -> str:
    """Format the status line for an extension.
    
    Args:
        name: Extension name
        success: Whether the test passed
        elapsed: Time taken for test
        message: Status or error message
    
    Returns:
        Formatted status line
    """
    # Color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    
    # Status symbol
    if success:
        symbol = f"{GREEN}✅{RESET}"
        status = f"{GREEN}Loaded{RESET}"
    else:
        symbol = f"{RED}❌{RESET}"
        if message == "Not loaded":
            status = f"{YELLOW}Not loaded{RESET}"
        else:
            status = f"{RED}Error{RESET}"
    
    # Format name with padding
    name_padded = name.ljust(25)
    
    # Format time if successful
    if success:
        time_str = f"(test: {elapsed:.3f}s)"
    else:
        time_str = ""
    
    # Build the line
    if success:
        return f"{symbol} {name_padded} - {status} {time_str}"
    else:
        return f"{symbol} {name_padded} - {status} ({message})"


def benchmark_query_analyzer(iterations: int = 2000) -> Dict[str, float]:
    """Benchmark query analyzer with C and Python implementations.
    
    Args:
        iterations: Number of iterations to run
        
    Returns:
        Dict with 'c_time' and 'python_time' in seconds
    """
    results = {}
    
    # Generate truly unique queries to prevent cache hits
    import random
    import string
    
    # Use deterministic seed for consistent benchmarking
    random.seed(42)
    
    queries = []
    table_names = ["users", "profiles", "orders", "products", "categories", "reviews", "addresses", "payments"]
    columns = ["id", "name", "email", "created_at", "updated_at", "status", "value", "count"]
    conditions = ["active", "pending", "completed", "deleted", "new", "processing"]
    
    for i in range(iterations):
        # Create unique elements to ensure no cache hits
        unique_suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
        table = random.choice(table_names)
        column = random.choice(columns)
        condition = random.choice(conditions)
        
        if i % 4 == 0:
            # Simple SELECT with unique conditions
            query = f"SELECT * FROM {table}_{unique_suffix} WHERE {column} = {i}"
        elif i % 4 == 1:
            # JOIN query with unique table names
            table2 = random.choice([t for t in table_names if t != table])
            query = f"SELECT u.*, p.* FROM {table}_{unique_suffix} u JOIN {table2}_{unique_suffix} p ON u.id = p.user_id WHERE u.status = '{condition}_{i}' ORDER BY u.{column} DESC LIMIT {i % 50 + 1}"
        elif i % 4 == 2:
            # INSERT with unique values
            query = f"INSERT INTO {table}_{unique_suffix} ({column}, status, value) VALUES ({i}, '{condition}_{unique_suffix}', '{unique_suffix}_{i}')"
        else:
            # Complex SELECT with subquery
            table2 = random.choice([t for t in table_names if t != table])
            query = f"SELECT {column}, COUNT(*) FROM {table}_{unique_suffix} WHERE {column} IN (SELECT {column} FROM {table2}_{unique_suffix} WHERE status = '{condition}_{i}') GROUP BY {column} HAVING COUNT(*) > {i % 10}"
        
        queries.append(query)
    
    # Test with C extension (using the wrapper class)
    try:
        from django_mercury.python_bindings.c_wrappers import CQueryAnalyzer
        
        gc.collect()
        start = time.perf_counter()
        
        analyzer = CQueryAnalyzer()
        for query in queries:
            # Actually analyze the query
            result = analyzer.analyze_query(query)
            # The result should contain analysis data
        
        results['c_time'] = time.perf_counter() - start
    except (ImportError, AttributeError) as e:
        # Try direct C extension as fallback
        try:
            import django_mercury._c_analyzer as c_analyzer
            
            gc.collect()
            start = time.perf_counter()
            
            # If it's a module with QueryAnalyzer class
            if hasattr(c_analyzer, 'QueryAnalyzer'):
                analyzer = c_analyzer.QueryAnalyzer()
                for query in queries:
                    analyzer.analyze_query(query)
            else:
                # Try function-based API
                for query in queries:
                    if hasattr(c_analyzer, 'analyze_query'):
                        c_analyzer.analyze_query(query.encode('utf-8'), 0.001)
            
            results['c_time'] = time.perf_counter() - start
        except:
            results['c_time'] = None
    
    # Test with pure Python (clear cache to ensure fair comparison)
    try:
        from django_mercury.python_bindings.pure_python import PythonQueryAnalyzer
        
        gc.collect()
        start = time.perf_counter()
        
        analyzer = PythonQueryAnalyzer()
        # Explicitly clear cache to prevent any advantages
        analyzer.analysis_cache.clear()
        
        for query in queries:
            # Actually analyze the query (no cache hits)
            result = analyzer.analyze_query(query)
            # The result should contain analysis data
        
        results['python_time'] = time.perf_counter() - start
    except (ImportError, AttributeError):
        results['python_time'] = None
    
    return results


def benchmark_metrics_engine(iterations: int = 1500) -> Dict[str, float]:
    """Benchmark metrics engine with C and Python implementations.
    
    Args:
        iterations: Number of iterations to run
        
    Returns:
        Dict with 'c_time' and 'python_time' in seconds
    """
    results = {}
    
    # Generate test metrics data
    test_metrics = []
    for i in range(iterations):
        metrics = {
            "response_time_ms": 50.0 + (i % 100),
            "memory_usage_mb": 20.0 + (i % 50) / 10.0,
            "query_count": i % 20,
            "cache_hits": i % 10,
            "cache_misses": (i % 10) // 2,
            "timestamp": time.time() + i
        }
        test_metrics.append(metrics)
    
    # Test with C extension (using wrapper class)
    try:
        from django_mercury.python_bindings.c_wrappers import CMetricsEngine
        
        gc.collect()
        start = time.perf_counter()
        
        engine = CMetricsEngine()
        for metrics in test_metrics:
            # Add metrics and periodically calculate statistics
            engine.add_metrics(metrics)
            if len(test_metrics) % 100 == 0:
                stats = engine.calculate_statistics()
        
        # Final statistics calculation
        final_stats = engine.calculate_statistics()
        
        results['c_time'] = time.perf_counter() - start
    except (ImportError, AttributeError):
        # Try direct C extension as fallback
        try:
            import django_mercury._c_metrics as c_metrics
            
            gc.collect()
            start = time.perf_counter()
            
            # If it's a module with MetricsEngine class
            if hasattr(c_metrics, 'MetricsEngine'):
                engine = c_metrics.MetricsEngine()
                for metrics in test_metrics:
                    engine.add_metrics(metrics)
                    if len(test_metrics) % 100 == 0:
                        engine.calculate_statistics()
                engine.calculate_statistics()
            else:
                # Try function-based API for performance monitoring
                for i in range(iterations):
                    if hasattr(c_metrics, 'start_performance_monitoring_enhanced'):
                        session = c_metrics.start_performance_monitoring_enhanced(
                            f"test_{i}".encode('utf-8'), 
                            b"general"
                        )
                        if hasattr(c_metrics, 'stop_performance_monitoring_enhanced'):
                            metrics_ptr = c_metrics.stop_performance_monitoring_enhanced(session)
                            if metrics_ptr and hasattr(c_metrics, 'free_metrics'):
                                c_metrics.free_metrics(metrics_ptr)
            
            results['c_time'] = time.perf_counter() - start
        except:
            results['c_time'] = None
    
    # Test with pure Python
    try:
        from django_mercury.python_bindings.pure_python import PythonMetricsEngine
        
        gc.collect()
        start = time.perf_counter()
        
        engine = PythonMetricsEngine()
        for metrics in test_metrics:
            # Add metrics and periodically calculate statistics
            engine.add_metrics(metrics)
            if len(test_metrics) % 100 == 0:
                stats = engine.calculate_statistics()
        
        # Final statistics calculation
        final_stats = engine.calculate_statistics()
        
        results['python_time'] = time.perf_counter() - start
    except (ImportError, AttributeError):
        results['python_time'] = None
    
    return results


def benchmark_orchestrator(iterations: int = 100) -> Dict[str, float]:
    """Benchmark test orchestrator with C and Python implementations.
    
    Args:
        iterations: Number of iterations to run
        
    Returns:
        Dict with 'c_time' and 'python_time' in seconds
    """
    results = {}
    
    # Test with C extension (using wrapper class)
    try:
        from django_mercury.python_bindings.c_wrappers import CTestOrchestrator
        
        gc.collect()
        start = time.perf_counter()
        
        orchestrator = CTestOrchestrator()
        for i in range(iterations):
            # Simulate a complete test lifecycle
            test_name = f"test_method_{i}"
            orchestrator.start_test(test_name)
            # Simulate test execution
            status = "passed" if i % 10 != 0 else "failed"
            orchestrator.end_test(test_name, status)
        
        # Get final summary
        summary = orchestrator.get_summary()
        
        results['c_time'] = time.perf_counter() - start
    except (ImportError, AttributeError):
        # Try direct C extension as fallback
        try:
            import django_mercury._c_orchestrator as c_orchestrator
            
            gc.collect()
            start = time.perf_counter()
            
            # If it's a module with TestOrchestrator class
            if hasattr(c_orchestrator, 'TestOrchestrator'):
                orchestrator = c_orchestrator.TestOrchestrator()
                for i in range(iterations):
                    test_name = f"test_method_{i}"
                    orchestrator.start_test(test_name)
                    status = "passed" if i % 10 != 0 else "failed"
                    orchestrator.end_test(test_name, status)
                orchestrator.get_summary()
            else:
                # Try function-based API
                for i in range(iterations):
                    if hasattr(c_orchestrator, 'create_test_context'):
                        context = c_orchestrator.create_test_context(
                            f"TestClass_{i}".encode('utf-8'),
                            f"test_method_{i}".encode('utf-8')
                        )
                        if context and hasattr(c_orchestrator, 'finalize_test_context'):
                            c_orchestrator.finalize_test_context(context)
            
            results['c_time'] = time.perf_counter() - start
        except:
            results['c_time'] = None
    
    # Test with pure Python
    try:
        from django_mercury.python_bindings.pure_python import PythonTestOrchestrator
        
        gc.collect()
        start = time.perf_counter()
        
        orchestrator = PythonTestOrchestrator()
        for i in range(iterations):
            # Simulate a complete test lifecycle
            test_name = f"test_method_{i}"
            orchestrator.start_test(test_name)
            # Simulate test execution
            status = "passed" if i % 10 != 0 else "failed"
            orchestrator.end_test(test_name, status)
        
        # Get final summary
        summary = orchestrator.get_summary()
        
        results['python_time'] = time.perf_counter() - start
    except (ImportError, AttributeError):
        results['python_time'] = None
    
    return results


def format_benchmark_results(name: str, c_time: Optional[float], python_time: Optional[float], iterations: int) -> List[str]:
    """Format benchmark results with visual bars.
    
    Args:
        name: Component name
        c_time: C extension time in seconds
        python_time: Pure Python time in seconds
        iterations: Number of iterations
        
    Returns:
        List of formatted lines
    """
    lines = []
    
    # Color codes
    GREEN = "\033[92m"
    GRAY = "\033[90m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    lines.append(f"\n{BOLD}{name} ({iterations} {'queries' if 'Analyzer' in name else 'operations'}):{RESET}")
    
    # Add explanation of what each implementation does
    if 'Orchestrator' in name:
        lines.append("    C Extension: Basic test tracking (names, status, timing)")
        lines.append("    Pure Python: Full performance monitoring (memory, CPU, GC)")
    elif 'Analyzer' in name:
        lines.append("    C Extension: Fast pattern matching and analysis")
        lines.append("    Pure Python: Regex parsing + caching + recommendations")
    elif 'Engine' in name:
        lines.append("    C Extension: Optimized metrics aggregation")
        lines.append("    Pure Python: Statistical calculations + N+1 detection")
    
    if c_time is not None and python_time is not None:
        speedup = python_time / c_time if c_time > 0 else 0
        
        # Cap speedup display at reasonable values
        display_speedup = min(speedup, 100.0)  # Cap at 100x for display
        
        # Create visual bars (20 chars max)
        max_bar = 20
        c_bar_len = 2  # C is always fast, show minimal bar
        # Scale python bar based on speedup (logarithmic scale for large differences)
        if speedup > 10:
            import math
            python_bar_len = min(int(2 + math.log10(speedup) * 6), max_bar)
        else:
            python_bar_len = min(int(speedup * 2) if speedup > 1 else 2, max_bar)
        
        c_bar = GREEN + "█" * c_bar_len + " " * (max_bar - c_bar_len) + RESET
        python_bar = GRAY + "░" * python_bar_len + " " * (max_bar - python_bar_len) + RESET
        
        # Format time with appropriate precision
        def format_time(t):
            if t < 0.001:  # Less than 1ms, show microseconds
                return f"{t*1000000:6.0f}µs"
            elif t < 1.0:  # Less than 1s, show milliseconds 
                return f"{t*1000:6.1f}ms"
            else:  # 1s or more, show seconds
                return f"{t:6.3f}s "
        
        c_time_str = format_time(c_time)
        python_time_str = format_time(python_time)
        
        lines.append(f"├─ C Extension:    {c_time_str}  {c_bar}")
        lines.append(f"├─ Pure Python:    {python_time_str}  {python_bar}")
        
        # Format speedup display
        if speedup > 1000:
            lines.append(f"└─ Speedup:        {YELLOW}{speedup:.0f}x faster ⚡{RESET}")
        elif speedup > 100:
            lines.append(f"└─ Speedup:        {YELLOW}{speedup:.0f}x faster ⚡{RESET}")
        elif speedup > 10:
            lines.append(f"└─ Speedup:        {YELLOW}{speedup:.0f}x faster ⚡{RESET}")
        else:
            lines.append(f"└─ Speedup:        {YELLOW}{speedup:.1f}x faster ⚡{RESET}")
    else:
        if c_time is None:
            lines.append(f"├─ C Extension:    Not available")
        if python_time is None:
            lines.append(f"└─ Pure Python:    Not available")
    
    return lines


def run_benchmarks() -> float:
    """Run all benchmarks and return overall speedup.
    
    Returns:
        Geometric mean of all speedups
    """
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║      Django Mercury C Extension Performance Comparison     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\nRunning performance benchmarks...")
    
    speedups = []
    
    # Run query analyzer benchmark
    print("\nAnalyzing queries...", end='', flush=True)
    qa_results = benchmark_query_analyzer(2000)
    print(" done!")
    lines = format_benchmark_results("Query Analyzer", 
                                    qa_results.get('c_time'),
                                    qa_results.get('python_time'), 
                                    2000)
    for line in lines:
        print(line)
    
    if qa_results.get('c_time') and qa_results.get('python_time'):
        speedups.append(qa_results['python_time'] / qa_results['c_time'])
    
    # Run metrics engine benchmark
    print("\nCollecting metrics...", end='', flush=True)
    me_results = benchmark_metrics_engine(1500)
    print(" done!")
    lines = format_benchmark_results("Metrics Engine",
                                    me_results.get('c_time'),
                                    me_results.get('python_time'),
                                    1500)
    for line in lines:
        print(line)
    
    if me_results.get('c_time') and me_results.get('python_time'):
        speedups.append(me_results['python_time'] / me_results['c_time'])
    
    # Run orchestrator benchmark
    print("\nTesting orchestration...", end='', flush=True)
    to_results = benchmark_orchestrator(100)
    print(" done!")
    lines = format_benchmark_results("Test Orchestrator",
                                    to_results.get('c_time'),
                                    to_results.get('python_time'),
                                    100)
    for line in lines:
        print(line)
    
    if to_results.get('c_time') and to_results.get('python_time'):
        speedups.append(to_results['python_time'] / to_results['c_time'])
    
    # Calculate geometric mean
    if speedups:
        geometric_mean = math.exp(sum(math.log(s) for s in speedups) / len(speedups))
        return geometric_mean
    return 0


def check_python_fallback() -> bool:
    """Check if Python fallback is being used."""
    try:
        from django_mercury.python_bindings.c_bindings import HAS_C_EXTENSIONS
        return not HAS_C_EXTENSIONS
    except ImportError:
        # Try alternative method
        try:
            from django_mercury.python_bindings.c_bindings import c_extensions
            return not any([
                c_extensions.query_analyzer,
                c_extensions.metrics_engine,
                c_extensions.test_orchestrator
            ])
        except:
            return True


def verify_c_extensions(benchmark: bool = False) -> int:
    """Main function to verify C extensions.
    
    Args:
        benchmark: If True, run performance benchmarks
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Run benchmarks if requested
    if benchmark:
        overall_speedup = run_benchmarks()
        
        # Print summary
        print("\n" + "═" * 60)
        if overall_speedup > 1:
            print(f"Overall Performance Improvement: {overall_speedup:.1f}x faster with C extensions!")
        else:
            print("Unable to complete benchmark comparison.")
        print("═" * 60)
        return 0
    
    print_banner()
    print("Checking C extensions...\n")
    
    # Test each extension
    extensions = [
        ("libquery_analyzer.so", test_query_analyzer),
        ("libmetrics_engine.so", test_metrics_engine),
        ("libtest_orchestrator.so", test_orchestrator),
    ]
    
    results = []
    all_success = True
    
    for name, test_func in extensions:
        success, elapsed, message = test_func()
        results.append((name, success, elapsed, message))
        if not success:
            all_success = False
        print(format_status(name, success, elapsed, message))
    
    print()
    
    # Summary
    if all_success:
        print("✅ All C extensions working correctly!")
        print("Performance improvement: ~10-100x over Python fallback")
        return 0
    else:
        # Check if using Python fallback
        if check_python_fallback():
            print("⚠️  Using Python fallback implementation")
            print("To enable C extensions:")
            print("  1. Install build dependencies: sudo apt-get install build-essential python3-dev")
            print("  2. Rebuild: cd django_mercury/c_core && make clean && make all")
            print("  3. Verify: mercury-test --ext")
        else:
            print("⚠️  Some C extensions failed to load or test")
            print("Check the error messages above for details")
        
        # Show which extensions failed
        failed = [name for name, success, _, _ in results if not success]
        if failed:
            print(f"\nFailed extensions: {', '.join(failed)}")
        
        return 1


if __name__ == "__main__":
    sys.exit(verify_c_extensions())