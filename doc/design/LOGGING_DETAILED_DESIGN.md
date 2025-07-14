# ロギング機能詳細設計

## 📋 概要
PostgreSQL Schema Diff Tool (PGSD) のロギング機能の詳細設計書

**作成日**: 2025-07-12  
**関連チケット**: PGSD-012  
**設計者**: Claude

## 🏗️ モジュール詳細設計

### 1. pgsd/utils/logger.py

#### 1.1 PGSDLogger クラス
```python
"""Logging utilities for PGSD."""

import structlog
import sys
from typing import Any, Dict, Optional, Union
from pathlib import Path
from .log_config import LogConfig, get_default_config

class PGSDLogger:
    """Unified logger interface for PGSD."""
    
    def __init__(self, name: str) -> None:
        """Initialize logger with given name.
        
        Args:
            name: Logger name (typically module name)
        """
        self.name = name
        self._logger = structlog.get_logger(name)
    
    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug message with structured data.
        
        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.debug(event, **self._sanitize_data(kwargs))
    
    def info(self, event: str, **kwargs: Any) -> None:
        """Log info message with structured data.
        
        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.info(event, **self._sanitize_data(kwargs))
    
    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning message with structured data.
        
        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.warning(event, **self._sanitize_data(kwargs))
    
    def error(self, event: str, **kwargs: Any) -> None:
        """Log error message with structured data.
        
        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.error(event, **self._sanitize_data(kwargs))
    
    def critical(self, event: str, **kwargs: Any) -> None:
        """Log critical message with structured data.
        
        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.critical(event, **self._sanitize_data(kwargs))
    
    def exception(self, event: str, **kwargs: Any) -> None:
        """Log exception with traceback.
        
        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.exception(event, **self._sanitize_data(kwargs))
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from log data.
        
        Args:
            data: Original data dictionary
            
        Returns:
            Sanitized data dictionary
        """
        SENSITIVE_FIELDS = {
            'password', 'secret', 'token', 'key', 
            'credential', 'auth', 'private', 'passwd'
        }
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
```

#### 1.2 モジュール関数
```python
# Global logger registry
_logger_registry: Dict[str, PGSDLogger] = {}
_is_configured = False

def get_logger(name: str) -> PGSDLogger:
    """Get logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        PGSDLogger instance
    """
    if not _is_configured:
        setup_logging()
    
    if name not in _logger_registry:
        _logger_registry[name] = PGSDLogger(name)
    
    return _logger_registry[name]

def setup_logging(config: Optional[LogConfig] = None) -> None:
    """Setup structlog configuration.
    
    Args:
        config: Logging configuration. If None, uses default config.
    """
    global _is_configured
    
    if config is None:
        config = get_default_config()
    
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FILENAME,
                       structlog.processors.CallsiteParameter.LINENO]
        ),
    ]
    
    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    import logging
    import logging.handlers
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.level.upper()))
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.file_path:
        config.file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))
        root_logger.addHandler(file_handler)
    
    _is_configured = True

def reset_logging() -> None:
    """Reset logging configuration (primarily for testing)."""
    global _is_configured, _logger_registry
    _is_configured = False
    _logger_registry.clear()
    
    import logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
```

### 2. pgsd/utils/log_config.py

