"""Connection pool for PGSD application."""

import logging
import queue
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import psycopg2
except ImportError:
    psycopg2 = None

from ..config.schema import DatabaseConfig
from ..constants.database import (
    PoolConstants,
    ErrorMessages,
    LogMessages,
)
from ..exceptions.database import DatabasePoolError
from ..models.database import PoolHealth
from .factory import ConnectionFactory
from .connector import DatabaseConnector


class PooledConnection:
    """Wrapper for pooled database connections."""

    def __init__(self, connection, created_at: datetime):
        """Initialize pooled connection.

        Args:
            connection: psycopg2 connection object
            created_at: Creation timestamp
        """
        self.connection = connection
        self.created_at = created_at
        self.last_used = created_at
        self.in_use = False
        self.is_healthy = True
        self.use_count = 0
        self.lock = threading.Lock()

    def mark_used(self):
        """Mark connection as used."""
        with self.lock:
            self.last_used = datetime.utcnow()
            self.use_count += 1

    def is_expired(self, max_lifetime: int) -> bool:
        """Check if connection has expired.

        Args:
            max_lifetime: Maximum lifetime in seconds

        Returns:
            True if connection has expired
        """
        return (datetime.utcnow() - self.created_at).total_seconds() > max_lifetime

    def is_idle_too_long(self, idle_timeout: int) -> bool:
        """Check if connection has been idle too long.

        Args:
            idle_timeout: Idle timeout in seconds

        Returns:
            True if connection has been idle too long
        """
        return (datetime.utcnow() - self.last_used).total_seconds() > idle_timeout

    def test_health(self) -> bool:
        """Test connection health.

        Returns:
            True if connection is healthy
        """
        try:
            if self.connection.closed:
                self.is_healthy = False
                return False

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            self.is_healthy = True
            return True
        except Exception:
            self.is_healthy = False
            return False

    def close(self):
        """Close the connection."""
        try:
            if not self.connection.closed:
                self.connection.close()
        except Exception:
            pass

        self.is_healthy = False


class ConnectionPool:
    """Database connection pool."""

    def __init__(self, db_config: DatabaseConfig, max_connections: int = None):
        """Initialize connection pool.

        Args:
            db_config: Database configuration
            max_connections: Maximum number of connections
        """
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for connection pooling")

        self.db_config = db_config
        self.max_connections = max_connections or PoolConstants.DEFAULT_MAX_CONNECTIONS
        self.min_connections = PoolConstants.DEFAULT_MIN_CONNECTIONS
        self.pool_timeout = PoolConstants.DEFAULT_POOL_TIMEOUT
        self.idle_timeout = PoolConstants.DEFAULT_IDLE_TIMEOUT
        self.max_lifetime = PoolConstants.DEFAULT_MAX_LIFETIME

        self.logger = logging.getLogger(__name__)
        self.factory = ConnectionFactory()

        # Pool state
        self._pool: queue.Queue = queue.Queue(maxsize=self.max_connections)
        self._all_connections: List[PooledConnection] = []
        self._lock = threading.Lock()
        self._created_count = 0
        self._health_check_thread = None
        self._shutdown = False

        # Statistics
        self._stats = {
            "total_created": 0,
            "total_destroyed": 0,
            "total_borrowed": 0,
            "total_returned": 0,
            "total_health_checks": 0,
            "total_health_failures": 0,
        }

        # Start health check thread
        self._start_health_check_thread()

        self.logger.info(
            LogMessages.POOL_CREATED,
            extra={
                "max_connections": self.max_connections,
                "min_connections": self.min_connections,
                "host": db_config.host,
                "database": db_config.database,
            },
        )

    def get_connection(self, timeout: Optional[float] = None) -> DatabaseConnector:
        """Get connection from pool.

        Args:
            timeout: Timeout in seconds

        Returns:
            Database connector

        Raises:
            DatabasePoolError: If connection cannot be obtained
        """
        if self._shutdown:
            raise DatabasePoolError("Connection pool is shutdown")

        timeout = timeout or self.pool_timeout
        start_time = time.time()

        try:
            # Try to get existing connection from pool
            try:
                pooled_conn = self._pool.get(timeout=timeout)

                # Test connection health
                if pooled_conn.test_health():
                    pooled_conn.mark_used()
                    pooled_conn.in_use = True

                    self._stats["total_borrowed"] += 1

                    return DatabaseConnector(pooled_conn.connection, self.db_config)
                else:
                    # Connection is unhealthy, remove it
                    self._remove_connection(pooled_conn)

                    # Try to create new connection
                    return self._create_new_connection()

            except queue.Empty:
                # No connections available, try to create new one
                if self._created_count < self.max_connections:
                    return self._create_new_connection()
                else:
                    # Pool is full, wait for available connection
                    remaining_time = timeout - (time.time() - start_time)
                    if remaining_time <= 0:
                        raise DatabasePoolError(ErrorMessages.POOL_TIMEOUT)

                    # Recursive call with remaining timeout
                    return self.get_connection(remaining_time)

        except Exception as e:
            self.logger.error(
                "Failed to get connection from pool",
                extra={
                    "error": str(e),
                    "timeout": timeout,
                    "created_count": self._created_count,
                    "max_connections": self.max_connections,
                },
            )

            if isinstance(e, DatabasePoolError):
                raise
            else:
                raise DatabasePoolError(f"Failed to get connection: {str(e)}")

    def return_connection(self, connector: DatabaseConnector) -> None:
        """Return connection to pool.

        Args:
            connector: Database connector to return
        """
        if self._shutdown:
            self._close_connection(connector.connection)
            return

        try:
            # Find the pooled connection
            pooled_conn = None
            with self._lock:
                for conn in self._all_connections:
                    if conn.connection == connector.connection:
                        pooled_conn = conn
                        break

            if pooled_conn:
                # Test connection health before returning
                if pooled_conn.test_health():
                    pooled_conn.in_use = False
                    pooled_conn.mark_used()

                    # Return to pool
                    try:
                        self._pool.put(pooled_conn, block=False)
                        self._stats["total_returned"] += 1
                    except queue.Full:
                        # Pool is full, close connection
                        self._remove_connection(pooled_conn)
                else:
                    # Connection is unhealthy, remove it
                    self._remove_connection(pooled_conn)
            else:
                # Connection not found in pool, just close it
                self._close_connection(connector.connection)

        except Exception as e:
            self.logger.error(
                "Failed to return connection to pool", extra={"error": str(e)}
            )

            # Close connection as fallback
            self._close_connection(connector.connection)

    def _create_new_connection(self) -> DatabaseConnector:
        """Create new connection.

        Returns:
            Database connector

        Raises:
            DatabasePoolError: If connection cannot be created
        """
        try:
            # Create connection
            connection = self.factory.create_connection(self.db_config)

            # Create pooled connection
            pooled_conn = PooledConnection(connection, datetime.utcnow())
            pooled_conn.in_use = True

            # Add to pool tracking
            with self._lock:
                self._all_connections.append(pooled_conn)
                self._created_count += 1

            self._stats["total_created"] += 1
            self._stats["total_borrowed"] += 1

            return DatabaseConnector(connection, self.db_config)

        except Exception as e:
            raise DatabasePoolError(f"Failed to create connection: {str(e)}")

    def _remove_connection(self, pooled_conn: PooledConnection) -> None:
        """Remove connection from pool.

        Args:
            pooled_conn: Pooled connection to remove
        """
        try:
            pooled_conn.close()

            with self._lock:
                if pooled_conn in self._all_connections:
                    self._all_connections.remove(pooled_conn)
                    self._created_count -= 1

            self._stats["total_destroyed"] += 1

        except Exception as e:
            self.logger.error(
                "Failed to remove connection from pool", extra={"error": str(e)}
            )

    def _close_connection(self, connection) -> None:
        """Close a connection.

        Args:
            connection: Connection to close
        """
        try:
            if not connection.closed:
                connection.close()
        except Exception:
            pass

    def health_check(self) -> PoolHealth:
        """Perform health check on pool.

        Returns:
            Pool health information
        """
        with self._lock:
            total_connections = len(self._all_connections)
            active_connections = sum(1 for conn in self._all_connections if conn.in_use)
            idle_connections = total_connections - active_connections

            # Count healthy connections
            healthy_connections = 0
            failed_connections = 0

            for conn in self._all_connections:
                if conn.test_health():
                    healthy_connections += 1
                else:
                    failed_connections += 1

            # Calculate average connection time
            if self._stats["total_created"] > 0:
                avg_connection_time = (
                    sum(
                        (datetime.utcnow() - conn.created_at).total_seconds()
                        for conn in self._all_connections
                    )
                    / len(self._all_connections)
                    if self._all_connections
                    else 0
                )
            else:
                avg_connection_time = 0

            self._stats["total_health_checks"] += 1
            self._stats["total_health_failures"] += failed_connections

        return PoolHealth(
            total_connections=total_connections,
            active_connections=active_connections,
            idle_connections=idle_connections,
            max_connections=self.max_connections,
            healthy_connections=healthy_connections,
            failed_connections=failed_connections,
            average_connection_time=avg_connection_time,
            last_health_check=datetime.utcnow(),
        )

    def cleanup_stale_connections(self) -> int:
        """Clean up stale connections.

        Returns:
            Number of connections cleaned up
        """
        cleaned_up = 0

        with self._lock:
            connections_to_remove = []

            for conn in self._all_connections:
                if not conn.in_use:
                    # Check if connection is expired or idle too long
                    if conn.is_expired(self.max_lifetime) or conn.is_idle_too_long(
                        self.idle_timeout
                    ):
                        connections_to_remove.append(conn)

            # Remove stale connections
            for conn in connections_to_remove:
                self._remove_connection(conn)
                cleaned_up += 1

        if cleaned_up > 0:
            self.logger.info(f"Cleaned up {cleaned_up} stale connections")

        return cleaned_up

    def _start_health_check_thread(self):
        """Start health check thread."""

        def health_check_worker():
            while not self._shutdown:
                try:
                    time.sleep(PoolConstants.HEALTH_CHECK_INTERVAL)

                    if not self._shutdown:
                        health = self.health_check()
                        self.cleanup_stale_connections()

                        self.logger.debug(
                            LogMessages.POOL_HEALTH_CHECK,
                            extra={
                                "total_connections": health.total_connections,
                                "active_connections": health.active_connections,
                                "healthy_connections": health.healthy_connections,
                                "failed_connections": health.failed_connections,
                            },
                        )

                except Exception as e:
                    if not self._shutdown:
                        self.logger.error(
                            "Health check failed", extra={"error": str(e)}
                        )

        self._health_check_thread = threading.Thread(
            target=health_check_worker, daemon=True, name="pgsd-pool-health-check"
        )
        self._health_check_thread.start()

    def close(self):
        """Close connection pool."""
        self._shutdown = True

        # Wait for health check thread to finish
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=5)

        # Close all connections
        with self._lock:
            for conn in self._all_connections:
                conn.close()

            self._all_connections.clear()
            self._created_count = 0

        # Clear pool queue
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except queue.Empty:
                break

        self.logger.info(
            LogMessages.POOL_DESTROYED,
            extra={
                "total_created": self._stats["total_created"],
                "total_destroyed": self._stats["total_destroyed"],
                "total_borrowed": self._stats["total_borrowed"],
                "total_returned": self._stats["total_returned"],
            },
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary of pool statistics
        """
        with self._lock:
            return {
                **self._stats,
                "current_connections": len(self._all_connections),
                "active_connections": sum(
                    1 for conn in self._all_connections if conn.in_use
                ),
                "max_connections": self.max_connections,
                "pool_utilization": (len(self._all_connections) / self.max_connections)
                * 100,
            }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Destructor - ensure pool is closed."""
        try:
            self.close()
        except Exception:
            pass
