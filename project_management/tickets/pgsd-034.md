# PGSD-034: リポート出力方法の改善 - テーブルごとのグルーピング

## 📋 基本情報

- **チケット番号**: PGSD-034
- **タイトル**: リポート出力方法の改善 - テーブルごとのグルーピング
- **種別**: 改善 (Enhancement)
- **優先度**: Middle
- **作成日**: 2025-07-15
- **担当者**: システム開発チーム
- **推定工数**: 4時間
- **ステータス**: TODO

## 📝 要件詳細

### 背景
現在のレポート出力では、列の追加/削除/属性の修正が変更種別ごとに分類されており、同じテーブルの変更が複数の箇所に分散している。これにより、特定のテーブルの変更内容を把握しにくい。

### 現在の出力構造
```
Tables Added:
- table_a
- table_b

Tables Removed:
- table_c

Tables Modified:
- table_d

Columns Added:
- table_a.column1
- table_d.column2

Columns Removed:
- table_d.column3

Column Attributes Modified:
- table_a.column4 (type: varchar(50) → varchar(100))
```

### 改善後の出力構造
```
Schema Changes Summary:

Tables Added (2):
├─ table_a
│  ├─ Columns: column1 (varchar(50)), column4 (text)
│  └─ Indexes: idx_table_a_column1
└─ table_b
   ├─ Columns: id (integer), name (varchar(100))
   └─ Primary Key: id

Tables Removed (1):
└─ table_c

Tables Modified (1):
└─ table_d
   ├─ Columns Added: column2 (timestamp)
   ├─ Columns Removed: column3
   ├─ Column Attributes Modified:
   │  └─ column4: varchar(50) → varchar(100)
   ├─ Indexes Added: idx_table_d_column2
   └─ Constraints Modified: fk_table_d_ref (ADDED)
```

## 🎯 実装方針

### 1. レポート構造の変更
- テーブル単位でのグルーピング
- 階層構造での表示（テーブル → 変更内容）
- 変更種別の詳細化（列、インデックス、制約）

### 2. 対象出力形式
- **HTML形式**: 折りたたみ可能な階層表示
- **Markdown形式**: ツリー構造での表示
- **JSON形式**: ネストしたオブジェクト構造
- **XML形式**: 階層的なXML構造

### 3. 情報の詳細化
- テーブルレベルの変更
- 列レベルの変更（型、制約、デフォルト値）
- インデックスの変更
- 制約の変更（外部キー、チェック制約等）

## 📝 実装タスク

### 必須タスク
- [ ] レポートデータ構造の見直し
- [ ] テーブル単位でのデータ集約ロジック実装
- [ ] HTML形式レポートの階層表示対応
- [ ] Markdown形式レポートのツリー構造対応
- [ ] JSON形式レポートのネスト構造対応

### オプションタスク
- [ ] XML形式レポートの階層構造対応
- [ ] CSS改善による視認性向上
- [ ] 折りたたみ/展開機能（HTML版）
- [ ] サマリー統計情報の追加

## 🎨 出力イメージ

### HTML形式（改善後）
```html
<div class="schema-changes">
  <h2>Schema Changes Summary</h2>
  
  <div class="tables-added">
    <h3>Tables Added (2)</h3>
    <div class="table-group">
      <h4>table_a</h4>
      <ul>
        <li>Columns: column1 (varchar(50)), column4 (text)</li>
        <li>Indexes: idx_table_a_column1</li>
      </ul>
    </div>
    <div class="table-group">
      <h4>table_b</h4>
      <ul>
        <li>Columns: id (integer), name (varchar(100))</li>
        <li>Primary Key: id</li>
      </ul>
    </div>
  </div>
  
  <div class="tables-modified">
    <h3>Tables Modified (1)</h3>
    <div class="table-group">
      <h4>table_d</h4>
      <ul>
        <li>Columns Added: column2 (timestamp)</li>
        <li>Columns Removed: column3</li>
        <li>Column Attributes Modified: column4: varchar(50) → varchar(100)</li>
      </ul>
    </div>
  </div>
</div>
```

### JSON形式（改善後）
```json
{
  "schema_changes": {
    "tables_added": [
      {
        "name": "table_a",
        "columns": [
          {"name": "column1", "type": "varchar(50)"},
          {"name": "column4", "type": "text"}
        ],
        "indexes": ["idx_table_a_column1"]
      }
    ],
    "tables_modified": [
      {
        "name": "table_d",
        "changes": {
          "columns_added": [
            {"name": "column2", "type": "timestamp"}
          ],
          "columns_removed": ["column3"],
          "column_attributes_modified": [
            {
              "name": "column4",
              "old_type": "varchar(50)",
              "new_type": "varchar(100)"
            }
          ]
        }
      }
    ]
  }
}
```

## 🧪 テスト計画

### 1. 機能テスト
```bash
# 複数テーブルの変更を含む比較
pgsd compare --source-host localhost --source-db db1 \
             --target-host localhost --target-db db2 \
             --format html --output ./test_reports/

# 各形式での出力確認
pgsd compare --config config/test.yaml --format markdown
pgsd compare --config config/test.yaml --format json
pgsd compare --config config/test.yaml --format xml
```

### 2. レポート品質テスト
- テーブル単位でのグルーピングが正しく動作する
- 階層構造が適切に表示される
- 各形式で一貫した情報が出力される
- 大量のテーブル変更でもパフォーマンスが劣化しない

### 3. 後方互換性テスト
- 既存のレポート形式との互換性確認
- API呼び出し元への影響確認

## 🚀 完了条件

1. **機能要件**
   - テーブル単位でのグルーピング表示が動作する
   - 全ての出力形式で新しい構造が適用される
   - 詳細な変更情報が階層的に表示される

2. **品質要件**
   - 既存機能に影響がない
   - パフォーマンスが劣化していない
   - 視認性が向上している

3. **ドキュメント**
   - 新しい出力形式の説明が追加されている
   - サンプルレポートが更新されている

## 📚 参考情報

### 関連ファイル
- `src/pgsd/reports/`: レポート生成モジュール
- `src/pgsd/reports/html_reporter.py`: HTML形式レポート
- `src/pgsd/reports/markdown_reporter.py`: Markdown形式レポート
- `src/pgsd/reports/json_reporter.py`: JSON形式レポート
- `src/pgsd/core/analyzer.py`: 差分解析ロジック

### 関連チケット
- PGSD-022: HTML形式レポート実装（完了）
- PGSD-023: Markdown形式レポート実装（完了）
- PGSD-024: JSON/XML形式レポート実装（TODO）

### 設計考慮事項
- レポートデータ構造の変更による既存コードへの影響
- 大量データ処理時のメモリ使用量
- 各出力形式での表現能力の違い

---
**チケット作成者**: Claude Assistant  
**最終更新**: 2025-07-15