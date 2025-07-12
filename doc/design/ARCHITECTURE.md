# アーキテクチャ設計書
**PostgreSQL Schema Diff Tool (PGSD)**

## 📋 概要
本文書は、要件定義書、機能設計書、および各種技術調査結果を統合したPGSDの総合的なアーキテクチャ設計を定義する。

---

## 🏗️ システム全体構成

### アーキテクチャ概要
```
┌─────────────────────────────────────────────────────────────┐
│                    PGSD Architecture                        │
├─────────────────────────────────────────────────────────────┤
│  CLI Interface (Click)                                      │
├─────────────────────────────────────────────────────────────┤
│  Configuration Manager (YAML)                              │
├─────────────────────────────────────────────────────────────┤
│  Core Engine                                               │
│  ├─ Schema Extractor (information_schema)                  │
│  ├─ Diff Analyzer (集合演算ベース)                           │
│  └─ Report Generator (Jinja2 Templates)                    │
├─────────────────────────────────────────────────────────────┤
│  Database Connector (psycopg2/asyncpg)                     │
├─────────────────────────────────────────────────────────────┤
│  Logging & Error Handler                                   │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL Databases                                      │
└─────────────────────────────────────────────────────────────┘
```

### レイヤー構成
1. **プレゼンテーション層**: CLI、設定管理
2. **ビジネスロジック層**: コアエンジン、差分検出
3. **データアクセス層**: DB接続、情報取得
4. **インフラ層**: ログ、エラーハンドリング

---

## 📦 モジュール設計

### パッケージ構成
```
pgsd/
├── src/
│   └── pgsd/
│       ├── __init__.py
│       ├── main.py                 # エントリーポイント
│       ├── cli.py                  # CLI処理
│       ├── config/
│       │   ├── __init__.py
│       │   ├── manager.py          # 設定管理
│       │   └── validator.py        # 設定値検証
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py           # メインエンジン
│       │   ├── extractor.py        # スキーマ情報取得
│       │   ├── analyzer.py         # 差分検出
│       │   └── models.py           # データモデル
│       ├── database/
│       │   ├── __init__.py
│       │   ├── connector.py        # DB接続管理
│       │   └── version.py          # バージョン管理
│       ├── reports/
│       │   ├── __init__.py
│       │   ├── generator.py        # レポート生成
│       │   ├── formatters/
│       │   │   ├── __init__.py
│       │   │   ├── html.py         # HTML出力
│       │   │   ├── markdown.py     # Markdown出力
│       │   │   ├── json.py         # JSON出力
│       │   │   └── xml.py          # XML出力
│       │   └── templates/          # Jinja2テンプレート
│       │       ├── html_template.html
│       │       └── markdown_template.md
│       └── utils/
│           ├── __init__.py
│           ├── logger.py           # ログ管理
│           ├── exceptions.py       # カスタム例外
│           └── helpers.py          # ユーティリティ
├── config/
│   └── pgsd_config.yaml.example   # 設定ファイルサンプル
├── tests/
│   ├── unit/                       # 単体テスト
│   ├── integration/                # 統合テスト
│   └── fixtures/                   # テストデータ
└── docs/
    └── api/                        # APIドキュメント
```

### 主要モジュール詳細

#### 1. CLI Module (cli.py)
```python
# Click framework使用
@click.command()
@click.option('--config', '-c', help='設定ファイルパス')
@click.option('--source-db', '-s', help='比較元DB接続文字列')
@click.option('--target-db', '-t', help='比較先DB接続文字列')
@click.option('--output', '-o', type=click.Choice(['html', 'markdown', 'json', 'xml']))
@click.option('--output-path', '-p', help='出力先ディレクトリ')
@click.option('--verbose', '-v', is_flag=True, help='詳細出力')
def main(config, source_db, target_db, output, output_path, verbose):
    pass
```

#### 2. Core Engine (core/engine.py)
```python
class PGSDEngine:
    def __init__(self, config):
        self.config = config
        self.extractor = SchemaExtractor(config)
        self.analyzer = DiffAnalyzer()
        self.reporter = ReportGenerator(config)
    
    async def run_comparison(self):
        # メインの差分検出処理
        pass
```

#### 3. Schema Extractor (core/extractor.py)
```python
class SchemaExtractor:
    def __init__(self, config):
        self.connector = DatabaseConnector(config)
    
    async def extract_schema(self, connection_info, schema_name):
        # information_schemaからスキーマ情報を取得
        pass
```

