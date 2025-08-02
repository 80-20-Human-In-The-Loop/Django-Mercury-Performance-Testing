# C Core Coverage System

The coverage system for the Mercury C Core has been completely revamped to provide a clean, organized way to analyze code coverage.

## Quick Start

```bash
# From the c_core directory:
make coverage
```

This will:
1. Clean any previous coverage data
2. Build tests with coverage instrumentation
3. Run all tests
4. Generate coverage reports in `tests/coverage/`
5. Display a summary showing **68.70% overall coverage**

## Features

### ✅ Organized Coverage Files
All coverage artifacts (.gcda, .gcno, .gcov) are now stored in `tests/coverage/` instead of cluttering the main directory.

### ✅ Easy-to-Read Summary
```
📊 Coverage Summary:
===================
File 'common.c'
Lines executed:53.51% of 441
File 'query_analyzer.c'
Lines executed:68.52% of 324
...
Lines executed:68.70% of 1051
```

### ✅ Multiple Ways to View Coverage

1. **Make target**: `make coverage` - Quick summary in terminal
2. **Shell script**: `./tests/coverage.sh` - Detailed analysis with colors
3. **Python tool**: `./tests/coverage_summary.py` - Advanced analysis
4. **Direct access**: `cat tests/coverage/*.gcov` - Line-by-line details

### ✅ Clean Management
- `make clean-coverage` - Remove all coverage files
- `make clean` - Also removes coverage files
- All coverage files are gitignored

## Directory Structure

```
tests/
├── coverage/                  # All coverage files go here
│   ├── *.gcda                # Coverage data files
│   ├── *.gcno                # Coverage notes files  
│   ├── *.gcov                # Human-readable coverage reports
│   ├── coverage_summary.txt  # gcov output
│   └── test_*.log            # Test execution logs
├── coverage.sh               # Shell script for detailed analysis
├── coverage_summary.py       # Python tool for advanced analysis
└── simple_test_*.c          # Test source files
```

## Coverage Goals

Current coverage: **68.70%**

Target areas for improvement:
- `common.c`: 53.51% → 80%+
- `query_analyzer.c`: 68.52% → 80%+
- Test files: Already at 96-100%

## Tips

- Run `make coverage` after making changes to ensure coverage doesn't drop
- Check `tests/coverage/*.gcov` files to see which lines aren't covered
- Use the shell script for a quick visual overview with color coding
- Coverage files are automatically cleaned before each run