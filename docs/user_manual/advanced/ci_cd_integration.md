# CI/CD統合

PGSDを継続的インテグレーション・継続的デプロイメント（CI/CD）パイプラインに統合する方法を説明します。

## 🎯 この章で学ぶこと

- CI/CDパイプラインでのPGSD活用
- 各種CI/CDツールとの統合方法
- 自動化されたスキーマ検証
- 失敗時の通知とロールバック

## 🔄 CI/CDでのPGSD活用シナリオ

### 1. プルリクエスト時の自動検証
- **目的**: コードマージ前のスキーマ変更確認
- **タイミング**: PR作成・更新時
- **アクション**: 差分レポート生成、重要変更の検出

### 2. デプロイ前の最終確認
- **目的**: 本番デプロイ前の最終検証
- **タイミング**: ステージング環境デプロイ後
- **アクション**: 本番との差分確認、マイグレーション準備

### 3. デプロイ後の整合性確認
- **目的**: デプロイ成功の確認
- **タイミング**: 本番デプロイ完了後
- **アクション**: 期待値との比較、ロールバック判定

## 🐙 GitHub Actions統合

### 基本ワークフロー

```yaml
# .github/workflows/schema-check.yml
name: Database Schema Validation

on:
  pull_request:
    branches: [ main, develop ]
    paths: 
      - 'migrations/**'
      - 'schema/**'
  
  push:
    branches: [ main ]

jobs:
  schema-validation:
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

      - name: Setup test databases
        run: |
          # ベーススキーマ適用（現在のmain）
          psql -h localhost -p 5432 -U postgres -d source_db < schema/base.sql
          
          # ターゲットスキーマ適用（PR変更後）
          psql -h localhost -p 5433 -U postgres -d target_db < schema/target.sql

      - name: Run schema comparison
        id: schema_comparison
        run: |
          pgsd compare \
            --source-host localhost --source-port 5432 --source-db source_db \
            --source-user postgres --source-password postgres \
            --target-host localhost --target-port 5433 --target-db target_db \
            --target-user postgres --target-password postgres \
            --format json \
            --output ./schema-diff-report \
            --quiet

      - name: Analyze results
        id: analyze
        run: |
          REPORT_FILE="./schema-diff-report/schema_diff_*.json"
          
          # 重要な変更の検出
          CRITICAL_CHANGES=$(jq -r '
            (.differences.tables.removed // []) + 
            (.differences.columns.removed // []) +
            (.differences.foreign_keys.removed // [])
            | length
          ' $REPORT_FILE)
          
          echo "critical_changes=$CRITICAL_CHANGES" >> $GITHUB_OUTPUT
          
          # レポート要約作成
          jq -r '
            "## 📊 Schema Comparison Summary\n\n" +
            "**Tables:** " + (.summary.categories.tables.identical // 0 | tostring) + " identical, " + 
                           (.summary.categories.tables.modified // 0 | tostring) + " modified, " +
                           (.summary.categories.tables.added // 0 | tostring) + " added, " +
                           (.summary.categories.tables.removed // 0 | tostring) + " removed\n\n" +
            "**Columns:** " + (.summary.categories.columns.identical // 0 | tostring) + " identical, " + 
                            (.summary.categories.columns.modified // 0 | tostring) + " modified, " +
                            (.summary.categories.columns.added // 0 | tostring) + " added, " +
                            (.summary.categories.columns.removed // 0 | tostring) + " removed\n\n" +
            (if (.summary.total_differences // 0) > 0 then
              "⚠️ **" + (.summary.total_differences | tostring) + " differences detected**\n\n" +
              "[View full report](" + "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}" + ")"
            else
              "✅ **No differences detected**"
            end)
          ' $REPORT_FILE > schema_summary.md

      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('schema_summary.md', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: schema-diff-report
          path: ./schema-diff-report/

      - name: Fail on critical changes
        if: steps.analyze.outputs.critical_changes > 0
        run: |
          echo "❌ Critical schema changes detected!"
          echo "Tables/columns/foreign keys have been removed."
          echo "Please review the changes and ensure they are intentional."
          exit 1
```

