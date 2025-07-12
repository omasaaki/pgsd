# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PostgreSQL Schema Diff Tool - PostgreSQLの2つのスキーマ間の差分を分析し、レポートを生成するツール

## Requirements

### 基本要件
- スキーマの比較はpg_dumpコマンドで取得できる情報を元に実現
  - `pg_dump -h %DB_HOST% -U %DB_USER% -d %DB_NAME% -n %TARGET_SCHEMA% --schema-only --no-owner --no-privileges`
- プラットフォーム
  - Python版: 
- 仮想環境
  - pyenvを用いた仮想環境上で開発
- 静的解析
  - 適切なツールを用いて静的解析
- UnitTest
  - 単体テストを作成
- 設計ドキュメント
  - /doc/に設計ドキュメントをMarkdown形式で作成
- ユーザ向けドキュメント
  - /docs/にユーザ向けドキュメントをMarkdown形式で作成

### ソース管理
- githubでソース管理
  - https://github.com/omasaaki/pgsd.git

### レポート形式
- HTML形式（デフォルト）
- Markdown形式
- JSON形式
- XML形式

### 設定管理
- 設定ファイルでプログラムの以下の振る舞いを制御
  - 比較するスキーマの接続情報
  - レポートの出力パス
  - 時刻のタイムゾーン

## Commands

### Development Commands
現在、プロジェクトは計画段階で実装コードはまだ存在しません。以下のコマンドは今後実装予定です：

```bash
# プロジェクト構造作成
mkdir -p src config reports doc/uml doc/images tests

# Python仮想環境セットアップ（pyenv使用予定）
pyenv install 3.x.x
pyenv virtualenv 3.x.x pgsd
pyenv activate pgsd

# 依存関係インストール（requirements.txt作成後）
pip install -r requirements.txt

# テスト実行（テストフレームワーク選定後）
# pytest または unittest の予定

# 静的解析実行（ツール選定後）
# flake8, black, mypy などの使用予定

# ドキュメント生成（PlantUML）
plantuml doc/uml/*.puml -o ../images/
```

### Project Management Commands
```bash
# チケット一覧確認
cat project_management/tickets.md

# 特定チケット詳細確認
# cat project_management/tickets/pgsd-xxx.md

# 開発ルール確認
cat project_management/dev_rule.md
```

## Architecture

### プロジェクト構造（計画）
```
pgsd/
├── src/                        # ソースコード（未実装）
├── config/                     # 設定ファイルサンプル（未実装）
├── reports/                    # レポート出力先（未実装）
├── doc/                        # 設計ドキュメント（未実装）
│   ├── uml/                   # PlantUMLソース
│   └── images/                # 画像出力
├── tests/                      # テストファイル（未実装）
├── project_management/         # プロジェクト管理（✓実装済み）
│   ├── project_management_rule.md
│   ├── tid.md
│   ├── work_rule.md
│   ├── dev_rule.md            # 開発ルール・フロー定義
│   ├── document_rule.md
│   ├── tickets.md             # チケット管理
│   └── tickets/               # 個別チケット（削除済み）
├── CHANGELOG.md               # 作業記録（未実装）
└── CLAUDE.md                  # このファイル
```

### 開発フロー（dev_rule.mdより）
このプロジェクトはチケット駆動開発を採用しています：

1. **チケット着手前の確認**
   - 実行可否確認（設計変更、技術選定、大規模実装等は要確認）
   - 依存チケットの完了状態確認

2. **開発プロセス**
   - 設計作業（アーキテクチャ設計 → 詳細設計）
   - テストコード作成
   - 実装作業
   - 品質チェック（セルフレビュー、静的解析）
   - テスト実行
   - 最終確認

3. **コード品質基準**
   - テストカバレッジ80%以上
   - 既存コード規約に従う
   - エラーハンドリング適切に実装
   - セキュリティ・パフォーマンス考慮

### 現在の状況
- **チケット状況**: 進捗率0%
- **実装状況**: プロジェクト管理体系は確立済み、コード実装は未着手
- **次のステップ**: 新規チケット作成またはコード実装開始
