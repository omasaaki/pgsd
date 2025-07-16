# スクリプト活用

PGSDを使った高度な自動化スクリプトの作成と活用について説明します。

## 🎯 この章で学ぶこと

- Pythonスクリプトでの高度な自動化
- Bashスクリプトによる統合
- 複雑なワークフローの実装
- スクリプトの保守とデバッグ

## 🐍 Python スクリプト

### 基本的なスクリプト構造

```python
#!/usr/bin/env python3
"""
PGSD Advanced Automation Script
複数データベースの自動比較とレポート生成
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import concurrent.futures

# PGSD Python SDK
from pgsd import PGSDClient, ComparisonConfig, ReportConfig
from pgsd.exceptions import PGSDException, ConnectionError, ComparisonError

class PGSDAutomation:
    def __init__(self, config_file: str):
        """自動化スクリプトの初期化"""
        self.config = self._load_config(config_file)
        self.client = PGSDClient(
            base_url=self.config['pgsd']['url'],
            api_key=self.config['pgsd']['api_key']
        )
        self.logger = self._setup_logging()
        self.results = []
    
    def _load_config(self, config_file: str) -> Dict:
        """設定ファイルを読み込み"""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('pgsd_automation')
        logger.setLevel(logging.INFO)
        
        # ファイルハンドラー
        file_handler = logging.FileHandler(
            self.config['logging']['file'],
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    async def run_comparison_batch(self, batch_name: str) -> List[Dict]:
        """バッチ比較の実行"""
        self.logger.info(f"Starting batch comparison: {batch_name}")
        
        batch_config = self.config['batches'][batch_name]
        comparison_tasks = []
        
        # 並列比較タスクを作成
        for comparison_config in batch_config['comparisons']:
            task = asyncio.create_task(
                self._run_single_comparison(comparison_config)
            )
            comparison_tasks.append(task)
        
        # 全ての比較を実行
        results = await asyncio.gather(*comparison_tasks, return_exceptions=True)
        
        # 結果処理
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    'comparison': batch_config['comparisons'][i]['name'],
                    'error': str(result)
                })
                self.logger.error(f"Comparison failed: {result}")
            else:
                successful_results.append(result)
                self.logger.info(f"Comparison completed: {result['name']}")
        
        # バッチ結果のサマリー
        batch_result = {
            'batch_name': batch_name,
            'started_at': datetime.now().isoformat(),
            'successful_comparisons': len(successful_results),
            'failed_comparisons': len(failed_results),
            'results': successful_results,
            'errors': failed_results
        }
        
        # 結果に応じた処理
        await self._handle_batch_results(batch_result)
        
        return batch_result
    
    async def _run_single_comparison(self, comparison_config: Dict) -> Dict:
        """個別比較の実行"""
        try:
            # 比較設定の作成
            config = ComparisonConfig(
                source=comparison_config['source'],
                target=comparison_config['target'],
                options=comparison_config.get('options', {})
            )
            
            # 比較実行
            comparison = await self.client.start_comparison(config)
            result = await self.client.wait_for_completion(
                comparison.id,
                timeout=comparison_config.get('timeout', 600)
            )
            
            # レポート生成
            if comparison_config.get('generate_report', True):
                report = await self._generate_comparison_report(
                    comparison.id,
                    comparison_config
                )
                result['report_url'] = report['url']
            
            return {
                'name': comparison_config['name'],
                'comparison_id': comparison.id,
                'status': 'completed',
                'result': result,
                'duration': result.get('execution_time', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Comparison {comparison_config['name']} failed: {e}")
            raise
    
    async def _generate_comparison_report(self, comparison_id: str, config: Dict) -> Dict:
        """比較レポートの生成"""
        report_config = ReportConfig(
            format=config.get('report_format', 'html'),
            template=config.get('report_template', 'default'),
            options=config.get('report_options', {})
        )
        
        report = await self.client.generate_report(comparison_id, report_config)
        return report
    
    async def _handle_batch_results(self, batch_result: Dict):
        """バッチ結果の処理"""
        # 重要な変更の検出
        critical_changes = self._detect_critical_changes(batch_result)
        
        if critical_changes:
            await self._send_critical_alerts(critical_changes)
        
        # 統計情報の更新
        await self._update_statistics(batch_result)
        
        # 定期レポートの生成
        await self._generate_batch_report(batch_result)
    
    def _detect_critical_changes(self, batch_result: Dict) -> List[Dict]:
        """重要な変更の検出"""
        critical_changes = []
        
        for result in batch_result['results']:
            if result['status'] == 'completed':
                differences = result['result'].get('differences', {})
                
                # 削除されたテーブル
                if differences.get('tables', {}).get('removed'):
                    critical_changes.append({
                        'type': 'tables_removed',
                        'comparison': result['name'],
                        'count': len(differences['tables']['removed']),
                        'details': differences['tables']['removed']
                    })
                
                # 削除されたカラム
                if differences.get('columns', {}).get('removed'):
                    critical_changes.append({
                        'type': 'columns_removed',
                        'comparison': result['name'],
                        'count': len(differences['columns']['removed']),
                        'details': differences['columns']['removed']
                    })
        
        return critical_changes
    
    async def _send_critical_alerts(self, critical_changes: List[Dict]):
        """重要な変更のアラート送信"""
        # Slack通知
        await self._send_slack_alert(critical_changes)
        
        # Email通知
        await self._send_email_alert(critical_changes)
        
        # PagerDuty通知（最重要の場合）
        if self._is_emergency_level(critical_changes):
            await self._send_pagerduty_alert(critical_changes)
    
    def schedule_automated_runs(self):
        """自動実行のスケジューリング"""
        import schedule
        
        # 定期実行スケジュール
        for schedule_config in self.config['schedules']:
            schedule_func = getattr(schedule.every(), schedule_config['interval'])
            if schedule_config.get('at'):
                schedule_func = schedule_func.at(schedule_config['at'])
            
            schedule_func.do(
                self._run_scheduled_batch,
                schedule_config['batch_name']
            )
        
        # スケジューラーの実行
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def _run_scheduled_batch(self, batch_name: str):
        """スケジュールされたバッチの実行"""
        try:
            result = asyncio.run(self.run_comparison_batch(batch_name))
            self.logger.info(f"Scheduled batch {batch_name} completed successfully")
        except Exception as e:
            self.logger.error(f"Scheduled batch {batch_name} failed: {e}")

# コマンドライン実行
def main():
    parser = argparse.ArgumentParser(description='PGSD Advanced Automation')
    parser.add_argument('--config', required=True, help='Configuration file path')
    parser.add_argument('--batch', help='Batch name to run')
    parser.add_argument('--schedule', action='store_true', help='Run scheduler')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    automation = PGSDAutomation(args.config)
    
    if args.schedule:
        automation.schedule_automated_runs()
    elif args.batch:
        result = asyncio.run(automation.run_comparison_batch(args.batch))
        print(json.dumps(result, indent=2))
    else:
        print("Please specify --batch or --schedule")

if __name__ == '__main__':
    main()
```

