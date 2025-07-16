# よくある問題

PGSDの使用中に発生する一般的な問題とその解決方法について説明します。

## 🎯 この章で学ぶこと

- 頻繁に発生する問題の特定と解決
- エラーメッセージの読み方
- 問題の診断手順
- 予防策と対応策

## 🔌 接続関連の問題

### 1. データベースに接続できない

#### 症状
```
Error: could not connect to server: Connection refused
  Is the server running on host "localhost" and accepting
  TCP/IP connections on port 5432?
```

#### 原因と解決策

**原因1: PostgreSQLサービスが起動していない**
```bash
# サービス状態の確認
sudo systemctl status postgresql

# サービスの起動
sudo systemctl start postgresql

# 自動起動の設定
sudo systemctl enable postgresql
```

**原因2: ポート番号の間違い**
```bash
# PostgreSQLのポート番号確認
sudo -u postgres psql -c "SHOW port;"

# 設定ファイルでの確認
grep "port" /etc/postgresql/*/main/postgresql.conf
```

**原因3: ファイアウォールの設定**
```bash
# ファイアウォールの状態確認
sudo ufw status

# ポートの開放
sudo ufw allow 5432/tcp

# 特定のIPからのみ許可
sudo ufw allow from 192.168.1.0/24 to any port 5432
```

**原因4: pg_hba.confの設定**
```bash
# pg_hba.confの場所を確認
sudo -u postgres psql -c "SHOW hba_file;"

# 設定例
echo "host    all             all             0.0.0.0/0               md5" >> /etc/postgresql/*/main/pg_hba.conf

# 設定再読み込み
sudo systemctl reload postgresql
```

### 2. 認証エラー

#### 症状
```
Error: FATAL: password authentication failed for user "myuser"
```

#### 解決策

**パスワード認証の確認**
```bash
# ユーザーの存在確認
sudo -u postgres psql -c "SELECT rolname FROM pg_roles WHERE rolname = 'myuser';"

# パスワードの設定
sudo -u postgres psql -c "ALTER USER myuser PASSWORD 'newpassword';"
```

**認証方法の確認**
```bash
# pg_hba.confの確認
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v "^#" | grep -v "^$"

# 接続テスト
psql -h localhost -U myuser -d testdb -c "SELECT 1;"
```

### 3. SSL接続エラー

#### 症状
```
Error: SSL connection has been closed unexpectedly
```

#### 解決策

**SSL設定の確認**
```bash
# SSL有効化の確認
sudo -u postgres psql -c "SHOW ssl;"

# 証明書の存在確認
sudo ls -la /etc/ssl/certs/ssl-cert-snakeoil.pem
sudo ls -la /etc/ssl/private/ssl-cert-snakeoil.key
```

**PGSDでのSSL設定**
```yaml
# config/ssl-config.yaml
databases:
  source:
    host: localhost
    sslmode: require  # または prefer, allow
    sslcert: /path/to/client.crt
    sslkey: /path/to/client.key
    sslrootcert: /path/to/ca.crt
```

## 📊 比較実行の問題

### 1. 比較処理が非常に遅い

#### 症状
- 比較処理が数時間経っても完了しない
- メモリ使用量が異常に高い
- CPUが100%の状態が続く

#### 解決策

**並列処理の調整**
```yaml
# config/performance.yaml
performance:
  parallel_processing:
    enabled: true
    max_workers: 4        # CPUコア数に応じて調整
    chunk_size: 1000      # データ量に応じて調整
  
  memory_management:
    max_memory_usage: "2GB"
    streaming_mode: true
```

**対象の制限**
```bash
# 特定のテーブルのみ比較
pgsd compare \
  --config config/default.yaml \
  --tables "users,orders,products" \
  --output reports/limited

# 特定のスキーマのみ比較
pgsd compare \
  --config config/default.yaml \
  --schema "public" \
  --output reports/schema-only
```

**インデックスの最適化**
```sql
-- 必要な統計情報の更新
ANALYZE;

-- 必要なインデックスの作成
CREATE INDEX CONCURRENTLY idx_table_column ON table_name(column_name);
```

### 2. メモリ不足エラー

#### 症状
```
Error: MemoryError: Unable to allocate memory
```

#### 解決策

**メモリ制限の設定**
```yaml
# config/memory-config.yaml
memory_management:
  total_memory_limit: "1GB"
  per_process_limit: "512MB"
  streaming_mode: true
  
  # バッチサイズの調整
  batch_processing:
    enabled: true
    batch_size: 500
    max_batch_memory: "100MB"
```

**システムメモリの確認**
```bash
# メモリ使用量の確認
free -h

# スワップの確認
swapon --show

# 必要に応じてスワップ追加
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. 権限エラー

#### 症状
```
Error: permission denied for relation "pg_class"
Error: permission denied for schema "information_schema"
```

#### 解決策

**必要な権限の付与**
```sql
-- 基本的な権限
GRANT USAGE ON SCHEMA public TO pgsd_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pgsd_user;

