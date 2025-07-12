# PGSD-007: 差分検出アルゴリズム検証レポート

## 📋 概要
- **チケットID**: PGSD-007
- **検証日**: 2025-07-12
- **検証者**: Claude
- **目的**: 機能設計書で定義した差分検出アルゴリズムの妥当性と実装可能性を検証

---

## 🎯 検証対象アルゴリズム

### 基本アルゴリズム（機能設計書より）
```python
def compare_schemas(schema_a, schema_b):
    diff_result = {
        'tables': {'added': [], 'removed': [], 'modified': []},
        'columns': {'added': [], 'removed': [], 'modified': []},
        'constraints': {'added': [], 'removed': [], 'modified': []},
        'views': {'added': [], 'removed': [], 'modified': []}
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

## 🧪 検証用サンプルスキーマ設計

### スキーマA（比較元）
```sql
-- ユーザーテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 投稿テーブル
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_published ON posts(published);

-- ビュー
CREATE VIEW published_posts AS
SELECT p.*, u.username 
FROM posts p 
JOIN users u ON p.user_id = u.id 
WHERE p.published = TRUE;
```

### スキーマB（比較先）
```sql
-- ユーザーテーブル（変更）
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(60) NOT NULL UNIQUE,  -- 長さ変更: 50→60
    email VARCHAR(100) NOT NULL,
    full_name VARCHAR(200),                -- 新規カラム追加
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP                   -- 新規カラム追加
);

-- 投稿テーブル（変更）
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,         -- 新規カラム追加
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- コメントテーブル（新規追加）
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス（変更・追加）
CREATE INDEX idx_posts_user_id ON posts(user_id);
-- idx_posts_published削除
CREATE INDEX idx_posts_view_count ON posts(view_count);  -- 新規追加
CREATE INDEX idx_comments_post_id ON comments(post_id);  -- 新規追加

-- ビュー（変更）
CREATE VIEW published_posts AS
SELECT p.*, u.username, u.full_name 
FROM posts p 
JOIN users u ON p.user_id = u.id 
WHERE p.published = TRUE;
```

---

## 📊 期待される差分検出結果

### テーブル差分
```json
{
  "tables": {
    "added": ["comments"],
    "removed": [],
    "modified": [
      {
        "name": "users",
        "changes": {
          "columns": {
            "added": ["full_name", "updated_at"],
            "modified": [
              {
                "name": "username",
                "change": "character_maximum_length: 50 → 60"
              }
            ]
          }
        }
      },
      {
        "name": "posts", 
        "changes": {
          "columns": {
            "added": ["view_count"]
          }
        }
      }
    ]
  }
}
```

### カラム差分
```json
{
  "columns": {
    "added": [
      "users.full_name",
      "users.updated_at", 
      "posts.view_count",
      "comments.id",
      "comments.post_id",
      "comments.user_id",
      "comments.content",
      "comments.created_at"
    ],
    "removed": [],
    "modified": [
      {
        "name": "users.username",
        "changes": {
          "character_maximum_length": {"from": 50, "to": 60}
        }
      }
    ]
  }
}
```

### 制約差分
```json
{
  "constraints": {
    "added": [
      "comments.comments_pkey",
      "comments.comments_post_id_fkey",
      "comments.comments_user_id_fkey"
    ],
    "removed": [],
    "modified": []
  }
}
```

---

## 🔍 アルゴリズム詳細検証

### 1. テーブル比較アルゴリズム
```python
def compare_tables(schema_a, schema_b):
    """テーブルレベルの差分検出"""
    tables_a = set(schema_a.tables.keys())
    tables_b = set(schema_b.tables.keys())
    
    return {
        'added': list(tables_b - tables_a),      # B にのみ存在
        'removed': list(tables_a - tables_b),    # A にのみ存在  
        'common': list(tables_a & tables_b)      # 両方に存在
    }

# 時間計算量: O(n + m) where n=|tables_a|, m=|tables_b|
# 空間計算量: O(n + m)
```

**検証結果**: ✅ 効率的で実装も容易

### 2. カラム比較アルゴリズム
```python
def compare_columns(table_a, table_b):
    """カラムレベルの差分検出"""
    columns_a = {col.name: col for col in table_a.columns}
    columns_b = {col.name: col for col in table_b.columns}
    
    added = []
    removed = []
    modified = []
    
    # 追加・削除されたカラム
    col_names_a = set(columns_a.keys())
    col_names_b = set(columns_b.keys())
    
    added = list(col_names_b - col_names_a)
    removed = list(col_names_a - col_names_b)
    
    # 変更されたカラム
    common_cols = col_names_a & col_names_b
    for col_name in common_cols:
        col_diff = compare_column_details(columns_a[col_name], columns_b[col_name])
        if col_diff:
            modified.append({
                'name': col_name,
                'changes': col_diff
            })
    
    return {'added': added, 'removed': removed, 'modified': modified}
