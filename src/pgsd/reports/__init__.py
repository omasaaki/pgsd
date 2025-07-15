"""Report generation module for PGSD.

This module provides comprehensive report generation functionality
for PostgreSQL schema comparison results in multiple formats.

Components:
- BaseReporter: Abstract base class for all report generators
- ReportFactory: Factory for creating appropriate report generators
- TemplateManager: Template management for report rendering
- ReportFormat: Enumeration of supported formats
- ReportConfig: Configuration for report generation

Usage:
    from pgsd.reports import create_reporter, ReportFormat, ReportConfig

    # Create a reporter
    config = ReportConfig(output_directory="./output")
    reporter = create_reporter(ReportFormat.HTML, config)

    # Generate report
    output_path = reporter.generate_report(diff_result)
"""

from .base import (
    BaseReporter,
    ReportFormat,
    ReportConfig,
    ReportMetadata,
)
from .factory import (
    ReportFactory,
    create_reporter,
    create_reporter_from_string,
    get_available_formats,
    is_format_supported,
    register_global_reporter,
)
from .templates import (
    TemplateManager,
    BuiltinTemplates,
    get_template,
)
from .html import HTMLReporter
from .markdown import MarkdownReporter

# Register reporters in global factory
register_global_reporter(ReportFormat.HTML, HTMLReporter)
register_global_reporter(ReportFormat.MARKDOWN, MarkdownReporter)

# Export main classes and functions
__all__ = [
    # Base classes
    "BaseReporter",
    "ReportFormat",
    "ReportConfig",
    "ReportMetadata",
    # Factory functions
    "ReportFactory",
    "create_reporter",
    "create_reporter_from_string",
    "get_available_formats",
    "is_format_supported",
    "register_global_reporter",
    # Template management
    "TemplateManager",
    "BuiltinTemplates",
    "get_template",
    # Specific reporters
    "HTMLReporter",
    "MarkdownReporter",
]

# Version information
__version__ = "1.0.0"

# Module metadata
__author__ = "PGSD Development Team"
__description__ = "Report generation for PostgreSQL schema comparison"
__license__ = "MIT"
