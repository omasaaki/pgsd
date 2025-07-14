"""Tests for performance monitoring utilities - Implementation."""

import pytest
import time
import threading
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from pgsd.utils.performance import (
    PerformanceContext,
    PerformanceTracker,
    PerformanceMetric,
    measure_time,
    log_performance,
    performance_measurement,
    get_performance_tracker,
)


class TestPerformanceMetric:
    """Test PerformanceMetric dataclass."""

    def test_metric_creation(self):
        """Test PerformanceMetric creation."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.5,
            timestamp=time.time(),
            context={"key": "value"},
            thread_id=123,
            success=True,
        )
        assert metric.operation == "test_op"
        assert metric.duration == 1.5
        assert metric.context == {"key": "value"}
        assert metric.success is True
        assert metric.error is None

    def test_metric_with_error(self):
        """Test PerformanceMetric with error information."""
        metric = PerformanceMetric(
            operation="failed_op",
            duration=0.5,
            timestamp=time.time(),
            context={},
            thread_id=123,
            success=False,
            error="Test error message",
        )
        assert metric.success is False
        assert metric.error == "Test error message"

    def test_metric_default_success(self):
        """Test PerformanceMetric default success value."""
        metric = PerformanceMetric(
            operation="default_op",
            duration=1.0,
            timestamp=time.time(),
            context={},
            thread_id=123,
        )
        assert metric.success is True
        assert metric.error is None


class TestPerformanceTracker:
    """Test PerformanceTracker functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.tracker = PerformanceTracker()

    def test_tracker_initialization(self):
        """Test PerformanceTracker initialization."""
        tracker = PerformanceTracker()
        assert len(tracker._metrics) == 0
        assert tracker._lock is not None

    def test_record_metric(self):
        """Test recording performance metrics."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=time.time(),
            context={},
            thread_id=123,
        )
        self.tracker.record(metric)

        stats = self.tracker.get_stats("test_op")
        assert stats["count"] == 1
        assert stats["avg"] == 1.0

    def test_get_stats_empty(self):
        """Test get_stats for non-existent operation."""
        stats = self.tracker.get_stats("non_existent")

        assert stats["count"] == 0
        assert stats["avg"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0

    def test_get_stats_single_metric(self):
        """Test get_stats with single metric."""
        metric = PerformanceMetric(
            operation="single_op",
            duration=2.5,
            timestamp=time.time(),
            context={},
            thread_id=123,
        )
        self.tracker.record(metric)

        stats = self.tracker.get_stats("single_op")
        assert stats["count"] == 1
        assert stats["avg"] == 2.5
        assert stats["min"] == 2.5
        assert stats["max"] == 2.5
        assert stats["p50"] == 2.5
        assert stats["p95"] == 2.5
        assert stats["p99"] == 2.5

    def test_get_stats_multiple_metrics(self):
        """Test get_stats with multiple metrics."""
        durations = [1.0, 2.0, 3.0, 4.0, 5.0]

        for i, duration in enumerate(durations):
            metric = PerformanceMetric(
                operation="multi_op",
                duration=duration,
                timestamp=time.time(),
                context={"iteration": i},
                thread_id=123,
            )
            self.tracker.record(metric)

        stats = self.tracker.get_stats("multi_op")
        assert stats["count"] == 5
        assert stats["avg"] == 3.0  # (1+2+3+4+5)/5
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["p50"] == 3.0  # Median

    def test_get_stats_with_failed_operations(self):
        """Test get_stats excludes failed operations."""
        # Add successful metrics
        for duration in [1.0, 2.0, 3.0]:
            metric = PerformanceMetric(
                operation="mixed_op",
                duration=duration,
                timestamp=time.time(),
                context={},
                thread_id=123,
                success=True,
            )
            self.tracker.record(metric)

        # Add failed metric
        failed_metric = PerformanceMetric(
            operation="mixed_op",
            duration=10.0,  # This should be excluded
            timestamp=time.time(),
            context={},
            thread_id=123,
            success=False,
            error="Test error",
        )
        self.tracker.record(failed_metric)

        stats = self.tracker.get_stats("mixed_op")
        assert stats["count"] == 3  # Only successful operations
        assert stats["avg"] == 2.0  # (1+2+3)/3
        assert stats["max"] == 3.0  # Failed operation excluded

    def test_get_recent_metrics(self):
        """Test get_recent_metrics functionality."""
        # Add multiple metrics
        for i in range(10):
            metric = PerformanceMetric(
                operation="recent_op",
                duration=i * 0.1,
                timestamp=time.time(),
                context={"iteration": i},
                thread_id=123,
            )
            self.tracker.record(metric)

        # Get recent metrics
        recent = self.tracker.get_recent_metrics("recent_op", limit=5)
        assert len(recent) == 5
        # Should be the last 5 metrics
        assert recent[-1].context["iteration"] == 9
        assert recent[0].context["iteration"] == 5

    def test_get_recent_metrics_non_existent(self):
        """Test get_recent_metrics for non-existent operation."""
        recent = self.tracker.get_recent_metrics("non_existent")
        assert recent == []

    def test_clear_specific_operation(self):
        """Test clearing metrics for specific operation."""
        # Add metrics for different operations
        for op in ["op1", "op2"]:
            metric = PerformanceMetric(
                operation=op,
                duration=1.0,
                timestamp=time.time(),
                context={},
                thread_id=123,
            )
            self.tracker.record(metric)

        # Clear only op1
        self.tracker.clear("op1")

        assert self.tracker.get_stats("op1")["count"] == 0
        assert self.tracker.get_stats("op2")["count"] == 1

    def test_clear_all_operations(self):
        """Test clearing all metrics."""
        # Add metrics for different operations
        for op in ["op1", "op2", "op3"]:
            metric = PerformanceMetric(
                operation=op,
                duration=1.0,
                timestamp=time.time(),
                context={},
                thread_id=123,
            )
            self.tracker.record(metric)

        # Clear all
        self.tracker.clear()

        for op in ["op1", "op2", "op3"]:
            assert self.tracker.get_stats(op)["count"] == 0

    def test_thread_safety(self):
        """Test PerformanceTracker thread safety."""

        def record_metrics(thread_id, count=100):
            for i in range(count):
                metric = PerformanceMetric(
                    operation="thread_test",
                    duration=0.001 * i,
                    timestamp=time.time(),
                    context={"thread": thread_id, "iteration": i},
                    thread_id=thread_id,
                )
                self.tracker.record(metric)

        # Run multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(record_metrics, i, 50) for i in range(5)]
            for future in futures:
                future.result()

        stats = self.tracker.get_stats("thread_test")
        assert stats["count"] == 250  # 5 threads * 50 metrics each


class TestPerformanceContext:
    """Test PerformanceContext functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Clear global tracker
        get_performance_tracker().clear()

    def test_context_basic_usage(self):
        """Test basic PerformanceContext usage."""
        with PerformanceContext("test_operation") as perf:
            time.sleep(0.01)

        assert perf.operation_name == "test_operation"
        assert perf.duration >= 0.01
        assert perf.success is True
        assert perf.error is None

    def test_context_with_custom_context(self):
        """Test PerformanceContext with custom context data."""
        with PerformanceContext("test_op", user_id=123, action="test") as perf:
            time.sleep(0.001)

        assert perf.context["user_id"] == 123
        assert perf.context["action"] == "test"

    def test_context_with_exception(self):
        """Test PerformanceContext with exception handling."""
        with pytest.raises(ValueError):
            with PerformanceContext("error_operation") as perf:
                raise ValueError("Test error")

        assert perf.success is False
        assert "Test error" in perf.error
        assert perf.duration > 0

    def test_context_records_to_tracker(self):
        """Test PerformanceContext records metrics to global tracker."""
        # Clear tracker
        get_performance_tracker().clear()

        with PerformanceContext("tracked_operation"):
            time.sleep(0.001)

        stats = get_performance_tracker().get_stats("tracked_operation")
        assert stats["count"] == 1

    @patch("pgsd.utils.performance.logger")
    def test_context_logging(self, mock_logger):
        """Test PerformanceContext logging."""
        with PerformanceContext("logged_operation", test_data="value"):
            time.sleep(0.001)

        # Should log start and completion
        assert mock_logger.debug.called
        assert mock_logger.info.called

    @patch("pgsd.utils.performance.logger")
    def test_context_logging_with_error(self, mock_logger):
        """Test PerformanceContext logging with error."""
        with pytest.raises(RuntimeError):
            with PerformanceContext("error_operation"):
                raise RuntimeError("Test runtime error")

        # Should log warning for failed operation
        assert mock_logger.warning.called


