# CLIコマンドリファレンス

PGSDのコマンドラインインターフェースの完全なリファレンスです。

## 🎯 この章で学ぶこと

- 全CLIコマンドの詳細仕様
- オプションとパラメータ
- 使用例とベストプラクティス
- 戻り値とエラーコード

## 📋 コマンド一覧

### 基本コマンド

```bash
pgsd --help                    # ヘルプ表示
pgsd --version                 # バージョン情報
pgsd compare                   # スキーマ比較実行
pgsd analyze                   # 結果分析
pgsd report                    # レポート生成
pgsd config                    # 設定管理
```

### 管理コマンド

```bash
pgsd validate-config           # 設定検証
pgsd test-connection          # 接続テスト
pgsd system-info              # システム情報
pgsd create-bug-report        # バグレポート作成
```

## 🔍 compare コマンド

スキーマ比較を実行するメインコマンドです。

### 構文

```bash
pgsd compare [OPTIONS] [SOURCE] [TARGET]
```

### 基本オプション

#### データベース接続

```bash
# ソースデータベース
--source-host HOST              # ソースホスト名
--source-port PORT              # ソースポート番号 (デフォルト: 5432)
--source-db DATABASE            # ソースデータベース名
--source-user USER              # ソースユーザー名
--source-password PASSWORD     # ソースパスワード
--source-schema SCHEMA          # ソーススキーマ名 (デフォルト: public)

# ターゲットデータベース
--target-host HOST              # ターゲットホスト名
--target-port PORT              # ターゲットポート番号 (デフォルト: 5432)
--target-db DATABASE            # ターゲットデータベース名
--target-user USER              # ターゲットユーザー名
--target-password PASSWORD     # ターゲットパスワード
--target-schema SCHEMA          # ターゲットスキーマ名 (デフォルト: public)
```

#### 出力設定

```bash
--output DIRECTORY              # 出力ディレクトリ (デフォルト: ./reports)
--format FORMAT                 # 出力形式 (html|markdown|json|xml)
--filename TEMPLATE             # ファイル名テンプレート
--template TEMPLATE             # カスタムテンプレート
```

#### 比較オプション

```bash
--include-comments              # コメントを比較に含める
--include-permissions           # 権限を比較に含める
--include-sequences             # シーケンスを比較に含める
--case-sensitive               # 大文字小文字を区別する
--tables TABLE1,TABLE2         # 特定のテーブルのみ比較
--exclude-tables TABLE1,TABLE2 # 特定のテーブルを除外
--diff-only                    # 差分のみを出力
```

#### 実行制御

```bash
--timeout SECONDS              # タイムアウト秒数 (デフォルト: 300)
--parallel WORKERS             # 並列ワーカー数 (デフォルト: 4)
--memory-limit SIZE            # メモリ制限 (例: 2GB)
--quiet                        # 出力を抑制
--verbose                      # 詳細出力
--debug                        # デバッグモード
```

### 使用例

#### 基本的な比較

```bash
# 最小限の設定
pgsd compare \
  --source-host localhost --source-db prod \
  --target-host localhost --target-db staging

# 詳細な設定
pgsd compare \
  --source-host prod.company.com \
  --source-db myapp \
  --source-user readonly \
  --source-password secret123 \
  --target-host staging.company.com \
  --target-db myapp \
  --target-user readonly \
  --target-password secret456 \
  --format html \
  --output reports/comparison \
  --include-comments \
  --verbose
```

#### 特定テーブルの比較

```bash
# 特定のテーブルのみ
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --tables "users,orders,products" \
  --format json

# 特定テーブルを除外
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --exclude-tables "temp_table,log_table" \
  --format html
```

#### 高度な設定

