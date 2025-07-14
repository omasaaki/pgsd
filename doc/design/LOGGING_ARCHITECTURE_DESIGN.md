# ロギング機能アーキテクチャ設計

## 📋 概要
PostgreSQL Schema Diff Tool (PGSD) のロギング機能のアーキテクチャ設計書

**作成日**: 2025-07-12  
**関連チケット**: PGSD-012  
**設計者**: Claude

## 🎯 設計目標

### 機能要件
- 統一的なロギングインターフェース
- 構造化ログ（JSON形式）対応
- パフォーマンス測定機能
- 設定可能なログレベル制御
- ログローテーション対応

### 非機能要件
- 高パフォーマンス（ログ出力がボトルネックにならない）
- スレッドセーフ
- 本番・開発環境での柔軟な出力制御
- テスト時のログ抑制

## 🏗️ アーキテクチャ概要

### システム構成
```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  pgsd.main  │  pgsd.cli  │  pgsd.core.*  │  pgsd.database  │
├─────────────────────────────────────────────────────────────┤
│                   Logging Interface                         │
│              (pgsd.utils.logger)                           │
├─────────────────────────────────────────────────────────────┤
│                 Performance Monitor                         │
│             (pgsd.utils.performance)                       │
├─────────────────────────────────────────────────────────────┤
│                   Configuration                             │
│              (pgsd.utils.log_config)                       │
├─────────────────────────────────────────────────────────────┤
│                    structlog Core                           │
├─────────────────────────────────────────────────────────────┤
│    Console Handler    │    File Handler    │  JSON Handler  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 モジュール設計

### 1. pgsd/utils/logger.py
**役割**: ロガーの初期化と統一インターフェース提供

```python
"""Logging utilities for PGSD."""

import structlog
from typing import Any, Dict, Optional
from .log_config import LogConfig

class PGSDLogger:
    """Unified logger interface for PGSD."""
    
    def __init__(self, name: str):
        self.name = name
        self._logger = structlog.get_logger(name)
    
    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug message with structured data."""
        
    def info(self, event: str, **kwargs: Any) -> None:
        """Log info message with structured data."""
        
    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning message with structured data."""
        
    def error(self, event: str, **kwargs: Any) -> None:
        """Log error message with structured data."""
        
    def critical(self, event: str, **kwargs: Any) -> None:
        """Log critical message with structured data."""

def get_logger(name: str) -> PGSDLogger:
    """Get logger instance for the given name."""
    
def setup_logging(config: Optional[LogConfig] = None) -> None:
    """Setup structlog configuration."""
```

### 2. pgsd/utils/log_config.py
**役割**: ログ設定の管理

```python
"""Logging configuration management."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
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
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LogConfig":
        """Create LogConfig from dictionary."""
        
    @classmethod
    def from_yaml_file(cls, file_path: Path) -> "LogConfig":
        """Load LogConfig from YAML file."""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert LogConfig to dictionary."""

def get_default_config() -> LogConfig:
    """Get default logging configuration."""
    
def get_test_config() -> LogConfig:
    """Get test environment logging configuration."""
```

### 3. pgsd/utils/performance.py
**役割**: パフォーマンス測定とメトリクス

```python
"""Performance monitoring utilities."""

import time
import functools
from typing import Callable, Any, Dict
from .logger import get_logger

logger = get_logger(__name__)

def measure_time(operation_name: str = None):
    """Decorator to measure execution time."""
    
def log_performance(func: Callable) -> Callable:
    """Decorator to log function performance."""
    
