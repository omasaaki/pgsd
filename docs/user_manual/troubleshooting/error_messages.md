# エラーメッセージ

PGSDで発生する具体的なエラーメッセージとその対処法について説明します。

## 🎯 この章で学ぶこと

- 各エラーメッセージの意味
- 具体的な解決手順
- エラーの予防方法
- デバッグの方法

## 🔌 接続エラー

### CONNECTION_REFUSED

**エラーメッセージ**
```
PGSD-E001: Connection refused - could not connect to server
Host: localhost, Port: 5432
Is the server running and accepting connections?
```

**原因と解決策**

1. **PostgreSQLサーバーが起動していない**
   ```bash
   # サーバー状態確認
   sudo systemctl status postgresql
   
   # サーバー起動
   sudo systemctl start postgresql
   ```

2. **ポート番号の不一致**
   ```bash
   # PostgreSQLの実際のポート確認
   sudo -u postgres psql -c "SHOW port;"
   
   # 設定ファイルの修正
   vim config/database.yaml
   ```

3. **ネットワークの問題**
   ```bash
   # ネットワーク接続確認
   telnet localhost 5432
   
   # DNS解決確認
   nslookup your-db-host.com
   ```

### AUTHENTICATION_FAILED

**エラーメッセージ**
```
PGSD-E002: Authentication failed for user 'myuser'
Database: mydb
Password authentication failed
```

**原因と解決策**

1. **パスワードの間違い**
   ```bash
   # パスワードの再設定
   sudo -u postgres psql
   postgres=# ALTER USER myuser PASSWORD 'new_password';
   ```

2. **ユーザーが存在しない**
   ```sql
   -- ユーザーの作成
   CREATE USER myuser WITH PASSWORD 'password';
   GRANT CONNECT ON DATABASE mydb TO myuser;
   ```

3. **pg_hba.confの設定問題**
   ```bash
   # pg_hba.confの編集
   sudo vim /etc/postgresql/*/main/pg_hba.conf
   
   # 以下の行を追加
   host    mydb    myuser    0.0.0.0/0    md5
   
   # 設定再読み込み
   sudo systemctl reload postgresql
   ```

### SSL_CONNECTION_ERROR

**エラーメッセージ**
```
PGSD-E003: SSL connection error
SSL connection has been closed unexpectedly
Certificate verification failed
```

**原因と解決策**

1. **SSL証明書の問題**
   ```bash
   # 証明書の確認
   openssl s_client -connect your-db-host:5432 -starttls postgres
   
   # 証明書の更新
   sudo cp new-cert.pem /etc/ssl/certs/
   sudo systemctl restart postgresql
   ```

2. **SSL設定の不整合**
   ```yaml
   # config/ssl-config.yaml
   databases:
     source:
       sslmode: "require"      # allow, prefer, require, verify-ca, verify-full
       sslcert: "/path/to/client.crt"
       sslkey: "/path/to/client.key"
       sslrootcert: "/path/to/ca.crt"
   ```

## 📊 比較処理エラー

### SCHEMA_NOT_FOUND

**エラーメッセージ**
```
PGSD-E101: Schema 'public' not found in database 'mydb'
Available schemas: information_schema, pg_catalog
```

**原因と解決策**

1. **スキーマ名の確認**
   ```sql
   -- 利用可能なスキーマの確認
   SELECT schema_name FROM information_schema.schemata;
   ```

2. **権限の問題**
   ```sql
   -- スキーマへの権限付与
   GRANT USAGE ON SCHEMA public TO myuser;
   ```

3. **設定ファイルの修正**
   ```yaml
   databases:
     source:
       schema: "correct_schema_name"
   ```

### TABLE_ACCESS_DENIED

**エラーメッセージ**
```
PGSD-E102: Access denied to table 'users'
Permission denied for relation users
Required privilege: SELECT
```

**原因と解決策**

1. **テーブル権限の付与**
   ```sql
   -- 特定テーブルへの権限
   GRANT SELECT ON users TO myuser;
   
   -- 全テーブルへの権限
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO myuser;
   
   -- 将来のテーブルにも権限付与
   ALTER DEFAULT PRIVILEGES IN SCHEMA public 
   GRANT SELECT ON TABLES TO myuser;
   ```

