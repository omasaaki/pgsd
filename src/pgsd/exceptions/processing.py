"""Processing-related exception classes."""

from typing import List, Optional
from pathlib import Path

from .base import PGSDError, ErrorSeverity, ErrorCategory


class ProcessingError(PGSDError):
    """Base class for processing-related errors."""

    default_error_code = "PROCESSING_ERROR"
    default_severity = ErrorSeverity.MEDIUM
    default_category = ErrorCategory.PROCESSING
    default_exit_code = 40
    retriable = True
    base_retry_delay = 1.0
    max_retry_delay = 10.0


class SchemaParsingError(ProcessingError):
    """Raised when schema parsing fails."""

    default_error_code = "SCHEMA_PARSING_FAILED"
    default_exit_code = 41
    retriable = False

    def __init__(
        self,
        schema_name: str,
        parsing_errors: List[str],
        line_number: Optional[int] = None,
        source_file: Optional[Path] = None,
    ) -> None:
        """Initialize schema parsing error.

        Args:
            schema_name: Name of the schema being parsed
            parsing_errors: List of specific parsing errors
            line_number: Line number where error occurred (optional)
            source_file: Source file being parsed (optional)
        """
        message = f"Failed to parse schema '{schema_name}'"

        if line_number and source_file:
            message += f" at line {line_number} in {source_file}"
        elif line_number:
            message += f" at line {line_number}"
        elif source_file:
            message += f" from {source_file}"

        # Technical details
        technical_details = {
            "schema_name": schema_name,
            "parsing_errors": parsing_errors,
            "line_number": line_number,
            "source_file": str(source_file) if source_file else None,
            "error_count": len(parsing_errors),
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Check schema definition syntax and structure",
            "Verify SQL dump format is valid and complete",
            "Ensure schema was generated with compatible pg_dump version",
        ]

        if source_file:
            recovery_suggestions.append(
                f"Review source file for syntax errors: {source_file}"
            )

        if line_number:
            recovery_suggestions.append(f"Check content around line {line_number}")

        # Add specific suggestions based on error types
        if any("encoding" in error.lower() for error in parsing_errors):
            recovery_suggestions.append("Check file encoding (UTF-8 recommended)")

        if any("incomplete" in error.lower() for error in parsing_errors):
            recovery_suggestions.append("Ensure complete schema dump was generated")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )


class ComparisonError(ProcessingError):
    """Raised when schema comparison fails."""

    default_error_code = "COMPARISON_FAILED"
    default_exit_code = 42

    def __init__(
        self,
        source_schema: str,
        target_schema: str,
        comparison_step: str,
        error_details: Optional[str] = None,
    ) -> None:
        """Initialize comparison error.

        Args:
            source_schema: Name of source schema
            target_schema: Name of target schema
            comparison_step: Step where comparison failed
            error_details: Additional error details (optional)
        """
        message = f"Failed to compare schemas '{source_schema}' and '{target_schema}' during {comparison_step}"

        if error_details:
            message += f": {error_details}"

        # Technical details
        technical_details = {
            "source_schema": source_schema,
            "target_schema": target_schema,
            "comparison_step": comparison_step,
            "error_details": error_details,
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Verify both schemas are valid and accessible",
            "Check that schemas have compatible structures",
            "Ensure sufficient memory for comparison operation",
            f"Review {comparison_step} logic and implementation",
        ]

        # Add step-specific suggestions
        if "table" in comparison_step.lower():
            recovery_suggestions.append("Verify table definitions and column types")
        elif "constraint" in comparison_step.lower():
            recovery_suggestions.append("Check constraint definitions and dependencies")
        elif "index" in comparison_step.lower():
            recovery_suggestions.append("Review index definitions and expressions")
        elif "function" in comparison_step.lower():
            recovery_suggestions.append(
                "Verify function signatures and implementations"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )


class ReportGenerationError(ProcessingError):
    """Raised when report generation fails."""

    default_error_code = "REPORT_GENERATION_FAILED"
    default_exit_code = 43

    def __init__(
        self,
        report_format: str,
        output_path: Optional[Path] = None,
        generation_step: Optional[str] = None,
        error_details: Optional[str] = None,
    ) -> None:
        """Initialize report generation error.

        Args:
            report_format: Format of the report being generated
            output_path: Path where report should be written (optional)
            generation_step: Step where generation failed (optional)
            error_details: Additional error details (optional)
        """
        message = f"Failed to generate {report_format} report"

        if generation_step:
            message += f" during {generation_step}"

        if error_details:
            message += f": {error_details}"

        # Technical details
        technical_details = {
            "report_format": report_format,
            "output_path": str(output_path) if output_path else None,
            "generation_step": generation_step,
            "error_details": error_details,
        }

        # Recovery suggestions
        recovery_suggestions = [
            f"Verify {report_format} format template is valid",
            "Check available disk space and write permissions",
            "Ensure comparison data is complete and valid",
        ]

        if output_path:
            parent_dir = output_path.parent
            recovery_suggestions.extend(
                [
                    f"Verify output directory exists: {parent_dir}",
                    f"Check write permissions for: {output_path}",
                ]
            )

        # Add format-specific suggestions
        if report_format.lower() == "html":
            recovery_suggestions.append("Verify HTML template syntax and CSS resources")
        elif report_format.lower() == "json":
            recovery_suggestions.append(
                "Check for circular references in comparison data"
            )
        elif report_format.lower() == "xml":
            recovery_suggestions.append("Verify XML schema and namespace definitions")
        elif report_format.lower() == "markdown":
            recovery_suggestions.append("Check Markdown template syntax and formatting")

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )
