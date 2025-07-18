"""Simple tests for performance utilities."""

import pytest
import time
import threading
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from pgsd.utils.performance import (
    PerformanceMetric,
    PerformanceTracker,
    PerformanceContext,
    get_performance_tracker,
    measure_time,
    log_performance,
    performance_measurement
)


class TestPerformanceMetric:
    """Test PerformanceMetric dataclass."""

    def test_performance_metric_creation(self):
        """Test creating PerformanceMetric."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.5,
            timestamp=time.time(),
            context={"key": "value"},
            thread_id=123,
            success=True,
            error=None
        )
        
        assert metric.operation == "test_op"
        assert metric.duration == 1.5
        assert metric.context == {"key": "value"}
        assert metric.thread_id == 123
        assert metric.success is True
        assert metric.error is None

    def test_performance_metric_with_error(self):
        """Test creating PerformanceMetric with error."""
        metric = PerformanceMetric(
            operation="failing_op",
            duration=0.5,
            timestamp=time.time(),
            context={},
            thread_id=456,
            success=False,
            error="Test error"
        )
        
        assert metric.operation == "failing_op"
        assert metric.success is False
        assert metric.error == "Test error"

    def test_performance_metric_defaults(self):
        """Test PerformanceMetric with default values."""
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=time.time(),
            context={},
            thread_id=789
        )
        
        assert metric.success is True  # Default
        assert metric.error is None   # Default


class TestPerformanceTracker:
    """Test PerformanceTracker class."""

    def test_performance_tracker_init(self):
        """Test PerformanceTracker initialization."""
        tracker = PerformanceTracker()
        
        assert tracker._metrics == {}
        assert tracker._lock is not None

    def test_performance_tracker_record_metric(self):
        """Test recording a metric."""
        tracker = PerformanceTracker()
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=time.time(),
            context={},
            thread_id=123
        )
        
        tracker.record(metric)
        
        assert "test_op" in tracker._metrics
        assert len(tracker._metrics["test_op"]) == 1
        assert tracker._metrics["test_op"][0] == metric

    def test_performance_tracker_record_multiple_metrics(self):
        """Test recording multiple metrics for same operation."""
        tracker = PerformanceTracker()
        
        for i in range(3):
            metric = PerformanceMetric(
                operation="test_op",
                duration=float(i),
                timestamp=time.time(),
                context={},
                thread_id=123
            )
            tracker.record(metric)
        
        assert len(tracker._metrics["test_op"]) == 3
        durations = [m.duration for m in tracker._metrics["test_op"]]
        assert durations == [0.0, 1.0, 2.0]

    def test_performance_tracker_get_stats_empty(self):
        """Test getting stats for non-existent operation."""
        tracker = PerformanceTracker()
        stats = tracker.get_stats("non_existent")
        
        expected = {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        assert stats == expected

    def test_performance_tracker_get_stats_single_metric(self):
        """Test getting stats for single metric."""
        tracker = PerformanceTracker()
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.5,
            timestamp=time.time(),
            context={},
            thread_id=123
        )
        tracker.record(metric)
        
        stats = tracker.get_stats("test_op")
        
        assert stats["count"] == 1
        assert stats["avg"] == 1.5
        assert stats["min"] == 1.5
        assert stats["max"] == 1.5
        assert stats["p50"] == 1.5
        assert stats["p95"] == 1.5
        assert stats["p99"] == 1.5

    def test_performance_tracker_get_stats_multiple_metrics(self):
        """Test getting stats for multiple metrics."""
        tracker = PerformanceTracker()
        durations = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for duration in durations:
            metric = PerformanceMetric(
                operation="test_op",
                duration=duration,
                timestamp=time.time(),
                context={},
                thread_id=123
            )
            tracker.record(metric)
        
        stats = tracker.get_stats("test_op")
        
        assert stats["count"] == 5
        assert stats["avg"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["p50"] == 3.0

    def test_performance_tracker_get_stats_with_failures(self):
        """Test getting stats excluding failed operations."""
        tracker = PerformanceTracker()
        
        # Add successful metric
        success_metric = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=time.time(),
            context={},
            thread_id=123,
            success=True
        )
        tracker.record(success_metric)
        
        # Add failed metric
        failed_metric = PerformanceMetric(
            operation="test_op",
            duration=2.0,
            timestamp=time.time(),
            context={},
            thread_id=123,
            success=False
        )
        tracker.record(failed_metric)
        
        stats = tracker.get_stats("test_op")
        
        # Should only include successful metrics
        assert stats["count"] == 1
        assert stats["avg"] == 1.0

    def test_performance_tracker_get_recent_metrics(self):
        """Test getting recent metrics."""
        tracker = PerformanceTracker()
        
        # Add 5 metrics
        for i in range(5):
            metric = PerformanceMetric(
                operation="test_op",
                duration=float(i),
                timestamp=time.time(),
                context={},
                thread_id=123
            )
            tracker.record(metric)
        
        # Get recent metrics with limit
        recent = tracker.get_recent_metrics("test_op", limit=3)
        
        assert len(recent) == 3
        # Should get the last 3 metrics
        durations = [m.duration for m in recent]
        assert durations == [2.0, 3.0, 4.0]

    def test_performance_tracker_get_recent_metrics_empty(self):
        """Test getting recent metrics for non-existent operation."""
        tracker = PerformanceTracker()
        recent = tracker.get_recent_metrics("non_existent")
        
        assert recent == []

    def test_performance_tracker_clear_all(self):
        """Test clearing all metrics."""
        tracker = PerformanceTracker()
        
        # Add some metrics
        metric = PerformanceMetric(
            operation="test_op",
            duration=1.0,
            timestamp=time.time(),
            context={},
            thread_id=123
        )
        tracker.record(metric)
        
        # Clear all
        tracker.clear()
        
        assert tracker._metrics == {}

    def test_performance_tracker_clear_specific_operation(self):
        """Test clearing metrics for specific operation."""
        tracker = PerformanceTracker()
        
        # Add metrics for two operations
        metric1 = PerformanceMetric(
            operation="op1",
            duration=1.0,
            timestamp=time.time(),
            context={},
            thread_id=123
        )
        metric2 = PerformanceMetric(
            operation="op2",
            duration=2.0,
            timestamp=time.time(),
            context={},
            thread_id=123
        )
        tracker.record(metric1)
        tracker.record(metric2)
        
        # Clear only op1
        tracker.clear("op1")
        
        assert "op1" not in tracker._metrics
        assert "op2" in tracker._metrics

    def test_performance_tracker_thread_safety(self):
        """Test thread safety of PerformanceTracker."""
        tracker = PerformanceTracker()
        results = []
        
        def record_metrics():
            for i in range(100):
                metric = PerformanceMetric(
                    operation="test_op",
                    duration=float(i),
                    timestamp=time.time(),
                    context={},
                    thread_id=threading.get_ident()
                )
                tracker.record(metric)
            results.append(len(tracker._metrics["test_op"]))
        
        # Start multiple threads
        threads = [threading.Thread(target=record_metrics) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have recorded all metrics
        assert len(tracker._metrics["test_op"]) == 300


class TestPerformanceContext:
    """Test PerformanceContext class."""

    def test_performance_context_init(self):
        """Test PerformanceContext initialization."""
        context = PerformanceContext("test_op", key="value")
        
        assert context.operation_name == "test_op"
        assert context.context == {"key": "value"}
        assert context.start_time is None
        assert context.duration == 0.0
        assert context.success is True
        assert context.error is None

    def test_performance_context_success(self):
        """Test PerformanceContext with successful operation."""
        with patch('pgsd.utils.performance.logger') as mock_logger:
            with PerformanceContext("test_op") as ctx:
                time.sleep(0.01)  # Small delay
            
            assert ctx.duration > 0
            assert ctx.success is True
            assert ctx.error is None
            
            # Should log start and completion
            assert mock_logger.debug.called
            assert mock_logger.info.called

    def test_performance_context_with_exception(self):
        """Test PerformanceContext with exception."""
        with patch('pgsd.utils.performance.logger') as mock_logger:
            with pytest.raises(ValueError):
                with PerformanceContext("test_op") as ctx:
                    time.sleep(0.01)
                    raise ValueError("Test error")
            
            assert ctx.duration > 0
            assert ctx.success is False
            assert ctx.error == "Test error"
            
            # Should log warning for failed operation
            assert mock_logger.warning.called

    def test_performance_context_with_context_data(self):
        """Test PerformanceContext with context data."""
        with patch('pgsd.utils.performance.logger') as mock_logger:
            with PerformanceContext("test_op", user_id=123, action="create"):
                time.sleep(0.01)
            
            # Check that context data is logged
            info_calls = mock_logger.info.call_args_list
            assert len(info_calls) > 0
            
            # Last call should be completion log
            completion_call = info_calls[-1]
            assert "user_id" in completion_call.kwargs
            assert "action" in completion_call.kwargs
            assert completion_call.kwargs["user_id"] == 123
            assert completion_call.kwargs["action"] == "create"


class TestGetPerformanceTracker:
    """Test get_performance_tracker function."""

    def test_get_performance_tracker_returns_singleton(self):
        """Test that get_performance_tracker returns same instance."""
        tracker1 = get_performance_tracker()
        tracker2 = get_performance_tracker()
        
        assert tracker1 is tracker2

    def test_get_performance_tracker_type(self):
        """Test that get_performance_tracker returns correct type."""
        tracker = get_performance_tracker()
        
        assert isinstance(tracker, PerformanceTracker)


class TestMeasureTimeDecorator:
    """Test measure_time decorator."""

    def test_measure_time_basic(self):
        """Test basic measure_time decorator."""
        @measure_time()
        def test_function():
            time.sleep(0.01)
            return "result"
        
        with patch('pgsd.utils.performance.logger'):
            result = test_function()
        
        assert result == "result"

    def test_measure_time_with_operation_name(self):
        """Test measure_time decorator with custom operation name."""
        @measure_time("custom_operation")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        with patch('pgsd.utils.performance.logger'):
            result = test_function()
        
        assert result == "result"

    def test_measure_time_with_context(self):
        """Test measure_time decorator with context."""
        @measure_time(user_id=123, action="test")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        with patch('pgsd.utils.performance.logger'):
            result = test_function()
        
        assert result == "result"

    def test_measure_time_with_exception(self):
        """Test measure_time decorator with exception."""
        @measure_time()
        def failing_function():
            time.sleep(0.01)
            raise ValueError("Test error")
        
        with patch('pgsd.utils.performance.logger'):
            with pytest.raises(ValueError):
                failing_function()

    def test_measure_time_preserves_function_metadata(self):
        """Test that measure_time preserves function metadata."""
        @measure_time()
        def documented_function():
            """This is a test function."""
            return "result"
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."

    def test_measure_time_with_function_args(self):
        """Test measure_time decorator with function arguments."""
        @measure_time()
        def function_with_args(arg1, arg2, kwarg1=None):
            time.sleep(0.01)
            return f"{arg1}-{arg2}-{kwarg1}"
        
        with patch('pgsd.utils.performance.logger'):
            result = function_with_args("a", "b", kwarg1="c")
        
        assert result == "a-b-c"

    def test_measure_time_with_perf_context(self):
        """Test measure_time decorator with _perf_context."""
        @measure_time()
        def test_function():
            time.sleep(0.01)
            return "result"
        
        with patch('pgsd.utils.performance.logger'):
            result = test_function(_perf_context={"custom": "context"})
        
        assert result == "result"


class TestLogPerformanceDecorator:
    """Test log_performance decorator."""

    def test_log_performance_basic(self):
        """Test basic log_performance decorator."""
        @log_performance
        def test_function():
            time.sleep(0.01)
            return "result"
        
        with patch('pgsd.utils.performance.logger'):
            result = test_function()
        
        assert result == "result"

    def test_log_performance_with_exception(self):
        """Test log_performance decorator with exception."""
        @log_performance
        def failing_function():
            time.sleep(0.01)
            raise ValueError("Test error")
        
        with patch('pgsd.utils.performance.logger'):
            with pytest.raises(ValueError):
                failing_function()

    def test_log_performance_preserves_metadata(self):
        """Test that log_performance preserves function metadata."""
        @log_performance
        def documented_function():
            """This is a test function."""
            return "result"
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestPerformanceMeasurementContext:
    """Test performance_measurement context manager."""

    def test_performance_measurement_basic(self):
        """Test basic performance_measurement context manager."""
        with patch('pgsd.utils.performance.logger'):
            with performance_measurement("test_operation") as perf:
                time.sleep(0.01)
                assert isinstance(perf, PerformanceContext)
                assert perf.operation_name == "test_operation"

    def test_performance_measurement_with_context(self):
        """Test performance_measurement with context data."""
        with patch('pgsd.utils.performance.logger'):
            with performance_measurement("test_operation", user_id=123) as perf:
                time.sleep(0.01)
                assert perf.context["user_id"] == 123

    def test_performance_measurement_with_exception(self):
        """Test performance_measurement with exception."""
        with patch('pgsd.utils.performance.logger'):
            with pytest.raises(ValueError):
                with performance_measurement("test_operation") as perf:
                    time.sleep(0.01)
                    raise ValueError("Test error")
                
                assert perf.success is False
                assert perf.error == "Test error"


class TestPerformanceIntegration:
    """Integration tests for performance utilities."""

    def test_end_to_end_performance_tracking(self):
        """Test end-to-end performance tracking."""
        tracker = get_performance_tracker()
        tracker.clear()  # Start clean
        
        @measure_time("integration_test")
        def test_operation():
            time.sleep(0.01)
            return "success"
        
        with patch('pgsd.utils.performance.logger'):
            result = test_operation()
        
        assert result == "success"
        
        # Check that metric was recorded
        stats = tracker.get_stats("integration_test")
        assert stats["count"] == 1
        assert stats["avg"] > 0

    def test_multiple_operations_tracking(self):
        """Test tracking multiple different operations."""
        tracker = get_performance_tracker()
        tracker.clear()
        
        @measure_time("op1")
        def operation1():
            time.sleep(0.01)
            return "op1_result"
        
        @measure_time("op2")
        def operation2():
            time.sleep(0.01)
            return "op2_result"
        
        with patch('pgsd.utils.performance.logger'):
            operation1()
            operation2()
            operation1()  # Call op1 again
        
        # Check stats for both operations
        stats1 = tracker.get_stats("op1")
        stats2 = tracker.get_stats("op2")
        
        assert stats1["count"] == 2
        assert stats2["count"] == 1

    def test_performance_tracking_with_errors(self):
        """Test performance tracking with errors."""
        tracker = get_performance_tracker()
        tracker.clear()
        
        @measure_time("error_prone_op")
        def error_prone_operation(should_fail=False):
            time.sleep(0.01)
            if should_fail:
                raise ValueError("Intentional error")
            return "success"
        
        with patch('pgsd.utils.performance.logger'):
            # Successful call
            error_prone_operation(should_fail=False)
            
            # Failed call
            with pytest.raises(ValueError):
                error_prone_operation(should_fail=True)
        
        # Check that both calls were recorded
        recent_metrics = tracker.get_recent_metrics("error_prone_op")
        assert len(recent_metrics) == 2
        
        # Check that stats only include successful calls
        stats = tracker.get_stats("error_prone_op")
        assert stats["count"] == 1  # Only successful call

    def test_concurrent_performance_tracking(self):
        """Test concurrent performance tracking."""
        tracker = get_performance_tracker()
        tracker.clear()
        
        @measure_time("concurrent_op")
        def concurrent_operation(thread_id):
            time.sleep(0.01)
            return f"result_{thread_id}"
        
        results = []
        
        def worker(thread_id):
            with patch('pgsd.utils.performance.logger'):
                result = concurrent_operation(thread_id)
                results.append(result)
        
        # Start multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Check that all operations were tracked
        stats = tracker.get_stats("concurrent_op")
        assert stats["count"] == 5
        assert len(results) == 5