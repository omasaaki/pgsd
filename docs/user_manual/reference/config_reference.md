# 設定リファレンス

PGSDの設定ファイルの完全なリファレンスです。

## 🎯 この章で学ぶこと

- 全設定項目の詳細仕様
- データ型と許可される値
- デフォルト値と推奨設定
- 設定例とベストプラクティス

## 📋 設定ファイルの基本構造

```yaml
# config/example.yaml
databases:          # データベース接続設定
  source: {}        # ソースデータベース
  target: {}        # ターゲットデータベース

output:             # 出力設定
  format: "html"    # 出力形式
  directory: "./reports"  # 出力先

comparison:         # 比較設定
  include_comments: true  # コメントを含める

performance:        # パフォーマンス設定
  parallel_processing: {} # 並列処理設定

logging:           # ログ設定
  level: "INFO"    # ログレベル
```

## 🔌 databases セクション

データベース接続に関する設定です。

### 基本接続設定

```yaml
databases:
  source:
    # 必須項目
    host: string                    # ホスト名またはIPアドレス
    port: integer                   # ポート番号 (デフォルト: 5432)
    database: string                # データベース名
    user: string                    # ユーザー名
    password: string                # パスワード
    
    # オプション項目
    schema: string                  # スキーマ名 (デフォルト: "public")
    application_name: string        # アプリケーション名 (デフォルト: "pgsd")
    connect_timeout: integer        # 接続タイムアウト秒 (デフォルト: 30)
    command_timeout: integer        # コマンドタイムアウト秒 (デフォルト: 300)
    
  target:
    # 同様の設定項目
```

### 詳細設定項目

#### 基本接続パラメータ

```yaml
databases:
  source:
    host: "localhost"
    port: 5432
    database: "myapp_production"
    user: "readonly_user"
    password: "${PROD_DB_PASSWORD}"
    schema: "public"
    
    # 接続オプション
    application_name: "pgsd-comparison"
    connect_timeout: 30
    command_timeout: 300
    
    # 文字エンコーディング
    client_encoding: "UTF8"
    
    # タイムゾーン
    timezone: "UTC"
    
    # 検索パス
    search_path: "public,app_schema"
```

#### SSL/TLS設定

```yaml
databases:
  source:
    host: "secure-db.company.com"
    port: 5432
    database: "myapp"
    user: "secure_user"
    password: "${SECURE_PASSWORD}"
    
    # SSL設定
    sslmode: "require"              # 許可される値: disable, allow, prefer, require, verify-ca, verify-full
    sslcert: "/path/to/client.crt"  # クライアント証明書
    sslkey: "/path/to/client.key"   # 秘密鍵
    sslrootcert: "/path/to/ca.crt"  # CA証明書
    sslcrl: "/path/to/root.crl"     # 証明書失効リスト
    
    # SSL詳細設定
    sslcompression: false           # SSL圧縮 (デフォルト: false)
    sslsni: true                    # SNI使用 (デフォルト: true)
```

#### 接続プール設定

```yaml
databases:
  source:
    # 基本接続設定...
    
    # 接続プール
    connection_pool:
      enabled: true                 # 接続プールを有効化 (デフォルト: false)
      min_connections: 2            # 最小接続数 (デフォルト: 1)
      max_connections: 10           # 最大接続数 (デフォルト: 5)
      max_idle_time: 300           # 最大アイドル時間秒 (デフォルト: 600)
      max_lifetime: 1800           # 最大接続寿命秒 (デフォルト: 3600)
      health_check_interval: 60    # ヘルスチェック間隔秒 (デフォルト: 60)
      validation_query: "SELECT 1"  # 検証クエリ
```

#### 高度な接続設定

