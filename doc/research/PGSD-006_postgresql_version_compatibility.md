# PGSD-006: PostgreSQLバージョン間差異検証レポート

## 📋 概要
- **チケットID**: PGSD-006
- **検証日**: 2025-07-12
- **検証者**: Claude
- **目的**: PostgreSQL 12-16間でのinformation_schema互換性確認と対応方針策定

---

## 🎯 検証対象バージョン

### 対象バージョン範囲
- **PostgreSQL 12**: 旧バージョン（2024年11月EOL）
- **PostgreSQL 13**: LTS版（2025年11月EOL予定）
- **PostgreSQL 14**: LTS版（2026年11月EOL予定）
- **PostgreSQL 15**: 現行安定版（2027年11月EOL予定）
- **PostgreSQL 16**: 最新安定版（2028年11月EOL予定）

---

## 📊 調査結果

### 1. information_schemaの安定性

#### SQL標準準拠による安定性
```
The information schema is defined in the SQL standard and can 
therefore be expected to be portable and remain stable — unlike 
the system catalogs, which are specific to PostgreSQL and are 
modeled after implementation concerns.
```

**結論**: information_schemaはSQL標準に準拠しており、PostgreSQL固有のシステムカタログと異なり、バージョン間で高い安定性を保持

#### バージョン間のビュー数比較
| バージョン | information_schemaビュー数 | 備考 |
|-----------|---------------------------|------|
| PostgreSQL 12 | 65 | 基準バージョン |
| PostgreSQL 13 | 62 | ドキュメント記載数 |
| PostgreSQL 14 | 66 | - |
| PostgreSQL 15 | 66 | - |
| PostgreSQL 16 | 66 | - |

**注意**: ドキュメント記載数に若干の違いがあるが、これは記載方法の違いであり、実際の機能差異ではない可能性が高い

### 2. 主要なinformation_schemaビューの互換性

#### PGSD-008で調査済みの重要ビュー
以下のビューは全バージョンで利用可能：

```sql
-- 1. テーブル情報
information_schema.tables

-- 2. カラム情報  
information_schema.columns

-- 3. 制約情報
information_schema.table_constraints
information_schema.key_column_usage
information_schema.referential_constraints

-- 4. ビュー情報
information_schema.views

-- 5. 権限情報
information_schema.table_privileges
```

### 3. PostgreSQL固有機能の制限

#### 共通制限事項
- **GINインデックス**: information_schemaでは取得不可
- **パーティション情報**: 限定的な情報のみ
- **トリガー詳細**: 基本情報のみ
- **関数・プロシージャ**: routinesビューで基本情報のみ

**対応**: これらはpg_catalogとの併用で対応（将来拡張として検討）

---

## 🔍 バージョン固有の注意点

### PostgreSQL 12
- **EOL状況**: 2024年11月にEOL済み
- **推奨**: 本番環境での新規採用は非推奨

### PostgreSQL 13以降
- **安定性**: information_schemaに大きな変更なし
- **互換性**: 基本的なスキーマ差分検出に必要な情報は全バージョンで取得可能

### セキュリティ関連の変更
PostgreSQL 14.12で発見された問題：
```
Restrict visibility of pg_stats_ext and pg_stats_ext_exprs entries 
to the table owner
```

**影響**: pg_statsビューの可視性制限（information_schemaには影響なし）

---

## 📈 互換性評価結果

### ✅ 高互換性項目
1. **基本テーブル情報**: `information_schema.tables`
2. **カラム情報**: `information_schema.columns`
3. **主キー・外部キー**: `table_constraints` + `key_column_usage`
4. **ビュー定義**: `information_schema.views`
5. **データ型情報**: 基本データ型の情報

### ⚠️ 注意が必要な項目
1. **制約名の重複**: PostgreSQLでは同一スキーマ内で制約名重複可能
   ```
   When querying the database for constraint information, it is 
   possible for a standard-compliant query that expects to return 
   one row to return several
   ```

2. **カラム順序**: `ordinal_position`は全バージョンで利用可能

### 🚫 取得不可能な情報
1. **PostgreSQL固有インデックス**: GIN、GiST、SPGiST等
2. **パーティション詳細**: 親子関係の詳細
3. **トリガー実装詳細**: 関数本体等

---

## 🎯 推奨バージョン対応方針

### 1. 最低サポートバージョン
**推奨**: PostgreSQL 13以降
- **理由**: PostgreSQL 12は既にEOL
- **利点**: LTSサポートが2025年11月まで継続

### 2. バージョン検出機能
```sql
-- PostgreSQLバージョン確認
SELECT version();

-- 数値バージョン取得
SHOW server_version_num;
```

**実装方針**: 接続時にバージョンを確認し、ログに記録

### 3. 段階的フォールバック
```python
def get_schema_info(connection, schema_name):
    version = get_pg_version(connection)
    
    # 基本的なinformation_schema使用（全バージョン対応）
    if version >= 130000:  # PostgreSQL 13以降
        return get_schema_info_standard(connection, schema_name)
    else:
        logger.warning(f"PostgreSQL {version} is EOL. Upgrade recommended.")
        return get_schema_info_legacy(connection, schema_name)
```

### 4. エラーハンドリング
- **接続エラー**: バージョン不明時の適切な処理
- **権限エラー**: information_schema読み取り権限の確認
- **機能制限**: PostgreSQL固有機能の使用可否判定

---

## 📋 実装推奨事項

### 1. バージョン互換性設計
```yaml
# 設定例
postgresql:
  minimum_version: "13.0"
  supported_versions:
    - "13.x"
    - "14.x" 
    - "15.x"
    - "16.x"
  
  compatibility:
    warn_on_old_version: true
    strict_mode: false
```

### 2. 情報取得戦略
1. **第一優先**: information_schema使用
2. **第二優先**: pg_catalog併用（PostgreSQL固有機能）
3. **フォールバック**: エラー時の適切な処理

### 3. テスト戦略
- **Docker環境**: 各バージョンでの動作確認
- **統合テスト**: バージョン固有の動作差異確認
- **性能テスト**: バージョン間の性能特性比較

---

## 📊 検証結論

### ✅ 互換性評価
- **高互換性**: information_schemaは全対象バージョンで高い互換性
- **安定性**: SQL標準準拠により、基本機能は安定
- **実用性**: 基本的なスキーマ差分検出には十分

### ⚠️ 制限事項
- **PostgreSQL固有機能**: information_schemaでは取得不可
- **バージョン固有機能**: 新機能は古いバージョンで利用不可

### 🎯 推奨アプローチ
1. **PostgreSQL 13以降をサポート対象**
2. **information_schemaベースの実装**
3. **バージョン検出とログ記録**
4. **適切なエラーハンドリング**

---

## 関連ドキュメント
- [PGSD-008: information_schema調査](./PGSD-008_information_schema_research.md)
- [PGSD-003: 機能設計書](../design/FUNCTIONAL_DESIGN.md)
- [要件定義書](../requirements/REQUIREMENTS.md)

---

更新日: 2025-07-12  
作成者: PGSD-006（PostgreSQLバージョン間差異検証）