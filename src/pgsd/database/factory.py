"""Connection factory for PGSD application."""

import logging
from typing import Optional

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    psycopg2 = None
    sql = None

from ..config.schema import DatabaseConfig
from ..constants.database import (
    SSLMode,
    ConnectionTimeout,
    ErrorMessages,
    LogMessages
)
from ..exceptions.database import (
    DatabaseConnectionError,
    DatabaseConfigurationError
)
from ..models.database import DatabaseType
from ..utils.security import mask_password


class ConnectionFactory:
    """Factory for creating database connections."""
    
    def __init__(self):
        """Initialize connection factory."""
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for database connections")
        
        self.logger = logging.getLogger(__name__)
    
    def create_connection(self, db_config: DatabaseConfig) -> 'psycopg2.connection':
        """Create a new database connection.
        
        Args:
            db_config: Database configuration
            
        Returns:
            psycopg2 connection object
            
        Raises:
            DatabaseConnectionError: If connection fails
            DatabaseConfigurationError: If configuration is invalid
        """
        # Validate configuration
        self._validate_config(db_config)
        
        # Build connection parameters
        conn_params = self._build_connection_params(db_config)
        
        # Log connection attempt (with masked password)
        self.logger.info("Attempting database connection", extra={
            "host": db_config.host,
            "port": db_config.port,
            "database": db_config.database,
            "user": db_config.username,
            "ssl_mode": db_config.ssl_mode.value if db_config.ssl_mode else "none"
        })
        
        try:
            # Create connection
            connection = psycopg2.connect(**conn_params)
            
            # Set connection properties
            connection.set_client_encoding('UTF8')
            
            # Set default schema if specified
            if db_config.schema and db_config.schema != "public":
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {db_config.schema}, public")
                    connection.commit()
            
            self.logger.info(LogMessages.CONNECTION_ESTABLISHED, extra={
                "host": db_config.host,
                "database": db_config.database,
                "user": db_config.username
            })
            
            return connection
            
        except psycopg2.OperationalError as e:
            # Handle specific PostgreSQL errors
            error_msg = str(e).lower()
            
            if "authentication failed" in error_msg:
                raise DatabaseConnectionError(
                    ErrorMessages.AUTHENTICATION_FAILED,
                    host=db_config.host,
                    port=db_config.port,
                    database=db_config.database,
                    user=db_config.username,
                    original_error=e
                )
            elif "database" in error_msg and "does not exist" in error_msg:
                raise DatabaseConnectionError(
                    ErrorMessages.DATABASE_NOT_FOUND,
                    host=db_config.host,
                    port=db_config.port,
                    database=db_config.database,
                    user=db_config.username,
                    original_error=e
                )
            elif "timeout" in error_msg:
                raise DatabaseConnectionError(
                    ErrorMessages.CONNECTION_TIMEOUT,
                    host=db_config.host,
                    port=db_config.port,
                    database=db_config.database,
                    user=db_config.username,
                    original_error=e
                )
            else:
                raise DatabaseConnectionError(
                    f"{ErrorMessages.CONNECTION_FAILED}: {str(e)}",
                    host=db_config.host,
                    port=db_config.port,
                    database=db_config.database,
                    user=db_config.username,
                    original_error=e
                )
        
        except Exception as e:
            self.logger.error("Unexpected error creating connection", extra={
                "host": db_config.host,
                "database": db_config.database,
                "user": db_config.username,
                "error": str(e)
            })
            
            raise DatabaseConnectionError(
                f"{ErrorMessages.CONNECTION_FAILED}: {str(e)}",
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.username,
                original_error=e
            )
    
    def _validate_config(self, db_config: DatabaseConfig) -> None:
        """Validate database configuration.
        
        Args:
            db_config: Database configuration to validate
            
        Raises:
            DatabaseConfigurationError: If configuration is invalid
        """
        errors = []
        
        # Required fields
        if not db_config.host:
            errors.append("Host is required")
        if not db_config.database:
            errors.append("Database name is required")
        if not db_config.username:
            errors.append("Username is required")
        
        # Port validation
        if db_config.port and (db_config.port < 1 or db_config.port > 65535):
            errors.append("Port must be between 1 and 65535")
        
        # Timeout validation
        if db_config.connection_timeout:
            if db_config.connection_timeout < ConnectionTimeout.MIN_CONNECT_TIMEOUT:
                errors.append(f"Connection timeout must be at least {ConnectionTimeout.MIN_CONNECT_TIMEOUT} seconds")
            if db_config.connection_timeout > ConnectionTimeout.MAX_CONNECT_TIMEOUT:
                errors.append(f"Connection timeout cannot exceed {ConnectionTimeout.MAX_CONNECT_TIMEOUT} seconds")
        
        # SSL configuration validation
        if db_config.ssl_mode:
            if db_config.ssl_mode in [SSLMode.VERIFY_CA, SSLMode.VERIFY_FULL]:
                if not db_config.ssl_ca:
                    errors.append("SSL CA certificate is required for verify-ca and verify-full modes")
        
        if errors:
            raise DatabaseConfigurationError(
                f"Invalid database configuration: {'; '.join(errors)}",
                config_errors=errors
            )
    
    def _build_connection_params(self, db_config: DatabaseConfig) -> dict:
        """Build psycopg2 connection parameters.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Dictionary of connection parameters
        """
        params = {
            'host': db_config.host,
            'port': db_config.port or 5432,
            'database': db_config.database,
            'user': db_config.username,
            'connect_timeout': db_config.connection_timeout or ConnectionTimeout.DEFAULT_CONNECT_TIMEOUT
        }
        
        # Add password if provided
        if db_config.password:
            params['password'] = db_config.password
        
        # Add SSL parameters
        if db_config.ssl_mode:
            params['sslmode'] = db_config.ssl_mode.value
            
            if db_config.ssl_cert:
                params['sslcert'] = db_config.ssl_cert
            
            if db_config.ssl_key:
                params['sslkey'] = db_config.ssl_key
            
            if db_config.ssl_ca:
                params['sslrootcert'] = db_config.ssl_ca
        
        # Add application name for monitoring
        params['application_name'] = 'pgsd'
        
        return params
    
    def create_connection_string(self, db_config: DatabaseConfig, mask_password: bool = True) -> str:
        """Create connection string for logging/debugging.
        
        Args:
            db_config: Database configuration
            mask_password: Whether to mask password in output
            
        Returns:
            Connection string
        """
        password = "***" if mask_password else db_config.password or "<none>"
        
        base_url = f"postgresql://{db_config.username}:{password}@{db_config.host}:{db_config.port or 5432}/{db_config.database}"
        
        # Add SSL parameters
        params = []
        if db_config.ssl_mode:
            params.append(f"sslmode={db_config.ssl_mode.value}")
        
        if db_config.connection_timeout:
            params.append(f"connect_timeout={db_config.connection_timeout}")
        
        if params:
            base_url += "?" + "&".join(params)
        
        return base_url
    
    def test_connection(self, db_config: DatabaseConfig) -> bool:
        """Test database connection without keeping it open.
        
        Args:
            db_config: Database configuration
            
        Returns:
            True if connection succeeds, False otherwise
        """
        try:
            connection = self.create_connection(db_config)
            connection.close()
            return True
        except Exception as e:
            self.logger.debug(f"Connection test failed: {str(e)}")
            return False
    
    @staticmethod
    def get_supported_database_types() -> list:
        """Get list of supported database types.
        
        Returns:
            List of supported database types
        """
        return [DatabaseType.POSTGRESQL]
    
    @staticmethod
    def is_database_type_supported(db_type: DatabaseType) -> bool:
        """Check if database type is supported.
        
        Args:
            db_type: Database type to check
            
        Returns:
            True if supported, False otherwise
        """
        return db_type in ConnectionFactory.get_supported_database_types()
