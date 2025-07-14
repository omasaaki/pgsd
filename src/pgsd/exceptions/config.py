"""Configuration-related exception classes."""

from typing import Any, List, Optional
from pathlib import Path

from .base import PGSDError, ErrorSeverity, ErrorCategory


class ConfigurationError(PGSDError):
    """Base class for configuration-related errors."""

    default_error_code = "CONFIGURATION_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_category = ErrorCategory.CONFIGURATION
    default_exit_code = 20
    retriable = False


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration contains invalid values."""

    default_error_code = "INVALID_CONFIGURATION"
    default_exit_code = 21

    def __init__(
        self,
        config_key: str,
        invalid_value: Any,
        expected_type_or_values: str,
        config_file: Optional[Path] = None,
    ) -> None:
        """Initialize invalid configuration error.

        Args:
            config_key: The configuration key with invalid value
            invalid_value: The invalid value
            expected_type_or_values: Description of expected type or valid values
            config_file: Path to configuration file (optional)
        """
        message = f"Invalid configuration value for '{config_key}': {invalid_value}. Expected: {expected_type_or_values}"

        # Technical details
        technical_details = {
            "config_key": config_key,
            "invalid_value": str(invalid_value),
            "expected": expected_type_or_values,
            "config_file": str(config_file) if config_file else None,
        }

        # Recovery suggestions
        recovery_suggestions = [
            f"Update '{config_key}' to a valid value: {expected_type_or_values}",
            "Check configuration file syntax and structure",
            "Refer to documentation for valid configuration options",
        ]

        if config_file:
            recovery_suggestions.append(f"Edit configuration file: {config_file}")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""

    default_error_code = "MISSING_CONFIGURATION"
    default_exit_code = 22

    def __init__(
        self,
        missing_keys: List[str],
        config_file: Optional[Path] = None,
        config_section: Optional[str] = None,
    ) -> None:
        """Initialize missing configuration error.

        Args:
            missing_keys: List of missing configuration keys
            config_file: Path to configuration file (optional)
            config_section: Configuration section name (optional)
        """
        if len(missing_keys) == 1:
            key_description = f"configuration key '{missing_keys[0]}'"
        else:
            keys_str = "', '".join(missing_keys)
            key_description = f"configuration keys: '{keys_str}'"

        if config_section:
            message = (
                f"Missing required {key_description} in section '{config_section}'"
            )
        else:
            message = f"Missing required {key_description}"

        # Technical details
        technical_details = {
            "missing_keys": missing_keys,
            "config_file": str(config_file) if config_file else None,
            "config_section": config_section,
        }

        # Recovery suggestions
        recovery_suggestions = [
            f"Add missing configuration keys: {', '.join(missing_keys)}",
            "Check configuration file completeness",
        ]

        if config_file:
            if config_file.exists():
                recovery_suggestions.append(
                    f"Edit existing configuration file: {config_file}"
                )
            else:
                recovery_suggestions.append(f"Create configuration file: {config_file}")
        else:
            recovery_suggestions.append(
                "Create a configuration file with required settings"
            )

        if config_section:
            recovery_suggestions.append(
                f"Ensure section '[{config_section}]' exists in configuration"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )
