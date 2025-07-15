# Docker環境でのデータベーステスト

このドキュメントでは、PGSDプロジェクトでDockerを使用したデータベース統合テストの設定と実行方法について説明します。

## 前提条件

### 必要なソフトウェア
- Docker (20.10以上)
- Docker Compose (2.0以上)
- Python (3.9以上)
- PostgreSQLクライアント（オプション、デバッグ用）

### Dockerのインストール確認
```bash
# Docker環境の確認
make docker-check

# または手動確認
docker --version
docker-compose --version
docker info
```

## データベーステスト環境

### サポートするPostgreSQLバージョン
- PostgreSQL 13 (ポート: 5433)
- PostgreSQL 14 (ポート: 5434)  
- PostgreSQL 15 (ポート: 5435)
- PostgreSQL 16 (ポート: 5436)

### テストデータベース
- データベース名: `pgsd_test`
- ユーザー名: `test_user`
- パスワード: `test_pass`

### テストスキーマ
- `test_schema_simple`: 基本的なテーブル構造
- `test_schema_complex`: 高度なPostgreSQL機能（ENUM、JSONB、全文検索など）

## テスト実行方法

### 1. 基本的なテスト実行

```bash
# 単体テストのみ（Dockerなし）
make test-unit

# データベースなしの統合テスト
make test-no-db

# 完全なテストスイート（Docker必要）
make test
```

### 2. データベーステストのみ

```bash
# データベース統合テスト
make test-db

# 特定のPostgreSQLバージョン
make test-pg13   # PostgreSQL 13
make test-pg14   # PostgreSQL 14
make test-pg15   # PostgreSQL 15
make test-pg16   # PostgreSQL 16
```

### 3. 手動でのDocker管理

```bash
# データベースコンテナ起動
make docker-up

# コンテナ状態確認
make db-status

# ログ確認
make docker-logs

# コンテナ停止
make docker-down

# 完全クリーンアップ
make clean-all
```

### 4. 環境変数での制御

```bash
# データベーステストをスキップ
SKIP_DB_TESTS=true pytest tests/

# データベーステストを有効化
SKIP_DB_TESTS=false pytest tests/integration/

# 特定のホスト指定
TEST_DB_HOST=localhost pytest tests/integration/
```

## 手動でのテスト実行

### スクリプトを使用
```bash
# 自動化スクリプト実行
./scripts/test-with-docker.sh
```

### 手動ステップ
```bash
# 1. コンテナ起動
docker-compose -f docker/docker-compose.test.yml up -d

# 2. 接続確認
docker exec pgsd_test_pg13 pg_isready -U test_user -d pgsd_test

# 3. テスト実行
PYTHONPATH=src SKIP_DB_TESTS=false pytest tests/integration/ -v

# 4. クリーンアップ
docker-compose -f docker/docker-compose.test.yml down
```

## テストの種類

### 1. データベース接続テスト
- 基本的な接続確認
- 認証エラーハンドリング
- 無効なホストへの接続テスト
- 複数PostgreSQLバージョンでの接続

### 2. スキーマ操作テスト
- スキーマ一覧取得
- テーブル一覧取得
- テーブル構造の取得
- 複雑なスキーマ要素（ビュー、関数、シーケンス等）

### 3. パフォーマンステスト
- 大量データでのクエリ性能
- 複数接続での動作確認
- メモリ使用量の確認

### 4. エラーハンドリングテスト
- 接続タイムアウト
- 無効なSQL文の処理
- 権限エラーの処理

## トラブルシューティング

### よくある問題

#### 1. Docker起動失敗
```bash
# エラー: Cannot connect to the Docker daemon
sudo systemctl start docker

# エラー: permission denied
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. ポート競合
```bash
# 使用中ポートの確認
netstat -tlnp | grep 543[3-6]

# コンテナ強制停止
docker-compose -f docker/docker-compose.test.yml down --remove-orphans
```

#### 3. データベース接続エラー
```bash
# コンテナログ確認
docker-compose -f docker/docker-compose.test.yml logs postgres-13

# 手動接続テスト
docker exec -it pgsd_test_pg13 psql -U test_user -d pgsd_test
```

#### 4. テストタイムアウト
```bash
# ヘルスチェック状態確認
docker-compose -f docker/docker-compose.test.yml ps

# コンテナ再起動
make db-reset
```

### ログ確認方法

```bash
# 全コンテナのログ
make docker-logs

# 特定コンテナのログ
docker logs pgsd_test_pg13

# リアルタイムログ
docker-compose -f docker/docker-compose.test.yml logs -f
```

## CI/CD環境での使用

### GitHub Actions
```yaml
services:
  postgres-13:
    image: postgres:13-alpine
    env:
      POSTGRES_DB: pgsd_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - 5433:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### ローカルCI
```bash
# CI環境でのテスト実行
make ci-test

# カバレッジ付きCI実行
make ci-coverage
```

## ベストプラクティス

### 1. テスト分離
- 各テストで独立したトランザクション使用
- テスト後のデータクリーンアップ
- スキーマ競合の回避

### 2. 効率的な実行
- 単体テストと統合テストの分離
- 必要時のみDocker環境を使用
- 並列実行での競合回避

### 3. 開発フロー
```bash
# 開発中の基本フロー
make test-unit           # 単体テスト（高速）
make test-no-db         # 統合テスト（DB除く）
make test-db            # DB統合テスト（本格的）
```

### 4. デバッグ方法
```bash
# テストデバッグモード
make test-debug

# 失敗したテストのみ再実行
make test-failed

# 詳細出力
make test-verbose
```

## 設定ファイル

### pytest設定 (pytest-docker.ini)
```ini
[tool:pytest]
markers =
    db: Database integration tests
    slow: Slow running tests
    docker: Tests requiring Docker
env = 
    SKIP_DB_TESTS=false
    TEST_DB_HOST=localhost
```

### Docker Compose設定
- `docker/docker-compose.test.yml`: メイン設定
- `docker/init/`: 初期化スクリプト

これで、Docker環境でのデータベーステストが完全にセットアップされ、開発者が効率的にテストを実行できるようになります。