class TestPerformanceDecorators:
    """Test performance measurement decorators."""

    def setup_method(self):
        """Setup test environment."""
        get_performance_tracker().clear()

    def test_measure_time_decorator(self):
        """Test measure_time decorator."""

        @measure_time("decorated_function")
        def test_function(x, y):
            time.sleep(0.001)
            return x + y

        result = test_function(1, 2)
        assert result == 3

        stats = get_performance_tracker().get_stats("decorated_function")
        assert stats["count"] >= 1

    def test_measure_time_with_default_name(self):
        """Test measure_time decorator with default name."""

        @measure_time()
        def test_function_default():
            time.sleep(0.001)
            return "test"

        result = test_function_default()
        assert result == "test"

        # Should use module.function_name
        expected_name = f"{test_function_default.__module__}.test_function_default"
        stats = get_performance_tracker().get_stats(expected_name)
        assert stats["count"] >= 1

    def test_measure_time_with_context(self):
        """Test measure_time decorator with context data."""

        @measure_time("context_function", service="test")
        def test_function_with_context(value):
            time.sleep(0.001)
            return value * 2

        result = test_function_with_context(5, _perf_context={"user": "test_user"})
        assert result == 10

        # Check that context was recorded
        recent = get_performance_tracker().get_recent_metrics("context_function", 1)
        assert len(recent) == 1
        assert recent[0].context["service"] == "test"
        assert recent[0].context["user"] == "test_user"

    def test_log_performance_decorator(self):
        """Test log_performance decorator."""

        @log_performance
        def test_logged_function():
            time.sleep(0.001)
            return "logged"

        result = test_logged_function()
        assert result == "logged"

        # Should be tracked with module.function name
        expected_name = f"{test_logged_function.__module__}.test_logged_function"
        stats = get_performance_tracker().get_stats(expected_name)
        assert stats["count"] >= 1

    def test_decorator_preserves_function_metadata(self):
        """Test that decorators preserve function metadata."""

        @measure_time("metadata_test")
        def documented_function(x):
            """This is a test function."""
            return x

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."

    def test_decorator_with_exception(self):
        """Test decorator handles exceptions properly."""

        @measure_time("exception_test")
        def failing_function():
            raise ValueError("Decorator test error")

        with pytest.raises(ValueError):
            failing_function()

        # Should still record the metric as failed
        recent = get_performance_tracker().get_recent_metrics("exception_test", 1)
        assert len(recent) == 1
        assert recent[0].success is False
        assert "Decorator test error" in recent[0].error