2. **システムカタログへの権限**
   ```sql
   -- システムカタログへの権限
   GRANT SELECT ON pg_catalog.pg_class TO myuser;
   GRANT SELECT ON pg_catalog.pg_attribute TO myuser;
   GRANT SELECT ON pg_catalog.pg_constraint TO myuser;
   ```

### COMPARISON_TIMEOUT

**エラーメッセージ**
```
PGSD-E103: Comparison operation timed out
Timeout: 300 seconds
Consider increasing timeout or optimizing query performance
```

**原因と解決策**

1. **タイムアウト値の調整**
   ```yaml
   # config/timeout-config.yaml
   comparison:
     timeout: 1800  # 30分
     
   database_settings:
     statement_timeout: 600000  # 10分
     query_timeout: 300000      # 5分
   ```

2. **パフォーマンスの最適化**
   ```sql
   -- 統計情報の更新
   ANALYZE;
   
   -- 必要なインデックスの作成
   CREATE INDEX CONCURRENTLY idx_table_column ON table_name(column);
   ```

3. **並列処理の有効化**
   ```yaml
   performance:
     parallel_processing:
       enabled: true
       max_workers: 4
   ```

## 💾 メモリ・リソースエラー

### MEMORY_EXCEEDED

**エラーメッセージ**
```
PGSD-E201: Memory limit exceeded
Current usage: 2.5GB
Maximum allowed: 2.0GB
Consider reducing batch size or increasing memory limit
```

**原因と解決策**

1. **メモリ制限の調整**
   ```yaml
   # config/memory-config.yaml
   memory_management:
     total_memory_limit: "4GB"
     per_process_limit: "1GB"
     streaming_mode: true
   ```

2. **バッチサイズの調整**
   ```yaml
   batch_processing:
     batch_size: 500      # デフォルト1000から削減
     max_batch_memory: "100MB"
   ```

3. **システムメモリの増強**
   ```bash
   # スワップファイルの作成
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### DISK_SPACE_INSUFFICIENT

**エラーメッセージ**
```
PGSD-E202: Insufficient disk space
Available: 1.2GB
Required: 2.5GB
Path: /tmp/pgsd_temp
```

**原因と解決策**

1. **一時ディレクトリの変更**
   ```yaml
   # config/disk-config.yaml
   temp_directory: "/var/tmp/pgsd"  # より大きなディスクパーティション
   ```

2. **古いファイルの削除**
   ```bash
   # 古い一時ファイルの削除
   find /tmp -name "pgsd_*" -mtime +1 -delete
   
   # 古いレポートの削除
   find reports/ -name "*.html" -mtime +30 -delete
   ```

3. **ディスクスペースの確認**
   ```bash
   # ディスク使用量の確認
   df -h
   
   # 大きなファイルの検索
   find / -size +100M -type f 2>/dev/null
   ```

## 📄 レポート生成エラー

### TEMPLATE_NOT_FOUND

**エラーメッセージ**
```
PGSD-E301: Template file not found
Template: custom-template.html
Path: /path/to/templates/
```

**原因と解決策**

1. **テンプレートファイルの確認**
   ```bash
   # テンプレートファイルの存在確認
   ls -la templates/
   
   # 権限の確認
   ls -la templates/custom-template.html
   ```

2. **テンプレートパスの設定**
   ```yaml
   # config/template-config.yaml
   html_output:
     template: "templates/custom-template.html"
     template_directory: "/full/path/to/templates"
   ```

3. **デフォルトテンプレートの使用**
   ```yaml
   html_output:
     template: "default"  # 組み込みテンプレートを使用
   ```

### REPORT_GENERATION_FAILED

**エラーメッセージ**
```
PGSD-E302: Report generation failed
Format: HTML
Error: Template rendering error at line 45
Variable 'undefined_variable' not found
```

**原因と解決策**

1. **テンプレート変数の確認**
   ```html
   <!-- テンプレートの修正例 -->
   <!-- 間違い -->
   <h1>{{undefined_variable}}</h1>
   
   <!-- 正しい -->
   <h1>{{report_title|default('Schema Comparison Report')}}</h1>
   ```

2. **テンプレートの検証**
   ```bash
   # テンプレートの構文チェック
   pgsd validate-template templates/custom-template.html
   ```

3. **デバッグモードでの実行**
   ```bash
   # デバッグモードで詳細エラー確認
   pgsd compare --config config/default.yaml --debug --verbose
   ```

## ⚙️ 設定エラー

### CONFIG_FILE_INVALID

**エラーメッセージ**
```
PGSD-E401: Configuration file is invalid
File: config/default.yaml
Line: 15, Column: 3
Error: Invalid YAML syntax - unexpected character ':'
```

**原因と解決策**

1. **YAML構文の確認**
   ```bash
   # YAML構文チェック
   python -c "import yaml; yaml.safe_load(open('config/default.yaml'))"
   
   # yamlintを使用
   yamllint config/default.yaml
   ```

2. **よくある構文エラー**
   ```yaml
   # 間違い：インデントの問題
   databases:
   source:
     host: localhost
   
   # 正しい
   databases:
     source:
       host: localhost
   ```

3. **設定ファイルの検証**
   ```bash
   # PGSD設定の検証
   pgsd validate-config config/default.yaml
   ```

### ENVIRONMENT_VARIABLE_MISSING

**エラーメッセージ**
```
PGSD-E402: Environment variable not set
Variable: DB_PASSWORD
Referenced in: config/production.yaml line 8
```

**原因と解決策**

1. **環境変数の設定**
   ```bash
   # 環境変数の設定
   export DB_PASSWORD="your_password"
   
   # 永続的な設定
   echo 'export DB_PASSWORD="your_password"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **設定ファイルの修正**
   ```yaml
   # デフォルト値の設定
   databases:
     source:
       password: "${DB_PASSWORD:-default_password}"
   ```

