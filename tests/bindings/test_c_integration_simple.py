#!/usr/bin/env python3
"""
Simple integration test for C libraries without Django dependencies.
"""

import ctypes
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_libperformance():
    """Test libperformance.so functionality."""
    print("Testing libperformance.so...")
    
    # Load library
    lib_path = Path(__file__).parent.parent.parent / "django_mercury" / "c_core" / "libperformance.so"
    lib = ctypes.CDLL(str(lib_path))
    
    # Define structure
    class EnhancedPerformanceMetrics(ctypes.Structure):
        _fields_ = [
            ("start_time_ns", ctypes.c_uint64),
            ("end_time_ns", ctypes.c_uint64),
            ("memory_start_bytes", ctypes.c_size_t),
            ("memory_peak_bytes", ctypes.c_size_t),
            ("memory_end_bytes", ctypes.c_size_t),
            ("query_count_start", ctypes.c_uint32),
            ("query_count_end", ctypes.c_uint32),
            ("cache_hits", ctypes.c_uint32),
            ("cache_misses", ctypes.c_uint32),
            ("operation_name", ctypes.c_char * 256),
            ("operation_type", ctypes.c_char * 64)
        ]
    
    # Configure functions
    lib.start_performance_monitoring_enhanced.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    lib.start_performance_monitoring_enhanced.restype = ctypes.c_int64
    
    lib.stop_performance_monitoring_enhanced.argtypes = [ctypes.c_int64]
    lib.stop_performance_monitoring_enhanced.restype = ctypes.POINTER(EnhancedPerformanceMetrics)
    
    lib.free_metrics.argtypes = [ctypes.POINTER(EnhancedPerformanceMetrics)]
    lib.free_metrics.restype = None
    
    lib.get_memory_delta_mb.argtypes = [ctypes.POINTER(EnhancedPerformanceMetrics)]
    lib.get_memory_delta_mb.restype = ctypes.c_double
    
    # Test 1: Basic monitoring
    print("  ✓ Library loaded successfully")
    
    handle = lib.start_performance_monitoring_enhanced(b"test_operation", b"test")
    assert handle > 0, f"Failed to start monitoring, handle={handle}"
    print("  ✓ Started monitoring")
    
    # Simulate some work
    time.sleep(0.01)
    
    metrics_ptr = lib.stop_performance_monitoring_enhanced(handle)
    assert metrics_ptr, "Failed to get metrics"
    print("  ✓ Stopped monitoring")
    
    # Check metrics
    metrics = metrics_ptr.contents
    assert metrics.operation_name.decode() == "test_operation"
    assert metrics.operation_type.decode() == "test"
    assert metrics.end_time_ns > metrics.start_time_ns
    print("  ✓ Metrics contain correct data")
    
    # Test memory delta function
    memory_delta = lib.get_memory_delta_mb(metrics_ptr)
    print(f"  ✓ Memory delta: {memory_delta:.2f} MB")
    
    # Free memory
    lib.free_metrics(metrics_ptr)
    print("  ✓ Memory freed successfully")
    
    # Test 2: Multiple concurrent monitors
    print("\nTesting concurrent monitors...")
    handles = []
    for i in range(5):
        h = lib.start_performance_monitoring_enhanced(f"op_{i}".encode(), b"concurrent")
        assert h > 0
        handles.append(h)
    
    for i, h in enumerate(handles):
        m = lib.stop_performance_monitoring_enhanced(h)
        assert m
        assert m.contents.operation_name.decode() == f"op_{i}"
        lib.free_metrics(m)
    
    print("  ✓ Concurrent monitors work correctly")
    
    # Test 3: Error handling
    print("\nTesting error handling...")
    
    # Invalid handle
    result = lib.stop_performance_monitoring_enhanced(99999)
    assert not result
    print("  ✓ Invalid handle returns NULL")
    
    # NULL operation name
    handle = lib.start_performance_monitoring_enhanced(None, b"test")
    assert handle == -1
    print("  ✓ NULL operation name returns -1")
    
    print("\n[PASS] All tests passed!")


def test_all_libraries():
    """Test that all C libraries can be loaded."""
    print("\nTesting all C libraries...")
    
    c_core = Path(__file__).parent.parent.parent / "django_mercury" / "c_core"
    libraries = [
        "libquery_analyzer.so",
        "libmetrics_engine.so", 
        "libtest_orchestrator.so",
        "libperformance.so"
    ]
    
    for lib_name in libraries:
        lib_path = c_core / lib_name
        try:
            lib = ctypes.CDLL(str(lib_path))
            print(f"  ✓ {lib_name} loaded successfully")
        except Exception as e:
            print(f"  ✗ {lib_name} failed to load: {e}")
            return False
    
    return True


def test_python_integration():
    """Test Python integration without Django."""
    print("\nTesting Python integration...")
    
    try:
        from django_mercury.python_bindings.monitor import PerformanceMonitor
        
        with PerformanceMonitor("python_test") as monitor:
            time.sleep(0.01)
        
        # The EnhancedPerformanceMonitor uses different attribute names
        assert hasattr(monitor, 'metrics') or hasattr(monitor, 'elapsed_time_ms')
        assert hasattr(monitor, 'operation_name')
        print("  ✓ PerformanceMonitor works correctly")
        
    except Exception as e:
        print(f"  ✗ Python integration failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("C Library Integration Tests")
    print("=" * 60)
    
    success = True
    
    try:
        test_libperformance()
    except Exception as e:
        print(f"\n❌ libperformance test failed: {e}")
        success = False
    
    if not test_all_libraries():
        success = False
    
    if not test_python_integration():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("[PASS] ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)