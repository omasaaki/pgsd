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
        "./pgsd_config.yml", 
        "~/.pgsd/config.yaml",
        "~/.pgsd/config.yml",
        "/etc/pgsd/config.yaml",
        "/etc/pgsd/config.yml"
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
        self._config_sources: Dict[str, str] = {}
    
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
        self.logger.info("Loading configuration from multiple sources...")
        
        try:
            # 1. Load from file
            file_config, file_source = self._load_file_config()
            
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
            
            # 6. Store configuration sources for debugging
            self._config_sources = {
                "file": file_source or "none",
                "environment_vars": len(env_config) > 0,
                "cli_args": len(cli_args or {}) > 0
            }
            
            # 7. Log configuration summary
            self._log_configuration_summary()
            
            self.logger.info("Configuration loaded and validated successfully")
            return self._config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            if isinstance(e, (ConfigurationError, InvalidConfigurationError)):
                raise
            else:
                raise ConfigurationError(f"Unexpected error during configuration loading: {e}") from e
    
    def _load_file_config(self) -> tuple[Dict[str, Any], Optional[str]]:
        """Load configuration from YAML file.
        
        Returns:
            Tuple of (configuration dictionary, file path used)
        """
        config_path = self._find_config_file()
        if not config_path:
            self.logger.info("No configuration file found, using defaults")
            return {}, None
        
        try:
            parser = YAMLParser()
            config = parser.parse(config_path)
            self.logger.info(f"Loaded configuration from {config_path}")
            return config, str(config_path)
            
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
            path = Path(self.config_file).expanduser().resolve()
            if path.exists():
                return path
            else:
                raise MissingConfigurationError(
                    missing_keys=["config_file"],
                    config_file=path
                )
        
        # Search in default locations
        for search_path in self.CONFIG_SEARCH_PATHS:
            path = Path(search_path).expanduser().resolve()
            if path.exists():
                self.logger.debug(f"Found configuration file: {path}")
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
        config = parser.parse()
        
        if config:
            self.logger.info(f"Loaded configuration from environment variables (prefix: {prefix})")
        
        return config
    
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
        # Start with empty base (defaults will be applied by dataclass)
        merged = {}
        
        # Apply file config (lowest priority)
        if file_config:
            self._deep_update(merged, file_config)
            self.logger.debug("Applied file configuration")
        
        # Apply environment config (medium priority)
        if env_config:
            self._deep_update(merged, env_config)
            self.logger.debug("Applied environment configuration")
        
        # Apply CLI config (highest priority)
        if cli_config:
            self._deep_update(merged, cli_config)
            self.logger.debug("Applied CLI configuration")
        
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
    
    def _log_configuration_summary(self) -> None:
        """Log a summary of the loaded configuration."""
        if not self._config:
            return
        
        self.logger.info("Configuration Summary:")
        self.logger.info(f"  Source DB: {self._config.source_db.host}:{self._config.source_db.port}/{self._config.source_db.database}")
        self.logger.info(f"  Target DB: {self._config.target_db.host}:{self._config.target_db.port}/{self._config.target_db.database}")
        self.logger.info(f"  Output Format: {self._config.output.format.value}")
        self.logger.info(f"  Output Path: {self._config.output.path}")
        self.logger.info(f"  Log Level: {self._config.system.log_level.value}")
        
        # Log configuration sources
        if self._config_sources:
            sources_used = []
            if self._config_sources.get("file", "none") != "none":
                sources_used.append(f"file ({self._config_sources['file']})")
            if self._config_sources.get("environment_vars"):
                sources_used.append("environment variables")
            if self._config_sources.get("cli_args"):
                sources_used.append("CLI arguments")
            
            if sources_used:
                self.logger.info(f"  Sources: {', '.join(sources_used)}")
    
    def get_configuration(self) -> PGSDConfiguration:
        """Get current configuration.
        
        Returns:
            Current configuration object
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded. Call load_configuration() first.")
        return self._config
    
    def get_masked_configuration(self) -> Dict[str, Any]:
        """Get configuration with sensitive fields masked.
        
        Returns:
            Masked configuration dictionary
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded. Call load_configuration() first.")
        return self._config.get_masked_dict()
    
    def get_configuration_sources(self) -> Dict[str, Any]:
        """Get information about configuration sources.
        
        Returns:
            Dictionary containing source information
        """
        return self._config_sources.copy()
    
    def reload_configuration(
        self,
        cli_args: Optional[Dict[str, Any]] = None,
        env_prefix: str = "PGSD_"
    ) -> PGSDConfiguration:
        """Reload configuration from all sources.
        
        Args:
            cli_args: CLI arguments dictionary
            env_prefix: Environment variable prefix
            
        Returns:
            Reloaded configuration
        """
        self.logger.info("Reloading configuration...")
        self._config = None
        self._config_sources = {}
        return self.load_configuration(cli_args, env_prefix)
    
    def validate_environment_variables(self) -> List[str]:
        """Validate that all required environment variables are available.
        
        Returns:
            List of missing environment variables
        """
        if not self._config:
            return ["Configuration not loaded"]
        
        config_dict = self._config.get_masked_dict()
        return self.substitutor.validate_substitutions(config_dict)
    
    def create_sample_config_file(self, output_path: str) -> None:
        """Create a sample configuration file.
        
        Args:
            output_path: Path where to create the sample file
        """
        sample_config = """# PGSD Configuration File
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
"""
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sample_config)
            
            self.logger.info(f"Sample configuration file created: {output_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create sample config file: {e}") from e
    
    def create_sample_env_file(self, output_path: str) -> None:
        """Create a sample .env file.
        
        Args:
            output_path: Path where to create the sample .env file
        """
        sample_env = """# PGSD Environment Variables Example
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
"""
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sample_env)
            
            self.logger.info(f"Sample .env file created: {output_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create sample .env file: {e}") from e