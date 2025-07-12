# 機能設計書
**PostgreSQL Schema Diff Tool (PGSD)**

## 📋 概要
本文書は、要件定義書（FR-001〜FR-004、NFR-001〜NFR-005）に基づく詳細な機能設計を定義する。

---

## 🎯 機能一覧

### F-001: スキーマ情報取得機能
**概要**: PostgreSQLデータベースからinformation_schemaを使用してスキーマ情報を取得

#### 入力
- データベース接続情報（ホスト、ポート、データベース名、ユーザー、パスワード）
- 対象スキーマ名

#### 処理
1. PostgreSQLデータベースへの接続
2. information_schemaからの情報取得
   - `information_schema.tables`
   - `information_schema.columns`
   - `information_schema.table_constraints`
   - `information_schema.key_column_usage`
   - `information_schema.referential_constraints`
   - `information_schema.views`
3. 取得データの構造化

#### 出力
- 構造化されたスキーマ情報オブジェクト（JSON形式内部表現）

#### エラーハンドリング
- データベース接続エラー
- 認証エラー
- スキーマ存在チェック
- 権限不足エラー

---

### F-002: スキーマ差分検出機能
**概要**: 2つのスキーマ情報を比較して差分を検出

#### 入力
- スキーマ情報A（比較元）
- スキーマ情報B（比較先）

#### 処理
1. **テーブル差分検出**
   - 追加されたテーブル
   - 削除されたテーブル
   - 名前変更されたテーブル（推定）

2. **カラム差分検出**
   - 追加されたカラム
   - 削除されたカラム
   - 変更されたカラム（データ型、NULL制約、デフォルト値）

3. **制約差分検出**
   - 追加された制約
   - 削除された制約
   - 変更された制約

4. **ビュー差分検出**
   - 追加されたビュー
   - 削除されたビュー
   - 変更されたビュー定義

#### 出力
- 差分情報オブジェクト（構造化データ）

#### アルゴリズム詳細
```python
def compare_schemas(schema_a, schema_b):
    diff_result = {
        'tables': {
            'added': [],
            'removed': [],
            'modified': []
        },
        'columns': {
            'added': [],
            'removed': [],
            'modified': []
        },
        'constraints': {
            'added': [],
            'removed': [],
            'modified': []
        },
        'views': {
            'added': [],
            'removed': [],
            'modified': []
        }
    }
    
    # テーブル差分検出
    tables_a = set(schema_a.tables.keys())
    tables_b = set(schema_b.tables.keys())
    
    diff_result['tables']['added'] = list(tables_b - tables_a)
    diff_result['tables']['removed'] = list(tables_a - tables_b)
    
    # 共通テーブルの詳細比較
    common_tables = tables_a & tables_b
    for table_name in common_tables:
        table_diff = compare_table_details(
            schema_a.tables[table_name],
            schema_b.tables[table_name]
        )
        if table_diff:
            diff_result['tables']['modified'].append({
                'name': table_name,
                'changes': table_diff
            })
    
    return diff_result
```

---

### F-003: レポート生成機能
**概要**: 差分情報を指定された形式でレポートとして出力

#### 入力
- 差分情報オブジェクト
- 出力形式指定（HTML/Markdown/JSON/XML）
- 出力先パス

#### 処理フロー
1. 差分情報の解析
2. 選択された形式での変換
3. ファイル出力

#### F-003-1: HTML形式出力
**特徴**: Webブラウザで閲覧可能な見やすいレポート

```html
<!DOCTYPE html>
<html>
<head>
    <title>PostgreSQL Schema Diff Report</title>
    <style>
        .added { background-color: #d4edda; }
        .removed { background-color: #f8d7da; }
        .modified { background-color: #fff3cd; }
    </style>
</head>
<body>
    <h1>Schema Diff Report</h1>
    <h2>Summary</h2>
    <ul>
        <li>Tables Added: {count}</li>
        <li>Tables Removed: {count}</li>
        <li>Tables Modified: {count}</li>
    </ul>
    <!-- 詳細差分表示 -->
</body>
</html>
```

#### F-003-2: Markdown形式出力
**特徴**: GitHubなどでの表示に適した形式

```markdown
# PostgreSQL Schema Diff Report

## Summary
- Tables Added: {count}
- Tables Removed: {count}
- Tables Modified: {count}

## Added Tables
| Table Name | Columns | Description |
|------------|---------|-------------|
| users_new  | 5       | New user table |

## Removed Tables
| Table Name | Reason |
|------------|--------|
| old_logs   | Deprecated |
```

#### F-003-3: JSON形式出力
**特徴**: プログラムでの後処理に適した構造化データ

```json
{
  "report_metadata": {
    "generated_at": "2025-07-12T10:00:00Z",
    "schema_a": "production",
    "schema_b": "development"
  },
  "summary": {
    "tables_added": 2,
    "tables_removed": 1,
    "tables_modified": 3
  },
  "details": {
    "tables": {
      "added": [...],
      "removed": [...],
      "modified": [...]
    }
  }
}
```

#### F-003-4: XML形式出力
**特徴**: 企業システムとの連携に適した形式

```xml
<?xml version="1.0" encoding="UTF-8"?>
<schema_diff_report>
    <metadata>
        <generated_at>2025-07-12T10:00:00Z</generated_at>
        <schema_a>production</schema_a>
        <schema_b>development</schema_b>
    </metadata>
    <summary>
        <tables_added>2</tables_added>
        <tables_removed>1</tables_removed>
        <tables_modified>3</tables_modified>
    </summary>
</schema_diff_report>
```

---

### F-004: 設定管理機能
**概要**: 設定ファイルによるプログラム動作の制御

#### 設定ファイル形式（YAML）
```yaml
# pgsd_config.yaml
database:
  source:
    host: "localhost"
    port: 5432
    database: "production_db"
    username: "readonly_user"
    password: "password"
    schema: "public"
  
  target:
    host: "localhost"
    port: 5432
    database: "development_db"
    username: "readonly_user"
    password: "password"
    schema: "public"

output:
  format: "html"  # html, markdown, json, xml
  path: "./reports/"
  filename_template: "schema_diff_{timestamp}"

comparison:
  include_views: true
  include_constraints: true
  ignore_case: false
  exclude_tables:
    - "temp_*"
    - "log_*"

system:
  timezone: "UTC"
  log_level: "INFO"
  connection_timeout: 30
```

#### 設定読み込み処理
1. デフォルト設定の読み込み
2. 設定ファイルの存在確認
3. 設定値の検証
4. 環境変数による設定上書き
5. コマンドライン引数による最終上書き

---

### F-005: コマンドラインインターフェース
**概要**: コマンドラインからの実行インターフェース

#### 基本実行形式
```bash
pgsd --config config.yaml
pgsd --source-db postgresql://user:pass@host:5432/db1 \
     --target-db postgresql://user:pass@host:5432/db2 \
     --output html \
     --output-path ./reports/
```

#### オプション一覧
| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|-----------|
| --config | -c | 設定ファイルパス | ./pgsd_config.yaml |
| --source-db | -s | 比較元DB接続文字列 | - |
| --target-db | -t | 比較先DB接続文字列 | - |
| --output | -o | 出力形式 | html |
| --output-path | -p | 出力先ディレクトリ | ./reports/ |
| --verbose | -v | 詳細出力 | false |
| --quiet | -q | 静寂モード | false |
| --help | -h | ヘルプ表示 | - |
| --version | - | バージョン表示 | - |

#### 使用例
```bash
# 設定ファイルを使用した実行
pgsd --config production_config.yaml

# 直接指定での実行
pgsd -s "postgresql://user:pass@prod:5432/app" \
     -t "postgresql://user:pass@dev:5432/app" \
     -o markdown -p ./diff_reports/

# ヘルプ表示
pgsd --help
```

---

## 📊 処理フロー

### メイン処理フロー
```
1. 設定読み込み
   ↓
2. データベース接続確認
   ↓
3. スキーマ情報取得（ソース）
   ↓
4. スキーマ情報取得（ターゲット）
   ↓
5. 差分検出処理
   ↓
6. レポート生成
   ↓
7. ファイル出力
   ↓
8. 結果サマリ表示
```

### エラーハンドリングフロー
```
エラー発生
   ↓
エラー種別判定
   ├─ 接続エラー → リトライ処理
   ├─ 認証エラー → ユーザーに設定確認を促す
   ├─ 権限エラー → 必要権限の案内
   ├─ 設定エラー → 設定例の表示
   └─ その他 → 詳細ログ出力
```

---

## 🔧 非機能設計

### パフォーマンス設計
- **接続プール**: データベース接続の再利用
- **並列処理**: 複数テーブルの情報取得を並列化
- **メモリ管理**: 大規模スキーマでのメモリ使用量制御

### エラーハンドリング設計
- **段階的リトライ**: 接続エラー時の自動リトライ
- **ユーザーフレンドリーなエラーメッセージ**: 原因と対処法の明示
- **ログ出力**: デバッグ用の詳細ログ

### セキュリティ設計
- **接続情報の保護**: 設定ファイルの適切なアクセス権設定
- **SQLインジェクション対策**: パラメータクエリの使用
- **最小権限の原則**: 読み取り専用権限での動作

---

## 📁 ファイル構成（実装時の想定）

```
pgsd/
├── src/
│   ├── pgsd/
│   │   ├── __init__.py
│   │   ├── main.py              # メイン処理
│   │   ├── config.py            # 設定管理
│   │   ├── database.py          # DB接続・情報取得
│   │   ├── schema.py            # スキーマ情報モデル
│   │   ├── diff.py              # 差分検出
│   │   ├── reporter.py          # レポート生成
│   │   └── cli.py               # CLI処理
│   └── templates/               # レポートテンプレート
│       ├── html_template.html
│       └── markdown_template.md
├── config/
│   └── pgsd_config.yaml.example
└── reports/                     # 出力先
```

---

## 関連ドキュメント
- [要件定義書](../requirements/REQUIREMENTS.md)
- [PGSD-005: スキーマ情報取得方法調査](../research/PGSD-005_schema_info_method_research.md)
- [PGSD-008: information_schema調査](../research/PGSD-008_information_schema_research.md)

---

更新日: 2025-07-12  
作成者: PGSD-003（機能設計）