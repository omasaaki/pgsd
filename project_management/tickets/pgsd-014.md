# PGSD-014: 設定管理機能実装

## チケット情報
- **ID**: PGSD-014
- **タイトル**: 設定管理機能実装
- **トラッカー**: 機能
- **優先度**: High
- **ステータス**: DONE
- **担当者**: Claude
- **見積（時間）**: 3時間
- **実績（時間）**: 3時間
- **依存チケット**: PGSD-009（プロジェクト基盤構築）
- **ブロックチケット**: PGSD-015, PGSD-025

## 概要
YAML設定ファイル、環境変数、CLIオプションを統合した階層的設定管理システムを実装する。

## 背景・理由
- 柔軟な設定変更対応
- 環境別設定の管理
- セキュリティ（機密情報の外部化）
- 運用時の設定変更容易性

## 詳細要件
### 設定階層（優先度順）
1. **CLIオプション** (最高優先度)
2. **環境変数**
3. **設定ファイル**
4. **デフォルト値** (最低優先度)

### YAML設定ファイル構造
```yaml
# pgsd_config.yaml
database:
  source:
    host: "localhost"
    port: 5432
    database: "production_db"
    username: "readonly_user"
    password: "${PGSD_SOURCE_PASSWORD}"
    schema: "public"
    connection_timeout: 30
  
  target:
    host: "localhost"
    port: 5432
    database: "development_db"
    username: "readonly_user"
    password: "${PGSD_TARGET_PASSWORD}"
    schema: "public"
    connection_timeout: 30

output:
  format: "html"
  path: "./reports/"
  filename_template: "schema_diff_{timestamp}"
  
comparison:
  include_views: true
  include_constraints: true
  ignore_case: false
  exclude_tables:
    - "temp_*"
    - "log_*"
  
system:
  timezone: "UTC"
  log_level: "INFO"
  log_file: "pgsd.log"
  max_connections: 5

postgresql:
  minimum_version: "13.0"
  version_check: true
  compatibility_mode: "strict"
```

### 環境変数サポート
- `${VAR_NAME}` 形式での変数置換
- `.env` ファイルサポート
- 設定値のマスキング（パスワード等）

### モジュール構成
- `pgsd/config/manager.py`: 設定管理メインクラス
- `pgsd/config/validator.py`: 設定値検証
- `pgsd/config/schema.py`: 設定スキーマ定義

## 受入条件
- [ ] YAML設定ファイルが正しく読み込める
- [ ] 環境変数の置換が動作する
- [ ] CLI引数が設定を上書きできる
- [ ] 設定値のバリデーションが動作する
- [ ] デフォルト値が適切に設定される
- [ ] 機密情報（パスワード）がマスキングされる

## テスト項目
### 単体テスト
- [ ] YAML読み込み機能の確認
- [ ] 環境変数置換の確認
- [ ] 設定階層の優先度確認
- [ ] バリデーション機能の確認
- [ ] デフォルト値の確認

### 統合テスト
- [ ] 複数設定ソースの統合確認
- [ ] 不正な設定ファイルでのエラー処理
- [ ] 大きな設定ファイルでのパフォーマンス
- [ ] 設定変更の動的反映

### 受入テスト
- [ ] 実際の運用設定での動作確認
- [ ] CLI経由での設定変更確認
- [ ] 環境変数経由での機密情報設定確認

## 実装検証項目
### セルフレビューチェックリスト
- [ ] 設定スキーマが適切に定義されている
- [ ] バリデーションが包括的である
- [ ] エラーメッセージが分かりやすい
- [ ] パフォーマンスが適切（設定読み込み<100ms）
- [ ] メモリ使用量が適切
- [ ] 型安全性が確保されている
- [ ] 設定値のログ出力で機密情報が漏洩しない
- [ ] ドキュメントに設定方法が詳述されている

### 静的解析
- [ ] 型ヒントが正しく設定されている
- [ ] YAMLスキーマの妥当性確認
- [ ] 循環参照の検出

## TODO
### 設計フェーズ
- [ ] 設定スキーマの詳細設計
- [ ] バリデーションルールの設計
- [ ] セキュリティ要件の整理

### 実装フェーズ
- [ ] manager.py実装
- [ ] validator.py実装
- [ ] schema.py実装
- [ ] サンプル設定ファイル作成
- [ ] 環境変数テンプレート作成

### 検証フェーズ
- [ ] 設定パターンテスト
- [ ] セキュリティテスト
- [ ] ドキュメント作成

## 作業メモ
- PyYAMLのセキュリティ設定（safe_load）
- 設定ファイルの場所検索優先順位
- 設定変更時の影響範囲

## 作業記録
- **開始日時**: 2025-07-14
- **完了日時**: 2025-07-14
- **実績時間**: 未定
- **見積との差異**: 未定
- **差異の理由**: 未定

## 技術検討事項
- [ ] PyYAML vs ruamel.yaml
- [ ] pydantic vs marshmallow（バリデーション）
- [ ] click.Context統合
- [ ] 設定ファイルの暗号化（将来）

---

作成日: 2025-07-12