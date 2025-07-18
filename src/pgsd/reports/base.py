"""Base classes for report generation in PGSD.

This module provides the foundation for generating schema comparison reports
in multiple formats (HTML, Markdown, JSON, XML).

Classes:
    ReportFormat: Enumeration of supported report formats
    BaseReporter: Abstract base class for all report generators
    ReportMetadata: Data class for report metadata
    ReportConfig: Configuration class for report generation
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.analyzer import DiffResult
from ..exceptions.processing import ProcessingError


logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats."""

    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"

    @classmethod
    def from_string(cls, format_str: str) -> "ReportFormat":
        """Create ReportFormat from string.

        Args:
            format_str: Format string (case-insensitive)

        Returns:
            ReportFormat enum value

        Raises:
            ProcessingError: If format string is not supported
        """
        try:
            return cls(format_str.lower())
        except ValueError:
            supported = [f.value for f in cls]
            raise ProcessingError(
                f"Unsupported report format: {format_str}. "
                f"Supported formats: {', '.join(supported)}"
            )

    @property
    def file_extension(self) -> str:
        """Get file extension for this format."""
        extensions = {
            ReportFormat.HTML: ".html",
            ReportFormat.MARKDOWN: ".md",
            ReportFormat.JSON: ".json",
            ReportFormat.XML: ".xml",
        }
        return extensions[self]

    @property
    def mime_type(self) -> str:
        """Get MIME type for this format."""
        mime_types = {
            ReportFormat.HTML: "text/html",
            ReportFormat.MARKDOWN: "text/markdown",
            ReportFormat.JSON: "application/json",
            ReportFormat.XML: "application/xml",
        }
        return mime_types[self]


