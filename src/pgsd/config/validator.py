"""Configuration validation for PGSD application."""

import os
import logging
from typing import Dict, Any, List
from pathlib import Path

from .schema import (
    PGSDConfiguration,
    DatabaseConfig,
    OutputConfig,
    SystemConfig,
    ComparisonConfig,
    PostgreSQLConfig,
    OutputFormat,
    LogLevel,
    SSLMode,
)
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
            # Normalize and convert enum values
            normalized_config = self._normalize_config(config_dict)

            # Create configuration object (this handles basic validation)
            config = PGSDConfiguration(**normalized_config)

            # Perform additional business logic validation
            self._validate_database_connectivity(config.source_db, "source_db")
            self._validate_database_connectivity(config.target_db, "target_db")
            self._validate_output_config(config.output)
            self._validate_system_config(config.system)
            self._validate_cross_references(config)

            self.logger.info("Configuration validation passed")
            return config

        except ValueError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise InvalidConfigurationError(
                config_key="configuration",
                invalid_value=str(e),
                expected_type_or_values="valid PGSD configuration",
            ) from e
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}")
            raise InvalidConfigurationError(
                config_key="configuration",
                invalid_value="validation_error",
                expected_type_or_values="valid configuration format",
            ) from e

    def _normalize_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize configuration values, converting strings to enums where needed.

        Args:
            config_dict: Raw configuration dictionary

        Returns:
            Normalized configuration dictionary with proper objects
        """
        normalized = {}

        for section_name, section_data in config_dict.items():
            if not isinstance(section_data, dict):
                normalized[section_name] = section_data
                continue

            if section_name == "source_db":
                # Create DatabaseConfig object for source database
                normalized_section = self._normalize_db_config(section_data)
                normalized[section_name] = DatabaseConfig(**normalized_section)
            elif section_name == "target_db":
                # Create DatabaseConfig object for target database
                normalized_section = self._normalize_db_config(section_data)
                normalized[section_name] = DatabaseConfig(**normalized_section)
            elif section_name == "output":
                # Create OutputConfig object
                normalized_section = self._normalize_output_config(section_data)
                normalized[section_name] = OutputConfig(**normalized_section)
            elif section_name == "system":
                # Create SystemConfig object
                normalized_section = self._normalize_system_config(section_data)
                normalized[section_name] = SystemConfig(**normalized_section)
            elif section_name == "comparison":
                # Create ComparisonConfig object
                normalized[section_name] = ComparisonConfig(**section_data)
            elif section_name == "postgresql":
                # Create PostgreSQLConfig object
                normalized[section_name] = PostgreSQLConfig(**section_data)
            else:
                # For other sections, just pass through
                normalized[section_name] = section_data

        return normalized

    def _normalize_db_config(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize database configuration.
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            Normalized database configuration
        """
        normalized = {}
        for key, value in db_config.items():
            if key == "ssl_mode":
                # Convert SSL mode string to enum
                normalized[key] = self._convert_to_enum(
                    value, SSLMode, f"database.{key}"
                )
            else:
                normalized[key] = value
        return normalized

    def _normalize_output_config(self, output_config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize output configuration.
        
        Args:
            output_config: Output configuration dictionary
            
        Returns:
            Normalized output configuration
        """
        normalized = {}
        for key, value in output_config.items():
            if key == "format":
                # Convert output format string to enum
                normalized[key] = self._convert_to_enum(
                    value, OutputFormat, f"output.{key}"
                )
            else:
                normalized[key] = value
        return normalized

    def _normalize_system_config(self, system_config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize system configuration.
        
        Args:
            system_config: System configuration dictionary
            
        Returns:
            Normalized system configuration
        """
        normalized = {}
        for key, value in system_config.items():
            if key == "log_level":
                # Convert log level string to enum
                normalized[key] = self._convert_to_enum(
                    value, LogLevel, f"system.{key}"
                )
            else:
                normalized[key] = value
        return normalized

    def _convert_to_enum(self, value: Any, enum_class: type, config_key: str):
        """Convert string value to enum.

        Args:
            value: Value to convert
            enum_class: Enum class to convert to
            config_key: Configuration key for error reporting

        Returns:
            Enum value

        Raises:
            InvalidConfigurationError: If conversion fails
        """
        if isinstance(value, enum_class):
            return value

        if isinstance(value, str):
            try:
                # Try to find enum by value
                for enum_member in enum_class:
                    if enum_member.value.lower() == value.lower():
                        return enum_member

                # If not found, raise error with valid options
                valid_values = [member.value for member in enum_class]
                raise InvalidConfigurationError(
                    config_key=config_key,
                    invalid_value=value,
                    expected_type_or_values=f"one of: {', '.join(valid_values)}",
                )
            except Exception as e:
                valid_values = [member.value for member in enum_class]
                raise InvalidConfigurationError(
                    config_key=config_key,
                    invalid_value=value,
                    expected_type_or_values=f"one of: {', '.join(valid_values)}",
                ) from e
        else:
            raise InvalidConfigurationError(
                config_key=config_key,
                invalid_value=value,
                expected_type_or_values=f"string value for {enum_class.__name__}",
            )

    def _validate_database_connectivity(
        self, db_config: DatabaseConfig, db_name: str
    ) -> None:
        """Validate database configuration.

        Args:
            db_config: Database configuration to validate
            db_name: Name of database (for error messages)

        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Check required fields
        if not db_config.host.strip():
            raise InvalidConfigurationError(
                config_key=f"{db_name}.host",
                invalid_value=db_config.host,
                expected_type_or_values="non-empty string",
            )

        if not db_config.database.strip():
            raise InvalidConfigurationError(
                config_key=f"{db_name}.database",
                invalid_value=db_config.database,
                expected_type_or_values="non-empty string",
            )

        if not db_config.username.strip():
            raise InvalidConfigurationError(
                config_key=f"{db_name}.username",
                invalid_value=db_config.username,
                expected_type_or_values="non-empty string",
            )

        # Validate port range
        if not (1 <= db_config.port <= 65535):
            raise InvalidConfigurationError(
                config_key=f"{db_name}.port",
                invalid_value=db_config.port,
                expected_type_or_values="1-65535",
            )

        # Validate timeout
        if db_config.connection_timeout < 1:
            raise InvalidConfigurationError(
                config_key=f"{db_name}.connection_timeout",
                invalid_value=db_config.connection_timeout,
                expected_type_or_values="positive integer",
            )

        # Validate SSL certificate files if specified
        if db_config.ssl_cert and not Path(db_config.ssl_cert).exists():
            self.logger.warning(f"SSL certificate file not found: {db_config.ssl_cert}")

        if db_config.ssl_key and not Path(db_config.ssl_key).exists():
            self.logger.warning(f"SSL key file not found: {db_config.ssl_key}")

        if db_config.ssl_ca and not Path(db_config.ssl_ca).exists():
            self.logger.warning(f"SSL CA file not found: {db_config.ssl_ca}")

    def _validate_output_config(self, output_config: OutputConfig) -> None:
        """Validate output configuration.

        Args:
            output_config: Output configuration to validate

        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Check output directory
        output_path = Path(output_config.path).expanduser()

        # Create directory if it doesn't exist
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise InvalidConfigurationError(
                config_key="output.path",
                invalid_value=output_config.path,
                expected_type_or_values="writable directory path",
            ) from e
        except Exception as e:
            raise InvalidConfigurationError(
                config_key="output.path",
                invalid_value=output_config.path,
                expected_type_or_values="valid directory path",
            ) from e

        # Check if directory is writable
        if not os.access(output_path, os.W_OK):
            raise InvalidConfigurationError(
                config_key="output.path",
                invalid_value=output_config.path,
                expected_type_or_values="writable directory",
            )

        # Validate filename template
        if not output_config.filename_template.strip():
            raise InvalidConfigurationError(
                config_key="output.filename_template",
                invalid_value=output_config.filename_template,
                expected_type_or_values="non-empty filename template",
            )

        # Check timestamp format if used
        if output_config.include_timestamp:
            try:
                from datetime import datetime

                # Test the timestamp format
                datetime.now().strftime(output_config.timestamp_format)
            except ValueError as e:
                raise InvalidConfigurationError(
                    config_key="output.timestamp_format",
                    invalid_value=output_config.timestamp_format,
                    expected_type_or_values="valid strftime format",
                ) from e

    def _validate_system_config(self, system_config) -> None:
        """Validate system configuration.

        Args:
            system_config: System configuration to validate

        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Validate temp directory
        temp_path = Path(system_config.temp_directory).expanduser()

        # Check if temp directory exists and is writable
        try:
            temp_path.mkdir(parents=True, exist_ok=True)
            if not os.access(temp_path, os.W_OK):
                raise InvalidConfigurationError(
                    config_key="system.temp_directory",
                    invalid_value=system_config.temp_directory,
                    expected_type_or_values="writable directory",
                )
        except Exception as e:
            self.logger.warning(f"Cannot validate temp directory: {e}")

        # Validate resource limits
        if system_config.worker_threads > 32:
            self.logger.warning(
                f"High worker_threads ({system_config.worker_threads}) "
                f"may impact performance"
            )

        if system_config.memory_limit_mb > 8192:
            self.logger.warning(
                f"High memory_limit_mb ({system_config.memory_limit_mb}) "
                f"may impact system performance"
            )

        if system_config.max_connections > 50:
            self.logger.warning(
                f"High max_connections ({system_config.max_connections}) "
                f"may impact database performance"
            )

    def _validate_cross_references(self, config: PGSDConfiguration) -> None:
        """Validate cross-references and business rules.

        Args:
            config: Configuration to validate

        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Ensure source and target databases are different
        if (
            config.source_db.host == config.target_db.host
            and config.source_db.port == config.target_db.port
            and config.source_db.database == config.target_db.database
            and config.source_db.schema == config.target_db.schema
        ):

            raise InvalidConfigurationError(
                config_key="database_configuration",
                invalid_value="source and target are identical",
                expected_type_or_values="different source and target databases",
            )

        # Check if both databases use the same credentials (potential issue)
        if (
            config.source_db.host == config.target_db.host
            and config.source_db.port == config.target_db.port
            and config.source_db.username == config.target_db.username
            and config.source_db.password == config.target_db.password
        ):

            self.logger.info("Source and target databases use same credentials")

        # Validate comparison limits
        if config.comparison.max_diff_items > 10000:
            self.logger.warning(
                f"Large max_diff_items ({config.comparison.max_diff_items}) "
                f"may impact performance"
            )

        # Check for conflicting exclusion patterns
        if config.comparison.exclude_tables:
            for pattern in config.comparison.exclude_tables:
                if not pattern.strip():
                    self.logger.warning("Empty table exclusion pattern found")

        if config.comparison.exclude_columns:
            for pattern in config.comparison.exclude_columns:
                if not pattern.strip():
                    self.logger.warning("Empty column exclusion pattern found")

    def validate_runtime_requirements(self, config: PGSDConfiguration) -> List[str]:
        """Validate runtime requirements and return warnings.

        Args:
            config: Configuration to validate

        Returns:
            List of warning messages
        """
        warnings = []

        # Check available disk space
        try:
            output_path = Path(config.output.path)
            stat = os.statvfs(output_path.parent)
            free_space_mb = (stat.f_frsize * stat.f_bavail) / (1024 * 1024)

            if free_space_mb < 100:  # Less than 100MB
                warnings.append(
                    f"Low disk space in output directory: "
                    f"{free_space_mb:.1f}MB available"
                )
        except Exception:
            warnings.append("Could not check disk space for output directory")

        # Check memory requirements
        try:
            import psutil

            available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
        except ImportError:
            warnings.append("psutil not available - cannot check memory usage")
            return warnings

        if config.system.memory_limit_mb > available_memory_mb * 0.8:
            warnings.append(
                f"Memory limit ({config.system.memory_limit_mb}MB) may exceed "
                f"available memory ({available_memory_mb:.0f}MB)"
            )

        return warnings
