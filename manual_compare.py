#!/usr/bin/env python3
"""手動スキーマ比較スクリプト"""

import psycopg2
from datetime import datetime

def get_table_info(conn, schema_name):
    """テーブル情報を取得する"""
    cur = conn.cursor()
    
    # テーブルの取得
    cur.execute('''
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        ORDER BY table_name
    ''', (schema_name,))
    tables = cur.fetchall()
    
    # 各テーブルのカラム情報を取得
    table_details = {}
    for table_name, table_type in tables:
        cur.execute('''
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        ''', (schema_name, table_name))
        columns = cur.fetchall()
        table_details[table_name] = {
            'type': table_type,
            'columns': columns
        }
    
    cur.close()
    return table_details

def compare_schemas(source_info, target_info):
    """スキーマを比較する"""
    differences = []
    
    # テーブルの比較
    source_tables = set(source_info.keys())
    target_tables = set(target_info.keys())
    
    # 追加されたテーブル
    added_tables = target_tables - source_tables
    for table in added_tables:
        differences.append({
            'type': 'table_added',
            'table': table,
            'columns': len(target_info[table]['columns'])
        })
    
    # 削除されたテーブル
    removed_tables = source_tables - target_tables
    for table in removed_tables:
        differences.append({
            'type': 'table_removed',
            'table': table,
            'columns': len(source_info[table]['columns'])
        })
    
    # 共通テーブルのカラム比較
    common_tables = source_tables & target_tables
    for table in common_tables:
        source_cols = {col[0]: col for col in source_info[table]['columns']}
        target_cols = {col[0]: col for col in target_info[table]['columns']}
        
        # 追加されたカラム
        added_cols = set(target_cols.keys()) - set(source_cols.keys())
        for col in added_cols:
            differences.append({
                'type': 'column_added',
                'table': table,
                'column': col,
                'data_type': target_cols[col][1]
            })
        
        # 削除されたカラム
        removed_cols = set(source_cols.keys()) - set(target_cols.keys())
        for col in removed_cols:
            differences.append({
                'type': 'column_removed',
                'table': table,
                'column': col,
                'data_type': source_cols[col][1]
            })
        
        # 変更されたカラム
        common_cols = set(source_cols.keys()) & set(target_cols.keys())
        for col in common_cols:
            if source_cols[col][1] != target_cols[col][1]:  # data_type changed
                differences.append({
                    'type': 'column_type_changed',
                    'table': table,
                    'column': col,
                    'old_type': source_cols[col][1],
                    'new_type': target_cols[col][1]
                })
    
    return differences

def main():
    """メイン処理"""
    try:
        print('=== PostgreSQL スキーマ比較レポート ===')
        print(f'実行時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print()
        
        # DB1 (ntb) の情報取得
        print('DB1 (ntb) のスキーマ情報を取得中...')
        conn1 = psycopg2.connect(
            host='localhost', port=5432, database='ntb', 
            user='ntb', password='ntb'
        )
        source_info = get_table_info(conn1, 'ntb')
        conn1.close()
        print(f'DB1: {len(source_info)} テーブル')
        
        # DB2 (ntb_demo3) の情報取得
        print('DB2 (ntb_demo3) のスキーマ情報を取得中...')
        conn2 = psycopg2.connect(
            host='localhost', port=5432, database='ntb_demo3', 
            user='ntb_demo3', password='ntb_demo3'
        )
        target_info = get_table_info(conn2, 'ntb_demo3')
        conn2.close()
        print(f'DB2: {len(target_info)} テーブル')
        
        # 比較の実行
        print()
        print('スキーマ比較を実行中...')
        differences = compare_schemas(source_info, target_info)
        
        # 結果の表示
        print()
        print('=== 比較結果 ===')
        print(f'差分の総数: {len(differences)}')
        print()
        
        # 差分の分類
        diff_types = {}
        for diff in differences:
            diff_type = diff['type']
            diff_types[diff_type] = diff_types.get(diff_type, 0) + 1
        
        print('差分の分類:')
        for diff_type, count in sorted(diff_types.items()):
            print(f'  {diff_type}: {count} 項目')
        
        # 詳細の表示（最初の20件）
        if differences:
            print()
            print('詳細 (最初の20件):')
            for i, diff in enumerate(differences[:20]):
                if diff['type'] == 'table_added':
                    print(f'{i+1}. テーブル追加: {diff["table"]} ({diff["columns"]} カラム)')
                elif diff['type'] == 'table_removed':
                    print(f'{i+1}. テーブル削除: {diff["table"]} ({diff["columns"]} カラム)')
                elif diff['type'] == 'column_added':
                    print(f'{i+1}. カラム追加: {diff["table"]}.{diff["column"]} ({diff["data_type"]})')
                elif diff['type'] == 'column_removed':
                    print(f'{i+1}. カラム削除: {diff["table"]}.{diff["column"]} ({diff["data_type"]})')
                elif diff['type'] == 'column_type_changed':
                    print(f'{i+1}. カラム型変更: {diff["table"]}.{diff["column"]} {diff["old_type"]} → {diff["new_type"]}')
        
        # HTMLレポート生成
        generate_html_report(differences, source_info, target_info)
        
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()

def generate_html_report(differences, source_info, target_info):
    """HTMLレポートを生成する"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>PostgreSQL スキーマ比較レポート</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; margin-bottom: 20px; }}
            .summary {{ background-color: #e8f4f8; padding: 15px; margin-bottom: 20px; }}
            .differences {{ margin-bottom: 20px; }}
            .diff-item {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
            .table-added {{ border-left-color: #4CAF50; background-color: #f1f8e9; }}
            .table-removed {{ border-left-color: #f44336; background-color: #ffebee; }}
            .column-added {{ border-left-color: #2196F3; background-color: #e3f2fd; }}
            .column-removed {{ border-left-color: #FF9800; background-color: #fff3e0; }}
            .column-type-changed {{ border-left-color: #9C27B0; background-color: #f3e5f5; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>PostgreSQL スキーマ比較レポート</h1>
            <p>実行時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <h2>概要</h2>
            <p>ソースDB (ntb): {len(source_info)} テーブル</p>
            <p>ターゲットDB (ntb_demo3): {len(target_info)} テーブル</p>
            <p>差分の総数: {len(differences)} 項目</p>
        </div>
        
        <div class="differences">
            <h2>差分詳細</h2>
    """
    
    for i, diff in enumerate(differences):
        css_class = diff['type'].replace('_', '-')
        if diff['type'] == 'table_added':
            html_content += f'<div class="diff-item {css_class}">{i+1}. テーブル追加: {diff["table"]} ({diff["columns"]} カラム)</div>'
        elif diff['type'] == 'table_removed':
            html_content += f'<div class="diff-item {css_class}">{i+1}. テーブル削除: {diff["table"]} ({diff["columns"]} カラム)</div>'
        elif diff['type'] == 'column_added':
            html_content += f'<div class="diff-item {css_class}">{i+1}. カラム追加: {diff["table"]}.{diff["column"]} ({diff["data_type"]})</div>'
        elif diff['type'] == 'column_removed':
            html_content += f'<div class="diff-item {css_class}">{i+1}. カラム削除: {diff["table"]}.{diff["column"]} ({diff["data_type"]})</div>'
        elif diff['type'] == 'column_type_changed':
            html_content += f'<div class="diff-item {css_class}">{i+1}. カラム型変更: {diff["table"]}.{diff["column"]} {diff["old_type"]} → {diff["new_type"]}</div>'
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # レポートを保存
    report_filename = f'reports/schema_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f'HTMLレポートを生成しました: {report_filename}')

if __name__ == '__main__':
    main()