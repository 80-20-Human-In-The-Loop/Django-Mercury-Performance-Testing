# Makefile for consolidation tests
# Tests for verifying library functionality and compatibility

CC = gcc
CFLAGS = -Wall -Wextra -g -I../.. -I..
LDFLAGS = -ldl -lpthread -lm

# Test executables
TESTS = test_feature_parity test_api_compatibility

# Main target
all: $(TESTS)

# Build rules for each test
test_feature_parity: test_feature_parity.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

test_api_compatibility: test_api_compatibility.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# Migration safety test removed - migration complete

# Run all tests
test: $(TESTS)
	@echo "=== Running Consolidation Tests ==="
	@echo ""
	@echo "1. Testing Feature Parity..."
	@./test_feature_parity || (echo "❌ Feature parity test failed"; exit 1)
	@echo ""
	@echo "2. Testing API Compatibility..."
	@./test_api_compatibility || (echo "❌ API compatibility test failed"; exit 1)
	@echo ""
	@echo "=== All Consolidation Tests Passed ✅ ==="

# Clean up
clean:
	rm -f $(TESTS)
	rm -f *.o

.PHONY: all test clean