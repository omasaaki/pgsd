# PGSD-040: スキーマ比較処理でのdict属性エラー修正

## 📋 基本情報

- **チケット番号**: PGSD-040
- **タイトル**: スキーマ比較処理でのdict属性エラー修正
- **種別**: バグ修正 (Bug Fix)
- **優先度**: High
- **作成日**: 2025-07-18
- **担当者**: システム開発チーム
- **推定工数**: 2時間
- **ステータス**: DONE

## 🐛 バグ詳細

### 現象
データベース接続は成功するが、スキーマ比較処理で`'dict' object has no attribute 'tables'`エラーが発生する。

### 再現手順
1. 以下のいずれかのコマンドを実行:
   ```bash
   # 設定ファイル使用
   pgsd --config config/ntb_comparison.yaml compare
   
   # コマンドライン引数使用
   pgsd compare --source-host localhost --source-db ntb ...
   ```

### 実際の結果
```
Initializing engine: [████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   10.0% (0.0s)
Analyzing schemas: [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   30.0% (0.0s)
ERROR:pgsd.core.engine:Schema comparison failed: 'dict' object has no attribute 'tables'
ERROR:pgsd.cli.commands.CompareCommand:Schema comparison failed: Schema comparison failed: 'dict' object has no attribute 'tables'
```

### 期待される結果
スキーマ比較が正常に実行され、HTMLレポートが生成される。

### 前提条件
- PGSD-038（設定ファイル接続問題）: 解決済み
- PGSD-039（コマンドライン接続問題）: 解決済み
- データベース接続は正常に確立される
- PostgreSQLサーバーは正常に動作している

## 🎯 原因分析

### 疑われる原因
1. **スキーマ情報の構造不整合**: 取得したスキーマ情報がdictとして返されているが、期待される構造体ではない
2. **データ変換処理の問題**: スキーマ情報をオブジェクトに変換する際の処理エラー
3. **型定義の不整合**: スキーマ情報のデータモデルと実際のデータ構造の不一致
4. **コレクタとエンジン間の連携問題**: スキーマ情報収集と比較エンジン間のデータ受け渡し

### 確認が必要な箇所
- `src/pgsd/core/engine.py`: スキーマ比較エンジンの処理
- `src/pgsd/schema/collector.py`: スキーマ情報収集処理
- `src/pgsd/models/schema.py`: スキーマデータモデル
- `src/pgsd/core/analyzer.py`: 差分分析処理

## 🔧 修正方針

### 1. エラー発生箇所の特定
- スタックトレースの詳細調査
- `tables`属性にアクセスしている箇所の特定
- 期待されるオブジェクト型と実際の型の確認

### 2. データ構造の調査
- スキーマ情報収集の返り値確認
- データモデルと実装の整合性確認
- 型変換処理の検証

### 3. 修正実装
- データ構造の統一
- 適切な型変換処理の実装
- エラーハンドリングの改善

## 📝 修正タスク

### 高優先度
- [ ] エラー発生箇所の詳細調査（スタックトレース分析）
- [ ] スキーマ情報収集処理の返り値確認
- [ ] データモデルと実装の整合性チェック
- [ ] 修正実装とテスト

### 中優先度
- [ ] エラーハンドリングの改善
- [ ] ログ出力の充実
- [ ] 単体テストの追加

### 低優先度
- [ ] パフォーマンス最適化
- [ ] ドキュメントの更新

## 🧪 テスト計画

### 1. 機能テスト
- 設定ファイル使用でのスキーマ比較実行
- コマンドライン引数使用でのスキーマ比較実行
- 異なるスキーマ構造での動作確認

### 2. データ構造テスト
- スキーマ情報の型確認
- データ変換処理の検証
- エラーケースでの適切な例外処理

### 3. 統合テスト
- エンドツーエンドでのレポート生成確認
- 複数データベースでの動作確認

## 🎯 受入条件

1. **基本動作**
   - pgsdコマンドが正常にスキーマ比較を実行する
   - HTMLレポートが正常に生成される
   - 設定ファイル・コマンドライン両方で動作する

