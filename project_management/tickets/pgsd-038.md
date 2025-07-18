# PGSD-038: 設定ファイル使用時のデータベース接続エラー修正

## 📋 基本情報

- **チケット番号**: PGSD-038
- **タイトル**: 設定ファイル使用時のデータベース接続エラー修正
- **種別**: バグ修正 (Bug Fix)
- **優先度**: High
- **作成日**: 2025-07-18
- **担当者**: システム開発チーム
- **推定工数**: 4時間
- **ステータス**: DONE

## 🐛 バグ詳細

### 現象
設定ファイル（YAML）を使用してpgsdコマンドを実行すると、データベース接続に失敗する。

### 再現手順
1. 設定ファイル `config/ntb_comparison.yaml` を作成
2. 以下のコマンドを実行:
   ```bash
   pgsd --config config/ntb_comparison.yaml compare
   ```

### 実際の結果
```
ERROR:pgsd.database.manager:Failed to initialize database manager
ERROR:pgsd.core.engine:Failed to initialize schema comparison engine: Database manager initialization failed: Source database verification failed: Database manager not initialized
ERROR:pgsd.cli.commands.CompareCommand:Schema comparison failed: Engine initialization failed: Database manager initialization failed: Source database verification failed: Database manager not initialized
```

### 期待される結果
設定ファイルの内容に基づいてデータベースに正常に接続し、スキーマ比較が実行される。

### 検証済み事項
- PostgreSQLサーバーは正常に動作している（`pg_isready -h localhost -p 5432` = OK）
- 直接的なデータベース接続は正常（`psql`で接続可能）
- コマンドライン引数を直接指定した場合は動作する可能性が高い

## 🎯 原因分析

### 疑われる原因
1. **設定ファイルの読み込み処理**: YAMLファイルの解析に問題がある
2. **引数解析の順序**: グローバルオプション（--config）とサブコマンド（compare）の処理順序
3. **設定値のマッピング**: YAML設定からデータベース接続パラメータへの変換処理
4. **データベースマネージャー初期化**: 設定ファイル経由の初期化ロジック

### 確認が必要な箇所
- `src/pgsd/config/manager.py`: 設定ファイル読み込み処理
- `src/pgsd/cli/main.py`: CLI引数解析処理
- `src/pgsd/database/manager.py`: データベースマネージャー初期化
- `src/pgsd/cli/commands.py`: compareコマンド実装

## 🔧 修正方針

### 1. 設定ファイル読み込みの検証
- YAML解析処理の確認
- 設定値のバリデーション強化
- エラーハンドリングの改善

### 2. CLI引数解析の修正
- グローバルオプションとサブコマンドの処理順序見直し
- 設定ファイル指定時のフォールバック処理改善

### 3. データベース接続処理の強化
- 設定ファイル経由での接続パラメータ設定
- 接続エラー時の詳細なエラーメッセージ

### 4. ログ出力の改善
- デバッグ情報の充実
- 設定値の可視化（パスワード除く）

## 📝 修正タスク

### 高優先度
- [ ] 設定ファイル読み込み処理の調査・デバッグ
- [ ] CLI引数解析ロジックの確認
- [ ] データベースマネージャー初期化処理の確認
- [ ] エラーハンドリングの改善

### 中優先度
- [ ] 設定ファイルバリデーション機能の強化
- [ ] 詳細なエラーメッセージの実装
- [ ] デバッグログの充実
- [ ] 単体テストの追加

### 低優先度
- [ ] 設定ファイル形式の検証
- [ ] ドキュメントの更新
- [ ] 使用例の追加

## 🧪 テスト計画

### 1. 機能テスト
- 設定ファイル経由での正常動作確認
- 不正な設定ファイルでのエラーハンドリング確認
- コマンドライン引数との併用テスト

### 2. 回帰テスト
- 既存のコマンドライン引数での動作確認
- 他の設定ファイル形式での動作確認

### 3. エラーケーステスト
- 存在しない設定ファイル
- 不正なYAML形式
- 無効なデータベース接続情報

## 🎯 受入条件

1. **基本動作**
   - 設定ファイルを使用したpgsdコマンドが正常に実行される
   - データベース接続が正常に確立される
   - スキーマ比較処理が正常に完了する

2. **エラーハンドリング**
   - 適切なエラーメッセージが表示される
   - ログ出力が充実している
   - 問題の特定が容易になる

3. **回帰防止**
   - 既存機能に影響を与えない
   - 単体テストでカバーされる
   - ドキュメントが更新される

## 📚 関連情報

### 関連ファイル
- `config/ntb_comparison.yaml`: 問題の設定ファイル
- `src/pgsd/config/manager.py`: 設定管理
- `src/pgsd/cli/main.py`: CLIメイン処理
- `src/pgsd/database/manager.py`: データベース管理

### 関連チケット
- PGSD-032: 設定システムの不整合修正（完了）
- PGSD-025: CLI実装（完了）

### デバッグ情報
```bash
# 動作する形式（想定）
pgsd compare --source-host localhost --source-db ntb ...

# エラーになる形式
pgsd --config config/ntb_comparison.yaml compare
```

## 📝 作業記録

- **開始日時**: 2025-07-18
- **完了日時**: 未完了
- **実績時間**: 未記録
- **見積との差異**: 未記録

---
**チケット作成者**: Claude Assistant  
**最終更新**: 2025-07-18