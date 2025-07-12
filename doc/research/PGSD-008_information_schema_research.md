# PGSD-008: information_schema詳細調査レポート

## 調査概要
- **チケットID**: PGSD-008
- **調査日**: 2025-07-12
- **調査者**: Claude
- **目的**: PostgreSQLのinformation_schemaを使用したスキーマ情報取得方法の確立

---

## 1. information_schema.tables

### 概要
データベース内のすべてのテーブルとビューの情報を格納

### 主要カラム
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| table_catalog | varchar | データベース名 |
| table_schema | varchar | スキーマ名 |
| table_name | varchar | テーブル名 |
| table_type | varchar | 'BASE TABLE' または 'VIEW' |

### サンプルクエリ
```sql
-- 特定スキーマのテーブル一覧取得
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

---

## 2. information_schema.columns

### 概要
テーブルのカラム情報を格納

### 主要カラム
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| table_schema | varchar | スキーマ名 |
| table_name | varchar | テーブル名 |
| column_name | varchar | カラム名 |
| ordinal_position | integer | カラムの順序 |
| column_default | varchar | デフォルト値 |
| is_nullable | varchar | 'YES' または 'NO' |
| data_type | varchar | データ型 |
| character_maximum_length | integer | 文字列の最大長 |
| numeric_precision | integer | 数値の精度 |
| numeric_scale | integer | 数値の位取り |

### サンプルクエリ
```sql
-- テーブルのカラム情報取得
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length,
    numeric_precision,
    numeric_scale
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'users'
ORDER BY ordinal_position;
```

---

## 3. information_schema.table_constraints

### 概要
テーブルの制約情報を格納

### 主要カラム
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| constraint_schema | varchar | 制約のスキーマ名 |
| constraint_name | varchar | 制約名 |
| table_schema | varchar | テーブルのスキーマ名 |
| table_name | varchar | テーブル名 |
| constraint_type | varchar | 制約タイプ |

### 制約タイプ
- `PRIMARY KEY`
- `FOREIGN KEY`
- `UNIQUE`
- `CHECK`

### サンプルクエリ
```sql
-- テーブルの制約一覧取得
SELECT 
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'public' 
  AND table_name = 'users'
ORDER BY constraint_type, constraint_name;
```

---

## 4. information_schema.key_column_usage

### 概要
キー制約に含まれるカラムの情報を格納

### 主要カラム
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| constraint_schema | varchar | 制約のスキーマ名 |
| constraint_name | varchar | 制約名 |
| table_schema | varchar | テーブルのスキーマ名 |
| table_name | varchar | テーブル名 |
| column_name | varchar | カラム名 |
| ordinal_position | integer | 制約内での順序 |

### サンプルクエリ
```sql
-- PRIMARY KEY構成カラムの取得
SELECT 
    tc.constraint_name,
    kcu.column_name,
    kcu.ordinal_position
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.table_schema = 'public'
  AND tc.table_name = 'users'
  AND tc.constraint_type = 'PRIMARY KEY'
ORDER BY kcu.ordinal_position;
```

---

## 5. information_schema.referential_constraints

### 概要
外部キー制約の参照関係情報を格納

### 主要カラム
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| constraint_schema | varchar | 制約のスキーマ名 |
| constraint_name | varchar | 外部キー制約名 |
| unique_constraint_schema | varchar | 参照先スキーマ名 |
| unique_constraint_name | varchar | 参照先制約名 |
| match_option | varchar | マッチオプション |
| update_rule | varchar | 更新時の動作 |
| delete_rule | varchar | 削除時の動作 |

### ルールの種類
- `CASCADE`
- `SET NULL`
- `SET DEFAULT`
- `RESTRICT`
- `NO ACTION`

### サンプルクエリ
```sql
-- 外部キーの詳細情報取得
SELECT 
    rc.constraint_name,
    rc.update_rule,
    rc.delete_rule,
    kcu.column_name AS fk_column,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column
FROM information_schema.referential_constraints rc
JOIN information_schema.key_column_usage kcu
    ON rc.constraint_name = kcu.constraint_name
    AND rc.constraint_schema = kcu.constraint_schema
