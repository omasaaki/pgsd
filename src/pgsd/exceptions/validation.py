"""Validation-related exception classes."""

from typing import List, Optional

from .base import PGSDError, ErrorSeverity, ErrorCategory


class ValidationError(PGSDError):
    """Base class for validation-related errors."""

    default_error_code = "VALIDATION_ERROR"
    default_severity = ErrorSeverity.MEDIUM
    default_category = ErrorCategory.VALIDATION
    default_exit_code = 30
    retriable = False


class InvalidSchemaError(ValidationError):
    """Raised when schema structure is invalid or corrupted."""

    default_error_code = "INVALID_SCHEMA"
    default_exit_code = 31

    def __init__(
        self,
        schema_name: str,
        validation_errors: List[str],
        database: Optional[str] = None,
    ) -> None:
        """Initialize invalid schema error.

        Args:
            schema_name: Name of the invalid schema
            validation_errors: List of specific validation errors
            database: Database name (optional)
        """
        if database:
            message = (
                f"Schema '{schema_name}' in database '{database}' failed validation"
            )
        else:
            message = f"Schema '{schema_name}' failed validation"

        # Technical details
        technical_details = {
            "schema_name": schema_name,
            "database": database,
            "validation_errors": validation_errors,
            "error_count": len(validation_errors),
        }

        # Recovery suggestions
        recovery_suggestions = [
            "Review schema structure and fix validation errors",
            "Check for corrupted or incomplete schema definitions",
            "Verify schema was properly migrated or created",
        ]

        # Add specific suggestions based on validation errors
        if any("missing" in error.lower() for error in validation_errors):
            recovery_suggestions.append("Restore missing schema objects or constraints")

        if any("constraint" in error.lower() for error in validation_errors):
            recovery_suggestions.append("Review and fix constraint definitions")

        if any(
            "reference" in error.lower() or "foreign" in error.lower()
            for error in validation_errors
        ):
            recovery_suggestions.append(
                "Check foreign key references and relationships"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )


class UnsupportedFeatureError(ValidationError):
    """Raised when encountering unsupported PostgreSQL features."""

    default_error_code = "UNSUPPORTED_FEATURE"
    default_severity = ErrorSeverity.LOW
    default_exit_code = 32

    def __init__(
        self,
        feature_name: str,
        feature_type: str,
        min_supported_version: Optional[str] = None,
        workaround_suggestion: Optional[str] = None,
    ) -> None:
        """Initialize unsupported feature error.

        Args:
            feature_name: Name of the unsupported feature
            feature_type: Type/category of the feature
            min_supported_version: Minimum version that supports this feature (optional)
            workaround_suggestion: Suggested workaround (optional)
        """
        message = f"Unsupported {feature_type}: '{feature_name}'"

        if min_supported_version:
            message += f" (requires PostgreSQL {min_supported_version} or higher)"

        # Technical details
        technical_details = {
            "feature_name": feature_name,
            "feature_type": feature_type,
            "min_supported_version": min_supported_version,
        }

        # Recovery suggestions
        recovery_suggestions = [
            f"Consider alternative implementations for {feature_type}",
            "Review PostgreSQL version compatibility requirements",
        ]

        if min_supported_version:
            recovery_suggestions.append(
                f"Upgrade PostgreSQL to version {min_supported_version} or higher"
            )

        if workaround_suggestion:
            recovery_suggestions.append(f"Workaround: {workaround_suggestion}")
        else:
            recovery_suggestions.append(
                "Check documentation for alternative approaches"
            )

        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
        )
