# PGSD-011: 基本的なテスト環境構築

## チケット情報
- **ID**: PGSD-011
- **タイトル**: 基本的なテスト環境構築
- **トラッカー**: 機能
- **優先度**: High
- **ステータス**: TODO
- **担当者**: 未定
- **見積（時間）**: 3時間
- **実績（時間）**: -
- **依存チケット**: PGSD-009（プロジェクト基盤構築）
- **ブロックチケット**: 全ての実装チケット

## 概要
pytest、Docker Compose、PostgreSQL複数バージョンを使用した包括的なテスト環境を構築し、テスト駆動開発を可能にする。

## 背景・理由
- テスト駆動開発の実現
- 複数PostgreSQLバージョンでの動作保証
- CI/CDパイプラインとの連携
- 品質保証の自動化

## 詳細要件
### テスト環境構成
1. **pytest設定**
   - pytest.ini設定
   - conftest.py（共通フィクスチャ）
   - テストディレクトリ構造

2. **Docker Compose環境**
   - PostgreSQL 13, 14, 15, 16
   - テスト用データベース自動作成
   - ポート分離（5433-5436）

3. **テストカテゴリ**
   - unit/: 単体テスト
   - integration/: 統合テスト
   - fixtures/: テストデータ

### テスト用設定
```yaml
# docker-compose.test.yml
services:
  postgres-13:
    image: postgres:13
    environment:
      POSTGRES_DB: pgsd_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"
```

## 受入条件
- [ ] pytest.iniが適切に設定されている
- [ ] conftest.pyで共通フィクスチャが定義されている
- [ ] docker-compose.test.ymlで複数PostgreSQL環境が定義されている
- [ ] `pytest`コマンドでテストが実行できる
- [ ] `pytest --cov`でカバレッジが測定できる
- [ ] テスト用サンプルスキーマが準備されている

## テスト項目
### 単体テスト
- [ ] pytest設定の妥当性検証
- [ ] フィクスチャの動作確認
- [ ] テストデータベース接続確認

### 統合テスト
- [ ] Docker Compose起動確認
- [ ] 複数PostgreSQLバージョンの並列起動
- [ ] CI環境での動作確認

### 受入テスト
- [ ] `make test`での統合テスト実行
- [ ] カバレッジレポート生成確認
- [ ] テスト並列実行の動作確認

## 実装検証項目
### セルフレビューチェックリスト
- [ ] テスト設定がベストプラクティスに従っている
- [ ] Docker環境がローカル開発に支障をきたさない
- [ ] テストの実行時間が適切（<30秒）
- [ ] テストデータが適切に分離されている
- [ ] CI/CD環境との整合性が取れている
- [ ] メモリ使用量が適切
- [ ] テストの並列実行が安全
- [ ] ドキュメントにテスト実行方法が記載されている

### 静的解析
- [ ] pytest設定ファイルの構文チェック
- [ ] docker-compose.ymlの構文チェック
- [ ] テストファイルの型チェック（mypy）

## TODO
### 設計フェーズ
- [ ] テスト戦略の詳細設計
- [ ] Docker環境の設計
- [ ] テストデータ設計

### 実装フェーズ
- [ ] pytest.ini作成
- [ ] conftest.py作成
- [ ] docker-compose.test.yml作成
- [ ] Makefile作成（テストコマンド）
- [ ] サンプルテストケース作成
- [ ] テストデータ準備

### 検証フェーズ
- [ ] テスト環境の動作確認
- [ ] パフォーマンステスト
- [ ] ドキュメント作成

## 作業メモ
- PostgreSQL各バージョンの初期化スクリプト準備
- テスト実行の高速化（キャッシュ活用）
- CI環境でのDocker in Docker対応

## 作業記録
- **開始日時**: 未定
- **完了日時**: 未定
- **実績時間**: 未定
- **見積との差異**: 未定
- **差異の理由**: 未定

## 技術検討事項
- [ ] pytest vs unittest
- [ ] pytest-asyncio対応
- [ ] pytest-xdist（並列実行）
- [ ] testcontainers vs docker-compose

---

作成日: 2025-07-12