-- システムカタログへの権限
GRANT SELECT ON pg_catalog.pg_class TO pgsd_user;
GRANT SELECT ON pg_catalog.pg_attribute TO pgsd_user;
GRANT SELECT ON pg_catalog.pg_constraint TO pgsd_user;
GRANT SELECT ON pg_catalog.pg_index TO pgsd_user;

-- 情報スキーマへの権限
GRANT SELECT ON information_schema.tables TO pgsd_user;
GRANT SELECT ON information_schema.columns TO pgsd_user;
```

**読み取り専用ユーザーの作成**
```sql
-- 専用ユーザーの作成
CREATE USER pgsd_readonly WITH PASSWORD 'secure_password';

-- 読み取り権限の付与
GRANT CONNECT ON DATABASE mydb TO pgsd_readonly;
GRANT USAGE ON SCHEMA public TO pgsd_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pgsd_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO pgsd_readonly;

-- 将来のオブジェクトにも権限を付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO pgsd_readonly;
```

## 📄 レポート生成の問題

### 1. HTMLレポートが表示されない

#### 症状
- ブラウザでHTMLファイルを開いても空白
- CSSやJavaScriptが読み込まれない
- 文字化けが発生

#### 解決策

**ファイル権限の確認**
```bash
# レポートファイルの権限確認
ls -la reports/