#### 2.1 LogConfig データクラス
```python
"""Logging configuration management."""

import os
import yaml
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union
from pathlib import Path

@dataclass
class LogConfig:
    """Logging configuration."""
    
    level: str = "INFO"
    format: str = "json"  # json, console
    file_path: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    timezone: str = "UTC"
    enable_performance: bool = True
    console_output: bool = True
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}. Must be one of {valid_levels}")
        
        valid_formats = {"json", "console"}
        if self.format not in valid_formats:
            raise ValueError(f"Invalid format: {self.format}. Must be one of {valid_formats}")
        
        if self.file_path and isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
        
        if self.max_file_size <= 0:
            raise ValueError("max_file_size must be positive")
        
        if self.backup_count < 0:
            raise ValueError("backup_count must be non-negative")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LogConfig":
        """Create LogConfig from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            LogConfig instance
        """
        # Handle nested logging configuration
        if "logging" in config_dict:
            config_dict = config_dict["logging"]
        
        # Handle file configuration
        if "file" in config_dict:
            file_config = config_dict.pop("file")
            if "path" in file_config:
                config_dict["file_path"] = file_config["path"]
            if "max_size" in file_config:
                config_dict["max_file_size"] = cls._parse_size(file_config["max_size"])
            if "backup_count" in file_config:
                config_dict["backup_count"] = file_config["backup_count"]
        
        # Handle performance configuration
        if "performance" in config_dict:
            perf_config = config_dict.pop("performance")
            if "enabled" in perf_config:
                config_dict["enable_performance"] = perf_config["enabled"]
        
        # Filter known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_config = {k: v for k, v in config_dict.items() if k in known_fields}
        
        return cls(**filtered_config)
    
    @classmethod
    def from_yaml_file(cls, file_path: Path) -> "LogConfig":
        """Load LogConfig from YAML file.
        
        Args:
            file_path: Path to YAML configuration file
            
        Returns:
            LogConfig instance
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_environment(cls) -> "LogConfig":
        """Create LogConfig from environment variables.
        
        Returns:
            LogConfig instance
        """
        config_dict = {}
        
        if level := os.getenv("PGSD_LOG_LEVEL"):
            config_dict["level"] = level
        
        if format_type := os.getenv("PGSD_LOG_FORMAT"):
            config_dict["format"] = format_type
        
        if file_path := os.getenv("PGSD_LOG_FILE"):
            config_dict["file_path"] = file_path
        
        if console_output := os.getenv("PGSD_LOG_CONSOLE"):
            config_dict["console_output"] = console_output.lower() in ("true", "1", "yes")
        
        return cls.from_dict(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LogConfig to dictionary.
        
        Returns:
            Configuration dictionary
        """
        data = asdict(self)
        
        # Convert Path to string
        if data["file_path"]:
            data["file_path"] = str(data["file_path"])
        
        return data
    
    @staticmethod
    def _parse_size(size_str: Union[str, int]) -> int:
        """Parse size string to bytes.
        
        Args:
            size_str: Size string like "10MB" or integer
            
        Returns:
            Size in bytes
        """
        if isinstance(size_str, int):
            return size_str
        
        size_str = size_str.upper()
        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                number = size_str[:-len(suffix)]
                return int(float(number) * multiplier)
        
        # If no suffix, assume bytes
        return int(size_str)

def get_default_config() -> LogConfig:
    """Get default logging configuration.
    
    Returns:
        Default LogConfig instance
    """
    return LogConfig(
        level="INFO",
        format="console",  # Console format for development
        console_output=True,
        file_path=None,
        enable_performance=True
    )

def get_production_config() -> LogConfig:
    """Get production logging configuration.
    
    Returns:
        Production LogConfig instance
    """
    return LogConfig(
        level="INFO",
        format="json",
        console_output=False,
        file_path=Path("logs/pgsd.log"),
        max_file_size=50 * 1024 * 1024,  # 50MB
        backup_count=10,
        enable_performance=True
    )

def get_test_config() -> LogConfig:
    """Get test environment logging configuration.
    
    Returns:
        Test LogConfig instance
    """
    return LogConfig(
        level="WARNING",
        format="console",
        console_output=False,  # Suppress output during tests
        file_path=None,
        enable_performance=False
    )
```

### 3. pgsd/utils/performance.py

#### 3.1 パフォーマンス測定機能
```python
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
                "p95": sorted_durations[int(count * 0.95)] if count > 1 else durations[0],
                "p99": sorted_durations[int(count * 0.99)] if count > 1 else durations[0],
            }
    
    def get_recent_metrics(self, operation: str, limit: int = 100) -> List[PerformanceMetric]:
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
        logger.debug("performance_measurement_started", 
                    operation=self.operation_name, **self.context)
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
            error=self.error
        )
        _performance_tracker.record(metric)
        
        # Log performance result
        log_data = {
            "operation": self.operation_name,
            "duration_ms": round(self.duration * 1000, 2),
            "success": self.success,
            **self.context
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
```

## 🧪 テストケース詳細設計

### 1. tests/unit/test_utils/test_logger.py

