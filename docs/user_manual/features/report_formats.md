# レポート形式

PGSDが提供する様々なレポート形式について詳しく説明します。

## 🎯 この章で学ぶこと

- 利用可能なレポート形式
- 各形式の特徴と用途
- カスタマイズ方法
- 形式間の変換

## 📊 利用可能なレポート形式

### 対応形式一覧

| 形式 | 拡張子 | 用途 | 特徴 |
|------|--------|------|------|
| HTML | .html | 閲覧・プレゼンテーション | インタラクティブ、視覚的 |
| Markdown | .md | ドキュメント・Git管理 | テキストベース、バージョン管理 |
| JSON | .json | API・プログラム処理 | 構造化データ、機械可読 |
| XML | .xml | システム連携・アーカイブ | 標準的、変換容易 |

## 🌐 HTML レポート

### 特徴
- **インタラクティブな表示**: クリックで詳細展開
- **視覚的な差分表示**: 色分けとアイコン
- **検索・フィルタ機能**: ブラウザ内検索
- **レスポンシブデザイン**: モバイル対応

### 生成方法

```bash
# 基本的なHTML レポート
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --format html \
  --output ./reports
```

### 構造例

```html
<!DOCTYPE html>
<html>
<head>
    <title>Schema Diff Report - 2025-07-15</title>
    <style>
        .diff-added { background-color: #d4edda; }
        .diff-removed { background-color: #f8d7da; }
        .diff-modified { background-color: #fff3cd; }
    </style>
</head>
<body>
    <header>
        <h1>PostgreSQL Schema Comparison Report</h1>
        <div class="metadata">
            <p>Generated: 2025-07-15 14:30:22</p>
            <p>Source: production.company.com/myapp</p>
            <p>Target: staging.company.com/myapp</p>
        </div>
    </header>
    
    <section class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat-item">
                <span class="label">Tables:</span>
                <span class="value">15 identical, 3 modified, 1 added</span>
            </div>
        </div>
    </section>
    
    <section class="details">
        <h2>Detailed Differences</h2>
        <div class="table-diff">
            <h3>Table: users</h3>
            <table class="diff-table">
                <tr class="diff-added">
                    <td>+ Column: last_login_ip (inet)</td>
                </tr>
            </table>
        </div>
    </section>
</body>
</html>
```

### カスタマイズ

#### テンプレート指定
```bash
pgsd compare \
  --format html \
  --template custom-template.html \
  --output ./reports
```

#### スタイルカスタマイズ
```yaml
# config/html-config.yaml
html_output:
  template: "templates/company-template.html"
  css_file: "assets/company-styles.css"
  include_assets: true
  
  # 表示オプション
  show_identical: false
  expand_details: true
  include_sql: true
  
  # 色テーマ
  theme:
    added_color: "#28a745"
    removed_color: "#dc3545"
    modified_color: "#ffc107"
```

## 📝 Markdown レポート

### 特徴
- **Git フレンドリー**: バージョン管理に適している
- **プレーンテキスト**: エディタで直接編集可能
- **GitHub互換**: GitHub Pages等で表示可能
- **軽量**: サイズが小さい

### 生成方法

```bash
# Markdown レポート生成
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --format markdown \
  --output ./docs/schema-changes
```

### 出力例

```markdown
# PostgreSQL Schema Comparison Report

**Generated:** 2025-07-15 14:30:22  
**Source:** production.company.com/myapp  
**Target:** staging.company.com/myapp

## 📊 Summary

| Category | Identical | Modified | Added | Removed |
|----------|-----------|----------|-------|---------|
| Tables   | 15        | 3        | 1     | 0       |
| Columns  | 89        | 5        | 3     | 1       |
| Indexes  | 23        | 2        | 1     | 0       |

## 🔍 Detailed Changes

### Tables

#### ➕ Added Tables
- **new_feature_table**
  - Columns: 5
  - Primary Key: id (bigint)
  - Created: 2025-07-15

#### ✏️ Modified Tables

##### users
- ➕ **Added Column:** `last_login_ip` (inet)
  - Nullable: true
  - Default: null

- ✏️ **Modified Column:** `email`
  - Length: varchar(255) → varchar(320)
  - Reason: RFC 5321 compliance

### Indexes

#### ➕ Added Indexes
- **idx_users_last_login_ip** on users(last_login_ip)
  - Type: btree
  - Unique: false

## 📋 Migration Suggestions

```sql
-- Add new column to users table
ALTER TABLE users ADD COLUMN last_login_ip inet;

