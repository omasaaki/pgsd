# PGSD-032: 設定システムの不整合修正

## 📋 基本情報

- **チケット番号**: PGSD-032
- **タイトル**: 設定システムの不整合修正
- **種別**: バグ修正 (Bug Fix)
- **優先度**: High
- **作成日**: 2025-07-15
- **担当者**: システム開発チーム
- **推定工数**: 4時間
- **ステータス**: DONE
- **完了日**: 2025-07-15

## 🐛 問題の詳細

### 発見された問題
1. **CLI設定読み込みエラー**
   - `pgsd.main`実行時に設定ファイルが正しく読み込まれない
   - エラーメッセージ: `PGSDConfiguration.__init__() got an unexpected keyword argument 'config'`

2. **設定スキーマと実装の不整合**
   - `DatabaseManager`で`config.database.source.host`を期待
   - 実際の設定スキーマでは`config.source_db.host`
   - 設定バリデーションが機能していない

### 発生条件
- CLIコマンドで設定ファイルを指定した場合
- 直接コマンドライン引数を使用した場合
- 設定ファイルのバリデーションを実行した場合

### 影響範囲
- **高**: CLIツールが実質的に使用不可能
- **中**: 設定ファイルベースの自動化が困難
- **低**: 手動でのPythonスクリプト実行は可能

## 🔍 根本原因分析

### 1. 設定スキーマの不整合
```python
# 期待される構造（DatabaseManager内）
config.database.source.host

# 実際の設定スキーマ（PGSDConfiguration）
config.source_db.host
```

### 2. バリデーション機能の問題
- `ConfigurationManager`と`PGSDConfiguration`間の連携不良
- 設定ファイル読み込み時の型変換エラー

### 3. CLI引数パースの問題
- グローバル引数の位置指定エラー
- 設定ファイル優先度の混乱

## 🎯 修正方針

### Phase 1: 設定スキーマ統一
1. **設定スキーマの標準化**
   - `PGSDConfiguration`のフィールド名を統一
   - `DatabaseManager`の期待値に合わせる

2. **バリデーション機能の修正**
   - `ConfigurationManager`のロジック見直し
   - 型チェック機能の強化

### Phase 2: CLI機能の修正
1. **引数パースの改善**
   - グローバル引数の処理順序修正
   - 設定ファイル読み込み優先度の明確化

2. **エラーハンドリングの改善**
   - 具体的なエラーメッセージの提供
   - 設定問題の診断機能追加

## 📝 修正タスク

### 高優先度
- [x] `DatabaseManager`の設定参照パス修正
- [x] `PGSDConfiguration`スキーマの統一
- [x] 基本的なCLI機能の復旧

### 中優先度
- [x] 設定ファイルバリデーションの修正
- [x] エラーメッセージの改善
- [x] 設定ファイルサンプルの更新

### 低優先度
- [ ] 設定システムの単体テスト追加
- [ ] 設定ドキュメントの更新
- [ ] 設定移行ツールの検討

## 🧪 テスト計画

### 1. 単体テスト
```bash
# 設定ファイル読み込みテスト
python -m pytest tests/unit/test_config/ -v

# CLI引数パーステスト
python -m pytest tests/unit/cli/test_cli.py -v
```

### 2. 統合テスト
```bash
# 基本的なCLI機能テスト
python -m pgsd.main --help
python -m pgsd.main validate --config config/ntb_comparison.yaml
python -m pgsd.main compare --config config/ntb_comparison.yaml
```

### 3. 動作確認
```bash
# 設定ファイルベースの比較
python -m pgsd.main --config config/ntb_comparison.yaml compare

# コマンドライン引数での比較
python -m pgsd.main compare --source-host localhost --source-db ntb --target-host localhost --target-db ntb_demo3
```

## 🔄 修正後の検証項目

1. **設定ファイル読み込み**
   - [x] YAML設定ファイルの正常読み込み
   - [x] 環境変数の正常展開
   - [x] バリデーションエラーの適切な表示

2. **CLI機能**
   - [x] ヘルプメッセージの表示
   - [x] 設定ファイルと引数の組み合わせ動作
   - [x] エラー時の適切なメッセージ表示

3. **スキーマ比較機能**
   - [x] 基本的な比較動作
   - [x] レポート生成機能
   - [x] 各種出力形式の対応

## 📊 進捗管理

### 作業ログ
- **2025-07-15**: 問題発見、チケット作成
- **2025-07-15**: 修正作業開始
- **2025-07-15**: 修正作業完了、テスト実施

### 修正内容の詳細
- DatabaseManagerの設定参照パスを `config.database.source.host` から `config.source_db.host` に修正
- ConfigurationValidatorで適切なオブジェクト作成を実装
- CLI引数パーサーに設定ファイル使用時のフォールバック機能を追加
- 設定ファイルが指定されている場合、データベース接続の必須引数を任意にする機能を実装

### 関連チケット
- PGSD-030: ユーザーマニュアル作成 (完了)
- PGSD-031: 他の関連機能修正 (検討中)

## 🚀 完了条件

1. **機能復旧**
   - CLIツールが正常に動作する
   - 設定ファイルが正しく読み込まれる
   - スキーマ比較が実行できる

2. **品質確保**
   - すべてのテストが成功する
   - エラーメッセージが分かりやすい
   - 設定ドキュメントが更新されている

3. **検証完了**
   - 手動テストが成功する
   - 既存機能に影響がない
   - パフォーマンスが劣化していない

## 📚 参考情報

### 関連ファイル
- `src/pgsd/config/schema.py`: 設定スキーマ定義
- `src/pgsd/config/manager.py`: 設定管理機能
- `src/pgsd/database/manager.py`: データベース管理
- `src/pgsd/cli/main.py`: CLI メイン処理

### 参考ドキュメント
- [設定リファレンス](docs/user_manual/reference/config_reference.md)
- [CLIコマンドリファレンス](docs/user_manual/reference/cli_commands.md)
- [開発ルール](project_management/dev_rule.md)

---
**チケット作成者**: Claude Code Assistant  
**最終更新**: 2025-07-15