# 権限の修正
chmod 644 reports/*.html
chmod 755 reports/assets/
```

**文字エンコーディングの設定**
```yaml
# config/report-config.yaml
html_output:
  encoding: "UTF-8"
  include_meta_charset: true
  
  # ブラウザ互換性
  browser_compatibility:
    ie_support: false
    mobile_optimization: true
```

**アセットファイルの確認**
```bash
# CSSファイルの存在確認
ls -la reports/assets/

# 相対パスの確認
grep -r "assets/" reports/*.html
```

### 2. レポートサイズが大きすぎる

#### 症状
- HTMLファイルが数十MBになる
- ブラウザでの表示が遅い
- メール送信に失敗する

#### 解決策

**レポート内容の最適化**
```yaml
# config/report-optimization.yaml
html_output:
  # 同一項目の非表示
  show_identical: false
  
  # 詳細の折りたたみ
  collapse_details: true
  
  # 大きなテーブルの分割
  pagination:
    enabled: true
    items_per_page: 100
  
  # 画像の最適化
  image_optimization:
    enabled: true
    max_width: 800
    quality: 75
```

**圧縮の有効化**
```yaml
output:
  compression:
    enabled: true
    compression_level: 6
    formats: ["html", "json"]
```

### 3. レポートの配信エラー

#### 症状
```
Error: Failed to send email: Message too large
Error: SMTP connection failed
```

#### 解決策

**メール設定の確認**
```yaml
# config/email-config.yaml
email:
  smtp_host: "smtp.company.com"
  smtp_port: 587
  use_tls: true
  username: "sender@company.com"
  password: "${EMAIL_PASSWORD}"
  
  # サイズ制限
  max_attachment_size: "10MB"
  compress_attachments: true
```

**代替配信方法**
```bash
# ファイル共有サービスへのアップロード
aws s3 cp reports/latest.html s3://company-reports/

# レポートサーバーへのアップロード
scp reports/latest.html user@reports.company.com:/var/www/html/
```

## 🔧 設定関連の問題

### 1. 設定ファイルの読み込みエラー

#### 症状
```
Error: Configuration file not found: config/default.yaml
Error: Invalid YAML syntax at line 15
```

#### 解決策

**ファイルパスの確認**
```bash
# 設定ファイルの存在確認
ls -la config/

# 絶対パスでの指定
pgsd compare --config /full/path/to/config.yaml
```

**YAML構文の確認**
```bash
# YAML構文チェック
python -c "import yaml; yaml.safe_load(open('config/default.yaml'))"

# またはyamlintを使用
yamllint config/default.yaml
```

**設定ファイルの例**
```yaml
# config/example.yaml
databases:
  source:
    host: "localhost"
    port: 5432
    database: "mydb"
    user: "myuser"
    password: "mypassword"
    schema: "public"
  
  target:
    host: "localhost"
    port: 5432
    database: "mydb2"
    user: "myuser"
    password: "mypassword"
    schema: "public"

output:
  format: "html"
  directory: "./reports"
```

### 2. 環境変数の問題

#### 症状
```
Error: Environment variable 'DB_PASSWORD' not set
Error: Invalid database configuration
```

#### 解決策

**環境変数の設定**
```bash
# 環境変数の設定
export DB_PASSWORD="my_secret_password"
export PGSD_CONFIG_FILE="config/production.yaml"

# 永続的な設定
echo 'export DB_PASSWORD="my_secret_password"' >> ~/.bashrc
source ~/.bashrc
```

**設定ファイルでの環境変数使用**
```yaml
# config/with-env.yaml
databases:
  source:
    host: "${DB_HOST}"
    database: "${DB_NAME}"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
```

**環境変数の確認**
```bash
# 設定されている環境変数の確認
env | grep DB_
echo $DB_PASSWORD
```

## 🚨 実行時エラー

### 1. プロセスが予期せず終了する

#### 症状
```
Error: Process killed by signal 9 (SIGKILL)
Error: Segmentation fault
```

#### 解決策

**リソース制限の確認**
```bash
# システムリソースの確認
ulimit -a

# メモリ制限の調整
ulimit -m 2097152  # 2GB

# プロセス制限の調整
ulimit -u 4096
```

**ログの確認**
```bash
# システムログの確認
journalctl -u postgresql --since="1 hour ago"

# dmesgでカーネルメッセージ確認
dmesg | grep -i "killed process"
```

### 2. デッドロックエラー

#### 症状
```
Error: deadlock detected
Error: could not obtain lock on relation
```

#### 解決策

**トランザクションの最適化**
```yaml
# config/transaction-config.yaml
database_settings:
  transaction_isolation: "read_committed"
  statement_timeout: 300000  # 5分
  lock_timeout: 30000        # 30秒
  idle_in_transaction_session_timeout: 600000  # 10分
```

**接続の管理**
```yaml
connection_pool:
  max_connections: 5
  connection_timeout: 30
  retry_attempts: 3
  retry_delay: 5
```

### 3. 文字エンコーディングエラー

#### 症状
```
Error: UnicodeDecodeError: 'utf-8' codec can't decode byte
Error: character with byte sequence 0x... in encoding "UTF8"
```

#### 解決策

**データベースエンコーディングの確認**
```sql
-- エンコーディングの確認
SELECT datname, encoding FROM pg_database;

-- 現在のエンコーディング
SHOW client_encoding;
SHOW server_encoding;
```

**設定での文字エンコーディング指定**
```yaml
# config/encoding-config.yaml
databases:
  source:
    host: "localhost"
    database: "mydb"
    user: "myuser"
    password: "mypassword"
    client_encoding: "UTF8"
    
comparison:
  encoding: "UTF-8"
  handle_encoding_errors: true
```

## 🔍 診断手順

### 1. 基本的な診断

```bash
# 1. PGSDのバージョン確認
pgsd --version

# 2. システム情報の確認
uname -a
python3 --version
psql --version

# 3. 設定ファイルの確認
pgsd validate-config config/default.yaml

# 4. データベース接続テスト
pgsd test-connection --config config/default.yaml

# 5. 詳細ログでの実行
pgsd compare --config config/default.yaml --verbose --debug
```

### 2. ログ分析

```bash
# エラーログの確認
tail -f /var/log/pgsd/error.log

# 特定のエラーの検索
grep -n "ERROR" /var/log/pgsd/pgsd.log

# 実行時間の分析
grep "duration" /var/log/pgsd/pgsd.log | tail -10
```

### 3. パフォーマンス分析

```bash
# システムリソースの監視
top -p $(pgrep pgsd)

# メモリ使用量の監視
watch -n 1 'free -h'

# ディスク使用量の確認
df -h
du -sh reports/
```

## 💡 予防策

### 1. 定期的なメンテナンス

```bash
#!/bin/bash
# scripts/maintenance.sh

# 古いログの削除
find /var/log/pgsd -name "*.log" -mtime +30 -delete

# 一時ファイルの削除
rm -rf /tmp/pgsd_*

# 統計情報の更新
sudo -u postgres psql -c "ANALYZE;"

# 設定ファイルの検証
pgsd validate-config config/production.yaml
```

### 2. 監視の設定

```yaml
# config/monitoring.yaml
monitoring:
  health_checks:
    enabled: true
    interval: 300  # 5分毎
    
  alerts:
    connection_failures:
      threshold: 3
      action: "send_alert"
    
    slow_comparisons:
      threshold: 600  # 10分
      action: "log_warning"
    
    high_memory_usage:
      threshold: "80%"
      action: "send_alert"
```

### 3. バックアップとリストア

```bash
# 設定ファイルのバックアップ
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# レポートのバックアップ
rsync -av reports/ backup_server:/backups/pgsd/

# 設定の復元
tar -xzf config_backup_20250715.tar.gz
```

## 🆘 緊急時の対応

### 1. サービス停止時の対応

```bash
# プロセスの確認
ps aux | grep pgsd

# 強制終了
pkill -f pgsd

# サービスの再起動
systemctl restart pgsd

# ログの確認
journalctl -u pgsd --since="10 minutes ago"
```

### 2. データベースロック時の対応

```sql
-- 現在のロックの確認
SELECT * FROM pg_locks WHERE NOT granted;

-- 長時間実行中のクエリ
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC;

-- 必要に応じてクエリを終了
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345;
```

### 3. 緊急連絡先

- **技術サポート**: support@pgsd.org
- **緊急時**: emergency@pgsd.org
- **ドキュメント**: https://docs.pgsd.org

## 🚀 次のステップ

よくある問題を理解したら：

1. **[エラーメッセージ](error_messages.md)** - 具体的なエラーメッセージと対処法
2. **[パフォーマンス問題](performance_issues.md)** - パフォーマンス関連の問題解決
3. **[設定問題](configuration_issues.md)** - 設定に関する問題の解決

## 📚 関連資料

- [ログ分析ガイド](../reference/log_analysis.md)
- [システム要件](../reference/system_requirements.md)
- [サポート情報](../reference/support_information.md)