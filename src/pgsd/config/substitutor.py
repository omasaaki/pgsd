"""Environment variable substitution for configuration values."""

import os
import re
import logging
from typing import Any, Dict, List
from pathlib import Path

from ..exceptions.config import InvalidConfigurationError


class EnvironmentSubstitutor:
    """Handles environment variable substitution in configuration values."""

    # Pattern for ${VAR_NAME} or ${VAR_NAME:default_value}
    ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")

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
                    expected_type_or_values="environment variable or default value",
                )

        return self.ENV_VAR_PATTERN.sub(replace_var, value)

    def _load_dotenv(self) -> None:
        """Load environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip("\"'")

                            # Only set if not already in environment
                            if key not in os.environ:
                                os.environ[key] = value

                self.logger.info("Loaded environment variables from .env file")
            except Exception as e:
                self.logger.warning(f"Failed to load .env file: {e}")
        else:
            self.logger.debug("No .env file found")

    def validate_substitutions(self, config: Dict[str, Any]) -> List[str]:
        """Validate that all environment variable references can be resolved.

        Args:
            config: Configuration dictionary to validate

        Returns:
            List of missing environment variables
        """
        missing_vars = []

        def check_recursive(obj: Any, path: str = ""):
            """Recursively check for missing environment variables."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    check_recursive(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                for match in self.ENV_VAR_PATTERN.finditer(obj):
                    var_name = match.group(1)
                    default_value = match.group(2)

                    if os.getenv(var_name) is None and default_value is None:
                        missing_vars.append(f"{var_name} (referenced in {path})")

        check_recursive(config)
        return missing_vars
