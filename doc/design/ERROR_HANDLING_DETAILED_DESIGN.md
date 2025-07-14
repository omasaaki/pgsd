# エラーハンドリング詳細設計書

## 1. 概要

このドキュメントは、PostgreSQL Schema Diff Tool (PGSD)のエラーハンドリングシステムの詳細設計を定義する。

## 2. ファイル構成

### 2.1 実装ファイル構造
```
src/pgsd/
├── exceptions/
│   ├── __init__.py              # 例外クラスエクスポート
│   ├── base.py                  # 基底例外クラス
│   ├── database.py              # データベース関連例外
│   ├── config.py                # 設定関連例外
│   ├── validation.py            # バリデーション例外
│   └── processing.py            # 処理関連例外
├── error_handling/
│   ├── __init__.py              # エラーハンドリングエクスポート
│   ├── handler.py               # メインエラーハンドラー
│   ├── retry.py                 # リトライ機構
│   ├── recovery.py              # 復旧機構
│   ├── reporters.py             # エラーレポーター
│   └── exit_codes.py            # 終了コード定義
└── constants/
    ├── __init__.py
    └── error_messages.py        # エラーメッセージカタログ
```

## 3. 詳細実装仕様

### 3.1 基底例外クラス (base.py)

```python
"""Base exception classes for PGSD application."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
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
        context: Optional[Dict[str, Any]] = None
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
        
        self.id = str(uuid.uuid4())
        self.message = message
        self.error_code = error_code or self.default_error_code
        self.severity = severity or self.default_severity
        self.category = category or self.default_category
        self.technical_details = technical_details or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.user_action_required = user_action_required
        self.original_error = original_error
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        
        # Add original error info to technical details
        if original_error:
            self.technical_details.update({
                "original_error_type": type(original_error).__name__,
                "original_error_message": str(original_error),
            })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging."""
        return {
            "id": self.id,
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "technical_details": self.technical_details,
            "recovery_suggestions": self.recovery_suggestions,
            "user_action_required": self.user_action_required,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_error) if self.original_error else None
        }
    
    def to_json(self) -> str:
        """Convert exception to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    def get_exit_code(self) -> int:
        """Get appropriate exit code for this error."""
        return getattr(self, 'exit_code', self.default_exit_code)
    
    def add_context(self, key: str, value: Any) -> None:
        """Add context information to the error."""
        self.context[key] = value
    
    def add_recovery_suggestion(self, suggestion: str) -> None:
        """Add a recovery suggestion."""
        if suggestion not in self.recovery_suggestions:
            self.recovery_suggestions.append(suggestion)
    
    def is_retriable(self) -> bool:
        """Check if this error type supports retry."""
        return getattr(self, 'retriable', False)
    
    def get_retry_delay(self, attempt: int) -> float:
        """Get retry delay for this attempt number."""
        base_delay = getattr(self, 'base_retry_delay', 1.0)
        max_delay = getattr(self, 'max_retry_delay', 60.0)
        backoff_factor = getattr(self, 'retry_backoff_factor', 2.0)
        
        delay = base_delay * (backoff_factor ** (attempt - 1))
        return min(delay, max_delay)


class PGSDWarning(UserWarning):
    """Base warning class for PGSD application."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.utcnow()
```

### 3.2 データベース例外クラス (database.py)

