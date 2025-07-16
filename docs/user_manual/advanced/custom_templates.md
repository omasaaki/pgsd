# カスタムテンプレート

PGSDのレポートテンプレートをカスタマイズして、組織のニーズに合わせたレポートを作成する方法について説明します。

## 🎯 この章で学ぶこと

- テンプレートエンジンの理解
- HTMLテンプレートのカスタマイズ
- Markdownテンプレートの作成
- 動的コンテンツの生成

## 🎨 テンプレートエンジンの基礎

### テンプレート言語

PGSDはJinja2テンプレートエンジンを使用しています：

```html
<!-- 基本的な変数展開 -->
<h1>{{report_title}}</h1>
<p>生成日時: {{generated_at}}</p>

<!-- 条件分岐 -->
{% if critical_changes %}
<div class="alert alert-danger">
  重要な変更が{{critical_changes|length}}件あります
</div>
{% endif %}

<!-- ループ処理 -->
{% for table in modified_tables %}
<h3>テーブル: {{table.name}}</h3>
<ul>
  {% for change in table.changes %}
  <li>{{change.description}}</li>
  {% endfor %}
</ul>
{% endfor %}

<!-- フィルタの使用 -->
<p>ファイルサイズ: {{file_size|filesizeformat}}</p>
<p>日時: {{timestamp|strftime('%Y-%m-%d %H:%M:%S')}}</p>
```

### 利用可能な変数

```yaml
# テンプレートで使用可能な変数
template_variables:
  # メタデータ
  metadata:
    generated_at: "2025-07-15T14:30:22Z"
    pgsd_version: "1.0.0"
    report_title: "Schema Comparison Report"
    user_name: "database_admin"
    
  # データベース情報
  source_database:
    host: "production.company.com"
    database: "myapp_production"
    schema: "public"
    connected_at: "2025-07-15T14:30:15Z"
  
  target_database:
    host: "staging.company.com"
    database: "myapp_staging"
    schema: "public"
    connected_at: "2025-07-15T14:30:16Z"
  
  # 比較結果
  summary:
    total_differences: 42
    severity_breakdown:
      critical: 3
      warning: 15
      info: 24
    
    categories:
      tables:
        identical: 15
        modified: 3
        added: 1
        removed: 0
  
  # 詳細差分
  differences:
    tables:
      added: [...]
      removed: [...]
      modified: [...]
    columns:
      added: [...]
      removed: [...]
      modified: [...]
```

## 🌐 HTMLテンプレートのカスタマイズ

### 基本HTMLテンプレート