```yaml
databases:
  source:
    # 基本設定...
    
    # PostgreSQL固有設定
    statement_timeout: 300000       # ステートメントタイムアウト ms (デフォルト: 0)
    lock_timeout: 30000            # ロックタイムアウト ms (デフォルト: 0)
    idle_in_transaction_session_timeout: 600000  # トランザクション内アイドルタイムアウト ms
    
    # 接続試行設定
    retry_attempts: 3               # 再試行回数 (デフォルト: 0)
    retry_delay: 5                  # 再試行間隔秒 (デフォルト: 1)
    retry_backoff: 2.0             # バックオフ係数 (デフォルト: 1.0)
    
    # 接続維持設定
    keepalive: true                # TCP Keep-Alive (デフォルト: false)
    keepalive_idle: 600           # Keep-Aliveアイドル時間秒 (デフォルト: 7200)
    keepalive_interval: 60        # Keep-Alive間隔秒 (デフォルト: 75)
    keepalive_count: 3            # Keep-Alive回数 (デフォルト: 9)
```

## 📊 output セクション

出力に関する設定です。

### 基本出力設定

```yaml
output:
  # 必須項目
  format: "html"                  # 出力形式: html, markdown, json, xml
  directory: "./reports"          # 出力ディレクトリ
  
  # オプション項目
  filename_template: "schema_diff_{timestamp}"  # ファイル名テンプレート
  overwrite_existing: false       # 既存ファイルの上書き (デフォルト: false)
  create_subdirectories: true     # サブディレクトリの自動作成 (デフォルト: true)
  compress_output: false          # 出力の圧縮 (デフォルト: false)
```

### ファイル名テンプレート

```yaml
output:
  filename_template: "{comparison_type}_{source_db}_vs_{target_db}_{timestamp}"
  
  # 利用可能な変数:
  # {timestamp}      - 実行時刻 (20250715_143022)
  # {date}          - 実行日 (20250715)
  # {time}          - 実行時刻 (143022)
  # {source_db}     - ソースDB名
  # {target_db}     - ターゲットDB名
  # {source_host}   - ソースホスト名
  # {target_host}   - ターゲットホスト名
  # {schema}        - スキーマ名
  # {format}        - 出力形式
  # {version}       - PGSDバージョン
  # {user}          - 実行ユーザー
  # {comparison_type} - 比較タイプ
```

### 形式別設定

#### HTML出力設定

```yaml
output:
  format: "html"
  
  html_output:
    template: "templates/custom.html"     # カスタムテンプレート
    stylesheet: "assets/styles.css"       # CSSファイル
    include_assets: true                  # アセットファイルの埋め込み
    
    # 表示オプション
    show_identical: false                 # 同一項目の表示
    expand_details: true                  # 詳細の自動展開
    include_sql: true                     # SQL文の表示
    interactive_features: true            # インタラクティブ機能
    
    # 色テーマ
    theme:
      primary_color: "#007bff"
      success_color: "#28a745"
      warning_color: "#ffc107"
      danger_color: "#dc3545"
      info_color: "#17a2b8"
    
    # ページネーション
    pagination:
      enabled: true
      items_per_page: 100
    
    # 最適化
    minify_html: true                     # HTML圧縮
    minify_css: true                      # CSS圧縮
    minify_js: true                       # JavaScript圧縮
```

#### Markdown出力設定

```yaml
output:
  format: "markdown"
  
  markdown_output:
    template: "templates/custom.md"       # カスタムテンプレート
    
    # GitHub Pages設定
    github_pages:
      enabled: true
      front_matter:
        layout: "report"
        title: "Schema Comparison Report"
        categories: ["database", "schema"]
        tags: ["postgresql", "comparison"]
    
    # 出力オプション
    include_toc: true                     # 目次の生成
    toc_depth: 3                          # 目次の深さ
    section_numbers: true                 # セクション番号
    syntax_highlighting: true             # シンタックスハイライト
    line_breaks: "github"                 # 改行スタイル
    
    # 拡張機能
    extensions:
      tables: true                        # テーブル拡張
      footnotes: true                     # 脚注
      definition_lists: true              # 定義リスト
      task_lists: true                    # タスクリスト
```

#### JSON出力設定

