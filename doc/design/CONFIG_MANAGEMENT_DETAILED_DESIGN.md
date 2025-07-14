# 設定管理詳細設計書

## 1. 概要

PostgreSQL Schema Diff Tool (PGSD)の設定管理システムの詳細実装仕様を定義する。

## 2. ファイル構成

### 2.1 実装ファイル構造
```
src/pgsd/
├── config/
│   ├── __init__.py              # 設定管理エクスポート
│   ├── manager.py               # 設定管理メインクラス
│   ├── schema.py                # 設定スキーマ定義
│   ├── validator.py             # 設定値バリデーター
│   ├── parsers.py               # 設定パーサー群
│   └── substitutor.py           # 環境変数置換
├── constants/
│   └── config_defaults.py       # デフォルト設定値
└── examples/
    ├── pgsd_config.yaml         # サンプル設定ファイル
    └── .env.example             # 環境変数サンプル
```

## 3. 詳細実装仕様

### 3.1 設定スキーマ定義 (schema.py)

```python
"""Configuration schema definitions for PGSD application."""

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
        def mask_value(obj, path):
            if path in self._sensitive_fields and obj:
                return "***MASKED***"
            return obj
        
        # Implementation would recursively mask sensitive fields
        # This is a simplified version
        return {
            "source_db": {
                "host": self.source_db.host,
                "port": self.source_db.port,
                "database": self.source_db.database,
                "username": self.source_db.username,
                "password": mask_value(self.source_db.password, "source_db.password"),
                "schema": self.source_db.schema,
                "connection_timeout": self.source_db.connection_timeout,
                "ssl_mode": self.source_db.ssl_mode.value
            },
            # Similar for other sections...
        }
```

### 3.2 設定管理メインクラス (manager.py)

```python
"""Configuration manager for PGSD application."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .schema import PGSDConfiguration
from .parsers import YAMLParser, EnvironmentParser, CLIParser
from .validator import ConfigurationValidator
from .substitutor import EnvironmentSubstitutor
from ..exceptions.config import (
    ConfigurationError, MissingConfigurationError, InvalidConfigurationError
)


class ConfigurationManager:
    """Manages PGSD configuration from multiple sources."""
    
    # Configuration file search paths (in order)
    CONFIG_SEARCH_PATHS = [
        "./pgsd_config.yaml",
        "~/.pgsd/config.yaml", 
        "/etc/pgsd/config.yaml"
    ]
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.validator = ConfigurationValidator()
        self.substitutor = EnvironmentSubstitutor()
        self._config: Optional[PGSDConfiguration] = None
    
    def load_configuration(
        self,
        cli_args: Optional[Dict[str, Any]] = None,
        env_prefix: str = "PGSD_"
    ) -> PGSDConfiguration:
        """Load configuration from all sources.
        
        Args:
            cli_args: CLI arguments dictionary
            env_prefix: Environment variable prefix
            
        Returns:
            Loaded and validated configuration
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            # 1. Load from file
            file_config = self._load_file_config()
            
            # 2. Load from environment
            env_config = self._load_env_config(env_prefix)
            
            # 3. Merge configurations (priority: CLI > Env > File > Default)
            merged_config = self._merge_configurations(
                file_config, env_config, cli_args or {}
            )
            
            # 4. Substitute environment variables
            substituted_config = self.substitutor.substitute(merged_config)
            
            # 5. Validate configuration
            self._config = self.validator.validate(substituted_config)
            
            self.logger.info("Configuration loaded successfully")
            return self._config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}") from e
    
    def _load_file_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Returns:
            Configuration dictionary from file
        """
        config_path = self._find_config_file()
        if not config_path:
            self.logger.info("No configuration file found, using defaults")
            return {}
        
        try:
            parser = YAMLParser()
            config = parser.parse(config_path)
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration file {config_path}: {e}"
            ) from e
    
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file using search paths.
        
        Returns:
            Path to configuration file or None if not found
        """
        # Use explicitly specified file first
        if self.config_file:
            path = Path(self.config_file).expanduser()
            if path.exists():
                return path
            else:
                raise MissingConfigurationError(
                    missing_keys=["config_file"],
                    config_file=path
                )
        
        # Search in default locations
        for search_path in self.CONFIG_SEARCH_PATHS:
            path = Path(search_path).expanduser()
            if path.exists():
                return path
        
        return None
    
    def _load_env_config(self, prefix: str) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix
            
        Returns:
            Configuration dictionary from environment
        """
        parser = EnvironmentParser(prefix)
        return parser.parse()
    
    def _merge_configurations(
        self,
        file_config: Dict[str, Any],
        env_config: Dict[str, Any],
        cli_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge configurations with priority handling.
        
        Args:
            file_config: Configuration from file
            env_config: Configuration from environment
            cli_config: Configuration from CLI
            
        Returns:
            Merged configuration dictionary
        """
        # Start with defaults
        merged = {}
        
        # Apply file config
        self._deep_update(merged, file_config)
        
        # Apply environment config (higher priority)
        self._deep_update(merged, env_config)
        
        # Apply CLI config (highest priority)
        self._deep_update(merged, cli_config)
        
        return merged
    
    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep update dictionary.
        
        Args:
            base: Base dictionary to update
            update: Updates to apply
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get_configuration(self) -> PGSDConfiguration:
        """Get current configuration.
        
        Returns:
            Current configuration object
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config
    
    def get_masked_configuration(self) -> Dict[str, Any]:
        """Get configuration with sensitive fields masked.
        
        Returns:
            Masked configuration dictionary
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config.get_masked_dict()
```

