# API統合

PGSDを外部システムと連携させるためのAPI統合について説明します。

## 🎯 この章で学ぶこと

- REST API の活用方法
- 外部システムとの連携
- Webhook の設定
- カスタムAPI開発

## 🔌 REST API の基本

### API エンドポイント

```yaml
# PGSDが提供するREST API
api_endpoints:
  # 比較実行
  POST /api/v1/comparisons:
    description: "スキーマ比較を実行"
    parameters:
      - source_config
      - target_config
      - comparison_options
    response:
      - comparison_id
      - status
      - estimated_duration
  
  # 比較結果取得
  GET /api/v1/comparisons/{id}:
    description: "比較結果を取得"
    response:
      - comparison_result
      - metadata
      - differences
  
  # レポート生成
  POST /api/v1/reports:
    description: "レポートを生成"
    parameters:
      - comparison_id
      - format
      - template
    response:
      - report_url
      - download_link
  
  # 統計情報
  GET /api/v1/statistics:
    description: "統計情報を取得"
    response:
      - usage_stats
      - performance_metrics
      - error_rates
```

### API クライアント設定

```python
# Python APIクライアント例
import requests
import json
from datetime import datetime

class PGSDClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'PGSD-Client/1.0'
        })
    
    def start_comparison(self, source_config, target_config, options=None):
        """スキーマ比較を開始"""
        payload = {
            'source': source_config,
            'target': target_config,
            'options': options or {}
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/comparisons',
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_comparison_result(self, comparison_id):
        """比較結果を取得"""
        response = self.session.get(
            f'{self.base_url}/api/v1/comparisons/{comparison_id}'
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, comparison_id, timeout=300):
        """比較完了を待機"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_comparison_result(comparison_id)
            
            if result['status'] == 'completed':
                return result
            elif result['status'] == 'failed':
                raise Exception(f"Comparison failed: {result.get('error')}")
            
            time.sleep(5)
        
        raise TimeoutError(f"Comparison {comparison_id} did not complete within {timeout} seconds")
    
    def generate_report(self, comparison_id, format='html', template=None):
        """レポートを生成"""
        payload = {
            'comparison_id': comparison_id,
            'format': format,
            'template': template
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/reports',
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_statistics(self, start_date=None, end_date=None):
        """統計情報を取得"""
        params = {}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        
        response = self.session.get(
            f'{self.base_url}/api/v1/statistics',
            params=params
        )
        response.raise_for_status()
        return response.json()

# 使用例
client = PGSDClient(
    base_url='https://pgsd.company.com',
    api_key='your-api-key-here'
)

# 比較実行
comparison = client.start_comparison(
    source_config={
        'host': 'prod.company.com',
        'database': 'myapp',
        'user': 'readonly',
        'password': 'secret'
    },
    target_config={
        'host': 'staging.company.com',
        'database': 'myapp',
        'user': 'readonly',
        'password': 'secret'
    },
    options={
        'include_comments': True,
        'case_sensitive': True
    }
)

# 結果待機
result = client.wait_for_completion(comparison['comparison_id'])

# レポート生成
report = client.generate_report(
    comparison['comparison_id'],
    format='html',
    template='executive-summary'
)

print(f"Report URL: {report['report_url']}")
```

## 🔗 外部システム連携

### Jira 統合