-- Modify email column length
ALTER TABLE users ALTER COLUMN email TYPE varchar(320);

-- Add new index
CREATE INDEX idx_users_last_login_ip ON users(last_login_ip);
```

## 🚨 Breaking Changes

> ⚠️ **Warning**: The following changes may require application updates:
> - Email field length increased - validate input validation rules
```

### GitHub Pages 対応

```yaml
# _config.yml (GitHub Pages)
title: "Database Schema Documentation"
description: "PostgreSQL schema comparison reports"

markdown: kramdown
highlighter: rouge
theme: minima

plugins:
  - jekyll-feed
  - jekyll-sitemap

# Collections
collections:
  schema_reports:
    output: true
    permalink: /:collection/:name/
```

## 📊 JSON レポート

### 特徴
- **構造化データ**: プログラムで処理しやすい
- **API連携**: RESTful API等との連携
- **データ分析**: BI ツール等での分析
- **変換容易**: 他形式への変換基盤

### 生成方法

```bash
# JSON レポート生成
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --format json \
  --output ./api-reports
```

### 構造例

```json
{
  "metadata": {
    "generated_at": "2025-07-15T14:30:22Z",
    "pgsd_version": "1.0.0",
    "source": {
      "host": "production.company.com",
      "database": "myapp",
      "schema": "public",
      "connected_at": "2025-07-15T14:30:15Z"
    },
    "target": {
      "host": "staging.company.com", 
      "database": "myapp",
      "schema": "public",
      "connected_at": "2025-07-15T14:30:16Z"
    },
    "comparison_options": {
      "case_sensitive": true,
      "include_comments": true,
      "include_permissions": false
    }
  },
  
  "summary": {
    "total_differences": 12,
    "severity_breakdown": {
      "critical": 0,
      "warning": 8,
      "info": 4
    },
    "categories": {
      "tables": {
        "identical": 15,
        "modified": 3,
        "added": 1,
        "removed": 0
      },
      "columns": {
        "identical": 89,
        "modified": 5,
        "added": 3,
        "removed": 1
      },
      "indexes": {
        "identical": 23,
        "modified": 2,
        "added": 1,
        "removed": 0
      }
    }
  },
  
  "differences": {
    "tables": {
      "added": [
        {
          "name": "new_feature_table",
          "columns": [
            {
              "name": "id",
              "type": "bigint",
              "nullable": false,
              "primary_key": true
            },
            {
              "name": "feature_name",
              "type": "varchar(100)",
              "nullable": false
            }
          ],
          "indexes": [
            {
              "name": "new_feature_table_pkey",
              "columns": ["id"],
              "unique": true,
              "type": "btree"
            }
          ]
        }
      ],
      "modified": [
        {
          "name": "users",
          "changes": [
            {
              "type": "column_added",
              "column": {
                "name": "last_login_ip",
                "type": "inet",
                "nullable": true,
                "default": null
              },
              "severity": "info"
            },
            {
              "type": "column_modified",
              "column": "email",
              "old_definition": {
                "type": "varchar(255)",
                "nullable": false
              },
              "new_definition": {
                "type": "varchar(320)",
                "nullable": false
              },
              "severity": "warning"
            }
          ]
        }
      ]
    }
  },
  
  "migration_suggestions": {
    "sql_commands": [
      "ALTER TABLE users ADD COLUMN last_login_ip inet;",
      "ALTER TABLE users ALTER COLUMN email TYPE varchar(320);"
    ],
    "rollback_commands": [
      "ALTER TABLE users DROP COLUMN last_login_ip;",
      "ALTER TABLE users ALTER COLUMN email TYPE varchar(255);"
    ]
  }
}
```

