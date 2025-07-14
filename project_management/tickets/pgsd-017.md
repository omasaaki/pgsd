# PGSD-017: スキーマ情報取得機能実装

## チケット情報
- **ID**: PGSD-017
- **タイトル**: スキーマ情報取得機能実装
- **トラッカー**: 機能
- **優先度**: High
- **ステータス**: DONE
- **担当者**: Claude
- **見積（時間）**: 4時間
- **実績（時間）**: -
- **依存チケット**: PGSD-015（データベース接続管理）、PGSD-016（バージョン検出）
- **ブロックチケット**: PGSD-018, PGSD-019

## 概要
PostgreSQLデータベースからスキーマ情報（テーブル、カラム、制約、インデックス等）を取得する機能を実装する。PGSD-015で実装したDatabaseManagerを活用してinformation_schemaから情報を収集する。

## 背景・理由
- スキーマ差分検出の前提となる情報収集
- PostgreSQLバージョン別の対応
- 権限チェック機能の統合
- 効率的な情報取得とキャッシュ機能

## 詳細要件
### スキーマ情報取得機能
```python
class SchemaInformationCollector:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.version_detector = VersionDetector(database_manager)
    
    async def collect_schema_info(self, schema_name):
        # 全スキーマ情報の収集
        pass
    
    async def collect_tables(self, schema_name):
        # テーブル情報の収集
        pass
    
    async def collect_columns(self, schema_name, table_name):
        # カラム情報の収集
        pass
    
    async def collect_constraints(self, schema_name):
        # 制約情報の収集
        pass
```

### 収集対象情報
- **テーブル**: 名前、所有者、テーブル空間、コメント
- **カラム**: 名前、データ型、NULL制約、デフォルト値、コメント
- **制約**: 主キー、外部キー、一意制約、チェック制約
- **インデックス**: 名前、タイプ、カラム、一意性、条件
- **ビュー**: 名前、定義、更新可能性
- **シーケンス**: 名前、開始値、増分値、最大値、最小値
- **トリガー**: 名前、イベント、タイミング、関数
- **関数/プロシージャ**: 名前、引数、戻り値、定義

### PostgreSQLバージョン対応
- PostgreSQL 13+固有の機能対応
- バージョン別のinformation_schemaの差異吸収
- 非対応機能の適切な処理

## 受入条件
- [ ] 指定スキーマのテーブル情報が取得できる
- [ ] カラム情報（型、制約、デフォルト値）が取得できる
- [ ] 制約情報（PK、FK、UNIQUE、CHECK）が取得できる
- [ ] インデックス情報が取得できる
- [ ] ビュー情報が取得できる
- [ ] 権限不足時の適切なエラー処理
- [ ] PostgreSQLバージョン別の対応

## テスト項目
### 単体テスト
- [ ] テーブル情報取得機能の確認
- [ ] カラム情報取得機能の確認
- [ ] 制約情報取得機能の確認
- [ ] インデックス情報取得機能の確認
- [ ] ビュー情報取得機能の確認
- [ ] エラーハンドリングの確認

### 統合テスト
- [ ] 複数PostgreSQLバージョンでの動作確認
- [ ] 大規模スキーマでのパフォーマンス確認
- [ ] 権限制限環境での動作確認
- [ ] 異なるスキーマ構造での動作確認

### 受入テスト
- [ ] 実際のPostgreSQLデータベースでの動作確認
- [ ] 複雑なスキーマ構造での情報取得確認
- [ ] 日本語を含むオブジェクト名での動作確認

## 実装検証項目
### セルフレビューチェックリスト
- [ ] information_schemaの適切な活用
- [ ] 権限チェックが適切に実装されている
- [ ] PostgreSQLバージョン対応が適切である
- [ ] エラーハンドリングが包括的である
- [ ] パフォーマンスが適切である（大規模スキーマ対応）
- [ ] ログ出力が適切である
- [ ] メモリ使用量が適切である
- [ ] ドキュメントが整備されている

### 静的解析
- [ ] 型安全性の確認
- [ ] SQLインジェクション対策の確認
- [ ] メモリリークの確認

## TODO
### 設計フェーズ
- [ ] information_schemaクエリの設計
- [ ] データ構造の設計
- [ ] バージョン対応戦略の設計

### 実装フェーズ
- [ ] schema_collector.py実装
- [ ] 各情報取得機能の実装
- [ ] バージョン対応機能の実装
- [ ] テストコード作成

### 検証フェーズ
- [ ] 機能テスト
- [ ] パフォーマンステスト
- [ ] 互換性テスト

## 作業メモ
- information_schemaの標準的な活用
- PostgreSQL固有のpg_catalog活用の検討
- 大規模スキーマでのパフォーマンス最適化
- 権限エラーの適切な処理

## 作業記録
- **開始日時**: 2025-07-14
- **完了日時**: 未定
- **実績時間**: 未定
- **見積との差異**: 未定
- **差異の理由**: 未定

## 技術検討事項
- [ ] information_schema vs pg_catalog
- [ ] 大規模スキーマでの分割取得
- [ ] 並列処理による高速化
- [ ] キャッシュ機能の実装

## 参考資料
- PostgreSQL Documentation: Information Schema
- PostgreSQL Documentation: System Catalogs
- PGSD-015: Database Connection Management
- PGSD-016: Version Detection

---

作成日: 2025-07-14