3. **環境変数の確認**
   ```bash
   # 設定済み環境変数の確認
   env | grep DB_
   echo $DB_PASSWORD
   ```

## 🔄 実行時エラー

### PROCESS_INTERRUPTED

**エラーメッセージ**
```
PGSD-E501: Process interrupted by signal
Signal: SIGTERM (15)
Current operation: Schema comparison
Progress: 75% completed
```

**原因と解決策**

1. **プロセスの再開**
   ```bash
   # 途中から再開（サポートされている場合）
   pgsd resume --comparison-id abc123
   
   # 完全な再実行
   pgsd compare --config config/default.yaml
   ```

2. **リソース制限の確認**
   ```bash
   # システムリソース制限の確認
   ulimit -a
   
   # メモリ制限の調整
   ulimit -v 4194304  # 4GB
   ```

3. **タイムアウトの調整**
   ```yaml
   execution:
     max_execution_time: 3600  # 1時間
     checkpoint_interval: 300  # 5分毎にチェックポイント
   ```

### DEADLOCK_DETECTED

**エラーメッセージ**
```
PGSD-E502: Database deadlock detected
Transaction aborted
Retry attempt: 2/3
```

**原因と解決策**

1. **自動リトライの設定**
   ```yaml
   # config/retry-config.yaml
   database_settings:
     retry_attempts: 5
     retry_delay: 10
     backoff_factor: 2
   ```

2. **トランザクション分離レベルの調整**
   ```yaml
   database_settings:
     isolation_level: "READ_COMMITTED"
     lock_timeout: 30000
   ```

3. **接続プールの調整**
   ```yaml
   connection_pool:
     max_connections: 3  # 小さめに設定
     connection_timeout: 60
   ```

## 🚨 致命的エラー

### SYSTEM_CORRUPTION

**エラーメッセージ**
```
PGSD-E901: System corruption detected
Internal state inconsistent
Please report this issue with debug logs
```

**原因と解決策**

1. **即座に実行を停止**
   ```bash
   # 実行中のプロセスを停止
   pkill -f pgsd
   ```

2. **ログの保存**
   ```bash
   # ログを保存
   cp /var/log/pgsd/debug.log /tmp/pgsd_error_$(date +%Y%m%d_%H%M%S).log
   ```

