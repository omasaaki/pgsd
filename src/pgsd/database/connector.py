"""Database connector for PGSD application."""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import sql
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    sql = None

from ..config.schema import DatabaseConfig
from ..constants.database import (
    QueryConstants,
    ErrorMessages,
    LogMessages,
    ConnectionTimeout,
)
from ..exceptions.database import (
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabasePermissionError,
    DatabaseVersionError,
)
from ..models.database import (
    PostgreSQLVersion,
    DatabasePermissions,
    ConnectionInfo,
    ConnectionStatus,
)
from ..error_handling.retry import retry_on_error


class DatabaseConnector:
    """Low-level database connection management."""

    def __init__(self, connection, db_config: DatabaseConfig):
        """Initialize database connector.

        Args:
            connection: psycopg2 connection object
            db_config: Database configuration
        """
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for database operations")

        self.connection = connection
        self.db_config = db_config
        self.connection_id = str(uuid.uuid4())
        self.logger = logging.getLogger(__name__)

        # Cached information
        self._version_info: Optional[PostgreSQLVersion] = None
        self._permissions: Optional[DatabasePermissions] = None
        self._connection_info: Optional[ConnectionInfo] = None

        # Initialize connection info
        self._connection_info = ConnectionInfo(
            connection_id=self.connection_id,
            database_name=db_config.database,
            host=db_config.host,
            port=db_config.port,
            username=db_config.username,
            schema=db_config.schema or "public",
            status=ConnectionStatus.CONNECTED,
            connection_time=datetime.utcnow(),
        )

        self.logger.info(
            LogMessages.CONNECTION_ESTABLISHED,
            extra={
                "connection_id": self.connection_id,
                "host": db_config.host,
                "database": db_config.database,
                "user": db_config.username,
            },
        )

    @retry_on_error(
        max_attempts=3, base_delay=1.0, retriable_exceptions=(DatabaseQueryError,)
    )
    async def execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, Dict[str, Any]]] = None,
        fetch_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results.

        Args:
            query: SQL query string
            params: Query parameters
            fetch_size: Maximum number of rows to fetch

        Returns:
            List of query results as dictionaries

        Raises:
            DatabaseQueryError: If query execution fails
        """
        if not self.connection or self.connection.closed:
            raise DatabaseConnectionError(
                ErrorMessages.CONNECTION_NOT_AVAILABLE, connection_id=self.connection_id
            )

        start_time = datetime.utcnow()

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Set query timeout
                timeout_ms = ConnectionTimeout.DEFAULT_QUERY_TIMEOUT * 1000
                cursor.execute(f"SET statement_timeout = {timeout_ms}")

                # Execute query
                cursor.execute(query, params)

                # Fetch results
                if cursor.description:
                    if fetch_size:
                        results = cursor.fetchmany(fetch_size)
                    else:
                        results = cursor.fetchall()

                    # Convert to list of dictionaries
                    return [dict(row) for row in results]
                else:
                    return []

        except psycopg2.Error as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.error(
                "Query execution failed",
                extra={
                    "connection_id": self.connection_id,
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "error": str(e),
                    "execution_time": execution_time,
                },
            )

            raise DatabaseQueryError(
                f"Query execution failed: {str(e)}",
                query=query,
                connection_id=self.connection_id,
                original_error=e,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.error(
                "Unexpected error during query execution",
                extra={
                    "connection_id": self.connection_id,
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "error": str(e),
                    "execution_time": execution_time,
                },
            )

            raise DatabaseQueryError(
                f"Unexpected error: {str(e)}",
                query=query,
                connection_id=self.connection_id,
                original_error=e,
            )

        finally:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._connection_info.last_activity = datetime.utcnow()

            self.logger.debug(
                LogMessages.QUERY_EXECUTED,
                extra={
                    "connection_id": self.connection_id,
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "execution_time": execution_time,
                },
            )

    async def get_version(self) -> PostgreSQLVersion:
        """Get PostgreSQL version information.

        Returns:
            PostgreSQL version information

        Raises:
            DatabaseVersionError: If version detection fails
        """
        if self._version_info:
            return self._version_info

        try:
            # Get version string
            version_result = await self.execute_query(QueryConstants.VERSION_QUERY)
            if not version_result:
                raise DatabaseVersionError(
                    ErrorMessages.VERSION_DETECTION_FAILED,
                    connection_id=self.connection_id,
                )

            version_string = version_result[0]["version"]

            # Parse version
            self._version_info = PostgreSQLVersion.parse(version_string)

            # Update connection info
            self._connection_info.version = self._version_info

            self.logger.info(
                LogMessages.VERSION_DETECTED,
                extra={
                    "connection_id": self.connection_id,
                    "version": str(self._version_info),
                },
            )

            return self._version_info

        except Exception as e:
            raise DatabaseVersionError(
                f"Version detection failed: {str(e)}",
                connection_id=self.connection_id,
                original_error=e,
            )

    async def check_permissions(self) -> DatabasePermissions:
        """Check database permissions.

        Returns:
            Database permissions information

        Raises:
            DatabasePermissionError: If permission check fails
        """
        if self._permissions:
            return self._permissions

        try:
            permissions = DatabasePermissions()

            # Check basic connection
            try:
                await self.execute_query(QueryConstants.CHECK_CONNECT_PERMISSION)
                permissions.can_connect = True
            except Exception:
                permissions.can_connect = False

            # Check schema usage
            try:
                result = await self.execute_query(
                    QueryConstants.CHECK_SCHEMA_USAGE,
                    (self.db_config.schema or "public",),
                )
                permissions.can_read_schema = result[0].get(
                    "has_schema_privilege", False
                )
            except Exception:
                permissions.can_read_schema = False

            # Check table access
            try:
                # Test with a known system table
                result = await self.execute_query(
                    QueryConstants.CHECK_TABLE_SELECT, ("information_schema.tables",)
                )
                permissions.can_read_tables = result[0].get(
                    "has_table_privilege", False
                )
            except Exception:
                permissions.can_read_tables = False

            # Check view access
            try:
                result = await self.execute_query(
                    QueryConstants.CHECK_TABLE_SELECT, ("information_schema.views",)
                )
                permissions.can_read_views = result[0].get("has_table_privilege", False)
            except Exception:
                permissions.can_read_views = False

            # Check constraint access
            try:
                result = await self.execute_query(
                    QueryConstants.CHECK_TABLE_SELECT,
                    ("information_schema.table_constraints",),
                )
                permissions.can_read_constraints = result[0].get(
                    "has_table_privilege", False
                )
            except Exception:
                permissions.can_read_constraints = False

            # Get accessible schemas
            try:
                schema_result = await self.execute_query(
                    QueryConstants.GET_ACCESSIBLE_SCHEMAS
                )
                permissions.accessible_schemas = [
                    row["schema_name"] for row in schema_result
                ]
            except Exception:
                permissions.accessible_schemas = []

            # Cache permissions
            self._permissions = permissions

            # Update connection info
            self._connection_info.permissions = permissions

            self.logger.info(
                LogMessages.PERMISSIONS_VERIFIED,
                extra={
                    "connection_id": self.connection_id,
                    "has_required_permissions": permissions.has_required_permissions(),
                    "accessible_schemas": len(permissions.accessible_schemas),
                },
            )

            return permissions

        except Exception as e:
            raise DatabasePermissionError(
                f"Permission check failed: {str(e)}",
                connection_id=self.connection_id,
                original_error=e,
            )

    async def verify_schema_access(self, schema_name: str) -> bool:
        """Verify access to specific schema.

        Args:
            schema_name: Schema name to check

        Returns:
            True if schema is accessible
        """
        try:
            result = await self.execute_query(
                QueryConstants.CHECK_SCHEMA_USAGE, (schema_name,)
            )
            return result[0].get("has_schema_privilege", False)
        except Exception:
            return False

    async def test_connection(self) -> bool:
        """Test database connection health.

        Returns:
            True if connection is healthy
        """
        try:
            await self.execute_query(QueryConstants.HEALTH_CHECK_QUERY)
            self._connection_info.status = ConnectionStatus.CONNECTED
            self._connection_info.last_activity = datetime.utcnow()
            return True
        except Exception as e:
            self._connection_info.status = ConnectionStatus.ERROR
            self._connection_info.error_message = str(e)
            return False

    async def get_connection_info(self) -> ConnectionInfo:
        """Get connection information.

        Returns:
            Connection information
        """
        # Refresh status
        await self.test_connection()

        # Ensure version and permissions are loaded
        if not self._version_info:
            try:
                await self.get_version()
            except Exception:
                pass

        if not self._permissions:
            try:
                await self.check_permissions()
            except Exception:
                pass

        return self._connection_info

    async def get_schema_objects(self, schema_name: str, object_type: str) -> List[str]:
        """Get list of objects in schema.

        Args:
            schema_name: Schema name
            object_type: Object type ('table', 'view', etc.)

        Returns:
            List of object names
        """
        if object_type == "table":
            query = QueryConstants.GET_TABLES_IN_SCHEMA
        elif object_type == "view":
            query = QueryConstants.GET_VIEWS_IN_SCHEMA
        else:
            raise ValueError(f"Unsupported object type: {object_type}")

        try:
            result = await self.execute_query(query, (schema_name,))
            return [row["table_name"] for row in result]
        except Exception as e:
            self.logger.error(
                f"Failed to get {object_type}s in schema {schema_name}",
                extra={
                    "connection_id": self.connection_id,
                    "schema": schema_name,
                    "object_type": object_type,
                    "error": str(e),
                },
            )
            return []

    def close(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self._connection_info.status = ConnectionStatus.DISCONNECTED

            self.logger.info(
                LogMessages.CONNECTION_CLOSED,
                extra={"connection_id": self.connection_id},
            )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Destructor - ensure connection is closed."""
        try:
            self.close()
        except Exception:
            pass
