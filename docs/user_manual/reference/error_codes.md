# エラーコード

PGSDで発生する全エラーコードの完全なリファレンスです。

## 🎯 この章で学ぶこと

- 全エラーコードの意味
- エラーの分類と重要度
- 対処方法と回避策
- プログラムでの処理方法

## 📋 エラーコードの体系

### コード体系

```
PGSD-[カテゴリ][番号]
```

**カテゴリ一覧**
- **E**: 接続エラー (Connection Errors)
- **C**: 設定エラー (Configuration Errors)
- **Q**: クエリエラー (Query Errors)
- **P**: 権限エラー (Permission Errors)
- **D**: データエラー (Data Errors)
- **R**: レポートエラー (Report Errors)
- **M**: メモリエラー (Memory Errors)
- **T**: タイムアウトエラー (Timeout Errors)
- **I**: 内部エラー (Internal Errors)
- **S**: システムエラー (System Errors)

### 重要度レベル

- **CRITICAL**: システムの動作に重大な影響
- **ERROR**: 処理が継続不可能
- **WARNING**: 処理は継続可能だが要注意
- **INFO**: 情報提供のみ

## 🔌 接続エラー (E001-E099)

### E001: CONNECTION_REFUSED
```
PGSD-E001: Connection refused - could not connect to server
```

**原因**
- PostgreSQLサーバーが起動していない
- ポート番号が間違っている
- ネットワーク接続の問題

**対処方法**
```bash
# サーバー状態確認
sudo systemctl status postgresql

# ポート確認
sudo netstat -tlnp | grep 5432

# 接続テスト
telnet hostname 5432
```

**コード例**
```python
try:
    result = client.compare(config)
except ConnectionError as e:
    if e.code == "E001":
        print("Database server is not running")
        # 自動再試行ロジック
```

### E002: AUTHENTICATION_FAILED
```
PGSD-E002: Authentication failed for user 'username'
```

**原因**
- パスワードが間違っている
- ユーザーが存在しない
- 認証方式の不一致

**対処方法**
```sql
-- パスワードリセット
ALTER USER username PASSWORD 'new_password';

-- ユーザー作成
CREATE USER username WITH PASSWORD 'password';
```

### E003: SSL_CONNECTION_ERROR
```
PGSD-E003: SSL connection error
```

**原因**
- SSL証明書の問題
- SSL設定の不整合
- サーバーのSSL無効化

**対処方法**
```yaml
# SSL設定の修正
databases:
  source:
    sslmode: "prefer"  # requireから変更
    # または証明書の指定
    sslcert: "/path/to/cert.pem"
    sslkey: "/path/to/key.pem"
```

### E004: HOST_NOT_FOUND
```
PGSD-E004: Host not found: hostname
```

**原因**
- DNS解決エラー
- ホスト名の間違い
- ネットワーク設定の問題

**対処方法**
```bash
# DNS解決確認
nslookup hostname

# IPアドレス直接指定
host: "192.168.1.100"
```

### E005: CONNECTION_TIMEOUT
```
PGSD-E005: Connection timeout after 30 seconds
```

**原因**
- ネットワーク遅延
- サーバー負荷
- ファイアウォールの設定

**対処方法**
```yaml
databases:
  source:
    connect_timeout: 60  # タイムアウト延長
```

## ⚙️ 設定エラー (C001-C099)

### C001: CONFIG_FILE_NOT_FOUND
```
PGSD-C001: Configuration file not found: config.yaml
```

**原因**
- 設定ファイルが存在しない
- パスが間違っている
- 権限不足

**対処方法**
```bash
# ファイル確認
ls -la config.yaml

# 権限修正
chmod 644 config.yaml
```

### C002: INVALID_YAML_SYNTAX
```
PGSD-C002: Invalid YAML syntax at line 15
```

**原因**
- YAML構文エラー
- インデントの問題
- 予約語の使用

**対処方法**
```bash
# YAML構文チェック
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# yamlintの使用
yamllint config.yaml
```

### C003: MISSING_REQUIRED_FIELD
```
PGSD-C003: Missing required field: databases.source.host
```

