"""Tests for main entry point module."""

import sys
import signal
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from src.pgsd.main import (
    main,
    setup_application,
    setup_signal_handlers,
    register_cleanup,
    cleanup,
    signal_handler,
    console_entry_point,
    _cleanup_callbacks
)
from src.pgsd.exceptions.base import PGSDError
from src.pgsd.exceptions.config import ConfigurationError


class TestMainFunction:
    """Test cases for main function."""

    def setup_method(self):
        """Clear cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_success(self, mock_setup, mock_cli_manager):
        """Test successful main execution."""
        # Setup mocks
        mock_cli_instance = Mock()
        mock_cli_instance.run.return_value = 0
        mock_cli_manager.return_value = mock_cli_instance
        
        # Execute
        result = main(['--help'])
        
        # Verify
        assert result == 0
        mock_setup.assert_called_once()
        mock_cli_manager.assert_called_once()
        mock_cli_instance.run.assert_called_once_with(['--help'])

    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_with_none_args(self, mock_setup, mock_cli_manager):
        """Test main with None args."""
        mock_cli_instance = Mock()
        mock_cli_instance.run.return_value = 0
        mock_cli_manager.return_value = mock_cli_instance
        
        result = main(None)
        
        assert result == 0
        mock_cli_instance.run.assert_called_once_with(None)

    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_keyboard_interrupt(self, mock_setup, mock_cli_manager):
        """Test main with KeyboardInterrupt."""
        mock_cli_manager.side_effect = KeyboardInterrupt()
        
        with patch('src.pgsd.main.print') as mock_print:
            result = main(['compare'])
            
        assert result == 130
        mock_print.assert_called_once_with("\nOperation cancelled by user", file=sys.stderr)

    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_configuration_error(self, mock_setup, mock_cli_manager):
        """Test main with ConfigurationError."""
        mock_cli_manager.side_effect = ConfigurationError("Config error")
        
        with patch('src.pgsd.main.print') as mock_print:
            result = main(['compare'])
            
        assert result == 2
        mock_print.assert_called_once_with("Configuration error: Config error", file=sys.stderr)

    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_pgsd_error(self, mock_setup, mock_cli_manager):
        """Test main with PGSDError."""
        mock_cli_manager.side_effect = PGSDError("PGSD error")
        
        with patch('src.pgsd.main.print') as mock_print:
            result = main(['compare'])
            
        assert result == 1
        mock_print.assert_called_once_with("PGSD error: PGSD error", file=sys.stderr)

    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_unexpected_error(self, mock_setup, mock_cli_manager):
        """Test main with unexpected error."""
        mock_cli_manager.side_effect = RuntimeError("Unexpected error")
        
        with patch('src.pgsd.main.print') as mock_print:
            result = main(['compare'])
            
        assert result == 1
        mock_print.assert_called_once_with("Unexpected error: Unexpected error", file=sys.stderr)

    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_unexpected_error_with_verbose(self, mock_setup, mock_cli_manager):
        """Test main with unexpected error and verbose flag."""
        mock_cli_manager.side_effect = RuntimeError("Unexpected error")
        
        with patch('src.pgsd.main.print') as mock_print, \
             patch('traceback.print_exc') as mock_traceback:
            result = main(['--verbose', 'compare'])
            
        assert result == 1
        mock_print.assert_called_once_with("Unexpected error: Unexpected error", file=sys.stderr)
        mock_traceback.assert_called_once()

    @patch('src.pgsd.main.cleanup')
    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_cleanup_always_called(self, mock_setup, mock_cli_manager, mock_cleanup):
        """Test that cleanup is always called."""
        mock_cli_instance = Mock()
        mock_cli_instance.run.return_value = 0
        mock_cli_manager.return_value = mock_cli_instance
        
        result = main(['--help'])
        
        assert result == 0
        mock_cleanup.assert_called_once()

    @patch('src.pgsd.main.cleanup')
    @patch('src.pgsd.main.CLIManager')
    @patch('src.pgsd.main.setup_application')
    def test_main_cleanup_called_on_error(self, mock_setup, mock_cli_manager, mock_cleanup):
        """Test that cleanup is called even on error."""
        mock_cli_manager.side_effect = RuntimeError("Error")
        
        with patch('src.pgsd.main.print'):
            result = main(['compare'])
            
        assert result == 1
        mock_cleanup.assert_called_once()


class TestConsoleEntryPoint:
    """Test cases for console entry point."""

    @patch('src.pgsd.main.main')
    @patch('sys.exit')
    def test_console_entry_point(self, mock_exit, mock_main):
        """Test console entry point."""
        mock_main.return_value = 0
        
        console_entry_point()
        
        mock_main.assert_called_once()
        mock_exit.assert_called_once_with(0)


class TestSetupApplication:
    """Test cases for setup_application function."""

    def setup_method(self):
        """Clear cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    @patch('atexit.register')
    @patch('src.pgsd.main.setup_signal_handlers')
    @patch('src.pgsd.main.get_default_config')
    @patch('logging.basicConfig')
    def test_setup_application(self, mock_basic_config, mock_get_config, 
                              mock_setup_signals, mock_atexit):
        """Test application setup."""
        # Setup mock config
        mock_config = Mock()
        mock_config.level = "WARNING"
        mock_get_config.return_value = mock_config
        
        setup_application()
        
        # Verify calls
        mock_atexit.assert_called_once_with(cleanup)
        mock_setup_signals.assert_called_once()
        mock_get_config.assert_called_once()
        mock_basic_config.assert_called_once()


