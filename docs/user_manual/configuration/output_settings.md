# 出力設定

PGSDのレポート出力に関する詳細な設定方法について説明します。

## 🎯 この章で学ぶこと

- 出力形式の詳細設定
- ファイル管理とディレクトリ構成
- カスタムテンプレートの作成
- 出力の最適化設定

## 📄 基本的な出力設定

### 出力形式の指定

```yaml
# config/output-basic.yaml
output:
  # 基本設定
  format: html                          # html, markdown, json, xml
  directory: "./reports"                # 出力ディレクトリ
  filename_template: "schema_diff_{timestamp}"  # ファイル名テンプレート
  
  # 複数形式の同時出力
  formats: ["html", "markdown", "json"] # 複数形式を指定
```

### ファイル名テンプレート

```yaml
output:
  # 利用可能な変数
  filename_template: "{comparison_type}_{source_db}_vs_{target_db}_{timestamp}"
  
  # 変数の説明:
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
  # {comparison_type} - 比較タイプ (daily, release, etc.)
```

### ディレクトリ構成

```yaml
output:
  directory: "./reports"
  
  # サブディレクトリの自動作成
  create_subdirectories: true
  subdirectory_template: "{date}/{comparison_type}"
  
  # 例: ./reports/20250715/daily/schema_diff_production_vs_staging_143022.html
```

## 🌐 HTML出力設定

### 基本HTML設定

```yaml
html_output:
  # テンプレート設定
  template: "templates/custom-html-template.html"
  stylesheet: "assets/custom-styles.css"
  include_assets: true                  # CSS/JSファイルの埋め込み
  
  # 表示オプション
  show_identical: false                 # 同一項目の表示
  expand_details: true                  # 詳細の自動展開
  include_sql: true                     # SQL文の表示
  interactive_features: true            # インタラクティブ機能
  
  # 色テーマ
  theme:
    primary_color: "#007bff"
    success_color: "#28a745"            # 追加項目
    warning_color: "#ffc107"            # 変更項目
    danger_color: "#dc3545"             # 削除項目
    info_color: "#17a2b8"               # 情報項目
```

### HTMLテンプレートのカスタマイズ

```html
<!-- templates/company-template.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{report_title}} - {{company_name}}</title>
    <link rel="stylesheet" href="{{stylesheet_url}}">
    <style>
        /* カスタムスタイル */
        .company-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .diff-summary {
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 20px 0;
        }
        
        .critical-change {
            background-color: #fff5f5;
            border: 1px solid #fc8181;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <header class="company-header">
        <img src="{{company_logo}}" alt="{{company_name}}" height="50">
        <h1>{{report_title}}</h1>
        <p>生成日時: {{generated_at}} | バージョン: {{pgsd_version}}</p>
    </header>
    
    <main class="container">
        <div class="diff-summary">
            <h2>📊 比較サマリー</h2>
            {{summary_section}}
        </div>
        
        <div class="diff-details">
            <h2>🔍 詳細差分</h2>
            {{details_section}}
        </div>
        
        {{#if critical_changes}}
        <div class="critical-change">
            <h3>🚨 重要な変更</h3>
            {{critical_changes_section}}
        </div>
        {{/if}}
    </main>
    
    <footer>
        <p>© {{company_name}} - {{contact_info}}</p>
        <p>機密情報 - 社外秘</p>
    </footer>
    
    <script src="{{javascript_url}}"></script>
</body>
</html>
```

### CSSカスタマイズ

```css
/* assets/company-styles.css */
:root {
  --primary-color: #2c3e50;
  --secondary-color: #3498db;
  --success-color: #27ae60;
  --warning-color: #f39c12;
  --danger-color: #e74c3c;
  --info-color: #9b59b6;
}

/* レスポンシブデザイン */
@media (max-width: 768px) {
  .diff-table {
    font-size: 0.8em;
    overflow-x: auto;
  }
  
  .container {
    padding: 10px;
  }
  
  .company-header h1 {
    font-size: 1.5em;
  }
}

/* 差分表示 */
.diff-added {
  background-color: #d4edda;
  border-left: 4px solid var(--success-color);
  padding: 8px 12px;
  margin: 4px 0;
}

.diff-removed {
  background-color: #f8d7da;
  border-left: 4px solid var(--danger-color);
  padding: 8px 12px;
  margin: 4px 0;
}

.diff-modified {
  background-color: #fff3cd;
  border-left: 4px solid var(--warning-color);
  padding: 8px 12px;
  margin: 4px 0;
}

/* アクセシビリティ対応 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* 印刷スタイル */
@media print {
  .no-print {
    display: none;
  }
  
  .company-header {
    background: none !important;
    color: black !important;
  }
}
```