#### 4. Diff Analyzer (core/analyzer.py)
```python
class DiffAnalyzer:
    def analyze(self, schema_a, schema_b):
        # 集合演算ベースの差分検出
        pass
    
    def _compare_tables(self, tables_a, tables_b):
        pass
    
    def _compare_columns(self, columns_a, columns_b):
        pass
```

---

## 🔄 データフロー設計

### メイン処理フロー
```
1. CLI起動
   ↓
2. 設定読み込み・検証
   ↓
3. データベース接続確認
   ↓
4. PostgreSQLバージョン検出
   ↓
5. スキーマA情報取得
   ↓
6. スキーマB情報取得
   ↓
7. 差分検出・分析
   ↓
8. レポート生成
   ↓
9. ファイル出力
   ↓
10. 結果サマリ表示
```

### データモデル設計
```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class TableInfo:
    name: str
    schema: str
    table_type: str
    columns: List['ColumnInfo']
    constraints: List['ConstraintInfo']

@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str]
    character_maximum_length: Optional[int]
    numeric_precision: Optional[int]
    ordinal_position: int

@dataclass
class ConstraintInfo:
    name: str
    constraint_type: str
    table_name: str
    columns: List[str]
    
@dataclass
class DiffResult:
    tables: Dict[str, List]
    columns: Dict[str, List]
    constraints: Dict[str, List]
    views: Dict[str, List]
    summary: Dict[str, int]
```

---

## ⚙️ 設定管理設計

### 設定ファイル構造 (YAML)
```yaml
# pgsd_config.yaml
database:
  source:
    host: "localhost"
    port: 5432
    database: "production_db"
    username: "readonly_user"
    password: "${PGSD_SOURCE_PASSWORD}"
    schema: "public"
    connection_timeout: 30
  
  target:
    host: "localhost"
    port: 5432
    database: "development_db"
    username: "readonly_user"
    password: "${PGSD_TARGET_PASSWORD}"
    schema: "public"
    connection_timeout: 30

output:
  format: "html"
  path: "./reports/"
  filename_template: "schema_diff_{timestamp}"
  
comparison:
  include_views: true
  include_constraints: true
  ignore_case: false
  exclude_tables:
    - "temp_*"
    - "log_*"
  
system:
  timezone: "UTC"
  log_level: "INFO"
  log_file: "pgsd.log"
  max_connections: 5

postgresql:
  minimum_version: "13.0"
  version_check: true
  compatibility_mode: "strict"
```

### 環境変数サポート
- `${VAR_NAME}` 形式での変数置換
- `.env` ファイルサポート
- 実行時のオーバーライド対応

---

## 🔗 データベース接続設計

### 接続管理
```python
class DatabaseConnector:
    def __init__(self, config):
        self.config = config
        self.connection_pool = None
    
    async def get_connection(self, db_config):
        # 接続プール管理
        pass
    
    async def verify_connection(self, db_config):
        # 接続確認
        pass
    
    async def check_permissions(self, connection):
        # 権限確認
        pass
    
    async def get_version(self, connection):
        # PostgreSQLバージョン取得
        pass
```

### バージョン対応
- PostgreSQL 13以降をサポート
- バージョン検出とログ記録
- 互換性チェック機能

---

## 📊 ログ・監視設計

### ログ設計
```python
import structlog

# 構造化ログ設計
logger = structlog.get_logger()

# ログレベル
# - DEBUG: 詳細なデバッグ情報
# - INFO: 一般的な処理情報
# - WARNING: 警告（処理は継続）
# - ERROR: エラー（処理停止）
# - CRITICAL: 致命的エラー

# ログ出力例
logger.info(
    "schema_extraction_started",
    database=db_name,
    schema=schema_name,
    timestamp=datetime.utcnow()
)
```

### メトリクス収集
- 処理時間測定
- メモリ使用量監視
- 差分検出件数統計
- エラー発生率

---

## 🚨 エラーハンドリング設計

### カスタム例外設計
```python
class PGSDError(Exception):
    """PGSD基底例外"""
    pass

class DatabaseConnectionError(PGSDError):
    """データベース接続エラー"""
    pass

class SchemaNotFoundError(PGSDError):
    """スキーマ未発見エラー"""
    pass

class InsufficientPrivilegesError(PGSDError):
    """権限不足エラー"""
    pass

class ConfigurationError(PGSDError):
    """設定エラー"""
    pass
```

