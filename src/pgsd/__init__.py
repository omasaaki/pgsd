"""PGSD - PostgreSQL Schema Diff Tool.

A comprehensive tool for comparing PostgreSQL database schemas and generating
detailed reports of differences between database structures.

This package provides:
- Database connection management with connection pooling
- Schema information collection and analysis
- Comprehensive diff detection for tables, columns, constraints, and indexes
- Multiple report formats (HTML, Markdown, JSON, XML)
- Configuration management with YAML support
- Command-line interface for easy automation

Example:
    Basic usage:
    
    from pgsd import CLIManager
    from pgsd.config import DatabaseConfig
    
    # Use CLI interface
    cli = CLIManager()
    exit_code = cli.run(['compare', '--source-host', 'localhost', '--source-db', 'db1',
                         '--target-host', 'localhost', '--target-db', 'db2'])
"""

from .core.analyzer import DiffResult
from .config.schema import DatabaseConfig, PGSDConfiguration
from .database.manager import DatabaseManager
from .reports import create_reporter, ReportFormat
from .cli import CLIManager

# Version information
__version__ = "1.0.0"
__author__ = "PGSD Development Team"
__email__ = "dev@pgsd.example.com"
__license__ = "MIT"

# Package metadata
__title__ = "pgsd"
__description__ = "PostgreSQL Schema Diff Tool"
__url__ = "https://github.com/omasaaki/pgsd"

# Export main classes and functions
__all__ = [
    # Core functionality
    "DiffResult",
    # Configuration
    "DatabaseConfig", 
    "PGSDConfiguration",
    # Database management
    "DatabaseManager",
    # Report generation
    "create_reporter",
    "ReportFormat",
    # CLI interface
    "CLIManager",
]
