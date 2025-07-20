"""Simple tests for validation-related exceptions."""

import pytest

from pgsd.exceptions.validation import (
    ValidationError,
    InvalidSchemaError,
    UnsupportedFeatureError
)
from pgsd.exceptions.base import ErrorSeverity, ErrorCategory


class TestValidationError:
    """Test cases for ValidationError class."""

    def test_init_default(self):
        """Test ValidationError initialization with defaults."""
        error = ValidationError("Validation failed")
        
        assert str(error) == "Validation failed"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.VALIDATION
        assert error.get_exit_code() == 30
        assert error.retriable is False

    def test_init_with_custom_params(self):
        """Test ValidationError initialization with custom parameters."""
        error = ValidationError(
            "Custom validation error",
            error_code="CUSTOM_VALIDATION",
            severity=ErrorSeverity.HIGH
        )
        
        assert str(error) == "Custom validation error"
        assert error.error_code == "CUSTOM_VALIDATION"
        assert error.severity == ErrorSeverity.HIGH
        assert error.get_exit_code() == 30  # Default validation error code

    def test_technical_details(self):
        """Test technical details are captured."""
        error = ValidationError("Validation failed")
        
        assert hasattr(error, 'technical_details')
        assert isinstance(error.technical_details, dict)

    def test_non_retriable(self):
        """Test that validation errors are not retriable by default."""
        error = ValidationError("Validation failed")
        
        assert error.retriable is False


class TestInvalidSchemaError:
    """Test cases for InvalidSchemaError class."""

    def test_init_without_database(self):
        """Test InvalidSchemaError initialization without database."""
        validation_errors = ["Missing primary key", "Invalid column type"]
        error = InvalidSchemaError("user_schema", validation_errors)
        
        error_message = str(error)
        assert "Schema 'user_schema' failed validation" in error_message
        assert error.error_code == "INVALID_SCHEMA"
        assert error.get_exit_code() == 31

    def test_init_with_database(self):
        """Test InvalidSchemaError initialization with database."""
        validation_errors = ["Constraint violation", "Index corruption"]
        error = InvalidSchemaError("public", validation_errors, database="production")
        
        error_message = str(error)
        assert "Schema 'public' in database 'production' failed validation" in error_message

    def test_technical_details(self):
        """Test technical details include validation errors."""
        validation_errors = ["Error 1", "Error 2", "Error 3"]
        error = InvalidSchemaError("test_schema", validation_errors, database="test_db")
        
        details = error.technical_details
        assert details["schema_name"] == "test_schema"
        assert details["database"] == "test_db"
        assert details["validation_errors"] == validation_errors
        assert details["error_count"] == 3

    def test_empty_validation_errors(self):
        """Test with empty validation errors list."""
        validation_errors = []
        error = InvalidSchemaError("empty_schema", validation_errors)
        
        assert error.technical_details["error_count"] == 0
        assert error.technical_details["validation_errors"] == []

    def test_single_validation_error(self):
        """Test with single validation error."""
        validation_errors = ["Single error"]
        error = InvalidSchemaError("single_error_schema", validation_errors)
        
        assert error.technical_details["error_count"] == 1
        assert len(error.technical_details["validation_errors"]) == 1


class TestUnsupportedFeatureError:
    """Test cases for UnsupportedFeatureError class."""

    def test_init_basic(self):
        """Test UnsupportedFeatureError initialization."""
        error = UnsupportedFeatureError("advanced_partitioning", "partitioning")
        
        error_message = str(error)
        assert "Unsupported partitioning" in error_message
        assert "advanced_partitioning" in error_message
        assert error.error_code == "UNSUPPORTED_FEATURE"

    def test_init_with_workaround(self):
        """Test UnsupportedFeatureError with workaround suggestion."""
        error = UnsupportedFeatureError(
            "json_operators", 
            "operator",
            workaround_suggestion="Use JSONB functions instead"
        )
        
        # Workaround is added to recovery_suggestions, not technical_details
        assert any("Use JSONB functions instead" in suggestion 
                  for suggestion in error.recovery_suggestions)

    def test_init_with_minimum_version(self):
        """Test UnsupportedFeatureError with minimum version requirement."""
        error = UnsupportedFeatureError(
            "window_functions", 
            "function",
            min_supported_version="8.4"
        )
        
        assert "min_supported_version" in error.technical_details
        assert error.technical_details["min_supported_version"] == "8.4"

    def test_technical_details(self):
        """Test technical details structure."""
        error = UnsupportedFeatureError("feature_name", "feature_type")
        
        details = error.technical_details
        assert details["feature_name"] == "feature_name"
        assert details["feature_type"] == "feature_type"
        assert details["min_supported_version"] is None

    def test_init_with_alternative(self):
        """Test UnsupportedFeatureError with alternative suggestion."""
        error = UnsupportedFeatureError(
            "partitioned_tables", 
            "table feature",
            workaround_suggestion="Use table inheritance instead"
        )
        
        # Alternative suggestions are in recovery_suggestions, not technical_details
        assert any("Use table inheritance instead" in suggestion 
                  for suggestion in error.recovery_suggestions)

    def test_init_with_all_optional_params(self):
        """Test UnsupportedFeatureError with all optional parameters."""
        error = UnsupportedFeatureError(
            "stored_procedures", 
            "procedure",
            min_supported_version="11",
            workaround_suggestion="Use functions instead"
        )
        
        details = error.technical_details
        assert details["feature_name"] == "stored_procedures"
        assert details["feature_type"] == "procedure"
        assert details["min_supported_version"] == "11"
        
        # Check workaround is in recovery suggestions
        assert any("Use functions instead" in suggestion 
                  for suggestion in error.recovery_suggestions)