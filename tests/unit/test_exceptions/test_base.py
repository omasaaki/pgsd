"""
Unit tests for base exception classes.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock

from pgsd.exceptions.base import PGSDError, PGSDWarning, ErrorSeverity, ErrorCategory


@pytest.mark.unit
class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_severity_values(self):
        """Test that severity enum has correct values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


@pytest.mark.unit
class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_category_values(self):
        """Test that category enum has correct values."""
        assert ErrorCategory.CONNECTION.value == "connection"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.AUTHORIZATION.value == "authorization"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.PROCESSING.value == "processing"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.SYSTEM.value == "system"
        assert ErrorCategory.USER_INPUT.value == "user_input"


@pytest.mark.unit
class TestPGSDError:
    """Test PGSDError base exception class."""

    def test_basic_error_creation(self):
        """Test basic error creation with minimal parameters."""
        error = PGSDError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "PGSD_ERROR"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.SYSTEM
        assert isinstance(error.id, str)
        assert len(error.id) == 36  # UUID4 length
        assert isinstance(error.timestamp, datetime)
        assert error.technical_details == {}
        assert error.recovery_suggestions == []
        assert error.user_action_required is True
        assert error.original_error is None
        assert error.context == {}

    def test_error_with_custom_parameters(self):
        """Test error creation with custom parameters."""
        original_error = ValueError("Original error")
        technical_details = {"database": "testdb", "port": 5432}
        recovery_suggestions = ["Check connection", "Verify credentials"]
        context = {"operation": "connect", "attempt": 1}

        error = PGSDError(
            message="Custom error message",
            error_code="CUSTOM_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONNECTION,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            user_action_required=False,
            original_error=original_error,
            context=context,
        )

        assert error.message == "Custom error message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.CONNECTION
        assert error.technical_details == technical_details
        assert error.recovery_suggestions == recovery_suggestions
        assert error.user_action_required is False
        assert error.original_error == original_error
        assert error.context == context

    def test_error_with_original_error(self):
        """Test error with original error information."""
        original_error = ConnectionError("Network unavailable")

        error = PGSDError("Failed to connect", original_error=original_error)

        assert error.original_error == original_error
        assert error.technical_details["original_error_type"] == "ConnectionError"
        assert (
            error.technical_details["original_error_message"] == "Network unavailable"
        )

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        original_error = ValueError("Test error")

        error = PGSDError(
            message="Test error",
            error_code="TEST_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.VALIDATION,
            technical_details={"key": "value"},
            recovery_suggestions=["Try again"],
            user_action_required=True,
            original_error=original_error,
            context={"test": True},
        )

        error_dict = error.to_dict()

        assert error_dict["id"] == error.id
        assert error_dict["error_type"] == "PGSDError"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["severity"] == "high"
        assert error_dict["category"] == "validation"
        assert error_dict["message"] == "Test error"
        assert error_dict["technical_details"]["key"] == "value"
        assert error_dict["recovery_suggestions"] == ["Try again"]
        assert error_dict["user_action_required"] is True
        assert error_dict["context"]["test"] is True
        assert error_dict["timestamp"] == error.timestamp.isoformat()
        assert error_dict["original_error"] == "Test error"

    def test_to_json_serialization(self):
        """Test serialization to JSON."""
        error = PGSDError(
            "Test error", error_code="TEST_JSON", technical_details={"number": 42}
        )

        json_str = error.to_json()

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["error_code"] == "TEST_JSON"
        assert parsed["message"] == "Test error"
        assert parsed["technical_details"]["number"] == 42

    def test_get_exit_code(self):
        """Test exit code retrieval."""
        # Test default exit code
        error = PGSDError("Test error")
        assert error.get_exit_code() == 1

        # Test custom exit code via class attribute
        class CustomError(PGSDError):
            exit_code = 42

        custom_error = CustomError("Custom error")
        assert custom_error.get_exit_code() == 42

    def test_add_context(self):
        """Test adding context information."""
        error = PGSDError("Test error")

        error.add_context("operation", "test_operation")
        error.add_context("user_id", 123)

        assert error.context["operation"] == "test_operation"
        assert error.context["user_id"] == 123

    def test_add_recovery_suggestion(self):
        """Test adding recovery suggestions."""
        error = PGSDError("Test error")

        error.add_recovery_suggestion("First suggestion")
        error.add_recovery_suggestion("Second suggestion")

        assert len(error.recovery_suggestions) == 2
        assert "First suggestion" in error.recovery_suggestions
        assert "Second suggestion" in error.recovery_suggestions

        # Test duplicate prevention
        error.add_recovery_suggestion("First suggestion")
        assert len(error.recovery_suggestions) == 2

    def test_is_retriable(self):
        """Test retriable check."""
        # Test default (not retriable)
        error = PGSDError("Test error")
        assert error.is_retriable() is False

        # Test custom retriable class
        class RetriableError(PGSDError):
            retriable = True

        retriable_error = RetriableError("Retriable error")
        assert retriable_error.is_retriable() is True

    def test_get_retry_delay(self):
        """Test retry delay calculation."""

        class RetriableError(PGSDError):
            retriable = True
            base_retry_delay = 2.0
            max_retry_delay = 30.0
            retry_backoff_factor = 3.0

        error = RetriableError("Retriable error")

        # Test exponential backoff
        assert error.get_retry_delay(1) == 2.0
        assert error.get_retry_delay(2) == 6.0  # 2.0 * 3^1
        assert error.get_retry_delay(3) == 18.0  # 2.0 * 3^2
        assert error.get_retry_delay(4) == 30.0  # Capped at max_retry_delay

    def test_timestamp_accuracy(self):
        """Test that timestamp is set accurately."""
        before = datetime.utcnow()
        error = PGSDError("Test error")
        after = datetime.utcnow()

        assert before <= error.timestamp <= after

    def test_inheritance_defaults(self):
        """Test that subclasses can override defaults."""

        class CustomError(PGSDError):
            default_error_code = "CUSTOM_DEFAULT"
            default_severity = ErrorSeverity.CRITICAL
            default_category = ErrorCategory.CONNECTION
            default_exit_code = 99

        error = CustomError("Custom error")

        assert error.error_code == "CUSTOM_DEFAULT"
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.category == ErrorCategory.CONNECTION
        assert error.get_exit_code() == 99