```python
"""Database-related exception classes."""

from typing import Any, Dict, List, Optional
import psycopg2
from .base import PGSDError, ErrorSeverity, ErrorCategory


class DatabaseError(PGSDError):
    """Base class for database-related errors."""
    
    default_error_code = "DATABASE_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_category = ErrorCategory.CONNECTION
    default_exit_code = 10
    retriable = True
    base_retry_delay = 2.0
    max_retry_delay = 30.0


class DatabaseConnectionError(DatabaseError):
    """Database connection failure."""
    
    default_error_code = "DB_CONNECTION_FAILED"
    default_severity = ErrorSeverity.CRITICAL
    exit_code = 11
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        message = f"Failed to connect to PostgreSQL database '{database}' at {host}:{port}"
        if user:
            message += f" as user '{user}'"
        
        technical_details = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "connection_type": "postgresql"
        }
        
        recovery_suggestions = [
            "Verify that PostgreSQL server is running",
            "Check connection parameters (host, port, database name)",
            "Verify network connectivity to the database server",
            "Check database user credentials",
            "Ensure the database exists and is accessible",
            "Check firewall settings and security groups"
        ]
        
        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            original_error=original_error
        )
    
    @classmethod
    def from_psycopg2_error(
        cls,
        error: psycopg2.Error,
        host: str,
        port: int,
        database: str,
        user: Optional[str] = None
    ) -> 'DatabaseConnectionError':
        """Create DatabaseConnectionError from psycopg2 error."""
        instance = cls(host, port, database, user, error)
        
        # Add psycopg2-specific details
        if hasattr(error, 'pgcode'):
            instance.technical_details['postgres_error_code'] = error.pgcode
        if hasattr(error, 'pgerror'):
            instance.technical_details['postgres_error_message'] = error.pgerror
        
        return instance


class SchemaNotFoundError(DatabaseError):
    """Schema not found in database."""
    
    default_error_code = "SCHEMA_NOT_FOUND"
    default_severity = ErrorSeverity.MEDIUM
    exit_code = 12
    retriable = False
    
    def __init__(
        self,
        schema_name: str,
        database: str,
        available_schemas: Optional[List[str]] = None
    ):
        message = f"Schema '{schema_name}' not found in database '{database}'"
        
        technical_details = {
            "schema_name": schema_name,
            "database": database,
            "available_schemas": available_schemas or []
        }
        
        recovery_suggestions = [
            f"Verify the schema name '{schema_name}' is correct",
            "Check if the schema exists in the database",
            "Ensure you have permissions to access the schema"
        ]
        
        if available_schemas:
            recovery_suggestions.append(
                f"Available schemas: {', '.join(available_schemas)}"
            )
        
        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions
        )


class InsufficientPrivilegesError(DatabaseError):
    """Insufficient database privileges."""
    
    default_error_code = "INSUFFICIENT_PRIVILEGES"
    default_severity = ErrorSeverity.HIGH
    default_category = ErrorCategory.AUTHORIZATION
    exit_code = 13
    retriable = False
    
    def __init__(
        self,
        operation: str,
        required_privileges: List[str],
        user: Optional[str] = None,
        object_name: Optional[str] = None
    ):
        message = f"Insufficient privileges to {operation}"
        if object_name:
            message += f" on {object_name}"
        if user:
            message += f" as user '{user}'"
        
        technical_details = {
            "operation": operation,
            "required_privileges": required_privileges,
            "user": user,
            "object_name": object_name
        }
        
        recovery_suggestions = [
            f"Ensure user has {', '.join(required_privileges)} privileges",
            "Contact database administrator to grant necessary permissions",
            "Use a different user account with appropriate privileges"
        ]
        
        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions
        )


class QueryExecutionError(DatabaseError):
    """SQL query execution error."""
    
    default_error_code = "QUERY_EXECUTION_FAILED"
    default_severity = ErrorSeverity.MEDIUM
    exit_code = 14
    retriable = True
    
    def __init__(
        self,
        query: str,
        error_message: str,
        postgres_error_code: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        message = f"Query execution failed: {error_message}"
        
        technical_details = {
            "query": query[:500] + "..." if len(query) > 500 else query,
            "error_message": error_message,
            "postgres_error_code": postgres_error_code
        }
        
        recovery_suggestions = [
            "Check SQL query syntax",
            "Verify table and column names exist",
            "Ensure proper data types in query",
            "Check database connection stability"
        ]
        
        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            original_error=original_error
        )
```

### 3.3 設定例外クラス (config.py)

