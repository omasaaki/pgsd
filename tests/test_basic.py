"""Basic test to verify package is importable."""

import pgsd


def test_package_import():
    """Test that package can be imported."""
    assert pgsd.__version__ == "1.0.0"


def test_main_entry_point():
    """Test main entry point."""
    from pgsd.main import main

    # Empty args should show help and return 2
    result = main([])
    assert result == 2
