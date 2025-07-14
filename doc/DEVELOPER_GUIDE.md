# 開発者ガイド

## 概要
PostgreSQL Schema Diff Tool (PGSD)プロジェクトの開発者向け包括ガイドです。

## 目次
1. [クイックスタート](#クイックスタート)
2. [開発環境セットアップ](#開発環境セットアップ)
3. [コーディング規約](#コーディング規約)
4. [テスト戦略](#テスト戦略)
5. [プルリクエストプロセス](#プルリクエストプロセス)
6. [プロジェクト構造](#プロジェクト構造)
7. [ツールとワークフロー](#ツールとワークフロー)

---

## クイックスタート

### 最短開発開始手順
```bash
# 1. リポジトリクローン
git clone https://github.com/omasaaki/pgsd.git
cd pgsd

# 2. 仮想環境セットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 依存関係インストール
pip install -r requirements-dev.txt
pip install -e .

# 4. 開発ツールセットアップ
pre-commit install

# 5. 動作確認
pytest
flake8 src tests
```

### 5分で確認できること
```bash
# ✅ インポートテスト
python -c "from pgsd.utils.logger import get_logger; print('✅ Import OK')"

# ✅ 基本機能テスト  
python -c "
from pgsd.utils.log_config import get_default_config
from pgsd.utils.performance import PerformanceTracker
print('✅ Basic functionality OK')
"

# ✅ 品質チェック
python -m pytest tests/test_cicd_validation.py
```

---

## 開発環境セットアップ

### 必要な環境
- **Python**: 3.8以上（推奨: 3.11）
- **Git**: 2.20以上
- **OS**: Linux, macOS, Windows

### 詳細セットアップ

#### 1. Python環境
```bash
# pyenvを使用する場合（推奨）
pyenv install 3.11.0
pyenv local 3.11.0

# 仮想環境作成
python -m venv venv
source venv/bin/activate
```

#### 2. 開発依存関係
```bash
# 全開発ツールインストール
pip install -r requirements-dev.txt

# 主要パッケージ確認
pip list | grep -E "(pytest|black|flake8|mypy)"
```

#### 3. エディタ設定

##### VSCode推奨設定 (.vscode/settings.json)
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

##### PyCharm設定
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing environment → `./venv/bin/python`
3. Tools → External Tools で各種ツール登録

#### 4. Git設定
```bash
# pre-commit hooks有効化
pre-commit install

# Git hooks確認
ls -la .git/hooks/
```

---

## コーディング規約

### 1. Python スタイルガイド

#### 基本方針
- **PEP 8準拠** + **Black自動フォーマット**
- **型ヒント必須** (Python 3.8+対応)
- **Docstring必須** (Google形式)

#### コードフォーマット
```python
# ✅ Good
from typing import Optional, Dict, Any
from pathlib import Path


def process_database_connection(
    host: str,
    port: int = 5432,
    options: Optional[Dict[str, Any]] = None,
) -> bool:
    """Connect to PostgreSQL database.
    
    Args:
        host: Database hostname
        port: Database port number
        options: Additional connection options
        
    Returns:
        True if connection successful
        
    Raises:
        ConnectionError: If connection fails
    """
    if options is None:
        options = {}
    # Implementation...
    return True
```

#### 避けるべきパターン
```python
# ❌ Bad - 型ヒントなし、docstringなし
def process_db(host, port=5432, options=None):
    if options == None:  # ❌ "is None" を使用
        options = {}
    return True

# ❌ Bad - 長すぎる行
result = very_long_function_name(very_long_parameter_name, another_very_long_parameter_name, yet_another_parameter)
```

### 2. プロジェクト固有規約

#### インポート順序（isort設定準拠）
```python
# 1. 標準ライブラリ
import os
import sys
from pathlib import Path
from typing import Optional

# 2. サードパーティ
import structlog
import yaml

# 3. ローカルインポート
from pgsd.utils.logger import get_logger
from pgsd.utils.performance import PerformanceTracker
```

#### ログ記録規約
```python
# ✅ 構造化ログ使用
logger = get_logger(__name__)
logger.info(
    "database_connection_established",
    host=config.host,
    port=config.port,
    schema_count=len(schemas)
)

# ❌ 文字列フォーマット使用
logger.info(f"Connected to {config.host}:{config.port}")
```

#### エラーハンドリング
```python
# ✅ 具体的な例外処理
try:
    connection = connect_to_database(config)
except ConnectionTimeoutError as e:
    logger.error("database_connection_timeout", error=str(e), host=config.host)
    raise DatabaseConnectionError(f"Timeout connecting to {config.host}") from e
except Exception as e:
    logger.error("database_connection_failed", error=str(e))
    raise

# ❌ 一般的すぎる例外処理
try:
    connection = connect_to_database(config)
except Exception:
    pass  # ❌ サイレント失敗
```

### 3. テストコード規約

#### テスト構造
```python
class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = get_test_config()
        self.tracker = PerformanceTracker()
    
    def test_successful_connection(self):
        """Test successful database connection."""
        # Arrange
        expected_schemas = ["public", "test"]
        
        # Act
        result = connect_to_database(self.config)
        
        # Assert
        assert result.is_connected
        assert result.schema_count == len(expected_schemas)
    
    @pytest.mark.parametrize("invalid_host", ["", "invalid-host", None])
    def test_connection_with_invalid_host(self, invalid_host):
        """Test connection failure with invalid hosts."""
        config = self.config._replace(host=invalid_host)
        
        with pytest.raises(DatabaseConnectionError):
            connect_to_database(config)
```

---

## テスト戦略

### 1. テスト分類

#### 単体テスト (Unit Tests)
- **対象**: 個別関数・クラス
- **実行時間**: < 1秒/テスト
- **外部依存**: なし（モック使用）

```python
def test_log_config_validation():
    """Test log configuration validation."""
    with pytest.raises(ValueError, match="Invalid log level"):
        LogConfig(level="INVALID")
```

#### 統合テスト (Integration Tests)
- **対象**: モジュール間連携
- **実行時間**: < 10秒/テスト
- **外部依存**: あり（テスト用DB等）

```python
@pytest.mark.integration
def test_database_schema_extraction():
    """Test schema extraction from real database."""
    # テスト用データベース使用
    pass
```

#### エンドツーエンドテスト (E2E Tests)
- **対象**: 全体フロー
- **実行時間**: < 60秒/テスト
- **外部依存**: 実環境相当

### 2. テスト実行

#### ローカル実行
```bash
# 全テスト実行
pytest

# 単体テストのみ
pytest -m unit

# 統合テストのみ  
pytest -m integration

# 高速実行（並列）
pytest -n auto

# カバレッジ付き
pytest --cov=src --cov-report=html
```

#### CI環境での実行
- **並列実行**: OS × Python バージョンマトリックス
- **タイムアウト**: 15分
- **カバレッジ要件**: 40%以上（段階的に80%へ）

### 3. テスト品質基準

#### カバレッジ目標
- **短期目標**: 40%以上（現在の基準）
- **中期目標**: 60%以上
- **長期目標**: 80%以上

#### テストケース必須項目
- [ ] 正常系テスト
- [ ] 異常系テスト (エラーケース)
- [ ] 境界値テスト
- [ ] パフォーマンステスト（重要機能）

---

## プルリクエストプロセス

### 1. ブランチ戦略

#### ブランチ命名規則
```
feature/PGSD-XXX-short-description    # 新機能
bugfix/PGSD-XXX-fix-description      # バグ修正
hotfix/PGSD-XXX-urgent-fix           # 緊急修正
refactor/PGSD-XXX-refactor-component # リファクタリング
```

#### ワークフロー
```
main ← feature/PGSD-XXX ← ローカル開発
  ↓
 PR作成 → レビュー → テスト → マージ
```

### 2. PR作成チェックリスト

#### 作成前チェック
- [ ] 最新mainから分岐している
- [ ] ローカルテストが全て通る
- [ ] コードフォーマットが適用済み
- [ ] コミットメッセージが規約準拠

#### PR内容チェック
- [ ] 変更内容が明確に説明されている
- [ ] 関連チケット番号が記載されている
- [ ] テストが追加されている
- [ ] ドキュメントが更新されている
- [ ] 破壊的変更がある場合は明記

### 3. レビュープロセス

#### レビュー観点
1. **機能要件**: 仕様通りの実装か
2. **コード品質**: 規約準拠・可読性
3. **テスト**: 適切なテストカバレッジ
4. **パフォーマンス**: 性能劣化はないか
5. **セキュリティ**: 脆弱性はないか

#### レビュア責任
- **24時間以内**: 初回レビュー
- **建設的フィードバック**: 改善提案
- **承認基準**: 全観点でOKかつCI通過

### 4. マージ基準

#### 必須条件
- [ ] レビュー承認（1名以上）
- [ ] CI/CD全て通過
- [ ] コンフリクト解決済み
- [ ] 最新mainとの差分確認済み

#### マージ後処理
- [ ] 機能ブランチ削除
- [ ] リリースノート更新（必要に応じて）
- [ ] チケットステータス更新

---

## プロジェクト構造

### 1. ディレクトリ構成
```
pgsd/
├── .github/                    # GitHub設定
│   ├── workflows/             # CI/CD設定
│   ├── ISSUE_TEMPLATE/        # Issue テンプレート
│   └── pull_request_template.md
├── doc/                       # ドキュメント
│   ├── design/               # 設計文書
│   └── operations/           # 運用文書
├── src/pgsd/                 # ソースコード
│   ├── utils/               # ユーティリティ
│   ├── core/                # コアロジック
│   ├── database/            # DB接続・操作
│   ├── reports/             # レポート生成
│   └── config/              # 設定管理
├── tests/                   # テストコード
│   ├── unit/               # 単体テスト
│   ├── integration/        # 統合テスト
│   └── fixtures/           # テストデータ
├── project_management/      # プロジェクト管理
└── requirements-dev.txt     # 開発依存関係
```

### 2. 主要モジュール

#### utils パッケージ
- **log_config.py**: ログ設定管理
- **logger.py**: 統一ログインターフェース
- **performance.py**: パフォーマンス測定

#### 今後実装予定
- **core/engine.py**: 差分検出エンジン
- **database/connector.py**: PostgreSQL接続
- **reports/generators.py**: レポート生成器

### 3. 設定ファイル

#### 開発ツール設定
- **pyproject.toml**: プロジェクト設定・ツール設定
- **.flake8**: 静的解析設定
- **.pre-commit-config.yaml**: pre-commit設定
- **requirements-dev.txt**: 開発依存関係

#### CI/CD設定
- **.github/workflows/**: GitHub Actions設定
- **.github/dependabot.yml**: 依存関係更新設定

---

## ツールとワークフロー

### 1. 開発ツールチェーン

#### コード品質
```bash
# フォーマット
black src tests                    # コードフォーマット
isort src tests                   # インポートソート

# 静的解析  
flake8 src tests                  # スタイルチェック
mypy src                          # 型チェック
bandit -r src/                    # セキュリティスキャン

# テスト
pytest                            # テスト実行
pytest --cov=src                  # カバレッジ付き
```

#### 依存関係管理
```bash
# 脆弱性チェック
safety check                      # 既知の脆弱性
pip-audit                         # 包括的監査

# アップデート確認
pip list --outdated              # 更新可能パッケージ
```

### 2. 自動化ワークフロー

#### Pre-commit（ローカル）
```yaml
# 自動実行内容
- trailing-whitespace            # 末尾空白除去
- end-of-file-fixer             # EOF修正
- check-yaml                    # YAML文法チェック
- black                         # フォーマット
- isort                         # インポートソート
- flake8                        # 静的解析
- mypy                          # 型チェック
- bandit                        # セキュリティ
```

#### GitHub Actions（CI/CD）
- **Pull Request**: 品質チェック
- **Main Push**: テスト・ビルド
- **Tag Push**: リリース作成
- **Weekly**: セキュリティスキャン

### 3. 推奨開発フロー

#### 日常開発
```bash
# 1. 最新化
git checkout main && git pull

# 2. ブランチ作成
git checkout -b feature/PGSD-XXX-description

# 3. 開発
# コード実装...

# 4. 品質チェック
pre-commit run --all-files
pytest

# 5. コミット
git add . && git commit -m "Add feature: description"

# 6. プッシュ・PR
git push origin feature/PGSD-XXX-description
# GitHub UIでPR作成
```

#### 問題解決フロー
```bash
# テスト失敗時
pytest tests/test_specific.py -v --tb=long

# 静的解析エラー時
flake8 src tests --show-source
mypy src --show-error-codes

# パフォーマンス問題時
pytest --durations=10           # 遅いテスト特定
py-spy record -o profile.svg -- python script.py  # プロファイリング
```

---

## パフォーマンス最適化

### 1. 開発環境最適化

#### 高速テスト実行
```bash
# 並列実行
pytest -n auto                   # CPU数に応じて並列

# 失敗時即停止
pytest -x                        # 最初の失敗で停止

# 前回失敗分のみ
pytest --lf                      # last failed

# マーカー活用
pytest -m "not slow"             # 重いテストをスキップ
```

#### 効率的デバッグ
```python
# パフォーマンス測定
from pgsd.utils.performance import performance_measurement

with performance_measurement("slow_operation"):
    # 測定対象の処理
    pass

# ログレベル調整
import logging
logging.getLogger("pgsd").setLevel(logging.DEBUG)
```

### 2. CI/CD最適化

#### キャッシュ活用
- **pip cache**: 依存関係インストール高速化
- **pre-commit cache**: hook実行高速化
- **pytest cache**: テスト結果キャッシュ

#### 並列実行
- **マトリックス**: OS × Python バージョン
- **ジョブ分割**: lint → test → security

---

## トラブルシューティング

### よくある問題と解決法

#### 1. インポートエラー
```bash
# 症状: ModuleNotFoundError: No module named 'pgsd'
# 解決法
pip install -e .               # 開発モードでインストール
python -c "import pgsd; print(pgsd.__file__)"  # 確認
```

#### 2. テスト失敗
```bash
# 症状: テストが通らない
# 診断
pytest tests/test_specific.py -v --tb=long    # 詳細エラー表示
pytest --pdb                                  # デバッガ起動

# 環境確認
python --version
pip list | grep -E "(pytest|pgsd)"
```

#### 3. 静的解析エラー
```bash
# flake8エラー修正
black src tests               # 自動フォーマット
isort src tests              # インポート順序修正

# mypy エラー確認
mypy src --show-error-codes  # エラーコード表示
```

#### 4. パフォーマンス問題
```bash
# 遅いテスト特定
pytest --durations=10

# メモリ使用量確認
memory_profiler -o profile.log script.py
```

### サポートリソース

- **GitHub Issues**: バグ報告・質問
- **GitHub Discussions**: 一般的な議論
- **CI/CD運用マニュアル**: `doc/operations/CICD_OPERATIONS_MANUAL.md`

---

## 更新履歴
- **2025-07-14**: 初版作成
- **YYYY-MM-DD**: 更新内容