# PGSD 使用例集

PostgreSQL Schema Diff Tool の実践的な使用例とサンプル集

## 目次
1. [基本的な使用例](#基本的な使用例)
2. [設定ファイルを使った例](#設定ファイルを使った例)
3. [レポート形式別の例](#レポート形式別の例)
4. [自動化スクリプト例](#自動化スクリプト例)
5. [CI/CD統合例](#cicd統合例)
6. [トラブルシューティング例](#トラブルシューティング例)
7. [アドバンスド使用例](#アドバンスド使用例)

## 基本的な使用例

### 1. ローカル環境での簡単な比較

```bash
# 同一サーバー上の2つのデータベースを比較
pgsd compare \
  --source-host localhost --source-db myapp_dev \
  --target-host localhost --target-db myapp_test

# 実行結果例:
# ✅ Schema comparison completed
# 📄 Report generated: ./reports/schema_diff_20240715_143022.html
```

### 2. リモートサーバー間の比較

```bash
# 本番環境とステージング環境の比較
pgsd compare \
  --source-host prod.mycompany.com --source-db production \
  --source-user readonly_user --source-password prod_pass123 \
  --target-host staging.mycompany.com --target-db staging \
  --target-user readonly_user --target-password staging_pass123
```

### 3. 特定スキーマの比較

```bash
# 'app_data' スキーマのみを比較
pgsd compare \
  --schema app_data \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

### 4. カスタム出力ディレクトリ

```bash
# 特定の出力ディレクトリを指定
pgsd compare \
  --output /home/user/schema-reports/$(date +%Y%m%d) \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

## 設定ファイルを使った例

### 1. 基本的な設定ファイル

**config/development.yaml:**
```yaml
databases:
  source:
    host: localhost
    port: 5432
    database: myapp_dev
    user: postgres
    password: dev_password
    schema: public
  
  target:
    host: localhost
    port: 5432
    database: myapp_test
    user: postgres
    password: test_password
    schema: public

output:
  format: html
  directory: ./reports/development
  filename_template: "dev_vs_test_{timestamp}"

logging:
  level: INFO
  console: true
```

**実行:**
```bash
pgsd compare --config config/development.yaml
```

### 2. 環境変数を使った設定

**config/production.yaml:**
```yaml
databases:
  source:
    host: "${PROD_DB_HOST}"
    port: "${PROD_DB_PORT:-5432}"
    database: "${PROD_DB_NAME}"
    user: "${DB_USER}"
    password: "${PROD_DB_PASSWORD}"
    schema: "${SCHEMA_NAME:-public}"
  
  target:
    host: "${STAGING_DB_HOST}"
    port: "${STAGING_DB_PORT:-5432}"
    database: "${STAGING_DB_NAME}"
    user: "${DB_USER}"
    password: "${STAGING_DB_PASSWORD}"
    schema: "${SCHEMA_NAME:-public}"

output:
  format: "${REPORT_FORMAT:-html}"
  directory: "${OUTPUT_DIR:-./reports}"

logging:
  level: "${LOG_LEVEL:-INFO}"
  file: "${LOG_FILE:-logs/pgsd.log}"
```

**環境変数設定:**
```bash
export PROD_DB_HOST=prod.example.com
export PROD_DB_NAME=myapp
export STAGING_DB_HOST=staging.example.com
export STAGING_DB_NAME=myapp
export DB_USER=schema_reader
export PROD_DB_PASSWORD=prod_secret123
export STAGING_DB_PASSWORD=staging_secret123
export REPORT_FORMAT=markdown
export OUTPUT_DIR=/var/reports/schema-diff

pgsd compare --config config/production.yaml
```

### 3. 複数環境対応設定

**config/multi-env.yaml:**
```yaml
# 複数環境の設定例
environments:
  development:
    source:
      host: localhost
      database: myapp_dev
    target:
      host: localhost
      database: myapp_local
  
  staging:
    source:
      host: prod.example.com
      database: production
    target:
      host: staging.example.com
      database: staging
  
  testing:
    source:
      host: staging.example.com
      database: staging
    target:
      host: test.example.com
      database: test

# デフォルト設定
defaults:
  user: postgres
  port: 5432
  schema: public
  
output:
  format: html
  directory: ./reports
```

## レポート形式別の例

### 1. HTML レポート（詳細表示用）

```bash
pgsd compare \
  --format html \
  --output ./html-reports \
  --source-host prod.example.com --source-db production \
  --target-host staging.example.com --target-db staging

# 生成されるファイル:
# - schema_diff_20240715_143022.html (インタラクティブなHTMLレポート)
# - 差分のハイライト表示
# - ドリルダウン可能な詳細情報
```

### 2. Markdown レポート（文書化用）

```bash
pgsd compare \
  --format markdown \
  --output ./docs/schema-changes \
  --source-host prod.example.com --source-db production \
  --target-host staging.example.com --target-db staging

# 生成されるファイル:
# - schema_diff_20240715_143022.md (GitHub互換Markdown)
# - バージョン管理に適したテキスト形式
# - プルリクエストでのレビューに最適
```

### 3. JSON レポート（API連携用）

```bash
pgsd compare \
  --format json \
  --output ./api-reports \
  --source-host prod.example.com --source-db production \
  --target-host staging.example.com --target-db staging

# 生成されるファイル:
# - schema_diff_20240715_143022.json
# - プログラマティック処理用の構造化データ
# - 他システムとの連携に最適
```

### 4. XML レポート（企業システム連携用）

```bash
pgsd compare \
  --format xml \
  --output ./xml-reports \
  --source-host prod.example.com --source-db production \
  --target-host staging.example.com --target-db staging

# 生成されるファイル:
# - schema_diff_20240715_143022.xml
# - 企業システムとの連携用
# - XSLT変換による独自フォーマット生成可能
```

## 自動化スクリプト例

### 1. 日次スキーマ比較スクリプト

**scripts/daily-schema-check.sh:**
```bash
#!/bin/bash

# 日次スキーマ比較スクリプト
set -euo pipefail

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../config/daily-check.yaml"
OUTPUT_DIR="/var/reports/schema-diff/$(date +%Y%m%d)"
LOG_FILE="/var/log/pgsd/daily-check.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# メイン処理
main() {
    log "Starting daily schema comparison"
    
    # 出力ディレクトリ作成
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # スキーマ比較実行
    if pgsd compare \
        --config "$CONFIG_FILE" \
        --output "$OUTPUT_DIR" \
        --format html \
        --verbose >> "$LOG_FILE" 2>&1; then
        
        log "Schema comparison completed successfully"
        
        # レポートをメール送信
        send_report_email "$OUTPUT_DIR"
        
        # 古いレポートのクリーンアップ（30日より古い）
        find /var/reports/schema-diff -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true
        
    else
        log "ERROR: Schema comparison failed"
        send_error_notification
        exit 1
    fi
}

# レポート送信
send_report_email() {
    local report_dir="$1"
    local report_file=$(find "$report_dir" -name "*.html" | head -1)
    
    if [[ -f "$report_file" ]]; then
        {
            echo "Daily Schema Diff Report - $(date +%Y-%m-%d)"
            echo "Report file: $report_file"
            echo ""
            echo "Summary:"
            grep -A 10 "comparison-summary" "$report_file" | sed 's/<[^>]*>//g' || echo "Summary extraction failed"
        } | mail -s "Daily Schema Diff Report" -a "$report_file" admin@example.com
    fi
}

# エラー通知
send_error_notification() {
    echo "ALERT: Daily schema comparison failed on $(hostname) at $(date)" | \
        mail -s "ALERT: Schema Diff Failure" admin@example.com
}

main "$@"
```

**cron設定:**
```bash
# 毎日午前2時に実行
0 2 * * * /opt/pgsd/scripts/daily-schema-check.sh
```

### 2. 複数環境一括比較スクリプト

**scripts/multi-env-check.sh:**
```bash
#!/bin/bash

# 複数環境のスキーマ比較スクリプト
set -euo pipefail

# 環境定義
declare -A ENVIRONMENTS=(
    ["dev-to-test"]="dev.yaml"
    ["test-to-staging"]="test-staging.yaml"
    ["staging-to-prod"]="staging-prod.yaml"
)

# 設定
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${BASE_DIR}/../config/environments"
OUTPUT_BASE="/var/reports/multi-env/$(date +%Y%m%d_%H%M%S)"

# 結果保存用
declare -a RESULTS=()

# 各環境の比較実行
for env_name in "${!ENVIRONMENTS[@]}"; do
    config_file="${CONFIG_DIR}/${ENVIRONMENTS[$env_name]}"
    output_dir="${OUTPUT_BASE}/${env_name}"
    
    echo "🔍 Comparing: $env_name"
    
    mkdir -p "$output_dir"
    
    if pgsd compare \
        --config "$config_file" \
        --output "$output_dir" \
        --format json \
        --quiet; then
        
        echo "✅ $env_name: SUCCESS"
        RESULTS+=("$env_name:SUCCESS")
    else
        echo "❌ $env_name: FAILED"
        RESULTS+=("$env_name:FAILED")
    fi
done

# 結果サマリー
echo ""
echo "📊 Comparison Summary:"
echo "===================="
for result in "${RESULTS[@]}"; do
    echo "  $result"
done

# Slack通知（webhook URLが設定されている場合）
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Multi-environment schema comparison completed:\n$(printf '%s\n' "${RESULTS[@]}")\"}" \
        "$SLACK_WEBHOOK_URL"
fi
```

### 3. バックアップと比較の統合スクリプト

**scripts/backup-and-compare.sh:**
```bash
#!/bin/bash

# データベースバックアップ後のスキーマ比較
set -euo pipefail

# 設定
SOURCE_HOST="prod.example.com"
SOURCE_DB="production"
BACKUP_HOST="backup.example.com"
BACKUP_DB="production_backup"
REPORT_DIR="/var/reports/backup-verification/$(date +%Y%m%d)"

# バックアップ実行
echo "🔄 Creating database backup..."
pg_dump -h "$SOURCE_HOST" -d "$SOURCE_DB" --schema-only | \
    psql -h "$BACKUP_HOST" -d "$BACKUP_DB" -q

# バックアップ完了確認
if [[ $? -eq 0 ]]; then
    echo "✅ Backup completed successfully"
else
    echo "❌ Backup failed"
    exit 1
fi

# スキーマ比較実行
echo "🔍 Comparing original vs backup schemas..."
mkdir -p "$REPORT_DIR"

pgsd compare \
    --source-host "$SOURCE_HOST" --source-db "$SOURCE_DB" \
    --target-host "$BACKUP_HOST" --target-db "$BACKUP_DB" \
    --output "$REPORT_DIR" \
    --format html

# 結果確認
if [[ $? -eq 0 ]]; then
    echo "✅ Schema verification completed"
    echo "📄 Report: $REPORT_DIR/schema_diff_*.html"
else
    echo "❌ Schema verification failed"
    exit 1
fi
```

## CI/CD統合例

### 1. GitHub Actions

**.github/workflows/schema-diff.yml:**
```yaml
name: Schema Difference Check

on:
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 6 * * *'  # 毎日午前6時

jobs:
  schema-diff:
    runs-on: ubuntu-latest
    
    services:
      postgres-source:
        image: postgres:15
        env:
          POSTGRES_DB: source_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      postgres-target:
        image: postgres:15
        env:
          POSTGRES_DB: target_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5433:5432

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install PGSD
        run: |
          pip install --upgrade pip
          pip install pgsd

      - name: Setup test schemas
        run: |
          # ソーススキーマのセットアップ
          psql -h localhost -p 5432 -U postgres -d source_db -c "
            CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100));
            CREATE INDEX idx_users_name ON users(name);
          "
          
          # ターゲットスキーマのセットアップ（差分あり）
          psql -h localhost -p 5433 -U postgres -d target_db -c "
            CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(200), email VARCHAR(255));
            CREATE INDEX idx_users_name ON users(name);
            CREATE INDEX idx_users_email ON users(email);
          "

      - name: Run Schema Comparison
        run: |
          pgsd compare \
            --source-host localhost --source-port 5432 --source-db source_db \
            --source-user postgres --source-password postgres \
            --target-host localhost --target-port 5433 --target-db target_db \
            --target-user postgres --target-password postgres \
            --format json \
            --output ./schema-diff-report

      - name: Upload Schema Diff Report
        uses: actions/upload-artifact@v3
        with:
          name: schema-diff-report
          path: ./schema-diff-report/

      - name: Comment PR with Schema Diff
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const path = './schema-diff-report/';
            const files = fs.readdirSync(path);
            const jsonFile = files.find(f => f.endsWith('.json'));
            
            if (jsonFile) {
              const report = JSON.parse(fs.readFileSync(path + jsonFile, 'utf8'));
              const summary = `## 📊 Schema Diff Report
              
              **Tables Added:** ${report.tables_added?.length || 0}
              **Tables Modified:** ${report.tables_modified?.length || 0}
              **Tables Removed:** ${report.tables_removed?.length || 0}
              
              [Download full report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
              `;
              
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: summary
              });
            }
```

### 2. GitLab CI

**.gitlab-ci.yml:**
```yaml
stages:
  - test
  - schema-diff
  - deploy

variables:
  POSTGRES_DB: test_db
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres

services:
  - postgres:15

schema-comparison:
  stage: schema-diff
  image: python:3.11
  
  before_script:
    - pip install pgsd psycopg2-binary
    - apt-get update && apt-get install -y postgresql-client
  
  script:
    # テストデータ準備
    - |
      PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB << EOF
      CREATE SCHEMA source_schema;
      CREATE SCHEMA target_schema;
      
      CREATE TABLE source_schema.users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
      );
      
      CREATE TABLE target_schema.users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP
      );
      EOF
    
    # スキーマ比較実行
    - |
      pgsd compare \
        --source-host postgres --source-db $POSTGRES_DB --source-user $POSTGRES_USER \
        --source-password $POSTGRES_PASSWORD --schema source_schema \
        --target-host postgres --target-db $POSTGRES_DB --target-user $POSTGRES_USER \
        --target-password $POSTGRES_PASSWORD --schema target_schema \
        --format html --output ./schema-reports/
  
  artifacts:
    paths:
      - schema-reports/
    expire_in: 1 week
    reports:
      junit: schema-reports/*.xml
  
  only:
    - merge_requests
    - main
```

### 3. Jenkins Pipeline

**Jenkinsfile:**
```groovy
pipeline {
    agent any
    
    environment {
        PGSD_CONFIG = credentials('pgsd-production-config')
        NOTIFICATION_EMAIL = 'devops@example.com'
    }
    
    triggers {
        cron('H 2 * * *')  // 毎日午前2時頃
    }
    
    stages {
        stage('Preparation') {
            steps {
                checkout scm
                sh 'pip install --user pgsd'
            }
        }
        
        stage('Schema Comparison') {
            parallel {
                stage('Production vs Staging') {
                    steps {
                        sh '''
                            mkdir -p reports/prod-staging
                            pgsd compare \
                                --config $PGSD_CONFIG \
                                --output reports/prod-staging \
                                --format html
                        '''
                    }
                }
                
                stage('Staging vs Development') {
                    steps {
                        sh '''
                            mkdir -p reports/staging-dev
                            pgsd compare \
                                --source-host staging.example.com --source-db myapp \
                                --target-host dev.example.com --target-db myapp \
                                --output reports/staging-dev \
                                --format markdown
                        '''
                    }
                }
            }
        }
        
        stage('Report Analysis') {
            steps {
                script {
                    def reportFiles = findFiles(glob: 'reports/**/*.html')
                    if (reportFiles.size() > 0) {
                        echo "Generated ${reportFiles.size()} schema diff reports"
                        
                        // レポートをアーカイブ
                        archiveArtifacts artifacts: 'reports/**/*', fingerprint: true
                        
                        // 差分がある場合の通知
                        def hasChanges = sh(
                            script: 'grep -r "differences found" reports/ || true',
                            returnStatus: true
                        ) == 0
                        
                        if (hasChanges) {
                            currentBuild.result = 'UNSTABLE'
                            emailext(
                                subject: "Schema Differences Detected - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                                body: """
                                Schema differences have been detected between environments.
                                
                                Please review the attached reports:
                                ${env.BUILD_URL}artifact/reports/
                                
                                Jenkins Build: ${env.BUILD_URL}
                                """,
                                to: env.NOTIFICATION_EMAIL,
                                attachmentsPattern: 'reports/**/*.html'
                            )
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        
        failure {
            emailext(
                subject: "Schema Diff Pipeline Failed - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                The schema difference pipeline has failed.
                
                Please check the Jenkins console output:
                ${env.BUILD_URL}console
                """,
                to: env.NOTIFICATION_EMAIL
            )
        }
    }
}
```

## トラブルシューティング例

### 1. 接続問題の診断

```bash
# ステップ1: 基本的な接続確認
pgsd list-schemas --host prod.example.com --db myapp --user readonly

# ステップ2: 詳細ログでの診断
pgsd compare --verbose \
  --source-host prod.example.com --source-db myapp \
  --target-host staging.example.com --target-db myapp

# ステップ3: 設定ファイルの検証
pgsd validate --config config.yaml

# ステップ4: ネットワーク接続確認
telnet prod.example.com 5432
```

### 2. 権限エラーの解決

```bash
# エラー例: permission denied for schema public
# 解決策: データベース側での権限付与確認

# PostgreSQL側で実行
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO readonly_user;

# 再実行
pgsd compare \
  --source-host localhost --source-db myapp --source-user readonly_user \
  --target-host localhost --target-db myapp_test --target-user readonly_user
```

### 3. パフォーマンス問題の対処

```bash
# 大きなデータベースでの最適化
pgsd compare \
  --schema app_data \  # 特定スキーマのみ
  --source-host localhost --source-db large_db \
  --target-host localhost --target-db large_db_copy \
  --format json \      # 軽量フォーマット
  --quiet             # ログ出力削減
```

## アドバンスド使用例

### 1. 条件付きスキーマ比較

**scripts/conditional-comparison.sh:**
```bash
#!/bin/bash

# 前回の比較結果と比べて差分がある場合のみ詳細レポート生成
set -euo pipefail

QUICK_REPORT="/tmp/schema_quick_check.json"
DETAILED_REPORT_DIR="/var/reports/detailed/$(date +%Y%m%d_%H%M%S)"

# 高速チェック（JSON形式）
echo "🔍 Quick schema check..."
pgsd compare \
    --config config/production.yaml \
    --format json \
    --output /tmp \
    --quiet

# 前回結果との比較
if [[ -f "/var/cache/pgsd/last_result.json" ]]; then
    if diff -q "$QUICK_REPORT" "/var/cache/pgsd/last_result.json" > /dev/null; then
        echo "✅ No changes detected since last check"
        exit 0
    fi
fi

# 差分があった場合の詳細レポート生成
echo "📊 Changes detected, generating detailed report..."
mkdir -p "$DETAILED_REPORT_DIR"

pgsd compare \
    --config config/production.yaml \
    --format html \
    --output "$DETAILED_REPORT_DIR" \
    --verbose

# 結果をキャッシュ
mkdir -p "/var/cache/pgsd"
cp "$QUICK_REPORT" "/var/cache/pgsd/last_result.json"

echo "📄 Detailed report: $DETAILED_REPORT_DIR"
```

### 2. 多段階環境の連鎖比較

**scripts/pipeline-comparison.sh:**
```bash
#!/bin/bash

# 開発 → テスト → ステージング → 本番の連鎖比較
set -euo pipefail

# 環境定義
ENVIRONMENTS=("dev" "test" "staging" "prod")
BASE_OUTPUT_DIR="/var/reports/pipeline/$(date +%Y%m%d_%H%M%S)"

declare -A RESULTS=()

# 連続比較実行
for i in $(seq 0 $((${#ENVIRONMENTS[@]} - 2))); do
    source_env="${ENVIRONMENTS[$i]}"
    target_env="${ENVIRONMENTS[$((i + 1))]}"
    comparison_name="${source_env}_to_${target_env}"
    output_dir="${BASE_OUTPUT_DIR}/${comparison_name}"
    
    echo "🔄 Comparing: $source_env → $target_env"
    
    mkdir -p "$output_dir"
    
    if pgsd compare \
        --config "config/${source_env}.yaml" \
        --target-host "$(get_host $target_env)" \
        --target-db "$(get_database $target_env)" \
        --output "$output_dir" \
        --format json \
        --quiet; then
        
        # 差分数を取得
        diff_count=$(jq '.summary.total_differences' "$output_dir"/*.json)
        RESULTS["$comparison_name"]="$diff_count differences"
        echo "✅ $comparison_name: $diff_count differences found"
    else
        RESULTS["$comparison_name"]="FAILED"
        echo "❌ $comparison_name: FAILED"
    fi
done

# パイプライン全体のサマリー生成
echo ""
echo "📊 Pipeline Comparison Summary"
echo "=============================="
for comparison in "${!RESULTS[@]}"; do
    printf "  %-20s: %s\n" "$comparison" "${RESULTS[$comparison]}"
done

# 統合レポート生成
generate_pipeline_report "$BASE_OUTPUT_DIR"
```

### 3. スキーマ進化の追跡

**scripts/schema-evolution-tracker.sh:**
```bash
#!/bin/bash

# スキーマの進化を時系列で追跡
set -euo pipefail

TRACKING_DIR="/var/lib/pgsd/evolution"
DATABASE_ID="production_myapp"
SNAPSHOT_FILE="$TRACKING_DIR/${DATABASE_ID}_$(date +%Y%m%d_%H%M%S).json"

# 現在のスキーマスナップショット作成
mkdir -p "$TRACKING_DIR"

pgsd compare \
    --source-host prod.example.com --source-db myapp \
    --target-host prod.example.com --target-db myapp \
    --format json \
    --output /tmp/current_snapshot

# スナップショット保存
cp /tmp/current_snapshot/*.json "$SNAPSHOT_FILE"

# 過去のスナップショットと比較
PREVIOUS_SNAPSHOT=$(ls -t "$TRACKING_DIR/${DATABASE_ID}"_*.json 2>/dev/null | sed -n '2p')

if [[ -n "$PREVIOUS_SNAPSHOT" && -f "$PREVIOUS_SNAPSHOT" ]]; then
    echo "📈 Comparing with previous snapshot: $(basename "$PREVIOUS_SNAPSHOT")"
    
    # 変更履歴レポート生成
    python3 << EOF
import json
import sys
from datetime import datetime

# スナップショット読み込み
with open('$SNAPSHOT_FILE', 'r') as f:
    current = json.load(f)
with open('$PREVIOUS_SNAPSHOT', 'r') as f:
    previous = json.load(f)

# 変更履歴分析
print("🔍 Schema Evolution Analysis")
print("=" * 40)
print(f"Previous: {previous.get('timestamp', 'unknown')}")
print(f"Current:  {current.get('timestamp', 'unknown')}")
print()

# テーブル変更の分析
current_tables = set(current.get('tables', {}).keys())
previous_tables = set(previous.get('tables', {}).keys())

added_tables = current_tables - previous_tables
removed_tables = previous_tables - current_tables

if added_tables:
    print(f"📝 Added Tables ({len(added_tables)}):")
    for table in sorted(added_tables):
        print(f"  + {table}")

if removed_tables:
    print(f"🗑️  Removed Tables ({len(removed_tables)}):")
    for table in sorted(removed_tables):
        print(f"  - {table}")

print()
print(f"📊 Total Tables: {len(previous_tables)} → {len(current_tables)}")
EOF

else
    echo "📝 First snapshot created: $(basename "$SNAPSHOT_FILE")"
fi

# 古いスナップショットのクリーンアップ（90日より古い）
find "$TRACKING_DIR" -name "${DATABASE_ID}_*.json" -mtime +90 -delete
```

これらの使用例を参考に、PGSDを様々な場面で効果的に活用してください。各例は実際のユースケースに基づいており、カスタマイズして使用することができます。