### 高度な分析スクリプト

```python
#!/usr/bin/env python3
"""
Advanced Schema Analysis Script
スキーマ変更の傾向分析とレポート生成
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
import sqlite3
from pathlib import Path

class SchemaAnalyzer:
    def __init__(self, database_path: str):
        """分析器の初期化"""
        self.db_path = database_path
        self.conn = sqlite3.connect(database_path)
        self._create_tables()
    
    def _create_tables(self):
        """分析用テーブルの作成"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS comparison_history (
                id INTEGER PRIMARY KEY,
                comparison_id TEXT,
                source_db TEXT,
                target_db TEXT,
                executed_at TIMESTAMP,
                total_differences INTEGER,
                critical_changes INTEGER,
                warning_changes INTEGER,
                info_changes INTEGER,
                execution_time REAL
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS change_details (
                id INTEGER PRIMARY KEY,
                comparison_id TEXT,
                object_type TEXT,
                object_name TEXT,
                change_type TEXT,
                severity TEXT,
                description TEXT,
                impact_score INTEGER
            )
        ''')
    
    def store_comparison_result(self, result: Dict):
        """比較結果を保存"""
        # 基本情報の保存
        self.conn.execute('''
            INSERT INTO comparison_history 
            (comparison_id, source_db, target_db, executed_at, 
             total_differences, critical_changes, warning_changes, info_changes, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['comparison_id'],
            result['source']['database'],
            result['target']['database'],
            result['executed_at'],
            result['summary']['total_differences'],
            result['summary']['severity_breakdown']['critical'],
            result['summary']['severity_breakdown']['warning'],
            result['summary']['severity_breakdown']['info'],
            result['execution_time']
        ))
        
        # 詳細変更の保存
        self._store_change_details(result)
        
        self.conn.commit()
    
    def _store_change_details(self, result: Dict):
        """詳細変更情報の保存"""
        comparison_id = result['comparison_id']
        differences = result.get('differences', {})
        
        for object_type, changes in differences.items():
            for change_type, items in changes.items():
                for item in items:
                    self.conn.execute('''
                        INSERT INTO change_details 
                        (comparison_id, object_type, object_name, change_type, severity, description, impact_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        comparison_id,
                        object_type,
                        item.get('name', 'unknown'),
                        change_type,
                        item.get('severity', 'info'),
                        item.get('description', ''),
                        self._calculate_impact_score(item)
                    ))
    
    def _calculate_impact_score(self, change: Dict) -> int:
        """変更のインパクトスコアを計算"""
        base_scores = {
            'critical': 100,
            'warning': 50,
            'info': 10
        }
        
        severity = change.get('severity', 'info')
        base_score = base_scores.get(severity, 10)
        
        # 変更タイプによる調整
        if change.get('type') == 'removed':
            base_score *= 1.5
        elif change.get('type') == 'added':
            base_score *= 0.8
        
        return int(base_score)
    
    def generate_trend_analysis(self, days: int = 30) -> Dict:
        """傾向分析の生成"""
        # データ取得
        df = pd.read_sql_query('''
            SELECT * FROM comparison_history 
            WHERE executed_at > datetime('now', '-{} days')
            ORDER BY executed_at
        '''.format(days), self.conn)
        
        if df.empty:
            return {'error': 'No data available for the specified period'}
        
        # 基本統計
        stats = {
            'total_comparisons': len(df),
            'avg_differences': df['total_differences'].mean(),
            'avg_execution_time': df['execution_time'].mean(),
            'critical_changes_trend': self._calculate_trend(df, 'critical_changes'),
            'warning_changes_trend': self._calculate_trend(df, 'warning_changes'),
            'most_active_databases': self._get_most_active_databases(df)
        }
        
        # 時系列分析
        time_series = self._analyze_time_series(df)
        
        # 異常検知
        anomalies = self._detect_anomalies(df)
        
        return {
            'period': f'Last {days} days',
            'statistics': stats,
            'time_series': time_series,
            'anomalies': anomalies,
            'recommendations': self._generate_recommendations(df)
        }
    
    def _calculate_trend(self, df: pd.DataFrame, column: str) -> str:
        """傾向の計算"""
        if len(df) < 2:
            return 'insufficient_data'
        
        recent_avg = df[column].tail(7).mean()
        older_avg = df[column].head(7).mean()
        
        if recent_avg > older_avg * 1.2:
            return 'increasing'
        elif recent_avg < older_avg * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _get_most_active_databases(self, df: pd.DataFrame) -> List[Dict]:
        """最も活発なデータベースの取得"""
        activity = df.groupby(['source_db', 'target_db']).agg({
            'total_differences': 'sum',
            'comparison_id': 'count'
        }).reset_index()
        
        activity.columns = ['source_db', 'target_db', 'total_differences', 'comparison_count']
        activity = activity.sort_values('total_differences', ascending=False)
        
        return activity.head(10).to_dict('records')
    
    def _analyze_time_series(self, df: pd.DataFrame) -> Dict:
        """時系列分析"""
        df['date'] = pd.to_datetime(df['executed_at']).dt.date
        daily_stats = df.groupby('date').agg({
            'total_differences': 'sum',
            'critical_changes': 'sum',
            'warning_changes': 'sum',
            'comparison_id': 'count'
        }).reset_index()
        
        return {
            'daily_differences': daily_stats.to_dict('records'),
            'peak_activity_date': daily_stats.loc[daily_stats['total_differences'].idxmax(), 'date'].isoformat(),
            'average_daily_differences': daily_stats['total_differences'].mean()
        }
    
    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """異常検知"""
        anomalies = []
        
        # 実行時間の異常
        execution_mean = df['execution_time'].mean()
        execution_std = df['execution_time'].std()
        
        slow_executions = df[df['execution_time'] > execution_mean + 2 * execution_std]
        
        for _, row in slow_executions.iterrows():
            anomalies.append({
                'type': 'slow_execution',
                'comparison_id': row['comparison_id'],
                'execution_time': row['execution_time'],
                'threshold': execution_mean + 2 * execution_std,
                'date': row['executed_at']
            })
        
        # 重要な変更の急増
        critical_mean = df['critical_changes'].mean()
        critical_std = df['critical_changes'].std()
        
        high_critical = df[df['critical_changes'] > critical_mean + 2 * critical_std]
        
        for _, row in high_critical.iterrows():
            anomalies.append({
                'type': 'high_critical_changes',
                'comparison_id': row['comparison_id'],
                'critical_changes': row['critical_changes'],
                'threshold': critical_mean + 2 * critical_std,
                'date': row['executed_at']
            })
        
        return anomalies
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """推奨事項の生成"""
        recommendations = []
        
        # 実行時間の推奨
        avg_execution_time = df['execution_time'].mean()
        if avg_execution_time > 300:  # 5分以上
            recommendations.append(
                "比較の実行時間が長くなっています。データベースの最適化やPGSDの設定調整を検討してください。"
            )
        
        # 重要な変更の推奨
        avg_critical = df['critical_changes'].mean()
        if avg_critical > 1:
            recommendations.append(
                "重要な変更が頻繁に発生しています。変更管理プロセスの見直しを検討してください。"
            )
        
        # 比較頻度の推奨
        if len(df) < 7:  # 週に1回未満
            recommendations.append(
                "比較の実行頻度が低いようです。定期的な比較実行をお勧めします。"
            )
        
        return recommendations
    
    def generate_visual_report(self, output_path: str, days: int = 30):
        """視覚的レポートの生成"""
        # データ取得
        df = pd.read_sql_query('''
            SELECT * FROM comparison_history 
            WHERE executed_at > datetime('now', '-{} days')
            ORDER BY executed_at
        '''.format(days), self.conn)
        
        if df.empty:
            print("No data available for visualization")
            return
        
        # 図のスタイル設定
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('PGSD Analysis Report', fontsize=16, fontweight='bold')
        
        # 1. 時系列変化
        df['date'] = pd.to_datetime(df['executed_at']).dt.date
        daily_stats = df.groupby('date').agg({
            'total_differences': 'sum',
            'critical_changes': 'sum',
            'warning_changes': 'sum'
        }).reset_index()
        
        axes[0, 0].plot(daily_stats['date'], daily_stats['total_differences'], 
                       marker='o', label='Total Differences')
        axes[0, 0].plot(daily_stats['date'], daily_stats['critical_changes'], 
                       marker='s', label='Critical Changes')
        axes[0, 0].set_title('Daily Change Trends')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Number of Changes')
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 重要度分布
        severity_data = [
            df['critical_changes'].sum(),
            df['warning_changes'].sum(),
            df['info_changes'].sum()
        ]
        severity_labels = ['Critical', 'Warning', 'Info']
        colors = ['#FF6B6B', '#FFD93D', '#6BCF7F']
        
        axes[0, 1].pie(severity_data, labels=severity_labels, colors=colors, 
                      autopct='%1.1f%%', startangle=90)
        axes[0, 1].set_title('Change Severity Distribution')
        
        # 3. 実行時間分布
        axes[1, 0].hist(df['execution_time'], bins=20, alpha=0.7, color='skyblue')
        axes[1, 0].set_title('Execution Time Distribution')
        axes[1, 0].set_xlabel('Execution Time (seconds)')
        axes[1, 0].set_ylabel('Frequency')
        
        # 4. データベース別活動度
        db_activity = df.groupby('source_db')['total_differences'].sum().head(10)
        axes[1, 1].bar(range(len(db_activity)), db_activity.values, color='lightcoral')
        axes[1, 1].set_title('Top 10 Most Active Databases')
        axes[1, 1].set_xlabel('Database')
        axes[1, 1].set_ylabel('Total Differences')
        axes[1, 1].set_xticks(range(len(db_activity)))
        axes[1, 1].set_xticklabels(db_activity.index, rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Visual report saved to {output_path}")

# コマンドライン実行
if __name__ == '__main__':
    analyzer = SchemaAnalyzer('pgsd_analysis.db')
    
    # 傾向分析
    trends = analyzer.generate_trend_analysis(days=30)
    print(json.dumps(trends, indent=2))
    
    # 視覚的レポート
    analyzer.generate_visual_report('pgsd_analysis_report.png', days=30)
```