## 📝 Markdown出力設定

### 基本Markdown設定

```yaml
markdown_output:
  # テンプレート
  template: "templates/custom-markdown.md"
  
  # GitHub Pages対応
  github_pages:
    enabled: true
    front_matter:
      layout: "report"
      title: "Schema Comparison Report"
      date: "{timestamp}"
      categories: ["database", "schema", "comparison"]
      tags: ["postgresql", "pgsd"]
  
  # 出力オプション
  include_toc: true                     # 目次の生成
  toc_depth: 3                          # 目次の深さ
  section_numbers: true                 # セクション番号
  syntax_highlighting: true             # シンタックスハイライト
  line_breaks: "github"                 # 改行スタイル (github, standard)
  
  # 追加情報
  metadata:
    author: "{{user_name}}"
    company: "{{company_name}}"
    environment: "{{environment}}"
```

### Markdownテンプレート

```markdown
<!-- templates/company-markdown.md -->
---
title: "{{report_title}}"
author: "{{author}}"
date: "{{generated_at}}"
company: "{{company_name}}"
classification: "社外秘"
---

# {{company_name}} データベーススキーマ分析レポート

**レポート日時:** {{generated_at}}  
**生成者:** {{author}}  
**環境:** {{environment}}  
**PGSDバージョン:** {{pgsd_version}}

---

## 🎯 エグゼクティブサマリー

{{executive_summary}}

### 主要な変更点

{{#if has_critical_changes}}
⚠️ **重要:** このレポートには重要な変更が含まれています。
{{/if}}

{{summary_statistics}}

---

## 📊 比較対象

| 項目 | ソース | ターゲット |
|------|--------|------------|
| ホスト | {{source_host}} | {{target_host}} |
| データベース | {{source_database}} | {{target_database}} |
| スキーマ | {{source_schema}} | {{target_schema}} |
| 接続時刻 | {{source_connected_at}} | {{target_connected_at}} |

---

## 🔍 詳細分析

{{detailed_analysis}}

### テーブル変更

{{table_changes}}

### カラム変更

{{column_changes}}

### インデックス変更

{{index_changes}}

### 制約変更

{{constraint_changes}}

---

## 📋 推奨アクション

{{recommended_actions}}

---

## 📎 技術詳細

### 実行されたSQL

```sql
{{executed_queries}}
```

### 比較設定

```yaml
{{comparison_config}}
```

---

**注意:** このレポートは{{company_name}}の機密情報です。社外への開示は禁止されています。

*生成ツール: PGSD v{{pgsd_version}}*
```

## 📊 JSON出力設定

### JSON構造の最適化

```yaml
json_output:
  # 出力構造
  format_version: "2.0"                 # JSONスキーマバージョン
  pretty_print: true                    # 整形出力
  include_metadata: true                # メタデータの包含
  
  # データ圧縮
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

### JSONスキーマ定義

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PGSD Schema Comparison Report",
  "type": "object",
  "required": ["metadata", "summary", "differences"],
  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "generated_at": {"type": "string", "format": "date-time"},
        "pgsd_version": {"type": "string"},
        "source": {"$ref": "#/definitions/database_info"},
        "target": {"$ref": "#/definitions/database_info"}
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_differences": {"type": "integer", "minimum": 0},
        "severity_breakdown": {
          "type": "object",
          "properties": {
            "critical": {"type": "integer", "minimum": 0},
            "warning": {"type": "integer", "minimum": 0},
            "info": {"type": "integer", "minimum": 0}
          }
        }
      }
    }
  },
  "definitions": {
    "database_info": {
      "type": "object",
      "properties": {
        "host": {"type": "string"},
        "database": {"type": "string"},
        "schema": {"type": "string"},
        "connected_at": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

## 🗂️ XML出力設定

### XML構造の設定

```yaml
xml_output:
  # XML設定
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

### XML変換スタイルシート

