# Building Mercury C Core

## Quick Build
```bash
cd backend/performance_testing/c_core
make clean && make
```

## What Gets Built
- `libquery_analyzer.so` - SQL query analysis
- `libmetrics_engine.so` - Performance metrics
- `libtest_orchestrator.so` - Test orchestration
- `libperformance.so` - Main performance monitoring (legacy)

## Requirements
- GCC or Clang
- Python dev headers (`python3-dev` on Ubuntu/Debian)
- Standard C library

## Platform Support
- Linux (x86_64, ARM64)
- macOS (Intel, Apple Silicon)
- Auto-detects architecture for optimizations

## Verify Build
```bash
# Check libraries exist
ls -la *.so

# Run tests
make test
```

## Clean Build
```bash
make clean
make
```

Binary files (.so) are gitignored and must be built locally.