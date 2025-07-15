#!/bin/bash

# PostgreSQL Docker test execution script
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🐳 Starting PostgreSQL test containers..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Start test containers
echo "📦 Starting containers..."
docker-compose -f docker/docker-compose.test.yml up -d

# Wait for containers to be healthy
echo "⏳ Waiting for databases to be ready..."
for port in 5433 5434 5435 5436; do
    echo "Waiting for PostgreSQL on port $port..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker exec pgsd_test_pg$(( port - 5432 + 12 )) pg_isready -U test_user -d pgsd_test &> /dev/null; then
            echo "✅ PostgreSQL on port $port is ready"
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -eq 0 ]; then
        echo "❌ Timeout waiting for PostgreSQL on port $port"
        docker-compose -f docker/docker-compose.test.yml logs
        exit 1
    fi
done

# Run database tests
echo "🧪 Running database integration tests..."
export PYTHONPATH="$PROJECT_ROOT/src"
export SKIP_DB_TESTS=false

# Test specific components
echo "📋 Testing database connections..."
python -m pytest tests/integration/test_database_integration.py::TestDatabaseConnection -v

echo "📊 Testing schema operations..."
python -m pytest tests/integration/test_database_integration.py::TestBasicSchemaOperations -v

echo "⚡ Testing performance..."
python -m pytest tests/integration/test_database_integration.py::TestDatabasePerformance -v -m "not slow"

# Run CLI tests that require database
echo "🖥️  Testing CLI with database..."
python -m pytest tests/integration/test_cli_comprehensive.py::TestListSchemasCommand -v

# Full integration tests
echo "🚀 Running full integration tests..."
python -m pytest tests/integration/ -v -m "integration and db" --maxfail=5

echo "✅ All database tests completed successfully!"

# Optional: Stop containers (uncomment if you want to stop after tests)
# echo "🛑 Stopping test containers..."
# docker-compose -f docker/docker-compose.test.yml down

echo "ℹ️  To stop test containers manually, run:"
echo "   docker-compose -f docker/docker-compose.test.yml down"