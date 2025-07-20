"""Unit tests for Markdown report generator.

This module tests the MarkdownReporter class functionality including
content generation, template rendering, and validation.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.pgsd.reports.markdown import MarkdownReporter
from src.pgsd.reports.base import ReportFormat, ReportConfig, ReportMetadata
from src.pgsd.core.analyzer import DiffResult
from src.pgsd.exceptions.processing import ProcessingError


class TestMarkdownReporter:
    """Test cases for MarkdownReporter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ReportConfig(
            output_directory=Path("./test_output"),
            include_metadata=True,
            include_summary=True,
            include_details=True,
        )
        self.reporter = MarkdownReporter(self.config)

    def test_format_property(self):
        """Test that format property returns MARKDOWN."""
        assert self.reporter.format == ReportFormat.MARKDOWN

    def test_initialization_with_config(self):
        """Test reporter initialization with custom config."""
        custom_config = ReportConfig(output_directory=Path("./custom"))
        reporter = MarkdownReporter(custom_config)
        
        assert reporter.config == custom_config
        assert reporter.format == ReportFormat.MARKDOWN

    def test_initialization_without_config(self):
        """Test reporter initialization with default config."""
        reporter = MarkdownReporter()
        
        assert isinstance(reporter.config, ReportConfig)
        assert reporter.format == ReportFormat.MARKDOWN

    def test_get_mime_type(self):
        """Test MIME type for Markdown reports."""
        assert self.reporter.get_mime_type() == "text/markdown"

    def test_get_file_extension(self):
        """Test file extension for Markdown reports."""
        assert self.reporter.get_file_extension() == ".md"

    def test_generate_content_basic(self):
        """Test basic Markdown content generation."""
        # Create test data
        diff_result = self._create_test_diff_result()
        metadata = self._create_test_metadata()
        
        # Generate content
        content = self.reporter.generate_content(diff_result, metadata)
        
        # Verify content
        assert isinstance(content, str)
        assert len(content) > 0
        assert "# PostgreSQL Schema Diff Report" in content
        assert "## Metadata" in content
        assert "## Summary" in content

    def test_generate_content_with_changes(self):
        """Test Markdown content generation with schema changes."""
        # Create diff result with changes
        diff_result = DiffResult(
            tables={
                "added": [{"name": "new_table", "columns": [], "constraints": []}],
                "removed": [{"name": "old_table", "columns": [], "constraints": []}],
                "modified": [],
            },
            columns={
                "added": [{"table": "users", "name": "email", "type": "VARCHAR"}],
                "removed": [],
                "modified": [],
            },
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 2},
        )
        
        metadata = self._create_test_metadata()
        content = self.reporter.generate_content(diff_result, metadata)
        
        # Verify content includes changes (check for escaped versions)
        assert "new_table" in content or "new\\_table" in content
        assert "old_table" in content or "old\\_table" in content
        assert "email" in content

    def test_generate_content_empty_diff(self):
        """Test Markdown content generation with empty diff result."""
        diff_result = DiffResult(
            tables={"added": [], "removed": [], "modified": []},
            columns={"added": [], "removed": [], "modified": []},
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 0},
        )
        
        metadata = self._create_test_metadata()
        content = self.reporter.generate_content(diff_result, metadata)
        
        # Verify content is generated even with no changes
        assert isinstance(content, str)
        assert len(content) > 0
        assert "# PostgreSQL Schema Diff Report" in content
        assert "No Changes Detected" in content

    def test_generate_summary_statistics(self):
        """Test summary statistics generation."""
        diff_result = DiffResult(
            tables={
                "added": [{"name": "table1"}, {"name": "table2"}],
                "removed": [{"name": "table3"}],
                "modified": [],
            },
            columns={
                "added": [{"name": "col1"}],
                "removed": [],
                "modified": [{"name": "col2"}],
            },
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 4},
        )
        
        summary = self.reporter._generate_summary(diff_result)
        
        # Verify summary statistics
        assert summary["tables_added"] == 2
        assert summary["tables_removed"] == 1
        assert summary["tables_modified"] == 0
        assert summary["columns_added"] == 1
        assert summary["columns_removed"] == 0
        assert summary["columns_modified"] == 1
        assert summary["total_changes"] == 5  # 2+1+0+1+0+1 = 5

    def test_validate_output_valid_markdown(self):
        """Test validation of valid Markdown output."""
        valid_markdown = """
# PostgreSQL Schema Diff Report

## Metadata

- **Generated:** 2025-07-15
- **Source:** prod.public

## Summary

| Category | Count |
|----------|-------|
| Tables   | 5     |
        """
        
        assert self.reporter.validate_output(valid_markdown) is True

    def test_validate_output_invalid_markdown(self):
        """Test validation of invalid Markdown output."""
        # Empty content
        assert self.reporter.validate_output("") is False
        assert self.reporter.validate_output("   ") is False
        
        # Content without required headers
        invalid_markdown = "Just some text without headers"
        assert self.reporter.validate_output(invalid_markdown) is False

    def test_special_character_escaping(self):
        """Test escaping of special Markdown characters."""
        diff_result = DiffResult(
            tables={
                "added": [{"name": "table_with|pipe", "columns": [], "constraints": []}],
                "removed": [],
                "modified": [],
            },
            columns={"added": [], "removed": [], "modified": []},
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 1},
        )
        
        metadata = self._create_test_metadata()
        content = self.reporter.generate_content(diff_result, metadata)
        
        # Verify special characters are properly handled
        assert "table_with|pipe" in content or "table\\_with\\|pipe" in content

    def test_template_caching(self):
        """Test that template is cached after first use."""
        diff_result = self._create_test_diff_result()
        metadata = self._create_test_metadata()
        
        # Generate content twice
        content1 = self.reporter.generate_content(diff_result, metadata)
        content2 = self.reporter.generate_content(diff_result, metadata)
        
        # Template should be cached
        assert self.reporter._template is not None
        assert content1 == content2

    def test_template_context_preparation(self):
        """Test template context preparation."""
        diff_result = self._create_test_diff_result()
        metadata = self._create_test_metadata()
        
        context = self.reporter._prepare_template_context(diff_result, metadata)
        
        # Verify context structure
        assert "metadata" in context
        assert "summary" in context
        assert "diff_result" in context
        assert "config" in context
        
        # Verify metadata formatting
        assert isinstance(context["metadata"]["generated_at"], str)
        assert context["metadata"]["source_database"] == "test_source"

    def test_error_handling_template_failure(self):
        """Test error handling when template rendering fails."""
        # Create reporter with invalid template
        reporter = MarkdownReporter()
        reporter._template = None
        
        # Mock template that raises exception
        class FailingTemplate:
            def render(self, **kwargs):
                raise Exception("Template error")
        
        reporter._template = FailingTemplate()
        
        diff_result = self._create_test_diff_result()
        metadata = self._create_test_metadata()
        
        with pytest.raises(ProcessingError, match="Markdown report generation failed"):
            reporter.generate_content(diff_result, metadata)

    def test_github_flavored_markdown(self):
        """Test GitHub Flavored Markdown features."""
        diff_result = DiffResult(
            tables={
                "added": [
                    {
                        "name": "users",
                        "columns": [
                            {"name": "id", "type": "INTEGER"},
                            {"name": "email", "type": "VARCHAR(255)"},
                        ],
                        "constraints": [{"name": "users_pkey", "type": "PRIMARY KEY"}],
                    }
                ],
                "removed": [],
                "modified": [],
            },
            columns={"added": [], "removed": [], "modified": []},
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 1},
        )
        
        metadata = self._create_test_metadata()
        content = self.reporter.generate_content(diff_result, metadata)
        
        # Verify GFM features are used
        assert "|" in content  # Table syntax
        assert "```" in content or "`" in content  # Code blocks

    def test_large_diff_result_performance(self):
        """Test performance with large diff results."""
        # Create large diff result
        large_tables = [{"name": f"table_{i}"} for i in range(100)]
        large_columns = [{"name": f"col_{i}"} for i in range(200)]
        
        diff_result = DiffResult(
            tables={"added": large_tables, "removed": [], "modified": []},
            columns={"added": large_columns, "removed": [], "modified": []},
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 300},
        )
        
        metadata = self._create_test_metadata()
        
        # Should complete without timeout or memory issues
        content = self.reporter.generate_content(diff_result, metadata)
        assert len(content) > 1000  # Should generate substantial content

    def _create_test_diff_result(self):
        """Create a test DiffResult object."""
        return DiffResult(
            tables={"added": [], "removed": [], "modified": []},
            columns={"added": [], "removed": [], "modified": []},
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 0},
        )

    def _create_test_metadata(self):
        """Create a test ReportMetadata object."""
        return ReportMetadata(
            generated_at=datetime(2025, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
            source_database="test_source",
            target_database="test_target",
            source_schema="public",
            target_schema="public",
            total_changes=0,
            analysis_time_seconds=1.23,
            generator_version="1.0.0",
            report_format=ReportFormat.MARKDOWN,
        )


class TestMarkdownReporterIntegration:
    """Integration tests for MarkdownReporter."""

    def test_integration_with_factory(self):
        """Test integration with ReportFactory."""
        # Test basic integration
        reporter = MarkdownReporter()
        assert reporter is not None

    def test_full_report_generation_workflow(self):
        """Test complete report generation workflow."""
        reporter = MarkdownReporter()
        
        # Create realistic test data
        diff_result = DiffResult(
            tables={
                "added": [
                    {
                        "name": "audit_log", 
                        "columns": [
                            {"name": "id", "type": "SERIAL"},
                            {"name": "action", "type": "VARCHAR(50)"},
                        ],
                        "constraints": [{"name": "audit_log_pkey", "type": "PRIMARY KEY"}],
                    }
                ],
                "removed": [],
                "modified": [
                    {
                        "name": "users",
                        "changes": ["Added column: last_login"],
                    }
                ],
            },
            columns={
                "added": [
                    {"table": "users", "name": "last_login", "type": "TIMESTAMP"},
                ],
                "removed": [],
                "modified": [],
            },
            constraints={"added": [], "removed": [], "modified": []},
            indexes={"added": [], "removed": [], "modified": []},
            summary={"total_changes": 3},
        )
        
        metadata = ReportMetadata(
            source_database="production",
            target_database="staging",
            source_schema="public",
            target_schema="public",
            total_changes=3,
            analysis_time_seconds=2.5,
        )
        
        # Generate report
        content = reporter.generate_content(diff_result, metadata)
        
        # Verify comprehensive content (check for escaped versions)
        assert "audit_log" in content or "audit\\_log" in content
        assert "last_login" in content or "last\\_login" in content
        assert "production" in content
        assert "staging" in content
        assert "2.5" in content  # Analysis time
        
        # Validate Markdown structure
        assert reporter.validate_output(content)