3. **サポートへの連絡**
   ```bash
   # バグレポートの作成
   pgsd create-bug-report --output bug_report.zip
   ```

### CRITICAL_DEPENDENCY_MISSING

**エラーメッセージ**
```
PGSD-E902: Critical dependency missing
Missing: libpq.so.5
This indicates a broken installation
```

**原因と解決策**

1. **依存関係の確認**
   ```bash
   # 依存関係の確認
   ldd $(which pgsd)
   
   # 必要なライブラリの確認
   ldconfig -p | grep libpq
   ```

2. **再インストール**
   ```bash
   # PGSDの再インストール
   pip uninstall pgsd
   pip install --upgrade pgsd
   
   # またはパッケージマネージャーで
   sudo apt-get install --reinstall postgresql-client
   ```

## 🔍 デバッグのヒント

### 1. 詳細ログの有効化

```yaml
# config/debug-config.yaml
logging:
  level: DEBUG
  console: true
  file: /var/log/pgsd/debug.log
  
  # 詳細なログ設定
  modules:
    connection: DEBUG
    comparison: DEBUG
    report: INFO
```

### 2. エラー再現の方法

```bash
# 最小限の設定で再現
pgsd compare \
  --source-host localhost \
  --source-db testdb \
  --target-host localhost \
  --target-db testdb2 \
  --debug \
  --verbose

# 特定のテーブルのみで再現
pgsd compare \
  --config config/minimal.yaml \
  --tables "problem_table" \
  --debug
```

### 3. システム情報の収集

```bash
# システム情報の収集
pgsd system-info --output system_info.json

# 環境情報の確認
pgsd env-check --verbose
```

## 💡 予防策

### 1. 設定ファイルの検証

```bash
# 定期的な設定検証
pgsd validate-config config/production.yaml

# 構文チェック
yamllint config/*.yaml
```

### 2. 依存関係の管理

```bash
# 依存関係の確認
pip list | grep pgsd
pip show pgsd

# 仮想環境での管理
python -m venv pgsd_env
source pgsd_env/bin/activate
pip install pgsd
```

### 3. 監視とアラート

```yaml
# config/monitoring.yaml
monitoring:
  health_checks:
    enabled: true
    interval: 60
    
  alerts:
    connection_errors:
      threshold: 3
      window: 300
      action: "send_alert"
```

## 🆘 緊急時の対応

### 1. エラー発生時の初期対応

```bash
# 1. 現在の状況確認
ps aux | grep pgsd
netstat -tlnp | grep 5432

# 2. ログの確認
tail -100 /var/log/pgsd/error.log

# 3. システムリソースの確認
free -h
df -h
```

### 2. 復旧手順

```bash
# 1. プロセスの停止
pkill -f pgsd

# 2. 一時ファイルの削除
rm -rf /tmp/pgsd_*

# 3. データベース接続の確認
psql -h localhost -U postgres -c "SELECT 1;"

# 4. 設定の検証
pgsd validate-config config/production.yaml

# 5. 再実行
pgsd compare --config config/production.yaml
```

## 📞 サポート情報

### 1. 技術サポート

- **メール**: support@pgsd.org
- **GitHub Issues**: https://github.com/pgsd/pgsd/issues
- **ドキュメント**: https://docs.pgsd.org

### 2. バグレポート

```bash
# バグレポートの作成
pgsd create-bug-report \
  --include-logs \
  --include-config \
  --output bug_report.zip
```

### 3. 緊急時の連絡先

- **緊急サポート**: emergency@pgsd.org
- **電話**: +1-800-PGSD-HELP (平日9-17時)

## 🚀 次のステップ

エラーメッセージを理解したら：

1. **[パフォーマンス問題](performance_issues.md)** - パフォーマンス関連のエラー
2. **[設定問題](configuration_issues.md)** - 設定関連のエラー
3. **[FAQ](../reference/faq.md)** - よくある質問と回答

## 📚 関連資料

- [ログ分析ガイド](../reference/log_analysis.md)
- [エラーコード一覧](../reference/error_codes.md)
- [デバッグガイド](../reference/debugging_guide.md)