```yaml
output:
  format: "json"
  
  json_output:
    pretty_print: true                    # 整形出力
    include_metadata: true                # メタデータの包含
    schema_version: "2.0"                 # JSONスキーマバージョン
    
    # データ最適化
    compress_arrays: false                # 配列の圧縮
    omit_null_values: true                # null値の省略
    
    # API互換性
    api_compatibility:
      include_legacy_fields: false        # 旧フィールドの包含
      camel_case_keys: false              # キー名のキャメルケース化
    
    # 拡張情報
    extended_info:
      include_query_performance: true     # クエリパフォーマンス情報
      include_statistics: true            # 統計情報
      include_recommendations: true       # 推奨事項
```

#### XML出力設定

```yaml
output:
  format: "xml"
  
  xml_output:
    encoding: "UTF-8"                     # 文字エンコーディング
    pretty_print: true                    # 整形出力
    include_xml_declaration: true         # XML宣言の包含
    
    # スキーマ
    schema_location: "https://pgsd.org/schema/report/v2.0"
    validate_against_schema: true         # スキーマ検証
    
    # 名前空間
    namespaces:
      default: "https://pgsd.org/schema/report/v2.0"
      xsi: "http://www.w3.org/2001/XMLSchema-instance"
    
    # XSLT変換
    xslt_transformation:
      enabled: true
      stylesheet: "templates/report-transform.xsl"
```

## 🔍 comparison セクション

比較処理に関する設定です。

### 基本比較設定

```yaml
comparison:
  # 比較対象
  include_comments: true                  # コメントの比較 (デフォルト: false)
  include_permissions: false              # 権限の比較 (デフォルト: false)
  include_sequences: true                 # シーケンスの比較 (デフォルト: true)
  include_views: true                     # ビューの比較 (デフォルト: true)
  include_functions: false                # 関数の比較 (デフォルト: false)
  include_triggers: false                 # トリガーの比較 (デフォルト: false)
  
  # 比較オプション
  case_sensitive: true                    # 大文字小文字の区別 (デフォルト: true)
  ignore_whitespace: false                # 空白文字の無視 (デフォルト: false)
  
  # タイムアウト設定
  timeout: 300                           # 比較タイムアウト秒 (デフォルト: 300)
  query_timeout: 60                      # クエリタイムアウト秒 (デフォルト: 60)
```

### 除外設定

```yaml
comparison:
  # 除外パターン
  exclude_tables:
    - "temp_*"                          # パターンマッチング
    - "log_archive"                     # 特定テーブル名
    - "migration_*"                     # マイグレーション履歴
  
  exclude_columns:
    - "created_at"                      # 全テーブルの該当カラム
    - "updated_at"                      # 全テーブルの該当カラム
    - "users.password"                  # 特定テーブルのカラム
  
  exclude_schemas:
    - "information_schema"              # 情報スキーマ
    - "pg_catalog"                      # PostgreSQLシステムカタログ
    - "pg_toast"                        # TOASTテーブル
  
  exclude_indexes:
    - "*_pkey"                          # 主キーインデックス
    - "pg_*"                            # PostgreSQL内部インデックス
```

### フィルタリング設定

```yaml
comparison:
  filters:
    # 日付範囲フィルタ
    date_range:
      enabled: false
      start_date: "2025-01-01"
      end_date: "2025-07-15"
      column: "created_at"
    
    # テーブルサイズフィルタ
    table_size:
      enabled: false
      min_rows: 0
      max_rows: 1000000
    
    # 更新頻度フィルタ
    activity_level:
      enabled: false
      exclude_static_tables: true
      min_modification_date: "2025-01-01"
    
    # 重要度フィルタ
    severity_filter:
      enabled: false
      min_severity: "warning"           # info, warning, critical
```

### データ型互換性設定

```yaml
comparison:
  type_compatibility:
    mode: "strict"                      # strict, loose, permissive
    
    # カスタム互換性ルール
    custom_rules:
      varchar:
        compatible_with: ["text", "char"]
        size_tolerance: 10              # サイズ差の許容範囲（%）
        
      decimal:
        compatible_with: ["numeric", "float"]
        precision_tolerance: 2
        
      timestamp:
        compatible_with: ["timestamptz"]
        ignore_timezone: true
```

