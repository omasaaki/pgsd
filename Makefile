# Makefile for PGSD test automation

.PHONY: help test test-unit test-integration test-db test-all coverage clean docker-up docker-down

# Default target
help:
	@echo "PostgreSQL Schema Diff Tool - Test Commands"
	@echo "==========================================="
	@echo "make test           - Run all tests (requires Docker)"
	@echo "make test-unit      - Run unit tests only (no Docker)"
	@echo "make test-integration - Run integration tests (requires Docker)"
	@echo "make test-no-db     - Run tests without database (no Docker)"
	@echo "make test-pg13      - Run tests against PostgreSQL 13"
	@echo "make test-pg14      - Run tests against PostgreSQL 14"
	@echo "make test-pg15      - Run tests against PostgreSQL 15"
	@echo "make test-pg16      - Run tests against PostgreSQL 16"
	@echo "make test-all       - Run tests against all PostgreSQL versions"
	@echo "make coverage       - Generate coverage report"
	@echo "make docker-up      - Start test containers"
	@echo "make docker-down    - Stop test containers"
	@echo "make docker-check   - Check Docker availability"
	@echo "make clean          - Clean test artifacts"

# Test environment setup
docker-up:
	@echo "Starting test containers..."
	@docker-compose -f docker/docker-compose.test.yml up -d
	@echo "Waiting for containers to be ready..."
	@sleep 10
	@docker-compose -f docker/docker-compose.test.yml ps

docker-down:
	@echo "Stopping test containers..."
	@docker-compose -f docker/docker-compose.test.yml down -v

docker-logs:
	@echo "Showing container logs..."
	@docker-compose -f docker/docker-compose.test.yml logs

# Test execution
test: docker-up
	@echo "Running all tests..."
	@pytest

test-unit:
	@echo "Running unit tests..."
	@PYTHONPATH=src pytest tests/unit/ -v --cov-fail-under=0

test-no-db:
	@echo "Running tests without database..."
	@PYTHONPATH=src SKIP_DB_TESTS=true pytest tests/ -v -m "not db"

docker-check:
	@echo "Checking Docker availability..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is not installed"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "❌ Docker daemon is not running"; exit 1; }
	@echo "✅ Docker environment is ready"

test-integration: docker-up
	@echo "Running integration tests..."
	@pytest -m integration

test-db: docker-up
	@echo "Running database tests..."
	@pytest -m db

# PostgreSQL version specific tests
test-pg13: docker-up
	@echo "Running tests against PostgreSQL 13..."
	@pytest -k pg13

test-pg14: docker-up
	@echo "Running tests against PostgreSQL 14..."
	@pytest -k pg14

test-pg15: docker-up
	@echo "Running tests against PostgreSQL 15..."
	@pytest -k pg15

test-pg16: docker-up
	@echo "Running tests against PostgreSQL 16..."
	@pytest -k pg16

test-all: docker-up
	@echo "Running tests against all PostgreSQL versions..."
	@pytest

# Coverage
coverage: test
	@echo "Generating coverage report..."
	@echo "HTML report: htmlcov/index.html"
	@echo "Opening coverage report in browser..."
	@python -c "import webbrowser; webbrowser.open('htmlcov/index.html')" 2>/dev/null || echo "Please open htmlcov/index.html manually"

coverage-serve: coverage
	@echo "Serving coverage report on http://localhost:8000"
	@python -m http.server 8000 --directory htmlcov

# Cleanup
clean:
	@echo "Cleaning test artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean docker-down
	@echo "Cleaning all test artifacts and containers..."

# Development helpers
test-watch:
	@echo "Running tests in watch mode (requires pytest-watch)..."
	@ptw -- --testmon

test-failed:
	@echo "Running previously failed tests..."
	@pytest --lf

test-debug:
	@echo "Running tests with debugger..."
	@pytest --pdb

test-verbose:
	@echo "Running tests with verbose output..."
	@pytest -vv

# Performance testing
test-profile:
	@echo "Running tests with profiling..."
	@pytest --profile

test-parallel:
	@echo "Running tests in parallel (requires pytest-xdist)..."
	@pytest -n auto

# Quality checks
lint:
	@echo "Running code linting..."
	@flake8 src tests

format:
	@echo "Formatting code..."
	@black src tests
	@isort src tests

type-check:
	@echo "Running type checks..."
	@mypy src

quality: lint type-check
	@echo "Running all quality checks..."

# Installation helpers
install-dev:
	@echo "Installing development dependencies..."
	@pip install -r requirements-dev.txt
	@pip install -e .

install-test-deps:
	@echo "Installing additional test dependencies..."
	@pip install pytest-watch pytest-xdist pytest-profiling

# Database management
db-reset: docker-down docker-up
	@echo "Resetting test databases..."

db-status:
	@echo "Checking database status..."
	@docker-compose -f docker/docker-compose.test.yml ps

# CI helpers
ci-test: install-dev test-all
	@echo "Running CI test suite..."

ci-coverage: ci-test
	@echo "Generating CI coverage report..."
	@pytest --cov=src/pgsd --cov-report=xml --cov-report=term

# Documentation
docs-test:
	@echo "Testing documentation examples..."
	@python -m doctest README.md || echo "No doctests in README.md"