```python
"""Configuration-related exception classes."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from .base import PGSDError, ErrorSeverity, ErrorCategory


class ConfigurationError(PGSDError):
    """Base class for configuration-related errors."""
    
    default_error_code = "CONFIGURATION_ERROR"
    default_severity = ErrorSeverity.HIGH
    default_category = ErrorCategory.CONFIGURATION
    default_exit_code = 20
    retriable = False


class InvalidConfigurationError(ConfigurationError):
    """Invalid configuration values."""
    
    default_error_code = "INVALID_CONFIGURATION"
    exit_code = 21
    
    def __init__(
        self,
        config_key: str,
        invalid_value: Any,
        expected_type: Optional[str] = None,
        valid_values: Optional[List[Any]] = None,
        config_file: Optional[Path] = None
    ):
        message = f"Invalid configuration value for '{config_key}': {invalid_value}"
        
        technical_details = {
            "config_key": config_key,
            "invalid_value": str(invalid_value),
            "expected_type": expected_type,
            "valid_values": valid_values,
            "config_file": str(config_file) if config_file else None
        }
        
        recovery_suggestions = [
            f"Check the value for '{config_key}' in configuration"
        ]
        
        if expected_type:
            recovery_suggestions.append(f"Value should be of type: {expected_type}")
        
        if valid_values:
            recovery_suggestions.append(f"Valid values are: {', '.join(map(str, valid_values))}")
        
        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions
        )


class MissingConfigurationError(ConfigurationError):
    """Required configuration missing."""
    
    default_error_code = "MISSING_CONFIGURATION"
    exit_code = 22
    
    def __init__(
        self,
        missing_keys: List[str],
        config_file: Optional[Path] = None,
        config_section: Optional[str] = None
    ):
        if len(missing_keys) == 1:
            message = f"Required configuration key '{missing_keys[0]}' is missing"
        else:
            message = f"Required configuration keys are missing: {', '.join(missing_keys)}"
        
        technical_details = {
            "missing_keys": missing_keys,
            "config_file": str(config_file) if config_file else None,
            "config_section": config_section
        }
        
        recovery_suggestions = [
            "Add missing configuration keys to your configuration file",
            "Use command line arguments to provide missing values",
            "Check configuration file format and structure"
        ]
        
        if config_file:
            recovery_suggestions.append(f"Configuration file: {config_file}")
        
        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions
        )


class ConfigurationParsingError(ConfigurationError):
    """Configuration file parsing error."""
    
    default_error_code = "CONFIG_PARSING_FAILED"
    exit_code = 23
    
    def __init__(
        self,
        config_file: Path,
        parsing_error: str,
        line_number: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        message = f"Failed to parse configuration file '{config_file}': {parsing_error}"
        
        technical_details = {
            "config_file": str(config_file),
            "parsing_error": parsing_error,
            "line_number": line_number,
            "file_exists": config_file.exists(),
            "file_size": config_file.stat().st_size if config_file.exists() else None
        }
        
        recovery_suggestions = [
            "Check configuration file syntax",
            "Validate YAML/JSON format if applicable",
            "Ensure file is not corrupted",
            "Check file encoding (should be UTF-8)"
        ]
        
        if line_number:
            recovery_suggestions.append(f"Check syntax around line {line_number}")
        
        super().__init__(
            message=message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            original_error=original_error
        )
```

### 3.4 リトライ機構 (retry.py)