## ⚡ performance セクション

パフォーマンスに関する設定です。

### 基本パフォーマンス設定

```yaml
performance:
  # 並列処理
  parallel_processing:
    enabled: true                       # 並列処理を有効化 (デフォルト: false)
    max_workers: 4                      # 最大ワーカー数 (デフォルト: CPUコア数)
    chunk_size: 1000                    # 処理チャンクサイズ (デフォルト: 1000)
    
  # メモリ管理
  memory_management:
    max_memory_usage: "2GB"             # 最大メモリ使用量 (デフォルト: "1GB")
    streaming_mode: true                # ストリーミングモード (デフォルト: false)
    cache_size: "100MB"                 # キャッシュサイズ (デフォルト: "50MB")
    
  # バッチ処理
  batch_processing:
    enabled: true                       # バッチ処理を有効化 (デフォルト: false)
    batch_size: 1000                    # バッチサイズ (デフォルト: 1000)
    max_batch_memory: "100MB"           # バッチあたりの最大メモリ (デフォルト: "50MB")
```

### 詳細パフォーマンス設定

```yaml
performance:
  # 接続最適化
  connection_optimization:
    persistent_connections: true        # 永続接続 (デフォルト: false)
    connection_caching: true            # 接続キャッシュ (デフォルト: false)
    lazy_loading: true                  # 遅延ロード (デフォルト: false)
    
  # クエリ最適化
  query_optimization:
    prepared_statements: true           # プリペアドステートメント (デフォルト: false)
    statement_caching: true             # ステートメントキャッシュ (デフォルト: false)
    fetch_size: 1000                    # フェッチサイズ (デフォルト: 1000)
    
  # I/O最適化
  io_optimization:
    read_ahead: true                    # 先読み (デフォルト: false)
    async_io: true                      # 非同期I/O (デフォルト: false)
    buffer_size: "64KB"                 # バッファサイズ (デフォルト: "32KB")
    
  # 圧縮設定
  compression:
    enabled: false                      # 圧縮を有効化 (デフォルト: false)
    algorithm: "gzip"                   # 圧縮アルゴリズム (gzip, lz4, zstd)
    level: 6                            # 圧縮レベル (デフォルト: 6)
    min_size: 1024                      # 圧縮開始サイズ (デフォルト: 1024)
```

### 適応的パフォーマンス設定

```yaml
performance:
  # 動的調整
  adaptive_tuning:
    enabled: false                      # 適応的調整を有効化 (デフォルト: false)
    adjustment_interval: 300            # 調整間隔秒 (デフォルト: 300)
    
    # 自動調整対象
    auto_adjust:
      - worker_count
      - batch_size
      - memory_allocation
      - cache_size
    
    # 調整範囲
    adjustment_ranges:
      worker_count: [1, 16]
      batch_size: [100, 10000]
      memory_allocation: ["100MB", "4GB"]
      cache_size: ["10MB", "500MB"]
  
  # 予測的スケーリング
  predictive_scaling:
    enabled: false                      # 予測的スケーリングを有効化 (デフォルト: false)
    prediction_horizon: 60              # 予測期間分 (デフォルト: 60)
    scaling_threshold: 0.8              # スケーリング閾値 (デフォルト: 0.8)
    
    # スケーリング戦略
    scaling_strategy:
      scale_up_factor: 1.5              # スケールアップ係数 (デフォルト: 1.5)
      scale_down_factor: 0.7            # スケールダウン係数 (デフォルト: 0.7)
      cooldown_period: 300              # クールダウン期間秒 (デフォルト: 300)
```

## 📝 logging セクション

ログに関する設定です。

### 基本ログ設定

