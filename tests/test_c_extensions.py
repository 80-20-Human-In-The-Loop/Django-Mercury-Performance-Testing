"""
Tests for C extension loading and fallback mechanisms.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock


def test_loader_imports():
    """Test that the loader module can be imported."""
    from django_mercury.python_bindings import loader
    assert loader is not None


def test_pure_python_imports():
    """Test that pure Python implementations can be imported."""
    from django_mercury.python_bindings import pure_python
    assert pure_python is not None
    
    # Check all classes are available
    assert hasattr(pure_python, 'PythonPerformanceMonitor')
    assert hasattr(pure_python, 'PythonMetricsEngine')
    assert hasattr(pure_python, 'PythonQueryAnalyzer')
    assert hasattr(pure_python, 'PythonTestOrchestrator')


def test_get_implementation_info():
    """Test getting implementation information."""
    from django_mercury.python_bindings.loader import get_implementation_info
    
    info = get_implementation_info()
    assert isinstance(info, dict)
    assert 'type' in info
    assert 'c_extensions_available' in info
    assert 'platform' in info
    assert 'python_version' in info


def test_performance_monitor_creation():
    """Test that we can create a PerformanceMonitor instance."""
    from django_mercury.python_bindings.loader import get_performance_monitor
    
    MonitorClass = get_performance_monitor()
    assert MonitorClass is not None
    
    # Create instance
    monitor = MonitorClass()
    assert monitor is not None
    
    # Check basic interface
    assert hasattr(monitor, 'start_monitoring')
    assert hasattr(monitor, 'stop_monitoring')
    assert hasattr(monitor, 'get_metrics')


def test_performance_monitor_basic_usage():
    """Test basic performance monitoring functionality."""
    from django_mercury.python_bindings.loader import get_performance_monitor
    import time
    
    MonitorClass = get_performance_monitor()
    monitor = MonitorClass()
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Simulate some work
    time.sleep(0.01)  # 10ms
    
    # Stop monitoring
    monitor.stop_monitoring()
    
    # Get metrics
    metrics = monitor.get_metrics()
    assert isinstance(metrics, dict)
    assert 'response_time_ms' in metrics
    assert metrics['response_time_ms'] > 0  # Should have measured some time


def test_force_pure_python():
    """Test forcing pure Python implementation."""
    # Set environment variable
    os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '1'
    
    try:
        # Reload the loader module
        from django_mercury.python_bindings import loader
        import importlib
        importlib.reload(loader)
        
        info = loader.get_implementation_info()
        assert info['forced_pure_python'] == True
        assert info['type'] == 'pure_python_forced'
        
    finally:
        # Clean up
        del os.environ['DJANGO_MERCURY_PURE_PYTHON']


def test_c_extension_fallback():
    """Test fallback when C extensions are not available."""
    with patch('django_mercury.python_bindings.loader._try_import_c_extensions') as mock_import:
        # Simulate C extension import failure
        mock_import.return_value = (False, "Import failed")
        
        # Reload the loader
        from django_mercury.python_bindings import loader
        import importlib
        importlib.reload(loader)
        
        # Should fall back to pure Python
        info = loader.get_implementation_info()
        assert info['c_extensions_available'] == False
        assert 'pure_python' in info['type']


def test_all_implementations_available():
    """Test that all implementation classes are available."""
    from django_mercury.python_bindings.loader import (
        get_performance_monitor,
        get_metrics_engine,
        get_query_analyzer,
        get_test_orchestrator,
    )
    
    # Get all classes
    monitor_class = get_performance_monitor()
    engine_class = get_metrics_engine()
    analyzer_class = get_query_analyzer()
    orchestrator_class = get_test_orchestrator()
    
    # Check they're not None
    assert monitor_class is not None
    assert engine_class is not None
    assert analyzer_class is not None
    assert orchestrator_class is not None
    
    # Create instances
    monitor = monitor_class()
    engine = engine_class()
    analyzer = analyzer_class()
    orchestrator = orchestrator_class()
    
    # Check instances
    assert monitor is not None
    assert engine is not None
    assert analyzer is not None
    assert orchestrator is not None


def test_metrics_engine_functionality():
    """Test MetricsEngine basic functionality."""
    from django_mercury.python_bindings.loader import get_metrics_engine
    
    EngineClass = get_metrics_engine()
    engine = EngineClass()
    
    # Add some metrics
    engine.add_metrics({'response_time_ms': 100, 'query_count': 5})
    engine.add_metrics({'response_time_ms': 150, 'query_count': 8})
    
    # Calculate statistics
    stats = engine.calculate_statistics()
    assert isinstance(stats, dict)
    assert 'response_time_stats' in stats
    assert 'query_count_stats' in stats


def test_query_analyzer_functionality():
    """Test QueryAnalyzer basic functionality."""
    from django_mercury.python_bindings.loader import get_query_analyzer
    
    AnalyzerClass = get_query_analyzer()
    analyzer = AnalyzerClass()
    
    # Analyze a simple query
    sql = "SELECT * FROM users WHERE id = 1"
    analysis = analyzer.analyze_query(sql)
    
    assert isinstance(analysis, dict)
    assert 'type' in analysis
    assert analysis['type'] == 'SELECT'


def test_test_orchestrator_functionality():
    """Test TestOrchestrator basic functionality."""
    from django_mercury.python_bindings.loader import get_test_orchestrator
    
    OrchestratorClass = get_test_orchestrator()
    orchestrator = OrchestratorClass()
    
    # Start a test
    orchestrator.start_test('test_example')
    
    # End the test
    result = orchestrator.end_test('test_example', 'passed')
    
    assert isinstance(result, dict)
    assert result.get('name') == 'test_example'
    assert result.get('status') == 'passed'
    
    # Get summary
    summary = orchestrator.get_summary()
    assert isinstance(summary, dict)
    assert summary['total_tests'] == 1
    assert summary['passed'] == 1


@pytest.mark.benchmark
def test_performance_comparison():
    """Compare performance of implementations if both are available."""
    from django_mercury.python_bindings.loader import get_implementation_info
    
    info = get_implementation_info()
    
    if info['c_extensions_available']:
        # Test C implementation speed
        from django_mercury.python_bindings.loader import get_performance_monitor
        import time
        
        MonitorClass = get_performance_monitor()
        monitor = MonitorClass()
        
        start = time.perf_counter()
        for _ in range(1000):
            monitor.start_monitoring()
            monitor.stop_monitoring()
        c_time = time.perf_counter() - start
        
        # Force pure Python and test
        os.environ['DJANGO_MERCURY_PURE_PYTHON'] = '1'
        from django_mercury.python_bindings import pure_python
        
        monitor = pure_python.PythonPerformanceMonitor()
        
        start = time.perf_counter()
        for _ in range(1000):
            monitor.start_monitoring()
            monitor.stop_monitoring()
        python_time = time.perf_counter() - start
        
        del os.environ['DJANGO_MERCURY_PURE_PYTHON']
        
        print(f"C implementation: {c_time:.4f}s")
        print(f"Python implementation: {python_time:.4f}s")
        print(f"C is {python_time/c_time:.1f}x faster")
        
        # C should be faster (but might not be in all cases)
        # This is informational, not a hard assertion
    else:
        pytest.skip("C extensions not available for comparison")


def test_check_c_extensions():
    """Test the check_c_extensions utility function."""
    from django_mercury.python_bindings.loader import check_c_extensions
    
    available, details = check_c_extensions()
    
    assert isinstance(available, bool)
    assert isinstance(details, dict)
    assert 'type' in details
    assert 'platform' in details
    
    if available:
        assert details.get('functional') is not None