```python
"""Retry mechanism for error recovery."""

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple, Type, Union
from .base import PGSDError


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    jitter_range: Tuple[float, float] = (0.5, 1.5)
    retriable_exceptions: Tuple[Type[Exception], ...] = (PGSDError,)
    retry_on_result: Optional[Callable[[Any], bool]] = None
    before_retry: Optional[Callable[[int, Exception], None]] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.backoff_factor < 1:
            raise ValueError("backoff_factor must be >= 1")


class RetryManager:
    """Manages retry logic and state."""
    
    def __init__(self, config: RetryConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        if attempt <= 0:
            return 0
        
        # Exponential backoff
        delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))
        delay = min(delay, self.config.max_delay)
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_min, jitter_max = self.config.jitter_range
            jitter_factor = random.uniform(jitter_min, jitter_max)
            delay *= jitter_factor
        
        return delay
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if retry should be attempted."""
        if attempt >= self.config.max_attempts:
            return False
        
        # Check if exception type is retriable
        if not isinstance(exception, self.config.retriable_exceptions):
            return False
        
        # For PGSD errors, check if they're marked as retriable
        if isinstance(exception, PGSDError) and not exception.is_retriable():
            return False
        
        return True
    
    def execute_with_retry(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                
                # Check if result indicates retry needed
                if self.config.retry_on_result and self.config.retry_on_result(result):
                    if attempt < self.config.max_attempts:
                        self._handle_retry_attempt(attempt, None, "Result indicates retry needed")
                        continue
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    raise
                
                if attempt < self.config.max_attempts:
                    self._handle_retry_attempt(attempt, e)
                    continue
                
                # Final attempt failed
                self.logger.error(
                    f"All {self.config.max_attempts} retry attempts failed for {func.__name__}",
                    extra={"error": str(e), "attempts": attempt}
                )
                raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
    
    def _handle_retry_attempt(self, attempt: int, exception: Optional[Exception], reason: str = None):
        """Handle retry attempt logging and delay."""
        delay = self.calculate_delay(attempt)
        
        log_msg = f"Retry attempt {attempt}/{self.config.max_attempts}"
        if reason:
            log_msg += f" - {reason}"
        elif exception:
            log_msg += f" - {type(exception).__name__}: {str(exception)}"
        
        log_msg += f" (waiting {delay:.2f}s)"
        
        self.logger.warning(log_msg, extra={
            "attempt": attempt,
            "max_attempts": self.config.max_attempts,
            "delay": delay,
            "exception_type": type(exception).__name__ if exception else None
        })
        
        # Call before_retry callback if provided
        if self.config.before_retry and exception:
            try:
                self.config.before_retry(attempt, exception)
            except Exception as callback_error:
                self.logger.error(f"Error in before_retry callback: {callback_error}")
        
        # Wait before retry
        if delay > 0:
            time.sleep(delay)


def retry_on_error(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retriable_exceptions: Tuple[Type[Exception], ...] = None,
    retry_on_result: Optional[Callable[[Any], bool]] = None,
    before_retry: Optional[Callable[[int, Exception], None]] = None,
    logger: Optional[logging.Logger] = None
) -> Callable:
    """Decorator for adding retry logic to functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Exponential backoff factor
        jitter: Whether to add random jitter to delays
        retriable_exceptions: Tuple of exception types to retry on
        retry_on_result: Function to check if result indicates retry needed
        before_retry: Callback called before each retry attempt
        logger: Logger instance for retry messages
    
    Returns:
        Decorated function with retry logic
    """
    if retriable_exceptions is None:
        retriable_exceptions = (PGSDError,)
    
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        retriable_exceptions=retriable_exceptions,
        retry_on_result=retry_on_result,
        before_retry=before_retry
    )
    
    def decorator(func: Callable) -> Callable:
        retry_manager = RetryManager(config, logger)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return retry_manager.execute_with_retry(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


def async_retry_on_error(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retriable_exceptions: Tuple[Type[Exception], ...] = None,
    retry_on_result: Optional[Callable[[Any], bool]] = None,
    before_retry: Optional[Callable[[int, Exception], None]] = None,
    logger: Optional[logging.Logger] = None
) -> Callable:
    """Async version of retry decorator."""
    if retriable_exceptions is None:
        retriable_exceptions = (PGSDError,)
    
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        retriable_exceptions=retriable_exceptions,
        retry_on_result=retry_on_result,
        before_retry=before_retry
    )
    
    def decorator(func: Callable) -> Callable:
        retry_manager = RetryManager(config, logger)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    if config.retry_on_result and config.retry_on_result(result):
                        if attempt < config.max_attempts:
                            delay = retry_manager.calculate_delay(attempt)
                            retry_manager.logger.warning(f"Async retry attempt {attempt}")
                            await asyncio.sleep(delay)
                            continue
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if not retry_manager.should_retry(e, attempt):
                        raise
                    
                    if attempt < config.max_attempts:
                        delay = retry_manager.calculate_delay(attempt)
                        retry_manager.logger.warning(f"Async retry attempt {attempt}")
                        await asyncio.sleep(delay)
                        continue
                    
                    raise
            
            if last_exception:
                raise last_exception
        
        return async_wrapper
    
    return decorator
```

### 3.5 エラーメッセージカタログ (error_messages.py)

