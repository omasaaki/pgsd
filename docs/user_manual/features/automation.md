# 自動化機能

PGSDの自動化機能を活用して、継続的なスキーマ監視と分析を実現する方法について説明します。

## 🎯 この章で学ぶこと

- 定期実行の設定方法
- 通知システムの構築
- 自動レポート配信
- CI/CDパイプラインとの統合

## ⏰ 定期実行の設定

### cronベースの基本設定

```bash
# crontab設定例
# 毎日午前6時に本番とステージングの比較
0 6 * * * /usr/local/bin/pgsd compare --config /etc/pgsd/daily-check.yaml

# 平日の午後6時に開発環境の変更チェック
0 18 * * 1-5 /usr/local/bin/pgsd compare --config /etc/pgsd/dev-check.yaml

# 毎週日曜日午前2時に週次レポート生成
0 2 * * 0 /usr/local/bin/pgsd weekly-report --config /etc/pgsd/weekly.yaml

# 月初1日午前1時に月次アーカイブ
0 1 1 * * /usr/local/bin/pgsd archive --older-than 30days
```

### systemdタイマーの活用

```ini
# /etc/systemd/system/pgsd-daily.service
[Unit]
Description=PGSD Daily Schema Comparison
Wants=pgsd-daily.timer

[Service]
Type=oneshot
User=pgsd
Group=pgsd
WorkingDirectory=/var/lib/pgsd
Environment=PGSD_CONFIG_FILE=/etc/pgsd/daily.yaml
ExecStart=/usr/local/bin/pgsd compare --quiet
ExecStartPost=/usr/local/bin/pgsd notify --slack

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/pgsd-daily.timer
[Unit]
Description=Run PGSD daily comparison
Requires=pgsd-daily.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

## 🔄 自動化ワークフロー

### 基本ワークフロー設定

```yaml
# config/automation-workflow.yaml
automation:
  workflows:
    daily_monitoring:
      name: "日次監視"
      schedule: "0 6 * * *"           # 毎日午前6時
      
      steps:
        - name: "production_vs_staging"
          action: "compare"
          config: "configs/prod-staging.yaml"
          
        - name: "analyze_changes"
          action: "analyze"
          input: "previous_step"
          
        - name: "send_notification"
          action: "notify"
          condition: "has_critical_changes"
          target: ["slack", "email"]
          
        - name: "archive_report"
          action: "archive"
          destination: "s3://reports-bucket/daily/"
    
    release_validation:
      name: "リリース検証"
      trigger: "manual"               # 手動実行
      
      steps:
        - name: "pre_release_check"
          action: "compare"
          config: "configs/release-check.yaml"
          
        - name: "impact_analysis"
          action: "analyze"
          analysis_type: "impact"
          
        - name: "generate_report"
          action: "report"
          formats: ["html", "pdf"]
          
        - name: "approval_notification"
          action: "notify"
          target: ["approval_team"]
          require_approval: true
```

### 条件分岐とエラーハンドリング

```yaml
workflow_logic:
  # 条件分岐
  conditional_execution:
    - name: "critical_change_handling"
      condition: "critical_changes > 0"
      actions:
        - send_urgent_notification
        - create_incident_ticket
        - halt_deployment
    
    - name: "normal_change_handling"
      condition: "total_changes > 0 and critical_changes == 0"
      actions:
        - send_summary_notification
        - update_dashboard
    
    - name: "no_change_handling"
      condition: "total_changes == 0"
      actions:
        - log_no_changes
        - update_health_status
  
  # エラーハンドリング
  error_handling:
    connection_failure:
      retry_attempts: 3
      retry_delay: 300              # 5分間隔
      fallback_action: "send_error_alert"
    
    analysis_failure:
      retry_attempts: 1
      fallback_action: "generate_minimal_report"
    
    notification_failure:
      retry_attempts: 2
      fallback_action: "log_to_file"
