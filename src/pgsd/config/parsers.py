"""Configuration parsers for different sources."""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from ..exceptions.config import ConfigurationError


class YAMLParser:
    """Parser for YAML configuration files."""
    
    def __init__(self):
        """Initialize YAML parser."""
        self.logger = logging.getLogger(__name__)
        
        if yaml is None:
            raise ConfigurationError(
                "PyYAML is required for YAML configuration support. "
                "Install with: pip install PyYAML"
            )
    
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
        env_vars_found = 0
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix):].lower()
                nested_key = self._convert_env_key(config_key)
                self._set_nested_value(config, nested_key, value)
                env_vars_found += 1
        
        self.logger.debug(f"Parsed {env_vars_found} environment variables")
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
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
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
        
        # List conversion (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',') if item.strip()]
        
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
            # Source database
            'source_host': 'source_db.host',
            'source_port': 'source_db.port',
            'source_database': 'source_db.database',
            'source_username': 'source_db.username',
            'source_password': 'source_db.password',
            'source_schema': 'source_db.schema',
            'source_ssl_mode': 'source_db.ssl_mode',
            'source_connection_timeout': 'source_db.connection_timeout',
            
            # Target database
            'target_host': 'target_db.host',
            'target_port': 'target_db.port',
            'target_database': 'target_db.database',
            'target_username': 'target_db.username',
            'target_password': 'target_db.password',
            'target_schema': 'target_db.schema',
            'target_ssl_mode': 'target_db.ssl_mode',
            'target_connection_timeout': 'target_db.connection_timeout',
            
            # Output
            'output_format': 'output.format',
            'output_path': 'output.path',
            'output_filename': 'output.filename_template',
            'open_browser': 'output.open_browser',
            
            # Comparison
            'include_views': 'comparison.include_views',
            'include_functions': 'comparison.include_functions',
            'include_constraints': 'comparison.include_constraints',
            'include_indexes': 'comparison.include_indexes',
            'include_triggers': 'comparison.include_triggers',
            'ignore_case': 'comparison.ignore_case',
            'exclude_tables': 'comparison.exclude_tables',
            'exclude_columns': 'comparison.exclude_columns',
            'max_diff_items': 'comparison.max_diff_items',
            
            # System
            'log_level': 'system.log_level',
            'log_file': 'system.log_file',
            'max_connections': 'system.max_connections',
            'temp_directory': 'system.temp_directory',
            'worker_threads': 'system.worker_threads',
            'memory_limit': 'system.memory_limit_mb',
            
            # PostgreSQL
            'minimum_version': 'postgresql.minimum_version',
            'version_check': 'postgresql.version_check',
            'compatibility_mode': 'postgresql.compatibility_mode',
        }
        
        args_processed = 0
        for cli_key, config_key in cli_mapping.items():
            if cli_key in cli_args and cli_args[cli_key] is not None:
                self._set_nested_value(config, config_key, cli_args[cli_key])
                args_processed += 1
        
        # Handle special cases
        if 'config_file' in cli_args and cli_args['config_file']:
            # This is handled by ConfigurationManager, not stored in config
            pass
        
        self.logger.debug(f"Parsed {args_processed} CLI arguments")
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