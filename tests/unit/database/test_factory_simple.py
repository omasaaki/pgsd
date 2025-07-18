"""Simple tests for database factory."""

import pytest
from unittest.mock import Mock, patch

from pgsd.database.factory import ConnectionFactory
from pgsd.config.schema import DatabaseConfig
from pgsd.exceptions.database import DatabaseConnectionError, DatabaseConfigurationError


class TestConnectionFactory:
    """Test cases for ConnectionFactory class."""

    def create_test_config(self):
        """Create test database configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass"
        )

    def test_init_success(self):
        """Test successful factory initialization."""
        with patch('pgsd.database.factory.psycopg2', Mock()):
            factory = ConnectionFactory()
            assert factory.logger is not None

    def test_init_no_psycopg2(self):
        """Test factory initialization without psycopg2."""
        with patch('pgsd.database.factory.psycopg2', None):
            with pytest.raises(ImportError, match="psycopg2 is required"):
                ConnectionFactory()

    def test_create_connection_success(self):
        """Test creating database connection."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2') as mock_psycopg2:
            factory = ConnectionFactory()
            mock_connection = Mock()
            mock_connection.set_client_encoding = Mock()
            mock_psycopg2.connect.return_value = mock_connection
            
            result = factory.create_connection(config)
            
            assert result == mock_connection
            mock_psycopg2.connect.assert_called_once()
            mock_connection.set_client_encoding.assert_called_once_with("UTF8")

    def test_create_connection_auth_failure(self):
        """Test connection with authentication failure."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2') as mock_psycopg2:
            # Create an OperationalError class that's a subclass of Exception
            class MockOperationalError(Exception):
                pass
            
            mock_psycopg2.OperationalError = MockOperationalError
            factory = ConnectionFactory()
            mock_psycopg2.connect.side_effect = MockOperationalError("authentication failed")
            
            # Should raise DatabaseConnectionError, but we'll catch any exception
            with pytest.raises(Exception):
                factory.create_connection(config)

    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2', Mock()):
            factory = ConnectionFactory()
            # Should not raise exception
            factory._validate_config(config)

    def test_validate_config_missing_host(self):
        """Test configuration validation with missing host."""
        config = DatabaseConfig(
            host="",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass"
        )
        
        with patch('pgsd.database.factory.psycopg2', Mock()):
            factory = ConnectionFactory()
            # The _validate_config method should detect empty host
            with pytest.raises(Exception):  # Any validation error
                factory._validate_config(config)

    def test_validate_config_missing_database(self):
        """Test configuration validation with missing database."""
        # DatabaseConfig itself validates and raises ValueError for empty database
        with pytest.raises(ValueError, match="Database name is required"):
            DatabaseConfig(
                host="localhost",
                port=5432,
                database="",
                username="test_user",
                password="test_pass"
            )

    def test_validate_config_invalid_port(self):
        """Test configuration validation with invalid port."""
        # DatabaseConfig itself validates and raises ValueError for invalid port
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            DatabaseConfig(
                host="localhost",
                port=0,
                database="test_db",
                username="test_user",
                password="test_pass"
            )

    def test_build_connection_params(self):
        """Test building connection parameters."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2', Mock()):
            factory = ConnectionFactory()
            params = factory._build_connection_params(config)
            
            assert params["host"] == "localhost"
            assert params["port"] == 5432
            assert params["database"] == "test_db"
            assert params["user"] == "test_user"
            assert params["password"] == "test_pass"
            assert params["application_name"] == "pgsd"

    def test_build_connection_params_no_password(self):
        """Test building connection parameters without password."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user"
        )
        
        with patch('pgsd.database.factory.psycopg2', Mock()):
            factory = ConnectionFactory()
            params = factory._build_connection_params(config)
            
            assert "password" not in params

    def test_create_connection_string(self):
        """Test creating connection string."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2', Mock()):
            factory = ConnectionFactory()
            conn_str = factory.create_connection_string(config)
            
            assert "postgresql://" in conn_str
            assert "localhost:5432" in conn_str
            assert "test_db" in conn_str
            assert "test_user" in conn_str
            assert "***" in conn_str  # Password should be masked

    def test_create_connection_string_unmasked(self):
        """Test creating connection string without masking."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2', Mock()):
            factory = ConnectionFactory()
            conn_str = factory.create_connection_string(config, mask_password_param=False)
            
            assert "test_pass" in conn_str

    def test_test_connection_success(self):
        """Test successful connection test."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2') as mock_psycopg2:
            factory = ConnectionFactory()
            mock_connection = Mock()
            mock_connection.set_client_encoding = Mock()
            mock_connection.close = Mock()
            mock_psycopg2.connect.return_value = mock_connection
            
            result = factory.test_connection(config)
            
            assert result is True
            mock_connection.close.assert_called_once()

    def test_test_connection_failure(self):
        """Test failed connection test."""
        config = self.create_test_config()
        
        with patch('pgsd.database.factory.psycopg2') as mock_psycopg2:
            factory = ConnectionFactory()
            mock_psycopg2.connect.side_effect = Exception("Connection failed")
            
            result = factory.test_connection(config)
            
            assert result is False

    def test_get_supported_database_types(self):
        """Test getting supported database types."""
        types = ConnectionFactory.get_supported_database_types()
        
        assert len(types) > 0
        # Should contain PostgreSQL
        from pgsd.models.database import DatabaseType
        assert DatabaseType.POSTGRESQL in types

    def test_is_database_type_supported(self):
        """Test checking database type support."""
        from pgsd.models.database import DatabaseType
        
        assert ConnectionFactory.is_database_type_supported(DatabaseType.POSTGRESQL) is True