## 🔧 Bash スクリプト

### 複合操作スクリプト

```bash
#!/bin/bash
# PGSD Advanced Automation Script
# 複数環境での自動比較とレポート配信

set -euo pipefail

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/config"
REPORTS_DIR="${SCRIPT_DIR}/reports"
LOGS_DIR="${SCRIPT_DIR}/logs"

# ログ設定
LOG_FILE="${LOGS_DIR}/pgsd_automation_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "${LOGS_DIR}"

# ログ関数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $*" | tee -a "${LOG_FILE}"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "${LOG_FILE}" >&2
}

log_warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $*" | tee -a "${LOG_FILE}"
}

# 設定読み込み
load_config() {
    local config_file="${CONFIG_DIR}/automation.conf"
    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        exit 1
    fi
    
    source "$config_file"
    log_info "Configuration loaded from $config_file"
}

# 環境チェック
check_environment() {
    log_info "Checking environment..."
    
    # 必要なツールの確認
    local required_tools=("pgsd" "jq" "curl" "mail")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # 設定ファイルの確認
    local required_configs=("${CONFIG_DIR}/production.yaml" "${CONFIG_DIR}/staging.yaml")
    for config in "${required_configs[@]}"; do
        if [[ ! -f "$config" ]]; then
            log_error "Configuration file not found: $config"
            exit 1
        fi
    done
    
    log_info "Environment check completed"
}

# 比較実行
run_comparison() {
    local comparison_name="$1"
    local config_file="$2"
    local output_dir="$3"
    
    log_info "Starting comparison: $comparison_name"
    
    # 出力ディレクトリ作成
    mkdir -p "$output_dir"
    
    # 比較実行
    local start_time=$(date +%s)
    
    if pgsd compare \
        --config "$config_file" \
        --output "$output_dir" \
        --format html,json \
        --verbose >> "${LOG_FILE}" 2>&1; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log_info "Comparison completed: $comparison_name (${duration}s)"
        
        # 結果ファイルの検索
        local html_report=$(find "$output_dir" -name "*.html" -type f | head -1)
        local json_report=$(find "$output_dir" -name "*.json" -type f | head -1)
        
        if [[ -n "$html_report" && -n "$json_report" ]]; then
            echo "$html_report|$json_report|$duration"
        else
            log_error "Report files not found for: $comparison_name"
            return 1
        fi
    else
        log_error "Comparison failed: $comparison_name"
        return 1
    fi
}

# 結果分析
analyze_results() {
    local json_report="$1"
    local comparison_name="$2"
    
    log_info "Analyzing results for: $comparison_name"
    
    # JSON から重要な情報を抽出
    local total_differences=$(jq -r '.summary.total_differences // 0' "$json_report")
    local critical_changes=$(jq -r '.summary.severity_breakdown.critical // 0' "$json_report")
    local warning_changes=$(jq -r '.summary.severity_breakdown.warning // 0' "$json_report")
    
    log_info "Results for $comparison_name: Total=$total_differences, Critical=$critical_changes, Warning=$warning_changes"
    
    # 重要な変更の詳細抽出
    local critical_details=""
    if [[ "$critical_changes" -gt 0 ]]; then
        critical_details=$(jq -r '
            .differences | to_entries[] | 
            select(.value.removed? and (.value.removed | length) > 0) | 
            "\(.key): \(.value.removed | length) removed"
        ' "$json_report" | tr '\n' ', ')
    fi
    
    # 分析結果を返す
    echo "$total_differences|$critical_changes|$warning_changes|$critical_details"
}

# 通知送信
send_notifications() {
    local comparison_name="$1"
    local html_report="$2"
    local json_report="$3"
    local analysis_result="$4"
    
    IFS='|' read -r total_diff critical_changes warning_changes critical_details <<< "$analysis_result"
    
    log_info "Sending notifications for: $comparison_name"
    
    # 重要度に応じた通知レベル決定
    local priority="LOW"
    local alert_level="INFO"
    
    if [[ "$critical_changes" -gt 0 ]]; then
        priority="HIGH"
        alert_level="CRITICAL"
    elif [[ "$warning_changes" -gt 5 ]]; then
        priority="MEDIUM"
        alert_level="WARNING"
    fi
    
    # Slack通知
    send_slack_notification "$comparison_name" "$priority" "$alert_level" "$analysis_result" "$html_report"
    
    # メール通知
    send_email_notification "$comparison_name" "$priority" "$alert_level" "$analysis_result" "$html_report"
    
    # 重要な変更の場合は追加通知
    if [[ "$critical_changes" -gt 0 ]]; then
        send_emergency_notification "$comparison_name" "$critical_details"
    fi
}

# Slack通知
send_slack_notification() {
    local comparison_name="$1"
    local priority="$2"
    local alert_level="$3"
    local analysis_result="$4"
    local html_report="$5"
    
    if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
        log_warning "Slack webhook URL not configured"
        return
    fi
    
    IFS='|' read -r total_diff critical_changes warning_changes critical_details <<< "$analysis_result"
    
    # アイコンと色の設定
    local icon_emoji=""
    local color=""
    
    case "$alert_level" in
        "CRITICAL")
            icon_emoji=":rotating_light:"
            color="#FF0000"
            ;;
        "WARNING")
            icon_emoji=":warning:"
            color="#FFA500"
            ;;
        *)
            icon_emoji=":information_source:"
            color="#0000FF"
            ;;
    esac
    
    # Slack メッセージ作成
    local message=$(cat <<EOF
{
    "username": "PGSD Bot",
    "icon_emoji": "$icon_emoji",
    "attachments": [
        {
            "color": "$color",
            "title": "Database Schema Changes - $comparison_name",
            "fields": [
                {
                    "title": "Priority",
                    "value": "$priority",
                    "short": true
                },
                {
                    "title": "Total Changes",
                    "value": "$total_diff",
                    "short": true
                },
                {
                    "title": "Critical Changes",
                    "value": "$critical_changes",
                    "short": true
                },
                {
                    "title": "Warning Changes",
                    "value": "$warning_changes",
                    "short": true
                }
            ],
            "actions": [
                {
                    "type": "button",
                    "text": "View Report",
                    "url": "$(get_report_url "$html_report")"
                }
            ]
        }
    ]
}
EOF
)
    
    # Slack に送信
    if curl -X POST -H 'Content-type: application/json' \
        --data "$message" \
        "$SLACK_WEBHOOK_URL" >> "${LOG_FILE}" 2>&1; then
        log_info "Slack notification sent successfully"
    else
        log_error "Failed to send Slack notification"
    fi
}

# メール通知
send_email_notification() {
    local comparison_name="$1"
    local priority="$2"
    local alert_level="$3"
    local analysis_result="$4"
    local html_report="$5"
    
    if [[ -z "${EMAIL_RECIPIENTS:-}" ]]; then
        log_warning "Email recipients not configured"
        return
    fi
    
    IFS='|' read -r total_diff critical_changes warning_changes critical_details <<< "$analysis_result"
    
    # メール本文作成
    local email_body=$(cat <<EOF
Subject: [PGSD] Database Schema Changes - $comparison_name ($priority Priority)

Database Schema Comparison Report

Comparison: $comparison_name
Priority: $priority
Alert Level: $alert_level
Generated: $(date '+%Y-%m-%d %H:%M:%S')

SUMMARY:
- Total Changes: $total_diff
- Critical Changes: $critical_changes
- Warning Changes: $warning_changes

EOF
)
    
    # 重要な変更の詳細追加
    if [[ -n "$critical_details" ]]; then
        email_body+="

CRITICAL CHANGES:
$critical_details
"
    fi
    
    # レポートURL追加
    local report_url=$(get_report_url "$html_report")
    email_body+="

REPORT URL: $report_url

This is an automated notification from PGSD.
"
    
    # メール送信
    if echo "$email_body" | mail -s "[PGSD] Schema Changes - $comparison_name" \
        "${EMAIL_RECIPIENTS}" >> "${LOG_FILE}" 2>&1; then
        log_info "Email notification sent successfully"
    else
        log_error "Failed to send email notification"
    fi
}

# 緊急通知
send_emergency_notification() {
    local comparison_name="$1"
    local critical_details="$2"
    
    log_warning "Sending emergency notification for: $comparison_name"
    
    # PagerDuty通知（設定されている場合）
    if [[ -n "${PAGERDUTY_API_KEY:-}" ]]; then
        send_pagerduty_alert "$comparison_name" "$critical_details"
    fi
    
    # SMS通知（設定されている場合）
    if [[ -n "${SMS_WEBHOOK_URL:-}" ]]; then
        send_sms_alert "$comparison_name" "$critical_details"
    fi
}

# レポートURLの取得
get_report_url() {
    local html_report="$1"
    
    # レポートサーバーが設定されている場合
    if [[ -n "${REPORT_SERVER_URL:-}" ]]; then
        local relative_path=$(realpath --relative-to="${REPORTS_DIR}" "$html_report")
        echo "${REPORT_SERVER_URL}/${relative_path}"
    else
        echo "file://$html_report"
    fi
}

# レポートアーカイブ
archive_old_reports() {
    local days_to_keep="${ARCHIVE_DAYS:-30}"
    
    log_info "Archiving reports older than $days_to_keep days"
    
    # 古いレポートを検索してアーカイブ
    find "${REPORTS_DIR}" -type f -name "*.html" -mtime +${days_to_keep} -exec gzip {} \;
    find "${REPORTS_DIR}" -type f -name "*.json" -mtime +${days_to_keep} -exec gzip {} \;
    
    # 非常に古いファイルを削除
    local deletion_days=$((days_to_keep * 2))
    find "${REPORTS_DIR}" -type f -name "*.gz" -mtime +${deletion_days} -delete
    
    log_info "Report archiving completed"
}

# 統計情報の更新
update_statistics() {
    local comparison_name="$1"
    local duration="$2"
    local analysis_result="$3"
    
    IFS='|' read -r total_diff critical_changes warning_changes critical_details <<< "$analysis_result"
    
    # 統計ファイルに追記
    local stats_file="${LOGS_DIR}/statistics.csv"
    
    # ヘッダー行の追加（ファイルが存在しない場合）
    if [[ ! -f "$stats_file" ]]; then
        echo "timestamp,comparison_name,duration,total_differences,critical_changes,warning_changes" > "$stats_file"
    fi
    
    # 統計データの追記
    echo "$(date '+%Y-%m-%d %H:%M:%S'),$comparison_name,$duration,$total_diff,$critical_changes,$warning_changes" >> "$stats_file"
    
    log_info "Statistics updated for: $comparison_name"
}

# メイン処理
main() {
    log_info "Starting PGSD automation script"
    
    # 設定読み込み
    load_config
    
    # 環境チェック
    check_environment
    
    # 比較実行
    local comparisons=(
        "production-vs-staging|${CONFIG_DIR}/prod-staging.yaml"
        "staging-vs-development|${CONFIG_DIR}/staging-dev.yaml"
    )
    
    for comparison_config in "${comparisons[@]}"; do
        IFS='|' read -r comparison_name config_file <<< "$comparison_config"
        
        local output_dir="${REPORTS_DIR}/$(date +%Y%m%d)/${comparison_name}"
        
        # 比較実行
        local comparison_result
        if comparison_result=$(run_comparison "$comparison_name" "$config_file" "$output_dir"); then
            IFS='|' read -r html_report json_report duration <<< "$comparison_result"
            
            # 結果分析
            local analysis_result=$(analyze_results "$json_report" "$comparison_name")
            
            # 統計情報更新
            update_statistics "$comparison_name" "$duration" "$analysis_result"
            
            # 通知送信
            send_notifications "$comparison_name" "$html_report" "$json_report" "$analysis_result"
        else
            log_error "Skipping notifications for failed comparison: $comparison_name"
        fi
    done
    
    # 古いレポートのアーカイブ
    archive_old_reports
    
    log_info "PGSD automation script completed"
}

# エラーハンドリング
trap 'log_error "Script interrupted"; exit 1' INT TERM

# スクリプト実行
main "$@"
```