### エラー処理フロー
1. 例外キャッチ
2. ログ記録
3. ユーザーフレンドリーなメッセージ表示
4. 適切な終了コード設定
5. クリーンアップ処理

---

## 🧪 テスト戦略

### テスト構成
```
tests/
├── unit/                    # 単体テスト (pytest)
│   ├── test_extractor.py   # スキーマ抽出テスト
│   ├── test_analyzer.py    # 差分検出テスト
│   ├── test_generator.py   # レポート生成テスト
│   └── test_config.py      # 設定管理テスト
├── integration/             # 統合テスト
│   ├── test_end_to_end.py  # E2Eテスト
│   └── test_database.py    # DB統合テスト
├── fixtures/               # テストデータ
│   ├── sample_schemas/     # サンプルスキーマ
│   └── config_samples/     # 設定サンプル
└── conftest.py             # pytest設定
```

### テスト実行環境
- **Docker Compose**: 複数PostgreSQLバージョン
- **GitHub Actions**: CI/CD自動実行
- **Coverage**: カバレッジ測定（目標: 85%以上）

---

## 🚀 CI/CD設計

### GitHub Actions ワークフロー
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
        postgresql-version: [13, 14, 15, 16]
    
    services:
      postgres:
        image: postgres:${{ matrix.postgresql-version }}
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    
    - name: Run linters
      run: |
        black --check .
        flake8 .
        mypy src/
    
    - name: Run tests
      run: |
        pytest --cov=pgsd --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Build package
      run: |
        python -m build
    
    - name: Publish to PyPI
      if: startsWith(github.ref, 'refs/tags')
      uses: pypa/gh-action-pypi-publish@release/v1
```

### パッケージング
- **setuptools**: パッケージビルド
- **PyPI**: 公開リリース
- **Docker**: コンテナ配布
- **GitHub Releases**: バイナリ配布

---

## 🔒 セキュリティ設計

### セキュリティ要件
1. **接続情報の保護**
   - 設定ファイルの適切なアクセス権限
   - 環境変数での機密情報管理
   - メモリ上での接続情報暗号化

2. **SQLインジェクション対策**
   - パラメータクエリの使用
   - 入力値検証・サニタイズ

3. **最小権限の原則**
   - 読み取り専用権限での動作
   - 必要最小限のスキーマアクセス

### セキュリティチェック
- **Bandit**: 静的セキュリティ解析
- **Safety**: 脆弱性スキャン
- **Dependabot**: 依存関係監視

---

## 📈 性能設計

### パフォーマンス目標
- **小規模**: ~50テーブル、処理時間 < 10秒
- **中規模**: ~500テーブル、処理時間 < 60秒
- **大規模**: ~1000テーブル、処理時間 < 300秒

### 最適化戦略
1. **並列処理**: 複数テーブルの並行取得
2. **接続プール**: DB接続の再利用
3. **メモリ管理**: ジェネレータによる遅延処理
4. **キャッシュ**: スキーマ情報の一時保存

---

## 🔧 運用・保守設計

### 監視項目
- 処理時間
- メモリ使用量
- エラー発生率
- 成功/失敗統計

### メンテナンス性
- 構造化ログ
- 設定の外部化
- モジュール分離
- APIドキュメント自動生成

---

## 🚀 将来拡張

### Phase 2 候補機能
1. **PostgreSQL固有機能対応**
   - pg_catalogを併用した詳細情報取得
   - パーティション、継承関係の対応

2. **高度な差分検出**
   - テーブル名変更推定
   - データ移行SQL生成

3. **Web UI**
   - ブラウザベースのインターフェース
   - リアルタイム監視ダッシュボード

4. **他DBMS対応**
   - MySQL、Oracle、SQL Server対応
   - 統一API設計

---

## 関連ドキュメント
- [要件定義書](../requirements/REQUIREMENTS.md)
- [機能設計書](./FUNCTIONAL_DESIGN.md)
- [PGSD-005: スキーマ情報取得方法調査](../research/PGSD-005_schema_info_method_research.md)
- [PGSD-006: PostgreSQLバージョン間差異検証](../research/PGSD-006_postgresql_version_compatibility.md)
- [PGSD-007: 差分検出アルゴリズム検証](../research/PGSD-007_diff_algorithm_verification.md)
- [PGSD-008: information_schema調査](../research/PGSD-008_information_schema_research.md)

---

更新日: 2025-07-12  
作成者: PGSD-004（アーキテクチャ設計）