**原因**
- 必須フィールドの欠落
- 設定項目の名前間違い

**対処方法**
```yaml
databases:
  source:
    host: "localhost"  # 必須フィールドを追加
    database: "mydb"
```

### C004: INVALID_FIELD_VALUE
```
PGSD-C004: Invalid value for field 'port': must be integer
```

**原因**
- データ型の不一致
- 範囲外の値
- 無効な値

**対処方法**
```yaml
databases:
  source:
    port: 5432  # 文字列ではなく数値
```

### C005: ENVIRONMENT_VARIABLE_NOT_SET
```
PGSD-C005: Environment variable not set: DB_PASSWORD
```

**原因**
- 環境変数が設定されていない
- 変数名の間違い

**対処方法**
```bash
# 環境変数設定
export DB_PASSWORD="password"

# 設定確認
echo $DB_PASSWORD
```

## 🔍 クエリエラー (Q001-Q099)

### Q001: INVALID_SQL_SYNTAX
```
PGSD-Q001: Invalid SQL syntax in query
```

**原因**
- SQLクエリの構文エラー
- データベースバージョンの不一致

**対処方法**
- クエリの修正
- データベースバージョンの確認

### Q002: TABLE_NOT_FOUND
```
PGSD-Q002: Table 'table_name' not found
```

**原因**
- テーブルが存在しない
- スキーマの指定間違い
- 権限不足

**対処方法**
```sql
-- テーブル確認
SELECT * FROM information_schema.tables 
WHERE table_name = 'table_name';

-- スキーマ確認
SELECT schema_name FROM information_schema.schemata;
```

### Q003: COLUMN_NOT_FOUND
```
PGSD-Q003: Column 'column_name' not found in table 'table_name'
```

**原因**
- カラムが存在しない
- カラム名の間違い

**対処方法**
```sql
-- カラム確認
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'table_name';
```

### Q004: QUERY_EXECUTION_ERROR
```
PGSD-Q004: Query execution failed: error_details
```

**原因**
- クエリ実行時エラー
- データベースの整合性問題

**対処方法**
- エラー詳細の確認
- データベースの修復

### Q005: DEADLOCK_DETECTED
```
PGSD-Q005: Deadlock detected during query execution
```

**原因**
- 複数のトランザクション間でのデッドロック
- 同時実行の問題

**対処方法**
```yaml
database_settings:
  lock_timeout: 30000  # ロックタイムアウト設定
  retry_attempts: 3    # 自動再試行
```

## 🔐 権限エラー (P001-P099)

### P001: INSUFFICIENT_PRIVILEGES
```
PGSD-P001: Insufficient privileges for operation
```

**原因**
- 必要な権限が不足
- ロールが適切に設定されていない

**対処方法**
```sql
-- 権限確認
SELECT * FROM information_schema.role_table_grants 
WHERE grantee = 'username';

-- 権限付与
GRANT SELECT ON ALL TABLES IN SCHEMA public TO username;
```

### P002: SCHEMA_ACCESS_DENIED
```
PGSD-P002: Access denied to schema 'schema_name'
```

**原因**
- スキーマへのアクセス権限不足

**対処方法**
```sql
-- スキーマ権限付与
GRANT USAGE ON SCHEMA schema_name TO username;
```

### P003: TABLE_ACCESS_DENIED
```
PGSD-P003: Access denied to table 'table_name'
```

**原因**
- テーブルへのアクセス権限不足

**対処方法**
```sql
-- テーブル権限付与
GRANT SELECT ON table_name TO username;
```

### P004: FUNCTION_ACCESS_DENIED
```
PGSD-P004: Access denied to function 'function_name'
```

**原因**
- 関数への実行権限不足

**対処方法**
```sql
-- 関数権限付与
GRANT EXECUTE ON FUNCTION function_name TO username;
```

### P005: SYSTEM_CATALOG_ACCESS_DENIED
```
PGSD-P005: Access denied to system catalog
```

**原因**
- システムカタログへのアクセス権限不足