### マトリックス戦略での複数環境テスト

```yaml
# .github/workflows/multi-env-schema-check.yml
name: Multi-Environment Schema Check

on:
  schedule:
    - cron: '0 6 * * *'  # 毎日午前6時
  workflow_dispatch:

jobs:
  schema-comparison:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        comparison:
          - name: "prod-vs-staging"
            source: "production"
            target: "staging"
          - name: "staging-vs-dev"
            source: "staging"
            target: "development"
        
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install PGSD
        run: pip install pgsd

      - name: Run comparison
        env:
          PGSD_SOURCE_HOST: ${{ secrets[format('DB_HOST_{0}', matrix.comparison.source)] }}
          PGSD_SOURCE_PASSWORD: ${{ secrets[format('DB_PASSWORD_{0}', matrix.comparison.source)] }}
          PGSD_TARGET_HOST: ${{ secrets[format('DB_HOST_{0}', matrix.comparison.target)] }}
          PGSD_TARGET_PASSWORD: ${{ secrets[format('DB_PASSWORD_{0}', matrix.comparison.target)] }}
        run: |
          pgsd compare \
            --source-host "$PGSD_SOURCE_HOST" \
            --source-db myapp \
            --source-user readonly \
            --source-password "$PGSD_SOURCE_PASSWORD" \
            --target-host "$PGSD_TARGET_HOST" \
            --target-db myapp \
            --target-user readonly \
            --target-password "$PGSD_TARGET_PASSWORD" \
            --format html \
            --output "./reports/${{ matrix.comparison.name }}"

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: schema-reports-${{ matrix.comparison.name }}
          path: ./reports/${{ matrix.comparison.name }}/
```

## 🦊 GitLab CI統合

### 基本パイプライン

```yaml
# .gitlab-ci.yml
stages:
  - test
  - schema-validation
  - deploy

variables:
  POSTGRES_DB: test_db
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres

services:
  - postgres:15

schema-validation:
  stage: schema-validation
  image: python:3.11
  
  before_script:
    - pip install pgsd psycopg2-binary
    - apt-get update && apt-get install -y postgresql-client

  script:
    # テストデータベース準備
    - |
      PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB << 'EOF'
      CREATE SCHEMA IF NOT EXISTS source_schema;
      CREATE SCHEMA IF NOT EXISTS target_schema;
      EOF
    
    # ベースライン適用
    - PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -c "\set ON_ERROR_STOP on" -f schema/baseline.sql
    
    # 変更適用
    - PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -c "\set ON_ERROR_STOP on" -f migrations/latest.sql
    
    # スキーマ比較実行
    - |
      pgsd compare \
        --source-host postgres --source-db $POSTGRES_DB --source-user $POSTGRES_USER \
        --source-password $POSTGRES_PASSWORD --schema source_schema \
        --target-host postgres --target-db $POSTGRES_DB --target-user $POSTGRES_USER \
        --target-password $POSTGRES_PASSWORD --schema target_schema \
        --format json --output ./schema-reports/
    
    # 結果分析
    - |
      python << 'EOF'
      import json
      import sys
      
      with open('./schema-reports/schema_diff_*.json', 'r') as f:
          report = json.load(f)
      
      critical_changes = report.get('summary', {}).get('severity_breakdown', {}).get('critical', 0)
      
      if critical_changes > 0:
          print(f"❌ {critical_changes} critical changes detected!")
          sys.exit(1)
      else:
          print("✅ Schema validation passed")
      EOF

  artifacts:
    reports:
      junit: schema-reports/*.xml
    paths:
      - schema-reports/
    expire_in: 1 week
  
  only:
    - merge_requests
    - main

# 本番デプロイ前の最終確認
pre-production-validation:
  stage: deploy
  image: python:3.11
  
  before_script:
    - pip install pgsd
  
  script:
    - |
      pgsd compare \
        --source-host $STAGING_DB_HOST --source-db myapp \
        --source-user $DB_USER --source-password $STAGING_DB_PASSWORD \
        --target-host $PROD_DB_HOST --target-db myapp \
        --target-user $DB_USER --target-password $PROD_DB_PASSWORD \
        --format html --output ./final-validation/
  
  artifacts:
    paths:
      - final-validation/
    expire_in: 30 days
  
  only:
    - main
  
  when: manual
```