```python
# Jira との統合例
import requests
from jira import JIRA

class JiraIntegration:
    def __init__(self, jira_url, username, api_token):
        self.jira = JIRA(
            server=jira_url,
            basic_auth=(username, api_token)
        )
    
    def create_schema_change_ticket(self, comparison_result):
        """スキーマ変更チケットを自動作成"""
        summary = f"Database Schema Changes - {comparison_result['metadata']['generated_at']}"
        
        # 重要度に応じた優先度設定
        priority = self._get_priority(comparison_result['summary'])
        
        # 説明文生成
        description = self._generate_description(comparison_result)
        
        # チケット作成
        issue = self.jira.create_issue(
            project='DBA',
            summary=summary,
            description=description,
            issuetype={'name': 'Task'},
            priority={'name': priority},
            labels=['database', 'schema', 'automated'],
            components=[{'name': 'Database'}]
        )
        
        # 変更に応じたサブタスク作成
        self._create_subtasks(issue, comparison_result)
        
        return issue.key
    
    def _get_priority(self, summary):
        """重要度に応じた優先度を決定"""
        if summary['severity_breakdown']['critical'] > 0:
            return 'Highest'
        elif summary['severity_breakdown']['warning'] > 5:
            return 'High'
        elif summary['total_differences'] > 20:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_description(self, result):
        """チケット説明文を生成"""
        summary = result['summary']
        
        description = f"""
        h2. スキーマ変更サマリー
        
        * 総変更数: {summary['total_differences']}
        * 重要な変更: {summary['severity_breakdown']['critical']}
        * 警告レベル: {summary['severity_breakdown']['warning']}
        * 情報レベル: {summary['severity_breakdown']['info']}
        
        h2. 対象データベース
        
        * ソース: {result['metadata']['source']['host']}/{result['metadata']['source']['database']}
        * ターゲット: {result['metadata']['target']['host']}/{result['metadata']['target']['database']}
        
        h2. 次のアクション
        
        1. 変更内容の詳細確認
        2. 影響範囲の調査
        3. 必要に応じてテスト計画策定
        4. 承認プロセスの実行
        
        h2. 関連リンク
        
        * [詳細レポート|{result.get('report_url', 'N/A')}]
        * [比較設定|{result.get('config_url', 'N/A')}]
        """
        
        return description
    
    def _create_subtasks(self, parent_issue, result):
        """変更内容に応じたサブタスクを作成"""
        differences = result.get('differences', {})
        
        # 重要な変更に対するサブタスク
        if differences.get('tables', {}).get('removed'):
            self.jira.create_issue(
                project='DBA',
                summary=f"Review table removals - {parent_issue.key}",
                issuetype={'name': 'Sub-task'},
                parent={'key': parent_issue.key},
                description="削除されたテーブルの影響調査と対応"
            )
        
        if differences.get('columns', {}).get('removed'):
            self.jira.create_issue(
                project='DBA',
                summary=f"Review column removals - {parent_issue.key}",
                issuetype={'name': 'Sub-task'},
                parent={'key': parent_issue.key},
                description="削除されたカラムの影響調査と対応"
            )
```

### Slack 統合