class TestSignalHandlers:
    """Test cases for signal handler functions."""

    @patch('threading.current_thread')
    @patch('threading.main_thread')
    @patch('signal.signal')
    def test_setup_signal_handlers_success(self, mock_signal, mock_main_thread, mock_current_thread):
        """Test successful signal handler setup."""
        # Mock threading
        mock_main_thread.return_value = "main"
        mock_current_thread.return_value = "main"
        
        setup_signal_handlers()
        
        # Verify signal handlers are set
        expected_calls = [
            call(signal.SIGINT, signal_handler),
            call(signal.SIGTERM, signal_handler)
        ]
        mock_signal.assert_has_calls(expected_calls)

    @patch('threading.current_thread')
    @patch('threading.main_thread')
    @patch('signal.signal')
    def test_setup_signal_handlers_not_main_thread(self, mock_signal, mock_main_thread, mock_current_thread):
        """Test signal handler setup when not in main thread."""
        # Mock threading - not main thread
        mock_main_thread.return_value = "main"
        mock_current_thread.return_value = "other"
        
        setup_signal_handlers()
        
        # Verify signal handlers are not set
        mock_signal.assert_not_called()

    @patch('threading.current_thread')
    @patch('threading.main_thread')
    @patch('signal.signal')
    def test_setup_signal_handlers_exception(self, mock_signal, mock_main_thread, mock_current_thread):
        """Test signal handler setup with exception."""
        # Mock threading
        mock_main_thread.return_value = "main"
        mock_current_thread.return_value = "main"
        mock_signal.side_effect = ValueError("Signal error")
        
        # Should not raise exception
        setup_signal_handlers()

    @patch('src.pgsd.main.cleanup')
    @patch('sys.exit')
    def test_signal_handler(self, mock_exit, mock_cleanup):
        """Test signal handler function."""
        with patch('src.pgsd.main.print') as mock_print:
            signal_handler(signal.SIGINT, None)
            
        mock_print.assert_called_once_with(f"\nReceived signal {signal.SIGINT}, shutting down...", file=sys.stderr)
        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(128 + signal.SIGINT)


class TestCleanupFunctions:
    """Test cases for cleanup functions."""

    def setup_method(self):
        """Clear cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def test_register_cleanup(self):
        """Test cleanup callback registration."""
        callback = Mock()
        
        register_cleanup(callback)
        
        assert callback in _cleanup_callbacks

    def test_cleanup_success(self):
        """Test successful cleanup execution."""
        callback1 = Mock()
        callback2 = Mock()
        
        register_cleanup(callback1)
        register_cleanup(callback2)
        
        cleanup()
        
        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_cleanup_with_exception(self):
        """Test cleanup with callback exception."""
        callback1 = Mock()
        callback1.side_effect = RuntimeError("Cleanup error")
        callback2 = Mock()
        
        register_cleanup(callback1)
        register_cleanup(callback2)
        
        with patch('src.pgsd.main.print') as mock_print:
            cleanup()
        
        # Both callbacks should be called despite exception
        callback1.assert_called_once()
        callback2.assert_called_once()
        
        # Error should be printed
        mock_print.assert_called_once_with("Warning: Cleanup error: Cleanup error", file=sys.stderr)

    def test_cleanup_empty_callbacks(self):
        """Test cleanup with no registered callbacks."""
        # Should not raise exception
        cleanup()


class TestMainModuleExecution:
    """Test cases for main module execution."""

    @patch('src.pgsd.main.main')
    @patch('sys.exit')
    def test_main_module_execution(self, mock_exit, mock_main):
        """Test main module execution."""
        mock_main.return_value = 0
        
        # Test the actual if __name__ == "__main__" logic
        # Since the module is already imported, we just verify the function exists
        from src.pgsd.main import main
        assert callable(main)
        
        # Test calling main directly
        result = main(['--help'])
        mock_main.assert_called_with(['--help'])


class TestMainIntegration:
    """Integration tests for main module."""

    def setup_method(self):
        """Clear cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    @patch('src.pgsd.main.CLIManager')
    def test_full_workflow_success(self, mock_cli_manager):
        """Test full workflow from main to CLI execution."""
        # Setup
        mock_cli_instance = Mock()
        mock_cli_instance.run.return_value = 0
        mock_cli_manager.return_value = mock_cli_instance
        
        # Execute
        with patch('src.pgsd.main.get_default_config') as mock_config:
            mock_config.return_value = Mock(level="WARNING")
            result = main(['version'])
        
        # Verify
        assert result == 0
        mock_cli_instance.run.assert_called_once_with(['version'])

    def test_error_propagation(self):
        """Test that errors are properly caught and handled."""
        # Test with mock that raises exception
        with patch('src.pgsd.main.CLIManager') as mock_cli:
            mock_cli.side_effect = RuntimeError("Test error")
            
            with patch('src.pgsd.main.print'):
                result = main(['test'])
                
        assert result == 1  # Error exit code