class TestPerformanceMeasurement:
    """Test performance_measurement context manager."""

    def setup_method(self):
        """Setup test environment."""
        get_performance_tracker().clear()

    def test_performance_measurement_context(self):
        """Test performance_measurement context manager."""
        with performance_measurement("context_test", data="test") as perf:
            time.sleep(0.001)
            perf_result = perf

        assert perf_result.operation_name == "context_test"
        assert perf_result.context["data"] == "test"
        assert perf_result.duration > 0

    def test_performance_measurement_exception(self):
        """Test performance_measurement with exception."""
        with pytest.raises(RuntimeError):
            with performance_measurement("error_context") as perf:
                raise RuntimeError("Test runtime error")

        assert perf.success is False
        assert "Test runtime error" in perf.error


class TestPerformanceIntegration:
    """Integration tests for performance monitoring."""

    def setup_method(self):
        """Setup test environment."""
        get_performance_tracker().clear()

    def test_global_tracker_singleton(self):
        """Test that get_performance_tracker returns singleton."""
        tracker1 = get_performance_tracker()
        tracker2 = get_performance_tracker()
        assert tracker1 is tracker2

    def test_concurrent_operations(self):
        """Test concurrent performance monitoring."""

        def worker(operation_name, iterations=10):
            for i in range(iterations):
                with PerformanceContext(operation_name, iteration=i):
                    time.sleep(0.001)

        # Run multiple operations concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(worker, f"concurrent_op_{i}", 5) for i in range(3)
            ]
            for future in futures:
                future.result()

        # Each operation should have its own metrics
        for i in range(3):
            stats = get_performance_tracker().get_stats(f"concurrent_op_{i}")
            assert stats["count"] == 5

    def test_high_volume_metrics(self):
        """Test performance with high volume of metrics."""
        # Record many metrics quickly
        for i in range(1000):
            metric = PerformanceMetric(
                operation="high_volume",
                duration=0.001 * i,
                timestamp=time.time(),
                context={"batch": i // 100},
                thread_id=threading.get_ident(),
            )
            get_performance_tracker().record(metric)

        stats = get_performance_tracker().get_stats("high_volume")
        assert stats["count"] == 1000

    def test_mixed_success_failure_tracking(self):
        """Test tracking of both successful and failed operations."""
        tracker = get_performance_tracker()

        # Add mix of successful and failed operations
        success_count = 0
        for i in range(10):
            success = i % 3 != 0  # Fail every 3rd operation
            if success:
                success_count += 1
            error = None if success else f"Error {i}"

            metric = PerformanceMetric(
                operation="mixed_results",
                duration=0.1 * i,
                timestamp=time.time(),
                context={"iteration": i},
                thread_id=123,
                success=success,
                error=error,
            )
            tracker.record(metric)

        stats = tracker.get_stats("mixed_results")
        # Should only count successful operations
        assert stats["count"] == success_count

        # Check recent metrics includes both success and failure
        recent = tracker.get_recent_metrics("mixed_results", 20)
        assert len(recent) == 10  # All metrics, including failed ones


# Test fixtures and utilities
@pytest.fixture
def clean_performance_tracker():
    """Provide clean performance tracker for testing."""
    get_performance_tracker().clear()
    yield get_performance_tracker()
    get_performance_tracker().clear()


@pytest.fixture
def mock_time():
    """Mock time.time() for predictable testing."""
    with patch("time.time") as mock:
        mock.return_value = 1609459200.0  # Fixed timestamp
        yield mock


def create_test_metric(operation="test", duration=1.0, success=True, **context):
    """Helper to create test performance metrics."""
    return PerformanceMetric(
        operation=operation,
        duration=duration,
        timestamp=time.time(),
        context=context,
        thread_id=threading.get_ident(),
        success=success,
        error=None if success else "Test error",
    )