```

## 📧 通知システム

### 多様な通知チャネル

```yaml
# config/notification-settings.yaml
notifications:
  channels:
    slack:
      enabled: true
      webhook_url: "${SLACK_WEBHOOK_URL}"
      channel: "#database-changes"
      
      # 通知レベル別設定
      levels:
        critical:
          mention: "@channel"
          color: "danger"
        warning:
          mention: "@here"
          color: "warning"
        info:
          color: "good"
      
      # メッセージテンプレート
      templates:
        critical: |
          🚨 *Critical Database Schema Changes Detected*
          
          *Environment:* {{environment}}
          *Changes:* {{critical_count}} critical, {{warning_count}} warning
          *Report:* {{report_url}}
          
          Please review immediately!
    
    email:
      enabled: true
      smtp_host: "smtp.company.com"
      smtp_port: 587
      username: "${EMAIL_USERNAME}"
      password: "${EMAIL_PASSWORD}"
      
      recipients:
        critical: ["dba-team@company.com", "dev-lead@company.com"]
        warning: ["dev-team@company.com"]
        info: ["dev-team@company.com"]
      
      templates:
        subject: "[PGSD] {{severity}} - Schema Changes in {{environment}}"
        body_template: "templates/email-notification.html"
    
    jira:
      enabled: true
      url: "https://company.atlassian.net"
      username: "${JIRA_USERNAME}"
      api_token: "${JIRA_API_TOKEN}"
      project: "DBA"
      
      # 自動チケット作成
      auto_create_ticket:
        critical_changes: true
        warning_threshold: 5          # 警告が5件以上でチケット作成
      
      ticket_template:
        summary: "Database Schema Changes - {{environment}} - {{date}}"
        description: |
          Automated schema comparison detected changes:
          
          - Critical: {{critical_count}}
          - Warning: {{warning_count}}
          - Info: {{info_count}}
          
          Report: {{report_url}}
        labels: ["database", "schema", "automation"]
```

### 通知のカスタマイズ

```yaml
notification_customization:
  # 条件付き通知
  conditional_notifications:
    - name: "business_hours_only"
      condition: "time_between('09:00', '18:00') and weekday"
      channels: ["slack", "email"]
    
    - name: "after_hours_critical"
      condition: "critical_changes > 0 and (not business_hours)"
      channels: ["phone", "pager"]
    
    - name: "weekend_summary"
      condition: "weekend and total_changes > 0"
      channels: ["email"]
      frequency: "daily_summary"
  
  # 通知の抑制
  suppression_rules:
    - name: "duplicate_suppression"
      condition: "same_changes_as_previous"
      suppress_for: "2 hours"
    
    - name: "maintenance_window"
      condition: "maintenance_mode_enabled"
      suppress_all: true
    
    - name: "known_issue"
      condition: "issue_id in known_issues"
      suppress_for: "24 hours"
```

## 📊 自動レポート配信

### 定期レポートの設定

```yaml
# config/automated-reports.yaml
automated_reports:
  daily_summary:
    schedule: "0 8 * * *"             # 毎日午前8時
    recipients: ["team-lead@company.com"]
    format: "html"
    template: "templates/daily-summary.html"
    
    content:
      - schema_changes_summary
      - critical_issues_highlight
      - trend_analysis
      - recommended_actions
  
  weekly_detailed:
    schedule: "0 9 * * 1"             # 毎週月曜日午前9時
    recipients: ["management@company.com", "architecture-team@company.com"]
    format: "pdf"
    template: "templates/weekly-detailed.html"
    
    content:
      - executive_summary
      - detailed_change_analysis
      - performance_impact_assessment
      - compliance_status
      - architecture_evolution_trends
  
  monthly_executive:
    schedule: "0 10 1 * *"            # 毎月1日午前10時
    recipients: ["cto@company.com", "vp-engineering@company.com"]
    format: "pdf"
    template: "templates/executive-summary.html"
    
    content:
      - high_level_metrics
      - business_impact_analysis
      - technology_debt_assessment
      - strategic_recommendations