```python
"""Error message catalog for internationalization and consistency."""

from enum import Enum
from typing import Dict, Any


class ErrorMessages:
    """Centralized error message definitions."""
    
    # Database connection messages
    DB_CONNECTION_FAILED = "Failed to connect to PostgreSQL database '{database}' at {host}:{port}"
    DB_CONNECTION_TIMEOUT = "Connection to database '{database}' timed out after {timeout} seconds"
    DB_AUTH_FAILED = "Authentication failed for user '{user}' on database '{database}'"
    
    # Schema messages
    SCHEMA_NOT_FOUND = "Schema '{schema}' not found in database '{database}'"
    SCHEMA_ACCESS_DENIED = "Access denied to schema '{schema}' for user '{user}'"
    SCHEMA_EMPTY = "Schema '{schema}' contains no tables or objects"
    
    # Configuration messages
    CONFIG_FILE_NOT_FOUND = "Configuration file not found: {file_path}"
    CONFIG_INVALID_FORMAT = "Invalid configuration format in file: {file_path}"
    CONFIG_MISSING_REQUIRED = "Required configuration key '{key}' is missing"
    CONFIG_INVALID_VALUE = "Invalid value '{value}' for configuration key '{key}'"
    
    # Validation messages
    VALIDATION_FAILED = "Validation failed: {details}"
    INVALID_INPUT_FORMAT = "Invalid input format: expected {expected}, got {actual}"
    INVALID_PARAMETER_VALUE = "Invalid value for parameter '{parameter}': {value}"
    
    # Processing messages
    COMPARISON_FAILED = "Schema comparison failed: {reason}"
    REPORT_GENERATION_FAILED = "Report generation failed: {reason}"
    FILE_PROCESSING_FAILED = "File processing failed for '{file_path}': {reason}"
    
    # System messages
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions to {operation}"
    NETWORK_ERROR = "Network error occurred: {details}"
    TIMEOUT_ERROR = "Operation timed out after {timeout} seconds"
    
    # Recovery suggestions
    RECOVERY_CHECK_CONNECTION = "Check database connection parameters"
    RECOVERY_VERIFY_CREDENTIALS = "Verify database credentials"
    RECOVERY_CHECK_PERMISSIONS = "Check user permissions"
    RECOVERY_RETRY_OPERATION = "Retry the operation"
    RECOVERY_CHECK_CONFIG = "Check configuration file"
    RECOVERY_CONTACT_ADMIN = "Contact system administrator"
    
    @classmethod
    def format_message(cls, message_template: str, **kwargs) -> str:
        """Format error message with provided parameters."""
        try:
            return message_template.format(**kwargs)
        except KeyError as e:
            return f"Error formatting message template '{message_template}': missing key {e}"
    
    @classmethod
    def get_recovery_suggestions(cls, error_type: str) -> list:
        """Get standard recovery suggestions for error type."""
        suggestions_map = {
            "DatabaseConnectionError": [
                cls.RECOVERY_CHECK_CONNECTION,
                cls.RECOVERY_VERIFY_CREDENTIALS,
                cls.RECOVERY_RETRY_OPERATION
            ],
            "SchemaNotFoundError": [
                "Verify schema name is correct",
                "Check if schema exists in database",
                cls.RECOVERY_CHECK_PERMISSIONS
            ],
            "ConfigurationError": [
                cls.RECOVERY_CHECK_CONFIG,
                "Validate configuration syntax",
                "Check required configuration keys"
            ],
            "InsufficientPrivilegesError": [
                cls.RECOVERY_CHECK_PERMISSIONS,
                cls.RECOVERY_CONTACT_ADMIN,
                "Use account with appropriate privileges"
            ]
        }
        
        return suggestions_map.get(error_type, [cls.RECOVERY_RETRY_OPERATION])


class UserMessages:
    """User-friendly messages for CLI output."""
    
    # Success messages
    SUCCESS_CONNECTION = "✓ Successfully connected to database"
    SUCCESS_SCHEMA_FOUND = "✓ Schema '{schema}' found and accessible"
    SUCCESS_COMPARISON = "✓ Schema comparison completed successfully"
    SUCCESS_REPORT_GENERATED = "✓ Report generated: {file_path}"
    
    # Progress messages
    PROGRESS_CONNECTING = "Connecting to database..."
    PROGRESS_ANALYZING = "Analyzing schema '{schema}'..."
    PROGRESS_COMPARING = "Comparing schemas..."
    PROGRESS_GENERATING_REPORT = "Generating report..."
    
    # Warning messages
    WARNING_SCHEMA_EMPTY = "⚠ Schema '{schema}' appears to be empty"
    WARNING_LARGE_SCHEMA = "⚠ Schema '{schema}' contains {count} objects (this may take time)"
    WARNING_DEPRECATED_CONFIG = "⚠ Configuration option '{option}' is deprecated"
    
    # Info messages
    INFO_RETRY_ATTEMPT = "ℹ Retrying operation (attempt {attempt}/{max_attempts})"
    INFO_FALLBACK_USED = "ℹ Using fallback method for {operation}"
    INFO_CACHE_USED = "ℹ Using cached data for {resource}"


class TechnicalMessages:
    """Technical messages for logging and debugging."""
    
    # Debug messages
    DEBUG_SQL_QUERY = "Executing SQL query: {query}"
    DEBUG_CONFIG_LOADED = "Configuration loaded from: {source}"
    DEBUG_CACHE_HIT = "Cache hit for key: {key}"
    DEBUG_CACHE_MISS = "Cache miss for key: {key}"
    
    # Performance messages
    PERF_OPERATION_TIME = "Operation '{operation}' completed in {duration:.3f}s"
    PERF_MEMORY_USAGE = "Memory usage: {usage}MB"
    PERF_SLOW_QUERY = "Slow query detected ({duration:.3f}s): {query}"
    
    # System messages
    SYSTEM_STARTUP = "PGSD application starting up"
    SYSTEM_SHUTDOWN = "PGSD application shutting down"
    SYSTEM_CONFIG_RELOAD = "Configuration reloaded"
```

