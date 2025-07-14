"""Exit codes for PGSD application."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Standard exit codes for PGSD application."""
    
    # Success
    SUCCESS = 0
    
    # General errors
    GENERAL_ERROR = 1
    INVALID_USAGE = 2
    KEYBOARD_INTERRUPT = 3
    
    # Database errors (10-19)
    DATABASE_ERROR = 10
    DB_CONNECTION_FAILED = 11
    SCHEMA_NOT_FOUND = 12
    INSUFFICIENT_PRIVILEGES = 13
    QUERY_EXECUTION_FAILED = 14
    
    # Configuration errors (20-29)
    CONFIGURATION_ERROR = 20
    INVALID_CONFIGURATION = 21
    MISSING_CONFIGURATION = 22
    
    # Validation errors (30-39)
    VALIDATION_ERROR = 30
    INVALID_SCHEMA = 31
    UNSUPPORTED_FEATURE = 32
    
    # Processing errors (40-49)
    PROCESSING_ERROR = 40
    SCHEMA_PARSING_FAILED = 41
    COMPARISON_FAILED = 42
    REPORT_GENERATION_FAILED = 43
    
    # System errors (50-59)
    SYSTEM_ERROR = 50
    INSUFFICIENT_MEMORY = 51
    DISK_FULL = 52
    PERMISSION_DENIED = 53
    
    @classmethod
    def get_exit_code_for_exception(cls, exception: Exception) -> int:
        """Get appropriate exit code for exception.
        
        Args:
            exception: Exception to get exit code for
            
        Returns:
            Appropriate exit code
        """
        from ..exceptions.base import PGSDError
        
        if isinstance(exception, PGSDError):
            return exception.get_exit_code()
        elif isinstance(exception, KeyboardInterrupt):
            return cls.KEYBOARD_INTERRUPT
        elif isinstance(exception, MemoryError):
            return cls.INSUFFICIENT_MEMORY
        elif isinstance(exception, OSError):
            return cls.SYSTEM_ERROR
        else:
            return cls.GENERAL_ERROR