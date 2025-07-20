"""Tests for log_config utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from tempfile import TemporaryDirectory

from src.pgsd.utils.log_config import (
    LogConfig,
    get_default_config,
    get_production_config,
    get_test_config
)


class TestLogConfig:
    """Test cases for LogConfig class."""

    def test_log_config_init_defaults(self):
        """Test LogConfig initialization with defaults."""
        config = LogConfig()
        
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.console_output is True
        assert config.file_path is None
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.backup_count == 5

    def test_log_config_init_custom(self):
        """Test LogConfig initialization with custom values."""
        with TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            config = LogConfig(
                level="DEBUG",
                format="json",
                console_output=False,
                file_path=log_file,
                max_file_size=1024,
                backup_count=3
            )
            
            assert config.level == "DEBUG"
            assert config.format == "json"
            assert config.console_output is False
            assert config.file_path == log_file
            assert config.max_file_size == 1024
            assert config.backup_count == 3

    def test_log_config_str_representation(self):
        """Test LogConfig string representation."""
        config = LogConfig(level="WARNING", format="json")
        str_repr = str(config)
        
        assert "WARNING" in str_repr
        assert "json" in str_repr
        assert "LogConfig" in str_repr

    def test_log_config_repr_representation(self):
        """Test LogConfig repr representation."""
        config = LogConfig(level="ERROR", format="console")
        repr_str = repr(config)
        
        assert "LogConfig" in repr_str
        assert "level='ERROR'" in repr_str
        assert "format='console'" in repr_str

    def test_log_config_equality(self):
        """Test LogConfig equality comparison."""
        config1 = LogConfig(level="INFO", format="console")
        config2 = LogConfig(level="INFO", format="console")
        config3 = LogConfig(level="DEBUG", format="console")
        
        assert config1 == config2
        assert config1 != config3
        assert config1 != "not a config"

    def test_log_config_file_path_as_string(self):
        """Test LogConfig with file_path as string."""
        config = LogConfig(file_path="/tmp/test.log")
        
        assert isinstance(config.file_path, Path)
        assert str(config.file_path) == "/tmp/test.log"

    def test_log_config_file_path_as_path(self):
        """Test LogConfig with file_path as Path object."""
        path_obj = Path("/tmp/test.log")
        config = LogConfig(file_path=path_obj)
        
        assert config.file_path == path_obj
        assert isinstance(config.file_path, Path)


class TestLogConfigFromDict:
    """Test cases for LogConfig.from_dict method."""

    def test_from_dict_empty(self):
        """Test creating config from empty dictionary."""
        config = LogConfig.from_dict({})
        
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.console_output is True
        assert config.file_path is None

    def test_from_dict_partial(self):
        """Test creating config from partial dictionary."""
        data = {
            "level": "DEBUG",
            "format": "console"
        }
        config = LogConfig.from_dict(data)
        
        assert config.level == "DEBUG"
        assert config.format == "console"
        assert config.console_output is True  # default
        assert config.file_path is None  # default

    def test_from_dict_complete(self):
        """Test creating config from complete dictionary."""
        data = {
            "level": "WARNING",
            "format": "json",
            "console_output": False,
            "file_path": "/tmp/test.log",
            "max_file_size": 2048,
            "backup_count": 10
        }
        config = LogConfig.from_dict(data)
        
        assert config.level == "WARNING"
        assert config.format == "json"
        assert config.console_output is False
        assert config.file_path == Path("/tmp/test.log")
        assert config.max_file_size == 2048
        assert config.backup_count == 10

    def test_from_dict_invalid_level(self):
        """Test creating config with invalid log level."""
        data = {"level": "INVALID"}
        
        with pytest.raises(ValueError, match="Invalid log level"):
            LogConfig.from_dict(data)

    def test_from_dict_invalid_format(self):
        """Test creating config with invalid format."""
        data = {"format": "invalid"}
        
        with pytest.raises(ValueError, match="Invalid format"):
            LogConfig.from_dict(data)

    def test_from_dict_nested_logging(self):
        """Test creating config from nested logging configuration."""
        data = {
            "logging": {
                "level": "DEBUG",
                "format": "console"
            }
        }
        config = LogConfig.from_dict(data)
        
        assert config.level == "DEBUG"
        assert config.format == "console"

    def test_from_dict_file_config(self):
        """Test creating config with file configuration."""
        data = {
            "level": "INFO",
            "file": {
                "path": "/tmp/test.log",
                "max_size": "1MB",
                "backup_count": 5
            }
        }
        config = LogConfig.from_dict(data)
        
        assert config.file_path == Path("/tmp/test.log")
        assert config.max_file_size == 1024 * 1024
        assert config.backup_count == 5


class TestGetDefaultConfig:
    """Test cases for get_default_config function."""

    def test_get_default_config_basic(self):
        """Test getting default config."""
        config = get_default_config()
        
        assert isinstance(config, LogConfig)
        assert config.level == "INFO"
        assert config.format == "console"
        assert config.console_output is True

    def test_get_production_config(self):
        """Test getting production config."""
        config = get_production_config()
        
        assert isinstance(config, LogConfig)
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.console_output is False
        assert config.file_path == Path("logs/pgsd.log")

    def test_get_test_config(self):
        """Test getting test config."""
        config = get_test_config()
        
        assert isinstance(config, LogConfig)
        assert config.level == "WARNING"
        assert config.format == "console"
        assert config.console_output is False
        assert config.file_path is None

    def test_config_from_environment(self):
        """Test config from environment variables."""
        with patch.dict('os.environ', {'PGSD_LOG_LEVEL': 'DEBUG'}):
            config = LogConfig.from_environment()
            assert config.level == "DEBUG"

    def test_config_from_environment_console(self):
        """Test config from environment with console setting."""
        with patch.dict('os.environ', {'PGSD_LOG_CONSOLE': 'false'}):
            config = LogConfig.from_environment()
            assert config.console_output is False

    def test_config_from_environment_file(self):
        """Test config from environment with file path."""
        with patch.dict('os.environ', {'PGSD_LOG_FILE': '/tmp/test.log'}):
            config = LogConfig.from_environment()
            assert config.file_path == Path("/tmp/test.log")

    def test_config_parse_size_mb(self):
        """Test size parsing with MB."""
        size = LogConfig._parse_size("10MB")
        assert size == 10 * 1024 * 1024

    def test_config_parse_size_kb(self):
        """Test size parsing with KB."""
        size = LogConfig._parse_size("512KB")
        assert size == 512 * 1024

    def test_config_parse_size_bytes(self):
        """Test size parsing with bytes."""
        size = LogConfig._parse_size("1024")
        assert size == 1024

    def test_config_parse_size_invalid(self):
        """Test size parsing with invalid format."""
        with pytest.raises(ValueError, match="Invalid size format"):
            LogConfig._parse_size("invalid")


class TestLogConfigIntegration:
    """Integration tests for log config module."""

    def test_config_round_trip(self):
        """Test creating config, converting to dict, and back."""
        original_config = LogConfig(
            level="DEBUG",
            format="json",
            console_output=False,
            file_path=Path("/tmp/test.log"),
            max_file_size=1024,
            backup_count=3
        )
        
        # Convert to dict and back
        config_dict = original_config.to_dict()
        new_config = LogConfig.from_dict(config_dict)
        
        assert new_config.level == original_config.level
        assert new_config.format == original_config.format
        assert new_config.console_output == original_config.console_output
        assert new_config.file_path == original_config.file_path
        assert new_config.max_file_size == original_config.max_file_size
        assert new_config.backup_count == original_config.backup_count

    def test_default_config_consistency(self):
        """Test that default config is consistent across calls."""
        config1 = get_default_config()
        config2 = get_default_config()
        
        # Should be same values
        assert config1.level == config2.level
        assert config1.format == config2.format
        assert config1.console_output == config2.console_output

    def test_validate_log_level_with_config(self):
        """Test log level validation in config creation."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LogConfig(level=level)
            assert config.level == level

    def test_path_handling_consistency(self):
        """Test consistent path handling across the module."""
        test_path = "/tmp/test.log"
        
        # Test with string
        config1 = LogConfig(file_path=test_path)
        
        # Test with Path object
        config2 = LogConfig(file_path=Path(test_path))
        
        # Test with dict creation
        config3 = LogConfig.from_dict({"file_path": test_path})
        
        assert config1.file_path == config2.file_path == config3.file_path
        assert all(isinstance(c.file_path, Path) for c in [config1, config2, config3])

    def test_config_validation_errors(self):
        """Test configuration validation errors."""
        # Test invalid log level
        with pytest.raises(ValueError, match="Invalid log level"):
            LogConfig(level="INVALID")

        # Test invalid format
        with pytest.raises(ValueError, match="Invalid format"):
            LogConfig(format="invalid")

        # Test invalid file size
        with pytest.raises(ValueError, match="max_file_size must be positive"):
            LogConfig(max_file_size=0)

        # Test invalid backup count
        with pytest.raises(ValueError, match="backup_count must be non-negative"):
            LogConfig(backup_count=-1)

    def test_yaml_file_functionality(self):
        """Test YAML file loading functionality."""
        from tempfile import NamedTemporaryFile
        import yaml
        
        config_data = {
            "level": "DEBUG",
            "format": "json",
            "console_output": False,
            "file_path": "/tmp/test.log"
        }
        
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            yaml_path = Path(f.name)
        
        try:
            config = LogConfig.from_yaml_file(yaml_path)
            assert config.level == "DEBUG"
            assert config.format == "json"
            assert config.console_output is False
            assert config.file_path == Path("/tmp/test.log")
        finally:
            yaml_path.unlink()

    def test_yaml_file_not_found(self):
        """Test YAML file loading with non-existent file."""
        non_existent_path = Path("/non/existent/file.yaml")
        
        with pytest.raises(FileNotFoundError):
            LogConfig.from_yaml_file(non_existent_path)