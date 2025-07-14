# データベース接続管理詳細設計書

## 1. 概要

PostgreSQL Schema Diff Tool (PGSD)のデータベース接続管理システムの詳細実装仕様を定義する。

## 2. ファイル構成

### 2.1 実装ファイル構造
```
src/pgsd/
├── database/
│   ├── __init__.py              # データベースモジュールエクスポート
│   ├── manager.py               # DatabaseManager
│   ├── connector.py             # DatabaseConnector
│   ├── pool.py                  # ConnectionPool
│   ├── factory.py               # ConnectionFactory
│   ├── version.py               # PostgreSQLVersion
│   └── health.py                # HealthMonitor
├── constants/
│   └── database.py              # データベース定数
└── models/
    └── database.py              # データベースモデル
```

## 3. 詳細実装仕様

### 3.1 データベースモデル定義 (models/database.py)

```python
"""Database models for PGSD application."""

from dataclasses import dataclass
from typing import Dict, Optional, List, Any
from enum import Enum
from datetime import datetime


class DatabaseType(Enum):
    """Database type enumeration."""
    POSTGRESQL = "postgresql"


class ConnectionStatus(Enum):
    """Connection status enumeration."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


@dataclass
class PostgreSQLVersion:
    """PostgreSQL version information."""
    major: int
    minor: int
    patch: int
    full_version: str
    server_version_num: int
    
    @classmethod
    def parse(cls, version_string: str) -> 'PostgreSQLVersion':
        """Parse version string to PostgreSQLVersion.
        
        Args:
            version_string: Version string like "14.5" or "PostgreSQL 14.5"
            
        Returns:
            PostgreSQLVersion instance
        """
        # Remove "PostgreSQL" prefix if present
        clean_version = version_string.replace("PostgreSQL", "").strip()
        
        # Split version parts
        parts = clean_version.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        # Calculate server_version_num (PostgreSQL format)
        server_version_num = major * 10000 + minor * 100 + patch
        
        return cls(
            major=major,
            minor=minor,
            patch=patch,
            full_version=clean_version,
            server_version_num=server_version_num
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def is_compatible(self, min_version: str) -> bool:
        """Check if version is compatible with minimum requirement.
        
        Args:
            min_version: Minimum version string
            
        Returns:
            True if compatible
        """
        min_ver = self.parse(min_version)
        return self.server_version_num >= min_ver.server_version_num


@dataclass
class DatabasePermissions:
    """Database permissions information."""
    usage_on_schema: bool
    select_on_tables: bool
    select_on_views: bool
    select_on_information_schema: bool
    connect_to_database: bool
    
    def is_sufficient_for_schema_diff(self) -> bool:
        """Check if permissions are sufficient for schema diff.
        
        Returns:
            True if permissions are sufficient
        """
        return (
            self.connect_to_database and
            self.usage_on_schema and
            self.select_on_information_schema and
            (self.select_on_tables or self.select_on_views)
        )


@dataclass
class ConnectionInfo:
    """Connection information."""
    host: str
    port: int
    database: str
    username: str
    schema: str
    status: ConnectionStatus
    version: Optional[PostgreSQLVersion] = None
    permissions: Optional[DatabasePermissions] = None
    connected_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    connection_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "schema": self.schema,
            "status": self.status.value,
            "version": str(self.version) if self.version else None,
            "permissions": self.permissions.__dict__ if self.permissions else None,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "connection_id": self.connection_id
        }


@dataclass
class PoolHealth:
    """Connection pool health information."""
    total_connections: int
    active_connections: int
    idle_connections: int
    failed_connections: int
    average_connection_time: float
    last_health_check: datetime
    healthy: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "failed_connections": self.failed_connections,
            "average_connection_time": self.average_connection_time,
            "last_health_check": self.last_health_check.isoformat(),
            "healthy": self.healthy
        }
```

### 3.2 データベースコネクター (connector.py)

```python
"""Database connector for PostgreSQL."""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.extensions
except ImportError:
    psycopg2 = None

from ..config.schema import DatabaseConfig
from ..exceptions.database import (
    DatabaseConnectionError, QueryExecutionError, InsufficientPrivilegesError
)
from ..models.database import PostgreSQLVersion, DatabasePermissions, ConnectionInfo, ConnectionStatus


class DatabaseConnector:
    """PostgreSQL database connector."""
    
    def __init__(self, connection: Any, db_config: DatabaseConfig):
        """Initialize database connector.
        
        Args:
            connection: psycopg2 connection object
            db_config: Database configuration
        """
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for database connectivity")
        
        self.connection = connection
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        self._version_info: Optional[PostgreSQLVersion] = None
        self._permissions: Optional[DatabasePermissions] = None
        self._connection_info: Optional[ConnectionInfo] = None
        
        # Initialize connection info
        self._initialize_connection_info()
    
    def _initialize_connection_info(self) -> None:
        """Initialize connection information."""
        self._connection_info = ConnectionInfo(
            host=self.db_config.host,
            port=self.db_config.port,
            database=self.db_config.database,
            username=self.db_config.username,
            schema=self.db_config.schema,
            status=ConnectionStatus.CONNECTED,
            connected_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            connection_id=str(id(self.connection))
        )
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        start_time = time.time()
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                # Handle different query types
                if cursor.description:
                    results = [dict(row) for row in cursor.fetchall()]
                else:
                    results = []
                
                execution_time = time.time() - start_time
                self.logger.debug(f"Query executed in {execution_time:.3f}s: {query[:100]}...")
                
                # Update last activity
                if self._connection_info:
                    self._connection_info.last_activity = datetime.utcnow()
                
                return results
                
        except psycopg2.Error as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Query failed after {execution_time:.3f}s: {e}")
            
            raise QueryExecutionError(
                query=query[:500],  # Truncate long queries
                error_message=str(e),
                postgres_error_code=getattr(e, 'pgcode', None),
                original_error=e
            ) from e
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Unexpected error after {execution_time:.3f}s: {e}")
            
            raise QueryExecutionError(
                query=query[:500],
                error_message=f"Unexpected error: {e}",
                original_error=e
            ) from e
    
    def get_version(self) -> PostgreSQLVersion:
        """Get PostgreSQL version information.
        
        Returns:
            PostgreSQL version information
            
        Raises:
            QueryExecutionError: If version query fails
        """
        if self._version_info is not None:
            return self._version_info
        
        try:
            # Get version string
            version_result = self.execute_query("SELECT version()")
            version_string = version_result[0]['version']
            
            # Get numeric version
            version_num_result = self.execute_query("SHOW server_version_num")
            version_num = int(version_num_result[0]['server_version_num'])
            
            # Parse version
            self._version_info = PostgreSQLVersion.parse(version_string)
            self._version_info.server_version_num = version_num
            
            # Update connection info
            if self._connection_info:
                self._connection_info.version = self._version_info
            
            self.logger.info(f"PostgreSQL version detected: {self._version_info}")
            return self._version_info
            
        except Exception as e:
            self.logger.error(f"Failed to get PostgreSQL version: {e}")
            raise QueryExecutionError(
                query="version detection",
                error_message=f"Failed to detect PostgreSQL version: {e}",
                original_error=e
            ) from e
    
    def check_permissions(self) -> DatabasePermissions:
        """Check database permissions.
        
        Returns:
            Database permissions information
            
        Raises:
            QueryExecutionError: If permission check fails
        """
        if self._permissions is not None:
            return self._permissions
        
        try:
            permissions = DatabasePermissions(
                usage_on_schema=False,
                select_on_tables=False,
                select_on_views=False,
                select_on_information_schema=False,
                connect_to_database=True  # We're already connected
            )
            
            # Check schema usage permission
            try:
                self.execute_query(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                    (self.db_config.schema,)
                )
                permissions.usage_on_schema = True
            except Exception:
                permissions.usage_on_schema = False
            
            # Check information_schema access
            try:
                self.execute_query("SELECT 1 FROM information_schema.tables LIMIT 1")
                permissions.select_on_information_schema = True
            except Exception:
                permissions.select_on_information_schema = False
            
            # Check table access
            try:
                self.execute_query(
                    "SELECT 1 FROM information_schema.tables WHERE table_schema = %s LIMIT 1",
                    (self.db_config.schema,)
                )
                permissions.select_on_tables = True
            except Exception:
                permissions.select_on_tables = False
            
            # Check view access
            try:
                self.execute_query(
                    "SELECT 1 FROM information_schema.views WHERE table_schema = %s LIMIT 1",
                    (self.db_config.schema,)
                )
                permissions.select_on_views = True
            except Exception:
                permissions.select_on_views = False
            
            self._permissions = permissions
            
            # Update connection info
            if self._connection_info:
                self._connection_info.permissions = permissions
            
            # Log permission summary
            if permissions.is_sufficient_for_schema_diff():
                self.logger.info("Database permissions are sufficient for schema diff")
            else:
                self.logger.warning("Database permissions may be insufficient for full schema diff")
            
            return permissions
            
        except Exception as e:
            self.logger.error(f"Failed to check database permissions: {e}")
            raise QueryExecutionError(
                query="permission check",
                error_message=f"Failed to check database permissions: {e}",
                original_error=e
            ) from e
    
    def verify_schema_access(self, schema_name: str) -> bool:
        """Verify access to specific schema.
        
        Args:
            schema_name: Name of schema to check
            
        Returns:
            True if schema is accessible
        """
        try:
            result = self.execute_query(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                (schema_name,)
            )
            return len(result) > 0
        except Exception as e:
            self.logger.warning(f"Cannot access schema '{schema_name}': {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test database connection.
        
        Returns:
            True if connection is working
        """
        try:
            # Simple connection test
            self.execute_query("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> ConnectionInfo:
        """Get connection information.
        
        Returns:
            Connection information
        """
        if self._connection_info is None:
            self._initialize_connection_info()
        return self._connection_info
    
    def close(self) -> None:
        """Close database connection."""
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()
                self.logger.debug("Database connection closed")
                
                # Update connection info
                if self._connection_info:
                    self._connection_info.status = ConnectionStatus.DISCONNECTED
                    
        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
```