### API 活用例

```python
# Python での JSON レポート処理
import json
import requests

# レポート読み込み
with open('schema_diff_report.json', 'r') as f:
    report = json.load(f)

# 重要な変更のみ抽出
critical_changes = [
    diff for diff in report['differences']['tables']['modified']
    if any(change['severity'] == 'critical' for change in diff['changes'])
]

# Slack通知
if critical_changes:
    slack_message = {
        "text": f"Critical schema changes detected: {len(critical_changes)} tables affected",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {
                        "title": change['name'],
                        "value": f"{len(change['changes'])} critical changes",
                        "short": True
                    }
                    for change in critical_changes
                ]
            }
        ]
    }
    
    requests.post(SLACK_WEBHOOK_URL, json=slack_message)
```

## 🗂️ XML レポート

### 特徴
- **標準準拠**: W3C XML標準
- **スキーマ検証**: XSD による構造検証
- **変換対応**: XSLT による変換
- **エンタープライズ対応**: 企業システム連携

### 生成方法

```bash
# XML レポート生成
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --format xml \
  --output ./enterprise-reports
```

### 構造例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<schema_comparison_report xmlns="https://pgsd.org/schema/report/v1.0"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         xsi:schemaLocation="https://pgsd.org/schema/report/v1.0 report.xsd">
  
  <metadata>
    <generated_at>2025-07-15T14:30:22Z</generated_at>
    <pgsd_version>1.0.0</pgsd_version>
    
    <source>
      <host>production.company.com</host>
      <database>myapp</database>
      <schema>public</schema>
      <connected_at>2025-07-15T14:30:15Z</connected_at>
    </source>
    
    <target>
      <host>staging.company.com</host>
      <database>myapp</database>
      <schema>public</schema>
      <connected_at>2025-07-15T14:30:16Z</connected_at>
    </target>
  </metadata>
  
  <summary>
    <total_differences>12</total_differences>
    <severity_breakdown>
      <critical>0</critical>
      <warning>8</warning>
      <info>4</info>
    </severity_breakdown>
    
    <category name="tables">
      <identical>15</identical>
      <modified>3</modified>
      <added>1</added>
      <removed>0</removed>
    </category>
  </summary>
  
  <differences>
    <tables>
      <added>
        <table name="new_feature_table">
          <columns>
            <column name="id" type="bigint" nullable="false" primary_key="true"/>
            <column name="feature_name" type="varchar(100)" nullable="false"/>
          </columns>
          <indexes>
            <index name="new_feature_table_pkey" unique="true" type="btree">
              <column>id</column>
            </index>
          </indexes>
        </table>
      </added>
      
      <modified>
        <table name="users">
          <changes>
            <change type="column_added" severity="info">
              <column name="last_login_ip" type="inet" nullable="true"/>
            </change>
            <change type="column_modified" severity="warning">
              <column name="email">
                <old_definition type="varchar(255)" nullable="false"/>
                <new_definition type="varchar(320)" nullable="false"/>
              </column>
            </change>
          </changes>
        </table>
      </modified>
    </tables>
  </differences>
  
  <migration_suggestions>
    <sql_command>ALTER TABLE users ADD COLUMN last_login_ip inet;</sql_command>
    <sql_command>ALTER TABLE users ALTER COLUMN email TYPE varchar(320);</sql_command>
  </migration_suggestions>
</schema_comparison_report>
```

### XSLT 変換例

```xsl
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rep="https://pgsd.org/schema/report/v1.0">
  
  <xsl:template match="/">
    <html>
      <head>
        <title>Schema Comparison Report</title>
        <style>
          .critical { color: red; }
          .warning { color: orange; }
          .info { color: blue; }
        </style>
      </head>
      <body>
        <h1>Schema Comparison Report</h1>
        
        <h2>Summary</h2>
        <p>Total Differences: <xsl:value-of select="//rep:summary/rep:total_differences"/></p>
        
        <h2>Tables Added</h2>
        <ul>
          <xsl:for-each select="//rep:tables/rep:added/rep:table">
            <li><xsl:value-of select="@name"/></li>
          </xsl:for-each>
        </ul>
        
        <h2>Migration Commands</h2>
        <pre>
          <xsl:for-each select="//rep:migration_suggestions/rep:sql_command">
            <xsl:value-of select="."/>
            <xsl:text>&#10;</xsl:text>
          </xsl:for-each>
        </pre>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
