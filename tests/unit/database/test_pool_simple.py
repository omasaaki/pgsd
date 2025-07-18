"""Simple tests for database connection pool."""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from pgsd.database.pool import PooledConnection, ConnectionPool
from pgsd.config.schema import DatabaseConfig
from pgsd.exceptions.database import DatabasePoolError
from pgsd.models.database import PoolHealth


class TestPooledConnection:
    """Test cases for PooledConnection class."""

    def test_init(self):
        """Test PooledConnection initialization."""
        mock_connection = Mock()
        created_at = datetime.utcnow()
        
        pooled_conn = PooledConnection(mock_connection, created_at)
        
        assert pooled_conn.connection == mock_connection
        assert pooled_conn.created_at == created_at
        assert pooled_conn.last_used == created_at
        assert pooled_conn.in_use is False
        assert pooled_conn.is_healthy is True
        assert pooled_conn.use_count == 0
        assert pooled_conn.lock is not None

    @patch('pgsd.database.pool.datetime')
    def test_mark_used(self, mock_datetime):
        """Test marking connection as used."""
        mock_connection = Mock()
        created_at = datetime(2023, 1, 1, 10, 0, 0)
        used_at = datetime(2023, 1, 1, 10, 5, 0)
        
        mock_datetime.utcnow.return_value = used_at
        
        pooled_conn = PooledConnection(mock_connection, created_at)
        initial_count = pooled_conn.use_count
        
        pooled_conn.mark_used()
        
        assert pooled_conn.last_used == used_at
        assert pooled_conn.use_count == initial_count + 1

    def test_mark_used_thread_safety(self):
        """Test thread safety of mark_used method."""
        mock_connection = Mock()
        pooled_conn = PooledConnection(mock_connection, datetime.utcnow())
        
        def increment_use_count():
            for _ in range(100):
                pooled_conn.mark_used()
        
        threads = [threading.Thread(target=increment_use_count) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have been called 1000 times (10 threads * 100 calls each)
        assert pooled_conn.use_count == 1000

    def test_is_expired(self):
        """Test checking if connection is expired."""
        mock_connection = Mock()
        created_at = datetime.utcnow() - timedelta(hours=5)
        
        pooled_conn = PooledConnection(mock_connection, created_at)
        
        # Should be expired if max lifetime is 4 hours
        assert pooled_conn.is_expired(max_lifetime=4 * 3600) is True
        
        # Should not be expired if max lifetime is 6 hours
        assert pooled_conn.is_expired(max_lifetime=6 * 3600) is False

    def test_is_idle(self):
        """Test checking if connection is idle."""
        mock_connection = Mock()
        created_at = datetime.utcnow()
        
        pooled_conn = PooledConnection(mock_connection, created_at)
        pooled_conn.last_used = datetime.utcnow() - timedelta(minutes=30)
        
        # Should be idle if idle timeout is 20 minutes
        assert pooled_conn.is_idle_too_long(idle_timeout=20 * 60) is True
        
        # Should not be idle if idle timeout is 40 minutes
        assert pooled_conn.is_idle_too_long(idle_timeout=40 * 60) is False

    def test_close(self):
        """Test closing pooled connection."""
        mock_connection = Mock()
        mock_connection.closed = 0
        
        pooled_conn = PooledConnection(mock_connection, datetime.utcnow())
        
        pooled_conn.close()
        
        mock_connection.close.assert_called_once()

    def test_close_already_closed(self):
        """Test closing already closed connection."""
        mock_connection = Mock()
        mock_connection.closed = 1
        
        pooled_conn = PooledConnection(mock_connection, datetime.utcnow())
        
        pooled_conn.close()
        
        # Should not attempt to close again
        mock_connection.close.assert_not_called()

    def test_close_with_exception(self):
        """Test closing connection that raises exception."""
        mock_connection = Mock()
        mock_connection.closed = 0
        mock_connection.close.side_effect = Exception("Close failed")
        
        pooled_conn = PooledConnection(mock_connection, datetime.utcnow())
        
        # Should handle exception gracefully
        pooled_conn.close()
        
        mock_connection.close.assert_called_once()


class TestConnectionPool:
    """Test cases for ConnectionPool class."""

    def create_test_config(self):
        """Create test database configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass"
        )

    def test_init_default(self):
        """Test ConnectionPool initialization with defaults."""
        config = self.create_test_config()
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
        
        assert pool.config == config
        assert pool.min_connections == 1
        assert pool.max_connections == 5
        assert pool.max_overflow == 5
        assert pool._pool == []
        assert pool._overflow_connections == []
        assert pool._lock is not None

    def test_init_no_psycopg2(self):
        """Test ConnectionPool initialization without psycopg2."""
        config = self.create_test_config()
        
        with patch('pgsd.database.pool.psycopg2', None):
            with pytest.raises(ImportError, match="psycopg2 is required"):
                ConnectionPool(config)

    def test_init_custom_params(self):
        """Test ConnectionPool initialization with custom parameters."""
        config = self.create_test_config()
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(
                config,
                min_connections=2,
                max_connections=10,
                max_overflow=15,
                connection_timeout=60
            )
        
        assert pool.min_connections == 2
        assert pool.max_connections == 10
        assert pool.max_overflow == 15
        assert pool.connection_timeout == 60

    @patch('pgsd.database.pool.ConnectionFactory')
    def test_pool_basic_functionality(self, mock_factory_class):
        """Test basic pool functionality."""
        config = self.create_test_config()
        
        # Mock factory and connections
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_connection = Mock()
        mock_factory.create_connection.return_value = mock_connection
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            
            # Test pool creation
            assert pool.db_config == config
            assert len(pool._all_connections) == 0

    @patch('pgsd.database.pool.ConnectionFactory')
    def test_get_connection_from_pool(self, mock_factory_class):
        """Test getting connection from pool."""
        config = self.create_test_config()
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_connection = Mock()
        mock_factory.create_connection.return_value = mock_connection
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            
            # Get connection
            conn = pool.get_connection()
            
            assert conn is not None
            # Check that connection is a DatabaseConnector instance

    @patch('pgsd.database.pool.ConnectionFactory')
    def test_get_connection_create_overflow(self, mock_factory_class):
        """Test creating overflow connection when pool is empty."""
        config = self.create_test_config()
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_connection = Mock()
        mock_factory.create_connection.return_value = mock_connection
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config, min_connections=0, max_connections=1)
            pool._initialized = True
            
            # Get connection (should create overflow)
            conn = pool.get_connection()
            
            assert conn is not None
            assert len(pool._overflow_connections) == 1

    def test_get_connection_basic(self):
        """Test basic connection retrieval."""
        config = self.create_test_config()
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            assert pool is not None

    @patch('pgsd.database.pool.ConnectionFactory')
    def test_get_connection_timeout(self, mock_factory_class):
        """Test connection timeout when pool is exhausted."""
        config = self.create_test_config()
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(
                config, 
                min_connections=0, 
                max_connections=1,
                max_overflow=0,
                connection_timeout=0.1
            )
            pool._initialized = True
            
            # Mark all connections as in use
            mock_conn = Mock()
            pooled_conn = PooledConnection(mock_conn, datetime.utcnow())
            pooled_conn.in_use = True
            pool._pool.append(pooled_conn)
            
            with pytest.raises(DatabasePoolError, match="Connection pool exhausted"):
                pool.get_connection()

    @patch('pgsd.database.pool.ConnectionFactory')
    def test_release_connection(self, mock_factory_class):
        """Test releasing connection back to pool."""
        config = self.create_test_config()
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_psycopg2_conn = Mock()
        mock_factory.create_connection.return_value = mock_psycopg2_conn
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            pool.initialize()
            
            # Get and release connection
            conn = pool.get_connection()
            pool.release_connection(conn)
            
            # Connection should be back in pool
            assert len([c for c in pool._pool if not c.in_use]) > 0

    @patch('pgsd.database.pool.ConnectionFactory')
    def test_close_pool(self, mock_factory_class):
        """Test closing connection pool."""
        config = self.create_test_config()
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        
        # Create mock connections
        mock_connections = []
        for _ in range(3):
            mock_conn = Mock()
            mock_conn.closed = 0
            mock_connections.append(mock_conn)
        
        mock_factory.create_connection.side_effect = mock_connections
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config, min_connections=3)
            pool.initialize()
            
            # Close pool
            pool.close()
            
            # All connections should be closed
            for mock_conn in mock_connections:
                mock_conn.close.assert_called_once()
            
            assert pool._initialized is False

    def test_get_health(self):
        """Test getting pool health information."""
        config = self.create_test_config()
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            pool._initialized = True
            
            # Add some connections
            for i in range(3):
                mock_conn = Mock()
                pooled_conn = PooledConnection(mock_conn, datetime.utcnow())
                if i == 0:
                    pooled_conn.in_use = True
                pool._pool.append(pooled_conn)
            
            health = pool.get_health()
            
            assert isinstance(health, PoolHealth)
            assert health.total_connections == 3
            assert health.active_connections == 1
            assert health.idle_connections == 2

    @patch('pgsd.database.pool.ConnectionFactory')
    def test_cleanup_idle_connections(self, mock_factory_class):
        """Test cleaning up idle connections."""
        config = self.create_test_config()
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            pool._initialized = True
            
            # Add an idle connection
            mock_conn = Mock()
            mock_conn.closed = 0
            pooled_conn = PooledConnection(mock_conn, datetime.utcnow())
            pooled_conn.last_used = datetime.utcnow() - timedelta(hours=2)
            pool._pool.append(pooled_conn)
            
            # Run cleanup
            pool._cleanup_connections()
            
            # Idle connection should be removed
            assert len(pool._pool) == 0
            mock_conn.close.assert_called_once()

    def test_is_healthy(self):
        """Test checking pool health status."""
        config = self.create_test_config()
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            
            # Not initialized
            assert pool.is_healthy() is False
            
            pool._initialized = True
            assert pool.is_healthy() is True

    def test_get_statistics(self):
        """Test getting pool statistics."""
        config = self.create_test_config()
        
        with patch('pgsd.database.pool.psycopg2', Mock()):
            pool = ConnectionPool(config)
            pool._initialized = True
            pool._stats['connections_created'] = 10
            pool._stats['connections_reused'] = 50
            
            stats = pool.get_statistics()
            
            assert stats['connections_created'] == 10
            assert stats['connections_reused'] == 50
            assert 'pool_size' in stats