"""Markdown report generator for schema comparison results.

This module implements the MarkdownReporter class which generates Markdown reports
from schema comparison results using built-in templates.
"""

import logging
from typing import Dict, Any, List

from jinja2 import Template

from .base import BaseReporter, ReportFormat, ReportMetadata, ReportConfig
from .templates import BuiltinTemplates
from .grouping import group_changes_by_table, get_table_summary, GroupedDiffResult
from ..core.analyzer import DiffResult
from ..exceptions.processing import ProcessingError


logger = logging.getLogger(__name__)


class MarkdownReporter(BaseReporter):
    """Markdown report generator.
    
    Generates Markdown reports from schema comparison results using Jinja2 templates.
    Supports GitHub Flavored Markdown (GFM) for enhanced formatting.
    
    Attributes:
        format (ReportFormat): Always ReportFormat.MARKDOWN
        config (ReportConfig): Configuration for report generation
    """

    def __init__(self, config: ReportConfig = None):
        """Initialize the Markdown reporter.
        
        Args:
            config: Report configuration (uses defaults if None)
        """
        super().__init__(config)
        self._template = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def format(self) -> ReportFormat:
        """Get the report format this reporter generates."""
        return ReportFormat.MARKDOWN

    def generate_content(
        self, diff_result: DiffResult, metadata: ReportMetadata
    ) -> str:
        """Generate Markdown report content.
        
        Args:
            diff_result: Schema comparison results
            metadata: Report metadata
            
        Returns:
            Markdown report content as string
            
        Raises:
            ProcessingError: If template rendering fails
        """
        try:
            # Get Markdown template
            template = self._get_template()
            
            # Prepare template context
            context = self._prepare_template_context(diff_result, metadata)
            
            # Generate details content only if not using table grouping
            if not self.config.group_by_table:
                details_content = self._generate_details_content(diff_result)
                context["content"] = details_content
            else:
                context["content"] = ""  # Empty content for grouped view
            
            # Render template
            markdown_content = template.render(**context)
            
            self.logger.info(
                f"Generated Markdown report with {len(markdown_content)} characters"
            )
            
            return markdown_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate Markdown report: {e}")
            raise ProcessingError(f"Markdown report generation failed: {str(e)}")

    def _get_template(self) -> Template:
        """Get or load the Markdown template.
        
        Returns:
            Jinja2 Template object
        """
        if self._template is None:
            template_content = BuiltinTemplates.MARKDOWN_TEMPLATE
            self._template = Template(template_content)
            self.logger.debug("Loaded Markdown template")
        
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

    def _generate_details_content(self, diff_result: DiffResult) -> str:
        """Generate detailed changes content for the report.
        
        Args:
            diff_result: Schema comparison results
            
        Returns:
            Markdown formatted details content
        """
        sections = []
        
        # Tables section
        if self._has_table_changes(diff_result):
            sections.append(self._generate_tables_section(diff_result))
        
        # Columns section
        if self._has_column_changes(diff_result):
            sections.append(self._generate_columns_section(diff_result))
        
        # Constraints section
        if self._has_constraint_changes(diff_result):
            sections.append(self._generate_constraints_section(diff_result))
        
        # Indexes section
        if self._has_index_changes(diff_result):
            sections.append(self._generate_indexes_section(diff_result))
        
        return "\n\n".join(sections)

    def _generate_tables_section(self, diff_result: DiffResult) -> str:
        """Generate the tables section of the report."""
        lines = ["## Tables"]
        
        # Added tables
        if diff_result.tables.get("added"):
            lines.append("\n### Added Tables")
            for table in diff_result.tables["added"]:
                lines.append(f"- **{self._escape_markdown(table['name'])}**")
                if table.get("columns"):
                    lines.append("  - Columns:")
                    for col in table["columns"]:
                        col_def = f"{col['name']} {col['type']}"
                        lines.append(f"    - `{self._escape_markdown(col_def)}`")
        
        # Removed tables
        if diff_result.tables.get("removed"):
            lines.append("\n### Removed Tables")
            for table in diff_result.tables["removed"]:
                lines.append(f"- **{self._escape_markdown(table['name'])}**")
        
        # Modified tables
        if diff_result.tables.get("modified"):
            lines.append("\n### Modified Tables")
            for table in diff_result.tables["modified"]:
                lines.append(f"- **{self._escape_markdown(table['name'])}**")
                if table.get("changes"):
                    for change in table["changes"]:
                        lines.append(f"  - {self._escape_markdown(change)}")
        
        return "\n".join(lines)

    def _generate_columns_section(self, diff_result: DiffResult) -> str:
        """Generate the columns section of the report."""
        lines = ["## Columns"]
        
        # Added columns
        if diff_result.columns.get("added"):
            lines.append("\n### Added Columns")
            for col in diff_result.columns["added"]:
                table_name = col.get("table", "Unknown")
                col_name = col.get("name", "Unknown")
                col_type = col.get("type", "Unknown")
                lines.append(
                    f"- **{self._escape_markdown(table_name)}**: "
                    f"`{self._escape_markdown(col_name)} {self._escape_markdown(col_type)}`"
                )
        
        # Removed columns
        if diff_result.columns.get("removed"):
            lines.append("\n### Removed Columns")
            for col in diff_result.columns["removed"]:
                table_name = col.get("table", "Unknown")
                col_name = col.get("name", "Unknown")
                lines.append(
                    f"- **{self._escape_markdown(table_name)}**: "
                    f"`{self._escape_markdown(col_name)}`"
                )
        
        # Modified columns
        if diff_result.columns.get("modified"):
            lines.append("\n### Modified Columns")
            for col in diff_result.columns["modified"]:
                table_name = col.get("table", "Unknown")
                col_name = col.get("name", "Unknown")
                lines.append(
                    f"- **{self._escape_markdown(table_name)}**: "
                    f"`{self._escape_markdown(col_name)}`"
                )
                if col.get("changes"):
                    for change in col["changes"]:
                        lines.append(f"  - {self._escape_markdown(change)}")
        
        return "\n".join(lines)

    def _generate_constraints_section(self, diff_result: DiffResult) -> str:
        """Generate the constraints section of the report."""
        lines = ["## Constraints"]
        
        # Added constraints
        if diff_result.constraints.get("added"):
            lines.append("\n### Added Constraints")
            for constraint in diff_result.constraints["added"]:
                name = constraint.get("name", "Unknown")
                type_ = constraint.get("type", "Unknown")
                table = constraint.get("table", "Unknown")
                lines.append(
                    f"- **{self._escape_markdown(name)}** "
                    f"({self._escape_markdown(type_)}) on "
                    f"`{self._escape_markdown(table)}`"
                )
        
        # Similar for removed and modified...
        
        return "\n".join(lines)

    def _generate_indexes_section(self, diff_result: DiffResult) -> str:
        """Generate the indexes section of the report."""
        lines = ["## Indexes"]
        
        # Added indexes
        if diff_result.indexes.get("added"):
            lines.append("\n### Added Indexes")
            for index in diff_result.indexes["added"]:
                name = index.get("name", "Unknown")
                table = index.get("table", "Unknown")
                lines.append(
                    f"- **{self._escape_markdown(name)}** on "
                    f"`{self._escape_markdown(table)}`"
                )
        
        # Similar for removed and modified...
        
        return "\n".join(lines)

    def _has_table_changes(self, diff_result: DiffResult) -> bool:
        """Check if there are any table changes."""
        return any([
            diff_result.tables.get("added"),
            diff_result.tables.get("removed"),
            diff_result.tables.get("modified")
        ])

    def _has_column_changes(self, diff_result: DiffResult) -> bool:
        """Check if there are any column changes."""
        return any([
            diff_result.columns.get("added"),
            diff_result.columns.get("removed"),
            diff_result.columns.get("modified")
        ])

    def _has_constraint_changes(self, diff_result: DiffResult) -> bool:
        """Check if there are any constraint changes."""
        return any([
            diff_result.constraints.get("added"),
            diff_result.constraints.get("removed"),
            diff_result.constraints.get("modified")
        ])

    def _has_index_changes(self, diff_result: DiffResult) -> bool:
        """Check if there are any index changes."""
        return any([
            diff_result.indexes.get("added"),
            diff_result.indexes.get("removed"),
            diff_result.indexes.get("modified")
        ])

    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for Markdown
        """
        if not text:
            return ""
        
        # Characters that need escaping in Markdown
        special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', 
                        '#', '+', '-', '.', '!', '|']
        
        escaped = str(text)
        for char in special_chars:
            escaped = escaped.replace(char, f'\\{char}')
        
        return escaped

    def validate_output(self, content: str) -> bool:
        """Validate that the generated content is valid Markdown.
        
        Args:
            content: Generated Markdown content
            
        Returns:
            True if valid, False otherwise
        """
        if not content or not content.strip():
            self.logger.warning("Empty or whitespace-only content")
            return False
        
        # Check for required headers
        required_headers = [
            "# PostgreSQL Schema Diff Report",
            "## Metadata",
            "## Summary"
        ]
        
        for header in required_headers:
            if header not in content:
                self.logger.warning(f"Missing required header: {header}")
                return False
        
        # Check for basic Markdown structure
        lines = content.strip().split('\n')
        if not lines[0].startswith('#'):
            self.logger.warning("Content does not start with a header")
            return False
        
        self.logger.debug("Markdown validation passed")
        return True

    def get_mime_type(self) -> str:
        """Get the MIME type for Markdown reports.
        
        Returns:
            MIME type string
        """
        return "text/markdown"

    def get_file_extension(self) -> str:
        """Get the file extension for Markdown reports.
        
        Returns:
            File extension with leading dot
        """
        return ".md"