```python
# Slack との統合例
import json
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackIntegration:
    def __init__(self, bot_token, signing_secret):
        self.client = WebClient(token=bot_token)
        self.signing_secret = signing_secret
    
    def send_schema_change_notification(self, comparison_result, channel="#database-alerts"):
        """スキーマ変更通知を送信"""
        
        # 重要度に応じた色とメンション
        severity = self._get_severity_info(comparison_result['summary'])
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity['emoji']} Database Schema Changes Detected"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\n{comparison_result['metadata']['source']['host']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Target:*\n{comparison_result['metadata']['target']['host']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Changes:*\n{comparison_result['summary']['total_differences']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Critical:*\n{comparison_result['summary']['severity_breakdown']['critical']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Priority:* {severity['priority']}\n*Recommended Action:* {severity['action']}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Report"
                        },
                        "url": comparison_result.get('report_url', ''),
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Create Ticket"
                        },
                        "value": f"create_ticket_{comparison_result['comparison_id']}"
                    }
                ]
            }
        ]
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=f"Database schema changes detected - {severity['priority']} priority",
                blocks=blocks,
                username="PGSD Bot",
                icon_emoji=":database:"
            )
            
            # 重要な変更の場合はスレッドで詳細を送信
            if comparison_result['summary']['severity_breakdown']['critical'] > 0:
                self._send_critical_details(channel, response['ts'], comparison_result)
            
            return response
            
        except SlackApiError as e:
            print(f"Error sending message: {e}")
            return None
    
    def _get_severity_info(self, summary):
        """重要度情報を取得"""
        critical = summary['severity_breakdown']['critical']
        warning = summary['severity_breakdown']['warning']
        
        if critical > 0:
            return {
                'emoji': '🚨',
                'priority': 'HIGH',
                'action': 'Immediate review required',
                'color': '#FF0000'
            }
        elif warning > 5:
            return {
                'emoji': '⚠️',
                'priority': 'MEDIUM',
                'action': 'Review within 24 hours',
                'color': '#FFA500'
            }
        else:
            return {
                'emoji': 'ℹ️',
                'priority': 'LOW',
                'action': 'Review at next maintenance window',
                'color': '#0000FF'
            }
    
    def _send_critical_details(self, channel, thread_ts, result):
        """重要な変更の詳細をスレッドで送信"""
        critical_changes = []
        
        # 削除されたテーブル
        if result.get('differences', {}).get('tables', {}).get('removed'):
            for table in result['differences']['tables']['removed']:
                critical_changes.append(f"🗑️ Table removed: `{table['name']}`")
        
        # 削除されたカラム
        if result.get('differences', {}).get('columns', {}).get('removed'):
            for column in result['differences']['columns']['removed']:
                critical_changes.append(f"🗑️ Column removed: `{column['table']}.{column['name']}`")
        
        if critical_changes:
            self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text="🚨 *Critical Changes Detected:*\n" + "\n".join(critical_changes[:10])
            )
```

### GitHub 統合

```python
# GitHub との統合例
import github
from github import Github

class GitHubIntegration:
    def __init__(self, access_token, repo_name):
        self.github = Github(access_token)
        self.repo = self.github.get_repo(repo_name)
    
    def create_schema_change_pr(self, comparison_result, migration_scripts):
        """スキーマ変更のPRを自動作成"""
        
        # ブランチ名生成
        timestamp = comparison_result['metadata']['generated_at']
        branch_name = f"schema-changes-{timestamp.replace(':', '-')}"
        
        # ベースブランチの取得
        base_branch = self.repo.get_branch('main')
        
        # 新しいブランチ作成
        self.repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_branch.commit.sha
        )
        
        # マイグレーションファイル作成
        for script in migration_scripts:
            self.repo.create_file(
                path=script['path'],
                message=f"Add migration script: {script['name']}",
                content=script['content'],
                branch=branch_name
            )
        
        # PR作成
        pr_title = f"Database Schema Changes - {timestamp}"
        pr_body = self._generate_pr_body(comparison_result)
        
        pull_request = self.repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base='main'
        )
        
        # ラベル付与
        self._add_pr_labels(pull_request, comparison_result)
        
        # レビュアー指定
        reviewers = self._get_reviewers(comparison_result)
        if reviewers:
            pull_request.create_review_request(reviewers=reviewers)
        
        return pull_request
    
    def _generate_pr_body(self, result):
        """PR本文を生成"""
        summary = result['summary']
        
        body = f"""
        ## Database Schema Changes
        
        This PR contains database schema changes detected on {result['metadata']['generated_at']}.
        
        ### Summary
        - **Total Changes:** {summary['total_differences']}
        - **Critical:** {summary['severity_breakdown']['critical']}
        - **Warning:** {summary['severity_breakdown']['warning']}
        - **Info:** {summary['severity_breakdown']['info']}
        
        ### Databases Compared
        - **Source:** {result['metadata']['source']['host']}/{result['metadata']['source']['database']}
        - **Target:** {result['metadata']['target']['host']}/{result['metadata']['target']['database']}
        
        ### Changes Overview
        """
        
        # 主要な変更を追加
        if result.get('differences', {}).get('tables', {}).get('removed'):
            body += "\n#### 🗑️ Tables Removed\n"
            for table in result['differences']['tables']['removed'][:5]:
                body += f"- `{table['name']}`\n"
        
        if result.get('differences', {}).get('columns', {}).get('removed'):
            body += "\n#### 🗑️ Columns Removed\n"
            for column in result['differences']['columns']['removed'][:5]:
                body += f"- `{column['table']}.{column['name']}`\n"
        
        body += f"""
        
        ### Next Steps
        1. Review the migration scripts in this PR
        2. Test the changes in a development environment
        3. Ensure all application code is compatible
        4. Schedule maintenance window for deployment
        
        ### Related Links
        - [Full Report]({result.get('report_url', 'N/A')})
        - [Comparison Configuration]({result.get('config_url', 'N/A')})
        
        ---
        *This PR was automatically generated by PGSD v{result['metadata']['pgsd_version']}*
        """
        
        return body
    
    def _add_pr_labels(self, pull_request, result):
        """PRにラベルを追加"""
        labels = ['database', 'schema', 'automated']
        
        # 重要度に応じたラベル
        critical = result['summary']['severity_breakdown']['critical']
        warning = result['summary']['severity_breakdown']['warning']
        
        if critical > 0:
            labels.append('critical')
            labels.append('needs-review')
        elif warning > 5:
            labels.append('high-priority')
        else:
            labels.append('low-priority')
        
        # 変更タイプに応じたラベル
        differences = result.get('differences', {})
        if differences.get('tables', {}).get('removed'):
            labels.append('breaking-change')
        if differences.get('columns', {}).get('added'):
            labels.append('feature-addition')
        
        # ラベル設定
        pull_request.set_labels(*labels)
    
    def _get_reviewers(self, result):
        """レビュアーを決定"""
        reviewers = ['dba-team']
        
        # 重要な変更の場合は追加のレビュアー
        if result['summary']['severity_breakdown']['critical'] > 0:
            reviewers.extend(['senior-dev', 'tech-lead'])
        
        return reviewers
```

