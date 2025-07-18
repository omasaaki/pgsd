"""HTML report generator for schema comparison results.

This module implements the HTMLReporter class which generates HTML reports
from schema comparison results using built-in templates.
"""

import logging
from typing import Dict, Any

from jinja2 import Template

from .base import BaseReporter, ReportFormat, ReportMetadata, ReportConfig
from .templates import BuiltinTemplates
from .templates_simple import SIMPLE_HTML_TEMPLATE
from .grouping import group_changes_by_table, get_table_summary, GroupedDiffResult
from ..core.analyzer import DiffResult
from ..exceptions.processing import ProcessingError


logger = logging.getLogger(__name__)


class HTMLReporter(BaseReporter):
    """HTML report generator.
    
    Generates HTML reports from schema comparison results using Jinja2 templates.
    The generated HTML includes embedded CSS for styling and responsive design.
    
    Attributes:
        format (ReportFormat): Always ReportFormat.HTML
        config (ReportConfig): Configuration for report generation
    """

    def __init__(self, config: ReportConfig = None):
        """Initialize the HTML reporter.
        
        Args:
            config: Report configuration (uses defaults if None)
        """
        super().__init__(config)
        self._template = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def format(self) -> ReportFormat:
        """Get the report format this reporter generates."""
        return ReportFormat.HTML

    def generate_content(
        self, diff_result: DiffResult, metadata: ReportMetadata
    ) -> str:
        """Generate HTML report content.
        
        Args:
            diff_result: Schema comparison results
            metadata: Report metadata
            
        Returns:
            HTML report content as string
            
        Raises:
            ProcessingError: If template rendering fails
        """
        try:
            # Get HTML template
            template = self._get_template()
            
            # Prepare template context
            context = self._prepare_template_context(diff_result, metadata)
            
            # Render template
            html_content = template.render(**context)
            
            self.logger.info(
                f"Generated HTML report with {len(html_content)} characters"
            )
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            raise ProcessingError(f"HTML report generation failed: {str(e)}")

    def _get_template(self) -> Template:
        """Get and cache the HTML template.
        
        Returns:
            Jinja2 Template instance
            
        Raises:
            ProcessingError: If template loading fails
        """
        if self._template is None:
            try:
                # Use simple template temporarily to avoid Jinja2 syntax error
                template_content = SIMPLE_HTML_TEMPLATE
                self._template = Template(template_content)
                self.logger.debug("HTML template (simple) loaded and cached")
            except Exception as e:
                raise ProcessingError(f"Failed to load HTML template: {str(e)}")
        
        return self._template

    def _prepare_template_context(
        self, diff_result: DiffResult, metadata: ReportMetadata
    ) -> Dict[str, Any]:
        """Prepare context data for template rendering.
        
        Args:
            diff_result: Schema comparison results
            metadata: Report metadata
            
        Returns:
            Dictionary with template context data
        """
        # Generate summary statistics
        summary = self._generate_summary(diff_result)
        
        # Prepare metadata for template
        template_metadata = {
            "generated_at": metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "source_database": metadata.source_database,
            "target_database": metadata.target_database,
            "source_schema": metadata.source_schema,
            "target_schema": metadata.target_schema,
            "analysis_time_seconds": metadata.analysis_time_seconds,
            "generator_version": metadata.generator_version,
        }
        
        # Prepare grouped data if table grouping is enabled
        context = {
            "metadata": template_metadata,
            "summary": summary,
            "diff_result": diff_result,
            "config": self.config,
        }
        
        if self.config.group_by_table:
            grouped_result = group_changes_by_table(diff_result)
            context.update({
                "grouped_result": grouped_result,
                "table_summaries": {
                    table.table_name: get_table_summary(table) 
                    for table in grouped_result.all_tables
                },
                "use_table_grouping": True,
            })
        else:
            context["use_table_grouping"] = False
            
        return context

    def _generate_summary(self, diff_result: DiffResult) -> Dict[str, Any]:
        """Generate summary statistics from diff result.
        
        Args:
            diff_result: Schema comparison results
            
        Returns:
            Dictionary with summary statistics
        """
        # Table statistics
        tables_added = len(diff_result.tables.get("added", []))
        tables_removed = len(diff_result.tables.get("removed", []))
        tables_modified = len(diff_result.tables.get("modified", []))
        
        # Column statistics
        columns_added = len(diff_result.columns.get("added", []))
        columns_removed = len(diff_result.columns.get("removed", []))
        columns_modified = len(diff_result.columns.get("modified", []))
        
        # Constraint statistics
        constraints_added = len(diff_result.constraints.get("added", []))
        constraints_removed = len(diff_result.constraints.get("removed", []))
        constraints_modified = len(diff_result.constraints.get("modified", []))
        
        # Index statistics
        indexes_added = len(diff_result.indexes.get("added", []))
        indexes_removed = len(diff_result.indexes.get("removed", []))
        indexes_modified = len(diff_result.indexes.get("modified", []))
        
        # Calculate totals
        total_changes = (
            tables_added + tables_removed + tables_modified +
            columns_added + columns_removed + columns_modified +
            constraints_added + constraints_removed + constraints_modified +
            indexes_added + indexes_removed + indexes_modified
        )
        
        return {
            "total_changes": total_changes,
            "tables_added": tables_added,
            "tables_removed": tables_removed,
            "tables_modified": tables_modified,
            "columns_added": columns_added,
            "columns_removed": columns_removed,
            "columns_modified": columns_modified,
            "constraints_added": constraints_added,
            "constraints_removed": constraints_removed,
            "constraints_modified": constraints_modified,
            "indexes_added": indexes_added,
            "indexes_removed": indexes_removed,
            "indexes_modified": indexes_modified,
        }

    def validate_output(self, content: str) -> bool:
        """Validate generated HTML content.
        
        Args:
            content: Generated HTML content
            
        Returns:
            True if content appears valid, False otherwise
        """
        if not content or not content.strip():
            return False
            
        # Basic HTML structure checks
        required_elements = [
            "<!DOCTYPE html>",
            "<html",
            "<head>",
            "<body>",
            "</html>",
        ]
        
        content_lower = content.lower()
        for element in required_elements:
            if element.lower() not in content_lower:
                self.logger.warning(f"Missing required HTML element: {element}")
                return False
        
        # Check for basic content sections
        if "PostgreSQL Schema Diff Report" not in content:
            self.logger.warning("Missing report title")
            return False
            
        return True

    def get_mime_type(self) -> str:
        """Get MIME type for HTML reports."""
        return "text/html"

    def get_file_extension(self) -> str:
        """Get file extension for HTML reports."""
        return ".html"