"""Tests for logger utilities."""

import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from tempfile import TemporaryDirectory

from src.pgsd.utils.logger import (
    PGSDLogger,
    get_logger,
    setup_logging,
    reset_logging,
    _logger_registry,
    _is_configured
)
from src.pgsd.utils.log_config import LogConfig


class TestPGSDLogger:
    """Test cases for PGSDLogger class."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def teardown_method(self):
        """Clean up after each test."""
        reset_logging()

    @patch('structlog.get_logger')
    def test_init(self, mock_get_logger):
        """Test PGSDLogger initialization."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        logger = PGSDLogger("test.module")
        
        assert logger.name == "test.module"
        assert logger._logger == mock_logger
        mock_get_logger.assert_called_once_with("test.module")

    def test_debug(self):
        """Test debug logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = PGSDLogger("test")
            logger.debug("Test debug message", field="value")
            
            mock_logger.debug.assert_called_once_with("Test debug message", field="value")

    def test_info(self):
        """Test info logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = PGSDLogger("test")
            logger.info("Test info message", key="value")
            
            # The logger sanitizes data, so check for sanitized call
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "Test info message"
            assert "key" in call_args[1]

    def test_warning(self):
        """Test warning logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = PGSDLogger("test")
            logger.warning("Test warning message", key="value")
            
            # The logger sanitizes data, so check for sanitized call
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "Test warning message"
            assert "key" in call_args[1]

    def test_error(self):
        """Test error logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = PGSDLogger("test")
            logger.error("Test error message", key="value")
            
            # The logger sanitizes data, so check for sanitized call
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "Test error message"
            assert "key" in call_args[1]

    def test_critical(self):
        """Test critical logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = PGSDLogger("test")
            logger.critical("Test critical message", key="value")
            
            # The logger sanitizes data, so check for sanitized call
            call_args = mock_logger.critical.call_args
            assert call_args[0][0] == "Test critical message"
            assert "key" in call_args[1]

    def test_exception(self):
        """Test exception logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = PGSDLogger("test")
            logger.exception("Test exception message", key="value")
            
            # The logger sanitizes data, so check for sanitized call
            call_args = mock_logger.exception.call_args
            assert call_args[0][0] == "Test exception message"
            assert "key" in call_args[1]

    def test_sanitize_data_basic(self):
        """Test basic data sanitization."""
        with patch('structlog.get_logger'):
            logger = PGSDLogger("test")
            
            data = {"normal": "value", "password": "secret"}
            sanitized = logger._sanitize_data(data)
            
            assert sanitized["normal"] == "value"
            assert sanitized["password"] == "***REDACTED***"

    def test_sanitize_data_sensitive_fields(self):
        """Test sanitization of all sensitive field types."""
        with patch('structlog.get_logger'):
            logger = PGSDLogger("test")
            
            data = {
                "password": "secret1",
                "secret": "secret2",
                "token": "secret3",
                "key": "secret4",
                "credential": "secret5",
                "auth": "secret6",
                "private": "secret7",
                "passwd": "secret8",
                "normal_field": "normal_value"
            }
            
            sanitized = logger._sanitize_data(data)
            
            # All sensitive fields should be redacted
            sensitive_fields = ["password", "secret", "token", "key", 
                              "credential", "auth", "private", "passwd"]
            for field in sensitive_fields:
                assert sanitized[field] == "***REDACTED***"
            
            # Normal field should remain
            assert sanitized["normal_field"] == "normal_value"

    def test_sanitize_data_case_insensitive(self):
        """Test case-insensitive sanitization."""
        with patch('structlog.get_logger'):
            logger = PGSDLogger("test")
            
            data = {
                "PASSWORD": "secret1",
                "Secret": "secret2",
                "TOKEN": "secret3",
                "user_password": "secret4",
                "API_KEY": "secret5",
                "normal": "value"
            }
            
            sanitized = logger._sanitize_data(data)
            
            assert sanitized["PASSWORD"] == "***REDACTED***"
            assert sanitized["Secret"] == "***REDACTED***"
            assert sanitized["TOKEN"] == "***REDACTED***"
            assert sanitized["user_password"] == "***REDACTED***"
            assert sanitized["API_KEY"] == "***REDACTED***"
            assert sanitized["normal"] == "value"

    def test_sanitize_data_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        with patch('structlog.get_logger'):
            logger = PGSDLogger("test")
            
            data = {
                "normal": "value",
                "nested": {
                    "password": "secret",
                    "normal": "value2"
                }
            }
            
            sanitized = logger._sanitize_data(data)
            
            assert sanitized["normal"] == "value"
            assert sanitized["nested"]["password"] == "***REDACTED***"
            assert sanitized["nested"]["normal"] == "value2"

    def test_sanitize_data_complex_structure(self):
        """Test sanitization of complex data structures."""
        with patch('structlog.get_logger'):
            logger = PGSDLogger("test")
            
            data = {
                "user": "john",
                "config": {
                    "database": {
                        "host": "localhost",
                        "password": "secret123"
                    },
                    "api_key": "apikey123"
                },
                "numbers": [1, 2, 3],
                "boolean": True
            }
            
            sanitized = logger._sanitize_data(data)
            
            assert sanitized["user"] == "john"
            assert sanitized["config"]["database"]["host"] == "localhost"
            assert sanitized["config"]["database"]["password"] == "***REDACTED***"
            assert sanitized["config"]["api_key"] == "***REDACTED***"
            assert sanitized["numbers"] == [1, 2, 3]
            assert sanitized["boolean"] is True


