# 差分解析

PGSDの高度な差分解析機能について詳しく説明します。

## 🎯 この章で学ぶこと

- 差分検出アルゴリズムの詳細
- 変更の重要度評価
- 影響度分析
- カスタム分析ルールの作成

## 🔍 差分検出の仕組み

### 検出アルゴリズム

PGSDは以下の段階で差分を検出します：

```yaml
# 差分検出プロセス
detection_process:
  1. メタデータ収集:
    - PostgreSQLシステムカタログからスキーマ情報を取得
    - pg_class, pg_attribute, pg_constraint等を活用
  
  2. 正規化:
    - データ型の統一（例：varchar(255) ↔ character varying(255)）
    - デフォルト値の正規化
    - 制約名の正規化
  
  3. 構造比較:
    - ハッシュベースの高速比較
    - 階層構造での差分検出
  
  4. 詳細分析:
    - 変更内容の詳細分類
    - 依存関係の分析
    - 影響範囲の特定
```

### 比較対象オブジェクト

```yaml
comparison_targets:
  database_objects:
    tables:
      - structure              # テーブル構造
      - columns                # カラム定義
      - constraints            # 制約
      - indexes                # インデックス
      - triggers               # トリガー
      - comments               # コメント
    
    views:
      - definition             # ビュー定義
      - dependencies           # 依存関係
    
    sequences:
      - current_value          # 現在値
      - increment              # 増分値
      - min_value             # 最小値
      - max_value             # 最大値
    
    functions:
      - definition             # 関数定義
      - parameters             # パラメータ
      - return_type           # 戻り値型
    
    types:
      - definition             # 型定義
      - enum_values           # ENUM値
```

## 📊 変更の分類

### 変更タイプの階層

```yaml
change_hierarchy:
  structural_changes:
    object_level:
      - object_added          # オブジェクト追加
      - object_removed        # オブジェクト削除
      - object_renamed        # オブジェクト名変更
    
    property_level:
      - property_added        # プロパティ追加
      - property_removed      # プロパティ削除
      - property_modified     # プロパティ変更
  
  behavioral_changes:
    constraint_changes:
      - constraint_added      # 制約追加
      - constraint_removed    # 制約削除
      - constraint_modified   # 制約変更
    
    performance_changes:
      - index_added          # インデックス追加
      - index_removed        # インデックス削除
      - index_modified       # インデックス変更
```

### 詳細な変更分類

```yaml
detailed_classification:
  table_changes:
    structure:
      - column_added:
          severity: info
          impact: low
          reversible: true
      - column_removed:
          severity: critical
          impact: high
          reversible: false
      - column_type_changed:
          severity: warning
          impact: medium
          reversible: depends_on_change
    
    constraints:
      - primary_key_added:
          severity: warning
          impact: medium
          reversible: true
      - foreign_key_removed:
          severity: critical
          impact: high
          reversible: true
      - check_constraint_modified:
          severity: warning
          impact: medium
          reversible: true
  
  index_changes:
    performance:
      - unique_index_removed:
          severity: critical
          impact: high
          reversible: true
      - index_definition_changed:
          severity: info
          impact: low
          reversible: true
```

## ⚖️ 重要度評価システム

### 基本重要度レベル

```yaml
severity_levels:
  critical:
    description: "データ損失やアプリケーション障害を引き起こす可能性"
    examples:
      - テーブル削除
      - カラム削除
      - NOT NULL制約追加（既存データでNULL値がある場合）
      - 主キー削除
      - 外部キー削除
    
    actions:
      - immediate_attention: true
      - manual_review_required: true
      - backup_recommended: true
  
  warning:
    description: "パフォーマンス影響や軽微な互換性問題の可能性"
    examples:
      - データ型変更
      - インデックス削除
      - デフォルト値変更
      - カラム長変更
    
    actions:
      - review_recommended: true
      - testing_required: true
  
  info:
    description: "機能追加や情報変更（影響は最小限）"
    examples:
      - カラム追加
      - インデックス追加
      - コメント変更
      - ビュー定義変更
    
    actions:
      - documentation_update: true
```

### カスタム重要度ルール

```yaml
# config/custom-severity-rules.yaml
custom_severity_rules:
  # テーブル固有のルール
  table_specific:
    critical_tables:
      - "users"
      - "orders"
      - "payments"
    rules:
      - if: "table in critical_tables and change_type == 'column_removed'"
        then: "critical"
      - if: "table in critical_tables and change_type == 'column_added' and nullable == false"
        then: "warning"
  
  # カラム名パターンベース
  column_patterns:
    audit_columns:
      pattern: "(created_at|updated_at|deleted_at)"
      rules:
        - if: "change_type == 'column_removed'"
          then: "warning"  # 通常はcriticalだが、監査カラムはwarning
  
  # ビジネスルールベース
  business_rules:
    - name: "PCI compliance check"
      condition: "column_name like '%card%' or column_name like '%payment%'"
      severity_modifier: "+1"  # 重要度を1段階上げる
    
    - name: "Personal data protection"
      condition: "column_name in ('email', 'phone', 'address')"
      severity_modifier: "+1"
```

