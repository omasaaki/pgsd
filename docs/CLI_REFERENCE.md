# PGSD CLI リファレンス

PostgreSQL Schema Diff Tool のコマンドライン インターフェース完全リファレンス

## 目次
1. [概要](#概要)
2. [グローバルオプション](#グローバルオプション)
3. [コマンド詳細](#コマンド詳細)
4. [設定ファイル連携](#設定ファイル連携)
5. [終了コード](#終了コード)
6. [環境変数](#環境変数)

## 概要

PGSDのコマンドライン インターフェースは4つの主要コマンドを提供します：

```bash
pgsd <COMMAND> [OPTIONS]
```

**利用可能なコマンド:**
- `compare` - スキーマ比較とレポート生成
- `list-schemas` - データベース内スキーマ一覧表示
- `validate` - 設定ファイル検証
- `version` - バージョン情報表示

## グローバルオプション

すべてのコマンドで使用可能なオプション:

### `--help`, `-h`
ヘルプメッセージを表示して終了

```bash
pgsd --help
pgsd compare --help
```

### `--version`
バージョン情報を表示して終了

```bash
pgsd --version
# 出力例: pgsd 1.0.0
```

### `--config`, `-c`
設定ファイルのパスを指定

```bash
pgsd --config /path/to/config.yaml compare
pgsd -c config.yaml compare
```

### `--verbose`, `-v`
詳細なログ出力を有効化

```bash
pgsd --verbose compare --source-host localhost --source-db db1 --target-host localhost --target-db db2
```

**出力レベル:**
- デフォルト: INFO以上
- --verbose: DEBUG以上
- --quiet: ERROR以上

### `--quiet`, `-q`
エラー以外の出力を抑制

```bash
pgsd --quiet compare --source-host localhost --source-db db1 --target-host localhost --target-db db2
```

## コマンド詳細

### `compare` - スキーマ比較

データベース間のスキーマを比較し、レポートを生成します。

#### 基本構文
```bash
pgsd compare [OPTIONS]
```

#### 必須オプション

**ソースデータベース:**
- `--source-host` - ソースデータベースホスト
- `--source-db` - ソースデータベース名

**ターゲットデータベース:**
- `--target-host` - ターゲットデータベースホスト  
- `--target-db` - ターゲットデータベース名

#### オプションパラメータ

**ソースデータベース接続:**
```bash
--source-port PORT          # ポート番号 (デフォルト: 5432)
--source-user USER          # ユーザー名
--source-password PASSWORD  # パスワード
```

**ターゲットデータベース接続:**
```bash
--target-port PORT          # ポート番号 (デフォルト: 5432)  
--target-user USER          # ユーザー名
--target-password PASSWORD  # パスワード
```

**比較オプション:**
```bash
--schema SCHEMA             # 比較するスキーマ名 (デフォルト: public)
--output DIR, -o DIR        # 出力ディレクトリ (デフォルト: ./reports)
--format FORMAT, -f FORMAT  # レポート形式: html,markdown,json,xml (デフォルト: html)
--dry-run                   # 実行内容の確認のみ（実際の比較は行わない）
```

#### 使用例

**基本的な比較:**
```bash
pgsd compare \
  --source-host localhost --source-db production \
  --target-host localhost --target-db staging
```

**詳細オプション指定:**
```bash
pgsd compare \
  --source-host prod.example.com \
  --source-port 5432 \
  --source-db myapp \
  --source-user app_user \
  --source-password secret123 \
  --target-host staging.example.com \
  --target-port 5433 \
  --target-db myapp_staging \
  --target-user app_user \
  --target-password secret123 \
  --schema public \
  --format markdown \
  --output ./schema-reports/
```

**ドライラン実行:**
```bash
pgsd compare --dry-run \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

### `list-schemas` - スキーマ一覧

指定したデータベース内の利用可能なスキーマを一覧表示します。

#### 基本構文
```bash
pgsd list-schemas [OPTIONS]
```

#### 必須オプション
```bash
--host HOST                 # データベースホスト
--db DATABASE               # データベース名
```

#### オプションパラメータ
```bash
--port PORT                 # ポート番号 (デフォルト: 5432)
--user USER                 # ユーザー名
--password PASSWORD         # パスワード
```

#### 使用例

**ローカルデータベースのスキーマ一覧:**
```bash
pgsd list-schemas --host localhost --db myapp
```

**認証情報付きでリモートデータベース:**
```bash
pgsd list-schemas \
  --host prod.example.com \
  --port 5432 \
  --db production \
  --user readonly_user \
  --password viewonly123
```

#### 出力例
```
Available schemas in database 'myapp':
- public
- app_data
- audit_logs
- temp_schema
```

### `validate` - 設定ファイル検証

PGSD設定ファイルの構文と内容を検証します。

#### 基本構文
```bash
pgsd validate [OPTIONS]
```

#### 必須オプション
```bash
--config FILE, -c FILE      # 検証する設定ファイルのパス
```

#### 使用例

**設定ファイル検証:**
```bash
pgsd validate --config config.yaml
pgsd validate -c /etc/pgsd/production.yml
```

#### 出力例

**正常な場合:**
```
✅ Configuration file 'config.yaml' is valid
- Database connections: OK
- Output settings: OK  
- Logging configuration: OK
```

**エラーがある場合:**
```
❌ Configuration file 'config.yaml' has errors:
- databases.source.host: required field missing
- output.format: invalid value 'pdf' (must be one of: html, markdown, json, xml)
- logging.level: invalid value 'TRACE' (must be one of: DEBUG, INFO, WARNING, ERROR)
```

### `version` - バージョン情報

PGSDのバージョン、ビルド情報、サポートしているPostgreSQLバージョンを表示します。

#### 基本構文
```bash
pgsd version
```

#### オプションなし
このコマンドにはオプションパラメータはありません。

#### 使用例
```bash
pgsd version
```

#### 出力例
```
PGSD (PostgreSQL Schema Diff Tool) v1.0.0

Build Information:
- Python: 3.11.2
- psycopg2: 2.9.5
- Build Date: 2024-07-15
- Git Commit: a1b2c3d

Supported PostgreSQL Versions:
- PostgreSQL 13.x ✅
- PostgreSQL 14.x ✅  
- PostgreSQL 15.x ✅
- PostgreSQL 16.x ✅

System Information:
- Platform: Linux 5.15.0
- Architecture: x86_64

For support and documentation: https://github.com/omasaaki/pgsd
```

## 設定ファイル連携

### 優先順位
PGSDは以下の優先順位で設定を読み込みます（高い順）：

1. **コマンドライン引数** - 最高優先度
2. **環境変数**
3. **設定ファイル** (`--config`で指定)
4. **デフォルト値** - 最低優先度

### 設定ファイル + CLI引数の組み合わせ

**設定ファイル (config.yaml):**
```yaml
databases:
  source:
    host: prod.example.com
    database: production
    user: app_user
  target:
    host: staging.example.com
    database: staging  
    user: app_user

output:
  format: html
  directory: ./reports
```

**CLI実行:**
```bash
# format を markdown に上書き
pgsd compare --config config.yaml --format markdown

# 出力ディレクトリを上書き
pgsd compare --config config.yaml --output /tmp/reports

# source-passwordのみ CLI で指定
pgsd compare --config config.yaml --source-password secret123
```

## 終了コード

PGSDは以下の終了コードを返します：

| コード | 意味 | 詳細 |
|--------|------|------|
| 0 | 成功 | 正常に処理が完了 |
| 1 | 一般エラー | 設定エラー、データベース接続エラーなど |
| 2 | 引数エラー | 不正なコマンドライン引数 |
| 3 | 設定ファイルエラー | 設定ファイルの構文エラーや存在しないファイル |
| 4 | データベースエラー | データベース接続や権限エラー |
| 5 | 処理エラー | スキーマ比較処理中のエラー |
| 130 | ユーザー中断 | Ctrl+C による中断 (SIGINT) |

### 終了コードの活用例

```bash
#!/bin/bash
# CI/CD スクリプト例

pgsd compare --config production.yaml
exit_code=$?

case $exit_code in
  0)
    echo "✅ Schema comparison completed successfully"
    ;;
  1|4|5)
    echo "❌ Schema comparison failed (exit code: $exit_code)"
    exit 1
    ;;
  2|3)
    echo "⚠️  Configuration error (exit code: $exit_code)"
    exit 1
    ;;
  130)
    echo "⏹️  Operation cancelled by user"
    exit 130
    ;;
  *)
    echo "❓ Unknown exit code: $exit_code"
    exit $exit_code
    ;;
esac
```

## 環境変数

PGSDは以下の環境変数をサポートします：

### データベース接続
```bash
# ソースデータベース
PGSD_SOURCE_HOST=prod.example.com
PGSD_SOURCE_PORT=5432
PGSD_SOURCE_DB=production
PGSD_SOURCE_USER=app_user
PGSD_SOURCE_PASSWORD=secret123

# ターゲットデータベース  
PGSD_TARGET_HOST=staging.example.com
PGSD_TARGET_PORT=5432
PGSD_TARGET_DB=staging
PGSD_TARGET_USER=app_user
PGSD_TARGET_PASSWORD=secret123
```

### PostgreSQL標準環境変数
```bash
# PostgreSQL クライアント標準
PGHOST=localhost           # データベースホスト
PGPORT=5432               # データベースポート
PGDATABASE=myapp          # データベース名
PGUSER=postgres           # ユーザー名
PGPASSWORD=password       # パスワード
PGPASSFILE=~/.pgpass      # パスワードファイル
```

### 出力・ログ設定
```bash
PGSD_OUTPUT_DIR=./reports         # 出力ディレクトリ
PGSD_OUTPUT_FORMAT=html           # レポート形式
PGSD_LOG_LEVEL=INFO               # ログレベル
PGSD_CONFIG_FILE=/etc/pgsd.yaml   # デフォルト設定ファイル
```

### 使用例

```bash
# 環境変数での接続情報設定
export PGSD_SOURCE_HOST=prod.server.com
export PGSD_SOURCE_DB=myapp
export PGSD_TARGET_HOST=staging.server.com  
export PGSD_TARGET_DB=myapp

# 簡潔なコマンド実行
pgsd compare --source-user app_user --target-user app_user
```

```bash
# .env ファイルと組み合わせ
echo "PGSD_SOURCE_PASSWORD=prod_secret" >> .env
echo "PGSD_TARGET_PASSWORD=staging_secret" >> .env
source .env

pgsd compare \
  --source-host prod.example.com --source-db myapp \
  --target-host staging.example.com --target-db myapp
```

このリファレンスを参考に、PGSDのCLI機能を効果的に活用してください。