### 3.3 接続ファクトリー (factory.py)

```python
"""Connection factory for creating database connections."""

import logging
from typing import Optional, Dict, Any

try:
    import psycopg2
    import psycopg2.extensions
except ImportError:
    psycopg2 = None

from ..config.schema import DatabaseConfig, SSLMode
from ..exceptions.database import DatabaseConnectionError, InvalidConfigurationError


class ConnectionFactory:
    """Factory for creating PostgreSQL connections."""
    
    def __init__(self):
        """Initialize connection factory."""
        self.logger = logging.getLogger(__name__)
        
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for database connectivity")
    
    def create_connection(self, db_config: DatabaseConfig) -> Any:
        """Create new database connection.
        
        Args:
            db_config: Database configuration
            
        Returns:
            psycopg2 connection object
            
        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            # Build connection parameters
            conn_params = self._build_connection_params(db_config)
            
            self.logger.debug(f"Connecting to {db_config.host}:{db_config.port}/{db_config.database}")
            
            # Create connection
            connection = psycopg2.connect(**conn_params)
            
            # Set connection properties
            connection.set_session(autocommit=True)
            connection.set_client_encoding('UTF8')
            
            self.logger.info(f"Successfully connected to {db_config.host}:{db_config.port}/{db_config.database}")
            return connection
            
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError.from_psycopg2_error(
                e, db_config.host, db_config.port, db_config.database, db_config.username
            ) from e
        except Exception as e:
            self.logger.error(f"Unexpected connection error: {e}")
            raise DatabaseConnectionError(
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.username,
                original_error=e
            ) from e
    
    def _build_connection_params(self, db_config: DatabaseConfig) -> Dict[str, Any]:
        """Build connection parameters for psycopg2.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Connection parameters dictionary
        """
        params = {
            'host': db_config.host,
            'port': db_config.port,
            'database': db_config.database,
            'user': db_config.username,
            'password': db_config.password,
            'connect_timeout': db_config.connection_timeout,
            'application_name': 'PGSD-Schema-Diff-Tool'
        }
        
        # Add SSL parameters if configured
        if db_config.ssl_mode != SSLMode.DISABLE:
            params['sslmode'] = db_config.ssl_mode.value
            
            if db_config.ssl_cert:
                params['sslcert'] = db_config.ssl_cert
            if db_config.ssl_key:
                params['sslkey'] = db_config.ssl_key
            if db_config.ssl_ca:
                params['sslrootcert'] = db_config.ssl_ca
        
        return params
    
    def test_connection_params(self, db_config: DatabaseConfig) -> bool:
        """Test connection parameters without creating persistent connection.
        
        Args:
            db_config: Database configuration
            
        Returns:
            True if connection parameters are valid
        """
        try:
            connection = self.create_connection(db_config)
            connection.close()
            return True
        except Exception as e:
            self.logger.debug(f"Connection test failed: {e}")
            return False
```

