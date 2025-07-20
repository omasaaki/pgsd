"""Base exception classes for PGSD application."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    PROCESSING = "processing"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class PGSDError(Exception):
    """Base exception class for PGSD application.

    Provides structured error information with context,
    recovery suggestions, and proper logging support.
    """

    # Default values for subclasses
    default_error_code: str = "PGSD_ERROR"
    default_severity: ErrorSeverity = ErrorSeverity.MEDIUM
    default_category: ErrorCategory = ErrorCategory.SYSTEM
    default_exit_code: int = 1

    # Retry configuration
    retriable: bool = False
    base_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    retry_backoff_factor: float = 2.0

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        technical_details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None,
        user_action_required: bool = True,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize PGSD error.

        Args:
            message: Human-readable error message
            error_code: Unique error identifier
            severity: Error severity level
            category: Error category for classification
            technical_details: Technical information for debugging
            recovery_suggestions: List of recovery suggestions
            user_action_required: Whether user action is needed
            original_error: Original exception if this is a wrapper
            context: Additional context information
        """
        super().__init__(message)

        self.message = message
        self.error_code = error_code or self.default_error_code
        self.severity = severity or self.default_severity
        self.category = category or self.default_category
        self.technical_details = technical_details or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.user_action_required = user_action_required
        self.original_error = original_error
        self.context = context or {}

        # Generate unique error ID and timestamp
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)

        # Add original error information to technical details
        if original_error:
            self.technical_details.update(
                {
                    "original_error_type": type(original_error).__name__,
                    "original_error_message": str(original_error),
                }
            )

    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization.

        Returns:
            Dictionary representation of the error
        """
        return {
            "id": self.id,
            "error_type": type(self).__name__,
            "error_code": self.error_code,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "technical_details": self.technical_details,
            "recovery_suggestions": self.recovery_suggestions,
            "user_action_required": self.user_action_required,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_error) if self.original_error else None,
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert error to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        try:
            return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
        except TypeError:
            # Fallback for non-serializable objects
            safe_dict = self.to_dict()
            for key, value in safe_dict.items():
                if not isinstance(
                    value, (str, int, float, bool, list, dict, type(None))
                ):
                    safe_dict[key] = str(value)
            return json.dumps(safe_dict, indent=indent, ensure_ascii=False)

    def get_exit_code(self) -> int:
        """Get exit code for CLI integration.

        Returns:
            Exit code for the error
        """
        return getattr(self, "exit_code", self.default_exit_code)

    def add_context(self, key: str, value: Any) -> None:
        """Add context information to the error.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value

    def add_recovery_suggestion(self, suggestion: str) -> None:
        """Add a recovery suggestion.

        Args:
            suggestion: Recovery suggestion text
        """
        if suggestion not in self.recovery_suggestions:
            self.recovery_suggestions.append(suggestion)

    def is_retriable(self) -> bool:
        """Check if this error should be retried.

        Returns:
            True if the error is retriable
        """
        return self.retriable

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay for given attempt.

        Args:
            attempt: Retry attempt number (starting from 1)

        Returns:
            Delay in seconds before next retry
        """
        if attempt <= 0:
            return 0

        delay = self.base_retry_delay * (self.retry_backoff_factor ** (attempt - 1))
        return min(delay, self.max_retry_delay)


class PGSDWarning(UserWarning):
    """Base warning class for PGSD application.

    Used for non-critical issues that don't stop execution
    but should be brought to user attention.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PGSD warning.

        Args:
            message: Warning message
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)

    def __str__(self) -> str:
        """Return string representation of the warning."""
        return self.message
