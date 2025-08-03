# Makefile for Django Mercury Performance Testing

.PHONY: help clean test coverage lint format install build docs

help:
	@echo "Django Mercury Performance Testing - Development Commands"
	@echo ""
	@echo "  make install    Install package in development mode"
	@echo "  make test       Run all tests"
	@echo "  make coverage   Run tests with coverage report"
	@echo "  make lint       Check code style"
	@echo "  make format     Auto-format code"
	@echo "  make build      Build wheels and source distribution"
	@echo "  make clean      Remove build artifacts"
	@echo "  make docs       Build documentation"
	@echo "  make c-test     Test C extensions specifically"
	@echo "  make perf       Run performance comparison"

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=django_mercury --cov-report=term-missing --cov-report=html

lint:
	ruff check django_mercury/
	black --check django_mercury/
	isort --check-only django_mercury/

format:
	ruff check --fix django_mercury/
	black django_mercury/
	isort django_mercury/

build:
	python setup.py build_ext --inplace
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .tox/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.so" -delete
	find . -type f -name "*.o" -delete

docs:
	@echo "Documentation building would go here"

c-test:
	python setup.py build_ext --inplace
	python test_performance_comparison.py
	python -c "from django_mercury.python_bindings.loader import check_c_extensions; available, details = check_c_extensions(); print(f'C Extensions Available: {available}'); print(f'Details: {details}')"

perf:
	python test_performance_comparison.py

# Development shortcuts
.PHONY: dev test-quick

dev: install
	@echo "Development environment ready!"

test-quick:
	pytest tests/test_c_extensions.py -v -x