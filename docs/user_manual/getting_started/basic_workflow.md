# 基本ワークフロー

PGSDを日常的に使用する基本的なワークフローについて説明します。

## 🎯 この章で学ぶこと

- 効率的な日常ワークフロー
- 設定ファイルの活用
- レポート管理のベストプラクティス
- 自動化の基礎

## 📋 基本的なワークフロー

### フェーズ1: 準備
1. **設定ファイルの作成**
2. **データベース接続の確認**
3. **出力ディレクトリの設定**

### フェーズ2: 実行
1. **スキーマ比較の実行**
2. **レポートの生成**
3. **結果の確認**

### フェーズ3: 分析・アクション
1. **差分の分析**
2. **必要な対応の決定**
3. **ドキュメント化**

## ⚙️ 設定ファイルでの効率化

### 基本設定ファイルの作成

日常使用のため、設定ファイルを作成します：

```yaml
# config/daily-comparison.yaml
databases:
  source:
    host: production.company.com
    port: 5432
    database: myapp_production
    user: readonly_user
    password: "${PROD_DB_PASSWORD}"
    schema: public
  
  target:
    host: staging.company.com
    port: 5432
    database: myapp_staging
    user: readonly_user
    password: "${STAGING_DB_PASSWORD}"
    schema: public

output:
  format: html
  directory: ./daily-reports
  filename_template: "daily_comparison_{timestamp}"

logging:
  level: INFO
  console: true
```

### 環境変数の設定

機密情報を環境変数で管理：

```bash
# .env ファイル または ~/.bashrc
export PROD_DB_PASSWORD="your_production_password"
export STAGING_DB_PASSWORD="your_staging_password"
export PGSD_CONFIG_FILE="./config/daily-comparison.yaml"
```

### 設定ファイルを使った実行

```bash
# 設定ファイルで実行
pgsd compare --config config/daily-comparison.yaml

# 設定ファイル + オプション上書き
pgsd compare --config config/daily-comparison.yaml --format markdown
```

## 🗓️ 日常的な使用パターン

### パターン1: 毎日の差分チェック

**目的**: 開発環境と本番環境の同期確認

```bash
#!/bin/bash
# scripts/daily-check.sh

# 日付ディレクトリ作成
mkdir -p reports/$(date +%Y%m%d)

# 比較実行
pgsd compare \
  --config config/prod-vs-staging.yaml \
  --output reports/$(date +%Y%m%d) \
  --format html

# レポート確認
echo "Report generated: reports/$(date +%Y%m%d)/schema_diff_*.html"
```

### パターン2: リリース前チェック

**目的**: リリース前のスキーマ差分確認

```bash
#!/bin/bash
# scripts/pre-release-check.sh

RELEASE_VERSION="v1.2.0"
REPORT_DIR="reports/release-checks/$RELEASE_VERSION"

mkdir -p "$REPORT_DIR"

# 本番 vs ステージング
pgsd compare \
  --config config/prod-vs-staging.yaml \
  --output "$REPORT_DIR" \
  --format html

# ステージング vs 開発
pgsd compare \
  --config config/staging-vs-dev.yaml \
  --output "$REPORT_DIR" \
  --format markdown

echo "Release check completed: $REPORT_DIR"
```

### パターン3: マイグレーション後検証

**目的**: データベースマイグレーション後の検証

```bash
#!/bin/bash
# scripts/post-migration-check.sh

MIGRATION_ID="20250715_001"
BACKUP_HOST="backup.company.com"

# マイグレーション前のバックアップと比較
pgsd compare \
  --source-host "$BACKUP_HOST" \
  --source-db "myapp_pre_migration" \
  --target-host "production.company.com" \
  --target-db "myapp_production" \
  --output "reports/migration-$MIGRATION_ID" \
  --format html
```

## 📊 レポート管理のベストプラクティス

### ディレクトリ構造の設計