## 📈 影響度分析

### 依存関係の分析

```yaml
dependency_analysis:
  # オブジェクト間の依存関係
  object_dependencies:
    tables:
      - foreign_key_dependencies    # 外部キー依存
      - view_dependencies          # ビュー依存
      - function_dependencies      # 関数依存
      - trigger_dependencies       # トリガー依存
    
    columns:
      - index_dependencies         # インデックス依存
      - constraint_dependencies    # 制約依存
      - view_column_dependencies   # ビューカラム依存
  
  # アプリケーションへの影響
  application_impact:
    breaking_changes:
      - column_removal            # カラム削除
      - table_removal            # テーブル削除
      - data_type_incompatible    # 互換性のないデータ型変更
    
    compatibility_changes:
      - column_nullable_change    # NULL許可の変更
      - default_value_change      # デフォルト値変更
      - constraint_addition       # 制約追加
```

### 影響度スコア計算

```yaml
impact_scoring:
  # 基本スコア（0-100）
  base_scores:
    table_removed: 100            # 最大影響
    column_removed: 80
    constraint_removed: 60
    index_removed: 40
    column_added: 20
    comment_changed: 5            # 最小影響
  
  # 修正係数
  modifiers:
    table_size:
      small: 1.0         # 1000行未満
      medium: 1.2        # 1000-100万行
      large: 1.5         # 100万行以上
    
    usage_frequency:
      high: 1.3          # 頻繁にアクセス
      medium: 1.1        # 中程度
      low: 0.9           # 低頻度
    
    business_criticality:
      core: 1.5          # コア機能
      important: 1.2     # 重要機能
      optional: 0.8      # オプション機能
  
  # 最終スコア = base_score × table_size × usage_frequency × business_criticality
```

## 🎯 高度な分析機能

### パターン分析

```yaml
pattern_analysis:
  # 変更パターンの検出
  change_patterns:
    schema_evolution:
      - table_normalization      # テーブル正規化
      - denormalization         # 非正規化
      - column_consolidation    # カラム統合
      - table_splitting         # テーブル分割
    
    performance_optimization:
      - index_optimization      # インデックス最適化
      - partition_introduction  # パーティション導入
      - column_type_optimization # 型最適化
    
    business_expansion:
      - feature_addition        # 機能追加
      - internationalization   # 国際化対応
      - audit_trail_addition   # 監査証跡追加
  
  # パターンマッチング設定
  pattern_detection:
    enabled: true
    confidence_threshold: 0.7   # 信頼度閾値
    min_changes_for_pattern: 3  # パターン検出に必要な最小変更数
```

### トレンド分析

```yaml
trend_analysis:
  # 履歴データの分析
  historical_analysis:
    enabled: true
    history_window_days: 90     # 分析対象期間
    
    metrics:
      - schema_growth_rate      # スキーマ成長率
      - change_frequency        # 変更頻度
      - rollback_frequency      # ロールバック頻度
      - error_prone_objects     # エラーが起きやすいオブジェクト
  
  # 予測分析
  predictive_analysis:
    enabled: true
    algorithms:
      - linear_regression       # 線形回帰
      - seasonal_decomposition  # 季節分解
      - anomaly_detection      # 異常検知
    
    predictions:
      - future_schema_size      # 将来のスキーマサイズ
      - maintenance_windows     # メンテナンス時期
      - potential_issues        # 潜在的問題
```

## 🔧 カスタム分析ルール

### ルール定義の構文

```yaml
# config/custom-analysis-rules.yaml
custom_rules:
  # ルール定義
  rules:
    - name: "audit_column_check"
      description: "監査カラムの整合性チェック"
      condition: |
        table.has_column('created_at') and 
        table.has_column('updated_at') and
        not table.has_column('created_by')
      severity: "warning"
      message: "監査カラム'created_by'が不足しています"
      recommendation: "ALTER TABLE {table_name} ADD COLUMN created_by VARCHAR(255);"
    
    - name: "primary_key_missing"
      description: "主キーの存在チェック"
      condition: "not table.has_primary_key()"
      severity: "critical"
      message: "テーブル'{table_name}'に主キーがありません"
      recommendation: "主キーとなるカラムを追加してください"
    
    - name: "large_varchar_check"
      description: "大きなVARCHARカラムのチェック"
      condition: |
        column.type == 'varchar' and 
        column.length > 1000
      severity: "info"
      message: "VARCHAR({column_length})は大きすぎる可能性があります"
      recommendation: "TEXTタイプの使用を検討してください"
```

### 条件式の記述