class TestLoggerRegistry:
    """Test cases for logger registry functions."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def teardown_method(self):
        """Clean up after each test."""
        reset_logging()

    @patch('src.pgsd.utils.logger.setup_logging')
    def test_get_logger_auto_setup(self, mock_setup):
        """Test that get_logger automatically sets up logging."""
        # Import to reset global state
        import src.pgsd.utils.logger
        src.pgsd.utils.logger._is_configured = False
        
        with patch('structlog.get_logger'):
            logger = get_logger("test.module")
            
        assert isinstance(logger, PGSDLogger)
        mock_setup.assert_called_once()

    def test_get_logger_caching(self):
        """Test that get_logger caches logger instances."""
        with patch('structlog.get_logger'), \
             patch('src.pgsd.utils.logger.setup_logging'):
            
            logger1 = get_logger("test.module")
            logger2 = get_logger("test.module")
            
            assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names create different loggers."""
        with patch('structlog.get_logger'), \
             patch('src.pgsd.utils.logger.setup_logging'):
            
            logger1 = get_logger("module1")
            logger2 = get_logger("module2")
            
            assert logger1 is not logger2
            assert logger1.name == "module1"
            assert logger2.name == "module2"

    def test_get_logger_already_configured(self):
        """Test get_logger when already configured."""
        import src.pgsd.utils.logger
        src.pgsd.utils.logger._is_configured = True
        
        with patch('structlog.get_logger'), \
             patch('src.pgsd.utils.logger.setup_logging') as mock_setup:
            
            logger = get_logger("test.module")
            
            assert isinstance(logger, PGSDLogger)
            mock_setup.assert_not_called()


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def teardown_method(self):
        """Clean up after each test."""
        reset_logging()

    @patch('structlog.configure')
    @patch('src.pgsd.utils.logger.get_default_config')
    def test_setup_logging_default_config(self, mock_get_config, mock_configure):
        """Test setup_logging with default configuration."""
        mock_config = Mock()
        mock_config.format = "console"
        mock_config.level = "INFO"
        mock_config.console_output = True
        mock_config.file_path = None
        mock_get_config.return_value = mock_config
        
        setup_logging()
        
        mock_get_config.assert_called_once()
        mock_configure.assert_called_once()

    @patch('structlog.configure')
    def test_setup_logging_custom_config(self, mock_configure):
        """Test setup_logging with custom configuration."""
        config = LogConfig(
            level="DEBUG",
            format="json",
            console_output=True,
            file_path=None,
            max_file_size=1024,
            backup_count=3
        )
        
        setup_logging(config)
        
        mock_configure.assert_called_once()

    @patch('structlog.configure')
    def test_setup_logging_json_format(self, mock_configure):
        """Test setup_logging with JSON format."""
        config = LogConfig(
            level="INFO",
            format="json",
            console_output=True,
            file_path=None,
            max_file_size=1024,
            backup_count=3
        )
        
        setup_logging(config)
        
        # Verify JSON renderer is used
        call_args = mock_configure.call_args
        processors = call_args.kwargs['processors']
        
        # Should contain JSONRenderer
        import structlog
        json_renderer_found = any(
            isinstance(p, structlog.processors.JSONRenderer) 
            for p in processors
        )
        assert json_renderer_found

    @patch('structlog.configure')
    def test_setup_logging_console_format(self, mock_configure):
        """Test setup_logging with console format."""
        config = LogConfig(
            level="INFO",
            format="console",
            console_output=True,
            file_path=None,
            max_file_size=1024,
            backup_count=3
        )
        
        setup_logging(config)
        
        # Verify console renderer is used
        call_args = mock_configure.call_args
        processors = call_args.kwargs['processors']
        
        # Should contain ConsoleRenderer
        import structlog
        console_renderer_found = any(
            isinstance(p, structlog.dev.ConsoleRenderer) 
            for p in processors
        )
        assert console_renderer_found

    @patch('logging.getLogger')
    def test_setup_logging_standard_library(self, mock_get_logger):
        """Test that setup_logging configures standard library logging."""
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger
        
        config = LogConfig(
            level="WARNING",
            format="console",
            console_output=False,
            file_path=None,
            max_file_size=1024,
            backup_count=3
        )
        
        with patch('structlog.configure'):
            setup_logging(config)
        
        mock_root_logger.setLevel.assert_called_with(logging.WARNING)
        mock_root_logger.handlers.clear.assert_called_once()

    def test_setup_logging_console_handler(self):
        """Test setup_logging with console handler."""
        config = LogConfig(
            level="INFO",
            format="console",
            console_output=True,
            file_path=None,
            max_file_size=1024,
            backup_count=3
        )
        
        with patch('structlog.configure'), \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_stream_handler:
            
            mock_root_logger = Mock()
            mock_get_logger.return_value = mock_root_logger
            mock_handler = Mock()
            mock_stream_handler.return_value = mock_handler
            
            setup_logging(config)
            
            mock_stream_handler.assert_called_once_with(sys.stdout)
            mock_handler.setLevel.assert_called_once_with(logging.INFO)
            mock_root_logger.addHandler.assert_called_with(mock_handler)

    def test_setup_logging_file_handler(self):
        """Test setup_logging with file handler."""
        with TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            config = LogConfig(
                level="DEBUG",
                format="console",
                console_output=False,
                file_path=log_file,
                max_file_size=2048,
                backup_count=5
            )
            
            with patch('structlog.configure'), \
                 patch('logging.getLogger') as mock_get_logger, \
                 patch('logging.handlers.RotatingFileHandler') as mock_file_handler:
                
                mock_root_logger = Mock()
                mock_get_logger.return_value = mock_root_logger
                mock_handler = Mock()
                mock_file_handler.return_value = mock_handler
                
                setup_logging(config)
                
                mock_file_handler.assert_called_once_with(
                    log_file,
                    maxBytes=2048,
                    backupCount=5,
                    encoding="utf-8"
                )
                mock_handler.setLevel.assert_called_once_with(logging.DEBUG)
                mock_root_logger.addHandler.assert_called_with(mock_handler)

    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates log directory."""
        with TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "test.log"
            
            config = LogConfig(
                level="INFO",
                format="console",
                console_output=False,
                file_path=log_file,
                max_file_size=1024,
                backup_count=3
            )
            
            with patch('structlog.configure'), \
                 patch('logging.getLogger'), \
                 patch('logging.handlers.RotatingFileHandler'):
                
                setup_logging(config)
                
                # Directory should be created
                assert log_file.parent.exists()

    def test_setup_logging_sets_configured_flag(self):
        """Test that setup_logging sets the configured flag."""
        import src.pgsd.utils.logger
        
        config = LogConfig(
            level="INFO",
            format="console",
            console_output=True,
            file_path=None,
            max_file_size=1024,
            backup_count=3
        )
        
        with patch('structlog.configure'), \
             patch('logging.getLogger'):
            
            assert not src.pgsd.utils.logger._is_configured
            setup_logging(config)
            assert src.pgsd.utils.logger._is_configured


class TestResetLogging:
    """Test cases for reset_logging function."""

    def test_reset_logging(self):
        """Test reset_logging functionality."""
        import src.pgsd.utils.logger
        
        # Set up initial state
        src.pgsd.utils.logger._is_configured = True
        src.pgsd.utils.logger._logger_registry["test"] = Mock()
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_root_logger = Mock()
            mock_get_logger.return_value = mock_root_logger
            
            reset_logging()
            
            assert not src.pgsd.utils.logger._is_configured
            assert len(src.pgsd.utils.logger._logger_registry) == 0
            mock_root_logger.handlers.clear.assert_called_once()


class TestLoggerIntegration:
    """Integration tests for logger module."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def teardown_method(self):
        """Clean up after each test."""
        reset_logging()

    def test_full_logging_workflow(self):
        """Test complete logging workflow."""
        config = LogConfig(
            level="INFO",
            format="console",
            console_output=True,
            file_path=None,
            max_file_size=1024,
            backup_count=3
        )
        
        with patch('structlog.configure'), \
             patch('logging.getLogger'), \
             patch('structlog.get_logger') as mock_get_structlog:
            
            mock_logger = Mock()
            mock_get_structlog.return_value = mock_logger
            
            # Setup logging
            setup_logging(config)
            
            # Get logger and use it
            logger = get_logger("test.module")
            logger.info("Test message", key="value")
            
            # Verify the chain - logger sanitizes data
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "Test message"
            assert "key" in call_args[1]

    def test_multiple_loggers(self):
        """Test multiple logger instances."""
        with patch('structlog.configure'), \
             patch('logging.getLogger'), \
             patch('structlog.get_logger') as mock_get_structlog:
            
            mock_logger1 = Mock()
            mock_logger2 = Mock()
            mock_get_structlog.side_effect = [mock_logger1, mock_logger2]
            
            logger1 = get_logger("module1")
            logger2 = get_logger("module2")
            
            logger1.info("Message 1")
            logger2.error("Message 2")
            
            mock_logger1.info.assert_called_once_with("Message 1")
            mock_logger2.error.assert_called_once_with("Message 2")

    def test_logger_with_sensitive_data(self):
        """Test logging with sensitive data sanitization."""
        with patch('structlog.configure'), \
             patch('logging.getLogger'), \
             patch('structlog.get_logger') as mock_get_structlog:
            
            mock_logger = Mock()
            mock_get_structlog.return_value = mock_logger
            
            logger = get_logger("test")
            logger.info("Database connection", password="secret", host="localhost")
            
            # Verify sanitization occurred
            call_args = mock_logger.info.call_args
            assert call_args[1]["password"] == "***REDACTED***"
            assert call_args[1]["host"] == "localhost"