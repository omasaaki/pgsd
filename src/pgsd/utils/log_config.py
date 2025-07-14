"""Logging configuration management."""

import os
import yaml
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union
from pathlib import Path


@dataclass
class LogConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"  # json, console
    file_path: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    timezone: str = "UTC"
    enable_performance: bool = True
    console_output: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {self.level}. Must be one of {valid_levels}"
            )

        valid_formats = {"json", "console"}
        if self.format not in valid_formats:
            raise ValueError(
                f"Invalid format: {self.format}. Must be one of {valid_formats}"
            )

        if self.file_path and isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)

        if self.max_file_size <= 0:
            raise ValueError("max_file_size must be positive")

        if self.backup_count < 0:
            raise ValueError("backup_count must be non-negative")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LogConfig":
        """Create LogConfig from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            LogConfig instance
        """
        # Handle nested logging configuration
        if "logging" in config_dict:
            config_dict = config_dict["logging"]

        # Handle file configuration
        if "file" in config_dict:
            file_config = config_dict.pop("file")
            if "path" in file_config:
                config_dict["file_path"] = file_config["path"]
            if "max_size" in file_config:
                config_dict["max_file_size"] = cls._parse_size(file_config["max_size"])
            if "backup_count" in file_config:
                config_dict["backup_count"] = file_config["backup_count"]

        # Handle performance configuration
        if "performance" in config_dict:
            perf_config = config_dict.pop("performance")
            if "enabled" in perf_config:
                config_dict["enable_performance"] = perf_config["enabled"]

        # Filter known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_config = {k: v for k, v in config_dict.items() if k in known_fields}

        return cls(**filtered_config)

    @classmethod
    def from_yaml_file(cls, file_path: Path) -> "LogConfig":
        """Load LogConfig from YAML file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            LogConfig instance

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls.from_dict(config_data)

    @classmethod
    def from_environment(cls) -> "LogConfig":
        """Create LogConfig from environment variables.

        Returns:
            LogConfig instance
        """
        config_dict = {}

        if level := os.getenv("PGSD_LOG_LEVEL"):
            config_dict["level"] = level

        if format_type := os.getenv("PGSD_LOG_FORMAT"):
            config_dict["format"] = format_type

        if file_path := os.getenv("PGSD_LOG_FILE"):
            config_dict["file_path"] = file_path

        if console_output := os.getenv("PGSD_LOG_CONSOLE"):
            config_dict["console_output"] = console_output.lower() in (
                "true",
                "1",
                "yes",
            )

        return cls.from_dict(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert LogConfig to dictionary.

        Returns:
            Configuration dictionary
        """
        data = asdict(self)

        # Convert Path to string
        if data["file_path"]:
            data["file_path"] = str(data["file_path"])

        return data

    @staticmethod
    def _parse_size(size_str: Union[str, int]) -> int:
        """Parse size string to bytes.

        Args:
            size_str: Size string like "10MB" or integer

        Returns:
            Size in bytes
        """
        if isinstance(size_str, int):
            return size_str

        size_str = size_str.upper().strip()
        multipliers = [
            ("GB", 1024**3),
            ("MB", 1024**2),
            ("KB", 1024),
            ("B", 1),
        ]

        for suffix, multiplier in multipliers:
            if size_str.endswith(suffix):
                number_str = size_str[: -len(suffix)].strip()
                try:
                    number = float(number_str)
                    return int(number * multiplier)
                except ValueError:
                    raise ValueError(f"Invalid size format: {size_str}")

        # If no suffix, assume bytes
        try:
            return int(float(size_str))
        except ValueError:
            raise ValueError(f"Invalid size format: {size_str}")


def get_default_config() -> LogConfig:
    """Get default logging configuration.

    Returns:
        Default LogConfig instance
    """
    return LogConfig(
        level="INFO",
        format="console",  # Console format for development
        console_output=True,
        file_path=None,
        enable_performance=True,
    )


def get_production_config() -> LogConfig:
    """Get production logging configuration.

    Returns:
        Production LogConfig instance
    """
    return LogConfig(
        level="INFO",
        format="json",
        console_output=False,
        file_path=Path("logs/pgsd.log"),
        max_file_size=50 * 1024 * 1024,  # 50MB
        backup_count=10,
        enable_performance=True,
    )


def get_test_config() -> LogConfig:
    """Get test environment logging configuration.

    Returns:
        Test LogConfig instance
    """
    return LogConfig(
        level="WARNING",
        format="console",
        console_output=False,  # Suppress output during tests
        file_path=None,
        enable_performance=False,
    )
