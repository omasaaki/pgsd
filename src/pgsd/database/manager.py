"""Database manager for PGSD application."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.schema import PGSDConfiguration
from ..constants.database import DatabaseConstants
from ..exceptions.database import (
    DatabaseConnectionError,
    DatabaseVersionError,
    DatabaseManagerError,
)
from ..models.database import PostgreSQLVersion, ConnectionInfo, PoolHealth
from .pool import ConnectionPool
from .connector import DatabaseConnector


class DatabaseManager:
    """High-level database connection management."""

    def __init__(self, config: PGSDConfiguration):
        """Initialize database manager.

        Args:
            config: PGSD configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Connection pools
        self.source_pool: Optional[ConnectionPool] = None
        self.target_pool: Optional[ConnectionPool] = None

        # Initialization state
        self._initialized = False
        self._initialization_time: Optional[datetime] = None

        self.logger.info(
            "Database manager initialized",
            extra={
                "source_host": config.database.source.host,
                "source_database": config.database.source.database,
                "target_host": config.database.target.host,
                "target_database": config.database.target.database,
            },
        )

    async def initialize(self) -> None:
        """Initialize database connections and pools.

        Raises:
            DatabaseManagerError: If initialization fails
        """
        if self._initialized:
            self.logger.warning("Database manager already initialized")
            return

        try:
            self.logger.info("Initializing database connections")

            # Create source connection pool
            self.source_pool = ConnectionPool(
                self.config.database.source,
                max_connections=self.config.system.max_connections,
            )

            # Create target connection pool
            self.target_pool = ConnectionPool(
                self.config.database.target,
                max_connections=self.config.system.max_connections,
            )

            # Verify connections
            await self._verify_initial_connections()

            self._initialized = True
            self._initialization_time = datetime.utcnow()

            self.logger.info("Database manager initialized successfully")

        except Exception as e:
            self.logger.error(
                "Failed to initialize database manager", extra={"error": str(e)}
            )

            # Cleanup on failure
            await self.close_all()

            raise DatabaseManagerError(
                f"Database manager initialization failed: {str(e)}", original_error=e
            )

    async def get_source_connection(self) -> DatabaseConnector:
        """Get source database connection.

        Returns:
            Database connector for source database

        Raises:
            DatabaseManagerError: If connection cannot be obtained
        """
        if not self._initialized:
            raise DatabaseManagerError("Database manager not initialized")

        if not self.source_pool:
            raise DatabaseManagerError("Source connection pool not available")

        try:
            return self.source_pool.get_connection()
        except Exception as e:
            self.logger.error(
                "Failed to get source connection", extra={"error": str(e)}
            )
            raise DatabaseManagerError(
                f"Failed to get source connection: {str(e)}", original_error=e
            )

    async def get_target_connection(self) -> DatabaseConnector:
        """Get target database connection.

        Returns:
            Database connector for target database

        Raises:
            DatabaseManagerError: If connection cannot be obtained
        """
        if not self._initialized:
            raise DatabaseManagerError("Database manager not initialized")

        if not self.target_pool:
            raise DatabaseManagerError("Target connection pool not available")

        try:
            return self.target_pool.get_connection()
        except Exception as e:
            self.logger.error(
                "Failed to get target connection", extra={"error": str(e)}
            )
            raise DatabaseManagerError(
                f"Failed to get target connection: {str(e)}", original_error=e
            )

    def return_source_connection(self, connector: DatabaseConnector) -> None:
        """Return source database connection to pool.

        Args:
            connector: Database connector to return
        """
        if self.source_pool:
            self.source_pool.return_connection(connector)

    def return_target_connection(self, connector: DatabaseConnector) -> None:
        """Return target database connection to pool.

        Args:
            connector: Database connector to return
        """
        if self.target_pool:
            self.target_pool.return_connection(connector)

    async def verify_connections(self) -> Dict[str, bool]:
        """Verify all database connections.

        Returns:
            Dictionary with connection verification results
        """
        if not self._initialized:
            return {"source": False, "target": False}

        results = {}

        # Test source connection
        try:
            source_conn = await self.get_source_connection()
            results["source"] = await source_conn.test_connection()
            self.return_source_connection(source_conn)
        except Exception as e:
            self.logger.error(
                "Source connection verification failed", extra={"error": str(e)}
            )
            results["source"] = False

        # Test target connection
        try:
            target_conn = await self.get_target_connection()
            results["target"] = await target_conn.test_connection()
            self.return_target_connection(target_conn)
        except Exception as e:
            self.logger.error(
                "Target connection verification failed", extra={"error": str(e)}
            )
            results["target"] = False

        self.logger.info(
            "Connection verification completed",
            extra={
                "source_healthy": results["source"],
                "target_healthy": results["target"],
            },
        )

        return results

    async def get_database_versions(self) -> Dict[str, Optional[PostgreSQLVersion]]:
        """Get PostgreSQL versions for both databases.

        Returns:
            Dictionary with version information
        """
        versions = {"source": None, "target": None}

        if not self._initialized:
            return versions

        # Get source version
        try:
            source_conn = await self.get_source_connection()
            versions["source"] = await source_conn.get_version()
            self.return_source_connection(source_conn)
        except Exception as e:
            self.logger.error(
                "Failed to get source database version", extra={"error": str(e)}
            )

        # Get target version
        try:
            target_conn = await self.get_target_connection()
            versions["target"] = await target_conn.get_version()
            self.return_target_connection(target_conn)
        except Exception as e:
            self.logger.error(
                "Failed to get target database version", extra={"error": str(e)}
            )

        return versions

    async def get_connection_info(self) -> Dict[str, Optional[ConnectionInfo]]:
        """Get connection information for both databases.

        Returns:
            Dictionary with connection information
        """
        info = {"source": None, "target": None}

        if not self._initialized:
            return info

        # Get source connection info
        try:
            source_conn = await self.get_source_connection()
            info["source"] = await source_conn.get_connection_info()
            self.return_source_connection(source_conn)
        except Exception as e:
            self.logger.error(
                "Failed to get source connection info", extra={"error": str(e)}
            )

        # Get target connection info
        try:
            target_conn = await self.get_target_connection()
            info["target"] = await target_conn.get_connection_info()
            self.return_target_connection(target_conn)
        except Exception as e:
            self.logger.error(
                "Failed to get target connection info", extra={"error": str(e)}
            )

        return info

    async def get_pool_health(self) -> Dict[str, Optional[PoolHealth]]:
        """Get health information for connection pools.

        Returns:
            Dictionary with pool health information
        """
        health = {"source": None, "target": None}

        if self.source_pool:
            health["source"] = self.source_pool.health_check()

        if self.target_pool:
            health["target"] = self.target_pool.health_check()

        return health

    async def cleanup_stale_connections(self) -> Dict[str, int]:
        """Clean up stale connections in both pools.

        Returns:
            Dictionary with cleanup counts
        """
        cleanup_counts = {"source": 0, "target": 0}

        if self.source_pool:
            cleanup_counts["source"] = self.source_pool.cleanup_stale_connections()

        if self.target_pool:
            cleanup_counts["target"] = self.target_pool.cleanup_stale_connections()

        total_cleaned = cleanup_counts["source"] + cleanup_counts["target"]

        if total_cleaned > 0:
            self.logger.info(
                f"Cleaned up {total_cleaned} stale connections",
                extra={
                    "source_cleaned": cleanup_counts["source"],
                    "target_cleaned": cleanup_counts["target"],
                },
            )

        return cleanup_counts

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for database manager.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "initialized": self._initialized,
            "initialization_time": (
                self._initialization_time.isoformat()
                if self._initialization_time
                else None
            ),
            "uptime_seconds": (
                (datetime.utcnow() - self._initialization_time).total_seconds()
                if self._initialization_time
                else 0
            ),
            "source_pool": None,
            "target_pool": None,
            "connections": await self.verify_connections(),
            "versions": await self.get_database_versions(),
            "pool_health": await self.get_pool_health(),
        }

        # Add pool statistics
        if self.source_pool:
            stats["source_pool"] = self.source_pool.get_statistics()

        if self.target_pool:
            stats["target_pool"] = self.target_pool.get_statistics()

        return stats

    async def _verify_initial_connections(self) -> None:
        """Verify initial connections during initialization.

        Raises:
            DatabaseManagerError: If connection verification fails
        """
        # Test source connection
        try:
            source_conn = await self.get_source_connection()

            # Test connection
            if not await source_conn.test_connection():
                raise DatabaseConnectionError("Source connection test failed")

            # Check version
            version = await source_conn.get_version()
            min_version = PostgreSQLVersion.parse(
                DatabaseConstants.MIN_SUPPORTED_VERSION
            )

            if version < min_version:
                raise DatabaseVersionError(
                    f"Source database version {version} is below minimum "
                    f"supported version {min_version}"
                )

            # Check permissions
            permissions = await source_conn.check_permissions()
            if not permissions.has_required_permissions():
                missing = permissions.get_missing_permissions()
                raise DatabaseConnectionError(
                    f"Source database missing required permissions: {', '.join(missing)}"
                )

            self.return_source_connection(source_conn)

            self.logger.info(
                "Source database connection verified",
                extra={
                    "version": str(version),
                    "has_permissions": permissions.has_required_permissions(),
                },
            )

        except Exception as e:
            raise DatabaseManagerError(f"Source database verification failed: {str(e)}")

        # Test target connection
        try:
            target_conn = await self.get_target_connection()

            # Test connection
            if not await target_conn.test_connection():
                raise DatabaseConnectionError("Target connection test failed")

            # Check version
            version = await target_conn.get_version()
            min_version = PostgreSQLVersion.parse(
                DatabaseConstants.MIN_SUPPORTED_VERSION
            )

            if version < min_version:
                raise DatabaseVersionError(
                    f"Target database version {version} is below minimum "
                    f"supported version {min_version}"
                )

            # Check permissions
            permissions = await target_conn.check_permissions()
            if not permissions.has_required_permissions():
                missing = permissions.get_missing_permissions()
                raise DatabaseConnectionError(
                    f"Target database missing required permissions: {', '.join(missing)}"
                )

            self.return_target_connection(target_conn)

            self.logger.info(
                "Target database connection verified",
                extra={
                    "version": str(version),
                    "has_permissions": permissions.has_required_permissions(),
                },
            )

        except Exception as e:
            raise DatabaseManagerError(f"Target database verification failed: {str(e)}")

    async def close_all(self) -> None:
        """Close all database connections and pools."""
        try:
            # Close source pool
            if self.source_pool:
                self.source_pool.close()
                self.source_pool = None

            # Close target pool
            if self.target_pool:
                self.target_pool.close()
                self.target_pool = None

            self._initialized = False

            self.logger.info("All database connections closed")

        except Exception as e:
            self.logger.error(
                "Error closing database connections", extra={"error": str(e)}
            )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all()

    def __del__(self):
        """Destructor - ensure connections are closed."""
        try:
            if self._initialized:
                if self.source_pool:
                    self.source_pool.close()
                if self.target_pool:
                    self.target_pool.close()
        except Exception:
            pass
