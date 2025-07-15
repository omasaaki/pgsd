"""CLI module for PGSD.

This module provides command-line interface functionality for the PostgreSQL
Schema Diff tool, including argument parsing, command execution, and
configuration integration.

Components:
    main: Main CLI manager and entry point
    commands: Individual command implementations
    progress: Progress reporting for CLI operations
"""

from .main import CLIManager

__all__ = [
    "CLIManager",
]

__version__ = "1.0.0"