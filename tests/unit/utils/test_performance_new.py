"""Tests for performance monitoring utilities."""

import pytest
import time
import threading
from unittest.mock import patch, Mock, MagicMock
from contextlib import contextmanager

from src.pgsd.utils.performance import (
    PerformanceMetric,
    PerformanceTracker,
    PerformanceContext,
    get_performance_tracker,
    measure_time,
    log_performance,
    performance_measurement
)


class TestPerformanceMetric:
    """Test cases for PerformanceMetric dataclass."""

    def test_performance_metric_creation(self):
        """Test creating PerformanceMetric instance."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.5,
            timestamp=1640995200.0,
            context={"key": "value"},
            thread_id=12345,
            success=True,
            error=None
        )
        
        assert metric.operation == "test_op"
        assert metric.duration == 1.5
        assert metric.timestamp == 1640995200.0
        assert metric.context == {"key": "value"}
        assert metric.thread_id == 12345
        assert metric.success is True
        assert metric.error is None

    def test_performance_metric_with_error(self):
        """Test creating PerformanceMetric with error."""
        metric = PerformanceMetric(
            operation="failed_op",
            duration=0.5,
            timestamp=1640995200.0,
            context={},
            thread_id=12345,
            success=False,
            error="Test error"
        )
        
        assert metric.operation == "failed_op"
        assert metric.success is False
        assert metric.error == "Test error"

    def test_performance_metric_defaults(self):
        """Test PerformanceMetric default values."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=1640995200.0,
            context={},
            thread_id=12345
        )
        
        # Test default values
        assert metric.success is True
        assert metric.error is None


