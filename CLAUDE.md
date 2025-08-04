# Architecture Overview

Django Mercury combines fast C extensions with flexible Python code. This framework tests Django application performance and teaches optimization techniques.

## Design Philosophy

Django Mercury follows the **80/20 Human-in-the-Loop** principle:
- **80% Computer Help**: Automated detection, monitoring, and analysis
- **20% Human Control**: Understanding, decision-making, and optimization

## Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Mercury Framework                  │
├─────────────────────────────────────────────────────────────┤
│  Python API Layer                                           │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐│
│  │ DjangoMercuryAPI    │  │ DjangoPerformanceAPI            ││
│  │ TestCase            │  │ TestCase                        ││
│  │ (Automatic)         │  │ (Manual Control)                ││
│  └─────────────────────┘  └─────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  Performance Monitoring Core                                │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐│
│  │ Pure Python         │  │ C Extensions                    ││
│  │ Implementation      │  │ (High Performance)              ││
│  │ (Fallback)          │  │                                 ││
│  └─────────────────────┘  └─────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  Detection & Analysis Engines                               │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────┐  │
│  │ N+1 Query     │ │ Memory        │ │ Response Time     │  │
│  │ Detection     │ │ Profiler      │ │ Analyzer          │  │
│  └───────────────┘ └───────────────┘ └───────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Django Integration Layer                                   │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────┐  │
│  │ ORM Hook      │ │ Middleware    │ │ Test Integration  │  │
│  │ System        │ │ Integration   │ │ Framework         │  │
│  └───────────────┘ └───────────────┘ └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### **Python API Layer**
- **DjangoMercuryAPITestCase**: Automatic monitoring with intelligent defaults
- **DjangoPerformanceAPITestCase**: Manual control for expert users
- **Monitor Context Managers**: Fine-grained performance tracking

### **Performance Monitoring Core**
- **Dual Implementation**: C extensions for speed, Python fallback for compatibility
- **Thread-Safe**: Handles concurrent test execution
- **Memory Efficient**: Minimal overhead during testing

### **C Extensions**
- **libperformance.so**: Monitors performance in real time
- **libmetrics_engine.so**: Calculates and combines metrics  
- **libquery_analyzer.so**: Analyzes SQL queries and finds N+1 problems
- **libtest_orchestrator.so**: Coordinates tests and measures timing

### **Detection Engines**
- **N+1 Query Detection**: Finds repeated database queries and rates severity
- **Memory Profiler**: Tracks memory use and finds memory leaks
- **Response Time Analyzer**: Measures response speed with statistical analysis
- **Cache Performance**: Measures how often cache is used successfully

## Data Flow

```
Test Execution → Django ORM Hooks → Performance Collection → 
Analysis Engines → Scoring System → Educational Reporting
```

1. **Test Execution**: Standard Django/DRF test runs
2. **Django ORM Hooks**: Intercept database queries and operations  
3. **Performance Collection**: Gather timing, memory, and query data
4. **Analysis Engines**: Process data through specialized analyzers
5. **Scoring System**: Generate letter grades (S, A+, A, B, C, D, F)
6. **Educational Reporting**: Provide actionable optimization guidance

## Configuration System

### **Mercury Config**
- **JSON-based configuration**: `mercury_config.json`
- **Environment variables**: Runtime overrides
- **Test-level settings**: Per-test customization
- **Adaptive thresholds**: Smart defaults based on operation type

### **Threshold Management**
```python
# Automatic threshold adaptation
cls.set_performance_thresholds({
    'response_time_ms': 100,    # Context-aware
    'query_count_max': 10,      # Operation-specific
    'memory_overhead_mb': 20,   # Intelligent defaults
})
```

## Integration Points

### **Django Framework**
- **Test Framework**: Extends Django's TestCase
- **ORM Integration**: Hooks into QuerySet execution
- **Middleware Compatible**: Works with existing Django middleware
- **Settings Integration**: Respects Django configuration

### **Django REST Framework**
- **APITestCase Extension**: Built on DRF's test framework
- **Serializer Monitoring**: Tracks serialization performance
- **View Performance**: Monitors API endpoint performance
- **Authentication Integration**: Works with DRF auth systems

## Performance Characteristics

### **Speed**
- **C Extensions**: Run 10-100 times faster than Python for critical operations
- **Low Overhead**: Adds less than 2% to test execution time
- **Efficient Loading**: Loads components only when you need them

### **Memory**
- **Low Memory Use**: Uses less than 50MB of memory typically
- **Automatic Cleanup**: Cleans up resources automatically
- **Self-Monitoring**: Monitors itself for memory leaks

### **Scalability**
- **Thread-Safe**: Works with tests running at the same time
- **Large Test Suites**: Handles over 1000 test methods efficiently
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Built for EduLite

Django Mercury was originally created for [EduLite](https://github.com/ibrahim-sisar/EduLite), an educational platform that needed to work well on slow internet connections:

- **Real-World Problem**: UserSearchView was making 825 database queries
- **Mercury Solution**: Detected the N+1 pattern and provided fix guidance
- **Result**: Reduced to 12 queries, dramatically improving performance

## Future Architecture

### **Planned Enhancements**
- **AI-Powered Analysis**: Use machine learning to suggest optimizations
- **Distributed Testing**: Test performance across multiple computers
- **Real-time Monitoring**: Monitor performance in production systems
- **Plugin System**: Allow third-party developers to add extensions

### **Community Integration**
- **Human-in-the-Loop Values**: Fair, Free, Open development approach
- **Educational Focus**: Teaches optimization techniques instead of only finding problems
- **Global Accessibility**: Works in environments with limited resources

---

*This architecture enables Django Mercury to be both powerful for experts and approachable for beginners, while maintaining the performance needed for large-scale applications.*