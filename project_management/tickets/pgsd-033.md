# PGSD-033: CLI引数でsource/targetのスキーマ名を個別指定可能にする

## 📋 基本情報

- **チケット番号**: PGSD-033
- **タイトル**: CLI引数でsource/targetのスキーマ名を個別指定可能にする
- **種別**: 機能追加 (Feature)
- **優先度**: Middle
- **作成日**: 2025-07-15
- **担当者**: システム開発チーム
- **推定工数**: 3時間
- **ステータス**: DONE
- **完了日**: 2025-07-15

## 📝 要件詳細

### 背景
現在のCLI実装では、`--schema`オプションが1つしかなく、sourceとtargetの両方に同じスキーマ名が適用される。異なるスキーマ名を持つデータベース間の比較ができない。

### 現在の仕様
```bash
# 現在の実装（両方のDBで同じスキーマ名を使用）
pgsd compare --source-db db1 --target-db db2 --schema public
```

### 要求仕様
```bash
# 新しい実装（個別にスキーマ名を指定可能）
pgsd compare --source-db db1 --target-db db2 --source-schema public --target-schema staging

# 後方互換性のため、既存の--schemaも維持
pgsd compare --source-db db1 --target-db db2 --schema public
# この場合、両方のDBでpublicスキーマを使用
```

## 🎯 実装方針

### 1. CLI引数の追加
- `--source-schema`: ソースデータベースのスキーマ名を指定
- `--target-schema`: ターゲットデータベースのスキーマ名を指定
- 既存の`--schema`オプションは後方互換性のため維持

### 2. 優先順位ルール
1. `--source-schema`/`--target-schema`が指定されている場合、それを使用
2. 個別指定がない場合、`--schema`の値を使用
3. どちらも指定されていない場合、デフォルト値（public）を使用

### 3. 設定ファイルのサポート
```yaml
source_db:
  host: "localhost"
  database: "production"
  schema: "public"  # 個別指定

target_db:
  host: "localhost"
  database: "staging"
  schema: "staging"  # 個別指定
```

## 📝 実装タスク

### 必須タスク
- [x] CLI引数パーサーに`--source-schema`と`--target-schema`を追加
- [x] CompareCommandでの引数処理を更新
- [x] 後方互換性の確保（既存の`--schema`オプションの維持）
- [x] 設定ファイルでの個別スキーマ指定のサポート確認

### オプションタスク
- [x] ヘルプメッセージの更新
- [ ] ユーザーマニュアルの更新
- [x] 統合テストの追加

## 🧪 テスト計画

### 1. 基本機能テスト
```bash
# 個別スキーマ指定
pgsd compare --source-host localhost --source-db db1 --source-schema public \
             --target-host localhost --target-db db2 --target-schema staging

# 後方互換性テスト（既存の--schema使用）
pgsd compare --source-host localhost --source-db db1 \
             --target-host localhost --target-db db2 --schema public

# 混在使用（--schemaと個別指定）
pgsd compare --source-host localhost --source-db db1 --schema public \
             --target-host localhost --target-db db2 --target-schema staging
```

### 2. 設定ファイルテスト
```bash
# 設定ファイルで個別スキーマ指定
pgsd compare --config config/multi_schema.yaml

# 設定ファイル + CLI引数のオーバーライド
pgsd compare --config config/base.yaml --target-schema override_schema
```

## 🚀 完了条件

1. **機能要件**
   - `--source-schema`と`--target-schema`オプションが動作する
   - 既存の`--schema`オプションが引き続き動作する
   - 設定ファイルで個別スキーマ指定が可能

2. **品質要件**
   - 後方互換性が保たれている
   - ヘルプメッセージが更新されている
   - テストケースが追加されている

3. **ドキュメント**
   - CLIリファレンスが更新されている
   - 使用例が追加されている

## 📚 参考情報

### 関連ファイル
- `src/pgsd/cli/main.py`: CLI引数定義
- `src/pgsd/cli/commands.py`: CompareCommand実装
- `src/pgsd/config/schema.py`: 設定スキーマ定義
- `docs/user_manual/reference/cli_commands.md`: CLIドキュメント

### 関連チケット
- PGSD-025: CLI実装（完了）
- PGSD-032: 設定システムの不整合修正（完了）

---
**チケット作成者**: Claude Assistant  
**最終更新**: 2025-07-15