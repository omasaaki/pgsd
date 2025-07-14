"""Retry mechanism for error handling."""

import asyncio
import functools
import random
import time
from typing import Any, Callable, Optional, Tuple, Type
from dataclasses import dataclass

from ..exceptions.base import PGSDError


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
        """Validate configuration parameters."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.backoff_factor < 1:
            raise ValueError("backoff_factor must be >= 1")


class RetryManager:
    """Manages retry logic and execution."""

    def __init__(self, config: RetryConfig, logger=None):
        """Initialize retry manager.

        Args:
            config: Retry configuration
            logger: Optional logger for retry events
        """
        self.config = config
        self.logger = logger

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Args:
            attempt: Attempt number (starting from 1)

        Returns:
            Delay in seconds
        """
        if attempt <= 0:
            return 0

        # Calculate exponential backoff
        delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))

        # Apply maximum delay cap
        delay = min(delay, self.config.max_delay)

        # Apply jitter if enabled
        if self.config.jitter:
            jitter_min, jitter_max = self.config.jitter_range
            jitter_factor = random.uniform(jitter_min, jitter_max)
            delay *= jitter_factor

        return delay

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error should be retried.

        Args:
            error: Exception that occurred
            attempt: Current attempt number

        Returns:
            True if should retry
        """
        # Check max attempts
        if attempt >= self.config.max_attempts:
            return False

        # Check if exception type is retriable
        if not isinstance(error, self.config.retriable_exceptions):
            return False

        # For PGSD errors, check retriable flag
        if isinstance(error, PGSDError):
            return error.is_retriable()

        return True

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = func(*args, **kwargs)

                # Check if result should trigger retry
                if self.config.retry_on_result and self.config.retry_on_result(result):
                    if attempt < self.config.max_attempts:
                        delay = self.calculate_delay(attempt)
                        if self.logger:
                            self.logger.info(
                                f"Result triggered retry, attempt {attempt + 1} in {delay:.2f}s"
                            )
                        time.sleep(delay)
                        continue

                return result

            except Exception as e:
                last_exception = e

                if not self.should_retry(e, attempt):
                    raise

                # Call before_retry callback if provided
                if self.config.before_retry:
                    try:
                        self.config.before_retry(attempt, e)
                    except Exception:
                        # Don't let callback failure stop retry
                        if self.logger:
                            self.logger.warning(
                                "before_retry callback failed", exc_info=True
                            )

                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    if self.logger:
                        self.logger.info(
                            f"Retrying after {type(e).__name__}, attempt {attempt + 1} in {delay:.2f}s"
                        )
                    time.sleep(delay)

        # All retries exhausted
        raise last_exception


def retry_on_error(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    jitter_range: Tuple[float, float] = (0.5, 1.5),
    retriable_exceptions: Tuple[Type[Exception], ...] = (PGSDError,),
    retry_on_result: Optional[Callable[[Any], bool]] = None,
    before_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable:
    """Decorator for adding retry behavior to functions.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        backoff_factor: Exponential backoff factor
        jitter: Whether to apply jitter to delays
        jitter_range: Range for jitter multiplication
        retriable_exceptions: Tuple of exception types to retry
        retry_on_result: Function to check if result should trigger retry
        before_retry: Callback called before each retry

    Returns:
        Decorated function
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        jitter_range=jitter_range,
        retriable_exceptions=retriable_exceptions,
        retry_on_result=retry_on_result,
        before_retry=before_retry,
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = RetryManager(config)
            return manager.execute_with_retry(func, *args, **kwargs)

        return wrapper

    return decorator


def async_retry_on_error(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    jitter_range: Tuple[float, float] = (0.5, 1.5),
    retriable_exceptions: Tuple[Type[Exception], ...] = (PGSDError,),
    retry_on_result: Optional[Callable[[Any], bool]] = None,
    before_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable:
    """Async decorator for adding retry behavior to async functions.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        backoff_factor: Exponential backoff factor
        jitter: Whether to apply jitter to delays
        jitter_range: Range for jitter multiplication
        retriable_exceptions: Tuple of exception types to retry
        retry_on_result: Function to check if result should trigger retry
        before_retry: Callback called before each retry

    Returns:
        Decorated async function
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        jitter_range=jitter_range,
        retriable_exceptions=retriable_exceptions,
        retry_on_result=retry_on_result,
        before_retry=before_retry,
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = RetryManager(config)
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)

                    # Check if result should trigger retry
                    if config.retry_on_result and config.retry_on_result(result):
                        if attempt < config.max_attempts:
                            delay = manager.calculate_delay(attempt)
                            await asyncio.sleep(delay)
                            continue

                    return result

                except Exception as e:
                    last_exception = e

                    if not manager.should_retry(e, attempt):
                        raise

                    # Call before_retry callback if provided
                    if config.before_retry:
                        try:
                            config.before_retry(attempt, e)
                        except Exception:
                            pass  # Don't let callback failure stop retry

                    if attempt < config.max_attempts:
                        delay = manager.calculate_delay(attempt)
                        await asyncio.sleep(delay)

            # All retries exhausted
            raise last_exception

        return async_wrapper

    return decorator
