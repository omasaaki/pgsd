# 設定ファイル

PGSDの設定ファイルの詳細な使用方法とカスタマイズオプションについて説明します。

## 🎯 この章で学ぶこと

- 設定ファイルの基本構造
- 環境別設定の管理
- 高度な設定オプション
- 設定ファイルのベストプラクティス

## 📋 設定ファイルの基本

### 基本構造

PGSDの設定ファイルはYAML形式で記述します：

```yaml
# config/example.yaml
# データベース接続設定
databases:
  source:
    host: localhost
    port: 5432
    database: myapp_production
    user: app_user
    password: "${SOURCE_DB_PASSWORD}"
    schema: public
  
  target:
    host: localhost
    port: 5432
    database: myapp_staging
    user: app_user
    password: "${TARGET_DB_PASSWORD}"
    schema: public

# 出力設定
output:
  format: html
  directory: ./reports
  filename_template: "schema_diff_{timestamp}"

# ログ設定
logging:
  level: INFO
  console: true
  file: pgsd.log
```

### 設定ファイルの使用

```bash
# 設定ファイルを指定して実行
pgsd compare --config config/my-config.yaml

# 環境変数で設定ファイルを指定
export PGSD_CONFIG_FILE="config/my-config.yaml"
pgsd compare
```

## 🗂️ 設定項目の詳細

### データベース接続設定

```yaml
databases:
  source:
    # 必須項目
    host: "production.company.com"
    port: 5432
    database: "myapp_production"
    user: "readonly_user"
    password: "${PROD_DB_PASSWORD}"
    
    # オプション項目
    schema: "public"                    # 対象スキーマ
    sslmode: "require"                  # SSL設定
    connect_timeout: 30                 # 接続タイムアウト
    application_name: "pgsd-comparison" # アプリケーション名
    
  target:
    host: "staging.company.com"
    port: 5432
    database: "myapp_staging"
    user: "readonly_user"
    password: "${STAGING_DB_PASSWORD}"
    schema: "public"
```

### SSL設定の詳細

```yaml
databases:
  source:
    host: "secure-db.company.com"
    port: 5432
    database: "myapp"
    user: "app_user"
    password: "${DB_PASSWORD}"
    
    # SSL設定
    sslmode: "require"           # disable, allow, prefer, require, verify-ca, verify-full
    sslcert: "client-cert.pem"   # クライアント証明書
    sslkey: "client-key.pem"     # クライアント秘密鍵
    sslrootcert: "ca-cert.pem"   # CA証明書
```

### 出力設定

```yaml
output:
  # 基本設定
  format: html                          # html, markdown, json, xml
  directory: "./reports"                # 出力ディレクトリ
  filename_template: "diff_{timestamp}" # ファイル名テンプレート
  
  # 高度な設定
  overwrite_existing: false             # 既存ファイルの上書き
  create_subdirectories: true           # サブディレクトリの自動作成
  compress_output: false                # 出力の圧縮
  
  # ファイル名テンプレート変数
  # {timestamp} - タイムスタンプ
  # {source_db} - ソースDB名
  # {target_db} - ターゲットDB名
  # {format} - 出力形式
```

### 比較設定

```yaml
comparison:
  # 基本比較設定
  case_sensitive: true                  # 大文字小文字の区別
  include_comments: true                # コメントの比較
  include_permissions: false            # 権限の比較
  include_sequences: true               # シーケンスの比較
  include_views: true                   # ビューの比較
  
  # 除外設定
  exclude_tables:
    - "temp_*"                          # パターンマッチで除外
    - "log_archive"                     # 特定テーブル名で除外
  
  exclude_columns:
    - "created_at"                      # 全テーブルの該当カラム
    - "users.last_updated"              # 特定テーブルのカラム
  
  exclude_schemas:
    - "information_schema"
    - "pg_catalog"
  
  # データ型の互換性
  type_compatibility:
    mode: "strict"                      # strict, loose, permissive
    custom_rules:
      varchar:
        compatible_with: ["text", "char"]
        size_tolerance: 10              # サイズ差の許容範囲（%）
```

