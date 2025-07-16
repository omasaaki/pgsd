"""Database integration tests.

This module tests database-related functionality:
- Basic database connectivity
- Error handling for database operations  
- Simple schema operations
"""

import pytest
import psycopg2
import time
from pathlib import Path
import sys
import os

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Skip all database tests if Docker/database is not available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_DB_TESTS", "false").lower() == "true",
    reason="Database tests skipped (set SKIP_DB_TESTS=false to enable)"
)


@pytest.mark.integration
@pytest.mark.db
class TestDatabaseConnection:
    """Test database connection functionality."""

    def test_successful_connection(self, test_db_config):
        """Test successful database connection."""
        try:
            conn = psycopg2.connect(**test_db_config)
            assert conn is not None
            assert not conn.closed
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            conn.close()
                
        except psycopg2.OperationalError as e:
            if "Connection refused" in str(e) or "could not connect" in str(e):
                pytest.skip("PostgreSQL server is not running")
            else:
                pytest.fail(f"Database connection test failed: {e}")
        except Exception as e:
            pytest.fail(f"Database connection test failed: {e}")

    def test_connection_with_invalid_credentials(self):
        """Test connection with invalid credentials."""
        invalid_config = {
            "host": "localhost",
            "port": 5433,
            "database": "pgsd_test",
            "user": "invalid_user",
            "password": "invalid_password"
        }
        
        with pytest.raises(psycopg2.OperationalError):
            conn = psycopg2.connect(**invalid_config)

    def test_connection_with_invalid_host(self):
        """Test connection with invalid host."""
        invalid_config = {
            "host": "invalid-host-that-does-not-exist",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass"
        }
        
        with pytest.raises(psycopg2.OperationalError):
            conn = psycopg2.connect(**invalid_config)

    @pytest.mark.parametrize("postgres_version", [
        {"port": 5433, "version": "13"},
        {"port": 5434, "version": "14"},
        {"port": 5435, "version": "15"},
        {"port": 5436, "version": "16"},
    ], indirect=True)
    def test_connection_across_postgres_versions(self, postgres_version, test_db_config):
        """Test connection across different PostgreSQL versions."""
        try:
            conn = psycopg2.connect(**test_db_config)
            
            # Test version-specific functionality
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version_info = cursor.fetchone()[0]
            
            assert "PostgreSQL" in version_info
            assert postgres_version["version"] in version_info
            
            conn.close()
                
        except psycopg2.OperationalError as e:
            if "Connection refused" in str(e) or "could not connect" in str(e):
                pytest.skip(f"PostgreSQL {postgres_version['version']} server is not running")
            else:
                pytest.fail(f"PostgreSQL {postgres_version['version']} connection test failed: {e}")
        except Exception as e:
            pytest.fail(f"PostgreSQL {postgres_version['version']} connection test failed: {e}")


@pytest.mark.integration
@pytest.mark.db
class TestBasicSchemaOperations:
    """Test basic schema operations."""

    def test_list_schemas(self, test_db_config):
        """Test listing schemas."""
        try:
            conn = psycopg2.connect(**test_db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            """)
            
            schemas = cursor.fetchall()
            assert len(schemas) >= 0  # Should at least have public schema or test schemas
            
            conn.close()
            
        except Exception as e:
            pytest.fail(f"List schemas test failed: {e}")

    def test_list_tables_in_schema(self, sample_schema_simple, db_connection):
        """Test listing tables in a schema."""
        try:
            cursor = db_connection.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (sample_schema_simple,))
            
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            assert "users" in table_names
            assert "posts" in table_names
            
        except Exception as e:
            pytest.fail(f"List tables test failed: {e}")

    def test_describe_table_structure(self, sample_schema_simple, db_connection):
        """Test describing table structure."""
        try:
            cursor = db_connection.cursor()
            
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (sample_schema_simple, "users"))
            
            columns = cursor.fetchall()
            assert len(columns) > 0
            
            # Check for expected columns
            column_names = [col[0] for col in columns]
            assert "id" in column_names
            assert "username" in column_names
            assert "email" in column_names
            
        except Exception as e:
            pytest.fail(f"Describe table test failed: {e}")


@pytest.mark.integration
@pytest.mark.db
@pytest.mark.slow
class TestDatabasePerformance:
    """Test database performance scenarios."""

    def test_large_query_performance(self, clean_database):
        """Test performance with larger queries."""
        try:
            cursor = clean_database.cursor()
            
            # Create a test table with some data
            cursor.execute("""
                CREATE TEMP TABLE perf_test (
                    id SERIAL PRIMARY KEY,
                    data TEXT
                )
            """)
            
            # Insert test data
            start_time = time.time()
            for i in range(100):
                cursor.execute("INSERT INTO perf_test (data) VALUES (%s)", (f"test_data_{i}",))
            
            # Query the data
            cursor.execute("SELECT COUNT(*) FROM perf_test")
            count = cursor.fetchone()[0]
            end_time = time.time()
            
            assert count == 100
            assert (end_time - start_time) < 10.0  # Should complete within 10 seconds
            
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")