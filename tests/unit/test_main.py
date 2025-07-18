"""Tests for main entry point."""

import pytest
import sys
import signal
import threading
from unittest.mock import Mock, patch, call
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pgsd.main import (
    register_cleanup, cleanup, signal_handler, setup_signal_handlers,
    setup_application, main, console_entry_point, _cleanup_callbacks
)
from pgsd.exceptions.base import PGSDError
from pgsd.exceptions.config import ConfigurationError


class TestCleanupFunctionality:
    """Test cleanup functionality."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    def test_register_cleanup(self):
        """Test registering cleanup callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        register_cleanup(callback1)
        register_cleanup(callback2)
        
        assert len(_cleanup_callbacks) == 2
        assert callback1 in _cleanup_callbacks
        assert callback2 in _cleanup_callbacks

    def test_cleanup_executes_callbacks(self):
        """Test cleanup executes all registered callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        register_cleanup(callback1)
        register_cleanup(callback2)
        
        cleanup()
        
        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_cleanup_handles_callback_exceptions(self, capsys):
        """Test cleanup handles exceptions in callbacks gracefully."""
        def failing_callback():
            raise RuntimeError("Callback error")
        
        def working_callback():
            pass
        
        register_cleanup(failing_callback)
        register_cleanup(working_callback)
        
        # Should not raise exception
        cleanup()
        
        captured = capsys.readouterr()
        assert "Warning: Cleanup error: Callback error" in captured.err

    def test_cleanup_empty_callbacks(self):
        """Test cleanup with no registered callbacks."""
        # Should not raise exception
        cleanup()


class TestSignalHandling:
    """Test signal handling functionality."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    @patch('pgsd.main.cleanup')
    @patch('sys.exit')
    def test_signal_handler(self, mock_exit, mock_cleanup, capsys):
        """Test signal handler functionality."""
        signal_handler(signal.SIGINT, None)
        
        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(128 + signal.SIGINT)
        
        captured = capsys.readouterr()
        assert f"Received signal {signal.SIGINT}, shutting down..." in captured.err

    @patch('threading.current_thread')
    @patch('threading.main_thread')
    @patch('signal.signal')
    def test_setup_signal_handlers_main_thread(self, mock_signal, mock_main_thread, mock_current_thread):
        """Test signal handler setup in main thread."""
        # Mock main thread detection
        main_thread_mock = Mock()
        mock_main_thread.return_value = main_thread_mock
        mock_current_thread.return_value = main_thread_mock
        
        setup_signal_handlers()
        
        # Should set up both SIGINT and SIGTERM handlers
        expected_calls = [
            call(signal.SIGINT, signal_handler),
            call(signal.SIGTERM, signal_handler)
        ]
        mock_signal.assert_has_calls(expected_calls)

    @patch('threading.current_thread')
    @patch('threading.main_thread')
    @patch('signal.signal')
    def test_setup_signal_handlers_not_main_thread(self, mock_signal, mock_main_thread, mock_current_thread):
        """Test signal handler setup not in main thread."""
        # Mock different threads
        mock_main_thread.return_value = Mock()
        mock_current_thread.return_value = Mock()
        
        setup_signal_handlers()
        
        # Should not set up signal handlers
        mock_signal.assert_not_called()

    @patch('signal.signal', side_effect=ValueError("Signal error"))
    def test_setup_signal_handlers_exception(self, mock_signal):
        """Test signal handler setup handles exceptions."""
        # Should not raise exception
        setup_signal_handlers()


class TestApplicationSetup:
    """Test application setup functionality."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    @patch('atexit.register')
    @patch('pgsd.main.setup_signal_handlers')
    @patch('logging.basicConfig')
    @patch('pgsd.main.get_default_config')
    def test_setup_application(self, mock_get_config, mock_basicConfig, mock_setup_signals, mock_atexit):
        """Test application setup."""
        # Mock log config
        mock_log_config = Mock()
        mock_log_config.level = "WARNING"
        mock_get_config.return_value = mock_log_config
        
        setup_application()
        
        mock_atexit.assert_called_once_with(cleanup)
        mock_setup_signals.assert_called_once()
        mock_basicConfig.assert_called_once()


class TestMainFunction:
    """Test main function functionality."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_success(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function successful execution."""
        # Mock CLI manager
        mock_cli_manager = Mock()
        mock_cli_manager.run.return_value = 0
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main(['version'])
        
        assert result == 0
        mock_setup.assert_called_once()
        mock_cli_manager.run.assert_called_once_with(['version'])
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_keyboard_interrupt(self, mock_setup, mock_cli_manager_class, mock_cleanup, capsys):
        """Test main function handles KeyboardInterrupt."""
        # Mock CLI manager to raise KeyboardInterrupt
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = KeyboardInterrupt()
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main(['version'])
        
        assert result == 130
        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_configuration_error(self, mock_setup, mock_cli_manager_class, mock_cleanup, capsys):
        """Test main function handles ConfigurationError."""
        # Mock CLI manager to raise ConfigurationError
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = ConfigurationError("Config error")
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main(['version'])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "Configuration error: Config error" in captured.err
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_pgsd_error(self, mock_setup, mock_cli_manager_class, mock_cleanup, capsys):
        """Test main function handles PGSDError."""
        # Mock CLI manager to raise PGSDError
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = PGSDError("PGSD error")
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main(['version'])
        
        assert result == 1
        captured = capsys.readouterr()
        assert "PGSD error: PGSD error" in captured.err
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_unexpected_error(self, mock_setup, mock_cli_manager_class, mock_cleanup, capsys):
        """Test main function handles unexpected errors."""
        # Mock CLI manager to raise unexpected error
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = RuntimeError("Unexpected error")
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main(['version'])
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Unexpected error: Unexpected error" in captured.err
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    @patch('traceback.print_exc')
    def test_main_unexpected_error_verbose(self, mock_traceback, mock_setup, mock_cli_manager_class, mock_cleanup, capsys):
        """Test main function shows traceback in verbose mode."""
        # Mock CLI manager to raise unexpected error
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = RuntimeError("Unexpected error")
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main(['--verbose', 'version'])
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Unexpected error: Unexpected error" in captured.err
        mock_traceback.assert_called_once()
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_default_args(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function with default args (None)."""
        # Mock CLI manager
        mock_cli_manager = Mock()
        mock_cli_manager.run.return_value = 0
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main()
        
        assert result == 0
        mock_cli_manager.run.assert_called_once_with(None)


class TestConsoleEntryPoint:
    """Test console entry point functionality."""

    @patch('sys.exit')
    @patch('pgsd.main.main')
    def test_console_entry_point(self, mock_main, mock_exit):
        """Test console entry point."""
        mock_main.return_value = 42
        
        console_entry_point()
        
        mock_main.assert_called_once()
        mock_exit.assert_called_once_with(42)


class TestMainModuleExecution:
    """Test __main__ execution."""

    def test_main_module_import(self):
        """Test that main module can be imported without errors."""
        # This test ensures the module can be imported
        # The __main__ block execution is tested through integration tests
        import pgsd.main
        assert hasattr(pgsd.main, 'main')
        assert hasattr(pgsd.main, 'console_entry_point')