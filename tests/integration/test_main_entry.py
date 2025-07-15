"""Integration tests for main entry points.

This module tests the main application entry points including
python -m pgsd execution and direct main() function calls.
"""

import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pgsd.main import main, console_entry_point, setup_application, cleanup
from pgsd.cli.main import CLIManager


class TestMainEntryPoint:
    """Test cases for main entry point function."""

    def test_main_with_version_command(self):
        """Test main function with version command."""
        args = ['version']
        exit_code = main(args)
        assert exit_code == 0

    def test_main_with_help_command(self):
        """Test main function with help command."""
        args = ['--help']
        
        # Help command exits with SystemExit, so we expect it
        with pytest.raises(SystemExit) as exc_info:
            main(args)
        assert exc_info.value.code == 0

    def test_main_with_invalid_command(self):
        """Test main function with invalid command."""
        args = ['invalid-command']
        with pytest.raises(SystemExit) as exc_info:
            main(args)
        assert exc_info.value.code == 2

    def test_main_without_arguments(self):
        """Test main function without arguments."""
        args = []
        exit_code = main(args)
        assert exit_code == 2  # Should show help and exit with code 2

    @patch('pgsd.main.CLIManager')
    def test_main_with_cli_manager_exception(self, mock_cli_manager):
        """Test main function when CLI manager raises exception."""
        mock_cli = Mock()
        mock_cli_manager.return_value = mock_cli
        mock_cli.run.side_effect = Exception("Test error")
        
        args = ['version']
        exit_code = main(args)
        assert exit_code == 1

    @patch('pgsd.main.CLIManager')
    def test_main_with_keyboard_interrupt(self, mock_cli_manager):
        """Test main function with keyboard interrupt."""
        mock_cli = Mock()
        mock_cli_manager.return_value = mock_cli
        mock_cli.run.side_effect = KeyboardInterrupt()
        
        args = ['version']
        exit_code = main(args)
        assert exit_code == 130


class TestModuleExecution:
    """Test cases for python -m pgsd execution."""

    def test_module_execution_version(self):
        """Test python -m pgsd version command."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pgsd', 'version'],
                cwd=Path(__file__).parent.parent.parent,
                env={'PYTHONPATH': str(Path(__file__).parent.parent.parent / 'src')},
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should succeed and show version information
            assert result.returncode == 0
            assert "PGSD" in result.stdout
            assert "1.0.0" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except FileNotFoundError:
            pytest.skip("Python module execution not available")

    def test_module_execution_help(self):
        """Test python -m pgsd --help command."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pgsd', '--help'],
                cwd=Path(__file__).parent.parent.parent,
                env={'PYTHONPATH': str(Path(__file__).parent.parent.parent / 'src')},
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should succeed and show help
            assert result.returncode == 0
            assert "PostgreSQL Schema Diff Tool" in result.stdout
            assert "compare" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except FileNotFoundError:
            pytest.skip("Python module execution not available")

    def test_module_execution_invalid_command(self):
        """Test python -m pgsd with invalid command."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pgsd', 'invalid-command'],
                cwd=Path(__file__).parent.parent.parent,
                env={'PYTHONPATH': str(Path(__file__).parent.parent.parent / 'src')},
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should fail with non-zero exit code
            assert result.returncode != 0
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except FileNotFoundError:
            pytest.skip("Python module execution not available")


class TestApplicationSetup:
    """Test cases for application setup and cleanup."""

    def test_setup_application(self):
        """Test application setup function."""
        # Should not raise any exceptions
        setup_application()

    def test_cleanup_function(self):
        """Test cleanup function."""
        # Should not raise any exceptions
        cleanup()

    def test_cleanup_with_registered_callbacks(self):
        """Test cleanup with registered callbacks."""
        from pgsd.main import register_cleanup
        
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        register_cleanup(test_callback)
        cleanup()
        
        assert callback_called

    def test_cleanup_with_failing_callback(self):
        """Test cleanup with failing callback."""
        from pgsd.main import register_cleanup
        
        def failing_callback():
            raise Exception("Test error")
        
        # Should not raise exception even if callback fails
        register_cleanup(failing_callback)
        cleanup()


class TestConsoleEntryPoint:
    """Test cases for console entry point."""

    @patch('pgsd.main.main')
    @patch('sys.exit')
    def test_console_entry_point(self, mock_exit, mock_main):
        """Test console entry point function."""
        mock_main.return_value = 0
        
        console_entry_point()
        
        mock_main.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('pgsd.main.main')
    @patch('sys.exit')
    def test_console_entry_point_with_error(self, mock_exit, mock_main):
        """Test console entry point with error."""
        mock_main.return_value = 1
        
        console_entry_point()
        
        mock_main.assert_called_once()
        mock_exit.assert_called_once_with(1)


class TestSignalHandling:
    """Test cases for signal handling."""

    @patch('pgsd.main.cleanup')
    @patch('sys.exit')
    def test_signal_handler(self, mock_exit, mock_cleanup):
        """Test signal handler function."""
        from pgsd.main import signal_handler
        
        signal_handler(2, None)  # SIGINT
        
        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(130)  # 128 + 2

    def test_setup_signal_handlers(self):
        """Test signal handlers setup."""
        from pgsd.main import setup_signal_handlers
        
        # Should not raise any exceptions
        setup_signal_handlers()


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    @patch('pgsd.main.CLIManager')
    def test_main_with_configuration_error(self, mock_cli_manager):
        """Test main function with configuration error."""
        from pgsd.exceptions.config import ConfigurationError
        
        mock_cli = Mock()
        mock_cli_manager.return_value = mock_cli
        mock_cli.run.side_effect = ConfigurationError("Test config error")
        
        args = ['version']
        exit_code = main(args)
        assert exit_code == 2

    @patch('pgsd.main.CLIManager')
    def test_main_with_pgsd_error(self, mock_cli_manager):
        """Test main function with PGSD error."""
        from pgsd.exceptions.base import PGSDError
        
        mock_cli = Mock()
        mock_cli_manager.return_value = mock_cli
        mock_cli.run.side_effect = PGSDError("Test PGSD error")
        
        args = ['version']
        exit_code = main(args)
        assert exit_code == 1

    @patch('pgsd.main.CLIManager')
    def test_main_with_verbose_exception(self, mock_cli_manager):
        """Test main function with verbose flag and exception."""
        mock_cli = Mock()
        mock_cli_manager.return_value = mock_cli
        mock_cli.run.side_effect = Exception("Test error")
        
        args = ['--verbose', 'version']
        exit_code = main(args)
        assert exit_code == 1


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_full_version_workflow(self):
        """Test complete version command workflow."""
        # This tests the entire stack from main() to CLI to command execution
        args = ['version']
        exit_code = main(args)
        
        assert exit_code == 0

    @pytest.mark.skip(reason="Requires database setup")
    def test_full_compare_workflow_dry_run(self):
        """Test complete compare command workflow in dry-run mode."""
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'test_db',
            '--target-host', 'localhost', 
            '--target-db', 'test_db',
            '--dry-run'
        ]
        
        # This should work without actual database connections
        exit_code = main(args)
        assert exit_code == 0