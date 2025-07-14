"""
Test environment validation and basic functionality tests.
"""
import pytest
import psycopg2
from pgsd.utils.logger import get_logger

@pytest.mark.unit
class TestTestEnvironment:
    """Test the test environment setup."""
    
    def test_pytest_markers_work(self):
        """Test that pytest markers are properly configured."""
        # This test validates the unit marker works
        assert True
    
    def test_logger_import(self):
        """Test that logger can be imported and used."""
        logger = get_logger("test_environment")
        assert logger is not None
        logger.info("Test environment validation")

@pytest.mark.integration 
@pytest.mark.db
class TestDatabaseConnection:
    """Test database connectivity across all PostgreSQL versions."""
    
    def test_database_connection(self, test_db_config):
        """Test basic database connection."""
        conn = psycopg2.connect(**test_db_config)
        assert conn is not None
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        conn.close()
    
    def test_database_version(self, test_db_config, postgres_version):
        """Test PostgreSQL version detection."""
        conn = psycopg2.connect(**test_db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version()")
        version_string = cursor.fetchone()[0]
        
        expected_version = postgres_version["version"]
        assert expected_version in version_string
        
        conn.close()
    
    def test_database_schemas(self, clean_database):
        """Test database schema operations."""
        cursor = clean_database.cursor()
        
        # Test schema creation
        test_schema = "test_schema_operations"
        cursor.execute(f"CREATE SCHEMA {test_schema}")
        
        # Verify schema exists
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s
        """, (test_schema,))
        
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == test_schema
        
        # Test schema cleanup (handled by fixture)

@pytest.mark.integration
@pytest.mark.db
class TestSampleSchemas:
    """Test sample schema fixtures."""
    
    def test_simple_schema_creation(self, sample_schema_simple, clean_database):
        """Test simple schema fixture."""
        cursor = clean_database.cursor()
        
        # Verify schema exists
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s
        """, (sample_schema_simple,))
        
        result = cursor.fetchone()
        assert result is not None
        
        # Verify tables exist
        cursor.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s
            ORDER BY table_name
        """, (sample_schema_simple,))
        
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        assert 'users' in table_names
        assert 'posts' in table_names
    
    def test_complex_schema_creation(self, sample_schema_complex, clean_database):
        """Test complex schema fixture."""
        cursor = clean_database.cursor()
        
        # Verify schema exists
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s
        """, (sample_schema_complex,))
        
        result = cursor.fetchone()
        assert result is not None
        
        # Verify custom types
        cursor.execute(f"""
            SELECT typname 
            FROM pg_type t
            JOIN pg_namespace n ON t.typnamespace = n.oid
            WHERE n.nspname = %s AND t.typtype = 'e'
        """, (sample_schema_complex,))
        
        types = cursor.fetchall()
        type_names = [type_row[0] for type_row in types]
        assert 'status_type' in type_names
        
        # Verify views
        cursor.execute(f"""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = %s
        """, (sample_schema_complex,))
        
        views = cursor.fetchall()
        view_names = [view[0] for view in views]
        assert 'active_products' in view_names

@pytest.mark.integration
@pytest.mark.db
class TestFixtureData:
    """Test that fixture data is properly loaded."""
    
    def test_connection_test_data(self, clean_database):
        """Test that basic fixture data exists."""
        cursor = clean_database.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM public.connection_test
        """)
        
        count = cursor.fetchone()[0]
        assert count >= 1
    
    def test_sample_users_data(self, clean_database):
        """Test that sample users data exists."""
        cursor = clean_database.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM test_fixtures.sample_users
        """)
        
        count = cursor.fetchone()[0]
        assert count >= 4  # Should have at least 4 sample users
        
        # Test specific user
        cursor.execute("""
            SELECT username, email FROM test_fixtures.sample_users 
            WHERE username = 'testuser1'
        """)
        
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'testuser1'
        assert result[1] == 'test1@example.com'

@pytest.mark.slow
@pytest.mark.integration
class TestPerformance:
    """Test environment performance characteristics."""
    
    def test_connection_speed(self, test_db_config):
        """Test that database connections are reasonably fast."""
        import time
        
        start_time = time.time()
        conn = psycopg2.connect(**test_db_config)
        connection_time = time.time() - start_time
        
        assert connection_time < 5.0  # Should connect within 5 seconds
        conn.close()
    
    def test_query_performance(self, clean_database):
        """Test basic query performance."""
        import time
        
        cursor = clean_database.cursor()
        
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM test_fixtures.sample_users")
        query_time = time.time() - start_time
        
        assert query_time < 1.0  # Simple query should complete quickly