```
reports/
├── daily/
│   ├── 20250715/
│   ├── 20250714/
│   └── 20250713/
├── releases/
│   ├── v1.2.0/
│   ├── v1.1.9/
│   └── v1.1.8/
├── migrations/
│   ├── 20250715_001/
│   └── 20250710_001/
└── ad-hoc/
    ├── feature-branch-check/
    └── emergency-check/
```

### レポート生成スクリプト

```bash
#!/bin/bash
# scripts/generate-reports.sh

DATE=$(date +%Y%m%d)
TIME=$(date +%H%M%S)

# 複数形式のレポート生成
generate_reports() {
  local config_file=$1
  local output_dir=$2
  local description=$3
  
  echo "🔍 Generating $description reports..."
  
  # HTML（閲覧用）
  pgsd compare --config "$config_file" \
    --output "$output_dir" --format html
  
  # Markdown（Git管理用）
  pgsd compare --config "$config_file" \
    --output "$output_dir" --format markdown
  
  # JSON（プログラム処理用）
  pgsd compare --config "$config_file" \
    --output "$output_dir" --format json
}

# 各環境の比較実行
generate_reports "config/prod-vs-staging.yaml" \
  "reports/daily/$DATE" "prod vs staging"

generate_reports "config/staging-vs-dev.yaml" \
  "reports/daily/$DATE" "staging vs dev"

echo "✅ All reports generated in reports/daily/$DATE"
```

### レポートの自動アーカイブ

```bash
#!/bin/bash
# scripts/archive-old-reports.sh

# 30日より古いレポートをアーカイブ
find reports/daily -type d -mtime +30 -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \;

# 90日より古いアーカイブを削除
find reports/daily -name "*.tar.gz" -mtime +90 -delete

echo "Old reports archived and cleaned up"
```

## 🔄 継続的な監視

### スキーマ変更の追跡

```bash
#!/bin/bash
# scripts/track-schema-changes.sh

CURRENT_REPORT="reports/current/schema_diff.json"
PREVIOUS_REPORT="reports/previous/schema_diff.json"

# 現在の状態を取得
pgsd compare \
  --config config/prod-vs-staging.yaml \
  --format json \
  --output reports/current

# 前回との差分確認
if [ -f "$PREVIOUS_REPORT" ]; then
  if ! diff -q "$CURRENT_REPORT" "$PREVIOUS_REPORT" > /dev/null; then
    echo "⚠️  Schema changes detected!"
    echo "Differences:"
    diff "$CURRENT_REPORT" "$PREVIOUS_REPORT"
    
    # 通知送信（例：Slack）
    send_notification "Schema changes detected in production"
  else
    echo "✅ No schema changes detected"
  fi
fi

# 現在を前回として保存
cp "$CURRENT_REPORT" "$PREVIOUS_REPORT"
```

### 定期実行の設定

```bash
# crontab設定例
# 毎日午前6時に実行
0 6 * * * /path/to/scripts/daily-check.sh

# 平日の午後6時に実行
0 18 * * 1-5 /path/to/scripts/track-schema-changes.sh

# 毎週日曜日にアーカイブ
0 2 * * 0 /path/to/scripts/archive-old-reports.sh
```

## 🚨 アラート設定

### 重要な変更の検出

```bash
#!/bin/bash
# scripts/critical-change-detector.sh

REPORT_FILE="reports/current/schema_diff.json"

# 重要な変更をチェック
check_critical_changes() {
  # テーブル削除の検出
  if jq -e '.tables.removed | length > 0' "$REPORT_FILE" > /dev/null; then
    echo "🚨 CRITICAL: Tables have been removed!"
    jq '.tables.removed[]' "$REPORT_FILE"
    return 1
  fi
  
  # カラム削除の検出
  if jq -e '.columns.removed | length > 0' "$REPORT_FILE" > /dev/null; then
    echo "⚠️  WARNING: Columns have been removed!"
    jq '.columns.removed[]' "$REPORT_FILE"
    return 1
  fi
  
  # インデックス削除の検出
  if jq -e '.indexes.removed | length > 0' "$REPORT_FILE" > /dev/null; then
    echo "ℹ️  INFO: Indexes have been removed"
    jq '.indexes.removed[]' "$REPORT_FILE"
  fi
  
  return 0
}

# チェック実行
if ! check_critical_changes; then
  # 緊急通知
  send_urgent_notification "Critical database schema changes detected"
fi
```

