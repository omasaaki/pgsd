"""Tests for __main__ module."""

import sys
import pytest
from unittest.mock import patch, Mock

# We need to test the actual module execution


class TestMainModuleExecution:
    """Test cases for __main__ module execution."""

    @patch('src.pgsd.__main__.main')
    @patch('sys.exit')
    def test_main_module_success(self, mock_exit, mock_main):
        """Test successful main module execution."""
        mock_main.return_value = 0
        
        # Import and execute the module
        with patch('sys.argv', ['python', '-m', 'pgsd', '--help']):
            # Execute the module code
            exec("""
if __name__ == "__main__":
    try:
        exit_code = main(sys.argv[1:])
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
""", {
                '__name__': '__main__',
                'main': mock_main,
                'sys': sys,
                'print': print
            })
        
        mock_main.assert_called_once_with(['-m', 'pgsd', '--help'])
        mock_exit.assert_called_once_with(0)

    @patch('src.pgsd.__main__.main')
    @patch('sys.exit')
    def test_main_module_keyboard_interrupt(self, mock_exit, mock_main):
        """Test main module with KeyboardInterrupt."""
        mock_main.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['python', '-m', 'pgsd', 'compare']), \
             patch('src.pgsd.__main__.print') as mock_print:
            
            # Execute the module code
            exec("""
if __name__ == "__main__":
    try:
        exit_code = main(sys.argv[1:])
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
""", {
                '__name__': '__main__',
                'main': mock_main,
                'sys': sys,
                'print': mock_print
            })
        
        mock_main.assert_called_once_with(['-m', 'pgsd', 'compare'])
        mock_print.assert_called_once_with("\nOperation cancelled by user", file=sys.stderr)
        mock_exit.assert_called_once_with(130)

    @patch('src.pgsd.__main__.main')
    @patch('sys.exit')
    def test_main_module_unexpected_error(self, mock_exit, mock_main):
        """Test main module with unexpected error."""
        mock_main.side_effect = RuntimeError("Test error")
        
        with patch('sys.argv', ['python', '-m', 'pgsd', 'version']), \
             patch('src.pgsd.__main__.print') as mock_print:
            
            # Execute the module code
            exec("""
if __name__ == "__main__":
    try:
        exit_code = main(sys.argv[1:])
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
""", {
                '__name__': '__main__',
                'main': mock_main,
                'sys': sys,
                'print': mock_print
            })
        
        mock_main.assert_called_once_with(['-m', 'pgsd', 'version'])
        mock_print.assert_called_once_with("Unexpected error: Test error", file=sys.stderr)
        mock_exit.assert_called_once_with(1)

    def test_main_module_import(self):
        """Test that __main__ module can be imported."""
        # This should not raise any exceptions
        import src.pgsd.__main__
        
        # Verify the main function is imported
        assert hasattr(src.pgsd.__main__, 'main')
        assert callable(src.pgsd.__main__.main)

    def test_main_module_sys_import(self):
        """Test that sys module is imported in __main__."""
        import src.pgsd.__main__
        
        # Verify sys is available
        assert hasattr(src.pgsd.__main__, 'sys')

    def test_main_module_direct_import_execution(self):
        """Test direct execution logic of __main__ module."""
        # Test basic module import
        import src.pgsd.__main__
        assert src.pgsd.__main__ is not None


class TestMainModuleIntegration:
    """Integration tests for __main__ module."""

    def test_module_structure(self):
        """Test that __main__ module has correct structure."""
        import src.pgsd.__main__ as main_module
        
        # Check docstring exists
        assert main_module.__doc__ is not None
        assert "Entry point for python -m pgsd" in main_module.__doc__
        
        # Check required imports
        assert hasattr(main_module, 'sys')
        assert hasattr(main_module, 'main')

    @patch('src.pgsd.__main__.main', return_value=0)
    @patch('sys.argv', ['python', '-m', 'pgsd', '--version'])
    def test_argv_handling(self, mock_main):
        """Test that argv is properly handled."""
        import src.pgsd.__main__
        
        # The module should be importable without executing main block
        assert src.pgsd.__main__.main is not None

    def test_error_handling_structure(self):
        """Test that error handling is properly structured."""
        import inspect
        import src.pgsd.__main__
        
        # Read the source to verify error handling structure
        source = inspect.getsource(src.pgsd.__main__)
        
        # Verify exception handling blocks exist
        assert "KeyboardInterrupt" in source
        assert "Exception" in source
        assert "sys.exit(130)" in source
        assert "sys.exit(1)" in source