JOIN information_schema.constraint_column_usage ccu
    ON rc.unique_constraint_name = ccu.constraint_name
    AND rc.unique_constraint_schema = ccu.constraint_schema
WHERE kcu.table_schema = 'public'
  AND kcu.table_name = 'orders';
```

---

## 6. information_schema.views

### 概要
ビューの定義情報を格納

### 主要カラム
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| table_schema | varchar | ビューのスキーマ名 |
| table_name | varchar | ビュー名 |
| view_definition | text | ビュー定義SQL |

### サンプルクエリ
```sql
-- ビュー定義の取得
SELECT 
    table_name,
    view_definition
FROM information_schema.views
WHERE table_schema = 'public'
ORDER BY table_name;
```

---

## 7. スキーマ差分検出用統合クエリ

### 完全なスキーマ情報取得クエリ

```sql
-- 1. テーブル情報
WITH tables AS (
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = $1  -- パラメータ: スキーマ名
      AND table_type = 'BASE TABLE'
),
-- 2. カラム情報
columns AS (
    SELECT 
        c.table_name,
        c.column_name,
        c.ordinal_position,
        c.data_type,
        c.is_nullable,
        c.column_default,
        c.character_maximum_length,
        c.numeric_precision,
        c.numeric_scale
    FROM information_schema.columns c
    WHERE c.table_schema = $1
),
-- 3. 制約情報
constraints AS (
    SELECT 
        tc.table_name,
        tc.constraint_name,
        tc.constraint_type,
        string_agg(kcu.column_name, ',' ORDER BY kcu.ordinal_position) AS columns
    FROM information_schema.table_constraints tc
    LEFT JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.table_schema = $1
    GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
),
-- 4. 外部キー詳細
foreign_keys AS (
    SELECT 
        kcu.table_name,
        rc.constraint_name,
        kcu.column_name,
        ccu.table_name AS ref_table,
        ccu.column_name AS ref_column,
        rc.update_rule,
        rc.delete_rule
    FROM information_schema.referential_constraints rc
    JOIN information_schema.key_column_usage kcu
        ON rc.constraint_name = kcu.constraint_name
        AND rc.constraint_schema = kcu.constraint_schema
    JOIN information_schema.constraint_column_usage ccu
        ON rc.unique_constraint_name = ccu.constraint_name
        AND rc.unique_constraint_schema = ccu.constraint_schema
    WHERE kcu.table_schema = $1
)
-- 結果の統合
SELECT 
    'TABLE' as object_type,
    t.table_name as object_name,
    NULL as details
FROM tables t
UNION ALL
SELECT 
    'COLUMN' as object_type,
    c.table_name || '.' || c.column_name as object_name,
    json_build_object(
        'data_type', c.data_type,
        'is_nullable', c.is_nullable,
        'column_default', c.column_default,
        'position', c.ordinal_position
    )::text as details
FROM columns c
UNION ALL
SELECT 
    'CONSTRAINT' as object_type,
    c.table_name || '.' || c.constraint_name as object_name,
    json_build_object(
        'constraint_type', c.constraint_type,
        'columns', c.columns
    )::text as details
FROM constraints c
ORDER BY object_type, object_name;
```

---

## まとめ

### 利点
1. **標準化**: SQL標準に準拠し、移植性が高い
2. **構造化**: 正規化されたテーブル構造で情報取得が容易
3. **完全性**: 基本的なスキーマ情報はすべて取得可能

### 制限事項
1. PostgreSQL固有の機能（GINインデックス、パーティション等）は取得不可
2. インデックスの詳細情報は限定的
3. トリガー、関数の詳細は取得困難

### 推奨事項
- 基本的なスキーマ構造の差分検出にはinformation_schemaで十分
- 将来的にPostgreSQL固有機能対応が必要な場合はpg_catalogの併用を検討
- パフォーマンスを考慮し、必要な情報のみを選択的に取得

---

## 関連ドキュメント
- [PGSD-005: スキーマ情報取得方法の調査レポート](./PGSD-005_schema_info_method_research.md)
- [要件定義書](../requirements/REQUIREMENTS.md)

---

更新日: 2025-07-12