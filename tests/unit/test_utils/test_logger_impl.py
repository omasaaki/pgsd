"""Tests for logger utilities - Implementation."""

import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from pgsd.utils.logger import (
    PGSDLogger,
    get_logger,
    setup_logging,
    reset_logging,
)
from pgsd.utils.log_config import LogConfig


class TestPGSDLogger:
    """Test PGSDLogger functionality."""

    def setup_method(self):
        """Setup test environment."""
        reset_logging()

    def teardown_method(self):
        """Cleanup test environment."""
        reset_logging()

    def test_logger_initialization(self):
        """Test PGSDLogger initialization."""
        logger = PGSDLogger("test.logger")
        assert logger.name == "test.logger"
        assert logger._logger is not None

    def test_debug_logging(self):
        """Test debug level logging."""
        logger = PGSDLogger("test.debug")

        with patch.object(logger._logger, "debug") as mock_debug:
            logger.debug("test event", user_id=123)
            # Check that sanitized data was passed (user_id is not sensitive)
            mock_debug.assert_called_once_with("test event", user_id=123)

    def test_info_logging(self):
        """Test info level logging."""
        logger = PGSDLogger("test.info")

        with patch.object(logger._logger, "info") as mock_info:
            logger.info("test event", data=123)
            mock_info.assert_called_once_with("test event", data=123)

    def test_warning_logging(self):
        """Test warning level logging."""
        logger = PGSDLogger("test.warning")

        with patch.object(logger._logger, "warning") as mock_warning:
            logger.warning("test event", message="warning")
            mock_warning.assert_called_once_with("test event", message="warning")

    def test_error_logging(self):
        """Test error level logging."""
        logger = PGSDLogger("test.error")

        with patch.object(logger._logger, "error") as mock_error:
            logger.error("test event", error_code=500)
            mock_error.assert_called_once_with("test event", error_code=500)

    def test_critical_logging(self):
        """Test critical level logging."""
        logger = PGSDLogger("test.critical")

        with patch.object(logger._logger, "critical") as mock_critical:
            logger.critical("test event", severity="high")
            mock_critical.assert_called_once_with("test event", severity="high")

    def test_exception_logging(self):
        """Test exception logging."""
        logger = PGSDLogger("test.exception")

        with patch.object(logger._logger, "exception") as mock_exception:
            logger.exception("test exception", context="error")
            mock_exception.assert_called_once_with("test exception", context="error")

    def test_sanitize_data_password_fields(self):
        """Test sanitization of password fields."""
        logger = PGSDLogger("test.sanitize")

        test_data = {
            "username": "user123",
            "password": "secret123",
            "api_key": "sensitive_key",
            "normal_field": "normal_value",
        }

        sanitized = logger._sanitize_data(test_data)

        assert sanitized["username"] == "user123"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["normal_field"] == "normal_value"

    def test_sanitize_data_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        logger = PGSDLogger("test.nested")

        test_data = {
            "user": {
                "name": "test_user",
                "password": "secret",
                "profile": {"email": "test@example.com", "secret_key": "nested_secret"},
            },
            "normal": "value",
        }

        sanitized = logger._sanitize_data(test_data)

        assert sanitized["user"]["name"] == "test_user"
        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["user"]["profile"]["email"] == "test@example.com"
        assert sanitized["user"]["profile"]["secret_key"] == "***REDACTED***"
        assert sanitized["normal"] == "value"

    def test_sanitize_data_various_sensitive_fields(self):
        """Test sanitization of various sensitive field patterns."""
        logger = PGSDLogger("test.sensitive")

        test_data = {
            "user_password": "secret1",
            "auth_token": "secret2",
            "private_key": "secret3",
            "credential_data": "secret4",
            "SECRET_CONFIG": "secret5",
            "normal_field": "normal",
        }

        sanitized = logger._sanitize_data(test_data)

        assert sanitized["user_password"] == "***REDACTED***"
        assert sanitized["auth_token"] == "***REDACTED***"
        assert sanitized["private_key"] == "***REDACTED***"
        assert sanitized["credential_data"] == "***REDACTED***"
        assert sanitized["SECRET_CONFIG"] == "***REDACTED***"
        assert sanitized["normal_field"] == "normal"

    def test_sanitize_data_empty_dict(self):
        """Test sanitization of empty dictionary."""
        logger = PGSDLogger("test.empty")

        sanitized = logger._sanitize_data({})
        assert sanitized == {}

    def test_sanitize_data_non_dict_values(self):
        """Test sanitization preserves non-dict values."""
        logger = PGSDLogger("test.values")

        test_data = {
            "number": 123,
            "list": [1, 2, 3],
            "string": "test",
            "boolean": True,
            "none_value": None,
        }

        sanitized = logger._sanitize_data(test_data)

        assert sanitized["number"] == 123
        assert sanitized["list"] == [1, 2, 3]
        assert sanitized["string"] == "test"
        assert sanitized["boolean"] is True
        assert sanitized["none_value"] is None


