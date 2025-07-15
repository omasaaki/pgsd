# PGSD ユーザーガイド

PostgreSQL Schema Diff Tool (PGSD) の包括的な使用マニュアル

## 目次
1. [はじめに](#はじめに)
2. [インストール](#インストール)
3. [基本的な使用方法](#基本的な使用方法)
4. [設定ファイルの活用](#設定ファイルの活用)
5. [高度な使用方法](#高度な使用方法)
6. [レポート形式と出力](#レポート形式と出力)
7. [トラブルシューティング](#トラブルシューティング)
8. [ベストプラクティス](#ベストプラクティス)

## はじめに

PGSDは、PostgreSQLデータベース間のスキーマ差分を分析し、わかりやすいレポートを生成するツールです。

### 主要機能
- **スキーマ比較**: テーブル、カラム、インデックス、制約などの差分検出
- **複数形式レポート**: HTML、Markdown、JSON、XML形式での出力
- **設定管理**: YAML設定ファイルによる柔軟な設定
- **CLI対応**: コマンドライン引数による直接実行
- **バージョン対応**: PostgreSQL 13-16 サポート

### 使用場面
- 開発環境と本番環境のスキーマ差分確認
- データベースマイグレーション前の差分チェック
- 継続的インテグレーション (CI/CD) での自動検証
- スキーマ変更の文書化とレビュー

## インストール

### 要件
- Python 3.9以上
- PostgreSQL クライアント（psycopg2-binary）
- インターネット接続（初回依存関係インストール時）

### pipからのインストール
```bash
pip install pgsd
```

### ソースからのインストール
```bash
git clone https://github.com/omasaaki/pgsd.git
cd pgsd
pip install -e .
```

### 仮想環境での使用（推奨）
```bash
# pyenvを使用した場合
pyenv virtualenv 3.11 pgsd-env
pyenv activate pgsd-env
pip install pgsd

# venvを使用した場合
python -m venv pgsd-env
source pgsd-env/bin/activate  # Linux/Mac
# pgsd-env\Scripts\activate.bat  # Windows
pip install pgsd
```

### インストール確認
```bash
pgsd version
```

## 基本的な使用方法

### 最も簡単な使用例
```bash
pgsd compare \
  --source-host localhost --source-db source_db \
  --target-host localhost --target-db target_db
```

### データベース接続情報の指定
```bash
pgsd compare \
  --source-host prod.example.com \
  --source-port 5432 \
  --source-db production \
  --source-user app_user \
  --source-password mypassword \
  --target-host staging.example.com \
  --target-port 5433 \
  --target-db staging \
  --target-user app_user \
  --target-password mypassword
```

### スキーマの指定
```bash
# 特定のスキーマのみ比較
pgsd compare --schema public \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2

# デフォルトは 'public' スキーマ
```

### レポート出力の指定
```bash
# HTML形式（デフォルト）
pgsd compare --format html --output ./reports \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2

# Markdown形式
pgsd compare --format markdown --output ./reports \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

## 設定ファイルの活用

### 設定ファイルのサンプル作成
```bash
# サンプル設定ファイルの作成
cp config/pgsd.yaml.example my-config.yaml
```

### 設定ファイルの基本構造
```yaml
# my-config.yaml
databases:
  source:
    host: localhost
    port: 5432
    database: source_db
    user: postgres
    password: "${DB_PASSWORD}"  # 環境変数使用
    schema: public
  
  target:
    host: localhost
    port: 5432
    database: target_db
    user: postgres
    password: "${DB_PASSWORD}"
    schema: public

output:
  format: html
  directory: ./reports
  filename_template: "schema_diff_{timestamp}"

logging:
  level: INFO
  file: logs/pgsd.log

comparison:
  include_permissions: false
  ignore_case: true
  timeout: 300
```

### 設定ファイルの使用
```bash
# 設定ファイルを使用した比較
pgsd compare --config my-config.yaml

# 設定ファイル + コマンドライン引数の組み合わせ
pgsd compare --config my-config.yaml --format markdown
```

### 環境変数の活用
```bash
# .envファイルまたは環境変数設定
export DB_PASSWORD="secret_password"
export PGSD_SOURCE_HOST="prod.example.com"
export PGSD_TARGET_HOST="staging.example.com"

pgsd compare --config config-with-env-vars.yaml
```

## 高度な使用方法

### ドライランによる事前確認
```bash
# 実際の比較を行わず、実行内容のみ確認
pgsd compare --dry-run \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

### 詳細ログの有効化
```bash
# 詳細なデバッグ情報を出力
pgsd compare --verbose \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2

# エラーのみ出力
pgsd compare --quiet \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

### バッチ処理での使用
```bash
#!/bin/bash
# batch-comparison.sh

# 複数データベースの連続比較
for db in db1 db2 db3; do
  echo "Comparing $db..."
  pgsd compare \
    --source-host prod.server.com --source-db $db \
    --target-host staging.server.com --target-db $db \
    --output "./reports/$db" \
    --format html
done
```

### CI/CDでの使用
```yaml
# .github/workflows/schema-check.yml
name: Schema Diff Check
on: [push, pull_request]

jobs:
  schema-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      
      - name: Install PGSD
        run: pip install pgsd
      
      - name: Schema Comparison
        run: |
          pgsd compare \
            --source-host ${{ secrets.PROD_DB_HOST }} \
            --source-db production \
            --target-host ${{ secrets.STAGING_DB_HOST }} \
            --target-db staging \
            --format json \
            --output ./diff-report.json
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: schema-diff-report
          path: diff-report.json
```

## レポート形式と出力

### HTML レポート
```bash
pgsd compare --format html --output ./reports \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

**生成されるファイル:**
- `schema_diff_20240715_143022.html` - メインレポート
- インタラクティブな差分表示
- ドリルダウン可能な詳細情報

### Markdown レポート
```bash
pgsd compare --format markdown --output ./reports \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

**特徴:**
- GitHub Flavored Markdown対応
- Markdownビューアで閲覧可能
- テキストベースでバージョン管理に適している

### JSON レポート
```bash
pgsd compare --format json --output ./reports \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

**用途:**
- プログラマティックな処理
- API連携
- カスタムレポート生成の基盤

### XML レポート
```bash
pgsd compare --format xml --output ./reports \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

**用途:**
- 企業システムとの連携
- 標準的なXMLパーサーでの処理
- XSLT変換による独自フォーマット生成

## トラブルシューティング

### よくあるエラーと対処法

#### 接続エラー
```
Error: could not connect to server: Connection refused
```
**対処法:**
- ホスト名、ポート番号を確認
- ファイアウォール設定を確認
- PostgreSQLサービスの起動状態を確認

#### 認証エラー
```
Error: FATAL: password authentication failed for user "postgres"
```
**対処法:**
- ユーザー名、パスワードを確認
- pg_hba.confの認証設定を確認
- データベースアクセス権限を確認

#### 権限エラー
```
Error: permission denied for schema public
```
**対処法:**
- ユーザーのスキーマアクセス権限を確認
- USAGE権限をユーザーに付与

#### タイムアウトエラー
```
Error: operation timed out after 300 seconds
```
**対処法:**
- 設定ファイルでタイムアウト値を調整
```yaml
comparison:
  timeout: 600  # 10分に延長
```

### ログの確認方法
```bash
# 詳細ログ出力
pgsd compare --verbose \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 2>&1 | tee debug.log

# ログファイルの設定
```
```yaml
logging:
  level: DEBUG
  file: /var/log/pgsd/debug.log
  console: true
```

### デバッグモード
```bash
# Python環境での詳細デバッグ
PYTHONPATH=src python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from pgsd.cli.main import main
main()
" compare --source-host localhost --source-db db1 --target-host localhost --target-db db2
```

## ベストプラクティス

### セキュリティ
1. **パスワードの安全な管理**
```bash
# 環境変数の使用
export PGPASSWORD="your_password"
pgsd compare --source-host localhost --source-db db1 --target-host localhost --target-db db2

# .pgpassファイルの使用
echo "localhost:5432:*:postgres:password" >> ~/.pgpass
chmod 600 ~/.pgpass
```

2. **設定ファイルの権限管理**
```bash
chmod 600 config.yaml  # 所有者のみ読み書き可能
```

### パフォーマンス
1. **スキーマの指定**
```bash
# 必要なスキーマのみ比較
pgsd compare --schema app_schema --source-host localhost --source-db db1 --target-host localhost --target-db db2
```

2. **ネットワーク最適化**
```yaml
# 設定ファイルでタイムアウトとコネクション数を調整
databases:
  source:
    connection_timeout: 30
    query_timeout: 120
```

### 継続的監視
1. **定期実行の設定**
```bash
# cron設定例
0 2 * * * /usr/local/bin/pgsd compare --config /etc/pgsd/config.yaml >> /var/log/pgsd/daily.log 2>&1
```

2. **レポートの自動配信**
```bash
#!/bin/bash
# daily-schema-check.sh
pgsd compare --config /etc/pgsd/config.yaml --format html --output /tmp/schema-report
mail -s "Daily Schema Diff Report" admin@example.com < /tmp/schema-report/schema_diff_*.html
```

### チーム開発
1. **設定ファイルのテンプレート化**
```yaml
# config-template.yaml
databases:
  source:
    host: "${SOURCE_HOST}"
    database: "${SOURCE_DB}"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
  target:
    host: "${TARGET_HOST}"
    database: "${TARGET_DB}"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
```

2. **レポート形式の統一**
```bash
# プロジェクト共通のレポート生成
pgsd compare --config team-config.yaml --format markdown --output ./docs/schema-reports/
```

このユーザーガイドを参考に、PGSDを効果的に活用してください。さらに詳細な情報は、`CLI_REFERENCE.md`および`EXAMPLES.md`をご参照ください。