```yaml
condition_syntax:
  # 利用可能な変数
  variables:
    table:
      - name                    # テーブル名
      - column_count           # カラム数
      - has_primary_key()      # 主キー存在確認
      - has_column(name)       # カラム存在確認
      - row_count             # 行数（推定）
    
    column:
      - name                   # カラム名
      - type                   # データ型
      - length                 # 長さ
      - nullable              # NULL許可
      - has_default           # デフォルト値有無
      - is_primary_key        # 主キーかどうか
    
    change:
      - type                   # 変更タイプ
      - severity              # 重要度
      - impact               # 影響度
      - reversible           # 可逆性
  
  # 利用可能な関数
  functions:
    string:
      - contains(str, substr)  # 文字列包含
      - starts_with(str, prefix) # 前方一致
      - ends_with(str, suffix)   # 後方一致
      - matches(str, pattern)    # 正規表現マッチ
    
    comparison:
      - in(value, list)        # リスト包含
      - between(value, min, max) # 範囲チェック
      - greater_than(a, b)     # 大小比較
    
    logical:
      - and(expr1, expr2)      # 論理積
      - or(expr1, expr2)       # 論理和
      - not(expr)              # 論理否定
```

## 📊 分析レポートの生成

### 詳細分析レポート

```yaml
analysis_reports:
  # 標準レポート
  standard_reports:
    - summary_report           # サマリーレポート
    - detailed_diff_report     # 詳細差分レポート
    - impact_analysis_report   # 影響度分析レポート
    - recommendation_report    # 推奨事項レポート
  
  # カスタムレポート
  custom_reports:
    - name: "security_analysis"
      template: "templates/security-analysis.md"
      focus_areas:
        - permission_changes
        - column_encryption
        - sensitive_data_exposure
    
    - name: "performance_impact"
      template: "templates/performance-impact.html"
      focus_areas:
        - index_changes
        - table_size_impact
        - query_performance_prediction
```

### レポートテンプレート例

```markdown
<!-- templates/impact-analysis.md -->
# 影響度分析レポート

## 🎯 エグゼクティブサマリー

**総合影響度スコア**: {{total_impact_score}}/100

{{#if critical_changes}}
⚠️ **重要:** {{critical_changes.length}}件の重要な変更が検出されました。
{{/if}}

## 📊 影響度分析

### 重要度別集計

| 重要度 | 件数 | 影響度スコア |
|--------|------|-------------|
| Critical | {{critical_count}} | {{critical_score}} |
| Warning | {{warning_count}} | {{warning_score}} |
| Info | {{info_count}} | {{info_score}} |

### トップ10影響度の高い変更

{{#each top_impact_changes}}
{{@index}}. **{{this.object_name}}** (スコア: {{this.impact_score}})
   - 変更タイプ: {{this.change_type}}
   - 説明: {{this.description}}
   - 推奨アクション: {{this.recommendation}}
{{/each}}

## 🎯 推奨アクション

### 即座に対応が必要

{{#each immediate_actions}}
- [ ] {{this.description}} ({{this.object_name}})
{{/each}}

### 計画的に対応

{{#each planned_actions}}
- [ ] {{this.description}} ({{this.object_name}})
{{/each}}

## 📈 リスク評価

{{risk_assessment}}

## 🔍 詳細分析

{{detailed_analysis}}
```

## 💡 ベストプラクティス

### 分析の段階的アプローチ

```yaml
staged_analysis:
  stage_1_quick_scan:
    duration: "< 1分"
    scope: "高レベル差分の検出"
    output: "サマリーレポート"
  
  stage_2_detailed_analysis:
    duration: "1-5分"
    scope: "詳細差分と基本影響度"
    output: "詳細差分レポート"
  
  stage_3_deep_analysis:
    duration: "5-15分"
    scope: "完全な影響度分析と推奨事項"
    output: "包括的分析レポート"
```

### 分析精度の向上

```yaml
accuracy_improvement:
  # 統計情報の活用
  statistics_usage:
    enabled: true
    table_stats: true         # テーブル統計
    column_stats: true        # カラム統計
    index_usage_stats: true   # インデックス使用統計
  
  # アプリケーション情報の統合
  application_integration:
    orm_metadata: true        # ORMメタデータ
    query_logs: true          # クエリログ
    performance_metrics: true # パフォーマンスメトリクス
```

## 🚀 次のステップ

差分解析を理解したら：

1. **[自動化機能](automation.md)** - 分析プロセスの自動化
2. **[カスタムテンプレート](../advanced/custom_templates.md)** - 分析レポートのカスタマイズ
3. **[API統合](../advanced/api_integration.md)** - 外部システムとの連携

## 📚 関連資料

- [分析ルール仕様](../reference/analysis_rules_spec.md)
- [影響度計算アルゴリズム](../reference/impact_calculation.md)
- [トラブルシューティング](../troubleshooting/analysis_issues.md)