### 3.4 接続プール (pool.py)

```python
"""Connection pool for managing database connections."""

import logging
import queue
import threading
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import psycopg2
except ImportError:
    psycopg2 = None

from ..config.schema import DatabaseConfig
from ..exceptions.database import DatabaseConnectionError
from ..models.database import PoolHealth
from .factory import ConnectionFactory
from .health import HealthMonitor


class ConnectionPool:
    """PostgreSQL connection pool."""
    
    def __init__(self, db_config: DatabaseConfig, max_connections: int = 5):
        """Initialize connection pool.
        
        Args:
            db_config: Database configuration
            max_connections: Maximum number of connections in pool
        """
        self.db_config = db_config
        self.max_connections = max_connections
        self.logger = logging.getLogger(__name__)
        
        # Connection management
        self._available_connections: queue.Queue = queue.Queue()
        self._active_connections: List[Any] = []
        self._connection_stats: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        # Factory and monitoring
        self._factory = ConnectionFactory()
        self._health_monitor = HealthMonitor()
        
        # Pool state
        self._closed = False
        self._total_created = 0
        self._total_failed = 0
        
        self.logger.info(f"Connection pool initialized (max_connections: {max_connections})")
    
    def get_connection(self) -> Any:
        """Get connection from pool.
        
        Returns:
            psycopg2 connection object
            
        Raises:
            DatabaseConnectionError: If unable to get connection
        """
        if self._closed:
            raise DatabaseConnectionError(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.username,
                original_error=RuntimeError("Connection pool is closed")
            )
        
        with self._lock:
            # Try to get existing connection
            try:
                connection = self._available_connections.get_nowait()
                if self._is_connection_valid(connection):
                    self._active_connections.append(connection)
                    self.logger.debug("Reused existing connection from pool")
                    return connection
                else:
                    # Connection is stale, discard it
                    self._close_connection(connection)
            except queue.Empty:
                pass
            
            # Create new connection if under limit
            if len(self._active_connections) < self.max_connections:
                try:
                    connection = self._create_new_connection()
                    self._active_connections.append(connection)
                    return connection
                except Exception as e:
                    self._total_failed += 1
                    raise
            
            # Pool is exhausted
            raise DatabaseConnectionError(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.username,
                original_error=RuntimeError(
                    f"Connection pool exhausted (max: {self.max_connections})"
                )
            )
    
    def return_connection(self, connection: Any) -> None:
        """Return connection to pool.
        
        Args:
            connection: Connection to return
        """
        if self._closed:
            self._close_connection(connection)
            return
        
        with self._lock:
            if connection in self._active_connections:
                self._active_connections.remove(connection)
                
                if self._is_connection_valid(connection):
                    self._available_connections.put(connection)
                    self.logger.debug("Connection returned to pool")
                else:
                    self._close_connection(connection)
                    self.logger.debug("Invalid connection discarded")
    
    def _create_new_connection(self) -> Any:
        """Create new database connection.
        
        Returns:
            New psycopg2 connection
        """
        start_time = time.time()
        
        try:
            connection = self._factory.create_connection(self.db_config)
            
            connection_time = time.time() - start_time
            self._total_created += 1
            
            # Store connection stats
            conn_id = str(id(connection))
            self._connection_stats[conn_id] = {
                'created_at': datetime.utcnow(),
                'connection_time': connection_time,
                'usage_count': 0
            }
            
            self.logger.debug(f"New connection created in {connection_time:.3f}s")
            return connection
            
        except Exception as e:
            connection_time = time.time() - start_time
            self.logger.error(f"Failed to create connection after {connection_time:.3f}s: {e}")
            raise
    
    def _is_connection_valid(self, connection: Any) -> bool:
        """Check if connection is still valid.
        
        Args:
            connection: Connection to check
            
        Returns:
            True if connection is valid
        """
        try:
            if connection.closed:
                return False
            
            # Simple ping test
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
                
        except Exception:
            return False
    
    def _close_connection(self, connection: Any) -> None:
        """Close connection and clean up stats.
        
        Args:
            connection: Connection to close
        """
        try:
            conn_id = str(id(connection))
            if conn_id in self._connection_stats:
                del self._connection_stats[conn_id]
            
            if not connection.closed:
                connection.close()
                
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")
    
    def get_health(self) -> PoolHealth:
        """Get pool health information.
        
        Returns:
            Pool health information
        """
        with self._lock:
            total_connections = len(self._active_connections) + self._available_connections.qsize()
            active_connections = len(self._active_connections)
            idle_connections = self._available_connections.qsize()
            
            # Calculate average connection time
            if self._connection_stats:
                avg_time = sum(
                    stats['connection_time'] 
                    for stats in self._connection_stats.values()
                ) / len(self._connection_stats)
            else:
                avg_time = 0.0
            
            # Determine if pool is healthy
            healthy = (
                not self._closed and
                self._total_failed < self._total_created * 0.1 and  # Less than 10% failure rate
                total_connections <= self.max_connections
            )
            
            return PoolHealth(
                total_connections=total_connections,
                active_connections=active_connections,
                idle_connections=idle_connections,
                failed_connections=self._total_failed,
                average_connection_time=avg_time,
                last_health_check=datetime.utcnow(),
                healthy=healthy
            )
    
    def cleanup_stale_connections(self, max_idle_time: int = 300) -> int:
        """Clean up stale idle connections.
        
        Args:
            max_idle_time: Maximum idle time in seconds
            
        Returns:
            Number of connections cleaned up
        """
        if self._closed:
            return 0
        
        cleaned_count = 0
        cutoff_time = datetime.utcnow() - timedelta(seconds=max_idle_time)
        
        with self._lock:
            # Check idle connections
            temp_connections = []
            
            while not self._available_connections.empty():
                try:
                    connection = self._available_connections.get_nowait()
                    conn_id = str(id(connection))
                    
                    # Check if connection is too old or invalid
                    if (conn_id in self._connection_stats and
                        self._connection_stats[conn_id]['created_at'] < cutoff_time):
                        self._close_connection(connection)
                        cleaned_count += 1
                    elif self._is_connection_valid(connection):
                        temp_connections.append(connection)
                    else:
                        self._close_connection(connection)
                        cleaned_count += 1
                        
                except queue.Empty:
                    break
            
            # Put back valid connections
            for connection in temp_connections:
                self._available_connections.put(connection)
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} stale connections")
        
        return cleaned_count
    
    def close_all(self) -> None:
        """Close all connections and shut down pool."""
        with self._lock:
            self._closed = True
            
            # Close active connections
            for connection in self._active_connections[:]:
                self._close_connection(connection)
            self._active_connections.clear()
            
            # Close idle connections
            while not self._available_connections.empty():
                try:
                    connection = self._available_connections.get_nowait()
                    self._close_connection(connection)
                except queue.Empty:
                    break
            
            # Clear stats
            self._connection_stats.clear()
            
            self.logger.info("Connection pool closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics.
        
        Returns:
            Pool statistics dictionary
        """
        health = self.get_health()
        
        return {
            "max_connections": self.max_connections,
            "total_created": self._total_created,
            "total_failed": self._total_failed,
            "current_active": health.active_connections,
            "current_idle": health.idle_connections,
            "average_connection_time": health.average_connection_time,
            "healthy": health.healthy,
            "closed": self._closed
        }
```