```

**検証結果**: ✅ 実装可能だが、カラム詳細比較の精度が重要

### 3. カラム詳細比較アルゴリズム
```python
def compare_column_details(col_a, col_b):
    """カラムの詳細属性比較"""
    changes = {}
    
    # データ型比較
    if col_a.data_type != col_b.data_type:
        changes['data_type'] = {'from': col_a.data_type, 'to': col_b.data_type}
    
    # NULL制約比較
    if col_a.is_nullable != col_b.is_nullable:
        changes['is_nullable'] = {'from': col_a.is_nullable, 'to': col_b.is_nullable}
    
    # デフォルト値比較
    if col_a.column_default != col_b.column_default:
        changes['column_default'] = {'from': col_a.column_default, 'to': col_b.column_default}
    
    # 文字列長比較
    if col_a.character_maximum_length != col_b.character_maximum_length:
        changes['character_maximum_length'] = {
            'from': col_a.character_maximum_length, 
            'to': col_b.character_maximum_length
        }
    
    # 数値精度比較
    if col_a.numeric_precision != col_b.numeric_precision:
        changes['numeric_precision'] = {
            'from': col_a.numeric_precision, 
            'to': col_b.numeric_precision
        }
    
    return changes if changes else None
```

**検証結果**: ✅ information_schemaの情報で十分対応可能

---

## ⚡ パフォーマンス分析

### 時間計算量
- **テーブル比較**: O(n + m)
- **カラム比較**: O(p × q) where p=テーブル数, q=平均カラム数
- **制約比較**: O(r) where r=制約数
- **全体**: O(p × q + r) ≈ O(テーブル数 × カラム数)

### 空間計算量
- **スキーマ情報保存**: O(総カラム数 + 総制約数)
- **差分結果保存**: O(差分の数)

### 実用性評価
```
中規模スキーマの想定：
- テーブル数: 100
- 平均カラム数: 10
- 総制約数: 200

計算量: O(100 × 10 + 200) = O(1,200)
→ 十分高速
```

**検証結果**: ✅ 実用的なパフォーマンス

---

## 🚨 エッジケース検証

### 1. テーブル名変更の検出
**課題**: 単純な集合演算では「削除+追加」として検出される

**解決案**: 
```python
def detect_table_renames(removed_tables, added_tables, similarity_threshold=0.8):
    """テーブル名変更の推定"""
    renames = []
    
    for removed in removed_tables[:]:
        for added in added_tables[:]:
            # カラム構造の類似度計算
            similarity = calculate_table_similarity(removed, added)
            if similarity >= similarity_threshold:
                renames.append({'from': removed.name, 'to': added.name})
                removed_tables.remove(removed)
                added_tables.remove(added)
                break
    
    return renames
```

**検証結果**: ⚠️ 複雑だが実装可能。初期バージョンでは対応せず将来拡張

### 2. カラム順序変更
**課題**: information_schemaの`ordinal_position`で検出可能だが重要度低

**対応**: 🔶 LOW優先度。レポートで表示するが警告レベル

### 3. 大規模スキーマでのメモリ使用量
**課題**: 1000テーブル × 20カラムで約20,000オブジェクト

**対応**: 
- ジェネレータ使用による遅延読み込み
- バッチ処理による部分比較
- メモリ監視機能

**検証結果**: ✅ 実装で対応可能

---

## 📋 検証結論

### ✅ 実装可能性
1. **基本アルゴリズム**: information_schemaベースで完全実装可能
2. **パフォーマンス**: 中規模スキーマで十分実用的
3. **精度**: 基本的な差分検出は高精度で実現可能

### ⚠️ 注意点・制限事項
1. **テーブル名変更推定**: 複雑な実装が必要
2. **PostgreSQL固有機能**: information_schemaの制限により一部対応不可
3. **大規模スキーマ**: メモリ管理の実装が必要

### 📈 実装優先度
1. **HIGH**: 基本的な追加・削除・変更検出
2. **MEDIUM**: エラーハンドリング・パフォーマンス最適化
3. **LOW**: 名前変更推定・PostgreSQL固有機能

### 🎯 推奨実装アプローチ
1. **フェーズ1**: 基本差分検出の実装
2. **フェーズ2**: パフォーマンス最適化
3. **フェーズ3**: 高度な推定機能追加

---

## 関連ドキュメント
- [機能設計書](../design/FUNCTIONAL_DESIGN.md)
- [PGSD-008: information_schema調査](./PGSD-008_information_schema_research.md)
- [要件定義書](../requirements/REQUIREMENTS.md)

---

更新日: 2025-07-12  
作成者: PGSD-007（差分検出アルゴリズム検証）