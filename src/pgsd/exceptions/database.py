"""Database-related exception classes."""

from typing import Any, List, Optional

try:
    import psycopg2
except ImportError:
    # Handle missing psycopg2 gracefully for testing
    psycopg2 = None

from .base import PGSDError, ErrorSeverity, ErrorCategory


class DatabaseError(PGSDError):
    """Base class for database-related errors."""

    default_error_code = "DATABASE_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_category = ErrorCategory.CONNECTION
    default_exit_code = 10
    retriable = True
    base_retry_delay = 2.0
    max_retry_delay = 30.0


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    default_error_code = "DB_CONNECTION_FAILED"
    default_severity = ErrorSeverity.CRITICAL
    default_exit_code = 11

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize database connection error.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user (optional)
            original_error: Original exception
        """
        # Construct error message
        connection_info = f"{host}:{port}"
        if user:
            message = f"Failed to connect to PostgreSQL database '{database}' at {connection_info} as user '{user}'"
        else:
            message = f"Failed to connect to PostgreSQL database '{database}' at {connection_info}"

        # Technical details
        technical_details = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "connection_type": "postgresql",
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Verify that PostgreSQL server is running and accessible",
            f"Check if host '{host}' and port {port} are correct",
            "Verify network connectivity to the database server",
            "Check firewall settings and security groups",
            "Ensure database credentials are correct",
            f"Verify that database '{database}' exists on the server",
        ]

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            original_error=original_error,
        )

    @classmethod
    def from_psycopg2_error(
        cls,
        error: Any,  # psycopg2.Error when available
        host: str,
        port: int,
        database: str,
        user: Optional[str] = None,
    ) -> "DatabaseConnectionError":
        """Create DatabaseConnectionError from psycopg2 error.

        Args:
            error: Original psycopg2 error
            host: Database host
            port: Database port
            database: Database name
            user: Database user (optional)

        Returns:
            DatabaseConnectionError instance
        """
        instance = cls(host, port, database, user, error)

        # Add PostgreSQL-specific technical details
        if hasattr(error, "pgcode"):
            instance.technical_details["postgres_error_code"] = error.pgcode
        if hasattr(error, "pgerror"):
            instance.technical_details["postgres_error_message"] = error.pgerror

        return instance


class SchemaNotFoundError(DatabaseError):
    """Raised when specified schema does not exist."""

    default_error_code = "SCHEMA_NOT_FOUND"
    default_severity = ErrorSeverity.MEDIUM
    default_exit_code = 12
    retriable = False

    def __init__(
        self,
        schema_name: str,
        database: str,
        available_schemas: Optional[List[str]] = None,
    ) -> None:
        """Initialize schema not found error.

        Args:
            schema_name: Name of the schema that was not found
            database: Database name
            available_schemas: List of available schemas (optional)
        """
        message = f"Schema '{schema_name}' not found in database '{database}'"

        # Technical details
        technical_details = {
            "schema_name": schema_name,
            "database": database,
            "available_schemas": available_schemas or [],
        }

        # Recovery suggestions
        recovery_suggestions = [
            f"Verify that schema '{schema_name}' exists in the database",
            "Check schema name spelling and case sensitivity",
            "Ensure you have proper permissions to access the schema",
        ]

        # Add available schemas to suggestions if provided
        if available_schemas:
            available_list = ", ".join(available_schemas)
            recovery_suggestions.append(f"Available schemas: {available_list}")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )


class InsufficientPrivilegesError(DatabaseError):
    """Raised when user lacks required database privileges."""

    default_error_code = "INSUFFICIENT_PRIVILEGES"
    default_severity = ErrorSeverity.HIGH
    default_category = ErrorCategory.AUTHORIZATION
    default_exit_code = 13
    retriable = False

    def __init__(
        self,
        operation: str,
        required_privileges: List[str],
        user: Optional[str] = None,
        object_name: Optional[str] = None,
    ) -> None:
        """Initialize insufficient privileges error.

        Args:
            operation: The operation that failed
            required_privileges: List of required privileges
            user: Database user (optional)
            object_name: Name of the database object (optional)
        """
        # Construct error message
        if object_name and user:
            message = (
                f"User '{user}' lacks privileges to {operation} on '{object_name}'"
            )
        elif user:
            message = f"User '{user}' lacks privileges to {operation}"
        elif object_name:
            message = f"Insufficient privileges to {operation} on '{object_name}'"
        else:
            message = f"Insufficient privileges to {operation}"

        # Technical details
        technical_details = {
            "operation": operation,
            "required_privileges": required_privileges,
            "user": user,
            "object_name": object_name,
        }

        # Recovery suggestions
        privileges_str = ", ".join(required_privileges)
        recovery_suggestions = [
            f"Grant required privileges: {privileges_str}",
            "Contact database administrator for privilege escalation",
            "Verify that user has proper role assignments",
        ]

        if object_name:
            recovery_suggestions.append(
                f"Check object-level permissions on '{object_name}'"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )


class QueryExecutionError(DatabaseError):
    """Raised when SQL query execution fails."""

    default_error_code = "QUERY_EXECUTION_FAILED"
    default_severity = ErrorSeverity.MEDIUM
    default_exit_code = 14
    retriable = True

    def __init__(
        self,
        query: str,
        error_message: str,
        postgres_error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize query execution error.

        Args:
            query: The SQL query that failed
            error_message: Error message from database
            postgres_error_code: PostgreSQL error code (optional)
            original_error: Original exception (optional)
        """
        message = f"Query execution failed: {error_message}"

        # Truncate very long queries for readability
        truncated_query = query if len(query) <= 500 else query[:500] + "..."

        # Technical details
        technical_details = {
            "query": truncated_query,
            "error_message": error_message,
            "postgres_error_code": postgres_error_code,
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Check SQL query syntax and structure",
            "Verify that referenced tables and columns exist",
            "Ensure query permissions are sufficient",
            "Check for data type compatibility issues",
        ]

        if postgres_error_code:
            recovery_suggestions.append(
                f"Refer to PostgreSQL error code documentation for '{postgres_error_code}'"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            original_error=original_error,
        )