## 🔄 ワークフロー統合

### GitHub Actions ワークフロー

```yaml
# .github/workflows/pgsd-automation.yml
name: PGSD Schema Monitoring

on:
  schedule:
    - cron: '0 6 * * *'  # 毎日午前6時
  push:
    paths:
      - 'db/migrations/**'
      - 'schema/**'
  workflow_dispatch:
    inputs:
      comparison_type:
        description: 'Comparison type'
        required: true
        default: 'full'
        type: choice
        options:
          - full
          - critical-only
          - custom

jobs:
  schema-monitoring:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        comparison:
          - name: "production-vs-staging"
            config: "configs/prod-staging.yaml"
          - name: "staging-vs-development"
            config: "configs/staging-dev.yaml"
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pgsd matplotlib pandas numpy seaborn
          pip install -r requirements.txt
      
      - name: Run schema comparison
        env:
          PGSD_API_KEY: ${{ secrets.PGSD_API_KEY }}
          DB_PASSWORD_PROD: ${{ secrets.DB_PASSWORD_PROD }}
          DB_PASSWORD_STAGING: ${{ secrets.DB_PASSWORD_STAGING }}
        run: |
          python scripts/advanced_automation.py \
            --config ${{ matrix.comparison.config }} \
            --batch ${{ matrix.comparison.name }} \
            --output reports/${{ matrix.comparison.name }}
      
      - name: Analyze results
        run: |
          python scripts/schema_analyzer.py \
            --input reports/${{ matrix.comparison.name }} \
            --output analysis/${{ matrix.comparison.name }}
      
      - name: Generate visual report
        run: |
          python scripts/generate_charts.py \
            --input analysis/${{ matrix.comparison.name }} \
            --output charts/${{ matrix.comparison.name }}.png
      
      - name: Send notifications
        if: always()
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
          EMAIL_RECIPIENTS: ${{ secrets.EMAIL_RECIPIENTS }}
        run: |
          python scripts/send_notifications.py \
            --comparison ${{ matrix.comparison.name }} \
            --results analysis/${{ matrix.comparison.name }} \
            --charts charts/${{ matrix.comparison.name }}.png
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: schema-reports-${{ matrix.comparison.name }}
          path: |
            reports/${{ matrix.comparison.name }}/
            analysis/${{ matrix.comparison.name }}/
            charts/${{ matrix.comparison.name }}.png
          retention-days: 30
      
      - name: Archive old reports
        run: |
          python scripts/archive_manager.py \
            --reports-dir reports \
            --archive-days 30 \
            --s3-bucket ${{ secrets.S3_BUCKET }}
```

## 🚀 次のステップ

スクリプト活用を理解したら：

1. **[セキュリティ設定](security.md)** - スクリプトのセキュリティ強化
2. **[トラブルシューティング](../troubleshooting/)** - スクリプトの問題解決
3. **[リファレンス](../reference/)** - 詳細なAPI仕様とコマンド

## 📚 関連資料

- [Python SDK ドキュメント](../reference/python_sdk.md)
- [Bash スクリプト例](../reference/bash_examples.md)
- [ワークフロー設定](../reference/workflow_configuration.md)