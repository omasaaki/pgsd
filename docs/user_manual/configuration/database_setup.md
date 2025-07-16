# データベース設定

PGSDでデータベース接続を設定する詳細な方法について説明します。

## 🎯 この章で学ぶこと

- データベース接続の設定方法
- 認証方式とセキュリティ
- 接続プールと最適化
- トラブルシューティング

## 🔌 基本的な接続設定

### 最小構成の設定

```yaml
# config/basic-connection.yaml
databases:
  source:
    host: localhost
    port: 5432
    database: myapp_production
    user: app_user
    password: your_password
    schema: public
  
  target:
    host: localhost
    port: 5432
    database: myapp_staging
    user: app_user
    password: your_password
    schema: public
```

### 完全な接続設定

```yaml
# config/full-connection.yaml
databases:
  source:
    # 必須項目
    host: production.company.com
    port: 5432
    database: myapp_production
    user: readonly_user
    password: "${PROD_DB_PASSWORD}"
    
    # オプション項目
    schema: public                      # 対象スキーマ
    sslmode: require                    # SSL設定
    sslcert: certs/client-cert.pem      # クライアント証明書
    sslkey: certs/client-key.pem        # 秘密鍵
    sslrootcert: certs/ca-cert.pem      # CA証明書
    
    # 接続オプション
    connect_timeout: 30                 # 接続タイムアウト（秒）
    command_timeout: 300                # コマンドタイムアウト（秒）
    application_name: pgsd-comparison   # アプリケーション名
    
    # PostgreSQL固有オプション
    search_path: public,app_schema      # スキーマ検索パス
    timezone: UTC                       # タイムゾーン
    statement_timeout: 0                # ステートメントタイムアウト
```

## 🔐 認証方式

### 1. パスワード認証

#### 直接指定（非推奨）
```yaml
databases:
  source:
    host: localhost
    user: app_user
    password: "my_password"             # 非推奨：平文パスワード
```

#### 環境変数使用（推奨）
```yaml
databases:
  source:
    host: localhost
    user: app_user
    password: "${DB_PASSWORD}"          # 推奨：環境変数
```

#### .pgpassファイル使用
```bash
# ~/.pgpass ファイル（600パーミッション必須）
hostname:port:database:username:password
localhost:5432:*:app_user:my_password
production.company.com:5432:myapp:readonly_user:prod_password
```

```yaml
# 設定ファイルではパスワード省略
databases:
  source:
    host: localhost
    user: app_user
    # password不要（.pgpassから自動取得）
```

### 2. SSL証明書認証

```yaml
databases:
  source:
    host: secure-db.company.com
    port: 5432
    database: myapp
    user: cert_user
    
    # SSL設定
    sslmode: verify-full                # 最高レベルのSSL検証
    sslcert: /path/to/client-cert.pem   # クライアント証明書
    sslkey: /path/to/client-key.pem     # 秘密鍵
    sslrootcert: /path/to/ca-cert.pem   # CA証明書
```

### 3. IAM認証（AWS RDS）

```yaml
databases:
  source:
    host: mydb.cluster-xxx.us-west-2.rds.amazonaws.com
    port: 5432
    database: myapp
    user: db_user
    
    # IAM認証
    aws_iam_auth: true
    aws_region: us-west-2
    aws_profile: production             # オプション：AWSプロファイル
```

### 4. Azure AD認証

```yaml
databases:
  source:
    host: myserver.database.windows.net
    port: 5432
    database: myapp
    user: user@company.com
    
    # Azure AD認証
    azure_ad_auth: true
    azure_tenant_id: "${AZURE_TENANT_ID}"
    azure_client_id: "${AZURE_CLIENT_ID}"
    azure_client_secret: "${AZURE_CLIENT_SECRET}"
```

## 🌐 SSL/TLS設定

### SSL接続モード

```yaml
databases:
  source:
    host: secure-db.company.com
    sslmode: verify-full
    # SSL接続モードの選択肢：
    # disable     - SSL無効
    # allow       - SSL可能なら使用
    # prefer      - SSL優先（デフォルト）
    # require     - SSL必須
    # verify-ca   - SSL必須＋CA検証
    # verify-full - SSL必須＋CA検証＋ホスト名検証
```

### 証明書の管理

