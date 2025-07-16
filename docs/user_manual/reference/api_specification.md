# API仕様

PGSDのREST APIとPython SDKの完全な仕様です。

## 🎯 この章で学ぶこと

- REST APIの詳細仕様
- Python SDKの使用方法
- 認証と認可
- APIの統合方法

## 🌐 REST API

### 基本情報

```
Base URL: https://api.pgsd.org/v1
Content-Type: application/json
Accept: application/json
```

### 認証

```http
Authorization: Bearer YOUR_API_KEY
```

### レスポンス形式

```json
{
  "success": true,
  "data": {},
  "message": "Success",
  "timestamp": "2025-07-15T14:30:22Z",
  "request_id": "req_123456789"
}
```

### エラーレスポンス

```json
{
  "success": false,
  "error": {
    "code": "E001",
    "message": "Invalid request parameters",
    "details": {
      "field": "source_host",
      "reason": "Required field missing"
    }
  },
  "timestamp": "2025-07-15T14:30:22Z",
  "request_id": "req_123456789"
}
```

## 🔍 比較API

### 比較の開始

比較処理を開始します。

**エンドポイント**
```
POST /comparisons
```

**リクエスト**
```json
{
  "source": {
    "host": "prod.company.com",
    "port": 5432,
    "database": "myapp",
    "user": "readonly",
    "password": "secret",
    "schema": "public"
  },
  "target": {
    "host": "staging.company.com",
    "port": 5432,
    "database": "myapp",
    "user": "readonly",
    "password": "secret",
    "schema": "public"
  },
  "options": {
    "include_comments": true,
    "include_permissions": false,
    "case_sensitive": true,
    "timeout": 300
  }
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "comparison_id": "comp_abc123def456",
    "status": "pending",
    "created_at": "2025-07-15T14:30:22Z",
    "estimated_duration": 120,
    "progress": {
      "current": 0,
      "total": 100,
      "stage": "initializing"
    }
  }
}
```

### 比較状態の取得

比較の進行状況を取得します。

**エンドポイント**
```
GET /comparisons/{comparison_id}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "comparison_id": "comp_abc123def456",
    "status": "completed",
    "created_at": "2025-07-15T14:30:22Z",
    "completed_at": "2025-07-15T14:32:45Z",
    "duration": 143,
    "progress": {
      "current": 100,
      "total": 100,
      "stage": "completed"
    },
    "result": {
      "summary": {
        "total_differences": 42,
        "severity_breakdown": {
          "critical": 3,
          "warning": 15,
          "info": 24
        }
      },
      "differences": {
        "tables": {
          "added": [...],
          "removed": [...],
          "modified": [...]
        },
        "columns": {
          "added": [...],
          "removed": [...],
          "modified": [...]
        }
      }
    }
  }
}
```

### 比較の停止

実行中の比較を停止します。

**エンドポイント**
```
DELETE /comparisons/{comparison_id}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "comparison_id": "comp_abc123def456",
    "status": "cancelled",
    "cancelled_at": "2025-07-15T14:31:30Z"
  }
}
```

### 比較履歴の取得

過去の比較結果を取得します。

**エンドポイント**
```
GET /comparisons
```

**クエリパラメータ**
```
?limit=10&offset=0&status=completed&from=2025-07-01&to=2025-07-15
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "comparisons": [
      {
        "comparison_id": "comp_abc123def456",
        "status": "completed",
        "created_at": "2025-07-15T14:30:22Z",
        "completed_at": "2025-07-15T14:32:45Z",
        "duration": 143,
        "source_db": "myapp@prod.company.com",
        "target_db": "myapp@staging.company.com",
        "total_differences": 42
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 10,
      "offset": 0,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## 📊 レポートAPI

### レポートの生成

比較結果からレポートを生成します。

**エンドポイント**
```
POST /reports
```

**リクエスト**
```json
{
  "comparison_id": "comp_abc123def456",
  "format": "html",
  "template": "executive-summary",
  "options": {
    "include_metadata": true,
    "include_recommendations": true,
    "theme": "corporate"
  }
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "report_id": "rep_xyz789abc123",
    "status": "generating",
    "created_at": "2025-07-15T14:35:00Z",
    "estimated_completion": "2025-07-15T14:35:30Z"
  }
}
```

### レポートの取得

生成されたレポートを取得します。

**エンドポイント**
```
GET /reports/{report_id}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "report_id": "rep_xyz789abc123",
    "status": "completed",
    "format": "html",
    "size": 2048576,
    "created_at": "2025-07-15T14:35:00Z",
    "completed_at": "2025-07-15T14:35:28Z",
    "download_url": "https://api.pgsd.org/v1/reports/rep_xyz789abc123/download",
    "expires_at": "2025-07-22T14:35:28Z"
  }
}
```

### レポートのダウンロード

生成されたレポートファイルをダウンロードします。

**エンドポイント**
```
GET /reports/{report_id}/download
```

**レスポンス**
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="schema_comparison_report.html"

[レポートファイルの内容]
```

## 🔧 設定API

### 設定の取得

現在の設定を取得します。

**エンドポイント**
```
GET /config
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "limits": {
      "max_concurrent_comparisons": 5,
      "max_comparison_duration": 3600,
      "max_report_size": 104857600
    },
    "features": {
      "experimental": false,
      "ml_predictions": false,
      "anomaly_detection": false
    }
  }
}
```

### 設定の更新

設定を更新します。

**エンドポイント**
```
PUT /config
```

**リクエスト**
```json
{
  "limits": {
    "max_concurrent_comparisons": 10
  },
  "features": {
    "experimental": true
  }
}
```

## 📈 統計API

### 統計情報の取得

使用統計を取得します。

**エンドポイント**
```
GET /statistics
```

**クエリパラメータ**
```
?period=30d&granularity=day
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "granularity": "day",
    "metrics": {
      "total_comparisons": 1247,
      "successful_comparisons": 1198,
      "failed_comparisons": 49,
      "average_duration": 156.7,
      "total_differences_detected": 18429
    },
    "daily_stats": [
      {
        "date": "2025-07-15",
        "comparisons": 42,
        "differences": 623,
        "average_duration": 143.2
      }
    ]
  }
}
```

## 🔔 Webhook API

### Webhook設定の取得

現在のWebhook設定を取得します。

**エンドポイント**
```
GET /webhooks
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "webhooks": [
      {
        "id": "wh_123456789",
        "url": "https://api.company.com/pgsd-webhook",
        "events": ["comparison_completed", "comparison_failed"],
        "active": true,
        "created_at": "2025-07-15T14:30:22Z"
      }
    ]
  }
}
```

### Webhook設定の作成

新しいWebhookを設定します。

**エンドポイント**
```
POST /webhooks
```

**リクエスト**
```json
{
  "url": "https://api.company.com/pgsd-webhook",
  "events": ["comparison_completed", "comparison_failed", "critical_changes_detected"],
  "secret": "webhook_secret_key",
  "active": true
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "id": "wh_123456789",
    "url": "https://api.company.com/pgsd-webhook",
    "events": ["comparison_completed", "comparison_failed", "critical_changes_detected"],
    "active": true,
    "created_at": "2025-07-15T14:30:22Z"
  }
}
```

## 🐍 Python SDK

### インストール

```bash
pip install pgsd-sdk
```

### 基本的な使用方法

```python
from pgsd_sdk import PGSDClient

# クライアントの初期化
client = PGSDClient(
    base_url="https://api.pgsd.org/v1",
    api_key="your_api_key_here"
)

# 比較の実行
comparison = client.comparisons.create(
    source={
        "host": "prod.company.com",
        "database": "myapp",
        "user": "readonly",
        "password": "secret"
    },
    target={
        "host": "staging.company.com",
        "database": "myapp",
        "user": "readonly",
        "password": "secret"
    },
    options={
        "include_comments": True,
        "case_sensitive": True
    }
)

# 結果の待機
result = client.comparisons.wait_for_completion(
    comparison.id,
    timeout=600
)

# レポートの生成
report = client.reports.create(
    comparison_id=comparison.id,
    format="html",
    template="executive-summary"
)

# レポートのダウンロード
with open("report.html", "wb") as f:
    client.reports.download(report.id, f)
```

### 高度な使用方法

```python
import asyncio
from pgsd_sdk import AsyncPGSDClient

async def main():
    # 非同期クライアント
    async with AsyncPGSDClient(
        base_url="https://api.pgsd.org/v1",
        api_key="your_api_key_here"
    ) as client:
        
        # 並列比較の実行
        tasks = []
        for config in comparison_configs:
            task = client.comparisons.create(**config)
            tasks.append(task)
        
        comparisons = await asyncio.gather(*tasks)
        
        # 結果の待機
        results = []
        for comparison in comparisons:
            result = await client.comparisons.wait_for_completion(
                comparison.id,
                timeout=600
            )
            results.append(result)
        
        return results

# 実行
results = asyncio.run(main())
```

### エラーハンドリング

```python
from pgsd_sdk import PGSDClient, PGSDError, ConnectionError, TimeoutError

client = PGSDClient(
    base_url="https://api.pgsd.org/v1",
    api_key="your_api_key_here"
)

try:
    comparison = client.comparisons.create(
        source=source_config,
        target=target_config
    )
    
    result = client.comparisons.wait_for_completion(
        comparison.id,
        timeout=600
    )
    
except ConnectionError as e:
    print(f"Connection error: {e}")
except TimeoutError as e:
    print(f"Timeout error: {e}")
except PGSDError as e:
    print(f"PGSD error: {e.code} - {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 設定とカスタマイズ

```python
from pgsd_sdk import PGSDClient, RetryConfig, LoggingConfig

# リトライ設定
retry_config = RetryConfig(
    max_attempts=3,
    backoff_factor=2.0,
    max_delay=60
)

# ログ設定
logging_config = LoggingConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# クライアントの設定
client = PGSDClient(
    base_url="https://api.pgsd.org/v1",
    api_key="your_api_key_here",
    retry_config=retry_config,
    logging_config=logging_config,
    timeout=30
)
```

## 🔍 GraphQL API

### GraphQLクエリ

```graphql
query GetComparison($id: ID!) {
  comparison(id: $id) {
    id
    status
    createdAt
    completedAt
    duration
    sourceDatabase {
      host
      database
      schema
    }
    targetDatabase {
      host
      database
      schema
    }
    summary {
      totalDifferences
      severityBreakdown {
        critical
        warning
        info
      }
    }
    differences {
      tables {
        added {
          name
          columnCount
        }
        removed {
          name
          columnCount
        }
        modified {
          name
          changes {
            type
            description
            severity
          }
        }
      }
    }
  }
}
```

### GraphQLミューテーション

```graphql
mutation StartComparison($input: ComparisonInput!) {
  startComparison(input: $input) {
    id
    status
    createdAt
    estimatedDuration
  }
}
```

### 変数

```json
{
  "input": {
    "source": {
      "host": "prod.company.com",
      "database": "myapp",
      "user": "readonly",
      "password": "secret"
    },
    "target": {
      "host": "staging.company.com",
      "database": "myapp",
      "user": "readonly",
      "password": "secret"
    },
    "options": {
      "includeComments": true,
      "caseSensitive": true
    }
  }
}
```

## 🔒 認証・認可

### API キーの管理

```python
from pgsd_sdk import PGSDClient

# API キーの作成
client = PGSDClient(
    base_url="https://api.pgsd.org/v1",
    api_key="master_api_key"
)

# 新しいAPI キーの作成
new_key = client.auth.create_api_key(
    name="CI/CD Pipeline",
    permissions=["comparisons:read", "comparisons:write", "reports:read"],
    expires_at="2025-12-31T23:59:59Z"
)

# API キーの無効化
client.auth.revoke_api_key(new_key.id)
```

### 権限管理

```python
# 権限の確認
permissions = client.auth.get_permissions()
print(permissions)

