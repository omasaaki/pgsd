"""Database constants for PGSD application."""

from enum import Enum


class SSLMode(Enum):
    """SSL connection modes for PostgreSQL."""
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


class ConnectionTimeout:
    """Connection timeout constants."""
    DEFAULT_CONNECT_TIMEOUT = 30  # seconds
    DEFAULT_QUERY_TIMEOUT = 60  # seconds
    DEFAULT_HEALTH_CHECK_TIMEOUT = 10  # seconds
    MAX_CONNECT_TIMEOUT = 300  # seconds
    MIN_CONNECT_TIMEOUT = 1  # seconds


class PoolConstants:
    """Connection pool constants."""
    DEFAULT_MAX_CONNECTIONS = 5
    DEFAULT_MIN_CONNECTIONS = 1
    MAX_POOL_SIZE = 20
    MIN_POOL_SIZE = 1
    DEFAULT_POOL_TIMEOUT = 30  # seconds
    DEFAULT_IDLE_TIMEOUT = 600  # seconds (10 minutes)
    DEFAULT_MAX_LIFETIME = 3600  # seconds (1 hour)
    HEALTH_CHECK_INTERVAL = 60  # seconds


class DatabaseConstants:
    """General database constants."""
    DEFAULT_PORT = 5432
    DEFAULT_SCHEMA = "public"
    MIN_SUPPORTED_VERSION = "13.0"
    RECOMMENDED_VERSION = "14.0"
    
    # Query constants
    MAX_QUERY_LENGTH = 1024 * 1024  # 1MB
    DEFAULT_FETCH_SIZE = 1000
    MAX_FETCH_SIZE = 10000
    
    # Schema objects
    SUPPORTED_OBJECT_TYPES = [
        "table",
        "view",
        "index",
        "constraint",
        "trigger",
        "procedure",
        "function",
        "sequence",
        "type"
    ]


class QueryConstants:
    """SQL query constants."""
    
    # Version detection
    VERSION_QUERY = "SELECT version()"
    SERVER_VERSION_QUERY = "SHOW server_version_num"
    
    # Permission checks
    CHECK_CONNECT_PERMISSION = """
        SELECT 1 FROM pg_database WHERE datname = current_database()
    """
    
    CHECK_SCHEMA_USAGE = """
        SELECT has_schema_privilege(current_user, %s, 'USAGE')
    """
    
    CHECK_TABLE_SELECT = """
        SELECT has_table_privilege(current_user, %s, 'SELECT')
    """
    
    # Schema information queries
    GET_ACCESSIBLE_SCHEMAS = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        AND has_schema_privilege(current_user, schema_name, 'USAGE')
        ORDER BY schema_name
    """
    
    GET_TABLES_IN_SCHEMA = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        AND table_type = 'BASE TABLE'
        AND has_table_privilege(current_user, 
                               table_schema || '.' || table_name, 'SELECT')
        ORDER BY table_name
    """
    
    GET_VIEWS_IN_SCHEMA = """
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = %s
        AND has_table_privilege(current_user, 
                               table_schema || '.' || table_name, 'SELECT')
        ORDER BY table_name
    """
    
    # Health check queries
    HEALTH_CHECK_QUERY = "SELECT 1"
    
    CONNECTION_INFO_QUERY = """
        SELECT 
            current_database() as database_name,
            current_user as username,
            current_schema() as current_schema,
            inet_server_addr() as server_address,
            inet_server_port() as server_port
    """


class ErrorMessages:
    """Database error messages."""
    
    # Connection errors
    CONNECTION_FAILED = "Failed to connect to database"
    CONNECTION_TIMEOUT = "Connection timeout exceeded"
    AUTHENTICATION_FAILED = "Authentication failed"
    DATABASE_NOT_FOUND = "Database not found"
    
    # Permission errors
    INSUFFICIENT_PERMISSIONS = "Insufficient database permissions"
    SCHEMA_ACCESS_DENIED = "Schema access denied"
    TABLE_ACCESS_DENIED = "Table access denied"
    
    # Version errors
    VERSION_NOT_SUPPORTED = "PostgreSQL version not supported"
    VERSION_DETECTION_FAILED = "Failed to detect PostgreSQL version"
    
    # Pool errors
    POOL_EXHAUSTED = "Connection pool exhausted"
    POOL_TIMEOUT = "Connection pool timeout"
    CONNECTION_NOT_AVAILABLE = "Connection not available"
    
    # Query errors
    QUERY_TIMEOUT = "Query execution timeout"
    QUERY_FAILED = "Query execution failed"
    INVALID_QUERY = "Invalid SQL query"
    
    # General errors
    INTERNAL_ERROR = "Internal database error"
    CONFIGURATION_ERROR = "Database configuration error"
    NETWORK_ERROR = "Network connectivity error"


class LogMessages:
    """Database log messages."""
    
    # Connection messages
    CONNECTION_ESTABLISHED = "Database connection established"
    CONNECTION_CLOSED = "Database connection closed"
    CONNECTION_RETRY = "Retrying database connection"
    
    # Pool messages
    POOL_CREATED = "Connection pool created"
    POOL_DESTROYED = "Connection pool destroyed"
    POOL_HEALTH_CHECK = "Connection pool health check"
    
    # Query messages
    QUERY_EXECUTED = "Query executed successfully"
    QUERY_SLOW = "Slow query detected"
    
    # Version messages
    VERSION_DETECTED = "PostgreSQL version detected"
    VERSION_COMPATIBLE = "PostgreSQL version is compatible"
    VERSION_WARNING = "PostgreSQL version compatibility warning"
    
    # Permission messages
    PERMISSIONS_VERIFIED = "Database permissions verified"
    PERMISSIONS_WARNING = "Database permissions warning"


class MetricNames:
    """Database metrics names."""
    
    # Connection metrics
    CONNECTIONS_TOTAL = "database_connections_total"
    CONNECTIONS_ACTIVE = "database_connections_active"
    CONNECTIONS_IDLE = "database_connections_idle"
    CONNECTIONS_FAILED = "database_connections_failed"
    CONNECTION_DURATION = "database_connection_duration_seconds"
    
    # Query metrics
    QUERIES_TOTAL = "database_queries_total"
    QUERY_DURATION = "database_query_duration_seconds"
    QUERY_ERRORS = "database_query_errors_total"
    
    # Pool metrics
    POOL_SIZE = "database_pool_size"
    POOL_UTILIZATION = "database_pool_utilization_percentage"
    POOL_WAIT_TIME = "database_pool_wait_time_seconds"
    
    # Health metrics
    HEALTH_CHECK_DURATION = "database_health_check_duration_seconds"
    HEALTH_CHECK_FAILURES = "database_health_check_failures_total"
