"""Performance monitoring utilities."""

import time
import threading
import functools
from typing import Callable, Any, Dict, Optional, List
from dataclasses import dataclass
from contextlib import contextmanager
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance measurement data."""

    operation: str
    duration: float
    timestamp: float
    context: Dict[str, Any]
    thread_id: int
    success: bool = True
    error: Optional[str] = None


class PerformanceTracker:
    """Thread-safe performance metrics tracker."""

    def __init__(self) -> None:
        """Initialize performance tracker."""
        self._metrics: Dict[str, List[PerformanceMetric]] = {}
        self._lock = threading.Lock()

    def record(self, metric: PerformanceMetric) -> None:
        """Record performance metric.

        Args:
            metric: Performance metric to record
        """
        with self._lock:
            if metric.operation not in self._metrics:
                self._metrics[metric.operation] = []
            self._metrics[metric.operation].append(metric)

    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for operation.

        Args:
            operation: Operation name

        Returns:
            Statistics dictionary with avg, min, max, count
        """
        with self._lock:
            if operation not in self._metrics or not self._metrics[operation]:
                return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}

            durations = [m.duration for m in self._metrics[operation] if m.success]
            if not durations:
                return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}

            sorted_durations = sorted(durations)
            count = len(durations)

            return {
                "count": count,
                "avg": sum(durations) / count,
                "min": min(durations),
                "max": max(durations),
                "p50": sorted_durations[count // 2],
                "p95": (
                    sorted_durations[int(count * 0.95)] if count > 1 else durations[0]
                ),
                "p99": (
                    sorted_durations[int(count * 0.99)] if count > 1 else durations[0]
                ),
            }

    def get_recent_metrics(
        self, operation: str, limit: int = 100
    ) -> List[PerformanceMetric]:
        """Get recent metrics for operation.

        Args:
            operation: Operation name
            limit: Maximum number of metrics to return

        Returns:
            List of recent performance metrics
        """
        with self._lock:
            if operation not in self._metrics:
                return []
            return self._metrics[operation][-limit:]

    def clear(self, operation: Optional[str] = None) -> None:
        """Clear metrics.

        Args:
            operation: Operation name to clear. If None, clear all.
        """
        with self._lock:
            if operation is None:
                self._metrics.clear()
            elif operation in self._metrics:
                del self._metrics[operation]


# Global performance tracker
_performance_tracker = PerformanceTracker()


def get_performance_tracker() -> PerformanceTracker:
    """Get global performance tracker.

    Returns:
        Global PerformanceTracker instance
    """
    return _performance_tracker


class PerformanceContext:
    """Context manager for performance measurement."""

    def __init__(self, operation_name: str, **context: Any) -> None:
        """Initialize performance context.

        Args:
            operation_name: Name of the operation being measured
            **context: Additional context data
        """
        self.operation_name = operation_name
        self.context = context
        self.start_time: Optional[float] = None
        self.duration: float = 0.0
        self.success = True
        self.error: Optional[str] = None

    def __enter__(self) -> "PerformanceContext":
        """Start performance measurement.

        Returns:
            Self for chaining
        """
        self.start_time = time.time()
        logger.debug(
            "performance_measurement_started",
            operation=self.operation_name,
            **self.context,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End performance measurement and log results.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if self.start_time is None:
            return

        self.duration = time.time() - self.start_time

        if exc_type is not None:
            self.success = False
            self.error = str(exc_val) if exc_val else str(exc_type)

        # Record metric
        metric = PerformanceMetric(
            operation=self.operation_name,
            duration=self.duration,
            timestamp=time.time(),
            context=self.context,
            thread_id=threading.get_ident(),
            success=self.success,
            error=self.error,
        )
        _performance_tracker.record(metric)

        # Log performance result
        log_data = {
            "operation": self.operation_name,
            "duration_ms": round(self.duration * 1000, 2),
            "success": self.success,
            **self.context,
        }

        if self.error:
            log_data["error"] = self.error
            logger.warning("performance_measurement_failed", **log_data)
        else:
            logger.info("performance_measurement_completed", **log_data)


def measure_time(operation_name: Optional[str] = None, **default_context: Any):
    """Decorator to measure execution time.

    Args:
        operation_name: Name of operation. If None, uses function name.
        **default_context: Default context data

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Merge default context with any context passed to function
            context = {**default_context}
            if "_perf_context" in kwargs:
                context.update(kwargs.pop("_perf_context"))

            with PerformanceContext(op_name, **context):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_performance(func: Callable) -> Callable:
    """Decorator to log function performance.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function
    """
    return measure_time()(func)


@contextmanager
def performance_measurement(operation_name: str, **context: Any):
    """Context manager for performance measurement.

    Args:
        operation_name: Name of the operation
        **context: Additional context data

    Yields:
        PerformanceContext instance
    """
    with PerformanceContext(operation_name, **context) as perf:
        yield perf