```bash
# パフォーマンス最適化
pgsd compare \
  --source-host localhost --source-db large_db \
  --target-host localhost --target-db large_db2 \
  --parallel 8 \
  --memory-limit 4GB \
  --timeout 1800 \
  --format json \
  --quiet

# SSL接続
pgsd compare \
  --source-host secure.company.com \
  --source-db myapp \
  --source-sslmode require \
  --source-sslcert client.crt \
  --source-sslkey client.key \
  --target-host secure2.company.com \
  --target-db myapp \
  --target-sslmode require
```

## 📊 analyze コマンド

比較結果を分析し、詳細なレポートを生成します。

### 構文

```bash
pgsd analyze [OPTIONS] INPUT_FILE
```

### オプション

```bash
--input FILE                   # 入力ファイル（JSON形式）
--output DIRECTORY             # 出力ディレクトリ
--analysis-type TYPE           # 分析タイプ (impact|trend|security)
--format FORMAT                # 出力形式 (html|markdown|json)
--severity-filter LEVEL        # 重要度フィルタ (critical|warning|info)
--include-recommendations      # 推奨事項を含める
--historical-data DAYS         # 履歴データの期間
```

### 使用例

```bash
# 基本的な分析
pgsd analyze \
  --input reports/comparison.json \
  --output analysis/ \
  --format html

# 影響度分析
pgsd analyze \
  --input reports/comparison.json \
  --analysis-type impact \
  --severity-filter critical \
  --include-recommendations

# トレンド分析
pgsd analyze \
  --input reports/comparison.json \
  --analysis-type trend \
  --historical-data 30 \
  --format markdown
```

## 📄 report コマンド

既存の比較結果から新しいレポートを生成します。

### 構文

```bash
pgsd report [OPTIONS] INPUT_FILE
```

### オプション

```bash
--input FILE                   # 入力ファイル（JSON形式）
--output DIRECTORY             # 出力ディレクトリ
--format FORMAT                # 出力形式 (html|markdown|json|xml)
--template TEMPLATE            # カスタムテンプレート
--variables FILE               # テンプレート変数ファイル
--combine FILES                # 複数のレポートを結合
--filter EXPRESSION            # フィルタ条件
```

### 使用例

```bash
# 基本的なレポート生成
pgsd report \
  --input comparison.json \
  --format html \
  --output reports/

# カスタムテンプレートの使用
pgsd report \
  --input comparison.json \
  --template custom-template.html \
  --variables template-vars.yaml \
  --format html

# 複数レポートの結合
pgsd report \
  --combine "reports/*.json" \
  --format html \
  --output combined-report/
```

## ⚙️ config コマンド

設定ファイルの管理を行います。

### 構文

```bash
pgsd config [SUBCOMMAND] [OPTIONS]
```

### サブコマンド

#### validate

```bash
pgsd config validate [CONFIG_FILE]

# 例
pgsd config validate config/production.yaml
pgsd config validate --all  # 全設定ファイルを検証
```

#### show

```bash
pgsd config show [CONFIG_FILE]

# 例
pgsd config show config/production.yaml
pgsd config show --effective  # 有効な設定を表示
```

#### create

```bash
pgsd config create [OPTIONS]

# オプション
--template TYPE                # テンプレートタイプ (basic|advanced|enterprise)
--output FILE                  # 出力ファイル
--interactive                  # インタラクティブモード

# 例
pgsd config create --template basic --output config/new-config.yaml
pgsd config create --interactive
```

#### update

```bash
pgsd config update [OPTIONS] CONFIG_FILE

# オプション
--set KEY=VALUE               # 設定値の変更
--add-database NAME           # データベース設定の追加
--remove-database NAME        # データベース設定の削除

# 例
pgsd config update config/prod.yaml --set output.format=json
pgsd config update config/prod.yaml --add-database staging
```

## 🔗 test-connection コマンド

データベース接続をテストします。

### 構文

```bash
pgsd test-connection [OPTIONS]
```

### オプション

