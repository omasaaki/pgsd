"""Exception classes for PGSD application."""

from .base import PGSDError, PGSDWarning, ErrorSeverity, ErrorCategory
from .database import (
    DatabaseError, DatabaseConnectionError, SchemaNotFoundError,
    InsufficientPrivilegesError, QueryExecutionError
)
from .config import (
    ConfigurationError, InvalidConfigurationError,
    MissingConfigurationError
)
from .validation import (
    ValidationError, InvalidSchemaError, UnsupportedFeatureError
)
from .processing import (
    ProcessingError, SchemaParsingError, ComparisonError,
    ReportGenerationError
)

__all__ = [
    # Base classes
    "PGSDError",
    "PGSDWarning", 
    "ErrorSeverity",
    "ErrorCategory",
    
    # Database exceptions
    "DatabaseError",
    "DatabaseConnectionError",
    "SchemaNotFoundError",
    "InsufficientPrivilegesError",
    "QueryExecutionError",
    
    # Configuration exceptions
    "ConfigurationError",
    "InvalidConfigurationError",
    "MissingConfigurationError",
    
    # Validation exceptions
    "ValidationError",
    "InvalidSchemaError",
    "UnsupportedFeatureError",
    
    # Processing exceptions
    "ProcessingError",
    "SchemaParsingError",
    "ComparisonError",
    "ReportGenerationError",
]