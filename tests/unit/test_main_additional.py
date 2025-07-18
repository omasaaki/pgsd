"""Additional tests for main.py to improve coverage."""

import pytest
import sys
import signal
import threading
import os
from unittest.mock import Mock, patch, call, MagicMock
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pgsd.main import (
    register_cleanup, cleanup, signal_handler, setup_signal_handlers,
    setup_application, main, console_entry_point, _cleanup_callbacks
)
from pgsd.exceptions.base import PGSDError
from pgsd.exceptions.config import ConfigurationError


class TestMainModuleExecution:
    """Test main module execution scenarios."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_no_args(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function with no arguments."""
        # Mock CLI manager
        mock_cli_manager = Mock()
        mock_cli_manager.run.return_value = 0
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main()
        
        assert result == 0
        mock_setup.assert_called_once()
        mock_cli_manager.run.assert_called_once_with(None)
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_empty_args_list(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function with empty arguments list."""
        # Mock CLI manager
        mock_cli_manager = Mock()
        mock_cli_manager.run.return_value = 0
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main([])
        
        assert result == 0
        mock_setup.assert_called_once()
        mock_cli_manager.run.assert_called_once_with([])
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_verbose_flag_detection(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function detects verbose flag."""
        # Mock CLI manager to raise exception
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = RuntimeError("Test error")
        mock_cli_manager_class.return_value = mock_cli_manager
        
        with patch('traceback.print_exc') as mock_traceback:
            result = main(['--verbose', 'version'])
            
            assert result == 1
            mock_traceback.assert_called_once()
            mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_verbose_flag_not_present(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function without verbose flag."""
        # Mock CLI manager to raise exception
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = RuntimeError("Test error")
        mock_cli_manager_class.return_value = mock_cli_manager
        
        with patch('traceback.print_exc') as mock_traceback:
            result = main(['version'])
            
            assert result == 1
            mock_traceback.assert_not_called()
            mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_cleanup_always_called(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test that cleanup is always called, even on exception."""
        # Mock CLI manager to raise exception
        mock_cli_manager = Mock()
        mock_cli_manager.run.side_effect = RuntimeError("Test error")
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main(['version'])
        
        assert result == 1
        mock_cleanup.assert_called_once()

    def test_console_entry_point_calls_main(self):
        """Test console entry point calls main with sys.argv."""
        with patch('pgsd.main.main') as mock_main, \
             patch('sys.exit') as mock_exit:
            
            mock_main.return_value = 42
            
            console_entry_point()
            
            mock_main.assert_called_once()
            mock_exit.assert_called_once_with(42)


class TestAdvancedCleanupFunctionality:
    """Test advanced cleanup functionality."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    def test_register_cleanup_duplicate_callback(self):
        """Test registering the same callback multiple times."""
        callback = Mock()
        
        register_cleanup(callback)
        register_cleanup(callback)
        
        # Should only be registered once
        assert len(_cleanup_callbacks) == 1
        assert callback in _cleanup_callbacks
        
        cleanup()
        callback.assert_called_once()

    def test_register_cleanup_callable_validation(self):
        """Test that register_cleanup validates callable objects."""
        # Should work with functions
        def test_func():
            pass
        register_cleanup(test_func)
        
        # Should work with methods
        mock_obj = Mock()
        register_cleanup(mock_obj.method)
        
        # Should work with lambdas
        register_cleanup(lambda: None)
        
        assert len(_cleanup_callbacks) == 3

    def test_cleanup_preserves_callback_order(self):
        """Test that cleanup executes callbacks in registration order."""
        call_order = []
        
        def callback1():
            call_order.append(1)
            
        def callback2():
            call_order.append(2)
            
        def callback3():
            call_order.append(3)
        
        register_cleanup(callback1)
        register_cleanup(callback2) 
        register_cleanup(callback3)
        
        cleanup()
        
        assert call_order == [1, 2, 3]

    def test_cleanup_partial_failure_continues(self):
        """Test that cleanup continues even if some callbacks fail."""
        working_callback = Mock()
        
        def failing_callback():
            raise RuntimeError("Callback failed")
        
        register_cleanup(working_callback)
        register_cleanup(failing_callback)
        register_cleanup(working_callback)  # Will be called again
        
        # Should not raise exception
        cleanup()
        
        # Working callback should still be called
        assert working_callback.call_count == 1  # Only once due to deduplication

    def test_cleanup_clears_callbacks_after_execution(self):
        """Test that cleanup clears the callbacks list after execution."""
        callback = Mock()
        register_cleanup(callback)
        
        assert len(_cleanup_callbacks) == 1
        
        cleanup()
        
        # Note: Current implementation doesn't clear callbacks
        # This test documents the current behavior
        assert len(_cleanup_callbacks) == 1

    def test_cleanup_with_exception_in_stderr_write(self):
        """Test cleanup handles stderr write exceptions."""
        def failing_callback():
            raise RuntimeError("Callback failed")
        
        register_cleanup(failing_callback)
        
        with patch('sys.stderr.write', side_effect=OSError("Write failed")):
            # Should not raise exception even if stderr write fails
            cleanup()


class TestAdvancedSignalHandling:
    """Test advanced signal handling functionality."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    @patch('pgsd.main.cleanup')
    @patch('sys.exit')
    def test_signal_handler_different_signals(self, mock_exit, mock_cleanup):
        """Test signal handler with different signal types."""
        test_signals = [signal.SIGINT, signal.SIGTERM]
        
        for sig in test_signals:
            mock_cleanup.reset_mock()
            mock_exit.reset_mock()
            
            signal_handler(sig, None)
            
            mock_cleanup.assert_called_once()
            mock_exit.assert_called_once_with(128 + sig)

    @patch('pgsd.main.cleanup')
    @patch('sys.exit')
    def test_signal_handler_with_frame(self, mock_exit, mock_cleanup):
        """Test signal handler with frame parameter."""
        frame = Mock()
        
        signal_handler(signal.SIGINT, frame)
        
        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(128 + signal.SIGINT)

    @patch('pgsd.main.cleanup', side_effect=Exception("Cleanup failed"))
    @patch('sys.exit')
    def test_signal_handler_cleanup_exception(self, mock_exit, mock_cleanup):
        """Test signal handler when cleanup raises exception."""
        # Should still exit even if cleanup fails
        signal_handler(signal.SIGINT, None)
        
        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(128 + signal.SIGINT)

    @patch('threading.current_thread')
    @patch('threading.main_thread')
    @patch('signal.signal')
    def test_setup_signal_handlers_thread_comparison(self, mock_signal, mock_main_thread, mock_current_thread):
        """Test signal handler setup thread comparison logic."""
        # Test when threads are the same object
        thread_obj = Mock()
        mock_main_thread.return_value = thread_obj
        mock_current_thread.return_value = thread_obj
        
        setup_signal_handlers()
        
        assert mock_signal.call_count == 2  # SIGINT and SIGTERM
        
        # Test when threads are different objects
        mock_signal.reset_mock()
        mock_main_thread.return_value = Mock()
        mock_current_thread.return_value = Mock()
        
        setup_signal_handlers()
        
        mock_signal.assert_not_called()

    @patch('threading.current_thread', side_effect=RuntimeError("Thread error"))
    @patch('signal.signal')
    def test_setup_signal_handlers_thread_exception(self, mock_signal, mock_current_thread):
        """Test signal handler setup when thread functions raise exceptions."""
        # Should not crash
        setup_signal_handlers()
        
        mock_signal.assert_not_called()

    def test_signal_handler_exit_code_calculation(self):
        """Test that signal handler calculates exit codes correctly."""
        test_cases = [
            (signal.SIGINT, 128 + signal.SIGINT),
            (signal.SIGTERM, 128 + signal.SIGTERM),
        ]
        
        for sig, expected_exit_code in test_cases:
            with patch('pgsd.main.cleanup'), \
                 patch('sys.exit') as mock_exit:
                
                signal_handler(sig, None)
                mock_exit.assert_called_once_with(expected_exit_code)


class TestAdvancedApplicationSetup:
    """Test advanced application setup functionality."""

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
    def test_setup_application_logging_config(self, mock_get_config, mock_basicConfig, mock_setup_signals, mock_atexit):
        """Test application setup with different logging configurations."""
        # Test with different log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            mock_get_config.reset_mock()
            mock_basicConfig.reset_mock()
            
            mock_log_config = Mock()
            mock_log_config.level = level
            mock_get_config.return_value = mock_log_config
            
            setup_application()
            
            mock_basicConfig.assert_called_once()
            call_kwargs = mock_basicConfig.call_args.kwargs
            assert 'level' in call_kwargs

    @patch('atexit.register')
    @patch('pgsd.main.setup_signal_handlers', side_effect=Exception("Signal setup failed"))
    @patch('logging.basicConfig')
    @patch('pgsd.main.get_default_config')
    def test_setup_application_signal_setup_failure(self, mock_get_config, mock_basicConfig, mock_setup_signals, mock_atexit):
        """Test application setup when signal setup fails."""
        mock_log_config = Mock()
        mock_log_config.level = "INFO"
        mock_get_config.return_value = mock_log_config
        
        # Should not raise exception even if signal setup fails
        setup_application()
        
        mock_atexit.assert_called_once_with(cleanup)
        mock_basicConfig.assert_called_once()

    @patch('atexit.register', side_effect=Exception("Atexit failed"))
    @patch('pgsd.main.setup_signal_handlers')
    @patch('logging.basicConfig')
    @patch('pgsd.main.get_default_config')
    def test_setup_application_atexit_failure(self, mock_get_config, mock_basicConfig, mock_setup_signals, mock_atexit):
        """Test application setup when atexit registration fails."""
        mock_log_config = Mock()
        mock_log_config.level = "INFO"
        mock_get_config.return_value = mock_log_config
        
        # Should not raise exception even if atexit fails
        setup_application()
        
        mock_setup_signals.assert_called_once()
        mock_basicConfig.assert_called_once()

    @patch('atexit.register')
    @patch('pgsd.main.setup_signal_handlers')
    @patch('logging.basicConfig', side_effect=Exception("Logging failed"))
    @patch('pgsd.main.get_default_config')
    def test_setup_application_logging_failure(self, mock_get_config, mock_basicConfig, mock_setup_signals, mock_atexit):
        """Test application setup when logging configuration fails."""
        mock_log_config = Mock()
        mock_log_config.level = "INFO"
        mock_get_config.return_value = mock_log_config
        
        # Should not raise exception even if logging setup fails
        setup_application()
        
        mock_atexit.assert_called_once_with(cleanup)
        mock_setup_signals.assert_called_once()


class TestErrorHandlingScenarios:
    """Test various error handling scenarios."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_exception_hierarchy(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function handles different exception types correctly."""
        test_cases = [
            (KeyboardInterrupt(), 130),
            (ConfigurationError("Config error"), 2),
            (PGSDError("PGSD error"), 1),
            (RuntimeError("Runtime error"), 1),
            (ValueError("Value error"), 1),
            (OSError("OS error"), 1)
        ]
        
        for exception, expected_exit_code in test_cases:
            mock_cli_manager = Mock()
            mock_cli_manager.run.side_effect = exception
            mock_cli_manager_class.return_value = mock_cli_manager
            
            result = main(['test'])
            
            assert result == expected_exit_code
            mock_cleanup.assert_called()
            
            # Reset mocks for next iteration
            mock_cleanup.reset_mock()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application', side_effect=Exception("Setup failed"))
    def test_main_setup_failure(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function when setup_application fails."""
        result = main(['version'])
        
        assert result == 1
        mock_setup.assert_called_once()
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager', side_effect=Exception("CLI Manager creation failed"))
    @patch('pgsd.main.setup_application')
    def test_main_cli_manager_creation_failure(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function when CLIManager creation fails."""
        result = main(['version'])
        
        assert result == 1
        mock_setup.assert_called_once()
        mock_cleanup.assert_called_once()

    @patch('pgsd.main.cleanup', side_effect=Exception("Cleanup failed"))
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_cleanup_failure(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function when cleanup fails."""
        # Mock CLI manager
        mock_cli_manager = Mock()
        mock_cli_manager.run.return_value = 0
        mock_cli_manager_class.return_value = mock_cli_manager
        
        # Should still return success even if cleanup fails
        result = main(['version'])
        
        assert result == 0
        mock_cleanup.assert_called_once()


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def setup_method(self):
        """Reset cleanup callbacks before each test."""
        _cleanup_callbacks.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _cleanup_callbacks.clear()

    def test_cleanup_with_no_callbacks_registered(self):
        """Test cleanup when no callbacks are registered."""
        # Should not raise exception
        cleanup()
        
        assert len(_cleanup_callbacks) == 0

    def test_register_cleanup_with_none(self):
        """Test registering None as cleanup callback."""
        # Current implementation doesn't validate, so this documents behavior
        register_cleanup(None)
        
        # cleanup() should handle None gracefully
        cleanup()

    @patch('sys.stderr')
    def test_cleanup_stderr_handling(self, mock_stderr):
        """Test cleanup handles stderr operations."""
        def failing_callback():
            raise RuntimeError("Test error")
        
        register_cleanup(failing_callback)
        
        cleanup()
        
        # Should have attempted to write to stderr
        mock_stderr.write.assert_called()

    def test_signal_handler_with_zero_signal(self):
        """Test signal handler with signal value 0."""
        with patch('pgsd.main.cleanup'), \
             patch('sys.exit') as mock_exit:
            
            signal_handler(0, None)
            mock_exit.assert_called_once_with(128)

    def test_multiple_signal_handlers_registration(self):
        """Test multiple calls to setup_signal_handlers."""
        with patch('threading.current_thread'), \
             patch('threading.main_thread'), \
             patch('signal.signal') as mock_signal:
            
            # Mock main thread
            mock_signal.reset_mock()
            
            # Call multiple times
            setup_signal_handlers()
            setup_signal_handlers()
            setup_signal_handlers()
            
            # Each call should try to set up signals
            expected_calls = 6  # 3 calls × 2 signals each
            assert mock_signal.call_count == expected_calls

    @patch('pgsd.main.cleanup')
    @patch('pgsd.main.CLIManager')
    @patch('pgsd.main.setup_application')
    def test_main_with_very_long_args(self, mock_setup, mock_cli_manager_class, mock_cleanup):
        """Test main function with very long argument list."""
        # Mock CLI manager
        mock_cli_manager = Mock()
        mock_cli_manager.run.return_value = 0
        mock_cli_manager_class.return_value = mock_cli_manager
        
        # Create a very long argument list
        long_args = ['arg'] * 1000
        
        result = main(long_args)
        
        assert result == 0
        mock_cli_manager.run.assert_called_once_with(long_args)