```html
<!-- templates/custom-html-report.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{report_title}} - {{company_name}}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{custom_css_url}}">
    <style>
        :root {
            --primary-color: {{theme.primary_color|default('#007bff')}};
            --success-color: {{theme.success_color|default('#28a745')}};
            --warning-color: {{theme.warning_color|default('#ffc107')}};
            --danger-color: {{theme.danger_color|default('#dc3545')}};
        }
        
        .company-header {
            background: linear-gradient(135deg, var(--primary-color) 0%, #6f42c1 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        
        .summary-card {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        
        .diff-item {
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        
        .diff-added {
            background-color: #d4edda;
            border-left-color: var(--success-color);
        }
        
        .diff-removed {
            background-color: #f8d7da;
            border-left-color: var(--danger-color);
        }
        
        .diff-modified {
            background-color: #fff3cd;
            border-left-color: var(--warning-color);
        }
        
        @media print {
            .no-print { display: none; }
            .company-header { background: none !important; color: black !important; }
        }
    </style>
</head>
<body>
    <!-- ヘッダー -->
    <header class="company-header">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-2">
                    {% if company_logo %}
                    <img src="{{company_logo}}" alt="{{company_name}}" class="img-fluid" style="max-height: 60px;">
                    {% endif %}
                </div>
                <div class="col-md-8 text-center">
                    <h1 class="mb-0">{{report_title}}</h1>
                    <p class="mb-0">{{source_database.host}} vs {{target_database.host}}</p>
                </div>
                <div class="col-md-2 text-end">
                    <small>{{generated_at|strftime('%Y-%m-%d %H:%M:%S')}}</small>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- エグゼクティブサマリー -->
        <section class="mb-5">
            <h2 class="mb-4">📊 エグゼクティブサマリー</h2>
            
            <div class="row">
                <div class="col-md-3">
                    <div class="card summary-card text-center">
                        <div class="card-body">
                            <h3 class="text-primary">{{summary.total_differences}}</h3>
                            <p class="card-text">総変更数</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card summary-card text-center">
                        <div class="card-body">
                            <h3 class="text-danger">{{summary.severity_breakdown.critical}}</h3>
                            <p class="card-text">重要な変更</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card summary-card text-center">
                        <div class="card-body">
                            <h3 class="text-warning">{{summary.severity_breakdown.warning}}</h3>
                            <p class="card-text">警告レベル</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card summary-card text-center">
                        <div class="card-body">
                            <h3 class="text-info">{{summary.severity_breakdown.info}}</h3>
                            <p class="card-text">情報レベル</p>
                        </div>
                    </div>
                </div>
            </div>
            
            {% if summary.severity_breakdown.critical > 0 %}
            <div class="alert alert-danger mt-3" role="alert">
                <h4 class="alert-heading">⚠️ 注意が必要です</h4>
                <p>{{summary.severity_breakdown.critical}}件の重要な変更が検出されました。これらの変更はアプリケーションに重大な影響を与える可能性があります。</p>
                <hr>
                <p class="mb-0">詳細を確認し、適切な対応を検討してください。</p>
            </div>
            {% endif %}
        </section>

        <!-- カテゴリ別サマリー -->
        <section class="mb-5">
            <h2 class="mb-4">📋 カテゴリ別変更サマリー</h2>
            
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead class="table-dark">
                        <tr>
                            <th>カテゴリ</th>
                            <th>同一</th>
                            <th>変更</th>
                            <th>追加</th>
                            <th>削除</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for category_name, category_data in summary.categories.items() %}
                        <tr>
                            <td><strong>{{category_name|title}}</strong></td>
                            <td><span class="badge bg-success">{{category_data.identical}}</span></td>
                            <td><span class="badge bg-warning">{{category_data.modified}}</span></td>
                            <td><span class="badge bg-primary">{{category_data.added}}</span></td>
                            <td><span class="badge bg-danger">{{category_data.removed}}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </section>

        <!-- 詳細変更内容 -->
        <section class="mb-5">
            <h2 class="mb-4">🔍 詳細変更内容</h2>
            
            <!-- テーブル変更 -->
            {% if differences.tables.added or differences.tables.removed or differences.tables.modified %}
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="mb-0">📊 テーブル変更</h3>
                </div>
                <div class="card-body">
                    <!-- 追加されたテーブル -->
                    {% if differences.tables.added %}
                    <h4 class="text-success">➕ 追加されたテーブル</h4>
                    {% for table in differences.tables.added %}
                    <div class="diff-item diff-added">
                        <strong>{{table.name}}</strong>
                        <small class="text-muted">({{table.columns|length}} カラム)</small>
                        {% if table.description %}
                        <p class="mb-0 mt-1">{{table.description}}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                    {% endif %}
                    
                    <!-- 削除されたテーブル -->
                    {% if differences.tables.removed %}
                    <h4 class="text-danger mt-4">➖ 削除されたテーブル</h4>
                    {% for table in differences.tables.removed %}
                    <div class="diff-item diff-removed">
                        <strong>{{table.name}}</strong>
                        <small class="text-muted">({{table.columns|length}} カラム)</small>
                        {% if table.description %}
                        <p class="mb-0 mt-1">{{table.description}}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                    {% endif %}
                    
                    <!-- 変更されたテーブル -->
                    {% if differences.tables.modified %}
                    <h4 class="text-warning mt-4">✏️ 変更されたテーブル</h4>
                    {% for table in differences.tables.modified %}
                    <div class="diff-item diff-modified">
                        <strong>{{table.name}}</strong>
                        <span class="badge bg-secondary ms-2">{{table.changes|length}} 変更</span>
                        
                        <div class="mt-2">
                            {% for change in table.changes %}
                            <div class="change-detail">
                                <small class="badge bg-{{change.severity_color|default('secondary')}}">
                                    {{change.type}}
                                </small>
                                {{change.description}}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                    {% endif %}
                </div>
            </div>
            {% endif %}
            
            <!-- カラム変更 -->
            {% if differences.columns.added or differences.columns.removed or differences.columns.modified %}
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="mb-0">📋 カラム変更</h3>
                </div>
                <div class="card-body">
                    <!-- 追加されたカラム -->
                    {% if differences.columns.added %}
                    <h4 class="text-success">➕ 追加されたカラム</h4>
                    {% for column in differences.columns.added %}
                    <div class="diff-item diff-added">
                        <strong>{{column.table}}.{{column.name}}</strong>
                        <code class="ms-2">{{column.type}}</code>
                        {% if not column.nullable %}<span class="badge bg-danger ms-1">NOT NULL</span>{% endif %}
                        {% if column.default %}<span class="badge bg-info ms-1">DEFAULT: {{column.default}}</span>{% endif %}
                    </div>
                    {% endfor %}
                    {% endif %}
                    
                    <!-- 削除されたカラム -->
                    {% if differences.columns.removed %}
                    <h4 class="text-danger mt-4">➖ 削除されたカラム</h4>
                    {% for column in differences.columns.removed %}
                    <div class="diff-item diff-removed">
                        <strong>{{column.table}}.{{column.name}}</strong>
                        <code class="ms-2">{{column.type}}</code>
                        {% if column.was_used_in_constraints %}
                        <span class="badge bg-warning ms-1">制約に使用されていました</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                    {% endif %}
                    
                    <!-- 変更されたカラム -->
                    {% if differences.columns.modified %}
                    <h4 class="text-warning mt-4">✏️ 変更されたカラム</h4>
                    {% for column in differences.columns.modified %}
                    <div class="diff-item diff-modified">
                        <strong>{{column.table}}.{{column.name}}</strong>
                        <div class="mt-1">
                            {% for change in column.changes %}
                            <div class="change-detail">
                                <strong>{{change.attribute}}:</strong>
                                <code>{{change.old_value}}</code> → <code>{{change.new_value}}</code>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </section>

        <!-- 推奨アクション -->
        {% if recommendations %}
        <section class="mb-5">
            <h2 class="mb-4">💡 推奨アクション</h2>
            
            <div class="accordion" id="recommendationsAccordion">
                {% for category, actions in recommendations.items() %}
                <div class="accordion-item">
                    <h2 class="accordion-header" id="heading{{loop.index}}">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#collapse{{loop.index}}" aria-expanded="true">
                            {{category|title}} ({{actions|length}} 項目)
                        </button>
                    </h2>
                    <div id="collapse{{loop.index}}" class="accordion-collapse collapse show">
                        <div class="accordion-body">
                            {% for action in actions %}
                            <div class="recommendation-item mb-3">
                                <h5>{{action.title}}</h5>
                                <p>{{action.description}}</p>
                                {% if action.sql_commands %}
                                <h6>実行すべきSQL:</h6>
                                <pre><code>{{action.sql_commands|join('\n')}}</code></pre>
                                {% endif %}
                                {% if action.priority %}
                                <span class="badge bg-{{action.priority_color}}">優先度: {{action.priority}}</span>
                                {% endif %}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}

        <!-- メタデータ -->
        <section class="mb-5">
            <h2 class="mb-4">📄 レポート情報</h2>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">ソースデータベース</h5>
                        </div>
                        <div class="card-body">
                            <dl class="row">
                                <dt class="col-sm-4">ホスト:</dt>
                                <dd class="col-sm-8">{{source_database.host}}</dd>
                                <dt class="col-sm-4">データベース:</dt>
                                <dd class="col-sm-8">{{source_database.database}}</dd>
                                <dt class="col-sm-4">スキーマ:</dt>
                                <dd class="col-sm-8">{{source_database.schema}}</dd>
                                <dt class="col-sm-4">接続時刻:</dt>
                                <dd class="col-sm-8">{{source_database.connected_at|strftime('%Y-%m-%d %H:%M:%S')}}</dd>
                            </dl>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">ターゲットデータベース</h5>
                        </div>
                        <div class="card-body">
                            <dl class="row">
                                <dt class="col-sm-4">ホスト:</dt>
                                <dd class="col-sm-8">{{target_database.host}}</dd>
                                <dt class="col-sm-4">データベース:</dt>
                                <dd class="col-sm-8">{{target_database.database}}</dd>
                                <dt class="col-sm-4">スキーマ:</dt>
                                <dd class="col-sm-8">{{target_database.schema}}</dd>
                                <dt class="col-sm-4">接続時刻:</dt>
                                <dd class="col-sm-8">{{target_database.connected_at|strftime('%Y-%m-%d %H:%M:%S')}}</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- フッター -->
    <footer class="bg-light py-4 mt-5">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <p class="mb-0">© {{company_name}} - 機密情報</p>
                    <small class="text-muted">{{contact_info}}</small>
                </div>
                <div class="col-md-6 text-end">
                    <p class="mb-0">PGSD v{{pgsd_version}}</p>
                    <small class="text-muted">レポート生成: {{generated_at|strftime('%Y-%m-%d %H:%M:%S')}}</small>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 印刷時の調整
        window.addEventListener('beforeprint', function() {
            document.querySelectorAll('.accordion-collapse').forEach(function(element) {
                element.classList.add('show');
            });
        });
        
        window.addEventListener('afterprint', function() {
            document.querySelectorAll('.accordion-collapse').forEach(function(element) {
                element.classList.remove('show');
            });
        });
    </script>
</body>
</html>
```

## 📝 Markdownテンプレートのカスタマイズ

### 基本Markdownテンプレート

```markdown
<!-- templates/custom-markdown-report.md -->
---
title: "{{report_title}}"
author: "{{user_name}}"
date: "{{generated_at|strftime('%Y-%m-%d')}}"
company: "{{company_name}}"
classification: "機密"
environment: "{{environment}}"
source_db: "{{source_database.host}}/{{source_database.database}}"
target_db: "{{target_database.host}}/{{target_database.database}}"
---

# {{company_name}} データベーススキーマ比較レポート

**レポート作成日時:** {{generated_at|strftime('%Y年%m月%d日 %H時%M分')}}  
**作成者:** {{user_name}}  
**比較対象:** {{source_database.host}} vs {{target_database.host}}

---

## 🎯 エグゼクティブサマリー

{% if summary.total_differences == 0 %}
✅ **スキーマに差分はありません**

両データベースのスキーマは完全に一致しています。
{% else %}
📊 **合計 {{summary.total_differences}} 件の差分が検出されました**

| 重要度 | 件数 | 説明 |
|--------|------|------|
| 🚨 Critical | {{summary.severity_breakdown.critical}} | 即座に対応が必要 |
| ⚠️ Warning | {{summary.severity_breakdown.warning}} | 注意深く検証が必要 |
| ℹ️ Info | {{summary.severity_breakdown.info}} | 情報として確認 |

{% if summary.severity_breakdown.critical > 0 %}
> ⚠️ **重要:** {{summary.severity_breakdown.critical}}件の重要な変更が検出されました。  
> これらの変更はアプリケーションに重大な影響を与える可能性があります。
{% endif %}
{% endif %}

---

## 📋 カテゴリ別変更サマリー

| カテゴリ | 同一 | 変更 | 追加 | 削除 |
|----------|------|------|------|------|
{% for category_name, category_data in summary.categories.items() -%}
| {{category_name|title}} | {{category_data.identical}} | {{category_data.modified}} | {{category_data.added}} | {{category_data.removed}} |
{% endfor %}

---

## 🔍 詳細変更内容

{% if differences.tables.added or differences.tables.removed or differences.tables.modified %}
### 📊 テーブル変更

{% if differences.tables.added %}
#### ➕ 追加されたテーブル

{% for table in differences.tables.added %}
**{{table.name}}**
- カラム数: {{table.columns|length}}
- 主キー: {% if table.primary_key %}{{table.primary_key}}{% else %}なし{% endif %}
{% if table.description %}- 説明: {{table.description}}{% endif %}

{% endfor %}
{% endif %}

{% if differences.tables.removed %}
#### ➖ 削除されたテーブル

{% for table in differences.tables.removed %}
**{{table.name}}**
- 元カラム数: {{table.columns|length}}
{% if table.dependent_objects %}- 依存オブジェクト: {{table.dependent_objects|join(', ')}}{% endif %}
{% if table.data_loss_risk %}- ⚠️ データ損失リスク: {{table.data_loss_risk}}{% endif %}

{% endfor %}
{% endif %}

{% if differences.tables.modified %}
#### ✏️ 変更されたテーブル

{% for table in differences.tables.modified %}
**{{table.name}}** ({{table.changes|length}} 変更)

{% for change in table.changes %}
- **{{change.type}}**: {{change.description}}
  {% if change.severity == 'critical' %}🚨{% elif change.severity == 'warning' %}⚠️{% else %}ℹ️{% endif %}
  {% if change.sql_required %}
  ```sql
  {{change.sql_command}}
  ```
  {% endif %}
{% endfor %}

{% endfor %}
{% endif %}
{% endif %}

{% if differences.columns.added or differences.columns.removed or differences.columns.modified %}
### 📋 カラム変更

{% if differences.columns.added %}
#### ➕ 追加されたカラム

| テーブル | カラム名 | データ型 | NULL許可 | デフォルト値 |
|----------|----------|----------|----------|--------------|
{% for column in differences.columns.added -%}
| {{column.table}} | {{column.name}} | `{{column.type}}` | {% if column.nullable %}✅{% else %}❌{% endif %} | {% if column.default %}`{{column.default}}`{% else %}-{% endif %} |
{% endfor %}
{% endif %}

{% if differences.columns.removed %}
#### ➖ 削除されたカラム

| テーブル | カラム名 | 元データ型 | 影響 |
|----------|----------|------------|------|
{% for column in differences.columns.removed -%}
| {{column.table}} | {{column.name}} | `{{column.type}}` | {% if column.has_constraints %}制約あり{% else %}影響軽微{% endif %} |
{% endfor %}

{% if differences.columns.removed|selectattr('has_constraints')|list %}
> ⚠️ **注意:** 制約があるカラムの削除は、関連するオブジェクトに影響します。
{% endif %}
{% endif %}

{% if differences.columns.modified %}
#### ✏️ 変更されたカラム

{% for column in differences.columns.modified %}
**{{column.table}}.{{column.name}}**

| 属性 | 変更前 | 変更後 | 互換性 |
|------|--------|--------|--------|
{% for change in column.changes -%}
| {{change.attribute}} | `{{change.old_value}}` | `{{change.new_value}}` | {% if change.compatible %}✅{% else %}❌{% endif %} |
{% endfor %}

{% if column.migration_required %}
**マイグレーション要:**
```sql
{{column.migration_sql}}
```
{% endif %}

{% endfor %}
{% endif %}
{% endif %}

{% if differences.indexes.added or differences.indexes.removed or differences.indexes.modified %}
### 🗂️ インデックス変更

{% if differences.indexes.added %}
#### ➕ 追加されたインデックス

{% for index in differences.indexes.added %}
- **{{index.name}}** ({{index.table}})
  - カラム: {{index.columns|join(', ')}}
  - タイプ: {{index.type}}{% if index.unique %}, UNIQUE{% endif %}
  - 目的: {% if index.purpose %}{{index.purpose}}{% else %}パフォーマンス向上{% endif %}

{% endfor %}
{% endif %}

{% if differences.indexes.removed %}
#### ➖ 削除されたインデックス

{% for index in differences.indexes.removed %}
- **{{index.name}}** ({{index.table}})
  - カラム: {{index.columns|join(', ')}}
  {% if index.unique %}- ⚠️ **UNIQUE制約**: データ整合性への影響可能性{% endif %}
  {% if index.performance_impact %}- 📊 **パフォーマンス影響**: {{index.performance_impact}}{% endif %}

{% endfor %}
{% endif %}
{% endif %}

---

## 💡 推奨アクション

{% if recommendations %}
{% for category, actions in recommendations.items() %}
### {{category|title}}

{% for action in actions %}
{{loop.index}}. **{{action.title}}**
   
   {{action.description}}
   
   {% if action.priority %}
   **優先度:** {% if action.priority == 'high' %}🔴 高{% elif action.priority == 'medium' %}🟡 中{% else %}🟢 低{% endif %}
   {% endif %}
   
   {% if action.sql_commands %}
   **実行SQL:**
   ```sql
   {% for sql in action.sql_commands %}
   {{sql}}
   {% endfor %}
   ```
   {% endif %}
   
   {% if action.estimated_duration %}
   **予想実行時間:** {{action.estimated_duration}}
   {% endif %}
   
   {% if action.risks %}
   **リスク:** {{action.risks}}
   {% endif %}

{% endfor %}
{% endfor %}
{% else %}
現在のところ、特別な対応は必要ありません。通常の運用を継続してください。
{% endif %}

---

## 📊 統計情報

### 比較実行情報

| 項目 | 値 |
|------|-----|
| 実行開始時刻 | {{execution_stats.start_time|strftime('%Y-%m-%d %H:%M:%S')}} |
| 実行終了時刻 | {{execution_stats.end_time|strftime('%Y-%m-%d %H:%M:%S')}} |
| 実行時間 | {{execution_stats.duration}} |
| 分析対象テーブル数 | {{execution_stats.total_tables}} |
| 分析対象カラム数 | {{execution_stats.total_columns}} |
| 分析対象インデックス数 | {{execution_stats.total_indexes}} |

### データベース情報

#### ソースデータベース
- **ホスト:** {{source_database.host}}
- **データベース:** {{source_database.database}}
- **スキーマ:** {{source_database.schema}}
- **接続時刻:** {{source_database.connected_at|strftime('%Y-%m-%d %H:%M:%S')}}
- **PostgreSQLバージョン:** {{source_database.version}}

#### ターゲットデータベース
- **ホスト:** {{target_database.host}}
- **データベース:** {{target_database.database}}
- **スキーマ:** {{target_database.schema}}
- **接続時刻:** {{target_database.connected_at|strftime('%Y-%m-%d %H:%M:%S')}}
- **PostgreSQLバージョン:** {{target_database.version}}

---

## 📋 次のステップ

{% if summary.severity_breakdown.critical > 0 %}
### 🚨 緊急対応 (24時間以内)

1. **重要な変更の詳細確認**
   - 削除されたテーブル・カラムの影響範囲調査
   - 依存関係の確認
   - データ損失リスクの評価

2. **ステークホルダーへの連絡**
   - 開発チームへの変更通知
   - 運用チームへの影響説明
   - 必要に応じて緊急会議の開催

3. **ロールバック計画の準備**
   - 変更前状態への復元手順
   - バックアップの確認
   - 緊急時の連絡体制
{% endif %}

{% if summary.severity_breakdown.warning > 0 %}
### ⚠️ 計画的対応 (1週間以内)

1. **警告レベル変更の検証**
   - テスト環境での動作確認
   - パフォーマンス影響の測定
   - アプリケーションコードの調整

2. **移行計画の策定**
   - 段階的移行スケジュール
   - ダウンタイム最小化戦略
   - ロールバック手順の文書化
{% endif %}

### 📈 継続的改善

1. **監視体制の強化**
   - 定期的なスキーマ比較の自動化
   - 変更通知システムの構築
   - パフォーマンス監視の充実

2. **プロセス改善**
   - スキーマ変更の承認フロー見直し
   - 変更影響評価の標準化
   - ドキュメントの更新体制

---

## 🔗 関連リンク

- [データベース変更管理ガイドライン]({{guidelines_url}})
- [緊急時対応手順]({{emergency_procedures_url}})
- [パフォーマンスモニタリングダッシュボード]({{monitoring_dashboard_url}})

---

**レポート生成情報**
- **ツール:** PGSD v{{pgsd_version}}
- **設定ファイル:** {{config_file}}
- **生成時刻:** {{generated_at|strftime('%Y年%m月%d日 %H時%M分%S秒')}}

---

*このレポートは{{company_name}}の機密情報です。社外への開示は禁止されています。*
```

## 🎨 スタイルとテーマのカスタマイズ

### CSSカスタマイズファイル

```css
/* assets/custom-styles.css */
:root {
  /* カスタムカラーパレット */
  --company-primary: #1e3a8a;
  --company-secondary: #3b82f6;
  --company-accent: #f59e0b;
  --success-green: #10b981;
  --warning-orange: #f59e0b;
  --danger-red: #ef4444;
  --info-blue: #3b82f6;
  
  /* フォント設定 */
  --font-family-sans: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-family-mono: 'JetBrains Mono', 'Consolas', monospace;
  
  /* スペーシング */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* 影とボーダー */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --border-radius: 0.5rem;
}

/* ベーススタイル */
body {
  font-family: var(--font-family-sans);
  line-height: 1.6;
  color: #374151;
}

/* ヘッダーコンポーネント */
.company-header {
  background: linear-gradient(135deg, var(--company-primary) 0%, var(--company-secondary) 100%);
  position: relative;
  overflow: hidden;
}

.company-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

.company-header .container {
  position: relative;
  z-index: 1;
}

/* カードコンポーネント */
.summary-card {
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.summary-card .card-body {
  padding: var(--spacing-lg);
}

.summary-card h3 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: var(--spacing-sm);
}

/* 差分表示 */
.diff-item {
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  margin: var(--spacing-sm) 0;
  border-left: 4px solid;
  position: relative;
  transition: all 0.2s ease;
}

.diff-item:hover {
  box-shadow: var(--shadow-sm);
}

.diff-added {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-left-color: var(--success-green);
}

.diff-removed {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  border-left-color: var(--danger-red);
}

.diff-modified {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-left-color: var(--warning-orange);
}

/* テーブルスタイリング */
.table-custom {
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.table-custom thead th {
  background: var(--company-primary);
  color: white;
  font-weight: 600;
  border: none;
  padding: var(--spacing-md);
}

.table-custom tbody tr:nth-child(even) {
  background-color: #f9fafb;
}

.table-custom tbody tr:hover {
  background-color: #f3f4f6;
}

/* バッジスタイリング */
.badge-custom {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.375rem 0.75rem;
  border-radius: 9999px;
}

.badge-success {
  background-color: var(--success-green);
  color: white;
}

.badge-warning {
  background-color: var(--warning-orange);
  color: white;
}

.badge-danger {
  background-color: var(--danger-red);
  color: white;
}

.badge-info {
  background-color: var(--info-blue);
  color: white;
}

/* コードブロック */
pre, code {
  font-family: var(--font-family-mono);
  font-size: 0.875rem;
}

pre {
  background: #1f2937;
  color: #f9fafb;
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  overflow-x: auto;
}

code {
  background: #f3f4f6;
  color: #1f2937;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
}

pre code {
  background: none;
  color: inherit;
  padding: 0;
}

/* アラートコンポーネント */
.alert-custom {
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  margin: var(--spacing-md) 0;
  border-left: 4px solid;
}

.alert-critical {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  border-left-color: var(--danger-red);
  color: #7f1d1d;
}

.alert-warning {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-left-color: var(--warning-orange);
  color: #78350f;
}

.alert-info {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-left-color: var(--info-blue);
  color: #1e3a8a;
}

/* レスポンシブデザイン */
@media (max-width: 768px) {
  .summary-card h3 {
    font-size: 2rem;
  }
  
  .company-header h1 {
    font-size: 1.75rem;
  }
  
  .table-responsive {
    font-size: 0.875rem;
  }
  
  .diff-item {
    padding: var(--spacing-sm);
  }
}

/* 印刷スタイル */
@media print {
  .no-print {
    display: none !important;
  }
  
  .company-header {
    background: none !important;
    color: black !important;
  }
  
  .summary-card {
    box-shadow: none !important;
    border: 1px solid #d1d5db !important;
  }
  
  .diff-item {
    box-shadow: none !important;
    page-break-inside: avoid;
  }
  
  pre {
    background: #f9fafb !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
  }
}

/* ダークモード対応 */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-color: #111827;
    --text-color: #f9fafb;
    --border-color: #374151;
  }
  
  body {
    background-color: var(--bg-color);
    color: var(--text-color);
  }
  
  .summary-card {
    background: #1f2937;
    border-color: var(--border-color);
  }
  
  .table-custom tbody tr:nth-child(even) {
    background-color: #374151;
  }
  
  .table-custom tbody tr:hover {
    background-color: #4b5563;
  }
}

/* アニメーション */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-in {
  animation: slideInUp 0.5s ease-out;
}

/* ユーティリティクラス */
.text-gradient {
  background: linear-gradient(135deg, var(--company-primary) 0%, var(--company-secondary) 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.glass-effect {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
}
```

