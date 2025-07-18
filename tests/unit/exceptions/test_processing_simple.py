"""Simple tests for processing-related exceptions."""

import pytest
from pathlib import Path

from pgsd.exceptions.processing import (
    ProcessingError,
    SchemaParsingError,
    ComparisonError,
    ReportGenerationError
)
from pgsd.exceptions.base import ErrorSeverity, ErrorCategory


class TestProcessingError:
    """Test cases for ProcessingError class."""

    def test_init_default(self):
        """Test ProcessingError initialization with defaults."""
        error = ProcessingError("Processing failed")
        
        assert str(error) == "Processing failed"
        assert error.error_code == "PROCESSING_ERROR"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.PROCESSING
        assert error.exit_code == 40
        assert error.retriable is True

    def test_init_with_custom_params(self):
        """Test ProcessingError initialization with custom parameters."""
        error = ProcessingError(
            "Custom processing error",
            error_code="CUSTOM_PROCESSING",
            severity=ErrorSeverity.HIGH,
            exit_code=50
        )
        
        assert str(error) == "Custom processing error"
        assert error.error_code == "CUSTOM_PROCESSING"
        assert error.severity == ErrorSeverity.HIGH
        assert error.exit_code == 50

    def test_technical_details(self):
        """Test technical details are captured."""
        error = ProcessingError("Processing failed")
        
        assert hasattr(error, 'technical_details')
        assert isinstance(error.technical_details, dict)

    def test_retry_properties(self):
        """Test retry-related properties."""
        error = ProcessingError("Processing failed")
        
        assert error.retriable is True
        assert error.base_retry_delay == 1.0
        assert error.max_retry_delay == 10.0


class TestSchemaParsingError:
    """Test cases for SchemaParsingError class."""

    def test_init_minimal(self):
        """Test SchemaParsingError initialization with minimal parameters."""
        parsing_errors = ["Column type mismatch", "Missing primary key"]
        error = SchemaParsingError("test_schema", parsing_errors)
        
        assert "Failed to parse schema 'test_schema'" in str(error)
        assert error.error_code == "SCHEMA_PARSING_FAILED"
        assert error.exit_code == 41
        assert error.retriable is False

    def test_init_with_line_number(self):
        """Test SchemaParsingError with line number."""
        parsing_errors = ["Syntax error"]
        error = SchemaParsingError("test_schema", parsing_errors, line_number=42)
        
        error_message = str(error)
        assert "Failed to parse schema 'test_schema'" in error_message
        assert "at line 42" in error_message

    def test_init_with_source_file(self):
        """Test SchemaParsingError with source file."""
        parsing_errors = ["Invalid SQL"]
        source_file = Path("/path/to/schema.sql")
        error = SchemaParsingError("test_schema", parsing_errors, source_file=source_file)
        
        error_message = str(error)
        assert "Failed to parse schema 'test_schema'" in error_message
        assert "from /path/to/schema.sql" in error_message

    def test_init_with_line_and_file(self):
        """Test SchemaParsingError with both line number and source file."""
        parsing_errors = ["Unexpected token"]
        source_file = Path("/path/to/schema.sql")
        error = SchemaParsingError(
            "test_schema", 
            parsing_errors, 
            line_number=15, 
            source_file=source_file
        )
        
        error_message = str(error)
        assert "Failed to parse schema 'test_schema'" in error_message
        assert "at line 15 in /path/to/schema.sql" in error_message

    def test_technical_details(self):
        """Test technical details include parsing errors."""
        parsing_errors = ["Error 1", "Error 2"]
        error = SchemaParsingError("test_schema", parsing_errors)
        
        assert "parsing_errors" in error.technical_details
        assert error.technical_details["parsing_errors"] == parsing_errors
        assert error.technical_details["schema_name"] == "test_schema"

    def test_multiple_parsing_errors(self):
        """Test with multiple parsing errors."""
        parsing_errors = [
            "Column 'id' type mismatch",
            "Missing foreign key constraint",
            "Invalid index definition"
        ]
        error = SchemaParsingError("complex_schema", parsing_errors)
        
        assert error.technical_details["error_count"] == 3
        assert len(error.technical_details["parsing_errors"]) == 3




class TestReportGenerationError:
    """Test cases for ReportGenerationError class."""

    def test_init_basic(self):
        """Test ReportGenerationError initialization."""
        error = ReportGenerationError("html", "Template not found")
        
        error_message = str(error)
        assert "Failed to generate html report" in error_message
        assert error.error_code == "REPORT_GENERATION_FAILED"

    def test_init_with_output_file(self):
        """Test ReportGenerationError with output file."""
        output_file = Path("/tmp/report.json")
        error = ReportGenerationError(
            "json", 
            "Disk space insufficient",
            output_file=output_file
        )
        
        assert "output_file" in error.technical_details
        assert error.technical_details["output_file"] == output_file

    def test_init_with_template_error(self):
        """Test ReportGenerationError with template error."""
        template_error = "Variable 'schema_name' is undefined"
        error = ReportGenerationError(
            "html", 
            "Template rendering failed",
            template_error=template_error
        )
        
        assert "template_error" in error.technical_details
        assert error.technical_details["template_error"] == template_error


class TestComparisonError:
    """Test cases for ComparisonError class."""

    def test_init_basic(self):
        """Test ComparisonError initialization."""
        error = ComparisonError("public", "inventory", "Schema structure mismatch")
        
        error_message = str(error)
        assert "Failed to compare schemas 'public' and 'inventory'" in error_message
        assert error.error_code == "SCHEMA_COMPARISON_FAILED"

    def test_init_with_comparison_type(self):
        """Test ComparisonError with comparison type."""
        error = ComparisonError(
            "source_schema", 
            "target_schema", 
            "Table count mismatch",
            comparison_type="table_structure"
        )
        
        assert "comparison_type" in error.technical_details
        assert error.technical_details["comparison_type"] == "table_structure"

    def test_init_with_details(self):
        """Test ComparisonError with detailed comparison information."""
        comparison_details = {
            "source_tables": 15,
            "target_tables": 12,
            "missing_tables": ["audit_log", "temp_data", "cache"]
        }
        error = ComparisonError(
            "prod_schema", 
            "test_schema", 
            "Table count and structure mismatch",
            comparison_details=comparison_details
        )
        
        assert "comparison_details" in error.technical_details
        assert error.technical_details["comparison_details"] == comparison_details

    def test_technical_details(self):
        """Test technical details structure."""
        error = ComparisonError("schema_a", "schema_b", "Comparison failed")
        
        details = error.technical_details
        assert details["source_schema"] == "schema_a"
        assert details["target_schema"] == "schema_b"
        assert details["comparison_error"] == "Comparison failed"