### 3.3 環境変数置換 (substitutor.py)

```python
"""Environment variable substitution for configuration values."""

import os
import re
import logging
from typing import Any, Dict, Union
from pathlib import Path

from ..exceptions.config import InvalidConfigurationError


class EnvironmentSubstitutor:
    """Handles environment variable substitution in configuration values."""
    
    # Pattern for ${VAR_NAME} or ${VAR_NAME:default_value}
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')
    
    def __init__(self, load_dotenv: bool = True):
        """Initialize environment substitutor.
        
        Args:
            load_dotenv: Whether to load .env file
        """
        self.logger = logging.getLogger(__name__)
        if load_dotenv:
            self._load_dotenv()
    
    def substitute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with substituted values
            
        Raises:
            InvalidConfigurationError: If required environment variable is missing
        """
        return self._substitute_recursive(config)
    
    def _substitute_recursive(self, obj: Any) -> Any:
        """Recursively substitute environment variables.
        
        Args:
            obj: Object to process
            
        Returns:
            Object with substituted values
        """
        if isinstance(obj, dict):
            return {k: self._substitute_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_string(obj)
        else:
            return obj
    
    def _substitute_string(self, value: str) -> str:
        """Substitute environment variables in string value.
        
        Args:
            value: String value to process
            
        Returns:
            String with substituted values
            
        Raises:
            InvalidConfigurationError: If required environment variable is missing
        """
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2)
            
            env_value = os.getenv(var_name)
            
            if env_value is not None:
                self.logger.debug(f"Substituted ${{{var_name}}} with environment value")
                return env_value
            elif default_value is not None:
                self.logger.debug(f"Used default value for ${{{var_name}}}")
                return default_value
            else:
                raise InvalidConfigurationError(
                    config_key=f"${{{var_name}}}",
                    invalid_value="undefined",
                    expected_type_or_values="environment variable or default value"
                )
        
        return self.ENV_VAR_PATTERN.sub(replace_var, value)
    
    def _load_dotenv(self) -> None:
        """Load environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            if key not in os.environ:
                                os.environ[key] = value
                
                self.logger.info("Loaded environment variables from .env file")
            except Exception as e:
                self.logger.warning(f"Failed to load .env file: {e}")
```

### 3.4 設定バリデーター (validator.py)

```python
"""Configuration validation for PGSD application."""

import logging
from typing import Dict, Any, List
from pathlib import Path

from .schema import PGSDConfiguration, DatabaseConfig, OutputConfig
from ..exceptions.config import InvalidConfigurationError


class ConfigurationValidator:
    """Validates PGSD configuration."""
    
    def __init__(self):
        """Initialize configuration validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate(self, config_dict: Dict[str, Any]) -> PGSDConfiguration:
        """Validate configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary to validate
            
        Returns:
            Validated configuration object
            
        Raises:
            InvalidConfigurationError: If validation fails
        """
        try:
            # Create configuration object (this handles basic validation)
            config = PGSDConfiguration(**config_dict)
            
            # Perform additional business logic validation
            self._validate_database_connectivity(config.source_db, "source")
            self._validate_database_connectivity(config.target_db, "target")
            self._validate_output_config(config.output)
            self._validate_cross_references(config)
            
            self.logger.info("Configuration validation passed")
            return config
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise InvalidConfigurationError(
                config_key="configuration",
                invalid_value=str(config_dict),
                expected_type_or_values="valid PGSD configuration"
            ) from e
    
    def _validate_database_connectivity(
        self, 
        db_config: DatabaseConfig, 
        db_name: str
    ) -> None:
        """Validate database configuration.
        
        Args:
            db_config: Database configuration to validate
            db_name: Name of database (for error messages)
            
        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Check required fields
        if not db_config.host:
            raise InvalidConfigurationError(
                config_key=f"{db_name}_db.host",
                invalid_value="",
                expected_type_or_values="non-empty string"
            )
        
        if not db_config.database:
            raise InvalidConfigurationError(
                config_key=f"{db_name}_db.database",
                invalid_value="",
                expected_type_or_values="non-empty string"
            )
        
        if not db_config.username:
            raise InvalidConfigurationError(
                config_key=f"{db_name}_db.username",
                invalid_value="",
                expected_type_or_values="non-empty string"
            )
        
        # Validate port range
        if not (1 <= db_config.port <= 65535):
            raise InvalidConfigurationError(
                config_key=f"{db_name}_db.port",
                invalid_value=db_config.port,
                expected_type_or_values="1-65535"
            )
        
        # Validate timeout
        if db_config.connection_timeout < 1:
            raise InvalidConfigurationError(
                config_key=f"{db_name}_db.connection_timeout",
                invalid_value=db_config.connection_timeout,
                expected_type_or_values="positive integer"
            )
    
    def _validate_output_config(self, output_config: OutputConfig) -> None:
        """Validate output configuration.
        
        Args:
            output_config: Output configuration to validate
            
        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Check output directory
        output_path = Path(output_config.path)
        
        # Create directory if it doesn't exist
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise InvalidConfigurationError(
                config_key="output.path",
                invalid_value=output_config.path,
                expected_type_or_values="writable directory path"
            ) from e
        
        # Check if directory is writable
        if not os.access(output_path, os.W_OK):
            raise InvalidConfigurationError(
                config_key="output.path",
                invalid_value=output_config.path,
                expected_type_or_values="writable directory"
            )
    
    def _validate_cross_references(self, config: PGSDConfiguration) -> None:
        """Validate cross-references and business rules.
        
        Args:
            config: Configuration to validate
            
        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Ensure source and target databases are different
        if (config.source_db.host == config.target_db.host and
            config.source_db.port == config.target_db.port and
            config.source_db.database == config.target_db.database and
            config.source_db.schema == config.target_db.schema):
            
            raise InvalidConfigurationError(
                config_key="database_configuration",
                invalid_value="source and target are identical",
                expected_type_or_values="different source and target databases"
            )
        
        # Validate system limits
        if config.system.max_connections > 20:
            self.logger.warning(
                f"High max_connections ({config.system.max_connections}) may impact performance"
            )
```

### 3.5 設定パーサー群 (parsers.py)

```python
"""Configuration parsers for different sources."""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..exceptions.config import ConfigurationError


class YAMLParser:
    """Parser for YAML configuration files."""
    
    def __init__(self):
        """Initialize YAML parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse YAML configuration file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            self.logger.debug(f"Parsed YAML configuration from {file_path}")
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {file_path}: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to read {file_path}: {e}") from e


class EnvironmentParser:
    """Parser for environment variable configuration."""
    
    def __init__(self, prefix: str = "PGSD_"):
        """Initialize environment parser.
        
        Args:
            prefix: Environment variable prefix
        """
        self.prefix = prefix
        self.logger = logging.getLogger(__name__)
    
    def parse(self) -> Dict[str, Any]:
        """Parse environment variables.
        
        Returns:
            Configuration dictionary from environment variables
        """
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix):].lower()
                nested_key = self._convert_env_key(config_key)
                self._set_nested_value(config, nested_key, value)
        
        self.logger.debug(f"Parsed {len(config)} environment variables")
        return config
    
    def _convert_env_key(self, env_key: str) -> str:
        """Convert environment key to nested configuration key.
        
        Args:
            env_key: Environment variable key (without prefix)
            
        Returns:
            Nested configuration key
        """
        # Convert SOURCE_DB_HOST to source_db.host
        return env_key.replace('_', '.').lower()
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: str) -> None:
        """Set nested value in configuration dictionary.
        
        Args:
            config: Configuration dictionary
            key: Nested key (e.g., "source_db.host")
            value: Value to set
        """
        keys = key.split('.')
        current = config
        
        for key_part in keys[:-1]:
            if key_part not in current:
                current[key_part] = {}
            current = current[key_part]
        
        # Convert value types
        final_value = self._convert_value_type(value)
        current[keys[-1]] = final_value
    
    def _convert_value_type(self, value: str) -> Any:
        """Convert string value to appropriate type.
        
        Args:
            value: String value
            
        Returns:
            Converted value
        """
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value


class CLIParser:
    """Parser for CLI argument configuration."""
    
    def __init__(self):
        """Initialize CLI parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse(self, cli_args: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CLI arguments.
        
        Args:
            cli_args: CLI arguments dictionary
            
        Returns:
            Configuration dictionary from CLI arguments
        """
        config = {}
        
        # Map CLI arguments to configuration keys
        cli_mapping = {
            'source_host': 'source_db.host',
            'source_port': 'source_db.port',
            'source_database': 'source_db.database',
            'source_username': 'source_db.username',
            'source_password': 'source_db.password',
            'source_schema': 'source_db.schema',
            'target_host': 'target_db.host',
            'target_port': 'target_db.port',
            'target_database': 'target_db.database',
            'target_username': 'target_db.username',
            'target_password': 'target_db.password',
            'target_schema': 'target_db.schema',
            'output_format': 'output.format',
            'output_path': 'output.path',
            'log_level': 'system.log_level',
        }
        
        for cli_key, config_key in cli_mapping.items():
            if cli_key in cli_args and cli_args[cli_key] is not None:
                self._set_nested_value(config, config_key, cli_args[cli_key])
        
        self.logger.debug(f"Parsed {len(config)} CLI arguments")
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested value in configuration dictionary.
        
        Args:
            config: Configuration dictionary
            key: Nested key (e.g., "source_db.host")
            value: Value to set
        """
        keys = key.split('.')
        current = config
        
        for key_part in keys[:-1]:
            if key_part not in current:
                current[key_part] = {}
            current = current[key_part]
        
        current[keys[-1]] = value
```