## 📋 チーム運用でのワークフロー

### 開発チーム向けワークフロー

1. **機能開発時**
   ```bash
   # 機能ブランチでの変更確認
   pgsd compare \
     --source-host localhost --source-db main_branch \
     --target-host localhost --target-db feature_branch \
     --output reports/feature-$(git branch --show-current)
   ```

2. **プルリクエスト時**
   ```bash
   # PR作成時の自動チェック
   pgsd compare \
     --config config/pr-check.yaml \
     --output reports/pr-$(git rev-parse --short HEAD) \
     --format markdown
   ```

### 運用チーム向けワークフロー

1. **デプロイ前確認**
   ```bash
   # デプロイ前の最終確認
   pgsd compare \
     --config config/pre-deploy.yaml \
     --format html \
     --output reports/deploy-$(date +%Y%m%d-%H%M%S)
   ```

2. **インシデント調査**
   ```bash
   # 問題発生時の緊急比較
   pgsd compare \
     --source-host backup.company.com --source-db incident_backup \
     --target-host production.company.com --target-db current \
     --output reports/incident-$(date +%Y%m%d-%H%M%S) \
     --format json
   ```

## 💡 効率化のヒント

### 1. エイリアスの活用
```bash
# ~/.bashrc または ~/.zshrc
alias pgsd-daily="pgsd compare --config config/daily.yaml"
alias pgsd-release="pgsd compare --config config/release-check.yaml"
alias pgsd-quick="pgsd compare --format json --quiet"
```

### 2. スクリプトのテンプレート化
```bash
# templates/comparison-template.sh
#!/bin/bash
CONFIG_FILE="${1:-config/default.yaml}"
OUTPUT_DIR="${2:-reports/$(date +%Y%m%d)}"
FORMAT="${3:-html}"

pgsd compare \
  --config "$CONFIG_FILE" \
  --output "$OUTPUT_DIR" \
  --format "$FORMAT"
```

### 3. 設定ファイルの環境別管理
```
config/
├── base.yaml          # 共通設定
├── development.yaml   # 開発環境
├── staging.yaml       # ステージング環境
├── production.yaml    # 本番環境
└── local.yaml         # ローカル開発用
```

## 🔍 トラブルシューティング

### よくある問題と解決法

#### 1. レポート生成の失敗
```bash
# 詳細ログで原因調査
pgsd compare --verbose --config config/problematic.yaml

# 接続テスト
pgsd list-schemas --host your-host --db your-db --user your-user
```

#### 2. パフォーマンス問題
```bash
# 特定スキーマのみ比較
pgsd compare --schema specific_schema --config config/default.yaml

# 軽量フォーマットで実行
pgsd compare --format json --quiet --config config/default.yaml
```

#### 3. 権限エラー
```sql
-- 最小権限の確認
SELECT 
  schemaname,
  has_schema_privilege('your_user', schemaname, 'USAGE') as schema_access,
  has_table_privilege('your_user', schemaname||'.table_name', 'SELECT') as table_access
FROM pg_tables 
WHERE schemaname = 'public';
```

## 🚀 次のステップ

基本ワークフローを習得したら：

1. **[設定ファイル詳細](../configuration/config_file.md)** - 高度な設定方法
2. **[自動化機能](../features/automation.md)** - CI/CD統合
3. **[パフォーマンス調整](../advanced/performance_tuning.md)** - 大規模環境での最適化

## 📚 関連資料

- [設定リファレンス](../reference/config_reference.md)
- [CLIコマンド](../reference/cli_commands.md)
- [トラブルシューティング](../troubleshooting/common_issues.md)