class SchemaCollectionError(DatabaseError):
    """Raised when schema information collection fails."""

    default_error_code = "SCHEMA_COLLECTION_FAILED"
    default_severity = ErrorSeverity.MEDIUM
    default_exit_code = 15

    def __init__(
        self,
        message: str,
        schema: Optional[str] = None,
        database_type: Optional[str] = None,
        **kwargs,
    ):
        self.schema = schema
        self.database_type = database_type

        # Technical details
        technical_details = {"schema": schema, "database_type": database_type}

        # Recovery suggestions
        recovery_suggestions = [
            "Verify schema exists and is accessible",
            "Check database connection permissions",
            "Ensure schema privileges are sufficient",
            "Verify PostgreSQL version compatibility",
        ]

        if schema:
            recovery_suggestions.append(
                f"Confirm schema '{schema}' exists in the database"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )


class DatabaseVersionError(DatabaseError):
    """Raised when PostgreSQL version detection or compatibility check fails."""

    default_error_code = "VERSION_ERROR"
    default_severity = ErrorSeverity.MEDIUM
    default_exit_code = 16

    def __init__(
        self,
        message: str,
        version: Optional[str] = None,
        minimum_required: Optional[str] = None,
        **kwargs,
    ):
        self.version = version
        self.minimum_required = minimum_required

        # Technical details
        technical_details = {
            "detected_version": version,
            "minimum_required": minimum_required,
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Check PostgreSQL server version",
            "Upgrade PostgreSQL if version is too old",
            "Verify version detection query permissions",
        ]

        if minimum_required:
            recovery_suggestions.append(
                f"Ensure PostgreSQL version is {minimum_required} or higher"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )


class DatabaseManagerError(DatabaseError):
    """Raised when database manager operations fail."""

    default_error_code = "MANAGER_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_exit_code = 17

    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        self.operation = operation

        # Technical details
        technical_details = {"operation": operation}

        # Recovery suggestions
        recovery_suggestions = [
            "Check database configuration",
            "Verify connection pool status",
            "Review database manager initialization",
            "Check for resource exhaustion",
        ]

        if operation:
            recovery_suggestions.append(f"Retry the '{operation}' operation")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )


class DatabasePoolError(DatabaseError):
    """Raised when database connection pool operations fail."""

    default_error_code = "POOL_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_exit_code = 18

    def __init__(
        self,
        message: str,
        pool_size: Optional[int] = None,
        active_connections: Optional[int] = None,
        **kwargs,
    ):
        self.pool_size = pool_size
        self.active_connections = active_connections

        # Technical details
        technical_details = {
            "pool_size": pool_size,
            "active_connections": active_connections,
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Check connection pool configuration",
            "Verify database server availability",
            "Check for connection leaks",
            "Consider increasing pool size if needed",
            "Review connection timeout settings",
        ]

        if pool_size and active_connections:
            if active_connections >= pool_size:
                recovery_suggestions.append("Pool is exhausted - wait or increase size")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )


class DatabaseQueryError(DatabaseError):
    """Raised when database query operations fail."""

    default_error_code = "QUERY_ERROR"
    default_severity = ErrorSeverity.MEDIUM
    default_exit_code = 19

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        error_code: Optional[str] = None,
        **kwargs,
    ):
        self.query = query
        self.error_code = error_code

        # Technical details
        technical_details = {"query": query, "error_code": error_code}

        # Recovery suggestions
        recovery_suggestions = [
            "Check SQL query syntax",
            "Verify database permissions",
            "Check database connection status",
            "Review query parameters",
        ]

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )


class DatabaseConfigurationError(DatabaseError):
    """Raised when database configuration is invalid."""

    default_error_code = "CONFIG_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_exit_code = 20

    def __init__(
        self,
        message: str,
        config_field: Optional[str] = None,
        config_value: Optional[str] = None,
        **kwargs,
    ):
        self.config_field = config_field
        self.config_value = config_value

        # Technical details
        technical_details = {
            "config_field": config_field,
            "config_value": config_value,
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Check database configuration file",
            "Verify configuration values are correct",
            "Review environment variables",
            "Check configuration file permissions",
        ]

        if config_field:
            recovery_suggestions.append(f"Verify '{config_field}' configuration")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )


class DatabasePermissionError(DatabaseError):
    """Raised when database permission checks fail."""

    default_error_code = "PERMISSION_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_exit_code = 21

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        object_name: Optional[str] = None,
        **kwargs,
    ):
        self.operation = operation
        self.object_name = object_name

        # Technical details
        technical_details = {"operation": operation, "object_name": object_name}

        # Recovery suggestions
        recovery_suggestions = [
            "Check database user permissions",
            "Verify role assignments",
            "Contact database administrator",
            "Review object-level permissions",
        ]

        if operation:
            recovery_suggestions.append(f"Grant permissions for '{operation}' operation")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )


class DatabaseHealthError(DatabaseError):
    """Raised when database health checks fail."""

    default_error_code = "HEALTH_ERROR"
    default_severity = ErrorSeverity.MEDIUM
    default_exit_code = 22

    def __init__(
        self,
        message: str,
        health_status: Optional[str] = None,
        failed_checks: Optional[List[str]] = None,
        **kwargs,
    ):
        self.health_status = health_status
        self.failed_checks = failed_checks or []

        # Technical details
        technical_details = {
            "health_status": health_status,
            "failed_checks": failed_checks,
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Check database server status",
            "Verify connection pool health",
            "Review database resource utilization",
            "Check database logs for errors",
        ]

        if failed_checks:
            for check in failed_checks:
                recovery_suggestions.append(f"Address failed health check: {check}")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            **kwargs,
        )
