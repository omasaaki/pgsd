# データベース接続管理アーキテクチャ設計書

## 1. 概要

PostgreSQL Schema Diff Tool (PGSD)のデータベース接続管理システムのアーキテクチャ設計を定義する。安全で効率的なデータベース接続、接続プール管理、バージョン検出、権限確認を提供する。

## 2. アーキテクチャ方針

### 2.1 設計原則
- **接続安定性**: 堅牢な接続管理と自動再接続
- **パフォーマンス**: 効率的な接続プール管理
- **セキュリティ**: 接続情報の安全な管理
- **可観測性**: 詳細なログ記録と監視
- **拡張性**: 複数データベース対応

### 2.2 技術選択
- **メインドライバー**: psycopg2（安定性重視）
- **接続プール**: カスタム実装（要件特化）
- **非同期対応**: 将来拡張用の設計
- **設定統合**: PGSD-014設定管理との連携

## 3. システム構成

### 3.1 コンポーネント図

```
┌─────────────────────────────────────────────────────────────┐
│                Database Connection Layer                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │   DatabaseManager   │  │     ConnectionFactory          │  │
│  │  - Multi-DB support │  │  - Connection creation        │  │
│  │  - Lifecycle mgmt   │  │  - SSL/Auth handling          │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
│              │                           │                     │
│              └───────────┬───────────────┘                     │
│                          │                                     │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │                ConnectionPool                             │  │
│  │  - Pool management    - Health monitoring               │  │
│  │  - Connection reuse   - Auto-cleanup                    │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                          │                                     │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │              DatabaseConnector                           │  │
│  │  - Low-level connection - Query execution               │  │
│  │  - Version detection    - Permission validation         │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
└─────────────────────────────┼─────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │           PostgreSQL Database           │
        │         (Source / Target)               │
        └─────────────────────────────────────────┘
```

### 3.2 レイヤー構成

#### Layer 1: Database Manager
- **責務**: 複数データベースの統合管理
- **機能**: 
  - ソース・ターゲットDB管理
  - ライフサイクル制御
  - エラー統合処理

#### Layer 2: Connection Factory & Pool
- **責務**: 接続の生成と管理
- **機能**:
  - 接続文字列構築
  - SSL/認証処理
  - 接続プール管理
  - ヘルスチェック

#### Layer 3: Database Connector
- **責務**: 低レベル接続操作
- **機能**:
  - 直接接続管理
  - クエリ実行
  - バージョン検出
  - 権限確認

## 4. 詳細設計

### 4.1 DatabaseManager クラス

```python
class DatabaseManager:
    """複数データベースの統合管理"""
    
    def __init__(self, config: PGSDConfiguration):
        self.config = config
        self.source_pool: Optional[ConnectionPool] = None
        self.target_pool: Optional[ConnectionPool] = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> None:
        """データベース接続の初期化"""
        
    async def get_source_connection(self) -> DatabaseConnector:
        """ソースDB接続取得"""
        
    async def get_target_connection(self) -> DatabaseConnector:
        """ターゲットDB接続取得"""
        
    async def verify_connections(self) -> Dict[str, bool]:
        """全接続の検証"""
        
    async def close_all(self) -> None:
        """全接続のクリーンアップ"""
```

### 4.2 ConnectionPool クラス

```python
class ConnectionPool:
    """接続プール管理"""
    
    def __init__(self, db_config: DatabaseConfig, max_connections: int = 5):
        self.db_config = db_config
        self.max_connections = max_connections
        self.active_connections: List[psycopg2.connection] = []
        self.available_connections: queue.Queue = queue.Queue()
        self.health_monitor = HealthMonitor()
    
    async def get_connection(self) -> psycopg2.connection:
        """接続取得（プールから再利用または新規作成）"""
        
    async def return_connection(self, connection: psycopg2.connection) -> None:
        """接続返却"""
        
    async def health_check(self) -> PoolHealth:
        """プール健全性チェック"""
        
    async def cleanup_stale_connections(self) -> None:
        """古い接続のクリーンアップ"""
```

### 4.3 DatabaseConnector クラス

```python
class DatabaseConnector:
    """個別データベース接続管理"""
    
    def __init__(self, connection: psycopg2.connection, db_config: DatabaseConfig):
        self.connection = connection
        self.db_config = db_config
        self.version_info: Optional[PostgreSQLVersion] = None
        self.permissions: Optional[Dict[str, bool]] = None
    
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """クエリ実行"""
        
    async def get_version(self) -> PostgreSQLVersion:
        """PostgreSQLバージョン取得"""
        
    async def check_permissions(self) -> Dict[str, bool]:
        """権限確認"""
        
    async def verify_schema_access(self, schema_name: str) -> bool:
        """スキーマアクセス確認"""
        
    async def test_connection(self) -> bool:
        """接続テスト"""
```

## 5. セキュリティ設計