```yaml
logging:
  # 基本設定
  level: "INFO"                         # ログレベル: DEBUG, INFO, WARNING, ERROR, CRITICAL
  console: true                         # コンソール出力 (デフォルト: false)
  file: "pgsd.log"                      # ログファイル (デフォルト: null)
  
  # ログフォーマット
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
  
  # ログローテーション
  rotation:
    enabled: true                       # ローテーションを有効化 (デフォルト: false)
    max_size: "10MB"                    # ファイルサイズ上限 (デフォルト: "10MB")
    backup_count: 5                     # 保持するバックアップ数 (デフォルト: 5)
    rotation_time: "midnight"           # ローテーション時刻 (デフォルト: "midnight")
```

### 詳細ログ設定

```yaml
logging:
  # モジュール別ログレベル
  modules:
    connection: "INFO"                  # 接続モジュール
    comparison: "INFO"                  # 比較モジュール
    report: "WARNING"                   # レポートモジュール
    performance: "ERROR"                # パフォーマンスモジュール
  
  # 構造化ログ
  structured:
    enabled: false                      # 構造化ログを有効化 (デフォルト: false)
    format: "json"                      # 構造化形式 (json, xml)
    fields:
      - timestamp
      - level
      - message
      - source_db
      - target_db
      - operation
      - duration
  
  # リモートログ
  remote:
    enabled: false                      # リモートログを有効化 (デフォルト: false)
    endpoint: "https://logs.company.com/api/ingest"
    api_key: "${LOGGING_API_KEY}"
    batch_size: 100                     # バッチサイズ (デフォルト: 100)
    flush_interval: 30                  # フラッシュ間隔秒 (デフォルト: 30)
```

## 🔔 notifications セクション

通知に関する設定です。

### 基本通知設定

```yaml
notifications:
  enabled: true                         # 通知を有効化 (デフォルト: false)
  
  # 通知条件
  conditions:
    critical_changes: true              # 重要な変更時に通知 (デフォルト: false)
    warning_threshold: 5                # 警告数の閾値 (デフォルト: 0)
    completion: false                   # 完了時に通知 (デフォルト: false)
    error: true                         # エラー時に通知 (デフォルト: false)
  
  # 通知チャネル
  channels:
    email:
      enabled: true
      recipients: ["admin@company.com"]
      smtp_host: "smtp.company.com"
      smtp_port: 587
      username: "notifications@company.com"
      password: "${EMAIL_PASSWORD}"
    
    slack:
      enabled: false
      webhook_url: "${SLACK_WEBHOOK_URL}"
      channel: "#database-alerts"
      username: "PGSD Bot"
```

## 🔒 security セクション

セキュリティに関する設定です。

### 基本セキュリティ設定

```yaml
security:
  # 認証
  authentication:
    require_authentication: true        # 認証を必須とする (デフォルト: false)
    auth_method: "database"             # 認証方法 (database, ldap, oauth)
    session_timeout: 3600               # セッションタイムアウト秒 (デフォルト: 3600)
  
  # 権限
  authorization:
    role_based_access: false            # ロールベースアクセス制御 (デフォルト: false)
    default_role: "viewer"              # デフォルトロール (viewer, analyst, admin)
    
  # 暗号化
  encryption:
    encrypt_passwords: true             # パスワード暗号化 (デフォルト: true)
    encryption_key: "${ENCRYPTION_KEY}"
    
  # 監査
  audit:
    enabled: false                      # 監査ログを有効化 (デフォルト: false)
    log_file: "audit.log"               # 監査ログファイル
    log_level: "INFO"                   # 監査ログレベル
```

## 🔧 advanced セクション

高度な設定オプションです。

### 実験的機能

```yaml
advanced:
  experimental:
    enabled: false                      # 実験的機能を有効化 (デフォルト: false)
    
    # 機械学習による予測
    ml_predictions:
      enabled: false
      model_path: "models/prediction.pkl"
      confidence_threshold: 0.8
    
    # 異常検知
    anomaly_detection:
      enabled: false
      sensitivity: 0.1
      window_size: 30
  
  # 内部設定
  internal:
    debug_mode: false                   # デバッグモード (デフォルト: false)
    profiling: false                    # プロファイリング (デフォルト: false)
    memory_profiling: false             # メモリプロファイリング (デフォルト: false)
    
    # 内部限界値
    limits:
      max_table_count: 10000            # 最大テーブル数 (デフォルト: 10000)
      max_column_count: 100000          # 最大カラム数 (デフォルト: 100000)
      max_index_count: 50000            # 最大インデックス数 (デフォルト: 50000)
```

