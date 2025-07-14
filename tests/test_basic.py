"""Basic test to verify package is importable."""

import pgsd


def test_package_import():
    """Test that package can be imported."""
    assert pgsd.__version__ == "0.1.0"


def test_main_entry_point():
    """Test main entry point."""
    from pgsd.main import main

    result = main([])
    assert result == 0