@pytest.mark.unit
class TestPGSDWarning:
    """Test PGSDWarning class."""

    def test_basic_warning_creation(self):
        """Test basic warning creation."""
        warning = PGSDWarning("Test warning message")

        assert str(warning) == "Test warning message"
        assert warning.message == "Test warning message"
        assert warning.context == {}
        assert isinstance(warning.timestamp, datetime)

    def test_warning_with_context(self):
        """Test warning with context information."""
        context = {"operation": "schema_check", "severity": "low"}
        warning = PGSDWarning("Test warning", context=context)

        assert warning.context == context

    def test_warning_inheritance(self):
        """Test that PGSDWarning inherits from UserWarning."""
        warning = PGSDWarning("Test warning")
        assert isinstance(warning, UserWarning)


@pytest.mark.unit
class TestErrorEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_long_message(self):
        """Test handling of very long error messages."""
        long_message = "A" * 10000
        error = PGSDError(long_message)

        assert error.message == long_message
        assert len(str(error)) == 10000

    def test_none_values_handling(self):
        """Test handling of None values in optional parameters."""
        error = PGSDError(
            "Test error",
            error_code=None,
            severity=None,
            category=None,
            technical_details=None,
            recovery_suggestions=None,
            original_error=None,
            context=None,
        )

        # Should use defaults when None is provided
        assert error.error_code == "PGSD_ERROR"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.SYSTEM
        assert error.technical_details == {}
        assert error.recovery_suggestions == []
        assert error.context == {}

    def test_special_characters_in_message(self):
        """Test handling of special characters in messages."""
        special_message = 'Error with 特殊文字 and émojis 🚨 and quotes "test"'
        error = PGSDError(special_message)

        assert error.message == special_message

        # Should be serializable to JSON
        json_str = error.to_json()
        parsed = json.loads(json_str)
        assert parsed["message"] == special_message

    def test_circular_reference_in_technical_details(self):
        """Test handling of complex objects in technical details."""
        # Create a mock object that might cause serialization issues
        mock_obj = Mock()
        mock_obj.name = "test_object"

        error = PGSDError("Test error", technical_details={"mock_object": mock_obj})

        # Should not raise exception
        error_dict = error.to_dict()
        assert "mock_object" in error_dict["technical_details"]

    def test_empty_string_message(self):
        """Test handling of empty string message."""
        error = PGSDError("")

        assert error.message == ""
        assert str(error) == ""

    def test_unicode_in_error_code(self):
        """Test handling of unicode characters in error code."""
        error = PGSDError("Test error", error_code="错误_CODE_123")

        assert error.error_code == "错误_CODE_123"

        # Should be serializable
        json_str = error.to_json()
        parsed = json.loads(json_str)
        assert parsed["error_code"] == "错误_CODE_123"


@pytest.mark.unit
class TestErrorPerformance:
    """Test performance characteristics of error handling."""

    def test_error_creation_performance(self):
        """Test that error creation is reasonably fast."""
        import time

        start_time = time.time()

        for i in range(1000):
            _ = PGSDError(f"Error {i}", technical_details={"index": i})

        end_time = time.time()
        duration = end_time - start_time

        # Should create 1000 errors in less than 1 second
        assert duration < 1.0

    def test_serialization_performance(self):
        """Test that serialization is reasonably fast."""
        import time

        error = PGSDError(
            "Performance test error",
            technical_details={f"key_{i}": f"value_{i}" for i in range(100)},
            recovery_suggestions=[f"Suggestion {i}" for i in range(50)],
        )

        start_time = time.time()

        for _ in range(100):
            error.to_json()

        end_time = time.time()
        duration = end_time - start_time

        # Should serialize 100 times in less than 1 second
        assert duration < 1.0

    def test_memory_usage(self):
        """Test memory usage of error objects."""
        import sys

        simple_error = PGSDError("Simple error")
        # Calculate total size including referenced objects and their contents
        simple_size = (
            sys.getsizeof(simple_error)
            + sys.getsizeof(simple_error.technical_details)
            + sys.getsizeof(simple_error.recovery_suggestions)
            + sys.getsizeof(simple_error.context)
            + sum(
                sys.getsizeof(k) + sys.getsizeof(v)
                for k, v in simple_error.technical_details.items()
            )
            + sum(sys.getsizeof(item) for item in simple_error.recovery_suggestions)
            + sum(
                sys.getsizeof(k) + sys.getsizeof(v)
                for k, v in simple_error.context.items()
            )
        )

        complex_error = PGSDError(
            "Complex error",
            technical_details={f"key_{i}": f"value_{i}" for i in range(100)},
            recovery_suggestions=[f"Suggestion {i}" for i in range(50)],
            context={f"ctx_{i}": i for i in range(50)},
        )
        # Calculate total size including referenced objects and their contents
        complex_size = (
            sys.getsizeof(complex_error)
            + sys.getsizeof(complex_error.technical_details)
            + sys.getsizeof(complex_error.recovery_suggestions)
            + sys.getsizeof(complex_error.context)
            + sum(
                sys.getsizeof(k) + sys.getsizeof(v)
                for k, v in complex_error.technical_details.items()
            )
            + sum(sys.getsizeof(item) for item in complex_error.recovery_suggestions)
            + sum(
                sys.getsizeof(k) + sys.getsizeof(v)
                for k, v in complex_error.context.items()
            )
        )

        # Complex error should be larger but not excessively so
        assert complex_size > simple_size
        assert (
            complex_size < simple_size * 200
        )  # Reasonable upper bound for 200 items (100 dict + 50 list + 50 context)