## 4. テスト設計

### 4.1 単体テストケース

```python
"""Test cases for error handling system."""

import pytest
import time
from unittest.mock import Mock, patch
from pgsd.exceptions import (
    PGSDError, DatabaseConnectionError, SchemaNotFoundError,
    ConfigurationError, ValidationError
)
from pgsd.error_handling.retry import retry_on_error, RetryConfig


class TestPGSDError:
    """Test cases for base PGSD error class."""
    
    def test_basic_error_creation(self):
        """Test basic error creation with minimal parameters."""
        error = PGSDError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "PGSD_ERROR"
        assert error.severity.value == "medium"
        assert isinstance(error.id, str)
        assert error.timestamp is not None
    
    def test_error_with_full_parameters(self):
        """Test error creation with all parameters."""
        original_error = ValueError("Original error")
        
        error = PGSDError(
            message="Custom error",
            error_code="CUSTOM_ERROR",
            technical_details={"key": "value"},
            recovery_suggestions=["Try again"],
            original_error=original_error,
            context={"operation": "test"}
        )
        
        assert error.error_code == "CUSTOM_ERROR"
        assert error.technical_details["key"] == "value"
        assert "Try again" in error.recovery_suggestions
        assert error.original_error == original_error
        assert error.context["operation"] == "test"
    
    def test_error_serialization(self):
        """Test error serialization to dict and JSON."""
        error = PGSDError(
            "Test error",
            error_code="TEST_ERROR",
            technical_details={"test": True}
        )
        
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "PGSDError"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["technical_details"]["test"] is True
        
        json_str = error.to_json()
        assert "TEST_ERROR" in json_str
        assert "Test error" in json_str
    
    def test_context_management(self):
        """Test adding context and recovery suggestions."""
        error = PGSDError("Test error")
        
        error.add_context("operation", "schema_comparison")
        error.add_recovery_suggestion("Check input parameters")
        
        assert error.context["operation"] == "schema_comparison"
        assert "Check input parameters" in error.recovery_suggestions
        
        # Test duplicate suggestion prevention
        error.add_recovery_suggestion("Check input parameters")
        assert error.recovery_suggestions.count("Check input parameters") == 1


class TestDatabaseConnectionError:
    """Test cases for database connection error."""
    
    def test_basic_connection_error(self):
        """Test basic database connection error."""
        error = DatabaseConnectionError(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser"
        )
        
        assert "localhost:5432" in str(error)
        assert "testdb" in str(error)
        assert "testuser" in str(error)
        assert error.technical_details["host"] == "localhost"
        assert error.technical_details["port"] == 5432
        assert error.is_retriable()
    
    def test_psycopg2_error_conversion(self):
        """Test conversion from psycopg2 error."""
        import psycopg2
        
        # Mock psycopg2 error
        pg_error = Mock(spec=psycopg2.OperationalError)
        pg_error.pgcode = "08006"
        pg_error.pgerror = "connection failed"
        
        error = DatabaseConnectionError.from_psycopg2_error(
            pg_error, "localhost", 5432, "testdb"
        )
        
        assert error.technical_details["postgres_error_code"] == "08006"
        assert error.technical_details["postgres_error_message"] == "connection failed"


class TestRetryMechanism:
    """Test cases for retry mechanism."""
    
    def test_successful_operation_no_retry(self):
        """Test successful operation that doesn't need retry."""
        call_count = 0
        
        @retry_on_error(max_attempts=3)
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_operation()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_retriable_error(self):
        """Test retry on retriable error."""
        call_count = 0
        
        @retry_on_error(max_attempts=3, base_delay=0.01)
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseConnectionError("localhost", 5432, "testdb")
            return "success"
        
        result = failing_operation()
        assert result == "success"
        assert call_count == 3
    
    def test_max_attempts_exceeded(self):
        """Test behavior when max attempts exceeded."""
        call_count = 0
        
        @retry_on_error(max_attempts=2, base_delay=0.01)
        def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise DatabaseConnectionError("localhost", 5432, "testdb")
        
        with pytest.raises(DatabaseConnectionError):
            always_failing_operation()
        
        assert call_count == 2
    
    def test_non_retriable_error(self):
        """Test that non-retriable errors are not retried."""
        call_count = 0
        
        @retry_on_error(max_attempts=3)
        def operation_with_non_retriable_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retriable")
        
        with pytest.raises(ValueError):
            operation_with_non_retriable_error()
        
        assert call_count == 1
    
    def test_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            max_delay=10.0,
            jitter=False
        )
        
        retry_manager = RetryManager(config)
        
        assert retry_manager.calculate_delay(1) == 1.0
        assert retry_manager.calculate_delay(2) == 2.0
        assert retry_manager.calculate_delay(3) == 4.0
        assert retry_manager.calculate_delay(4) == 8.0
        assert retry_manager.calculate_delay(5) == 10.0  # capped at max_delay


class TestErrorHandlerIntegration:
    """Integration tests for error handling system."""
    
    def test_database_error_flow(self):
        """Test complete database error handling flow."""
        with patch('psycopg2.connect') as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
            
            # This would be called by actual database connection code
            try:
                # Simulate database connection attempt
                raise DatabaseConnectionError("localhost", 5432, "testdb")
            except DatabaseConnectionError as e:
                # Verify error structure
                assert e.is_retriable()
                assert "localhost:5432" in str(e)
                assert len(e.recovery_suggestions) > 0
                
                # Verify error can be serialized
                error_dict = e.to_dict()
                assert error_dict["error_code"] == "DB_CONNECTION_FAILED"
    
    def test_configuration_error_flow(self):
        """Test configuration error handling flow."""
        from pgsd.exceptions.config import MissingConfigurationError
        
        error = MissingConfigurationError(
            missing_keys=["database.host", "database.port"],
            config_file=Path("config.yaml")
        )
        
        assert not error.is_retriable()
        assert "database.host" in str(error)
        assert "database.port" in str(error)
        assert error.get_exit_code() == 22
```

## 5. 実装優先順位

### 5.1 Phase 1: 基本例外クラス (本チケット)
- base.py - 基底例外クラス
- database.py - データベース例外
- config.py - 設定例外
- exit_codes.py - 終了コード定義

### 5.2 Phase 2: エラーハンドリング機構
- handler.py - メインエラーハンドラー
- retry.py - リトライ機構
- reporters.py - エラーレポーター

### 5.3 Phase 3: 統合とテスト
- 既存コードへの統合
- 包括的テスト実装
- パフォーマンス最適化

---

作成日: 2025-07-14