## 🔧 テンプレート設定

### テンプレート設定ファイル

```yaml
# config/template-settings.yaml
template_settings:
  # 基本設定
  template_engine: "jinja2"
  template_directory: "templates/"
  asset_directory: "assets/"
  
  # HTML テンプレート設定
  html_templates:
    default: "custom-html-report.html"
    executive: "executive-summary.html"
    technical: "technical-details.html"
    minimal: "minimal-report.html"
    
    # テンプレート固有設定
    custom_variables:
      company_name: "Acme Corporation"
      company_logo: "assets/images/logo.png"
      contact_info: "dba-team@acme.com"
      environment: "production"
      
    # CSS とJS の包含
    include_assets:
      bootstrap_css: true
      custom_css: "assets/custom-styles.css"
      bootstrap_js: true
      custom_js: "assets/custom-scripts.js"
      
    # 機能設定
    features:
      interactive_charts: true
      collapsible_sections: true
      search_functionality: true
      export_buttons: true
  
  # Markdown テンプレート設定
  markdown_templates:
    default: "custom-markdown-report.md"
    github_pages: "github-pages-report.md"
    confluence: "confluence-report.md"
    
    # GitHub Pages 設定
    github_pages:
      enabled: true
      front_matter:
        layout: "report"
        permalink: "/reports/:year/:month/:day/:title/"
        categories: ["database", "schema"]
        tags: ["postgresql", "comparison"]
      
    # 拡張機能
    extensions:
      table_of_contents: true
      syntax_highlighting: true
      math_support: false
      mermaid_diagrams: true
  
  # 共通変数
  global_variables:
    report_version: "2.0"
    timezone: "Asia/Tokyo"
    date_format: "%Y年%m月%d日"
    time_format: "%H時%M分"
    
  # テンプレート検証
  validation:
    enabled: true
    strict_mode: false
    required_variables:
      - "report_title"
      - "generated_at"
      - "summary"
      - "differences"
```

## 🚀 次のステップ

カスタムテンプレートを理解したら：

1. **[API統合](api_integration.md)** - 外部システムとの連携
2. **[セキュリティ設定](security.md)** - セキュアなレポート生成
3. **[スクリプト活用](scripting.md)** - 高度な自動化

## 📚 関連資料

- [Jinja2テンプレート言語仕様](https://jinja.palletsprojects.com/)
- [HTMLテンプレート仕様](../reference/html_template_spec.md)
- [Markdownテンプレート仕様](../reference/markdown_template_spec.md)