```bash
# 証明書ディレクトリの構成
certs/
├── ca-cert.pem          # CA証明書
├── client-cert.pem      # クライアント証明書
├── client-key.pem       # 秘密鍵
└── server-cert.pem      # サーバー証明書（検証用）
```

```yaml
# 設定での証明書指定
databases:
  source:
    host: secure-db.company.com
    sslmode: verify-full
    sslcert: "certs/client-cert.pem"
    sslkey: "certs/client-key.pem"
    sslrootcert: "certs/ca-cert.pem"
    
    # 証明書失効リスト
    sslcrl: "certs/root.crl"
```

## 🚀 接続最適化

### 接続プール設定

```yaml
connection_pool:
  # プール基本設定
  enabled: true
  min_connections: 2                    # 最小接続数
  max_connections: 10                   # 最大接続数
  
  # タイムアウト設定
  acquire_timeout: 30                   # 接続取得タイムアウト
  idle_timeout: 300                     # アイドルタイムアウト
  max_lifetime: 1800                    # 最大接続寿命
  
  # ヘルスチェック
  health_check_interval: 60             # ヘルスチェック間隔
  validation_query: "SELECT 1"          # 検証クエリ
```

### 接続パフォーマンス

```yaml
performance:
  # 接続最適化
  connection_optimization:
    persistent_connections: true        # 永続接続
    connection_caching: true            # 接続キャッシュ
    lazy_loading: true                  # 遅延ロード
  
  # クエリ最適化
  query_optimization:
    prepared_statements: true           # プリペアドステートメント
    statement_caching: true             # ステートメントキャッシュ
    fetch_size: 1000                    # フェッチサイズ
```

## 🗄️ 高可用性設定

### 読み取りレプリカ設定

```yaml
databases:
  source:
    # マスター接続（書き込み用・メタデータ取得）
    host: master.db.company.com
    port: 5432
    database: myapp
    user: app_user
    password: "${DB_PASSWORD}"
    
    # 読み取りレプリカ（データ読み取り）
    read_replicas:
      - host: replica1.db.company.com
        port: 5432
        weight: 1                       # 負荷分散の重み
      - host: replica2.db.company.com
        port: 5432
        weight: 1
    
    # フェイルオーバー設定
    failover:
      enabled: true
      timeout: 10                       # フェイルオーバータイムアウト
      retry_attempts: 3                 # 再試行回数
```

### クラスター設定

```yaml
databases:
  source:
    # クラスター設定
    cluster:
      nodes:
        - host: node1.cluster.company.com
          port: 5432
          priority: 1                   # 優先度（1が最高）
        - host: node2.cluster.company.com
          port: 5432
          priority: 2
        - host: node3.cluster.company.com
          port: 5432
          priority: 3
      
      # 負荷分散設定
      load_balancing:
        strategy: round_robin           # round_robin, least_connections, priority
        health_check: true
```

## 📊 監視とログ

### 接続監視

```yaml
monitoring:
  connection_monitoring:
    enabled: true
    metrics:
      - connection_count              # 接続数
      - connection_duration           # 接続時間
      - query_duration               # クエリ実行時間
      - error_count                  # エラー数
    
    # アラート設定
    alerts:
      connection_timeout:
        threshold: 30                 # 30秒以上の接続でアラート
        action: "log_warning"
      
      connection_failure:
        threshold: 3                  # 3回失敗でアラート
        action: "send_notification"
```

### デバッグログ

```yaml
logging:
  connection_debug:
    enabled: true
    log_connections: true             # 接続/切断ログ
    log_queries: false                # クエリログ（機密情報注意）
    log_parameters: false             # パラメータログ（機密情報注意）
    
    # ログレベル
    connection_level: INFO
    query_level: DEBUG
```

## 🔧 トラブルシューティング

### 接続診断

```bash
# 接続テストコマンド
pgsd test-connection --config config/my-config.yaml

# 詳細診断
pgsd diagnose-connection \
  --host production.company.com \
  --port 5432 \
  --database myapp \
  --user readonly_user
```

### よくある問題と解決法

#### 1. 接続タイムアウト

```yaml
# 設定での対処
databases:
  source:
    connect_timeout: 60               # タイムアウトを延長
    command_timeout: 600              # コマンドタイムアウトも延長
```

#### 2. SSL接続エラー