**対処方法**
```sql
-- システムカタログ権限付与
GRANT SELECT ON pg_catalog.pg_class TO username;
GRANT SELECT ON pg_catalog.pg_attribute TO username;
```

## 📊 データエラー (D001-D099)

### D001: INVALID_DATA_TYPE
```
PGSD-D001: Invalid data type in column 'column_name'
```

**原因**
- サポートされていないデータ型
- データ型の変換エラー

**対処方法**
- データ型の確認
- 変換ロジックの修正

### D002: DATA_TRUNCATED
```
PGSD-D002: Data truncated in column 'column_name'
```

**原因**
- データが制限を超えている
- 文字列の長さ制限

**対処方法**
- データの確認
- 制限値の調整

### D003: CONSTRAINT_VIOLATION
```
PGSD-D003: Constraint violation in table 'table_name'
```

**原因**
- 制約違反
- データの整合性問題

**対処方法**
- 制約の確認
- データの修正

### D004: ENCODING_ERROR
```
PGSD-D004: Character encoding error
```

**原因**
- 文字エンコーディングの問題
- 不正な文字

**対処方法**
```yaml
databases:
  source:
    client_encoding: "UTF8"
```

### D005: NULL_VALUE_ERROR
```
PGSD-D005: Unexpected null value in column 'column_name'
```

**原因**
- 予期しないNULL値
- NOT NULL制約の違反

**対処方法**
- データの確認
- 制約の見直し

## 📄 レポートエラー (R001-R099)

### R001: TEMPLATE_NOT_FOUND
```
PGSD-R001: Template file not found: template.html
```

**原因**
- テンプレートファイルが存在しない
- パスが間違っている

**対処方法**
```bash
# テンプレートファイル確認
ls -la templates/

# パス修正
template: "templates/custom.html"
```

### R002: TEMPLATE_RENDERING_ERROR
```
PGSD-R002: Template rendering failed at line 25
```

**原因**
- テンプレート構文エラー
- 未定義変数の使用

**対処方法**
```html
<!-- 変数の存在確認 -->
{% if variable is defined %}
  {{ variable }}
{% endif %}

<!-- デフォルト値の使用 -->
{{ variable|default('default_value') }}
```

### R003: REPORT_GENERATION_FAILED
```
PGSD-R003: Report generation failed: disk space
```

**原因**
- ディスク容量不足
- 権限不足

**対処方法**
```bash
# ディスク容量確認
df -h

# 権限確認
ls -la reports/
```

### R004: INVALID_OUTPUT_FORMAT
```
PGSD-R004: Invalid output format: unknown_format
```

**原因**
- サポートされていない出力形式
- 形式名の間違い

**対処方法**
```yaml
output:
  format: "html"  # html, markdown, json, xml
```

### R005: ASSET_FILE_NOT_FOUND
```
PGSD-R005: Asset file not found: styles.css
```

**原因**
- アセットファイルが存在しない
- パスが間違っている

**対処方法**
```bash
# アセットファイル確認
ls -la assets/

# パス修正
stylesheet: "assets/styles.css"
```

## 💾 メモリエラー (M001-M099)

### M001: MEMORY_LIMIT_EXCEEDED
```
PGSD-M001: Memory limit exceeded: 2.1GB > 2.0GB
```

**原因**
- メモリ使用量が制限を超過
- 大量のデータ処理

**対処方法**
```yaml
memory_management:
  max_memory_usage: "4GB"  # 制限値を増加
  streaming_mode: true     # ストリーミングモード有効
```

### M002: OUT_OF_MEMORY
```
PGSD-M002: Out of memory: unable to allocate 512MB
```

**原因**
- システムメモリ不足
- メモリリーク

**対処方法**
```bash
# メモリ使用量確認
free -h

# スワップ追加
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### M003: BUFFER_OVERFLOW
```
PGSD-M003: Buffer overflow detected
```

**原因**
- バッファサイズ不足
- 大量データの処理

**対処方法**
```yaml
performance:
  io_optimization:
    buffer_size: "128KB"  # バッファサイズ増加