## 🔔 Webhook 設定

### Webhook サーバーの実装

```python
# webhook_server.py
from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import logging

app = Flask(__name__)

class WebhookHandler:
    def __init__(self, secret_key):
        self.secret_key = secret_key
        self.handlers = {
            'comparison_completed': self._handle_comparison_completed,
            'comparison_failed': self._handle_comparison_failed,
            'critical_changes_detected': self._handle_critical_changes,
            'report_generated': self._handle_report_generated
        }
    
    def verify_signature(self, payload, signature):
        """Webhook署名を検証"""
        expected_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(
            f"sha256={expected_signature}",
            signature
        )
    
    def handle_webhook(self, event_type, payload):
        """Webhookイベントを処理"""
        handler = self.handlers.get(event_type)
        if handler:
            return handler(payload)
        else:
            logging.warning(f"Unknown event type: {event_type}")
            return False
    
    def _handle_comparison_completed(self, payload):
        """比較完了時の処理"""
        comparison_id = payload['comparison_id']
        result = payload['result']
        
        # 結果に応じた処理
        if result['summary']['severity_breakdown']['critical'] > 0:
            self._send_critical_alert(result)
        
        # 統計情報更新
        self._update_statistics(result)
        
        # 自動レポート生成
        self._generate_automated_reports(comparison_id, result)
        
        return True
    
    def _handle_comparison_failed(self, payload):
        """比較失敗時の処理"""
        comparison_id = payload['comparison_id']
        error = payload['error']
        
        # エラーログ記録
        logging.error(f"Comparison {comparison_id} failed: {error}")
        
        # 運用チームへの通知
        self._send_error_notification(comparison_id, error)
        
        return True
    
    def _handle_critical_changes(self, payload):
        """重要な変更検出時の処理"""
        result = payload['result']
        
        # 緊急通知
        self._send_urgent_notification(result)
        
        # 自動チケット作成
        self._create_emergency_ticket(result)
        
        # 関係者への直接連絡
        self._notify_stakeholders(result)
        
        return True
    
    def _handle_report_generated(self, payload):
        """レポート生成完了時の処理"""
        report_info = payload['report_info']
        
        # レポートの配信
        self._distribute_report(report_info)
        
        # アーカイブ処理
        self._archive_report(report_info)
        
        return True
    
    def _send_critical_alert(self, result):
        """重要な変更のアラート送信"""
        # Slack通知
        slack_integration = SlackIntegration(
            bot_token=os.environ['SLACK_BOT_TOKEN'],
            signing_secret=os.environ['SLACK_SIGNING_SECRET']
        )
        slack_integration.send_schema_change_notification(
            result,
            channel="#critical-alerts"
        )
        
        # PagerDuty通知
        # pagerduty_integration.send_alert(result)
    
    def _update_statistics(self, result):
        """統計情報の更新"""
        # データベースまたはメトリクスシステムに統計情報を記録
        pass
    
    def _generate_automated_reports(self, comparison_id, result):
        """自動レポート生成"""
        # 管理者用詳細レポート
        # 開発者用サマリーレポート
        # 経営陣用エグゼクティブレポート
        pass

# Webhook エンドポイント
webhook_handler = WebhookHandler(secret_key=os.environ['WEBHOOK_SECRET'])

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # 署名検証
    signature = request.headers.get('X-PGSD-Signature')
    if not webhook_handler.verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # イベント処理
    event_type = request.headers.get('X-PGSD-Event')
    payload = request.json
    
    try:
        success = webhook_handler.handle_webhook(event_type, payload)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Handler failed'}), 500
    except Exception as e:
        logging.error(f"Webhook handling error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Webhook 設定

```yaml
# config/webhook-settings.yaml
webhooks:
  # 基本設定
  enabled: true
  secret_key: "${WEBHOOK_SECRET_KEY}"
  retry_attempts: 3
  retry_delay: 60
  timeout: 30
  
  # エンドポイント設定
  endpoints:
    - name: "internal_webhook"
      url: "https://internal.company.com/webhook"
      events:
        - "comparison_completed"
        - "comparison_failed"
        - "critical_changes_detected"
      headers:
        Authorization: "Bearer ${INTERNAL_API_TOKEN}"
        Content-Type: "application/json"
    
    - name: "external_monitoring"
      url: "https://monitoring.company.com/pgsd-webhook"
      events:
        - "comparison_completed"
        - "report_generated"
      headers:
        X-API-Key: "${MONITORING_API_KEY}"
  
  # イベントフィルタ
  event_filters:
    critical_changes_detected:
      conditions:
        - "severity_breakdown.critical > 0"
        - "total_differences > 10"
    
    comparison_completed:
      conditions:
        - "total_differences > 0"
  
  # 配信制御
  delivery_settings:
    max_concurrent_deliveries: 5
    rate_limit: "100/hour"
    circuit_breaker:
      failure_threshold: 5
      recovery_timeout: 300
