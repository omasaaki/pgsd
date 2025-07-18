# 要件定義書
**PostgreSQL Schema Diff Tool (PGSD)**

## 📋 概要

### プロジェクト名
PostgreSQL Schema Diff Tool (PGSD)

### 目的
PostgreSQLの2つのスキーマ間の差分を分析し、分かりやすいレポート形式で出力することで、データベーススキーマの変更管理と差分確認を効率化する。

### 背景
- データベーススキーマの変更管理が煩雑
- 手動での差分確認によるミスのリスク
- 開発・本番環境間のスキーマ差分把握の困難
- レビューや承認プロセスでの可視化ニーズ

---

## 🎯 機能要件

### FR-001: スキーマ差分検出機能
**概要**: 2つのPostgreSQLスキーマ間の差分を検出する

**詳細要件**:
- pg_dumpコマンドの出力結果を利用した差分検出
- テーブル、カラム、インデックス、制約の差分検出
- データ型変更の検出
- 権限設定の差分検出（将来拡張）

**受入条件**:
- [ ] 2つのスキーマファイルを入力として受け取れる
- [ ] テーブルの追加・削除・変更を検出できる
- [ ] カラムの追加・削除・変更を検出できる
- [ ] インデックスの追加・削除・変更を検出できる
- [ ] 制約の追加・削除・変更を検出できる

### FR-002: 複数形式レポート出力機能
**概要**: 差分結果を複数の形式で出力する

**詳細要件**:
- HTML形式での出力（デフォルト）
- Markdown形式での出力
- JSON形式での出力
- XML形式での出力

**受入条件**:
- [ ] HTML形式で見やすいレポートを出力できる
- [ ] Markdown形式でドキュメント化できる
- [ ] JSON形式でプログラムから処理できる
- [ ] XML形式で構造化データとして利用できる

### FR-003: 設定管理機能
**概要**: プログラムの動作を設定ファイルで制御する

**詳細要件**:
- データベース接続情報の設定
- レポート出力パスの設定
- タイムゾーン設定
- 比較対象項目の設定

**受入条件**:
- [ ] 設定ファイル（YAML/JSON形式）で動作を制御できる
- [ ] データベース接続情報を設定できる
- [ ] 出力先ディレクトリを指定できる
- [ ] 比較対象を選択できる

### FR-004: pg_dump連携機能
**概要**: pg_dumpコマンドと連携してスキーマ情報を取得する

**詳細要件**:
- pg_dumpコマンドの自動実行
- スキーマ限定でのダンプ取得
- 適切なオプション指定（--schema-only --no-owner --no-privileges）

**受入条件**:
- [ ] pg_dumpコマンドを自動実行できる
- [ ] 指定スキーマのみをダンプできる
- [ ] 不要な情報を除外してダンプできる

---

## 🔧 非機能要件

### NFR-001: パフォーマンス要件
- **処理時間**: 中規模スキーマ（100テーブル程度）で5分以内
- **メモリ使用量**: 1GB以下
- **対象スキーマサイズ**: 最大1000テーブルまで対応

### NFR-002: 可用性要件
- **稼働率**: 単発実行ツールのため稼働率要件なし
- **復旧時間**: 障害時は再実行で対応

### NFR-003: セキュリティ要件
- **認証**: PostgreSQLの既存認証機構を利用
- **機密情報**: データベース接続情報の安全な管理
- **アクセス制御**: 設定ファイルのアクセス権限設定

### NFR-004: 保守性要件
- **コード品質**: テストカバレッジ80%以上
- **ドキュメント**: 包括的な技術ドキュメント整備
- **拡張性**: 新しい比較項目の追加が容易

### NFR-005: 移植性要件
- **対応OS**: Linux、Windows、macOS
- **Python環境**: Python 3.8以上
- **PostgreSQL**: PostgreSQL 12以上対応

---

## 👥 ステークホルダー要件

### 開発者
- **ニーズ**: スキーマ変更の影響範囲確認
- **期待**: 自動化された差分検出とレビュー資料作成

### データベース管理者
- **ニーズ**: 本番環境への変更前の差分確認
- **期待**: 詳細で正確な差分レポート

### プロジェクトマネージャー
- **ニーズ**: 変更内容の可視化と承認プロセス
- **期待**: 分かりやすいレポート形式

---

## 🚫 制約条件

### 技術的制約
- pg_dumpコマンドが利用可能であること
- PostgreSQLへの接続権限があること
- Python実行環境があること

### 運用制約
- ネットワーク経由でのデータベースアクセスが必要
- 比較対象スキーマへの読み取り権限が必要

### プロジェクト制約
- 開発期間: 約3ヶ月
- 開発工数: 110時間
- 品質基準: テストカバレッジ80%以上

---

## 🎯 成功基準

### 機能面
- [ ] すべての機能要件を満たす
- [ ] 複数形式でのレポート出力が正常動作
- [ ] 設定ファイルによる柔軟な動作制御

### 品質面
- [ ] テストカバレッジ80%以上
- [ ] エラーハンドリングの適切な実装
- [ ] セキュリティ要件の遵守

### 運用面
- [ ] ユーザーマニュアルの整備
- [ ] トラブルシューティングガイドの作成
- [ ] 保守・運用手順の文書化

---

## 🔄 関連ドキュメント
- [プロジェクト計画書](../plans/PROJECT_PLAN.md)
- [機能設計書](../design/) ※今後作成予定
- [アーキテクチャ設計書](../design/) ※今後作成予定

---

## 📅 更新履歴
- **2025-07-12**: 新規作成（PGSD-002）