### フィルタリング設定

```yaml
filters:
  # 日付範囲フィルタ
  date_range:
    start: "2025-01-01"
    end: "2025-07-15"
    column: "created_at"                # 基準カラム
  
  # テーブルサイズフィルタ
  table_size:
    min_rows: 0
    max_rows: 1000000
  
  # 更新頻度フィルタ
  activity_level:
    exclude_static_tables: true        # 更新されないテーブルを除外
    min_modification_date: "2025-01-01"
```

## 🌍 環境別設定管理

### 環境固有の設定ファイル

```yaml
# config/base.yaml - 共通設定
output:
  format: html
  directory: "./reports"

logging:
  level: INFO
  console: true

comparison:
  case_sensitive: true
  include_comments: true
```

```yaml
# config/production.yaml - 本番環境
extends: "base.yaml"

databases:
  source:
    host: "prod-primary.company.com"
    database: "myapp_production"
    user: "readonly_user"
    password: "${PROD_DB_PASSWORD}"
  target:
    host: "prod-replica.company.com"
    database: "myapp_production"
    user: "readonly_user"
    password: "${PROD_REPLICA_PASSWORD}"

logging:
  level: WARNING                        # 本番では警告以上のみ
  file: "/var/log/pgsd/production.log"
```

```yaml
# config/development.yaml - 開発環境
extends: "base.yaml"

databases:
  source:
    host: "localhost"
    database: "myapp_development"
    user: "dev_user"
    password: "dev_password"
  target:
    host: "localhost"
    database: "myapp_test"
    user: "dev_user"
    password: "dev_password"

logging:
  level: DEBUG                          # 開発では詳細ログ
  console: true

comparison:
  include_permissions: true             # 開発では権限も比較
```

### プロファイル機能

```yaml
# config/profiles.yaml
profiles:
  daily-check:
    databases:
      source:
        host: "production.company.com"
        database: "myapp"
      target:
        host: "staging.company.com"
        database: "myapp"
    output:
      format: html
      directory: "./daily-reports"
  
  release-validation:
    databases:
      source:
        host: "staging.company.com"
        database: "myapp"
      target:
        host: "production.company.com"
        database: "myapp"
    output:
      format: ["html", "json"]
      directory: "./release-reports"
    comparison:
      include_permissions: true
```

```bash
# プロファイルを使用した実行
pgsd compare --profile daily-check
pgsd compare --profile release-validation
```

## 🔐 認証情報の管理

### 環境変数の活用

```yaml
# config/secure.yaml
databases:
  source:
    host: "${SOURCE_DB_HOST}"
    port: "${SOURCE_DB_PORT:-5432}"     # デフォルト値付き
    database: "${SOURCE_DB_NAME}"
    user: "${SOURCE_DB_USER}"
    password: "${SOURCE_DB_PASSWORD}"
  
  target:
    host: "${TARGET_DB_HOST}"
    database: "${TARGET_DB_NAME}"
    user: "${TARGET_DB_USER}"
    password: "${TARGET_DB_PASSWORD}"
```

```bash
# 環境変数ファイル .env
SOURCE_DB_HOST=production.company.com
SOURCE_DB_NAME=myapp_production
SOURCE_DB_USER=readonly_user
SOURCE_DB_PASSWORD=secure_password123

TARGET_DB_HOST=staging.company.com
TARGET_DB_NAME=myapp_staging
TARGET_DB_USER=readonly_user
TARGET_DB_PASSWORD=staging_password456
```

### AWS Secrets Manager統合

