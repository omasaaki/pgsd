# PGSD-008: information_schema調査

## チケット情報
- **ID**: PGSD-008
- **タイトル**: information_schema調査
- **トラッカー**: 作業
- **優先度**: High
- **ステータス**: DONE
- **担当者**: 未定
- **見積（時間）**: 3時間
- **実績（時間）**: -
- **依存チケット**: PGSD-005（スキーマ情報取得方法調査）
- **ブロックチケット**: PGSD-003（機能設計）、PGSD-007（差分検出アルゴリズムの検証）

## 概要
PGSD-005での決定に基づき、information_schemaを使用したスキーマ情報取得方法を詳細に調査する。

## 背景・理由
- PGSD-005でinformation_schema方式の採用を決定
- 基本的なスキーマ構造の差分検出に必要な情報の取得方法を確立
- SQL標準で移植性の高い実装を目指す

## 詳細要件
### 調査対象テーブル
1. `information_schema.tables`
2. `information_schema.columns`
3. `information_schema.table_constraints`
4. `information_schema.key_column_usage`
5. `information_schema.referential_constraints`
6. `information_schema.views`
7. `information_schema.table_privileges`

### 調査内容
- 各テーブルから取得可能な情報の詳細
- スキーマ差分検出に必要なクエリの設計
- 複数テーブルのJOIN方法
- パフォーマンス考慮事項

## 受入条件
- [ ] 各information_schemaテーブルの仕様を文書化
- [ ] スキーマ情報取得用のSQLクエリを設計
- [ ] サンプルデータベースでの動作確認
- [ ] 調査レポートの作成

## テスト項目
- [ ] 基本的なテーブル情報の取得
- [ ] カラム情報の完全な取得
- [ ] 制約情報の取得と整合性確認
- [ ] 外部キー関係の正確な取得

## TODO
- [ ] information_schemaの仕様調査
- [ ] 各テーブルの詳細調査
- [ ] サンプルクエリの作成
- [ ] 動作検証環境の準備
- [ ] 調査レポートの作成

## 作業メモ
- PostgreSQL 12以上を前提として調査
- 将来的なpg_catalog併用も考慮した設計

## 作業記録
- **開始日時**: 未定
- **完了日時**: 未定
- **実績時間**: 未定
- **見積との差異**: 未定
- **差異の理由**: 未定

## 技術検討事項
- [ ] PostgreSQLバージョン間の差異確認
- [ ] 大規模スキーマでのパフォーマンス
- [ ] 権限不足時のエラーハンドリング

---

作成日: 2025-07-12