@dataclass
class ReportMetadata:
    """Metadata for schema comparison reports."""

    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_database: str = ""
    target_database: str = ""
    source_schema: str = ""
    target_schema: str = ""
    total_changes: int = 0
    analysis_time_seconds: float = 0.0
    generator_version: str = "1.0.0"
    report_format: ReportFormat = ReportFormat.HTML

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "source_database": self.source_database,
            "target_database": self.target_database,
            "source_schema": self.source_schema,
            "target_schema": self.target_schema,
            "total_changes": self.total_changes,
            "analysis_time_seconds": self.analysis_time_seconds,
            "generator_version": self.generator_version,
            "report_format": self.report_format.value,
        }


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    output_directory: Path = field(default_factory=lambda: Path("./reports"))
    filename_template: str = "schema_diff_{timestamp}_{format}"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    include_metadata: bool = True
    include_summary: bool = True
    include_details: bool = True
    timezone: str = "UTC"
    overwrite_existing: bool = True
    
    # Table grouping options
    group_by_table: bool = True
    show_legacy_format: bool = False
    collapse_sections: bool = True
    show_change_counts: bool = True

    def __post_init__(self):
        """Post-initialization processing."""
        # Ensure output directory is Path object
        if isinstance(self.output_directory, str):
            self.output_directory = Path(self.output_directory)

    def generate_filename(
        self, report_format: ReportFormat, timestamp: Optional[datetime] = None
    ) -> str:
        """Generate filename for report.

        Args:
            report_format: Report format
            timestamp: Timestamp to use (defaults to current time)

        Returns:
            Generated filename with extension
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        timestamp_str = timestamp.strftime(self.timestamp_format)

        filename = self.filename_template.format(
            timestamp=timestamp_str, format=report_format.value
        )

        return filename + report_format.file_extension

    def get_output_path(
        self, report_format: ReportFormat, timestamp: Optional[datetime] = None
    ) -> Path:
        """Get full output path for report.

        Args:
            report_format: Report format
            timestamp: Timestamp to use (defaults to current time)

        Returns:
            Full path for report file
        """
        filename = self.generate_filename(report_format, timestamp)
        return self.output_directory / filename


class BaseReporter(ABC):
    """Abstract base class for report generators.

    This class defines the interface that all report generators must implement.
    It provides common functionality for handling report metadata, configuration,
    and file operations.

    Attributes:
        format (ReportFormat): The format this reporter generates
        config (ReportConfig): Configuration for report generation
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialize the reporter.

        Args:
            config: Report configuration (uses defaults if None)
        """
        self.config = config or ReportConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def format(self) -> ReportFormat:
        """Get the report format this reporter generates."""

    @abstractmethod
    def generate_content(
        self, diff_result: DiffResult, metadata: ReportMetadata
    ) -> str:
        """Generate report content.

        Args:
            diff_result: Schema comparison results
            metadata: Report metadata

        Returns:
            Generated report content as string

        Raises:
            ProcessingError: If content generation fails
        """

    def create_metadata(self, diff_result: DiffResult) -> ReportMetadata:
        """Create report metadata from diff result.

        Args:
            diff_result: Schema comparison results

        Returns:
            Report metadata
        """
        metadata = ReportMetadata(
            report_format=self.format,
            total_changes=diff_result.summary.get("total_changes", 0),
        )

        # Extract metadata from diff result if available
        if hasattr(diff_result, "metadata") and diff_result.metadata:
            result_meta = diff_result.metadata
            metadata.source_database = result_meta.get("source_database", "")
            metadata.target_database = result_meta.get("target_database", "")
            metadata.source_schema = result_meta.get("source_schema", "")
            metadata.target_schema = result_meta.get("target_schema", "")
            metadata.analysis_time_seconds = result_meta.get(
                "analysis_time_seconds", 0.0
            )
            

        return metadata

    def validate_diff_result(self, diff_result: DiffResult) -> None:
        """Validate diff result before generating report.

        Args:
            diff_result: Schema comparison results

        Raises:
            ProcessingError: If diff result is invalid
        """
        if not isinstance(diff_result, DiffResult):
            raise ProcessingError("Invalid diff_result: must be DiffResult instance")

        if not hasattr(diff_result, "summary") or not diff_result.summary:
            raise ProcessingError("Invalid diff_result: missing summary")

    def ensure_output_directory(self) -> None:
        """Ensure output directory exists.

        Raises:
            ProcessingError: If directory creation fails
        """
        try:
            self.config.output_directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(
                f"Output directory ensured: {self.config.output_directory}"
            )
        except Exception as e:
            raise ProcessingError(f"Failed to create output directory: {e}")

    def write_report(
        self,
        content: str,
        output_path: Optional[Path] = None,
        timestamp: Optional[datetime] = None,
    ) -> Path:
        """Write report content to file.

        Args:
            content: Report content to write
            output_path: Custom output path (overrides config)
            timestamp: Timestamp for filename generation

        Returns:
            Path to written report file

        Raises:
            ProcessingError: If file writing fails
        """
        if output_path is None:
            output_path = self.config.get_output_path(self.format, timestamp)
        elif output_path.is_dir():
            # If a directory is provided, generate filename within that directory
            filename = self.config.generate_filename(self.format, timestamp)
            output_path = output_path / filename

        # Check if file exists and overwrite is disabled
        if output_path.exists() and not self.config.overwrite_existing:
            raise ProcessingError(
                f"Report file already exists: {output_path}. "
                "Set overwrite_existing=True to overwrite."
            )

        try:
            self.ensure_output_directory()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Report written to: {output_path}")
            return output_path

        except Exception as e:
            raise ProcessingError(f"Failed to write report file {output_path}: {e}")

    def generate_report(
        self,
        diff_result: DiffResult,
        output_path: Optional[Path] = None,
        metadata: Optional[ReportMetadata] = None,
    ) -> Path:
        """Generate complete report and write to file.

        This is the main method that orchestrates the entire report generation process.

        Args:
            diff_result: Schema comparison results
            output_path: Custom output path (overrides config)
            metadata: Custom metadata (will be created if None)

        Returns:
            Path to generated report file

        Raises:
            ProcessingError: If report generation fails
        """
        try:
            self.logger.info(f"Generating {self.format.value} report")

            # Validate input
            self.validate_diff_result(diff_result)

            # Create metadata
            if metadata is None:
                metadata = self.create_metadata(diff_result)

            # Generate content
            content = self.generate_content(diff_result, metadata)

            # Write to file
            output_path = self.write_report(content, output_path)

            self.logger.info(
                f"Successfully generated {self.format.value} report: {output_path}"
            )
            return output_path

        except Exception as e:
            self.logger.error(f"Failed to generate {self.format.value} report: {e}")
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(f"Report generation failed: {e}")

    def get_summary_data(self, diff_result: DiffResult) -> Dict[str, Any]:
        """Extract summary data from diff result.

        Args:
            diff_result: Schema comparison results

        Returns:
            Dictionary with summary data
        """
        summary = diff_result.summary.copy()

        # Add detailed counts
        for category in [
            "tables",
            "columns",
            "constraints",
            "indexes",
            "views",
            "functions",
            "sequences",
            "triggers",
        ]:
            if hasattr(diff_result, category):
                category_data = getattr(diff_result, category)
                summary[f"{category}_added"] = len(category_data.get("added", []))
                summary[f"{category}_removed"] = len(category_data.get("removed", []))
                summary[f"{category}_modified"] = len(category_data.get("modified", []))

        return summary

    def __repr__(self) -> str:
        """String representation of the reporter."""
        return f"{self.__class__.__name__}(format={self.format.value})"