```bash
--config FILE                  # 設定ファイル
--host HOST                    # ホスト名
--port PORT                    # ポート番号
--database DATABASE            # データベース名
--user USER                    # ユーザー名
--password PASSWORD            # パスワード
--timeout SECONDS              # タイムアウト秒数
--ssl                          # SSL接続
--verbose                      # 詳細出力
```

### 使用例

```bash
# 設定ファイルを使用
pgsd test-connection --config config/production.yaml

# 直接指定
pgsd test-connection \
  --host localhost \
  --database mydb \
  --user myuser \
  --password mypassword \
  --verbose

# SSL接続のテスト
pgsd test-connection \
  --host secure.company.com \
  --database mydb \
  --user myuser \
  --ssl \
  --verbose
```

## 🔍 validate-config コマンド

設定ファイルの妥当性を検証します。

### 構文

```bash
pgsd validate-config [OPTIONS] CONFIG_FILE
```

### オプション

```bash
--strict                       # 厳密な検証
--check-connections           # データベース接続の検証
--check-templates             # テンプレートの検証
--check-permissions           # 権限の検証
--output FORMAT               # 出力形式 (text|json|yaml)
--quiet                       # 出力を抑制
```

### 使用例

```bash
# 基本的な検証
pgsd validate-config config/production.yaml

# 厳密な検証
pgsd validate-config \
  --strict \
  --check-connections \
  --check-templates \
  config/production.yaml

# JSON形式での結果出力
pgsd validate-config \
  --output json \
  config/production.yaml
```

## 🖥️ system-info コマンド

システム情報を表示します。

### 構文

```bash
pgsd system-info [OPTIONS]
```

### オプション

```bash
--output FORMAT               # 出力形式 (text|json|yaml)
--include-config              # 設定情報を含める
--include-database            # データベース情報を含める
--include-performance         # パフォーマンス情報を含める
--save FILE                   # ファイルに保存
```

### 使用例

```bash
# 基本情報
pgsd system-info

# 詳細情報
pgsd system-info \
  --include-config \
  --include-database \
  --include-performance

# JSON形式で保存
pgsd system-info \
  --output json \
  --save system-info.json
```

## 🐛 create-bug-report コマンド

バグレポートを作成します。

### 構文

```bash
pgsd create-bug-report [OPTIONS]
```

### オプション

```bash
--output FILE                 # 出力ファイル
--include-logs               # ログファイルを含める
--include-config             # 設定ファイルを含める
--include-system-info        # システム情報を含める
--include-recent-commands    # 最近のコマンド履歴を含める
--anonymize                  # 機密情報を匿名化
--compression LEVEL          # 圧縮レベル (0-9)
```

### 使用例

```bash
# 基本的なバグレポート
pgsd create-bug-report --output bug-report.zip

# 完全なバグレポート
pgsd create-bug-report \
  --include-logs \
  --include-config \
  --include-system-info \
  --include-recent-commands \
  --anonymize \
  --output complete-bug-report.zip
```

## 📊 グローバルオプション

全てのコマンドで使用可能なオプションです。

### 共通オプション

```bash
--help, -h                    # ヘルプ表示
--version, -v                 # バージョン情報
--config FILE, -c FILE        # 設定ファイル
--log-level LEVEL             # ログレベル (DEBUG|INFO|WARNING|ERROR)
--log-file FILE               # ログファイル
--quiet, -q                   # 出力を抑制
--verbose, -V                 # 詳細出力
--debug                       # デバッグモード
--no-color                    # カラー出力を無効化
--json                        # JSON形式での出力
```

### 環境変数

```bash
PGSD_CONFIG_FILE             # デフォルト設定ファイル
PGSD_LOG_LEVEL              # ログレベル
PGSD_LOG_FILE               # ログファイル
PGSD_DATA_DIR               # データディレクトリ
PGSD_TEMP_DIR               # 一時ディレクトリ
```

## 🔢 終了コード

```bash
0    # 成功
1    # 一般的なエラー
2    # 設定エラー
3    # 接続エラー
4    # 権限エラー
5    # タイムアウト
6    # メモリ不足
7    # ディスク容量不足
8    # 互換性エラー
9    # 内部エラー
```