```

### レポート配信の最適化

```yaml
report_delivery_optimization:
  # 配信設定
  delivery_settings:
    retry_attempts: 3
    retry_delay: 600                  # 10分間隔
    timeout: 1800                     # 30分タイムアウト
    
    # 大容量レポートの処理
    large_report_handling:
      size_threshold: "10MB"
      compress: true
      split_delivery: true
      cloud_storage_link: true
  
  # 配信最適化
  delivery_optimization:
    # 時差配信
    staggered_delivery:
      enabled: true
      delay_between_recipients: 60    # 1分間隔
    
    # 帯域制限
    bandwidth_limiting:
      enabled: true
      max_concurrent_deliveries: 5
      rate_limit: "1MB/s"
  
  # 配信追跡
  delivery_tracking:
    enabled: true
    track_opens: true
    track_clicks: true
    delivery_confirmation: true
```

## 🔧 CI/CDパイプライン統合

### GitHub Actions統合

```yaml
# .github/workflows/schema-automation.yml
name: Schema Change Automation

on:
  schedule:
    - cron: '0 */6 * * *'             # 6時間毎実行
  push:
    paths:
      - 'db/migrations/**'
  pull_request:
    paths:
      - 'db/migrations/**'

jobs:
  automated-schema-check:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup PGSD
        run: |
          pip install pgsd
          pgsd --version
      
      - name: Automated Schema Comparison
        env:
          PROD_DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}
          STAGING_DB_PASSWORD: ${{ secrets.STAGING_DB_PASSWORD }}
        run: |
          pgsd compare \
            --config .pgsd/automation-config.yaml \
            --output ./reports \
            --format json
      
      - name: Analyze and Notify
        run: |
          pgsd analyze \
            --input ./reports \
            --notify \
            --webhook ${{ secrets.SLACK_WEBHOOK }}
      
      - name: Archive Reports
        uses: actions/upload-artifact@v3
        with:
          name: schema-reports
          path: ./reports/
          retention-days: 30
```

### GitLab CI統合

```yaml
# .gitlab-ci.yml
stages:
  - schema-check
  - analysis
  - notification

variables:
  PGSD_CONFIG: ".pgsd/automation.yaml"

schema-automated-check:
  stage: schema-check
  image: python:3.11
  
  before_script:
    - pip install pgsd
  
  script:
    - |
      pgsd compare \
        --config $PGSD_CONFIG \
        --output reports/ \
        --format json \
        --automated-mode
  
  artifacts:
    paths:
      - reports/
    expire_in: 30 days
  
  only:
    - schedules
    - web

automated-analysis:
  stage: analysis
  dependencies:
    - schema-automated-check
  
  script:
    - |
      pgsd analyze \
        --input reports/ \
        --automated-rules \
        --output analysis/
  
  artifacts:
    paths:
      - analysis/
    expire_in: 7 days

automated-notification:
  stage: notification
  dependencies:
    - automated-analysis
  
  script:
    - |
      pgsd notify \
        --input analysis/ \
        --channels slack,email \
        --template automation
  
  only:
    variables:
      - $CI_PIPELINE_SOURCE == "schedule"
```

## 🎛️ 高度な自動化設定

### 機械学習による予測

```yaml
ml_automation:
  # 異常検知
  anomaly_detection:
    enabled: true
    model: "isolation_forest"
    sensitivity: 0.1                  # 感度設定
    
    features:
      - change_frequency
      - change_magnitude
      - time_patterns
      - object_types
    
    actions:
      anomaly_detected:
        - increase_monitoring_frequency
        - send_anomaly_alert
        - create_investigation_ticket
  
  # 変更予測
  change_prediction:
    enabled: true
    model: "time_series_forecast"
    prediction_horizon: 30            # 30日先まで予測
    
    predictions:
      - schema_growth_rate
      - maintenance_windows
      - potential_conflicts
    
    actions:
      high_risk_prediction:
        - preventive_notification
        - schedule_review_meeting