```

## 🔧 カスタムAPI開発

### GraphQL API の実装

```python
# graphql_api.py
import graphene
from graphene import ObjectType, String, Int, List, Field, Argument
from pgsd_core import PGSDComparison, PGSDAnalyzer

class DatabaseInfo(ObjectType):
    host = String()
    database = String()
    schema = String()
    connected_at = String()

class SeverityBreakdown(ObjectType):
    critical = Int()
    warning = Int()
    info = Int()

class ComparisonSummary(ObjectType):
    total_differences = Int()
    severity_breakdown = Field(SeverityBreakdown)

class TableDifference(ObjectType):
    name = String()
    change_type = String()
    description = String()
    severity = String()

class ComparisonResult(ObjectType):
    comparison_id = String()
    status = String()
    source_database = Field(DatabaseInfo)
    target_database = Field(DatabaseInfo)
    summary = Field(ComparisonSummary)
    table_differences = List(TableDifference)
    
    def resolve_table_differences(self, info):
        # 実際の差分データから TableDifference オブジェクトを生成
        return []

class Query(ObjectType):
    comparison = Field(
        ComparisonResult,
        id=Argument(String, required=True)
    )
    
    comparisons = List(
        ComparisonResult,
        limit=Argument(Int, default_value=10),
        offset=Argument(Int, default_value=0),
        status=Argument(String)
    )
    
    def resolve_comparison(self, info, id):
        # 比較結果を取得
        return PGSDComparison.get_by_id(id)
    
    def resolve_comparisons(self, info, limit, offset, status=None):
        # 比較結果一覧を取得
        return PGSDComparison.list(
            limit=limit,
            offset=offset,
            status=status
        )