```

## 🔄 形式間の変換

### 複数形式同時生成

```bash
# 複数形式を一度に生成
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --format html,markdown,json \
  --output ./multi-format-reports
```

### バッチ変換スクリプト

```bash
#!/bin/bash
# scripts/convert-reports.sh

INPUT_DIR="./json-reports"
OUTPUT_DIR="./converted-reports"

# JSON から他形式への変換
for json_file in "$INPUT_DIR"/*.json; do
  base_name=$(basename "$json_file" .json)
  
  # HTML 変換
  pgsd convert \
    --input "$json_file" \
    --output "$OUTPUT_DIR/${base_name}.html" \
    --format html
  
  # Markdown 変換
  pgsd convert \
    --input "$json_file" \
    --output "$OUTPUT_DIR/${base_name}.md" \
    --format markdown
  
  # XML 変換
  pgsd convert \
    --input "$json_file" \
    --output "$OUTPUT_DIR/${base_name}.xml" \
    --format xml
done
```

## 🎨 カスタマイズとテンプレート

### HTML テンプレートカスタマイズ

```html
<!-- templates/custom-report.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{{company_name}} Schema Report</title>
    <link rel="stylesheet" href="{{css_file}}">
</head>
<body>
    <header class="company-header">
        <img src="{{company_logo}}" alt="Company Logo">
        <h1>Database Schema Analysis</h1>
    </header>
    
    <main>
        {{report_content}}
    </main>
    
    <footer>
        <p>Generated by PGSD v{{pgsd_version}} on {{generated_at}}</p>
        <p>© {{company_name}} - Internal Use Only</p>
    </footer>
</body>
</html>
```

### Markdown テンプレートカスタマイズ

```markdown
<!-- templates/custom-markdown.md -->
# {{company_name}} Database Schema Analysis

**Report Date:** {{generated_at}}  
**Generated By:** {{user_name}}  
**Environment:** {{environment}}

---

## Executive Summary

{{executive_summary}}

## Technical Details

{{technical_details}}

---

*This report is confidential and proprietary to {{company_name}}.*
```

### 設定ファイルでのカスタマイズ

```yaml
# config/report-customization.yaml
report_templates:
  html:
    template_file: "templates/company-template.html"
    css_file: "assets/company-styles.css"
    variables:
      company_name: "Acme Corporation"
      company_logo: "assets/logo.png"
      environment: "Production"
  
  markdown:
    template_file: "templates/company-markdown.md"
    variables:
      company_name: "Acme Corporation"
      user_name: "Database Team"
  
  # 共通変数
  global_variables:
    generated_at: "{{timestamp}}"
    pgsd_version: "{{version}}"
```

## 📱 モバイル対応とアクセシビリティ

### レスポンシブ HTML

```css
/* assets/responsive-styles.css */
@media (max-width: 768px) {
  .diff-table {
    font-size: 0.8em;
    overflow-x: auto;
  }
  
  .summary-stats {
    flex-direction: column;
  }
  
  .details-section {
    padding: 0.5em;
  }
}

/* アクセシビリティ対応 */
.diff-added {
  background-color: #d4edda;
  border-left: 4px solid #28a745;
}

.diff-removed {
  background-color: #f8d7da; 
  border-left: 4px solid #dc3545;
}

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
```

## 🚀 次のステップ

レポート形式を理解したら：

1. **[差分解析](diff_analysis.md)** - 差分の詳細分析
2. **[自動化機能](automation.md)** - レポート生成の自動化
3. **[カスタムテンプレート](../advanced/custom_templates.md)** - 高度なカスタマイズ

## 📚 関連資料

- [設定リファレンス](../reference/config_reference.md)
- [カスタムテンプレート](../advanced/custom_templates.md)
- [API リファレンス](../reference/api_reference.md)