### 3.6 設定エクスポート (__init__.py)

```python
"""Configuration management module for PGSD application."""

from .manager import ConfigurationManager
from .schema import (
    PGSDConfiguration, DatabaseConfig, OutputConfig, 
    ComparisonConfig, SystemConfig, PostgreSQLConfig,
    OutputFormat, LogLevel, SSLMode
)
from .validator import ConfigurationValidator
from .substitutor import EnvironmentSubstitutor

__all__ = [
    "ConfigurationManager",
    "PGSDConfiguration",
    "DatabaseConfig", 
    "OutputConfig",
    "ComparisonConfig",
    "SystemConfig", 
    "PostgreSQLConfig",
    "OutputFormat",
    "LogLevel",
    "SSLMode",
    "ConfigurationValidator",
    "EnvironmentSubstitutor",
]
```

## 4. サンプル設定ファイル

### 4.1 pgsd_config.yaml
```yaml
# PGSD Configuration File
# PostgreSQL Schema Diff Tool Configuration

database:
  source:
    host: "localhost"
    port: 5432
    database: "production_db"
    username: "readonly_user"
    password: "${PGSD_SOURCE_PASSWORD}"
    schema: "public"
    connection_timeout: 30
    ssl_mode: "prefer"
  
  target:
    host: "localhost"
    port: 5432
    database: "development_db"
    username: "readonly_user"
    password: "${PGSD_TARGET_PASSWORD}"
    schema: "public"
    connection_timeout: 30
    ssl_mode: "prefer"

output:
  format: "html"
  path: "./reports/"
  filename_template: "schema_diff_{timestamp}"
  include_timestamp: true
  timestamp_format: "%Y%m%d_%H%M%S"
  open_browser: false

comparison:
  include_views: true
  include_functions: true
  include_constraints: true
  include_indexes: true
  include_triggers: true
  ignore_case: false
  exclude_tables:
    - "temp_*"
    - "log_*"
    - "_migration_*"
  exclude_columns:
    - "created_at"
    - "updated_at"
  max_diff_items: 1000

system:
  timezone: "UTC"
  log_level: "INFO"
  log_file: "pgsd.log"
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_connections: 5
  temp_directory: "/tmp"
  worker_threads: 4
  memory_limit_mb: 1024

postgresql:
  minimum_version: "13.0"
  version_check: true
  compatibility_mode: "strict"
  max_identifier_length: 63
  case_sensitive_identifiers: false
```

### 4.2 .env.example
```bash
# PGSD Environment Variables Example
# Copy this file to .env and set your values

# Source Database Credentials
PGSD_SOURCE_PASSWORD=your_source_password_here
PGSD_SOURCE_HOST=localhost
PGSD_SOURCE_PORT=5432
PGSD_SOURCE_DATABASE=production_db
PGSD_SOURCE_USERNAME=readonly_user
PGSD_SOURCE_SCHEMA=public

# Target Database Credentials  
PGSD_TARGET_PASSWORD=your_target_password_here
PGSD_TARGET_HOST=localhost
PGSD_TARGET_PORT=5432
PGSD_TARGET_DATABASE=development_db
PGSD_TARGET_USERNAME=readonly_user
PGSD_TARGET_SCHEMA=public

# System Configuration
PGSD_SYSTEM_LOG_LEVEL=INFO
PGSD_SYSTEM_LOG_FILE=pgsd.log
PGSD_SYSTEM_MAX_CONNECTIONS=5

# Output Configuration
PGSD_OUTPUT_FORMAT=html
PGSD_OUTPUT_PATH=./reports/
```

---

この詳細設計に基づいて実装を進める。