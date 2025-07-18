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
        assert error.exit_code == 30
        assert error.retriable is False

    def test_init_with_custom_params(self):
        """Test ValidationError initialization with custom parameters."""
        error = ValidationError(
            "Custom validation error",
            error_code="CUSTOM_VALIDATION",
            severity=ErrorSeverity.HIGH,
            exit_code=35
        )
        
        assert str(error) == "Custom validation error"
        assert error.error_code == "CUSTOM_VALIDATION"
        assert error.severity == ErrorSeverity.HIGH
        assert error.exit_code == 35

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
        assert error.exit_code == 31

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
        error = UnsupportedFeatureError("advanced_partitioning", "PostgreSQL 12")
        
        error_message = str(error)
        assert "Feature 'advanced_partitioning' is not supported" in error_message
        assert "PostgreSQL 12" in error_message
        assert error.error_code == "UNSUPPORTED_FEATURE"

    def test_init_with_workaround(self):
        """Test UnsupportedFeatureError with workaround suggestion."""
        error = UnsupportedFeatureError(
            "json_operators", 
            "PostgreSQL 9.6",
            workaround="Use JSONB functions instead"
        )
        
        assert "workaround" in error.technical_details
        assert error.technical_details["workaround"] == "Use JSONB functions instead"

    def test_init_with_minimum_version(self):
        """Test UnsupportedFeatureError with minimum version requirement."""
        error = UnsupportedFeatureError(
            "window_functions", 
            "PostgreSQL 8.3",
            minimum_version="PostgreSQL 8.4"
        )
        
        assert "minimum_version" in error.technical_details
        assert error.technical_details["minimum_version"] == "PostgreSQL 8.4"

    def test_technical_details(self):
        """Test technical details structure."""
        error = UnsupportedFeatureError("feature_name", "current_version")
        
        details = error.technical_details
        assert details["feature_name"] == "feature_name"
        assert details["current_version"] == "current_version"

    def test_init_with_alternative(self):
        """Test UnsupportedFeatureError with alternative suggestion."""
        error = UnsupportedFeatureError(
            "partitioned_tables", 
            "PostgreSQL 9.6",
            alternative="Use table inheritance instead"
        )
        
        assert "alternative" in error.technical_details
        assert error.technical_details["alternative"] == "Use table inheritance instead"

    def test_init_with_all_optional_params(self):
        """Test UnsupportedFeatureError with all optional parameters."""
        error = UnsupportedFeatureError(
            "stored_procedures", 
            "PostgreSQL 10",
            workaround="Use functions instead",
            minimum_version="PostgreSQL 11",
            alternative="Use PL/pgSQL functions"
        )
        
        details = error.technical_details
        assert details["workaround"] == "Use functions instead"
        assert details["minimum_version"] == "PostgreSQL 11"
        assert details["alternative"] == "Use PL/pgSQL functions"