class TestLoggerRegistry:
    """Test logger registry functionality."""

    def setup_method(self):
        """Setup test environment."""
        reset_logging()

    def teardown_method(self):
        """Cleanup test environment."""
        reset_logging()

    def test_get_logger_singleton(self):
        """Test get_logger returns same instance for same name."""
        logger1 = get_logger("test.singleton")
        logger2 = get_logger("test.singleton")

        assert logger1 is logger2
        assert logger1.name == "test.singleton"

    def test_get_logger_different_names(self):
        """Test get_logger returns different instances for different names."""
        logger1 = get_logger("test.logger1")
        logger2 = get_logger("test.logger2")

        assert logger1 is not logger2
        assert logger1.name == "test.logger1"
        assert logger2.name == "test.logger2"

    def test_get_logger_auto_setup(self):
        """Test get_logger automatically sets up logging."""
        # Ensure logging is not configured
        reset_logging()

        # Get logger should trigger setup
        logger = get_logger("test.autosetup")

        assert logger is not None
        # Check that setup was called by verifying root logger has handlers
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0


class TestLoggingSetup:
    """Test logging setup functionality."""

    def setup_method(self):
        """Setup test environment."""
        reset_logging()

    def teardown_method(self):
        """Cleanup test environment."""
        reset_logging()

    def test_setup_logging_default_config(self):
        """Test setup_logging with default configuration."""
        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0

    def test_setup_logging_custom_config(self):
        """Test setup_logging with custom configuration."""
        config = LogConfig(
            level="DEBUG",
            format="json",
            console_output=True,
        )

        setup_logging(config)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_with_file_output(self):
        """Test setup_logging with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            config = LogConfig(
                level="INFO",
                format="console",
                console_output=False,
                file_path=log_file,
                max_file_size=1024 * 1024,
                backup_count=3,
            )

            setup_logging(config)

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 1

            # Check file handler
            file_handler = root_logger.handlers[0]
            assert isinstance(file_handler, logging.handlers.RotatingFileHandler)
            assert str(file_handler.baseFilename) == str(log_file)

    def test_setup_logging_console_and_file(self):
        """Test setup_logging with both console and file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            config = LogConfig(
                level="WARNING",
                format="json",
                console_output=True,
                file_path=log_file,
            )

            setup_logging(config)

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 2

            # Check handler types
            handler_types = [type(h).__name__ for h in root_logger.handlers]
            assert "StreamHandler" in handler_types
            assert "RotatingFileHandler" in handler_types

    def test_setup_logging_creates_directory(self):
        """Test setup_logging creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "subdir" / "nested" / "test.log"

            config = LogConfig(
                level="INFO",
                console_output=False,
                file_path=log_file,
            )

            setup_logging(config)

            # Directory should be created
            assert log_file.parent.exists()
            assert log_file.parent.is_dir()

    def test_setup_logging_clears_existing_handlers(self):
        """Test setup_logging clears existing handlers."""
        # Reset first to ensure clean state
        reset_logging()

        # Add a dummy handler
        root_logger = logging.getLogger()
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)

        initial_count = len(root_logger.handlers)
        assert dummy_handler in root_logger.handlers

        # Setup logging should clear existing handlers
        setup_logging()

        # Should have new handlers, not the dummy one
        assert dummy_handler not in root_logger.handlers

    def test_setup_logging_idempotent(self):
        """Test setup_logging can be called multiple times safely."""
        config = LogConfig(level="INFO", console_output=True)

        setup_logging(config)
        handler_count_1 = len(logging.getLogger().handlers)

        setup_logging(config)
        handler_count_2 = len(logging.getLogger().handlers)

        # Should not accumulate handlers
        assert handler_count_1 == handler_count_2


class TestResetLogging:
    """Test reset_logging functionality."""

    def test_reset_logging_clears_state(self):
        """Test reset_logging clears all logging state."""
        # Setup logging
        setup_logging()
        logger = get_logger("test.reset")

        # Verify state exists
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

        # Reset
        reset_logging()

        # Verify state is cleared
        assert len(root_logger.handlers) == 0

    def test_reset_logging_clears_registry(self):
        """Test reset_logging clears logger registry."""
        # Get some loggers
        logger1 = get_logger("test.clear1")
        logger2 = get_logger("test.clear2")

        # Reset
        reset_logging()

        # Getting loggers again should create new instances
        new_logger1 = get_logger("test.clear1")
        new_logger2 = get_logger("test.clear2")

        # Should be different instances
        assert new_logger1 is not logger1
        assert new_logger2 is not logger2


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def setup_method(self):
        """Setup test environment."""
        reset_logging()

    def teardown_method(self):
        """Cleanup test environment."""
        reset_logging()

    def test_end_to_end_logging_flow(self):
        """Test complete logging flow from setup to usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "integration.log"

            # Setup with file logging
            config = LogConfig(
                level="DEBUG",
                format="console",
                console_output=False,
                file_path=log_file,
            )
            setup_logging(config)

            # Get logger and log messages
            logger = get_logger("test.integration")
            logger.info("Test message", user_id=123, password="secret")

            # File should exist and contain logs
            assert log_file.exists()

            # Read log content
            with open(log_file, "r") as f:
                content = f.read()

            assert "Test message" in content
            assert "user_id" in content
            assert "123" in content
            # Password should be redacted
            assert "secret" not in content
            assert "***REDACTED***" in content

    def test_multiple_loggers_same_config(self):
        """Test multiple loggers using same configuration."""
        setup_logging()

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # Both loggers should work
        with patch("structlog.get_logger") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.return_value = mock_logger

            logger1 = PGSDLogger("module1")
            logger2 = PGSDLogger("module2")

            logger1.info("Message from module1")
            logger2.info("Message from module2")

            assert mock_structlog.call_count == 2
            assert mock_logger.info.call_count == 2