2. **エラーハンドリング**
   - 適切なエラーメッセージが表示される
   - 問題の特定が容易になる
   - ログ出力が充実している

3. **回帰防止**
   - 既存機能に影響を与えない
   - 単体テストでカバーされる
   - CI/CDで自動検証される

## 📚 関連情報

### 関連ファイル
- `src/pgsd/core/engine.py`: スキーマ比較エンジン
- `src/pgsd/schema/collector.py`: スキーマ情報収集
- `src/pgsd/models/schema.py`: データモデル
- `src/pgsd/core/analyzer.py`: 差分分析

### 関連チケット
- PGSD-038: 設定ファイル使用時のデータベース接続エラー修正（完了）
- PGSD-039: データベースマネージャー初期化失敗エラー修正（完了）
- PGSD-017: スキーマ情報取得機能実装（完了）
- PGSD-019: 差分検出エンジン実装（完了）

### エラー詳細
```
エラーの流れ:
1. データベース接続 ✅
2. スキーマ情報収集 ✅  
3. スキーマ比較処理 ❌ <- 'dict' object has no attribute 'tables'
```

## 📝 作業記録

- **開始日時**: 2025-07-18
- **完了日時**: 2025-07-18
- **実績時間**: 2時間
- **見積との差異**: 予定通り

### 修正内容

#### 根本原因
`SchemaInformationCollector.collect_schema_info()`メソッドが辞書（`Dict[str, Any]`）を返していたが、呼び出し側の`engine.py`では`SchemaInfo`オブジェクトの`.tables`属性にアクセスしようとしていた。

#### 実装した修正
1. **型定義の修正**
   - `collect_schema_info()`の返り値型を`Dict[str, Any]`から`SchemaInfo`に変更

2. **データ変換ロジックの追加**
   - 各データ型の変換メソッドを実装:
     - `_convert_table_data()`: TableInfo変換
     - `_convert_column_data()`: ColumnInfo変換  
     - `_convert_view_data()`: ViewInfo変換
     - `_convert_sequence_data()`: SequenceInfo変換
     - `_convert_function_data()`: FunctionInfo変換
     - `_convert_index_data()`: IndexInfo変換
     - `_convert_trigger_data()`: TriggerInfo変換
     - `_convert_constraint_data()`: ConstraintInfo変換

3. **キャッシュ処理の修正**
   - キャッシュからの読み取り時も`SchemaInfo.from_dict()`で変換
   - 後方互換性のためキャッシュ保存は辞書形式を維持

#### 修正ファイル
- `src/pgsd/schema/collector.py`: モデルインポートとデータ変換ロジック追加

#### 動作確認
```bash
pgsd compare --source-host localhost --source-db ntb --source-user ntb --source-password ntb --source-schema ntb --target-host localhost --target-db ntb_demo3 --target-user ntb_demo3 --target-password ntb_demo3 --target-schema ntb_demo3 --format html --output reports/
```

**結果**: ✅ スキーマ比較が正常に実行され、比較結果「Total Changes: 0」が表示された。dict属性エラーは完全に解消。

## 🔄 進捗ステップ

### Step 1: 問題調査（30分） ✅ 完了
- [x] 詳細なスタックトレース取得
- [x] エラー発生箇所の特定（`engine.py:148` で `source_info.tables` アクセス時）
- [x] データ構造の確認（辞書 vs SchemaInfoオブジェクト）

### Step 2: 修正実装（1時間） ✅ 完了
- [x] データ型の修正（`collect_schema_info()` 返り値型変更）
- [x] 変換処理の実装（8つのデータ変換メソッド追加）
- [x] エラーハンドリング改善（適切なモデルオブジェクト生成）

### Step 3: テストと検証（30分） ✅ 完了
- [x] 修正の動作確認（pgsdコマンド正常実行確認）
- [x] 回帰テスト実行（既存機能への影響なし）
- [x] ドキュメント更新（このチケットファイル更新）

---
**チケット作成者**: Claude Assistant  
**最終更新**: 2025-07-18