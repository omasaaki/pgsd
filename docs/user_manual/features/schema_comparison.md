# スキーマ比較機能

PGSDのコア機能であるスキーマ比較について詳しく説明します。

## 🎯 この章で学ぶこと

- スキーマ比較の仕組み
- 検出される差分の種類
- 比較精度の調整方法
- 高度な比較オプション

## 🔍 スキーマ比較の仕組み

### 比較プロセス

PGSDは以下の段階でスキーマを比較します：

1. **メタデータ収集**: 各データベースからスキーマ情報を取得
2. **正規化**: データを比較可能な形式に変換
3. **差分検出**: アルゴリズムにより差分を特定
4. **分類・優先度付け**: 差分を種類と重要度で分類
5. **レポート生成**: 結果を指定形式で出力

### 情報取得方法

```sql
-- PGSDが内部で実行するクエリの例
SELECT 
  schemaname,
  tablename,
  attname as column_name,
  typname as data_type,
  attlen as length,
  attnotnull as not_null,
  atthasdef as has_default
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
JOIN pg_type t ON a.atttypid = t.oid
WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  AND a.attnum > 0
  AND NOT a.attisdropped;
```

## 📊 検出される差分の種類

### テーブル関連

#### 1. テーブル構造
- **テーブル追加/削除**
- **テーブル名変更**
- **テーブルコメント変更**

```yaml
# 検出例
tables:
  added:
    - name: "new_feature_table"
      columns: 5
      created: "2025-07-15 10:30:00"
  
  removed:
    - name: "deprecated_table" 
      last_seen: "2025-07-14 15:45:00"
  
  modified:
    - name: "user_profiles"
      changes:
        - type: "comment_changed"
          old: "User profile information"
          new: "Enhanced user profile data"
```

#### 2. カラム構造
- **カラム追加/削除**
- **データ型変更**
- **制約変更（NOT NULL、DEFAULT等）**

```yaml
# 検出例
columns:
  added:
    - table: "users"
      name: "last_login_ip"
      type: "inet"
      nullable: true
  
  removed:
    - table: "orders"
      name: "legacy_field"
      type: "varchar(50)"
  
  modified:
    - table: "products"
      name: "price"
      changes:
        - type: "type_changed"
          old: "decimal(10,2)"
          new: "decimal(12,2)"
        - type: "default_changed"
          old: "0.00"
          new: "null"
```

### インデックス関連

#### 1. インデックス構造
- **インデックス追加/削除**
- **インデックス定義変更**
- **一意制約の変更**

```yaml
# 検出例
indexes:
  added:
    - name: "idx_users_email_verified"
      table: "users"
      columns: ["email", "verified_at"]
      unique: false
      type: "btree"
  
  removed:
    - name: "idx_old_composite"
      table: "orders"
      columns: ["status", "created_at"]
  
  modified:
    - name: "idx_products_name"
      table: "products"
      changes:
        - type: "uniqueness_changed"
          old: false
          new: true
```

### 制約関連

#### 1. 外部キー制約
- **外部キー追加/削除**
- **参照テーブル変更**
- **カスケード設定変更**

```yaml
# 検出例
foreign_keys:
  added:
    - name: "fk_orders_customer_id"
      table: "orders"
      column: "customer_id"
      references:
        table: "customers"
        column: "id"
      on_delete: "CASCADE"
      on_update: "RESTRICT"
  
  removed:
    - name: "fk_old_reference"
      table: "order_items"
      column: "product_id"
```

#### 2. CHECK制約
- **CHECK制約追加/削除**
- **制約条件変更**

```yaml
# 検出例
check_constraints:
  added:
    - name: "chk_price_positive"
      table: "products"
      condition: "price > 0"
  
  modified:
    - name: "chk_status_valid"
      table: "orders"
      changes:
        - type: "condition_changed"
          old: "status IN ('pending', 'completed')"
          new: "status IN ('pending', 'processing', 'completed', 'cancelled')"
```

### ビューとシーケンス

#### 1. ビュー
- **ビュー定義変更**
- **ビュー追加/削除**

```yaml
# 検出例
views:
  modified:
    - name: "customer_summary"
      changes:
        - type: "definition_changed"
          old: "SELECT id, name, email FROM customers"
          new: "SELECT id, name, email, phone FROM customers WHERE active = true"
```

#### 2. シーケンス
- **シーケンス設定変更**
- **開始値・増分値変更**

## ⚙️ 比較精度の調整

### 基本設定

```yaml
# config/comparison-settings.yaml
comparison:
  # 大文字小文字の区別
  case_sensitive: true
  
  # コメント変更を検出
  include_comments: true
  
  # 権限情報を比較
  include_permissions: false
  
  # デフォルト値の比較精度
  default_value_precision: "exact"  # exact, loose, ignore
  
  # データ型の互換性チェック
  type_compatibility: "strict"  # strict, loose, permissive
```

### 除外ルール

```yaml
# 比較から除外する項目
exclusions:
  # 除外するテーブル
  tables:
    - "temp_*"           # 一時テーブル
    - "log_*"            # ログテーブル
    - "migration_*"      # マイグレーション履歴
  
  # 除外するカラム
  columns:
    - "created_at"       # 作成日時（自動生成）
    - "updated_at"       # 更新日時
    - "*_timestamp"      # タイムスタンプ系
  
  # 除外するインデックス
  indexes:
    - "*_pkey"          # 主キー（自動生成される場合）
    - "pg_*"            # PostgreSQL内部インデックス
```

### フィルタリング