```bash
# SSL設定の確認
openssl s_client -connect your-db-host:5432 -starttls postgres

# 証明書の検証
openssl verify -CAfile ca-cert.pem client-cert.pem
```

#### 3. 認証エラー

```sql
-- PostgreSQLでの権限確認
SELECT 
  rolname,
  rolsuper,
  rolcreaterole,
  rolcreatedb,
  rolcanlogin
FROM pg_roles 
WHERE rolname = 'your_username';

-- スキーマアクセス権の確認
SELECT 
  schema_name,
  has_schema_privilege('your_username', schema_name, 'USAGE') as has_usage
FROM information_schema.schemata;
```

#### 4. パフォーマンス問題

```yaml
# 最適化設定
databases:
  source:
    # 接続数の調整
    max_connections: 20
    
    # クエリタイムアウトの設定
    statement_timeout: 300000         # 5分
    
    # 並列処理の制限
    max_parallel_workers: 4
```

## 🏢 企業環境での設定

### プロキシ経由接続

```yaml
databases:
  source:
    host: db-proxy.company.com
    port: 5432
    database: myapp
    user: app_user
    password: "${DB_PASSWORD}"
    
    # プロキシ設定
    proxy:
      type: http                      # http, socks5
      host: proxy.company.com
      port: 8080
      username: proxy_user            # プロキシ認証（オプション）
      password: "${PROXY_PASSWORD}"
```

### VPN接続

```yaml
databases:
  source:
    host: internal-db.company.local
    port: 5432
    database: myapp
    user: vpn_user
    password: "${VPN_DB_PASSWORD}"
    
    # VPN必須の設定
    vpn_required: true
    network_interface: tun0           # VPNインターフェース
    
    # VPN接続確認
    connectivity_check:
      enabled: true
      target_host: internal-db.company.local
      timeout: 10
```

### Active Directory統合

```yaml
databases:
  source:
    host: db.company.com
    port: 5432
    database: myapp
    
    # Active Directory認証
    authentication:
      type: active_directory
      domain: COMPANY
      username: "${AD_USERNAME}"
      password: "${AD_PASSWORD}"
      
      # Kerberos設定
      kerberos:
        realm: COMPANY.COM
        kdc: kdc.company.com
        keytab: /etc/krb5.keytab
```

## 📋 設定テンプレート

### 開発環境テンプレート

```yaml
# templates/development.yaml
databases:
  source:
    host: localhost
    port: 5432
    database: myapp_dev
    user: dev_user
    password: dev_password
    schema: public
    
    # 開発環境用設定
    sslmode: disable                  # 開発環境ではSSL無効
    connect_timeout: 10
    application_name: pgsd-dev
```

### ステージング環境テンプレート

```yaml
# templates/staging.yaml
databases:
  source:
    host: staging-db.company.com
    port: 5432
    database: myapp_staging
    user: staging_user
    password: "${STAGING_DB_PASSWORD}"
    schema: public
    
    # ステージング環境用設定
    sslmode: require
    connect_timeout: 30
    application_name: pgsd-staging
```

### 本番環境テンプレート

```yaml
# templates/production.yaml
databases:
  source:
    host: prod-primary.company.com
    port: 5432
    database: myapp_production
    user: readonly_user
    password: "${PROD_DB_PASSWORD}"
    schema: public
    
    # 本番環境用設定
    sslmode: verify-full
    sslcert: certs/prod-client-cert.pem
    sslkey: certs/prod-client-key.pem
    sslrootcert: certs/prod-ca-cert.pem
    connect_timeout: 60
    command_timeout: 1800
    application_name: pgsd-production
    
    # 読み取りレプリカ
    read_replicas:
      - host: prod-replica1.company.com
        port: 5432
      - host: prod-replica2.company.com
        port: 5432
```

## 🚀 次のステップ

データベース設定を理解したら：

1. **[出力設定](output_settings.md)** - レポート出力の詳細設定
2. **[パフォーマンス調整](../advanced/performance_tuning.md)** - 大規模データベースでの最適化
3. **[セキュリティ設定](../advanced/security.md)** - セキュリティ強化

## 📚 関連資料

- [PostgreSQL接続文字列リファレンス](https://www.postgresql.org/docs/current/libpq-connect.html)
- [SSL設定ガイド](../advanced/ssl_configuration.md)
- [トラブルシューティング](../troubleshooting/connection_issues.md)