```

### M004: MEMORY_FRAGMENTATION
```
PGSD-M004: Memory fragmentation detected
```

**原因**
- メモリの断片化
- 長時間の実行

**対処方法**
```yaml
memory_management:
  garbage_collection:
    enabled: true
    gc_threshold: 0.8
```

### M005: CACHE_OVERFLOW
```
PGSD-M005: Cache overflow: evicting entries
```

**原因**
- キャッシュサイズ不足
- 大量のデータ

**対処方法**
```yaml
performance:
  memory_management:
    cache_size: "500MB"  # キャッシュサイズ増加
```

## ⏰ タイムアウトエラー (T001-T099)

### T001: CONNECTION_TIMEOUT
```
PGSD-T001: Connection timeout after 30 seconds
```

**原因**
- ネットワーク遅延
- サーバー負荷

**対処方法**
```yaml
databases:
  source:
    connect_timeout: 60  # タイムアウト延長
```

### T002: QUERY_TIMEOUT
```
PGSD-T002: Query timeout after 60 seconds
```

**原因**
- クエリ実行時間が長い
- データベースの負荷

**対処方法**
```yaml
comparison:
  query_timeout: 300  # タイムアウト延長

# またはデータベース側の設定
database_settings:
  statement_timeout: 300000  # 5分
```

### T003: COMPARISON_TIMEOUT
```
PGSD-T003: Comparison timeout after 300 seconds
```

**原因**
- 比較処理時間が長い
- 大量のデータ

**対処方法**
```yaml
comparison:
  timeout: 1800  # 30分に延長

performance:
  parallel_processing:
    enabled: true
    max_workers: 8
```

### T004: REPORT_GENERATION_TIMEOUT
```
PGSD-T004: Report generation timeout after 120 seconds
```

**原因**
- レポート生成時間が長い
- 複雑なテンプレート

**対処方法**
```yaml
output:
  timeout: 300  # 5分に延長
```

### T005: LOCK_TIMEOUT
```
PGSD-T005: Lock timeout: could not obtain lock
```

**原因**
- データベースロックの競合
- 他のトランザクションの長時間実行

**対処方法**
```yaml
database_settings:
  lock_timeout: 60000  # 1分に延長
```

## 🔧 内部エラー (I001-I099)

### I001: INTERNAL_ERROR
```
PGSD-I001: Internal error: unexpected exception
```

**原因**
- プログラムの内部エラー
- 予期しない例外

**対処方法**
- バグレポートの作成
- ログの確認

### I002: ASSERTION_FAILED
```
PGSD-I002: Assertion failed: condition not met
```

**原因**
- 内部状態の不整合
- プログラムのバグ

**対処方法**
- デバッグログの確認
- 開発者への報告

### I003: CORRUPTED_DATA
```
PGSD-I003: Corrupted data structure detected
```

**原因**
- データ構造の破損
- メモリ破損

**対処方法**
- プロセスの再起動
- データの再取得

### I004: INVALID_STATE
```
PGSD-I004: Invalid internal state
```

**原因**
- 不正な内部状態
- 状態遷移エラー

**対処方法**
- 処理の再開
- 初期化の実行

### I005: RESOURCE_LEAK
```
PGSD-I005: Resource leak detected
```

**原因**
- リソースの解放漏れ
- メモリリーク

**対処方法**
- プロセスの再起動
- 開発者への報告

## 🖥️ システムエラー (S001-S099)

### S001: DISK_SPACE_INSUFFICIENT
```
PGSD-S001: Insufficient disk space: 1.2GB < 2.0GB
```

**原因**
- ディスク容量不足
- 一時ファイルの蓄積

**対処方法**
```bash
# ディスク容量確認
df -h

# 一時ファイル削除
find /tmp -name "pgsd_*" -mtime +1 -delete
```

### S002: FILE_PERMISSION_DENIED
```
PGSD-S002: Permission denied: unable to write to file
```

**原因**
- ファイル権限不足
- ディレクトリの権限問題

**対処方法**
```bash
# 権限確認
ls -la filename

# 権限修正
chmod 644 filename
```

### S003: DEPENDENCY_MISSING
```
PGSD-S003: Required dependency not found: libpq
```

**原因**
- 必要なライブラリが不足
- 依存関係の問題

**対処方法**
```bash
# 依存関係確認
ldd $(which pgsd)