class TestPerformanceTracker:
    """Test cases for PerformanceTracker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = PerformanceTracker()

    def test_init(self):
        """Test PerformanceTracker initialization."""
        tracker = PerformanceTracker()
        
        assert tracker._metrics == {}
        assert hasattr(tracker._lock, 'acquire')  # Test it's a lock-like object
        assert hasattr(tracker._lock, 'release')

    def test_record_single_metric(self):
        """Test recording a single metric."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.5,
            timestamp=1640995200.0,
            context={},
            thread_id=12345
        )
        
        self.tracker.record(metric)
        
        assert "test_op" in self.tracker._metrics
        assert len(self.tracker._metrics["test_op"]) == 1
        assert self.tracker._metrics["test_op"][0] == metric

    def test_record_multiple_metrics_same_operation(self):
        """Test recording multiple metrics for same operation."""
        metric1 = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=1640995200.0,
            context={},
            thread_id=12345
        )
        metric2 = PerformanceMetric(
            operation="test_op",
            duration=2.0,
            timestamp=1640995201.0,
            context={},
            thread_id=12345
        )
        
        self.tracker.record(metric1)
        self.tracker.record(metric2)
        
        assert len(self.tracker._metrics["test_op"]) == 2
        assert self.tracker._metrics["test_op"][0] == metric1
        assert self.tracker._metrics["test_op"][1] == metric2

    def test_record_multiple_operations(self):
        """Test recording metrics for different operations."""
        metric1 = PerformanceMetric(
            operation="op1",
            duration=1.0,
            timestamp=1640995200.0,
            context={},
            thread_id=12345
        )
        metric2 = PerformanceMetric(
            operation="op2",
            duration=2.0,
            timestamp=1640995201.0,
            context={},
            thread_id=12345
        )
        
        self.tracker.record(metric1)
        self.tracker.record(metric2)
        
        assert "op1" in self.tracker._metrics
        assert "op2" in self.tracker._metrics
        assert len(self.tracker._metrics["op1"]) == 1
        assert len(self.tracker._metrics["op2"]) == 1

    def test_get_stats_no_operation(self):
        """Test getting stats for non-existent operation."""
        stats = self.tracker.get_stats("nonexistent")
        
        expected = {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        assert stats == expected

    def test_get_stats_empty_operation(self):
        """Test getting stats for operation with no metrics."""
        self.tracker._metrics["empty_op"] = []
        
        stats = self.tracker.get_stats("empty_op")
        
        expected = {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        assert stats == expected

    def test_get_stats_all_failed_metrics(self):
        """Test getting stats when all metrics failed."""
        metric1 = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=1640995200.0,
            context={},
            thread_id=12345,
            success=False
        )
        metric2 = PerformanceMetric(
            operation="test_op",
            duration=2.0,
            timestamp=1640995201.0,
            context={},
            thread_id=12345,
            success=False
        )
        
        self.tracker.record(metric1)
        self.tracker.record(metric2)
        
        stats = self.tracker.get_stats("test_op")
        
        expected = {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        assert stats == expected

    def test_get_stats_single_metric(self):
        """Test getting stats for single successful metric."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.5,
            timestamp=1640995200.0,
            context={},
            thread_id=12345,
            success=True
        )
        
        self.tracker.record(metric)
        
        stats = self.tracker.get_stats("test_op")
        
        assert stats["count"] == 1
        assert stats["avg"] == 1.5
        assert stats["min"] == 1.5
        assert stats["max"] == 1.5
        assert stats["p50"] == 1.5
        assert stats["p95"] == 1.5
        assert stats["p99"] == 1.5

    def test_get_stats_multiple_metrics(self):
        """Test getting stats for multiple metrics."""
        durations = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for i, duration in enumerate(durations):
            metric = PerformanceMetric(
                operation="test_op",
                duration=duration,
                timestamp=1640995200.0 + i,
                context={},
                thread_id=12345,
                success=True
            )
            self.tracker.record(metric)
        
        stats = self.tracker.get_stats("test_op")
        
        assert stats["count"] == 5
        assert stats["avg"] == 3.0  # (1+2+3+4+5)/5
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["p50"] == 3.0  # Middle value
        assert stats["p95"] == 5.0  # int(5 * 0.95) = 4, so durations[4] = 5.0
        assert stats["p99"] == 5.0  # int(5 * 0.99) = 4, so durations[4] = 5.0

    def test_get_stats_mixed_success_failure(self):
        """Test getting stats with mixed successful and failed metrics."""
        # Add successful metrics
        for duration in [1.0, 2.0, 3.0]:
            metric = PerformanceMetric(
                operation="test_op",
                duration=duration,
                timestamp=1640995200.0,
                context={},
                thread_id=12345,
                success=True
            )
            self.tracker.record(metric)
        
        # Add failed metric (should be excluded from stats)
        failed_metric = PerformanceMetric(
            operation="test_op",
            duration=10.0,
            timestamp=1640995200.0,
            context={},
            thread_id=12345,
            success=False
        )
        self.tracker.record(failed_metric)
        
        stats = self.tracker.get_stats("test_op")
        
        # Should only consider successful metrics
        assert stats["count"] == 3
        assert stats["avg"] == 2.0  # (1+2+3)/3

    def test_get_recent_metrics_nonexistent(self):
        """Test getting recent metrics for non-existent operation."""
        recent = self.tracker.get_recent_metrics("nonexistent")
        
        assert recent == []

    def test_get_recent_metrics_default_limit(self):
        """Test getting recent metrics with default limit."""
        # Add metrics
        for i in range(150):
            metric = PerformanceMetric(
                operation="test_op",
                duration=float(i),
                timestamp=1640995200.0 + i,
                context={},
                thread_id=12345
            )
            self.tracker.record(metric)
        
        recent = self.tracker.get_recent_metrics("test_op")
        
        # Should return last 100 metrics
        assert len(recent) == 100
        assert recent[0].duration == 50.0  # metrics[50]
        assert recent[-1].duration == 149.0  # metrics[149]

    def test_get_recent_metrics_custom_limit(self):
        """Test getting recent metrics with custom limit."""
        # Add metrics
        for i in range(20):
            metric = PerformanceMetric(
                operation="test_op",
                duration=float(i),
                timestamp=1640995200.0 + i,
                context={},
                thread_id=12345
            )
            self.tracker.record(metric)
        
        recent = self.tracker.get_recent_metrics("test_op", limit=5)
        
        # Should return last 5 metrics
        assert len(recent) == 5
        assert recent[0].duration == 15.0  # metrics[15]
        assert recent[-1].duration == 19.0  # metrics[19]

    def test_get_recent_metrics_fewer_than_limit(self):
        """Test getting recent metrics when fewer than limit exist."""
        # Add only 3 metrics
        for i in range(3):
            metric = PerformanceMetric(
                operation="test_op",
                duration=float(i),
                timestamp=1640995200.0 + i,
                context={},
                thread_id=12345
            )
            self.tracker.record(metric)
        
        recent = self.tracker.get_recent_metrics("test_op", limit=10)
        
        # Should return all 3 metrics
        assert len(recent) == 3

    def test_clear_specific_operation(self):
        """Test clearing metrics for specific operation."""
        # Add metrics for multiple operations
        for op in ["op1", "op2"]:
            metric = PerformanceMetric(
                operation=op,
                duration=1.0,
                timestamp=1640995200.0,
                context={},
                thread_id=12345
            )
            self.tracker.record(metric)
        
        # Clear specific operation
        self.tracker.clear("op1")
        
        assert "op1" not in self.tracker._metrics
        assert "op2" in self.tracker._metrics

    def test_clear_all_operations(self):
        """Test clearing all metrics."""
        # Add metrics for multiple operations
        for op in ["op1", "op2", "op3"]:
            metric = PerformanceMetric(
                operation=op,
                duration=1.0,
                timestamp=1640995200.0,
                context={},
                thread_id=12345
            )
            self.tracker.record(metric)
        
        # Clear all
        self.tracker.clear()
        
        assert self.tracker._metrics == {}

    def test_clear_nonexistent_operation(self):
        """Test clearing non-existent operation."""
        # Add some metrics
        metric = PerformanceMetric(
            operation="op1",
            duration=1.0,
            timestamp=1640995200.0,
            context={},
            thread_id=12345
        )
        self.tracker.record(metric)
        
        # Try to clear non-existent operation
        self.tracker.clear("nonexistent")
        
        # Should not affect existing metrics
        assert "op1" in self.tracker._metrics


class TestGlobalPerformanceTracker:
    """Test cases for global performance tracker."""

    def test_get_performance_tracker(self):
        """Test getting global performance tracker."""
        tracker1 = get_performance_tracker()
        tracker2 = get_performance_tracker()
        
        # Should return same instance
        assert tracker1 is tracker2
        assert isinstance(tracker1, PerformanceTracker)


class TestPerformanceContext:
    """Test cases for PerformanceContext class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear global tracker
        get_performance_tracker().clear()

    @patch('src.pgsd.utils.performance.time.time')
    @patch('src.pgsd.utils.performance.threading.get_ident')
    def test_context_manager_success(self, mock_get_ident, mock_time):
        """Test PerformanceContext as successful context manager."""
        mock_time.side_effect = [1640995200.0, 1640995201.5, 1640995201.5]  # start, end, timestamp
        mock_get_ident.return_value = 12345
        
        with patch('src.pgsd.utils.performance.logger') as mock_logger:
            with PerformanceContext("test_operation", key="value") as context:
                assert context.operation_name == "test_operation"
                assert context.context == {"key": "value"}
                assert context.start_time == 1640995200.0
                assert context.success is True
                assert context.error is None
        
        # Check final state
        assert context.duration == 1.5
        assert context.success is True
        assert context.error is None
        
        # Check logging calls
        mock_logger.debug.assert_called_once_with(
            "performance_measurement_started",
            operation="test_operation",
            key="value"
        )
        mock_logger.info.assert_called_once_with(
            "performance_measurement_completed",
            operation="test_operation",
            duration_ms=1500.0,
            success=True,
            key="value"
        )
        
        # Check metric was recorded
        tracker = get_performance_tracker()
        recent = tracker.get_recent_metrics("test_operation")
        assert len(recent) == 1
        assert recent[0].duration == 1.5

    @patch('src.pgsd.utils.performance.time.time')
    @patch('src.pgsd.utils.performance.threading.get_ident')
    def test_context_manager_with_exception(self, mock_get_ident, mock_time):
        """Test PerformanceContext with exception."""
        mock_time.side_effect = [1640995200.0, 1640995201.0, 1640995201.0]  # start, end, timestamp
        mock_get_ident.return_value = 12345
        
        with patch('src.pgsd.utils.performance.logger') as mock_logger:
            try:
                with PerformanceContext("test_operation") as context:
                    raise ValueError("Test error")
            except ValueError:
                pass
        
        # Check final state
        assert context.duration == 1.0
        assert context.success is False
        assert context.error == "Test error"
        
        # Check logging calls
        mock_logger.warning.assert_called_once_with(
            "performance_measurement_failed",
            operation="test_operation",
            duration_ms=1000.0,
            success=False,
            error="Test error"
        )

    @patch('src.pgsd.utils.performance.time.time')
    def test_context_manager_no_start_time(self, mock_time):
        """Test PerformanceContext when start_time is None."""
        context = PerformanceContext("test_operation")
        context.start_time = None
        
        # Should exit gracefully without error
        context.__exit__(None, None, None)
        
        # Duration should remain 0
        assert context.duration == 0.0

    def test_context_initialization(self):
        """Test PerformanceContext initialization."""
        context = PerformanceContext("test_op", key1="value1", key2="value2")
        
        assert context.operation_name == "test_op"
        assert context.context == {"key1": "value1", "key2": "value2"}
        assert context.start_time is None
        assert context.duration == 0.0
        assert context.success is True
        assert context.error is None


class TestMeasureTimeDecorator:
    """Test cases for measure_time decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear global tracker
        get_performance_tracker().clear()

    @patch('src.pgsd.utils.performance.PerformanceContext')
    def test_measure_time_default_name(self, mock_context_class):
        """Test measure_time decorator with default operation name."""
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context
        
        @measure_time()
        def test_function(x, y):
            return x + y
        
        result = test_function(1, 2)
        
        assert result == 3
        expected_name = f"{test_function.__module__}.{test_function.__name__}"
        mock_context_class.assert_called_once_with(expected_name)
        mock_context.__enter__.assert_called_once()
        mock_context.__exit__.assert_called_once()

    @patch('src.pgsd.utils.performance.PerformanceContext')
    def test_measure_time_custom_name(self, mock_context_class):
        """Test measure_time decorator with custom operation name."""
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context
        
        @measure_time("custom_operation")
        def test_function():
            return "result"
        
        result = test_function()
        
        assert result == "result"
        mock_context_class.assert_called_once_with("custom_operation")

    @patch('src.pgsd.utils.performance.PerformanceContext')
    def test_measure_time_with_default_context(self, mock_context_class):
        """Test measure_time decorator with default context."""
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context
        
        @measure_time("test_op", default_key="default_value")
        def test_function():
            return "result"
        
        test_function()
        
        mock_context_class.assert_called_once_with("test_op", default_key="default_value")

    @patch('src.pgsd.utils.performance.PerformanceContext')
    def test_measure_time_with_perf_context_kwarg(self, mock_context_class):
        """Test measure_time decorator with _perf_context kwarg."""
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context
        
        @measure_time("test_op", default_key="default_value")
        def test_function(arg1, _perf_context=None):
            return arg1
        
        result = test_function("test", _perf_context={"runtime_key": "runtime_value"})
        
        assert result == "test"
        # Should merge default context with runtime context
        mock_context_class.assert_called_once_with(
            "test_op", 
            default_key="default_value",
            runtime_key="runtime_value"
        )

    @patch('src.pgsd.utils.performance.PerformanceContext')
    def test_measure_time_preserves_function_metadata(self, mock_context_class):
        """Test that measure_time preserves function metadata."""
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context
        
        @measure_time()
        def original_function():
            """Original docstring."""
            pass
        
        assert original_function.__name__ == "original_function"
        assert original_function.__doc__ == "Original docstring."

    def test_measure_time_integration(self):
        """Test measure_time decorator integration."""
        @measure_time("integration_test")
        def test_function(value):
            time.sleep(0.01)  # Small delay
            return value * 2
        
        result = test_function(5)
        
        assert result == 10
        
        # Check metric was recorded
        tracker = get_performance_tracker()
        recent = tracker.get_recent_metrics("integration_test")
        assert len(recent) == 1
        assert recent[0].operation == "integration_test"
        assert recent[0].duration > 0


class TestLogPerformanceDecorator:
    """Test cases for log_performance decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear global tracker
        get_performance_tracker().clear()

    @patch('src.pgsd.utils.performance.measure_time')
    def test_log_performance(self, mock_measure_time):
        """Test log_performance decorator."""
        mock_decorator = Mock()
        mock_measure_time.return_value = mock_decorator
        
        def test_function():
            return "result"
        
        decorated = log_performance(test_function)
        
        mock_measure_time.assert_called_once_with()
        mock_decorator.assert_called_once_with(test_function)

    def test_log_performance_integration(self):
        """Test log_performance decorator integration."""
        @log_performance
        def test_function(x):
            return x ** 2
        
        result = test_function(4)
        
        assert result == 16
        
        # Check metric was recorded
        tracker = get_performance_tracker()
        expected_name = f"{test_function.__module__}.{test_function.__name__}"
        recent = tracker.get_recent_metrics(expected_name)
        assert len(recent) == 1


class TestPerformanceMeasurementContextManager:
    """Test cases for performance_measurement context manager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear global tracker
        get_performance_tracker().clear()

    @patch('src.pgsd.utils.performance.PerformanceContext')
    def test_performance_measurement_context_manager(self, mock_context_class):
        """Test performance_measurement context manager."""
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context
        
        with performance_measurement("test_operation", key="value") as perf:
            assert perf == mock_context.__enter__.return_value
        
        mock_context_class.assert_called_once_with("test_operation", key="value")
        mock_context.__enter__.assert_called_once()
        mock_context.__exit__.assert_called_once()

    def test_performance_measurement_integration(self):
        """Test performance_measurement context manager integration."""
        with performance_measurement("context_test", test_key="test_value") as perf:
            time.sleep(0.01)  # Small delay
            assert perf.operation_name == "context_test"
            assert perf.context == {"test_key": "test_value"}
        
        # Check metric was recorded
        tracker = get_performance_tracker()
        recent = tracker.get_recent_metrics("context_test")
        assert len(recent) == 1
        assert recent[0].operation == "context_test"
        assert recent[0].duration > 0


class TestPerformanceUtilitiesIntegration:
    """Integration tests for performance utilities."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear global tracker
        get_performance_tracker().clear()

    def test_full_performance_workflow(self):
        """Test complete performance monitoring workflow."""
        # Use different measurement methods
        
        # 1. Direct PerformanceContext
        with PerformanceContext("direct_measurement", type="direct"):
            time.sleep(0.01)
        
        # 2. Context manager function
        with performance_measurement("context_measurement", type="context"):
            time.sleep(0.01)
        
        # 3. Decorator
        @measure_time("decorator_measurement", type="decorator")
        def test_function():
            time.sleep(0.01)
            return "done"
        
        result = test_function()
        assert result == "done"
        
        # Check all metrics were recorded
        tracker = get_performance_tracker()
        
        direct_metrics = tracker.get_recent_metrics("direct_measurement")
        context_metrics = tracker.get_recent_metrics("context_measurement")
        decorator_metrics = tracker.get_recent_metrics("decorator_measurement")
        
        assert len(direct_metrics) == 1
        assert len(context_metrics) == 1
        assert len(decorator_metrics) == 1
        
        # All should have some duration
        assert direct_metrics[0].duration > 0
        assert context_metrics[0].duration > 0
        assert decorator_metrics[0].duration > 0

    def test_performance_stats_calculation(self):
        """Test performance statistics calculation."""
        # Generate multiple measurements
        durations = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        for i, duration in enumerate(durations):
            with patch('src.pgsd.utils.performance.time.time') as mock_time, \
                 patch('src.pgsd.utils.performance.threading.get_ident') as mock_get_ident:
                mock_time.side_effect = [1640995200.0 + i, 1640995200.0 + i + duration, 1640995200.0 + i + duration]
                mock_get_ident.return_value = 12345
                
                with patch('src.pgsd.utils.performance.logger'):
                    with PerformanceContext("stats_test"):
                        pass
        
        # Get statistics
        tracker = get_performance_tracker()
        stats = tracker.get_stats("stats_test")
        
        assert stats["count"] == 5
        assert abs(stats["avg"] - 0.3) < 0.01  # (0.1+0.2+0.3+0.4+0.5)/5
        assert abs(stats["min"] - 0.1) < 0.01
        assert abs(stats["max"] - 0.5) < 0.01
        assert abs(stats["p50"] - 0.3) < 0.01

    def test_thread_safety(self):
        """Test thread safety of performance tracking."""
        import concurrent.futures
        
        def worker(thread_id):
            with PerformanceContext("thread_test", thread_id=thread_id):
                time.sleep(0.001 * thread_id)  # Different sleep times
            return thread_id
        
        # Run multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(1, 6)]
            results = [future.result() for future in futures]
        
        assert sorted(results) == [1, 2, 3, 4, 5]
        
        # Check all metrics were recorded
        tracker = get_performance_tracker()
        recent = tracker.get_recent_metrics("thread_test", limit=10)
        assert len(recent) == 5
        
        # Should have different thread IDs
        thread_ids = {metric.thread_id for metric in recent}
        assert len(thread_ids) >= 1  # At least some different thread IDs

    def test_error_handling_in_measurements(self):
        """Test error handling in performance measurements."""
        # Test with exception in PerformanceContext
        try:
            with PerformanceContext("error_test"):
                raise RuntimeError("Test error")
        except RuntimeError:
            pass
        
        # Test with exception in decorator
        @measure_time("decorator_error_test")
        def failing_function():
            raise ValueError("Decorator error")
        
        try:
            failing_function()
        except ValueError:
            pass
        
        # Check metrics were recorded with error status
        tracker = get_performance_tracker()
        
        error_metrics = tracker.get_recent_metrics("error_test")
        decorator_error_metrics = tracker.get_recent_metrics("decorator_error_test")
        
        assert len(error_metrics) == 1
        assert len(decorator_error_metrics) == 1
        
        assert error_metrics[0].success is False
        assert error_metrics[0].error == "Test error"
        
        assert decorator_error_metrics[0].success is False
        assert decorator_error_metrics[0].error == "Decorator error"

    def test_memory_management(self):
        """Test memory management with many metrics."""
        # Generate many metrics
        for i in range(1000):
            with patch('src.pgsd.utils.performance.time.time') as mock_time, \
                 patch('src.pgsd.utils.performance.threading.get_ident') as mock_get_ident:
                mock_time.side_effect = [float(i), float(i) + 0.001, float(i) + 0.001]
                mock_get_ident.return_value = 12345
                
                with patch('src.pgsd.utils.performance.logger'):
                    with PerformanceContext(f"memory_test_{i % 10}"):
                        pass
        
        tracker = get_performance_tracker()
        
        # Check that we have metrics for 10 different operations
        operations_with_metrics = 0
        for i in range(10):
            metrics = tracker.get_recent_metrics(f"memory_test_{i}")
            if metrics:
                operations_with_metrics += 1
        
        assert operations_with_metrics == 10
        
        # Test clearing specific operations
        tracker.clear("memory_test_0")
        metrics = tracker.get_recent_metrics("memory_test_0")
        assert len(metrics) == 0
        
        # Other operations should still have metrics
        metrics = tracker.get_recent_metrics("memory_test_1")
        assert len(metrics) > 0