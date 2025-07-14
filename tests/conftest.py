"""
Pytest configuration and shared fixtures for PGSD tests.
"""
import os
import pytest
import psycopg2
from typing import Generator, Dict, Any, Optional
from pathlib import Path
import docker
from docker.models.containers import Container
import time
from pgsd.utils.logger import get_logger

logger = get_logger(__name__)

# Test configuration
TEST_DB_NAME = "pgsd_test"
TEST_DB_USER = "test_user" 
TEST_DB_PASSWORD = "test_pass"
TEST_SCHEMA_PREFIX = "test_schema"

@pytest.fixture(scope="session")
def docker_client():
    """Get Docker client."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

@pytest.fixture(scope="session")
def ensure_test_containers(docker_client):
    """Ensure test containers are running."""
    compose_file = Path(__file__).parent.parent / "docker" / "docker-compose.test.yml"
    
    # Check if containers are already running
    containers = docker_client.containers.list(filters={"label": "com.pgsd.test=true"})
    if not containers:
        logger.info("Starting test containers...")
        os.system(f"docker-compose -f {compose_file} up -d")
        time.sleep(5)  # Wait for containers to be ready
    
    yield
    
    # Cleanup handled by developer or CI

@pytest.fixture
def test_db_config(postgres_version) -> Dict[str, Any]:
    """Test database configuration for specific PostgreSQL version."""
    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": postgres_version["port"],
        "database": TEST_DB_NAME,
        "user": TEST_DB_USER,
        "password": TEST_DB_PASSWORD,
    }

@pytest.fixture(
    params=[
        {"port": 5433, "version": "13"},
        {"port": 5434, "version": "14"},
        {"port": 5435, "version": "15"},
        {"port": 5436, "version": "16"},
    ],
    ids=["pg13", "pg14", "pg15", "pg16"]
)
def postgres_version(request) -> Dict[str, Any]:
    """Parameterized fixture for multiple PostgreSQL versions."""
    return request.param

@pytest.fixture
def db_connection(test_db_config, ensure_test_containers):
    """Create database connection for tests."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**test_db_config)
            conn.autocommit = True
            yield conn
            conn.close()
            return
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)
            else:
                raise

@pytest.fixture
def clean_database(db_connection):
    """Ensure clean database state for each test."""
    cursor = db_connection.cursor()
    
    # Drop all test schemas
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE %s
    """, (f"{TEST_SCHEMA_PREFIX}%",))
    
    schemas = cursor.fetchall()
    for schema in schemas:
        cursor.execute(f"DROP SCHEMA {schema[0]} CASCADE")
    
    yield db_connection
    
    # Cleanup after test
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE %s
    """, (f"{TEST_SCHEMA_PREFIX}%",))
    
    schemas = cursor.fetchall()
    for schema in schemas:
        cursor.execute(f"DROP SCHEMA {schema[0]} CASCADE")

@pytest.fixture
def test_schemas_path() -> Path:
    """Path to test schema fixtures."""
    return Path(__file__).parent / "fixtures" / "schemas"

@pytest.fixture
def sample_schema_simple(clean_database) -> str:
    """Create simple test schema."""
    cursor = clean_database.cursor()
    schema_name = f"{TEST_SCHEMA_PREFIX}_simple"
    
    cursor.execute(f"CREATE SCHEMA {schema_name}")
    cursor.execute(f"""
        CREATE TABLE {schema_name}.users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE {schema_name}.posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES {schema_name}.users(id),
            title VARCHAR(200) NOT NULL,
            content TEXT,
            published_at TIMESTAMP
        )
    """)
    
    return schema_name

@pytest.fixture
def sample_schema_complex(clean_database) -> str:
    """Create complex test schema with various PostgreSQL features."""
    cursor = clean_database.cursor()
    schema_name = f"{TEST_SCHEMA_PREFIX}_complex"
    
    cursor.execute(f"CREATE SCHEMA {schema_name}")
    
    # Create custom types
    cursor.execute(f"""
        CREATE TYPE {schema_name}.status_type AS ENUM ('active', 'inactive', 'pending')
    """)
    
    # Create tables with complex features
    cursor.execute(f"""
        CREATE TABLE {schema_name}.categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            status {schema_name}.status_type DEFAULT 'active',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT unique_active_category UNIQUE (name) 
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE {schema_name}.products (
            id SERIAL PRIMARY KEY,
            category_id INTEGER REFERENCES {schema_name}.categories(id),
            name VARCHAR(200) NOT NULL,
            price DECIMAL(10,2) CHECK (price > 0),
            metadata JSONB,
            search_vector TSVECTOR,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Create indexes
    cursor.execute(f"""
        CREATE INDEX idx_products_category ON {schema_name}.products(category_id)
    """)
    cursor.execute(f"""
        CREATE INDEX idx_products_search ON {schema_name}.products USING gin(search_vector)
    """)
    cursor.execute(f"""
        CREATE INDEX idx_products_metadata ON {schema_name}.products USING gin(metadata)
    """)
    
    # Create view
    cursor.execute(f"""
        CREATE VIEW {schema_name}.active_products AS
        SELECT p.*, c.name as category_name
        FROM {schema_name}.products p
        JOIN {schema_name}.categories c ON p.category_id = c.id
        WHERE c.status = 'active'
    """)
    
    return schema_name

# Test markers registration
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "db: mark test as requiring database"
    )

# Hooks for test reporting
def pytest_runtest_setup(item):
    """Setup for each test."""
    logger.debug(f"Starting test: {item.name}")

def pytest_runtest_teardown(item):
    """Teardown for each test."""
    logger.debug(f"Finished test: {item.name}")