class PerformanceContext:
    """Context manager for performance measurement."""
    
    def __init__(self, operation_name: str, **context: Any):
        self.operation_name = operation_name
        self.context = context
        self.start_time: Optional[float] = None
        
    def __enter__(self) -> "PerformanceContext":
        """Start performance measurement."""
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End performance measurement and log results."""

class PerformanceTracker:
    """Performance metrics tracker."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        
    def record(self, operation: str, duration: float, **context: Any) -> None:
        """Record performance metric."""
        
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for operation."""
        
    def clear(self) -> None:
        """Clear all metrics."""
```

## 🔧 設定仕様

### ログレベル階層
```python
CRITICAL = 50   # 致命的エラー、システム停止
ERROR = 40      # エラー、処理失敗
WARNING = 30    # 警告、処理は継続
INFO = 20       # 一般的な処理情報
DEBUG = 10      # 詳細なデバッグ情報
```

### 構造化ログフォーマット
```json
{
  "timestamp": "2025-07-12T10:30:45.123Z",
  "level": "INFO",
  "logger": "pgsd.database.connection",
  "event": "database_connection_established",
  "host": "localhost",
  "database": "test_db",
  "schema": "public",
  "connection_time_ms": 45.2,
  "process_id": 12345,
  "thread_id": 67890
}
```

### 設定ファイル例（config/logging.yaml）
```yaml
logging:
  level: "INFO"
  format: "json"
  console_output: true
  
  file:
    path: "logs/pgsd.log"
    max_size: "10MB"
    backup_count: 5
    
  performance:
    enabled: true
    slow_query_threshold: 1.0  # seconds
    
  timezone: "UTC"
  
  # 開発環境用設定
  development:
    level: "DEBUG"
    format: "console"
    
  # テスト環境用設定  
  test:
    level: "WARNING"
    console_output: false
```

## 📊 パフォーマンス測定ポイント

### 自動測定対象
1. **データベース操作**
   - 接続確立時間
   - クエリ実行時間
   - スキーマ情報取得時間

2. **差分検出処理**
   - スキーマ比較処理時間
   - 差分計算時間
   - 結果マージ時間

3. **レポート生成**
   - テンプレート処理時間
   - ファイル出力時間
   - 形式変換時間

### 測定方法
```python
# デコレータ方式
@log_performance
def extract_schema_info(self, connection):
    """Extract schema information."""
    pass

# コンテキストマネージャー方式
with PerformanceContext("schema_comparison", 
                       source_tables=len(source), 
                       target_tables=len(target)):
    differences = compare_schemas(source, target)
```

## 🔒 セキュリティ考慮事項

### 機密情報の除外
```python
SENSITIVE_FIELDS = {
    'password', 'secret', 'token', 'key', 
    'credential', 'auth', 'private'
}

def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive information from log data."""
    return {
        k: "***REDACTED***" if any(s in k.lower() for s in SENSITIVE_FIELDS) else v
        for k, v in data.items()
    }
```

### ログアクセス制御
- ログファイルの適切な権限設定（600）
- ログローテーション時の権限維持
- 機密情報を含む可能性がある場合の暗号化

## 🎨 出力フォーマット設計

### コンソール出力（開発時）
```
2025-07-12 10:30:45 [INFO ] pgsd.database: Connection established host=localhost db=test_db time=45.2ms
2025-07-12 10:30:46 [DEBUG] pgsd.core.engine: Starting schema comparison source_tables=15 target_tables=12
2025-07-12 10:30:47 [WARN ] pgsd.core.engine: Table mismatch detected table=users missing_in=target
2025-07-12 10:30:48 [ERROR] pgsd.database: Query failed query="SELECT..." error="connection timeout"
```

### JSON出力（本番時）
```json
{
  "timestamp": "2025-07-12T10:30:45.123Z",
  "level": "INFO",
  "logger": "pgsd.database.connection",
  "event": "connection_established",
  "host": "localhost",
  "database": "test_db",
  "connection_time_ms": 45.2,
  "process_id": 12345
}
```

## 🔄 ログローテーション戦略

### ファイルサイズベース
- 最大ファイルサイズ: 10MB
- バックアップファイル数: 5個
- 命名規則: `pgsd.log`, `pgsd.log.1`, `pgsd.log.2`, ...

### 時間ベース（将来拡張）
- 日次ローテーション
- 命名規則: `pgsd-2025-07-12.log`
- 保持期間: 30日

## 🧪 テスト戦略

### ログ出力テスト
```python
def test_structured_logging():
    """Test structured log output."""
    with LogCapture() as log_capture:
        logger = get_logger("test")
        logger.info("test_event", key="value", count=42)
        
        assert log_capture.records[0].event == "test_event"
        assert log_capture.records[0].key == "value"
        assert log_capture.records[0].count == 42
```

### パフォーマンス測定テスト
```python
def test_performance_measurement():
    """Test performance measurement accuracy."""
    with PerformanceContext("test_operation") as perf:
        time.sleep(0.1)  # Simulate work
        
    assert 0.09 <= perf.duration <= 0.11
```

## 📈 メトリクス・監視

### 自動収集メトリクス
- ログレベル別出力件数
- エラー発生率
- パフォーマンス統計（P50, P95, P99）
- ログファイルサイズ

### アラート基準（将来拡張）
- ERROR/CRITICALログが連続発生
- パフォーマンス劣化（閾値超過）
- ログファイル容量不足

## 🔧 実装時の注意点

### パフォーマンス
- ログ出力は非同期処理を検討
- 大量データのログ出力時はサンプリング
- デバッグレベルでの過剰な出力を避ける

### 可用性
- ログ出力エラーがアプリケーション停止を引き起こさない
- ディスク容量不足時の適切な処理
- ログファイルロック時の回避策

### 保守性
- ログメッセージの一貫性
- 将来の拡張性を考慮した設計
- 設定変更の動的反映

---

**次フェーズ**: 詳細設計・実装フェーズへ移行