## 📝 設定ファイル形式

### 基本構造

```yaml
# config/example.yaml
databases:
  source:
    host: "localhost"
    port: 5432
    database: "mydb"
    user: "myuser"
    password: "${DB_PASSWORD}"
    schema: "public"
  
  target:
    host: "localhost"
    port: 5432
    database: "mydb2"
    user: "myuser"
    password: "${DB_PASSWORD}"
    schema: "public"

output:
  format: "html"
  directory: "./reports"
  filename_template: "comparison_{timestamp}"

comparison:
  include_comments: true
  include_permissions: false
  case_sensitive: true
  timeout: 300

logging:
  level: "INFO"
  file: "pgsd.log"
  console: true
```

### 環境変数の使用

```yaml
# 環境変数の参照
databases:
  source:
    host: "${DB_HOST}"
    database: "${DB_NAME}"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"

# デフォルト値の設定
output:
  directory: "${REPORT_DIR:-./reports}"
  format: "${REPORT_FORMAT:-html}"
```

## 🎯 使用パターン

### 日常的な使用

```bash
# 基本的な比較
pgsd compare --config config/daily.yaml

# 特定環境の比較
pgsd compare --config config/prod-staging.yaml --quiet

# 自動化での使用
pgsd compare --config config/automated.yaml --json --quiet
```

### 開発時の使用

```bash
# 開発環境での詳細比較
pgsd compare \
  --config config/dev.yaml \
  --verbose \
  --debug \
  --include-comments

# 特定テーブルの詳細分析
pgsd compare \
  --config config/dev.yaml \
  --tables "users,orders" \
  --format json | \
pgsd analyze --analysis-type impact
```

### CI/CDでの使用

```bash
# CI/CDパイプラインでの使用
pgsd compare \
  --config config/ci.yaml \
  --format json \
  --quiet \
  --timeout 600 || exit 1

# 結果の検証
pgsd analyze \
  --input comparison.json \
  --severity-filter critical \
  --format json | \
jq '.critical_changes | length' | \
xargs -I {} test {} -eq 0
```

## 🔧 高度な使用方法

### パイプラインでの使用

```bash
# 比較結果の加工
pgsd compare --config config/prod.yaml --format json | \
jq '.differences.tables.removed' | \
wc -l

# 複数環境の比較
for env in staging development; do
  pgsd compare \
    --config config/prod-${env}.yaml \
    --format json \
    --output reports/${env}/
done
```

### スクリプトでの使用

```bash
#!/bin/bash
# 自動化スクリプト例

set -e

CONFIG_FILE="config/production.yaml"
OUTPUT_DIR="reports/$(date +%Y%m%d)"

# 比較実行
pgsd compare \
  --config "$CONFIG_FILE" \
  --output "$OUTPUT_DIR" \
  --format html,json \
  --quiet

# 結果分析
pgsd analyze \
  --input "$OUTPUT_DIR/comparison.json" \
  --analysis-type impact \
  --include-recommendations

# 重要な変更のチェック
CRITICAL_CHANGES=$(jq '.summary.severity_breakdown.critical' "$OUTPUT_DIR/comparison.json")

if [ "$CRITICAL_CHANGES" -gt 0 ]; then
  echo "Critical changes detected: $CRITICAL_CHANGES"
  exit 1
fi
```

## 🚀 次のステップ

CLIコマンドを理解したら：

1. **[設定リファレンス](config_reference.md)** - 設定ファイルの詳細
2. **[API仕様](api_specification.md)** - プログラムからの利用
3. **[エラーコード](error_codes.md)** - エラーコードの詳細

## 📚 関連資料

- [インストールガイド](../getting_started/installation.md)
- [基本ワークフロー](../getting_started/basic_workflow.md)
- [設定ファイル](../configuration/config_file.md)