class StartComparison(graphene.Mutation):
    class Arguments:
        source_host = String(required=True)
        source_database = String(required=True)
        target_host = String(required=True)
        target_database = String(required=True)
        options = String()
    
    comparison_id = String()
    status = String()
    
    def mutate(self, info, source_host, source_database, target_host, target_database, options=None):
        # 比較を開始
        comparison = PGSDComparison.start(
            source_config={
                'host': source_host,
                'database': source_database
            },
            target_config={
                'host': target_host,
                'database': target_database
            },
            options=options
        )
        
        return StartComparison(
            comparison_id=comparison.id,
            status=comparison.status
        )

class Mutation(ObjectType):
    start_comparison = StartComparison.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

# GraphQL エンドポイント
from flask import Flask
from flask_graphql import GraphQLView

app = Flask(__name__)
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)
```

## 📊 メトリクス と監視

### Prometheus メトリクス

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import functools

# メトリクス定義
comparisons_total = Counter('pgsd_comparisons_total', 'Total comparisons executed')
comparison_duration = Histogram('pgsd_comparison_duration_seconds', 'Comparison execution time')
active_comparisons = Gauge('pgsd_active_comparisons', 'Currently active comparisons')
differences_detected = Counter('pgsd_differences_detected_total', 'Total differences detected', ['severity'])
api_requests_total = Counter('pgsd_api_requests_total', 'Total API requests', ['method', 'endpoint'])

class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
    
    def record_comparison_start(self):
        """比較開始時のメトリクス記録"""
        comparisons_total.inc()
        active_comparisons.inc()
        return time.time()
    
    def record_comparison_end(self, start_time, differences_summary):
        """比較終了時のメトリクス記録"""
        duration = time.time() - start_time
        comparison_duration.observe(duration)
        active_comparisons.dec()
        
        # 重要度別の差分数を記録
        for severity, count in differences_summary.items():
            differences_detected.labels(severity=severity).inc(count)
    
    def record_api_request(self, method, endpoint):
        """API リクエストのメトリクス記録"""
        api_requests_total.labels(method=method, endpoint=endpoint).inc()

# デコレータ
def measure_comparison_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        active_comparisons.inc()
        try:
            result = func(*args, **kwargs)
            comparison_duration.observe(time.time() - start_time)
            return result
        finally:
            active_comparisons.dec()
    return wrapper

# メトリクスサーバー起動
def start_metrics_server(port=8000):
    start_http_server(port)
    print(f"Metrics server started on port {port}")
```

## 🚀 次のステップ

API統合を理解したら：

1. **[セキュリティ設定](security.md)** - APIのセキュリティ強化
2. **[スクリプト活用](scripting.md)** - 高度な自動化スクリプト
3. **[トラブルシューティング](../troubleshooting/)** - 統合時の問題解決

## 📚 関連資料

- [REST API仕様](../reference/api_specification.md)
- [GraphQL スキーマ](../reference/graphql_schema.md)
- [Webhook 設定ガイド](../reference/webhook_configuration.md)