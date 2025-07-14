"""Tests for log configuration management - Implementation."""

import pytest
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import patch

from pgsd.utils.log_config import (
    LogConfig,
    get_default_config,
    get_production_config,
    get_test_config,
)


class TestLogConfig:
    """Test LogConfig functionality."""

    def test_default_initialization(self):
        """Test default LogConfig initialization."""
        config = LogConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.console_output is True
        assert config.file_path is None
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5
        assert config.enable_performance is True

    def test_custom_initialization(self):
        """Test LogConfig with custom parameters."""
        config = LogConfig(
            level="DEBUG",
            format="console",
            file_path=Path("/tmp/test.log"),
            max_file_size=5 * 1024 * 1024,
            backup_count=3,
        )
        assert config.level == "DEBUG"
        assert config.format == "console"
        assert config.file_path == Path("/tmp/test.log")
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.backup_count == 3

    def test_validation_invalid_level(self):
        """Test validation of invalid log level."""
        with pytest.raises(ValueError, match="Invalid log level"):
            LogConfig(level="INVALID")

    def test_validation_invalid_format(self):
        """Test validation of invalid format."""
        with pytest.raises(ValueError, match="Invalid format"):
            LogConfig(format="invalid")

    def test_validation_invalid_file_size(self):
        """Test validation of invalid file size."""
        with pytest.raises(ValueError, match="max_file_size must be positive"):
            LogConfig(max_file_size=0)

        with pytest.raises(ValueError, match="max_file_size must be positive"):
            LogConfig(max_file_size=-1)

    def test_validation_invalid_backup_count(self):
        """Test validation of invalid backup count."""
        with pytest.raises(ValueError, match="backup_count must be non-negative"):
            LogConfig(backup_count=-1)

    def test_from_dict_simple(self):
        """Test LogConfig creation from dictionary."""
        config_dict = {
            "level": "DEBUG",
            "format": "console",
            "console_output": False,
            "enable_performance": False,
        }
        config = LogConfig.from_dict(config_dict)
        assert config.level == "DEBUG"
        assert config.format == "console"
        assert config.console_output is False
        assert config.enable_performance is False

    def test_from_dict_nested_logging(self):
        """Test LogConfig from dictionary with nested logging section."""
        config_dict = {"logging": {"level": "WARNING", "format": "json"}}
        config = LogConfig.from_dict(config_dict)
        assert config.level == "WARNING"
        assert config.format == "json"

    def test_from_dict_file_section(self):
        """Test LogConfig from dictionary with file section."""
        config_dict = {
            "logging": {
                "file": {"path": "/tmp/app.log", "max_size": "50MB", "backup_count": 10}
            }
        }
        config = LogConfig.from_dict(config_dict)
        assert config.file_path == Path("/tmp/app.log")
        assert config.max_file_size == 50 * 1024 * 1024
        assert config.backup_count == 10

    def test_from_dict_performance_section(self):
        """Test LogConfig from dictionary with performance section."""
        config_dict = {"logging": {"performance": {"enabled": False}}}
        config = LogConfig.from_dict(config_dict)
        assert config.enable_performance is False

    def test_from_yaml_file(self):
        """Test LogConfig from YAML file."""
        yaml_content = """
logging:
  level: "DEBUG"
  format: "console"
  file:
    path: "/tmp/test.log"
    max_size: "20MB"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = LogConfig.from_yaml_file(Path(f.name))
            assert config.level == "DEBUG"
            assert config.format == "console"
            assert config.file_path == Path("/tmp/test.log")
            assert config.max_file_size == 20 * 1024 * 1024

        os.unlink(f.name)

    def test_from_yaml_file_not_found(self):
        """Test LogConfig from non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            LogConfig.from_yaml_file(Path("/non/existent/file.yaml"))

    def test_from_yaml_file_invalid_yaml(self):
        """Test LogConfig from invalid YAML file."""
        invalid_yaml = "invalid: yaml: content: ["

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml)
            f.flush()

            with pytest.raises(yaml.YAMLError):
                LogConfig.from_yaml_file(Path(f.name))

        os.unlink(f.name)

    def test_from_environment(self):
        """Test LogConfig from environment variables."""
        with patch.dict(
            os.environ,
            {
                "PGSD_LOG_LEVEL": "WARNING",
                "PGSD_LOG_FORMAT": "console",
                "PGSD_LOG_FILE": "/tmp/env.log",
                "PGSD_LOG_CONSOLE": "false",
            },
        ):
            config = LogConfig.from_environment()
            assert config.level == "WARNING"
            assert config.format == "console"
            assert config.file_path == Path("/tmp/env.log")
            assert config.console_output is False

    def test_to_dict(self):
        """Test LogConfig conversion to dictionary."""
        config = LogConfig(
            level="DEBUG", format="json", file_path=Path("/tmp/test.log")
        )
        result = config.to_dict()

        assert result["level"] == "DEBUG"
        assert result["format"] == "json"
        assert result["file_path"] == "/tmp/test.log"
        assert isinstance(result["max_file_size"], int)

    def test_parse_size_bytes(self):
        """Test size parsing with different units."""
        assert LogConfig._parse_size("1024") == 1024
        assert LogConfig._parse_size(2048) == 2048
        assert LogConfig._parse_size("1KB") == 1024
        assert LogConfig._parse_size("1MB") == 1024 * 1024
        assert LogConfig._parse_size("1GB") == 1024 * 1024 * 1024
        assert LogConfig._parse_size("2.5MB") == int(2.5 * 1024 * 1024)


class TestLogConfigPresets:
    """Test predefined configuration presets."""

    def test_get_default_config(self):
        """Test default configuration preset."""
        config = get_default_config()
        assert config.level == "INFO"
        assert config.format == "console"
        assert config.console_output is True
        assert config.file_path is None
        assert config.enable_performance is True

    def test_get_production_config(self):
        """Test production configuration preset."""
        config = get_production_config()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.console_output is False
        assert config.file_path == Path("logs/pgsd.log")
        assert config.max_file_size == 50 * 1024 * 1024
        assert config.backup_count == 10

    def test_get_test_config(self):
        """Test test configuration preset."""
        config = get_test_config()
        assert config.level == "WARNING"
        assert config.format == "console"
        assert config.console_output is False
        assert config.file_path is None
        assert config.enable_performance is False


class TestLogConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dict(self):
        """Test LogConfig from empty dictionary."""
        config = LogConfig.from_dict({})
        # Should use defaults
        assert config.level == "INFO"
        assert config.format == "json"

    def test_partial_config(self):
        """Test LogConfig with partial configuration."""
        config_dict = {"level": "DEBUG"}
        config = LogConfig.from_dict(config_dict)
        assert config.level == "DEBUG"
        # Other fields should use defaults
        assert config.format == "json"
        assert config.console_output is True

    def test_unknown_fields_ignored(self):
        """Test that unknown fields are ignored."""
        config_dict = {
            "level": "INFO",
            "unknown_field": "should_be_ignored",
            "another_unknown": 123,
        }
        config = LogConfig.from_dict(config_dict)
        assert config.level == "INFO"
        # Should not have unknown fields
        assert not hasattr(config, "unknown_field")

    def test_string_to_path_conversion(self):
        """Test automatic string to Path conversion."""
        config = LogConfig(file_path="/tmp/test.log")
        assert isinstance(config.file_path, Path)
        assert config.file_path == Path("/tmp/test.log")
