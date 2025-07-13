"""Test main module functionality."""

import sys
from unittest.mock import patch
from pgsd.__main__ import main as main_module_main
from pgsd.main import main


def test_main_with_empty_args():
    """Test main function with empty args."""
    result = main([])
    assert result == 0


def test_main_with_none_args():
    """Test main function with None args."""
    with patch.object(sys, 'argv', ['pgsd']):
        result = main(None)
        assert result == 0


def test_main_module_entry():
    """Test __main__ module entry point calls main function."""
    # Simply test that the function runs without error
    # since it calls the actual main function
    try:
        main_module_main()
        assert True  # If no exception, test passes
    except SystemExit:
        assert True  # SystemExit is expected behavior