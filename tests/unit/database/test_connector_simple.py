"""Simple tests for database connector."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from pgsd.database.connector import DatabaseConnector
from pgsd.config.schema import DatabaseConfig
from pgsd.exceptions.database import (
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabasePermissionError,
    DatabaseVersionError
)
from pgsd.models.database import ConnectionStatus


class TestDatabaseConnector:
    """Test cases for DatabaseConnector class."""

    def create_test_config(self):
        """Create test database configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass"
        )

    def create_mock_connection(self):
        """Create mock psycopg2 connection."""
        mock_connection = Mock()
        mock_connection.closed = 0  # Not closed
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.description = True
        mock_cursor.fetchall.return_value = [{"test": "value"}]
        mock_connection.cursor.return_value = mock_cursor
        return mock_connection

    def test_init_success(self):
        """Test successful connector initialization."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
        
        assert connector.connection == mock_connection
        assert connector.db_config == config
        assert connector.connection_id is not None
        assert connector._version_info is None
        assert connector._permissions is None
        assert connector._connection_info is not None

    def test_init_no_psycopg2(self):
        """Test connector initialization without psycopg2."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', None):
            with pytest.raises(ImportError, match="psycopg2 is required"):
                DatabaseConnector(mock_connection, config)

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.execute_query("SELECT 1")
            
            assert result == [{"test": "value"}]
            mock_connection.cursor.assert_called()

    @pytest.mark.asyncio
    async def test_execute_query_connection_closed(self):
        """Test query execution with closed connection."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        mock_connection.closed = 1  # Closed connection
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            # Should raise some connection error
            with pytest.raises(Exception):
                await connector.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_psycopg2_error(self):
        """Test query execution with psycopg2 error."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Create a proper psycopg2.Error class
        class MockPsycopg2Error(Exception):
            pass
        
        with patch('pgsd.database.connector.psycopg2') as mock_psycopg2:
            mock_psycopg2.Error = MockPsycopg2Error
            
            # Make cursor.execute raise the error
            mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
            mock_cursor.execute.side_effect = MockPsycopg2Error("Query failed")
            
            connector = DatabaseConnector(mock_connection, config)
            
            # Should raise some query error
            with pytest.raises(Exception):
                await connector.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self):
        """Test query execution with parameters."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.execute_query("SELECT $1", ("param1",))
            
            assert result == [{"test": "value"}]
            mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
            mock_cursor.execute.assert_called_with("SELECT $1", ("param1",))

    @pytest.mark.asyncio
    async def test_execute_query_no_results(self):
        """Test query execution with no results."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # No description means no results
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.description = None
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.execute_query("UPDATE table SET value=1")
            
            assert result == []

    @pytest.mark.asyncio
    async def test_execute_query_with_fetch_size(self):
        """Test query execution with fetch size."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchmany.return_value = [{"test": "limited"}]
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.execute_query("SELECT * FROM big_table", fetch_size=10)
            
            assert result == [{"test": "limited"}]
            mock_cursor.fetchmany.assert_called_with(10)

    @pytest.mark.asyncio
    async def test_get_version_success(self):
        """Test getting PostgreSQL version."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock version result
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [{"version": "PostgreSQL 13.5 on x86_64"}]
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            with patch('pgsd.models.database.PostgreSQLVersion.parse') as mock_parse:
                mock_version = Mock()
                mock_parse.return_value = mock_version
                
                version = await connector.get_version()
                
                assert version == mock_version
                assert connector._version_info == mock_version

    @pytest.mark.asyncio
    async def test_get_version_cached(self):
        """Test getting cached version."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            # Set cached version
            mock_version = Mock()
            connector._version_info = mock_version
            
            version = await connector.get_version()
            
            assert version == mock_version
            # Should not call cursor (no database query)
            mock_connection.cursor.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_version_failure(self):
        """Test version detection failure."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock empty result
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = []
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            # Should raise some version error
            with pytest.raises(Exception):
                await connector.get_version()

    @pytest.mark.asyncio
    async def test_check_permissions_success(self):
        """Test checking database permissions."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock various permission check results
        check_results = [
            [{"result": "success"}],  # Basic connection check
            [{"has_schema_privilege": True}],  # Schema usage
            [{"has_table_privilege": True}],   # Table select
            [{"has_table_privilege": True}],   # View select
            [{"has_table_privilege": True}],   # Constraint select
            [{"schema_name": "public"}]       # Accessible schemas
        ]
        
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.side_effect = check_results
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            permissions = await connector.check_permissions()
            
            assert permissions is not None
            assert connector._permissions == permissions

    @pytest.mark.asyncio
    async def test_check_permissions_cached(self):
        """Test getting cached permissions."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            # Set cached permissions
            mock_permissions = Mock()
            connector._permissions = mock_permissions
            
            permissions = await connector.check_permissions()
            
            assert permissions == mock_permissions

    @pytest.mark.asyncio
    async def test_verify_schema_access_success(self):
        """Test verifying schema access."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock successful schema access result
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [{"has_schema_privilege": True}]
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.verify_schema_access("test_schema")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_schema_access_failure(self):
        """Test verifying schema access with failure."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock exception during query
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("Permission denied")
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.verify_schema_access("test_schema")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection health check."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.test_connection()
            
            assert result is True
            assert connector._connection_info.status == ConnectionStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection health check failure."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock query failure
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("Connection lost")
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.test_connection()
            
            assert result is False
            assert connector._connection_info.status == ConnectionStatus.ERROR

    @pytest.mark.asyncio
    async def test_get_connection_info(self):
        """Test getting connection information."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            info = await connector.get_connection_info()
            
            assert info is not None
            assert info.connection_id == connector.connection_id
            assert info.database_name == config.database

    @pytest.mark.asyncio
    async def test_get_schema_objects_tables(self):
        """Test getting tables in schema."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock table results
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            {"table_name": "table1"},
            {"table_name": "table2"}
        ]
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            tables = await connector.get_schema_objects("test_schema", "table")
            
            assert tables == ["table1", "table2"]

    @pytest.mark.asyncio
    async def test_get_schema_objects_views(self):
        """Test getting views in schema."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock view results
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [{"table_name": "view1"}]
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            views = await connector.get_schema_objects("test_schema", "view")
            
            assert views == ["view1"]

    @pytest.mark.asyncio
    async def test_get_schema_objects_unsupported_type(self):
        """Test getting objects with unsupported type."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            with pytest.raises(ValueError, match="Unsupported object type"):
                await connector.get_schema_objects("test_schema", "function")

    @pytest.mark.asyncio
    async def test_get_schema_objects_error(self):
        """Test getting objects with query error."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        # Mock query failure
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("Query failed")
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            result = await connector.get_schema_objects("test_schema", "table")
            
            assert result == []

    def test_close(self):
        """Test closing connection."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            connector.close()
            
            mock_connection.close.assert_called_once()
            assert connector._connection_info.status == ConnectionStatus.DISCONNECTED

    def test_close_already_closed(self):
        """Test closing already closed connection."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        mock_connection.closed = 1  # Already closed
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            connector.close()
            
            # Should not attempt to close again
            mock_connection.close.assert_not_called()

    def test_context_manager(self):
        """Test using connector as context manager."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            with connector as ctx:
                assert ctx == connector
            
            mock_connection.close.assert_called_once()

    def test_context_manager_with_exception(self):
        """Test context manager with exception."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            with pytest.raises(ValueError):
                with connector:
                    raise ValueError("Test error")
            
            # Should still close connection
            mock_connection.close.assert_called_once()

    def test_destructor(self):
        """Test destructor closes connection."""
        config = self.create_test_config()
        mock_connection = self.create_mock_connection()
        
        with patch('pgsd.database.connector.psycopg2', Mock()):
            connector = DatabaseConnector(mock_connection, config)
            
            # Manually call destructor
            connector.__del__()
            
            mock_connection.close.assert_called_once()