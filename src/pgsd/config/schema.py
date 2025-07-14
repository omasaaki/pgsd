"""Configuration schema definitions for PGSD application."""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class OutputFormat(Enum):
    """Supported output formats."""
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"


class LogLevel(Enum):
    """Supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SSLMode(Enum):
    """PostgreSQL SSL modes."""
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    schema: str = "public"
    connection_timeout: int = 30
    ssl_mode: SSLMode = SSLMode.PREFER
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    
    def __post_init__(self):
        """Validate database configuration."""
        if not self.database:
            raise ValueError("Database name is required")
        if not self.username:
            raise ValueError("Database username is required")
        if self.port < 1 or self.port > 65535:
            raise ValueError("Port must be between 1 and 65535")
        if self.connection_timeout < 1:
            raise ValueError("Connection timeout must be positive")


@dataclass
class OutputConfig:
    """Output configuration."""
    format: OutputFormat = OutputFormat.HTML
    path: str = "./reports/"
    filename_template: str = "schema_diff_{timestamp}"
    include_timestamp: bool = True
    timestamp_format: str = "%Y%m%d_%H%M%S"
    open_browser: bool = False
    
    def __post_init__(self):
        """Validate output configuration."""
        if not self.path:
            raise ValueError("Output path is required")


@dataclass
class ComparisonConfig:
    """Schema comparison configuration."""
    include_views: bool = True
    include_functions: bool = True
    include_constraints: bool = True
    include_indexes: bool = True
    include_triggers: bool = True
    ignore_case: bool = False
    exclude_tables: List[str] = field(default_factory=list)
    exclude_columns: List[str] = field(default_factory=list)
    exclude_schemas: List[str] = field(default_factory=list)
    max_diff_items: int = 1000
    
    def __post_init__(self):
        """Validate comparison configuration."""
        if self.max_diff_items < 1:
            raise ValueError("max_diff_items must be positive")


@dataclass
class SystemConfig:
    """System configuration."""
    timezone: str = "UTC"
    log_level: LogLevel = LogLevel.INFO
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_connections: int = 5
    temp_directory: str = "/tmp"
    worker_threads: int = 4
    memory_limit_mb: int = 1024
    
    def __post_init__(self):
        """Validate system configuration."""
        if self.max_connections < 1:
            raise ValueError("max_connections must be positive")
        if self.worker_threads < 1:
            raise ValueError("worker_threads must be positive")
        if self.memory_limit_mb < 100:
            raise ValueError("memory_limit_mb must be at least 100")


@dataclass
class PostgreSQLConfig:
    """PostgreSQL specific configuration."""
    minimum_version: str = "13.0"
    version_check: bool = True
    compatibility_mode: str = "strict"
    max_identifier_length: int = 63
    case_sensitive_identifiers: bool = False
    
    def __post_init__(self):
        """Validate PostgreSQL configuration."""
        if not self.minimum_version:
            raise ValueError("minimum_version is required")
        if self.max_identifier_length < 1:
            raise ValueError("max_identifier_length must be positive")


@dataclass
class PGSDConfiguration:
    """Main PGSD configuration."""
    source_db: DatabaseConfig = field(default_factory=DatabaseConfig)
    target_db: DatabaseConfig = field(default_factory=DatabaseConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    comparison: ComparisonConfig = field(default_factory=ComparisonConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    postgresql: PostgreSQLConfig = field(default_factory=PostgreSQLConfig)
    
    # Sensitive fields for masking
    _sensitive_fields = {
        'source_db.password',
        'target_db.password',
        'source_db.ssl_key',
        'target_db.ssl_key'
    }
    
    def get_masked_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary with sensitive fields masked."""
        def mask_sensitive_value(value: Any, path: str = "") -> Any:
            """Recursively mask sensitive values."""
            if isinstance(value, dict):
                return {
                    k: mask_sensitive_value(v, f"{path}.{k}" if path else k)
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                return [mask_sensitive_value(item, path) for item in value]
            elif path in self._sensitive_fields and value:
                return "***MASKED***"
            elif hasattr(value, 'value'):  # Handle Enum values
                return value.value
            else:
                return value
        
        config_dict = {
            "source_db": {
                "host": self.source_db.host,
                "port": self.source_db.port,
                "database": self.source_db.database,
                "username": self.source_db.username,
                "password": self.source_db.password,
                "schema": self.source_db.schema,
                "connection_timeout": self.source_db.connection_timeout,
                "ssl_mode": self.source_db.ssl_mode.value,
                "ssl_cert": self.source_db.ssl_cert,
                "ssl_key": self.source_db.ssl_key,
                "ssl_ca": self.source_db.ssl_ca
            },
            "target_db": {
                "host": self.target_db.host,
                "port": self.target_db.port,
                "database": self.target_db.database,
                "username": self.target_db.username,
                "password": self.target_db.password,
                "schema": self.target_db.schema,
                "connection_timeout": self.target_db.connection_timeout,
                "ssl_mode": self.target_db.ssl_mode.value,
                "ssl_cert": self.target_db.ssl_cert,
                "ssl_key": self.target_db.ssl_key,
                "ssl_ca": self.target_db.ssl_ca
            },
            "output": {
                "format": self.output.format.value,
                "path": self.output.path,
                "filename_template": self.output.filename_template,
                "include_timestamp": self.output.include_timestamp,
                "timestamp_format": self.output.timestamp_format,
                "open_browser": self.output.open_browser
            },
            "comparison": {
                "include_views": self.comparison.include_views,
                "include_functions": self.comparison.include_functions,
                "include_constraints": self.comparison.include_constraints,
                "include_indexes": self.comparison.include_indexes,
                "include_triggers": self.comparison.include_triggers,
                "ignore_case": self.comparison.ignore_case,
                "exclude_tables": self.comparison.exclude_tables,
                "exclude_columns": self.comparison.exclude_columns,
                "exclude_schemas": self.comparison.exclude_schemas,
                "max_diff_items": self.comparison.max_diff_items
            },
            "system": {
                "timezone": self.system.timezone,
                "log_level": self.system.log_level.value,
                "log_file": self.system.log_file,
                "log_format": self.system.log_format,
                "max_connections": self.system.max_connections,
                "temp_directory": self.system.temp_directory,
                "worker_threads": self.system.worker_threads,
                "memory_limit_mb": self.system.memory_limit_mb
            },
            "postgresql": {
                "minimum_version": self.postgresql.minimum_version,
                "version_check": self.postgresql.version_check,
                "compatibility_mode": self.postgresql.compatibility_mode,
                "max_identifier_length": self.postgresql.max_identifier_length,
                "case_sensitive_identifiers": self.postgresql.case_sensitive_identifiers
            }
        }
        
        return mask_sensitive_value(config_dict)
    
    def __post_init__(self):
        """Validate cross-configuration rules."""
        # Ensure source and target are different
        if (self.source_db.host == self.target_db.host and
            self.source_db.port == self.target_db.port and
            self.source_db.database == self.target_db.database and
            self.source_db.schema == self.target_db.schema):
            raise ValueError("Source and target databases cannot be identical")