```python
"""Tests for logging utilities."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from pgsd.utils.logger import get_logger, setup_logging, reset_logging
from pgsd.utils.log_config import LogConfig

class TestPGSDLogger:
    """Test PGSDLogger functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        reset_logging()
    
    def test_logger_creation(self):
        """Test logger instance creation."""
        logger1 = get_logger("test.module1")
        logger2 = get_logger("test.module2")
        logger1_again = get_logger("test.module1")
        
        assert logger1.name == "test.module1"
        assert logger2.name == "test.module2"
        assert logger1 is logger1_again  # Same instance
    
    def test_log_levels(self, caplog):
        """Test different log levels."""
        config = LogConfig(level="DEBUG", format="console")
        setup_logging(config)
        
        logger = get_logger("test.logger")
        
        logger.debug("debug message", key="debug_value")
        logger.info("info message", key="info_value")
        logger.warning("warning message", key="warning_value")
        logger.error("error message", key="error_value")
        logger.critical("critical message", key="critical_value")
        
        assert len(caplog.records) == 5
    
    def test_structured_logging(self, caplog):
        """Test structured data logging."""
        config = LogConfig(level="INFO", format="console")
        setup_logging(config)
        
        logger = get_logger("test.structured")
        logger.info("test_event", 
                   user_id=123,
                   operation="test",
                   metadata={"key": "value"})
        
        record = caplog.records[0]
        assert "test_event" in record.getMessage()
        assert record.user_id == 123
        assert record.operation == "test"
        assert record.metadata == {"key": "value"}
    
    def test_sensitive_data_sanitization(self, caplog):
        """Test sensitive data is redacted."""
        config = LogConfig(level="INFO", format="console")
        setup_logging(config)
        
        logger = get_logger("test.sanitize")
        logger.info("login_attempt",
                   username="testuser",
                   password="secret123",
                   auth_token="token456")
        
        record = caplog.records[0]
        assert record.username == "testuser"
        assert record.password == "***REDACTED***"
        assert record.auth_token == "***REDACTED***"
    
    def test_json_format_output(self):
        """Test JSON format output."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            config = LogConfig(
                level="INFO",
                format="json",
                file_path=Path(f.name),
                console_output=False
            )
            setup_logging(config)
            
            logger = get_logger("test.json")
            logger.info("json_test", key="value", number=42)
            
            # Force log flush
            import logging
            for handler in logging.getLogger().handlers:
                handler.flush()
            
            # Read and verify JSON
            f.seek(0)
            log_line = f.readline().strip()
            log_data = json.loads(log_line)
            
            assert log_data["event"] == "json_test"
            assert log_data["key"] == "value"
            assert log_data["number"] == 42
            assert "timestamp" in log_data
```

### 2. tests/unit/test_utils/test_performance.py

```python
"""Tests for performance monitoring."""

import time
import pytest
from pgsd.utils.performance import (
    PerformanceContext, PerformanceTracker, measure_time,
    performance_measurement, get_performance_tracker
)

class TestPerformanceTracker:
    """Test PerformanceTracker functionality."""
    
    def test_performance_context(self):
        """Test performance context manager."""
        with PerformanceContext("test_operation", user_id=123) as perf:
            time.sleep(0.01)  # Simulate work
        
        assert perf.operation_name == "test_operation"
        assert perf.duration > 0.005  # At least 5ms
        assert perf.success is True
        assert perf.context["user_id"] == 123
    
    def test_performance_context_with_exception(self):
        """Test performance context with exception."""
        with pytest.raises(ValueError):
            with PerformanceContext("test_error") as perf:
                raise ValueError("Test error")
        
        assert perf.success is False
        assert "Test error" in perf.error
        assert perf.duration > 0
    
    def test_measure_time_decorator(self):
        """Test measure_time decorator."""
        tracker = PerformanceTracker()
        
        @measure_time("decorated_function")
        def test_function(x, y):
            time.sleep(0.01)
            return x + y
        
        result = test_function(1, 2)
        assert result == 3
        
        # Performance should be recorded
        stats = get_performance_tracker().get_stats("decorated_function")
        assert stats["count"] >= 1
    
    def test_performance_tracker_stats(self):
        """Test performance statistics calculation."""
        tracker = PerformanceTracker()
        
        # Add some test metrics
        for i in range(10):
            with PerformanceContext("test_stats"):
                time.sleep(0.001 * (i + 1))  # Variable duration
        
        stats = get_performance_tracker().get_stats("test_stats")
        
        assert stats["count"] == 10
        assert stats["avg"] > 0
        assert stats["min"] > 0
        assert stats["max"] > stats["min"]
        assert stats["p50"] > 0
        assert stats["p95"] > 0
```

## 🔧 エラーハンドリング設計

### エラー分類と対応

1. **設定エラー**
   - 無効なログレベル → ValueError with clear message
   - 無効なファイルパス → FileNotFoundError
   - YAML解析エラー → yaml.YAMLError

2. **ランタイムエラー**
   - ディスク容量不足 → 適切なfallback（コンソール出力）
   - ファイル権限エラー → ログ出力継続、警告表示
   - ログローテーションエラー → 既存ファイル使用継続

3. **パフォーマンス測定エラー**
   - 測定開始前のコンテキスト終了 → 無視
   - 例外発生時の測定 → エラー情報付きで記録

### エラー回復戦略

```python
def safe_log_output(self, level: str, event: str, **kwargs: Any) -> None:
    """Safe logging with fallback on errors."""
    try:
        getattr(self._logger, level.lower())(event, **kwargs)
    except Exception as e:
        # Fallback to console output
        print(f"[LOG ERROR] Failed to log: {event} - {e}", file=sys.stderr)
```

---

**次フェーズ**: テストコード作成作業へ移行