```yaml
# 特定条件での比較
filters:
  # 特定のスキーマのみ
  schemas:
    include: ["public", "app_data"]
    exclude: ["information_schema", "pg_catalog"]
  
  # 特定のテーブルパターン
  tables:
    include_pattern: "app_*"
    exclude_pattern: "temp_*"
  
  # 最終更新日でフィルタ
  last_modified:
    after: "2025-07-01"
    before: "2025-07-15"
```

## 🔧 高度な比較オプション

### カスタム比較ルール

```yaml
# config/custom-rules.yaml
comparison_rules:
  # データ型の互換性定義
  type_compatibility:
    varchar:
      compatible_with: ["text", "char"]
      size_tolerance: 10  # サイズ差10%まで許容
    
    decimal:
      compatible_with: ["numeric"]
      precision_tolerance: 2
  
  # インデックス重要度
  index_importance:
    unique_indexes: "critical"
    foreign_key_indexes: "important"
    performance_indexes: "normal"
  
  # 制約の重要度
  constraint_importance:
    foreign_keys: "critical"
    check_constraints: "important"
    not_null: "normal"
```

### バッチ比較

```bash
# 複数データベースの一括比較
pgsd compare \
  --config config/batch-comparison.yaml \
  --batch-mode \
  --parallel 4
```

```yaml
# config/batch-comparison.yaml
batch_comparison:
  comparisons:
    - name: "prod-vs-staging"
      source:
        host: "prod.company.com"
        database: "myapp"
      target:
        host: "staging.company.com"
        database: "myapp"
    
    - name: "staging-vs-dev"
      source:
        host: "staging.company.com"
        database: "myapp"
      target:
        host: "dev.company.com"
        database: "myapp"
  
  output:
    directory: "./batch-reports"
    format: ["html", "json"]
```

### 履歴追跡

```yaml
# config/history-tracking.yaml
history:
  # 比較履歴の保存
  enabled: true
  storage_path: "./comparison-history"
  
  # 変更パターンの分析
  pattern_analysis:
    enabled: true
    window_days: 30
  
  # トレンド分析
  trend_analysis:
    enabled: true
    metrics:
      - "table_count_change"
      - "column_count_change"
      - "index_count_change"
```

## 📈 比較結果の分析

### 重要度による分類

```yaml
# 差分の重要度分類
severity_levels:
  critical:
    - table_removed
    - column_removed
    - foreign_key_removed
    - unique_constraint_removed
  
  warning:
    - table_added
    - column_added
    - data_type_changed
    - not_null_added
  
  info:
    - index_added
    - index_removed
    - comment_changed
    - default_value_changed
```

### 影響度分析

```yaml
# 変更の影響度評価
impact_analysis:
  breaking_changes:
    - "column_removed"
    - "table_removed"
    - "not_null_constraint_added"
    - "foreign_key_cascade_changed"
  
  migration_required:
    - "data_type_changed"
    - "column_length_decreased"
    - "check_constraint_added"
  
  performance_impact:
    - "index_removed"
    - "large_table_structure_changed"
    - "foreign_key_added"
```

## 🎛️ パフォーマンス最適化

### 大規模スキーマの処理

```yaml
# config/performance-tuning.yaml
performance:
  # 並列処理設定
  parallel_processing:
    enabled: true
    max_workers: 4
    chunk_size: 1000
  
  # キャッシュ設定
  caching:
    enabled: true
    ttl_seconds: 3600
    max_cache_size: "100MB"
  
  # メモリ管理
  memory_management:
    max_memory_usage: "2GB"
    streaming_mode: true
```

### 選択的比較

```bash
# 特定テーブルのみ比較
pgsd compare \
  --config config/default.yaml \
  --tables "users,orders,products" \
  --fast-mode

# インデックスのみ比較
pgsd compare \
  --config config/default.yaml \
  --compare-only indexes \
  --output reports/indexes-only
```

## 🔍 デバッグとトラブルシューティング

### 詳細ログ

```bash
# 詳細な比較ログを出力
pgsd compare \
  --config config/default.yaml \
  --verbose \
  --debug \
  --log-file comparison-debug.log
```

### 比較プロセスの可視化

```yaml
# config/debug.yaml
debug:
  # 実行計画の出力
  explain_queries: true
  
  # 中間結果の保存
  save_intermediate_results: true
  output_path: "./debug-output"
  
  # パフォーマンス統計
  performance_stats: true
```

## 💡 ベストプラクティス

### 1. 段階的比較
```bash
# 1. 高レベル比較（高速）
pgsd compare --config config/default.yaml --summary-only

# 2. 詳細比較（特定テーブル）
pgsd compare --config config/default.yaml --tables "critical_tables" --detailed

# 3. 完全比較（全項目）
pgsd compare --config config/default.yaml --comprehensive
```

### 2. 定期的な設定見直し
```yaml
# 設定の定期見直し項目
review_schedule:
  monthly:
    - exclusion_rules
    - performance_settings
  quarterly:
    - comparison_rules
    - severity_levels
  annually:
    - overall_strategy
    - tool_version_upgrade
```

### 3. チーム共有設定
```yaml
# チーム共通設定
team_settings:
  # 標準化されたルール
  standard_exclusions: true
  
  # 共通の重要度設定
  shared_severity_config: "config/team-severity.yaml"
  
  # レポート形式の統一
  default_formats: ["html", "markdown"]
```

## 🚀 次のステップ

スキーマ比較機能を理解したら：

1. **[レポート形式](report_formats.md)** - 様々な出力形式の活用
2. **[差分解析](diff_analysis.md)** - 差分の詳細分析方法
3. **[自動化機能](automation.md)** - 比較プロセスの自動化

## 📚 関連資料

- [設定リファレンス](../reference/config_reference.md)
- [パフォーマンス調整](../advanced/performance_tuning.md)
- [トラブルシューティング](../troubleshooting/performance_issues.md)