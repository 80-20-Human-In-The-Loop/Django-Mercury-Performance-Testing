#!/usr/bin/env python
"""
Performance comparison between C extensions and pure Python implementation.
"""

import time
import os
import sys

def benchmark_implementation(use_c_extension=True):
    """Benchmark the implementation."""
    
    # Force implementation type
    if not use_c_extension:
        os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '1'
    else:
        os.environ.pop('DJANGO_MERCURY_PURE_PYTHON', None)
    
    # Reload modules to pick up environment change
    if 'django_mercury.python_bindings.loader' in sys.modules:
        del sys.modules['django_mercury.python_bindings.loader']
    
    from django_mercury.python_bindings.loader import (
        get_performance_monitor,
        get_metrics_engine,
        get_query_analyzer,
        get_implementation_info
    )
    
    info = get_implementation_info()
    impl_type = info['type']
    
    print(f"\n{'='*60}")
    print(f"Testing: {impl_type}")
    print(f"{'='*60}")
    
    # Benchmark PerformanceMonitor
    Monitor = get_performance_monitor()
    start = time.perf_counter()
    
    for i in range(10000):
        monitor = Monitor()
        monitor.start_monitoring()
        monitor.track_query(f"SELECT * FROM table_{i}", 0.001 * i)
        monitor.stop_monitoring()
        metrics = monitor.get_metrics()
    
    perf_time = time.perf_counter() - start
    print(f"PerformanceMonitor (10,000 iterations): {perf_time:.3f}s")
    print(f"  Implementation: {metrics.get('implementation', 'unknown')}")
    
    # Benchmark MetricsEngine
    Engine = get_metrics_engine()
    engine = Engine()
    start = time.perf_counter()
    
    for i in range(5000):
        engine.add_metrics({
            'response_time_ms': 10.0 + i * 0.1,
            'query_count': i % 10
        })
    
    stats = engine.calculate_statistics()
    metrics_time = time.perf_counter() - start
    print(f"\nMetricsEngine (5,000 additions + statistics): {metrics_time:.3f}s")
    print(f"  Implementation: {stats.get('implementation', 'unknown')}")
    print(f"  Mean response time: {stats.get('mean', 0):.2f}ms")
    
    # Benchmark QueryAnalyzer
    Analyzer = get_query_analyzer()
    analyzer = Analyzer()
    
    queries = [
        "SELECT * FROM users WHERE id = 1",
        "SELECT u.*, p.* FROM users u LEFT JOIN profiles p ON u.id = p.user_id",
        "UPDATE users SET last_login = NOW() WHERE id = 1",
        "DELETE FROM sessions WHERE expired < NOW()",
        "SELECT COUNT(*) FROM orders WHERE status = 'pending' AND created > DATE_SUB(NOW(), INTERVAL 1 DAY)",
    ]
    
    start = time.perf_counter()
    
    for i in range(2000):
        for query in queries:
            analysis = analyzer.analyze_query(query)
    
    analyzer_time = time.perf_counter() - start
    print(f"\nQueryAnalyzer (10,000 query analyses): {analyzer_time:.3f}s")
    print(f"  Implementation: {analysis.get('implementation', 'unknown')}")
    
    total_time = perf_time + metrics_time + analyzer_time
    
    return {
        'implementation': impl_type,
        'performance_monitor': perf_time,
        'metrics_engine': metrics_time,
        'query_analyzer': analyzer_time,
        'total': total_time
    }

def main():
    """Run performance comparison."""
    
    print("Django Mercury Performance Testing - Implementation Comparison")
    print("=" * 60)
    
    # Test C extensions
    c_results = benchmark_implementation(use_c_extension=True)
    
    # Test pure Python
    python_results = benchmark_implementation(use_c_extension=False)
    
    # Print comparison
    print(f"\n{'='*60}")
    print("PERFORMANCE COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    print(f"\nC Extensions Total Time: {c_results['total']:.3f}s")
    print(f"Pure Python Total Time:  {python_results['total']:.3f}s")
    
    speedup = python_results['total'] / c_results['total']
    print(f"\nC Extensions are {speedup:.2f}x faster overall!")
    
    print("\nDetailed Speedup by Component:")
    for component in ['performance_monitor', 'metrics_engine', 'query_analyzer']:
        c_time = c_results[component]
        py_time = python_results[component]
        component_speedup = py_time / c_time if c_time > 0 else 1.0
        print(f"  {component.replace('_', ' ').title()}: {component_speedup:.2f}x faster")

if __name__ == '__main__':
    main()