### 5.1 接続情報の保護
- **パスワード管理**: 環境変数またはキーストア
- **接続文字列**: メモリ内での最小限保持
- **ログ記録**: 機密情報の自動マスキング

### 5.2 SSL/TLS サポート
```python
ssl_config = {
    'sslmode': db_config.ssl_mode.value,
    'sslcert': db_config.ssl_cert,
    'sslkey': db_config.ssl_key,
    'sslrootcert': db_config.ssl_ca,
    'sslcrl': None
}
```

### 5.3 権限最小化
- **読み取り専用アクセス**: スキーマ情報の取得のみ
- **必要最小権限**: USAGE, SELECT権限のみ
- **権限検証**: 接続時の自動確認

## 6. パフォーマンス設計

### 6.1 接続プール最適化
- **プールサイズ**: 設定可能（デフォルト5）
- **接続再利用**: アクティブ接続の効率的管理
- **タイムアウト管理**: 接続・クエリタイムアウト
- **ヘルスチェック**: 定期的な接続生存確認

### 6.2 メモリ管理
```python
class MemoryManager:
    """メモリ使用量の監視と制御"""
    
    def __init__(self, max_memory_mb: int):
        self.max_memory_mb = max_memory_mb
        self.current_usage = 0
    
    def check_memory_usage(self) -> bool:
        """メモリ使用量チェック"""
        
    def cleanup_if_needed(self) -> None:
        """必要に応じたクリーンアップ"""
```

## 7. エラーハンドリング統合

### 7.1 PGSD例外との統合
```python
# PGSD-013で実装した例外との連携
try:
    connection = await pool.get_connection()
except psycopg2.OperationalError as e:
    raise DatabaseConnectionError.from_psycopg2_error(
        e, host=db_config.host, port=db_config.port, 
        database=db_config.database, user=db_config.username
    )
```

### 7.2 リトライ機構統合
```python
@retry_on_error(
    max_attempts=3,
    base_delay=1.0,
    retriable_exceptions=(DatabaseConnectionError,)
)
async def establish_connection(db_config: DatabaseConfig) -> psycopg2.connection:
    """リトライ付き接続確立"""
```

## 8. 監視・ログ設計

### 8.1 メトリクス収集
- **接続数**: アクティブ/アイドル接続数
- **接続時間**: 接続確立時間の測定
- **クエリ実行時間**: パフォーマンス監視
- **エラー率**: 接続・クエリエラー率

### 8.2 ログ出力
```python
# 接続ログ例
logger.info("Database connection established", extra={
    "host": db_config.host,
    "database": db_config.database,
    "user": db_config.username,
    "ssl_mode": db_config.ssl_mode.value,
    "connection_time_ms": connection_time
})
```

## 9. テスト戦略

### 9.1 単体テスト
- 接続プール動作テスト
- バージョン検出テスト
- 権限確認テスト
- エラーハンドリングテスト

### 9.2 統合テスト
- 複数DB同時接続テスト
- 長時間接続安定性テスト
- 障害復旧テスト
- 負荷テスト

### 9.3 モックテスト
```python
class MockDatabaseConnector:
    """テスト用のモックコネクター"""
    
    def __init__(self, version: str = "14.0", permissions: Dict[str, bool] = None):
        self.version = PostgreSQLVersion.parse(version)
        self.permissions = permissions or {"usage": True, "select": True}
```

## 10. 設定統合

### 10.1 PGSD-014設定管理との連携
```python
# 設定からのデータベース接続情報取得
config_manager = ConfigurationManager()
config = config_manager.get_configuration()

db_manager = DatabaseManager(config)
await db_manager.initialize()
```

### 10.2 環境別設定
- **開発環境**: 接続プール最小化
- **本番環境**: 接続プール最適化
- **テスト環境**: モック使用可能

## 11. 非同期対応設計

### 11.1 将来拡張対応
```python
# 現在は同期、将来の非同期対応を考慮した設計
class AsyncDatabaseConnector:
    """将来の非同期実装用インターフェース"""
    
    async def execute_query_async(self, query: str) -> List[Dict]:
        """非同期クエリ実行"""
        
    async def get_version_async(self) -> PostgreSQLVersion:
        """非同期バージョン取得"""
```

### 11.2 互換性維持
- 既存の同期APIを維持
- 段階的な非同期移行対応
- パフォーマンス要件に応じた選択

## 12. 実装優先度

### Phase 1 (基本機能)
1. DatabaseConnector基本実装
2. 単純な接続管理
3. バージョン検出
4. 基本的なエラーハンドリング

### Phase 2 (接続プール)
1. ConnectionPool実装
2. 接続再利用機能
3. ヘルスチェック
4. メモリ管理

### Phase 3 (高度な機能)
1. DatabaseManager統合
2. 複数DB管理
3. 詳細な監視機能
4. パフォーマンス最適化

---

このアーキテクチャ設計に基づいて、PGSD-015の実装を進める。