## 🌍 環境変数

設定ファイルで使用できる環境変数です。

### 標準環境変数

```bash
# データベース接続
DB_HOST                                 # データベースホスト
DB_PORT                                 # データベースポート
DB_NAME                                 # データベース名
DB_USER                                 # ユーザー名
DB_PASSWORD                             # パスワード

# PGSD設定
PGSD_CONFIG_FILE                        # 設定ファイルパス
PGSD_LOG_LEVEL                          # ログレベル
PGSD_LOG_FILE                           # ログファイル
PGSD_DATA_DIR                           # データディレクトリ
PGSD_TEMP_DIR                           # 一時ディレクトリ

# 通知設定
SLACK_WEBHOOK_URL                       # Slack Webhook URL
EMAIL_PASSWORD                          # メール認証パスワード
LOGGING_API_KEY                         # ログAPI キー
```

### 環境変数の使用例

```yaml
# config/env-example.yaml
databases:
  source:
    host: "${DB_HOST}"
    port: "${DB_PORT:-5432}"            # デフォルト値付き
    database: "${DB_NAME}"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
    
    # 条件付き設定
    sslmode: "${SSL_MODE:-prefer}"
    
logging:
  level: "${LOG_LEVEL:-INFO}"
  file: "${LOG_FILE:-pgsd.log}"
  
notifications:
  channels:
    slack:
      webhook_url: "${SLACK_WEBHOOK_URL}"
      enabled: "${SLACK_ENABLED:-false}"
```

## 🔍 設定検証

### 設定ファイルの検証

```bash
# 基本検証
pgsd validate-config config/production.yaml

# 厳密な検証
pgsd validate-config --strict config/production.yaml

# 接続確認を含む検証
pgsd validate-config --check-connections config/production.yaml
```

### 設定の表示

```bash
# 有効な設定の表示
pgsd config show --effective

# 設定の詳細表示
pgsd config show --verbose config/production.yaml
```

## 💡 設定のベストプラクティス

### 1. 環境別設定

```bash
config/
├── base.yaml              # 共通設定
├── development.yaml       # 開発環境
├── staging.yaml           # ステージング環境
├── production.yaml        # 本番環境
└── local.yaml             # ローカル開発用
```

### 2. 機密情報の管理

```yaml
# 機密情報は環境変数で管理
databases:
  source:
    password: "${DB_PASSWORD}"          # ✅ 推奨
    # password: "hardcoded_password"    # ❌ 非推奨
```

### 3. 設定の継承

```yaml
# config/production.yaml
extends: "base.yaml"                    # 基本設定を継承

# 本番環境固有の設定のみ記述
databases:
  source:
    host: "prod.company.com"
    
logging:
  level: "WARNING"
```

### 4. 設定の分離

```yaml
# config/database.yaml - データベース設定のみ
databases:
  source:
    host: "${DB_HOST}"
    database: "${DB_NAME}"

# config/output.yaml - 出力設定のみ
output:
  format: "html"
  directory: "./reports"

# config/main.yaml - メイン設定
include:
  - "database.yaml"
  - "output.yaml"
```

## 🚀 次のステップ

設定リファレンスを理解したら：

1. **[API仕様](api_specification.md)** - プログラムからの利用
2. **[CLIコマンド](cli_commands.md)** - コマンドラインでの利用
3. **[エラーコード](error_codes.md)** - エラーコードの詳細

## 📚 関連資料

- [設定ファイル](../configuration/config_file.md)
- [データベース設定](../configuration/database_setup.md)
- [出力設定](../configuration/output_settings.md)