### 3.5 ヘルスモニター (health.py)

```python
"""Health monitoring for database connections."""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta


class HealthMonitor:
    """Monitors health of database connections and pools."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.logger = logging.getLogger(__name__)
        self._health_history: List[Dict[str, Any]] = []
        self._max_history_size = 100
    
    def record_connection_attempt(self, success: bool, duration: float, error: str = None) -> None:
        """Record connection attempt for health tracking.
        
        Args:
            success: Whether connection was successful
            duration: Connection duration in seconds
            error: Error message if failed
        """
        record = {
            'timestamp': datetime.utcnow(),
            'success': success,
            'duration': duration,
            'error': error
        }
        
        self._health_history.append(record)
        
        # Keep history size manageable
        if len(self._health_history) > self._max_history_size:
            self._health_history.pop(0)
        
        if not success:
            self.logger.warning(f"Connection attempt failed in {duration:.3f}s: {error}")
    
    def get_health_summary(self, window_minutes: int = 10) -> Dict[str, Any]:
        """Get health summary for recent time window.
        
        Args:
            window_minutes: Time window in minutes
            
        Returns:
            Health summary dictionary
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_records = [
            record for record in self._health_history
            if record['timestamp'] > cutoff_time
        ]
        
        if not recent_records:
            return {
                'total_attempts': 0,
                'success_rate': 1.0,
                'average_duration': 0.0,
                'max_duration': 0.0,
                'recent_errors': [],
                'healthy': True
            }
        
        total_attempts = len(recent_records)
        successful_attempts = sum(1 for r in recent_records if r['success'])
        success_rate = successful_attempts / total_attempts
        
        durations = [r['duration'] for r in recent_records if r['success']]
        average_duration = sum(durations) / len(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0.0
        
        recent_errors = [
            r['error'] for r in recent_records[-5:]  # Last 5 errors
            if not r['success'] and r['error']
        ]
        
        # Determine if healthy (>90% success rate, reasonable response times)
        healthy = (
            success_rate >= 0.9 and
            average_duration < 5.0 and  # Average connection time under 5s
            max_duration < 30.0  # No connection taking more than 30s
        )
        
        return {
            'total_attempts': total_attempts,
            'success_rate': success_rate,
            'average_duration': average_duration,
            'max_duration': max_duration,
            'recent_errors': recent_errors,
            'healthy': healthy,
            'window_minutes': window_minutes
        }
    
    def is_healthy(self, window_minutes: int = 10) -> bool:
        """Check if connections are healthy.
        
        Args:
            window_minutes: Time window to check
            
        Returns:
            True if healthy
        """
        summary = self.get_health_summary(window_minutes)
        return summary['healthy']
    
    def clear_history(self) -> None:
        """Clear health history."""
        self._health_history.clear()
        self.logger.debug("Health monitor history cleared")
```