# パッケージ再インストール
sudo apt-get install postgresql-client-dev
```

### S004: PROCESS_KILLED
```
PGSD-S004: Process killed by signal 9 (SIGKILL)
```

**原因**
- OOM Killerによる強制終了
- システムリソース不足

**対処方法**
```bash
# システムログ確認
dmesg | grep -i "killed process"

# メモリ使用量確認
free -h
```

### S005: NETWORK_ERROR
```
PGSD-S005: Network error: connection reset
```

**原因**
- ネットワーク接続の問題
- ファイアウォール設定

**対処方法**
```bash
# ネットワーク確認
ping hostname

# ファイアウォール確認
sudo ufw status
```

## 🔍 エラーハンドリング

### Python SDKでのエラーハンドリング

```python
from pgsd_sdk import PGSDClient, PGSDError

client = PGSDClient(api_key="your_api_key")

try:
    result = client.compare(config)
except PGSDError as e:
    error_handlers = {
        "E001": handle_connection_refused,
        "E002": handle_authentication_failed,
        "C001": handle_config_not_found,
        "M001": handle_memory_exceeded,
        "T001": handle_timeout,
    }
    
    handler = error_handlers.get(e.code)
    if handler:
        handler(e)
    else:
        print(f"Unknown error: {e.code} - {e.message}")

def handle_connection_refused(error):
    print("Database connection failed. Checking server status...")
    # 再試行ロジック
    
def handle_memory_exceeded(error):
    print("Memory limit exceeded. Enabling streaming mode...")
    # ストリーミングモードで再実行
```

### CLI でのエラーハンドリング

```bash
#!/bin/bash
# エラーコードに応じた処理

pgsd compare --config config.yaml
exit_code=$?

case $exit_code in
    0)
        echo "Comparison completed successfully"
        ;;
    1)
        echo "General error occurred"
        ;;
    2)
        echo "Configuration error - check config file"
        ;;
    3)
        echo "Connection error - check database settings"
        ;;
    4)
        echo "Permission error - check user privileges"
        ;;
    *)
        echo "Unknown error with exit code: $exit_code"
        ;;
esac
```

## 📊 エラー統計

### よく発生するエラーTop 10

1. **E002**: Authentication failed (35%)
2. **P001**: Insufficient privileges (18%)
3. **C003**: Missing required field (12%)
4. **T002**: Query timeout (8%)
5. **E001**: Connection refused (7%)
6. **R001**: Template not found (5%)
7. **M001**: Memory limit exceeded (4%)
8. **Q002**: Table not found (4%)
9. **C002**: Invalid YAML syntax (3%)
10. **S001**: Disk space insufficient (4%)

### エラー発生傾向

- **新規導入時**: 設定エラー（C001-C099）が多発
- **運用時**: 接続エラー（E001-E099）とタイムアウト（T001-T099）が主
- **大規模環境**: メモリエラー（M001-M099）が増加

## 🛠️ 予防策

### 1. 設定ファイルの検証

```bash
# 定期的な設定検証
pgsd validate-config --strict config/production.yaml
```

### 2. 接続の監視

```yaml
# 接続監視設定
monitoring:
  connection_health:
    enabled: true
    check_interval: 60
    timeout: 10
```

### 3. リソース監視

```bash
# システムリソース監視
watch -n 1 'free -h; df -h'
```

### 4. ログ監視

```bash
# エラーログの監視
tail -f /var/log/pgsd/error.log | grep -E "(ERROR|CRITICAL)"
```

## 🚀 次のステップ

エラーコードを理解したら：

1. **[デバッグガイド](debugging_guide.md)** - 詳細なデバッグ方法
2. **[ログ分析](log_analysis.md)** - ログの分析方法
3. **[パフォーマンス監視](performance_monitoring.md)** - 監視とアラート

## 📚 関連資料

- [エラーメッセージ](../troubleshooting/error_messages.md)
- [よくある問題](../troubleshooting/common_issues.md)
- [サポート情報](support_information.md)