# 権限の詳細
{
  "comparisons:read": True,
  "comparisons:write": True,
  "reports:read": True,
  "reports:write": False,
  "config:read": False,
  "config:write": False
}
```

## 📊 レート制限

### 制限値

```
- 認証済みユーザー: 1000リクエスト/時間
- 未認証ユーザー: 100リクエスト/時間
- 比較実行: 10リクエスト/時間
- レポート生成: 50リクエスト/時間
```

### レート制限ヘッダー

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1658764800
```

### レート制限の処理

```python
from pgsd_sdk import PGSDClient, RateLimitError
import time

client = PGSDClient(
    base_url="https://api.pgsd.org/v1",
    api_key="your_api_key"
)

def make_request_with_retry():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client.comparisons.list()
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = e.retry_after or 60
                time.sleep(wait_time)
                continue
            raise
```

## 🔧 統合例

### CI/CDパイプラインとの統合

```python
# ci_integration.py
import os
from pgsd_sdk import PGSDClient
import json

def run_schema_comparison():
    client = PGSDClient(
        base_url=os.environ['PGSD_API_URL'],
        api_key=os.environ['PGSD_API_KEY']
    )
    
    # 比較実行
    comparison = client.comparisons.create(
        source={
            "host": os.environ['PROD_DB_HOST'],
            "database": os.environ['PROD_DB_NAME'],
            "user": os.environ['PROD_DB_USER'],
            "password": os.environ['PROD_DB_PASSWORD']
        },
        target={
            "host": os.environ['STAGING_DB_HOST'],
            "database": os.environ['STAGING_DB_NAME'],
            "user": os.environ['STAGING_DB_USER'],
            "password": os.environ['STAGING_DB_PASSWORD']
        }
    )
    
    # 結果待機
    result = client.comparisons.wait_for_completion(
        comparison.id,
        timeout=600
    )
    
    # 重要な変更のチェック
    critical_changes = result.summary.severity_breakdown.critical
    if critical_changes > 0:
        print(f"Critical changes detected: {critical_changes}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(run_schema_comparison())
```

### 監視システムとの統合

```python
# monitoring_integration.py
from pgsd_sdk import PGSDClient
import time
import requests

def monitor_schema_changes():
    client = PGSDClient(
        base_url="https://api.pgsd.org/v1",
        api_key="monitoring_api_key"
    )
    
    while True:
        try:
            # 定期的な比較実行
            comparison = client.comparisons.create(
                source=source_config,
                target=target_config
            )
            
            result = client.comparisons.wait_for_completion(
                comparison.id,
                timeout=300
            )
            
            # メトリクスの送信
            send_metrics(result)
            
            # アラートの判定
            if result.summary.severity_breakdown.critical > 0:
                send_alert(result)
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(3600)  # 1時間間隔

def send_metrics(result):
    # Prometheusメトリクスの送信
    metrics = {
        "pgsd_total_differences": result.summary.total_differences,
        "pgsd_critical_changes": result.summary.severity_breakdown.critical,
        "pgsd_warning_changes": result.summary.severity_breakdown.warning
    }
    
    # メトリクスゲートウェイに送信
    requests.post(
        "http://prometheus-gateway:9091/metrics/job/pgsd",
        data=metrics
    )

def send_alert(result):
    # Slackアラートの送信
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    
    payload = {
        "text": f"Critical schema changes detected: {result.summary.severity_breakdown.critical}",
        "attachments": [{
            "color": "danger",
            "fields": [{
                "title": "Total Differences",
                "value": str(result.summary.total_differences),
                "short": True
            }]
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

## 🚀 次のステップ

API仕様を理解したら：

1. **[Python SDK詳細](python_sdk.md)** - Python SDKの詳細な使用方法
2. **[Webhook設定](webhook_configuration.md)** - Webhookの詳細設定
3. **[GraphQL仕様](graphql_schema.md)** - GraphQL APIの詳細

## 📚 関連資料

- [API統合ガイド](../advanced/api_integration.md)
- [認証設定](../advanced/security.md)
- [エラーコード](error_codes.md)