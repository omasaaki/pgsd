# PGSD-039: データベースマネージャー初期化失敗エラー修正

## 📋 基本情報

- **チケット番号**: PGSD-039
- **タイトル**: データベースマネージャー初期化失敗エラー修正
- **種別**: バグ修正 (Bug Fix)
- **優先度**: High
- **作成日**: 2025-07-18
- **担当者**: システム開発チーム
- **推定工数**: 3時間
- **ステータス**: TODO

## 🐛 バグ詳細

### 現象
コマンドライン引数を直接指定してpgsdコマンドを実行すると、データベースマネージャーの初期化に失敗する。

### 再現手順
1. 以下のコマンドを実行:
   ```bash
   pgsd compare \
     --source-host localhost \
     --source-db ntb \
     --source-user ntb \
     --source-password ntb \
     --source-schema ntb \
     --target-host localhost \
     --target-db ntb_demo3 \
     --target-user ntb_demo3 \
     --target-password ntb_demo3 \
     --target-schema ntb_demo3 \
     --format html \
     --output reports/
   ```

### 実際の結果
```
Analyzing schemas: [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   30.0% (0.0s)
ERROR:pgsd.database.manager:Failed to initialize database manager
ERROR:pgsd.core.engine:Failed to initialize schema comparison engine: Database manager initialization failed: Source database verification failed: Database manager not initialized
ERROR:pgsd.cli.commands.CompareCommand:Schema comparison failed: Engine initialization failed: Database manager initialization failed: Source database verification failed: Database manager not initialized
```

### 期待される結果
データベースマネージャーが正常に初期化され、スキーマ比較処理が実行される。

### 検証済み事項
- PostgreSQLサーバーは正常に動作している（`pg_isready -h localhost -p 5432` = OK）
- 直接的なデータベース接続は正常（`psql`で両データベースに接続可能）
- 接続情報は正しく指定されている

## 🎯 原因分析

### 疑われる原因
1. **非同期処理の問題**: `DatabaseManager.initialize()`がasyncメソッドだが、適切にawaitされていない
2. **初期化タイミング**: エンジン初期化時にマネージャーの初期化が完了していない
3. **エラーハンドリング**: 初期化失敗時の例外処理が不適切
4. **設定値の伝播**: コマンドライン引数から設定オブジェクトへの変換に問題

### 確認が必要な箇所
- `src/pgsd/core/engine.py`: エンジン初期化処理
- `src/pgsd/database/manager.py`: データベースマネージャー初期化
- `src/pgsd/cli/commands.py`: compareコマンド実装
- `src/pgsd/config/manager.py`: 設定値の構築

## 🔧 修正方針

### 1. 非同期処理の修正
- エンジン初期化時のawait処理確認
- データベースマネージャー初期化の同期化
- 適切な非同期コンテキスト管理

### 2. 初期化順序の見直し
- データベースマネージャー → エンジン の順序保証
- 初期化状態の適切な管理
- 依存関係の明確化

### 3. エラーハンドリング強化
- 詳細なエラーメッセージの追加
- 初期化失敗原因の特定機能
- ログ出力の改善

### 4. 設定値検証
- コマンドライン引数の正しい設定オブジェクト変換
- 必須パラメータの検証
- デフォルト値の適用

## 📝 修正タスク

### 高優先度
- [ ] core/engine.py の初期化処理調査
- [ ] データベースマネージャーの非同期処理確認
- [ ] コマンドライン引数から設定オブジェクトへの変換確認
- [ ] 初期化エラーの詳細ログ出力

### 中優先度
- [ ] 初期化順序の最適化
- [ ] エラーハンドリングの改善
- [ ] 単体テストの追加
- [ ] 統合テストの強化

### 低優先度
- [ ] パフォーマンス最適化
- [ ] ドキュメントの更新
- [ ] 使用例の追加

## 🧪 テスト計画

### 1. 機能テスト
- コマンドライン引数での正常動作確認
- 異なるデータベース設定での動作確認
- エラーケースでの適切なエラーメッセージ確認

### 2. 非同期処理テスト
- データベースマネージャー初期化の同期テスト
- エンジン初期化のタイミングテスト
- 並行処理での動作確認

### 3. エラーケーステスト
- 無効な接続情報でのエラーハンドリング
- データベースサーバー停止時の動作
- 権限不足での動作

## 🎯 受入条件

1. **基本動作**
   - コマンドライン引数でのpgsdコマンドが正常実行される
   - データベースマネージャーが正常に初期化される
   - スキーマ比較処理が正常に完了する

2. **エラーハンドリング**
   - 初期化失敗時に詳細なエラーメッセージが表示される
   - 問題の特定が容易になる
   - 適切なログ出力がされる

3. **回帰防止**
   - 既存機能に影響を与えない
   - 単体テストでカバーされる
   - CI/CDで自動検証される

## 📚 関連情報

### 関連ファイル
- `src/pgsd/core/engine.py`: スキーマ比較エンジン
- `src/pgsd/database/manager.py`: データベースマネージャー
- `src/pgsd/cli/commands.py`: CLIコマンド処理
- `src/pgsd/config/manager.py`: 設定管理

### 関連チケット
- PGSD-038: 設定ファイル使用時のデータベース接続エラー修正（別件）
- PGSD-025: CLI実装（完了）
- PGSD-015: データベース接続管理実装（完了）

### 技術的詳細
```python
# DatabaseManager.initialize() は非同期メソッド
async def initialize(self) -> None:
    # 初期化処理

# エラーメッセージの流れ
# 1. "Database manager not initialized" 
# 2. "Source database verification failed"
# 3. "Database manager initialization failed"
```

## 📝 作業記録

- **開始日時**: 2025-07-18
- **完了日時**: 未完了
- **実績時間**: 未記録
- **見積との差異**: 未記録

---
**チケット作成者**: Claude Assistant  
**最終更新**: 2025-07-18