```xsl
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" 
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rep="https://pgsd.org/schema/report/v2.0">
  
  <xsl:output method="html" indent="yes" encoding="UTF-8"/>
  
  <xsl:template match="/">
    <html>
      <head>
        <title>Schema Comparison Report</title>
        <style>
          .critical { color: #dc3545; font-weight: bold; }
          .warning { color: #ffc107; font-weight: bold; }
          .info { color: #17a2b8; }
          .summary-table { border-collapse: collapse; width: 100%; }
          .summary-table th, .summary-table td { 
            border: 1px solid #ddd; 
            padding: 8px; 
            text-align: left; 
          }
        </style>
      </head>
      <body>
        <h1>Schema Comparison Report</h1>
        
        <h2>Summary</h2>
        <table class="summary-table">
          <tr>
            <th>Category</th>
            <th>Identical</th>
            <th>Modified</th>
            <th>Added</th>
            <th>Removed</th>
          </tr>
          <xsl:for-each select="//rep:summary/rep:categories/rep:category">
            <tr>
              <td><xsl:value-of select="@name"/></td>
              <td><xsl:value-of select="rep:identical"/></td>
              <td><xsl:value-of select="rep:modified"/></td>
              <td><xsl:value-of select="rep:added"/></td>
              <td><xsl:value-of select="rep:removed"/></td>
            </tr>
          </xsl:for-each>
        </table>
        
        <h2>Critical Changes</h2>
        <xsl:for-each select="//rep:change[@severity='critical']">
          <div class="critical">
            <xsl:value-of select="@type"/>: <xsl:value-of select="text()"/>
          </div>
        </xsl:for-each>
        
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
```

## 📁 ファイル管理設定

### アーカイブ設定

```yaml
file_management:
  # 自動アーカイブ
  auto_archive:
    enabled: true
    older_than_days: 30                 # 30日以上古いファイル
    archive_format: "tar.gz"            # zip, tar.gz, tar.bz2
    archive_directory: "./archive"      # アーカイブ先
  
  # ファイル削除
  auto_cleanup:
    enabled: true
    older_than_days: 90                 # 90日以上古いファイル
    keep_count: 100                     # 最新100ファイルは保持
  
  # バックアップ
  backup:
    enabled: true
    backup_location: "s3://my-bucket/pgsd-reports"
    backup_frequency: "daily"           # daily, weekly, monthly
```

### ディレクトリ構成の自動管理

```yaml
directory_management:
  # 自動ディレクトリ作成
  auto_create_directories: true
  
  # ディレクトリ構造テンプレート
  structure_template: |
    {base_directory}/
    ├── {year}/
    │   ├── {month}/
    │   │   ├── {day}/
    │   │   │   ├── {comparison_type}/
    │   │   │   │   ├── {format}/
    │   │   │   │   │   └── {filename}
  
  # パーミッション設定
  directory_permissions: "755"
  file_permissions: "644"
```

## 🔧 出力最適化

### パフォーマンス最適化

```yaml
performance_optimization:
  # 並列出力
  parallel_output:
    enabled: true
    max_workers: 4                      # 並列ワーカー数
  
  # メモリ使用量制限
  memory_limits:
    max_memory_per_format: "500MB"      # フォーマット毎の最大メモリ
    streaming_threshold: "100MB"        # ストリーミング開始閾値
  
  # キャッシュ設定
  caching:
    template_cache: true                # テンプレートキャッシュ
    asset_cache: true                   # アセットキャッシュ
    cache_ttl: 3600                     # キャッシュ有効時間（秒）
```

### 圧縮設定

```yaml
compression:
  # 出力ファイルの圧縮
  compress_output:
    enabled: true
    formats: ["html", "xml"]            # 圧縮対象フォーマット
    compression_level: 6                # 圧縮レベル (1-9)
    
  # 画像の最適化
  image_optimization:
    enabled: true
    max_width: 1200                     # 最大幅
    quality: 85                         # 品質 (1-100)
    format: "webp"                      # 出力形式
```

## 📱 レスポンシブ対応

### モバイル最適化

```yaml
responsive_design:
  # モバイル対応
  mobile_optimization:
    enabled: true
    viewport_meta: true                 # viewportメタタグ
    touch_friendly: true                # タッチフレンドリー
    
  # ブレークポイント
  breakpoints:
    mobile: "480px"
    tablet: "768px"
    desktop: "1024px"
    wide: "1200px"
  
  # モバイル専用機能
  mobile_features:
    collapsible_sections: true          # セクションの折りたたみ
    simplified_tables: true             # テーブルの簡素化
    swipe_navigation: true              # スワイプナビゲーション
```

## 🚀 次のステップ

出力設定を理解したら：

1. **[カスタムテンプレート](../advanced/custom_templates.md)** - 高度なテンプレートカスタマイズ
2. **[自動化機能](../features/automation.md)** - 出力の自動化と配信
3. **[API統合](../advanced/api_integration.md)** - 外部システムとの連携

## 📚 関連資料

- [HTMLテンプレート仕様](../reference/html_template_spec.md)
- [JSONスキーマリファレンス](../reference/json_schema.md)
- [トラブルシューティング](../troubleshooting/output_issues.md)