```yaml
# config/aws-secrets.yaml
databases:
  source:
    host: "production.rds.amazonaws.com"
    database: "myapp"
    # AWS Secrets Managerから認証情報を取得
    aws_secret:
      region: "us-west-2"
      secret_name: "rds/production/credentials"
      username_key: "username"
      password_key: "password"
  
  target:
    host: "staging.rds.amazonaws.com"
    database: "myapp"
    aws_secret:
      region: "us-west-2"
      secret_name: "rds/staging/credentials"
```

### Azure Key Vault統合

```yaml
# config/azure-keyvault.yaml
databases:
  source:
    host: "prod-db.database.windows.net"
    database: "myapp"
    azure_keyvault:
      vault_url: "https://myvault.vault.azure.net/"
      client_id: "${AZURE_CLIENT_ID}"
      client_secret: "${AZURE_CLIENT_SECRET}"
      tenant_id: "${AZURE_TENANT_ID}"
      username_secret: "db-username"
      password_secret: "db-password"
```

## 📝 ログ設定の詳細

### 基本ログ設定

```yaml
logging:
  # ログレベル
  level: INFO                           # DEBUG, INFO, WARNING, ERROR, CRITICAL
  
  # 出力先
  console: true                         # コンソール出力
  file: "pgsd.log"                      # ファイル出力
  
  # ログフォーマット
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
  
  # ログローテーション
  rotation:
    enabled: true
    max_size: "10MB"                    # ファイルサイズ上限
    backup_count: 5                     # 保持するバックアップ数
```

### 構造化ログ

```yaml
logging:
  format: "json"                        # json, text
  structured_fields:
    - timestamp
    - level
    - message
    - source_db
    - target_db
    - operation
    - duration
  
  # ログの送信
  remote_logging:
    enabled: true
    endpoint: "https://logs.company.com/api/ingest"
    api_key: "${LOGGING_API_KEY}"
```

## ⚡ パフォーマンス設定

### 並列処理設定

```yaml
performance:
  # 並列処理
  parallel_processing:
    enabled: true
    max_workers: 4                      # 並列ワーカー数
    chunk_size: 1000                    # 処理チャンクサイズ
  
  # メモリ管理
  memory:
    max_usage: "2GB"                    # 最大メモリ使用量
    streaming_mode: true                # ストリーミングモード
    cache_size: "100MB"                 # キャッシュサイズ
  
  # 接続プール
  connection_pool:
    max_connections: 10                 # 最大接続数
    idle_timeout: 300                   # アイドルタイムアウト（秒）
```

### タイムアウト設定

```yaml
timeouts:
  connection: 30                        # 接続タイムアウト（秒）
  query: 300                           # クエリタイムアウト（秒）
  total_comparison: 1800               # 全体のタイムアウト（秒）
  
  # 段階的タイムアウト
  progressive_timeout:
    enabled: true
    initial: 60                        # 初期タイムアウト
    increment: 30                      # 増分
    max_attempts: 3                    # 最大試行回数
```

## 🔧 カスタマイズオプション

### カスタム重要度設定

```yaml
severity_mapping:
  critical:
    - "table_removed"
    - "column_removed"
    - "foreign_key_removed"
    - "unique_constraint_removed"
  
  warning:
    - "table_added"
    - "column_added"
    - "data_type_changed"
    - "constraint_modified"
  
  info:
    - "index_added"
    - "index_removed"
    - "comment_changed"
    - "default_value_changed"
```

### カスタムルール

```yaml
custom_rules:
  # データ型の互換性ルール
  type_compatibility:
    varchar:
      compatible_types: ["text", "char"]
      max_size_difference: 50           # 最大サイズ差
    
    decimal:
      compatible_types: ["numeric", "float"]
      precision_tolerance: 2            # 精度の許容差
  
  # 命名規則
  naming_conventions:
    tables:
      pattern: "^[a-z][a-z0-9_]*[a-z0-9]$"
      message: "Table names should be lowercase with underscores"
    
    columns:
      pattern: "^[a-z][a-z0-9_]*[a-z0-9]$"
      message: "Column names should be lowercase with underscores"
  
  # ビジネスルール
  business_rules:
    - name: "Primary key required"
      condition: "every table must have a primary key"
      check: "table.primary_key is not null"
    
    - name: "Audit columns required"
      condition: "tables should have created_at and updated_at"
      check: "table.has_columns(['created_at', 'updated_at'])"
```