```

### イベント駆動自動化

```yaml
event_driven_automation:
  # イベントトリガー
  event_triggers:
    deployment_completed:
      source: "deployment_system"
      action: "immediate_schema_check"
      
    high_traffic_detected:
      source: "monitoring_system"
      action: "performance_focused_analysis"
      
    security_incident:
      source: "security_system"
      action: "security_focused_schema_audit"
  
  # ワークフロー連携
  workflow_integration:
    jira_integration:
      auto_create_tickets: true
      auto_update_status: true
      
    jenkins_integration:
      trigger_builds: true
      pass_parameters: true
      
    monitoring_integration:
      update_dashboards: true
      create_alerts: true
```

## 📈 監視とメトリクス

### 自動化システムの監視

```yaml
automation_monitoring:
  # システムメトリクス
  system_metrics:
    - execution_frequency
    - success_rate
    - average_execution_time
    - resource_usage
    - error_rate
  
  # ビジネスメトリクス
  business_metrics:
    - schema_change_detection_rate
    - false_positive_rate
    - notification_effectiveness
    - response_time_to_critical_changes
  
  # アラート設定
  alerts:
    automation_failure:
      threshold: "3 consecutive failures"
      action: "escalate_to_oncall"
    
    high_error_rate:
      threshold: "error_rate > 5%"
      action: "investigate_and_fix"
    
    performance_degradation:
      threshold: "execution_time > 2x average"
      action: "optimize_configuration"
```

### ダッシュボード設定

```yaml
dashboard_configuration:
  grafana_dashboard:
    panels:
      - name: "Automation Health"
        metrics: ["success_rate", "execution_frequency"]
        type: "stat"
        
      - name: "Schema Changes Over Time"
        metrics: ["total_changes", "critical_changes"]
        type: "graph"
        
      - name: "Response Times"
        metrics: ["notification_latency", "analysis_duration"]
        type: "heatmap"
      
      - name: "Error Tracking"
        metrics: ["error_count", "error_types"]
        type: "table"
  
  # アラート設定
  alert_rules:
    - name: "Automation Down"
      expression: "up{job='pgsd-automation'} == 0"
      for: "5m"
      severity: "critical"
    
    - name: "High Error Rate"
      expression: "rate(pgsd_errors_total[5m]) > 0.1"
      for: "10m"
      severity: "warning"
```

## 💡 ベストプラクティス

### 自動化の段階的導入

```yaml
phased_automation:
  phase_1_monitoring:
    duration: "2-4週間"
    scope: "基本的な監視と通知"
    activities:
      - 定期的なスキーマ比較
      - 基本的な通知設定
      - レポート生成
  
  phase_2_analysis:
    duration: "4-6週間"
    scope: "自動分析と分類"
    activities:
      - 重要度の自動評価
      - 影響度分析
      - 推奨事項の生成
  
  phase_3_integration:
    duration: "6-8週間"
    scope: "システム統合と高度な自動化"
    activities:
      - CI/CDパイプライン統合
      - 外部システム連携
      - 機械学習ベースの予測
```

### 設定管理

```yaml
configuration_management:
  # 設定の版管理
  version_control:
    repository: "git@github.com:company/pgsd-configs.git"
    branch_strategy: "environment_branches"
    review_process: "pull_request_required"
  
  # 環境間の設定同期
  environment_sync:
    development_to_staging: "automatic"
    staging_to_production: "manual_approval"
    rollback_capability: true
  
  # 設定の検証
  configuration_validation:
    syntax_check: true
    connectivity_test: true
    permission_verification: true
```

## 🚀 次のステップ

自動化機能を理解したら：

1. **[パフォーマンス調整](../advanced/performance_tuning.md)** - 大規模環境での最適化
2. **[API統合](../advanced/api_integration.md)** - 外部システムとの高度な連携
3. **[セキュリティ設定](../advanced/security.md)** - セキュアな自動化の実装

## 📚 関連資料

- [自動化API仕様](../reference/automation_api.md)
- [通知システム設定](../reference/notification_config.md)
- [トラブルシューティング](../troubleshooting/automation_issues.md)