## 4. 統合実装

### 4.1 データベースマネージャー (manager.py)

```python
"""Database manager for coordinating multiple database connections."""

import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from ..config.schema import PGSDConfiguration, DatabaseConfig
from ..exceptions.database import DatabaseConnectionError
from ..models.database import ConnectionInfo, PoolHealth
from .connector import DatabaseConnector
from .pool import ConnectionPool
from .factory import ConnectionFactory


class DatabaseManager:
    """Manages multiple database connections for PGSD."""
    
    def __init__(self, config: PGSDConfiguration):
        """Initialize database manager.
        
        Args:
            config: PGSD configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection pools
        self._source_pool: Optional[ConnectionPool] = None
        self._target_pool: Optional[ConnectionPool] = None
        
        # Connection factory
        self._factory = ConnectionFactory()
        
        # State
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database connections and pools."""
        if self._initialized:
            self.logger.warning("Database manager already initialized")
            return
        
        try:
            # Initialize source database pool
            self._source_pool = ConnectionPool(
                self.config.source_db,
                max_connections=self.config.system.max_connections
            )
            
            # Initialize target database pool
            self._target_pool = ConnectionPool(
                self.config.target_db,
                max_connections=self.config.system.max_connections
            )
            
            # Test initial connections
            self.verify_connections()
            
            self._initialized = True
            self.logger.info("Database manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database manager: {e}")
            self.close_all()
            raise
    
    def get_source_connection(self) -> DatabaseConnector:
        """Get source database connection.
        
        Returns:
            DatabaseConnector for source database
            
        Raises:
            DatabaseConnectionError: If connection fails
        """
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        
        if self._source_pool is None:
            raise RuntimeError("Source database pool not available")
        
        connection = self._source_pool.get_connection()
        return DatabaseConnector(connection, self.config.source_db)
    
    def get_target_connection(self) -> DatabaseConnector:
        """Get target database connection.
        
        Returns:
            DatabaseConnector for target database
            
        Raises:
            DatabaseConnectionError: If connection fails
        """
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        
        if self._target_pool is None:
            raise RuntimeError("Target database pool not available")
        
        connection = self._target_pool.get_connection()
        return DatabaseConnector(connection, self.config.target_db)
    
    def return_connection(self, connector: DatabaseConnector) -> None:
        """Return connection to appropriate pool.
        
        Args:
            connector: DatabaseConnector to return
        """
        # Determine which pool the connection belongs to
        if (connector.db_config.host == self.config.source_db.host and
            connector.db_config.port == self.config.source_db.port and
            connector.db_config.database == self.config.source_db.database):
            if self._source_pool:
                self._source_pool.return_connection(connector.connection)
        else:
            if self._target_pool:
                self._target_pool.return_connection(connector.connection)
    
    def verify_connections(self) -> Dict[str, bool]:
        """Verify all database connections.
        
        Returns:
            Dictionary with connection status for each database
        """
        results = {}
        
        # Test source connection
        try:
            with self.get_source_connection() as connector:
                results['source'] = connector.test_connection()
                if results['source']:
                    version = connector.get_version()
                    permissions = connector.check_permissions()
                    self.logger.info(f"Source DB: {version}, sufficient permissions: {permissions.is_sufficient_for_schema_diff()}")
        except Exception as e:
            self.logger.error(f"Source database verification failed: {e}")
            results['source'] = False
        
        # Test target connection
        try:
            with self.get_target_connection() as connector:
                results['target'] = connector.test_connection()
                if results['target']:
                    version = connector.get_version()
                    permissions = connector.check_permissions()
                    self.logger.info(f"Target DB: {version}, sufficient permissions: {permissions.is_sufficient_for_schema_diff()}")
        except Exception as e:
            self.logger.error(f"Target database verification failed: {e}")
            results['target'] = False
        
        return results
    
    def get_pool_health(self) -> Dict[str, PoolHealth]:
        """Get health information for all pools.
        
        Returns:
            Dictionary with pool health for each database
        """
        health = {}
        
        if self._source_pool:
            health['source'] = self._source_pool.get_health()
        
        if self._target_pool:
            health['target'] = self._target_pool.get_health()
        
        return health
    
    def cleanup_stale_connections(self) -> Dict[str, int]:
        """Clean up stale connections in all pools.
        
        Returns:
            Dictionary with cleanup counts for each pool
        """
        cleanup_counts = {}
        
        if self._source_pool:
            cleanup_counts['source'] = self._source_pool.cleanup_stale_connections()
        
        if self._target_pool:
            cleanup_counts['target'] = self._target_pool.cleanup_stale_connections()
        
        total_cleaned = sum(cleanup_counts.values())
        if total_cleaned > 0:
            self.logger.info(f"Cleaned up {total_cleaned} stale connections")
        
        return cleanup_counts
    
    def close_all(self) -> None:
        """Close all database connections and pools."""
        try:
            if self._source_pool:
                self._source_pool.close_all()
                self._source_pool = None
            
            if self._target_pool:
                self._target_pool.close_all()
                self._target_pool = None
            
            self._initialized = False
            self.logger.info("All database connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall database manager status.
        
        Returns:
            Status information dictionary
        """
        return {
            'initialized': self._initialized,
            'pool_health': self.get_pool_health(),
            'connections_verified': self.verify_connections() if self._initialized else {}
        }
    
    def __enter__(self):
        """Context manager entry."""
        if not self._initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all()
```

---

この詳細設計に基づいて実装を進める。