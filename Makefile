# Makefile for VPNHD development tasks

.PHONY: help install install-dev test test-quick test-coverage lint format clean build docs pre-commit

# Default target
help:
	@echo "VPNHD Development Commands:"
	@echo ""
	@echo "  make install        - Install package in editable mode"
	@echo "  make install-dev    - Install package with development dependencies"
	@echo "  make test           - Run full test suite with coverage"
	@echo "  make test-quick     - Run tests without coverage (fast)"
	@echo "  make test-coverage  - Run tests and open coverage report"
	@echo "  make lint           - Run all linters (black, flake8, isort, mypy)"
	@echo "  make format         - Format code with black and isort"
	@echo "  make clean          - Remove build artifacts and caches"
	@echo "  make build          - Build distribution packages"
	@echo "  make pre-commit     - Install and run pre-commit hooks"
	@echo "  make security       - Run security scans (bandit, safety)"
	@echo ""

# Install package
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -e ".[dev]"
	pip install pytest pytest-cov pytest-mock
	pip install black flake8 isort mypy
	pip install bandit safety
	pip install pre-commit

# Run full test suite
test:
	pytest --cov=src/vpnhd --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Quick test run without coverage
test-quick:
	pytest -x --no-cov

# Run tests and open coverage report
test-coverage: test
	@echo "Opening coverage report..."
	@command -v xdg-open >/dev/null 2>&1 && xdg-open htmlcov/index.html || \
	command -v open >/dev/null 2>&1 && open htmlcov/index.html || \
	echo "Coverage report generated in htmlcov/index.html"

# Run linters
lint:
	@echo "Running Black..."
	black --check src/ tests/
	@echo "Running isort..."
	isort --check-only src/ tests/
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running mypy..."
	mypy src/vpnhd --ignore-missing-imports || true

# Format code
format:
	@echo "Formatting with Black..."
	black src/ tests/
	@echo "Sorting imports with isort..."
	isort src/ tests/

# Run security scans
security:
	@echo "Running Bandit security scan..."
	bandit -r src/vpnhd -ll
	@echo "Running Safety dependency check..."
	safety check || true

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete

# Build distribution
build: clean
	@echo "Building distribution packages..."
	python -m build
	twine check dist/*

# Install and run pre-commit
pre-commit:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

# Update dependencies
update-deps:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

# Check for outdated dependencies
check-deps:
	pip list --outdated
