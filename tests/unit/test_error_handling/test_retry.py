"""
Unit tests for retry mechanism.
"""
import asyncio
import pytest
import time
from unittest.mock import Mock, patch, call
from typing import Any

from pgsd.exceptions.base import PGSDError
from pgsd.exceptions.database import DatabaseConnectionError
from pgsd.error_handling.retry import (
    RetryConfig, RetryManager, retry_on_error, async_retry_on_error
)


@pytest.mark.unit
class TestRetryConfig:
    """Test RetryConfig class."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True
        assert config.jitter_range == (0.5, 1.5)
        assert config.retriable_exceptions == (PGSDError,)
        assert config.retry_on_result is None
        assert config.before_retry is None
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        custom_exceptions = (DatabaseConnectionError, ConnectionError)
        retry_callback = Mock()
        result_checker = Mock(return_value=False)
        
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=30.0,
            backoff_factor=1.5,
            jitter=False,
            jitter_range=(0.8, 1.2),
            retriable_exceptions=custom_exceptions,
            retry_on_result=result_checker,
            before_retry=retry_callback
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 1.5
        assert config.jitter is False
        assert config.jitter_range == (0.8, 1.2)
        assert config.retriable_exceptions == custom_exceptions
        assert config.retry_on_result == result_checker
        assert config.before_retry == retry_callback
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid max_attempts
        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            RetryConfig(max_attempts=0)
        
        # Test invalid base_delay
        with pytest.raises(ValueError, match="base_delay must be non-negative"):
            RetryConfig(base_delay=-1.0)
        
        # Test invalid max_delay
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)
        
        # Test invalid backoff_factor
        with pytest.raises(ValueError, match="backoff_factor must be >= 1"):
            RetryConfig(backoff_factor=0.5)


@pytest.mark.unit
class TestRetryManager:
    """Test RetryManager class."""
    
    def test_calculate_delay_without_jitter(self):
        """Test delay calculation without jitter."""
        config = RetryConfig(
            base_delay=2.0,
            backoff_factor=3.0,
            max_delay=20.0,
            jitter=False
        )
        manager = RetryManager(config)
        
        assert manager.calculate_delay(0) == 0
        assert manager.calculate_delay(1) == 2.0
        assert manager.calculate_delay(2) == 6.0   # 2.0 * 3^1
        assert manager.calculate_delay(3) == 18.0  # 2.0 * 3^2
        assert manager.calculate_delay(4) == 20.0  # Capped at max_delay
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            max_delay=60.0,
            jitter=True,
            jitter_range=(0.5, 1.5)
        )
        manager = RetryManager(config)
        
        # Test multiple times to check jitter variability
        delays = [manager.calculate_delay(2) for _ in range(10)]
        
        # All delays should be between 1.0 and 3.0 (2.0 * jitter_range)
        for delay in delays:
            assert 1.0 <= delay <= 3.0
        
        # Should have some variability (not all the same)
        assert len(set(delays)) > 1
    
    def test_should_retry_max_attempts(self):
        """Test retry decision based on max attempts."""
        config = RetryConfig(max_attempts=3)
        manager = RetryManager(config)
        
        error = PGSDError("Test error")
        
        assert manager.should_retry(error, 1) is True
        assert manager.should_retry(error, 2) is True
        assert manager.should_retry(error, 3) is False
        assert manager.should_retry(error, 4) is False
    
    def test_should_retry_exception_type(self):
        """Test retry decision based on exception type."""
        config = RetryConfig(retriable_exceptions=(DatabaseConnectionError,))
        manager = RetryManager(config)
        
        db_error = DatabaseConnectionError("localhost", 5432, "testdb")
        other_error = ValueError("Not retriable")
        
        assert manager.should_retry(db_error, 1) is True
        assert manager.should_retry(other_error, 1) is False
    
    def test_should_retry_pgsd_error_retriable_flag(self):
        """Test retry decision for PGSD errors with retriable flag."""
        class RetriableError(PGSDError):
            retriable = True
        
        class NonRetriableError(PGSDError):
            retriable = False
        
        config = RetryConfig()
        manager = RetryManager(config)
        
        retriable_error = RetriableError("Retriable")
        non_retriable_error = NonRetriableError("Not retriable")
        
        assert manager.should_retry(retriable_error, 1) is True
        assert manager.should_retry(non_retriable_error, 1) is False
    
    @patch('time.sleep')
    def test_execute_with_retry_success_first_attempt(self, mock_sleep):
        """Test successful execution on first attempt."""
        config = RetryConfig()
        manager = RetryManager(config)
        
        mock_func = Mock(return_value="success")
        
        result = manager.execute_with_retry(mock_func, "arg1", key="value")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")
        mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    def test_execute_with_retry_success_after_retries(self, mock_sleep):
        """Test successful execution after retries."""
        config = RetryConfig(base_delay=0.1)
        manager = RetryManager(config)
        
        mock_func = Mock(side_effect=[
            DatabaseConnectionError("localhost", 5432, "testdb"),
            DatabaseConnectionError("localhost", 5432, "testdb"),
            "success"
        ])
        
        result = manager.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('time.sleep')
    def test_execute_with_retry_max_attempts_exceeded(self, mock_sleep):
        """Test failure when max attempts exceeded."""
        config = RetryConfig(max_attempts=2, base_delay=0.1)
        manager = RetryManager(config)
        
        error = DatabaseConnectionError("localhost", 5432, "testdb")
        mock_func = Mock(side_effect=error)
        
        with pytest.raises(DatabaseConnectionError):
            manager.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('time.sleep')
    def test_execute_with_retry_non_retriable_error(self, mock_sleep):
        """Test immediate failure for non-retriable errors."""
        config = RetryConfig()
        manager = RetryManager(config)
        
        mock_func = Mock(side_effect=ValueError("Not retriable"))
        
        with pytest.raises(ValueError):
            manager.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 1
        mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    def test_execute_with_retry_on_result(self, mock_sleep):
        """Test retry based on result check."""
        def should_retry_result(result):
            return result == "retry"
        
        config = RetryConfig(retry_on_result=should_retry_result, base_delay=0.1)
        manager = RetryManager(config)
        
        mock_func = Mock(side_effect=["retry", "retry", "success"])
        
        result = manager.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
    
    def test_before_retry_callback(self):
        """Test before_retry callback is called."""
        callback_mock = Mock()
        config = RetryConfig(before_retry=callback_mock, base_delay=0.01)
        manager = RetryManager(config)
        
        error = DatabaseConnectionError("localhost", 5432, "testdb")
        mock_func = Mock(side_effect=[error, "success"])
        
        result = manager.execute_with_retry(mock_func)
        
        assert result == "success"
        callback_mock.assert_called_once_with(1, error)


@pytest.mark.unit
class TestRetryDecorator:
    """Test retry_on_error decorator."""
    
    @patch('time.sleep')
    def test_successful_function_no_retry(self, mock_sleep):
        """Test successful function doesn't retry."""
        @retry_on_error(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        
        assert result == "success"
        mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    def test_function_with_retries(self, mock_sleep):
        """Test function that succeeds after retries."""
        call_count = 0
        
        @retry_on_error(max_attempts=3, base_delay=0.01)
        def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseConnectionError("localhost", 5432, "testdb")
            return "success"
        
        result = failing_then_succeeding()
        
        assert result == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('time.sleep')
    def test_function_max_attempts_exceeded(self, mock_sleep):
        """Test function that fails all attempts."""
        @retry_on_error(max_attempts=2, base_delay=0.01)
        def always_failing():
            raise DatabaseConnectionError("localhost", 5432, "testdb")
        
        with pytest.raises(DatabaseConnectionError):
            always_failing()
        
        assert mock_sleep.call_count == 1  # Only one retry
    
    def test_function_with_custom_exceptions(self):
        """Test function with custom retriable exceptions."""
        @retry_on_error(
            max_attempts=2,
            base_delay=0.01,
            retriable_exceptions=(ConnectionError,)
        )
        def function_with_different_error():
            raise DatabaseConnectionError("localhost", 5432, "testdb")
        
        # DatabaseConnectionError not in retriable_exceptions, so no retry
        with pytest.raises(DatabaseConnectionError):
            function_with_different_error()
    
    def test_function_with_retry_on_result(self):
        """Test function with result-based retry."""
        call_count = 0
        
        @retry_on_error(
            max_attempts=3,
            base_delay=0.01,
            retry_on_result=lambda x: x == "retry"
        )
        def function_returning_retry_signal():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return "retry"
            return "success"
        
        result = function_returning_retry_signal()
        
        assert result == "success"
        assert call_count == 3
    
    def test_function_with_before_retry_callback(self):
        """Test function with before_retry callback."""
        callback_mock = Mock()
        call_count = 0
        
        @retry_on_error(
            max_attempts=2,
            base_delay=0.01,
            before_retry=callback_mock
        )
        def function_with_callback():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise DatabaseConnectionError("localhost", 5432, "testdb")
            return "success"
        
        result = function_with_callback()
        
        assert result == "success"
        assert callback_mock.call_count == 1


@pytest.mark.unit
class TestAsyncRetryDecorator:
    """Test async_retry_on_error decorator."""
    
    @pytest.mark.asyncio
    async def test_successful_async_function_no_retry(self):
        """Test successful async function doesn't retry."""
        @async_retry_on_error(max_attempts=3)
        async def successful_async_function():
            return "success"
        
        result = await successful_async_function()
        
        assert result == "success"
    
    @pytest.mark.asyncio
    @patch('asyncio.sleep')
    async def test_async_function_with_retries(self, mock_sleep):
        """Test async function that succeeds after retries."""
        call_count = 0
        
        @async_retry_on_error(max_attempts=3, base_delay=0.01)
        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseConnectionError("localhost", 5432, "testdb")
            return "success"
        
        result = await failing_then_succeeding()
        
        assert result == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2
    
    @pytest.mark.asyncio
    @patch('asyncio.sleep')
    async def test_async_function_max_attempts_exceeded(self, mock_sleep):
        """Test async function that fails all attempts."""
        @async_retry_on_error(max_attempts=2, base_delay=0.01)
        async def always_failing():
            raise DatabaseConnectionError("localhost", 5432, "testdb")
        
        with pytest.raises(DatabaseConnectionError):
            await always_failing()
        
        assert mock_sleep.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_function_with_retry_on_result(self):
        """Test async function with result-based retry."""
        call_count = 0
        
        @async_retry_on_error(
            max_attempts=3,
            base_delay=0.01,
            retry_on_result=lambda x: x == "retry"
        )
        async def async_function_returning_retry_signal():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return "retry"
            return "success"
        
        result = await async_function_returning_retry_signal()
        
        assert result == "success"
        assert call_count == 3


@pytest.mark.unit
class TestRetryEdgeCases:
    """Test edge cases for retry mechanism."""
    
    def test_zero_delay(self):
        """Test retry with zero delay."""
        config = RetryConfig(base_delay=0.0, jitter=False)
        manager = RetryManager(config)
        
        assert manager.calculate_delay(1) == 0.0
        assert manager.calculate_delay(2) == 0.0
    
    def test_very_large_backoff(self):
        """Test retry with very large backoff factor."""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=10.0,
            max_delay=5.0,
            jitter=False
        )
        manager = RetryManager(config)
        
        # Should be capped at max_delay
        assert manager.calculate_delay(1) == 1.0
        assert manager.calculate_delay(2) == 5.0  # Capped
        assert manager.calculate_delay(3) == 5.0  # Capped
    
    def test_jitter_edge_values(self):
        """Test jitter with edge values."""
        config = RetryConfig(
            base_delay=2.0,
            jitter=True,
            jitter_range=(1.0, 1.0)  # No actual jitter
        )
        manager = RetryManager(config)
        
        # With jitter range (1.0, 1.0), should be exactly base_delay
        delay = manager.calculate_delay(1)
        assert delay == 2.0
    
    @patch('time.sleep')
    def test_exception_in_before_retry_callback(self, mock_sleep):
        """Test handling of exception in before_retry callback."""
        def failing_callback(attempt, error):
            raise RuntimeError("Callback failed")
        
        config = RetryConfig(
            before_retry=failing_callback,
            base_delay=0.01
        )
        manager = RetryManager(config)
        
        mock_func = Mock(side_effect=[
            DatabaseConnectionError("localhost", 5432, "testdb"),
            "success"
        ])
        
        # Should still work despite callback failure
        result = manager.execute_with_retry(mock_func)
        assert result == "success"
    
    def test_retry_manager_with_none_logger(self):
        """Test RetryManager with None logger."""
        config = RetryConfig()
        manager = RetryManager(config, logger=None)
        
        # Should not crash when logging
        mock_func = Mock(side_effect=[
            DatabaseConnectionError("localhost", 5432, "testdb"),
            "success"
        ])
        
        result = manager.execute_with_retry(mock_func)
        assert result == "success"


@pytest.mark.unit
class TestRetryPerformance:
    """Test performance characteristics of retry mechanism."""
    
    def test_delay_calculation_performance(self):
        """Test that delay calculation is fast."""
        config = RetryConfig()
        manager = RetryManager(config)
        
        start_time = time.time()
        
        for i in range(1000):
            manager.calculate_delay(i % 10 + 1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should calculate 1000 delays in less than 0.1 seconds
        assert duration < 0.1
    
    def test_retry_decision_performance(self):
        """Test that retry decision is fast."""
        config = RetryConfig()
        manager = RetryManager(config)
        
        error = DatabaseConnectionError("localhost", 5432, "testdb")
        
        start_time = time.time()
        
        for i in range(1000):
            manager.should_retry(error, i % 5 + 1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should make 1000 retry decisions in less than 0.1 seconds
        assert duration < 0.1