## 📊 レポートカスタマイズ

### HTMLレポート設定

```yaml
html_report:
  template: "templates/company-template.html"
  stylesheet: "assets/company-styles.css"
  
  # 表示オプション
  show_identical: false                 # 同一項目の表示
  expand_details: true                  # 詳細の自動展開
  include_sql: true                     # SQL文の表示
  
  # 色テーマ
  theme:
    primary_color: "#007bff"
    success_color: "#28a745"
    warning_color: "#ffc107"
    danger_color: "#dc3545"
  
  # 追加情報
  metadata:
    company_name: "Acme Corporation"
    report_author: "Database Team"
    contact_info: "dba@acme.com"
```

### Markdownレポート設定

```yaml
markdown_report:
  template: "templates/custom-markdown.md"
  
  # GitHub Pages対応
  github_pages:
    enabled: true
    front_matter:
      layout: "report"
      title: "Schema Comparison Report"
      date: "{timestamp}"
  
  # 出力オプション
  include_toc: true                     # 目次の生成
  section_numbers: true                 # セクション番号
  syntax_highlighting: true             # シンタックスハイライト
```

## ⚙️ 設定ファイルの検証

### スキーマ検証

```yaml
# config-schema.yaml - 設定ファイルのスキーマ
type: object
required:
  - databases
properties:
  databases:
    type: object
    required:
      - source
      - target
    properties:
      source:
        type: object
        required:
          - host
          - database
        properties:
          host:
            type: string
          port:
            type: integer
            minimum: 1
            maximum: 65535
          database:
            type: string
            minLength: 1
```

### 設定の検証コマンド

```bash
# 設定ファイルの妥当性チェック
pgsd validate-config config/my-config.yaml

# 接続テスト
pgsd test-connection config/my-config.yaml

# 設定内容の表示
pgsd show-config config/my-config.yaml
```

## 💡 ベストプラクティス

### 1. 設定ファイルの構成

```
config/
├── base.yaml                 # 共通設定
├── environments/
│   ├── development.yaml      # 開発環境
│   ├── staging.yaml          # ステージング環境
│   └── production.yaml       # 本番環境
├── profiles/
│   ├── daily-check.yaml      # 日次チェック
│   └── release-check.yaml    # リリースチェック
└── templates/
    ├── html-template.html    # HTMLテンプレート
    └── markdown-template.md  # Markdownテンプレート
```

### 2. セキュリティ

```yaml
# 機密情報は環境変数で管理
databases:
  source:
    password: "${SOURCE_DB_PASSWORD}"   # ✅ 良い例
    # password: "hardcoded_password"    # ❌ 悪い例

# .gitignore に機密情報を含むファイルを追加
config/local.yaml
config/secrets.yaml
.env
```

### 3. 設定の継承

```yaml
# config/base.yaml
output:
  format: html
  directory: "./reports"

logging:
  level: INFO
```

```yaml
# config/production.yaml
extends: "base.yaml"           # 基本設定を継承

# 本番環境固有の設定のみ記述
databases:
  source:
    host: "prod.company.com"
    
logging:
  level: WARNING               # 本番では警告レベル
```

## 🚀 次のステップ

設定ファイルを理解したら：

1. **[データベース設定](database_setup.md)** - データベース接続の詳細設定
2. **[出力設定](output_settings.md)** - 出力形式とカスタマイズ
3. **[自動化機能](../features/automation.md)** - 設定ファイルを使った自動化

## 📚 関連資料

- [設定リファレンス](../reference/config_reference.md)
- [環境変数リファレンス](../reference/environment_variables.md)
- [トラブルシューティング](../troubleshooting/configuration_issues.md)