## 🔨 Jenkins統合

### 宣言的パイプライン

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        PGSD_VERSION = '1.0.0'
        REPORT_DIR = "${WORKSPACE}/schema-reports"
    }
    
    triggers {
        pollSCM('H/15 * * * *')  // 15分ごとにSCMポーリング
        cron('H 2 * * *')        // 毎日午前2時
    }
    
    stages {
        stage('Preparation') {
            steps {
                checkout scm
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install pgsd==${PGSD_VERSION}
                '''
            }
        }
        
        stage('Schema Validation') {
            parallel {
                stage('Development vs Staging') {
                    steps {
                        script {
                            def reportDir = "${REPORT_DIR}/dev-vs-staging"
                            sh """
                                mkdir -p ${reportDir}
                                . venv/bin/activate
                                pgsd compare \\
                                    --source-host ${DEV_DB_HOST} --source-db myapp \\
                                    --source-user \$DB_USER --source-password \$DEV_DB_PASSWORD \\
                                    --target-host ${STAGING_DB_HOST} --target-db myapp \\
                                    --target-user \$DB_USER --target-password \$STAGING_DB_PASSWORD \\
                                    --format json --output ${reportDir}
                            """
                            
                            // 結果分析
                            def reportFile = sh(
                                script: "find ${reportDir} -name '*.json' | head -1",
                                returnStdout: true
                            ).trim()
                            
                            def report = readJSON file: reportFile
                            def criticalChanges = report.summary?.severity_breakdown?.critical ?: 0
                            
                            if (criticalChanges > 0) {
                                currentBuild.result = 'UNSTABLE'
                                env.CRITICAL_CHANGES_DEV_STAGING = criticalChanges.toString()
                            }
                        }
                    }
                }
                
                stage('Staging vs Production') {
                    steps {
                        script {
                            def reportDir = "${REPORT_DIR}/staging-vs-prod"
                            sh """
                                mkdir -p ${reportDir}
                                . venv/bin/activate
                                pgsd compare \\
                                    --source-host ${STAGING_DB_HOST} --source-db myapp \\
                                    --source-user \$DB_USER --source-password \$STAGING_DB_PASSWORD \\
                                    --target-host ${PROD_DB_HOST} --target-db myapp \\
                                    --target-user \$DB_USER --target-password \$PROD_DB_PASSWORD \\
                                    --format html --output ${reportDir}
                            """
                        }
                    }
                }
            }
        }
        
        stage('Report Generation') {
            steps {
                sh '''
                    . venv/bin/activate
                    python scripts/generate-consolidated-report.py
                '''
                
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: "${REPORT_DIR}",
                    reportFiles: 'consolidated-report.html',
                    reportName: 'Schema Diff Report'
                ])
            }
        }
        
        stage('Notification') {
            steps {
                script {
                    def message = "Schema validation completed"
                    def color = "good"
                    
                    if (env.CRITICAL_CHANGES_DEV_STAGING) {
                        message = "⚠️ Critical changes detected: ${env.CRITICAL_CHANGES_DEV_STAGING} between dev and staging"
                        color = "warning"
                    }
                    
                    slackSend(
                        channel: '#database-changes',
                        color: color,
                        message: message,
                        teamDomain: 'your-team',
                        tokenCredentialId: 'slack-token'
                    )
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'schema-reports/**/*', fingerprint: true
            cleanWs()
        }
        
        failure {
            emailext(
                subject: "Schema Validation Failed - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                The schema validation pipeline has failed.
                
                Build URL: ${env.BUILD_URL}
                Console Output: ${env.BUILD_URL}console
                
                Please check the schema differences and take appropriate action.
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL}, database-team@company.com"
            )
        }
    }
}
```

## ☁️ Azure DevOps統合

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - migrations/*
      - schema/*

pr:
  branches:
    include:
      - main
  paths:
    include:
      - migrations/*
      - schema/*

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.11'
  pgsdVersion: '1.0.0'

stages:
- stage: SchemaValidation
  displayName: 'Schema Validation'
  jobs:
  - job: CompareSchemas
    displayName: 'Compare Database Schemas'
    
    services:
      postgres-source:
        image: postgres:15
        env:
          POSTGRES_DB: source_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
      
      postgres-target:
        image: postgres:15
        env:
          POSTGRES_DB: target_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5433:5432
    
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
        displayName: 'Use Python $(pythonVersion)'

    - script: |
        python -m pip install --upgrade pip
        pip install pgsd==$(pgsdVersion)
      displayName: 'Install PGSD'

    - script: |
        # データベース準備
        PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d source_db < schema/baseline.sql
        PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d target_db < schema/current.sql
      displayName: 'Prepare test databases'

    - script: |
        pgsd compare \
          --source-host localhost --source-port 5432 --source-db source_db \
          --source-user postgres --source-password postgres \
          --target-host localhost --target-port 5433 --target-db target_db \
          --target-user postgres --target-password postgres \
          --format json \
          --output $(Agent.TempDirectory)/schema-reports
      displayName: 'Run schema comparison'

    - task: PythonScript@0
      inputs:
        scriptSource: 'inline'
        script: |
          import json
          import glob
          import os
          
          # レポートファイル検索
          report_files = glob.glob('$(Agent.TempDirectory)/schema-reports/*.json')
          if not report_files:
              print("No report files found!")
              exit(1)
          
          # 最新レポート読み込み
          with open(report_files[0], 'r') as f:
              report = json.load(f)
          
          # Azure DevOps変数設定
          total_differences = report.get('summary', {}).get('total_differences', 0)
          critical_changes = report.get('summary', {}).get('severity_breakdown', {}).get('critical', 0)
          
          print(f"##vso[task.setvariable variable=totalDifferences]{total_differences}")
          print(f"##vso[task.setvariable variable=criticalChanges]{critical_changes}")
          
          # レポート要約作成
          summary = f"""
          ## Schema Comparison Results
          
          - **Total Differences:** {total_differences}
          - **Critical Changes:** {critical_changes}
          - **Tables Modified:** {report.get('summary', {}).get('categories', {}).get('tables', {}).get('modified', 0)}
          - **Columns Modified:** {report.get('summary', {}).get('categories', {}).get('columns', {}).get('modified', 0)}
          """
          
          with open('$(Agent.TempDirectory)/schema-summary.md', 'w') as f:
              f.write(summary)
      displayName: 'Analyze results'

    - task: PublishBuildArtifacts@1
      inputs:
        pathToPublish: '$(Agent.TempDirectory)/schema-reports'
        artifactName: 'schema-diff-reports'
      displayName: 'Publish schema reports'

    - script: |
        if [ "$(criticalChanges)" -gt "0" ]; then
          echo "❌ Critical schema changes detected!"
          echo "##vso[task.logissue type=error]Critical changes found: $(criticalChanges)"
          exit 1
        else
          echo "✅ No critical changes detected"
        fi
      displayName: 'Validate changes'
      condition: always()
```

## 🚀 Kubernetes/Helm統合

### Helm Hookでのスキーマ検証

```yaml
# templates/schema-validation-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ include "myapp.fullname" . }}-schema-validation"
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "{{ include "myapp.fullname" . }}-schema-validation"
    spec:
      restartPolicy: Never
      containers:
      - name: schema-validator
        image: python:3.11-slim
        command:
          - /bin/bash
          - -c
          - |
            pip install pgsd
            
            pgsd compare \
              --source-host {{ .Values.database.current.host }} \
              --source-db {{ .Values.database.current.name }} \
              --source-user {{ .Values.database.current.user }} \
              --source-password {{ .Values.database.current.password }} \
              --target-host {{ .Values.database.target.host }} \
              --target-db {{ .Values.database.target.name }} \
              --target-user {{ .Values.database.target.user }} \
              --target-password {{ .Values.database.target.password }} \
              --format json \
              --output /tmp/reports
            
            # 重要な変更の検出
            CRITICAL_CHANGES=$(jq -r '.summary.severity_breakdown.critical // 0' /tmp/reports/*.json)
            
            if [ "$CRITICAL_CHANGES" -gt "0" ]; then
              echo "❌ Critical schema changes detected: $CRITICAL_CHANGES"
              echo "Deployment will be halted for manual review."
              exit 1
            fi
            
            echo "✅ Schema validation passed"
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ include "myapp.fullname" . }}-db-secret
              key: password
        volumeMounts:
        - name: reports
          mountPath: /tmp/reports
      volumes:
      - name: reports
        emptyDir: {}
```

## 📊 監視とアラート

### Prometheus メトリクス

```python
# scripts/pgsd-metrics-exporter.py
import json
import time
from prometheus_client import start_http_server, Gauge, Counter

# メトリクス定義
schema_differences_total = Gauge('pgsd_schema_differences_total', 'Total schema differences')
critical_changes_total = Gauge('pgsd_critical_changes_total', 'Critical schema changes')
comparison_duration_seconds = Gauge('pgsd_comparison_duration_seconds', 'Comparison duration')
comparison_success_total = Counter('pgsd_comparison_success_total', 'Successful comparisons')
comparison_failure_total = Counter('pgsd_comparison_failure_total', 'Failed comparisons')

def export_metrics_from_report(report_file):
    """レポートファイルからメトリクスを出力"""
    try:
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        # メトリクス更新
        total_diff = report.get('summary', {}).get('total_differences', 0)
        critical = report.get('summary', {}).get('severity_breakdown', {}).get('critical', 0)
        
        schema_differences_total.set(total_diff)
        critical_changes_total.set(critical)
        comparison_success_total.inc()
        
    except Exception as e:
        comparison_failure_total.inc()
        print(f"Error processing report: {e}")

if __name__ == '__main__':
    start_http_server(8000)
    print("Metrics server started on port 8000")
    
    while True:
        time.sleep(60)
```

### Grafana ダッシュボード設定

```json
{
  "dashboard": {
    "title": "PGSD Schema Monitoring",
    "panels": [
      {
        "title": "Schema Differences Over Time",
        "type": "graph",
        "targets": [
          {
            "expr": "pgsd_schema_differences_total",
            "legendFormat": "Total Differences"
          },
          {
            "expr": "pgsd_critical_changes_total", 
            "legendFormat": "Critical Changes"
          }
        ]
      },
      {
        "title": "Comparison Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(pgsd_comparison_success_total[5m]) / (rate(pgsd_comparison_success_total[5m]) + rate(pgsd_comparison_failure_total[5m])) * 100"
          }
        ]
      }
    ]
  }
}
```

## 🚀 次のステップ

CI/CD統合を理解したら：

1. **[スクリプト活用](scripting.md)** - 高度な自動化スクリプト
2. **[パフォーマンス調整](performance_tuning.md)** - 大規模環境での最適化
3. **[トラブルシューティング](../troubleshooting/common_issues.md)** - 問題解決方法

## 📚 関連資料

- [自動化機能](../features/automation.md)
- [設定リファレンス](../reference/config_reference.md)
- [API リファレンス](../reference/api_reference.md)